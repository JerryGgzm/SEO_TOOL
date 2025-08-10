"""User Profile Repository

This module provides data access layer for user profile management,
now using the unified founders table instead of separate user_profiles table.
"""
import os
import logging
import hashlib
import secrets
import base64
import bcrypt
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from cryptography.fernet import Fernet
from dotenv import load_dotenv

from .models import UserProfileData, ProductInfoData, TwitterCredentials, UserRegistration, UserLogin
from database.models import Founder, TwitterCredential

logger = logging.getLogger(__name__)
load_dotenv('.env')

class UserProfileRepository:
    """User profile data access layer - now using founders table"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.model_class = TwitterCredential  # 使用统一的TwitterCredential模型
        
        # 初始化加密密钥
        encryption_key = os.getenv('ENCRYPTION_KEY')
        if not encryption_key:
            raise ValueError("ENCRYPTION_KEY environment variable is required")
        
        # 确保密钥长度正确
        key_bytes = base64.urlsafe_b64encode(encryption_key.encode()[:32].ljust(32, b'0'))
        self.cipher_suite = Fernet(key_bytes)
    
    def _encrypt_token(self, token: str) -> str:
        """加密令牌"""
        if not token:
            return None
        return self.cipher_suite.encrypt(token.encode()).decode()
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """解密令牌"""
        if not encrypted_token:
            return None
        try:
            return self.cipher_suite.decrypt(encrypted_token.encode()).decode()
        except Exception as e:
            logger.error(f"解密令牌失败: {e}")
            return None
    
    def create_user(self, user_data: UserRegistration) -> Optional[str]:
        """Create new user"""
        try:
            user_id = self._generate_user_id()
            password_hash = self._hash_password(user_data.password)
            
            user = Founder(
                id=user_id,
                email=user_data.email,
                username=user_data.username,
                hashed_password=password_hash,
                full_name=user_data.full_name,
                company_name=user_data.company_name,
                role=None,  # Will be set later if needed
                timezone='UTC',  # Default timezone
                is_active=True,
                settings={},  # Initialize empty settings
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db_session.add(user)
            self.db_session.commit()
            return user_id
            
        except IntegrityError:
            self.db_session.rollback()
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[UserProfileData]:
        """Get user information by user ID"""
        user = self.db_session.query(Founder).filter(
            Founder.id == user_id,
            Founder.is_active == True
        ).first()
        
        if not user:
            return None
            
        return self._user_table_to_model(user)
    
    def get_user_by_email(self, email: str) -> Optional[UserProfileData]:
        """Get user information by email"""
        user = self.db_session.query(Founder).filter(
            Founder.email == email,
            Founder.is_active == True
        ).first()
        
        if not user:
            return None
            
        return self._user_table_to_model(user)
    
    def verify_password(self, email: str, password: str) -> Optional[str]:
        """Verify user password, return user ID"""
        user = self.db_session.query(Founder).filter(
            Founder.email == email,
            Founder.is_active == True
        ).first()
        
        if not user:
            return None
            
        if self._verify_password(password, user.hashed_password):
            return str(user.id)
        return None
    
    def update_product_info(self, user_id: str, product_info: ProductInfoData) -> bool:
        """Update user product information"""
        try:
            user = self.db_session.query(Founder).filter(
                Founder.id == user_id
            ).first()
            
            if not user:
                return False
            
            # Store product info in settings JSON field
            if not user.settings:
                user.settings = {}
            user.settings['product_info'] = product_info.dict()
            user.updated_at = datetime.utcnow()
            
            self.db_session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update product info: {e}")
            self.db_session.rollback()
            return False
    
    def save_twitter_credentials(self, user_id: str, credentials: Dict[str, Any]) -> bool:
        """Save Twitter credentials for user"""
        try:
            # Check if user exists
            user = self.db_session.query(Founder).filter(Founder.id == user_id).first()
            if not user:
                return False
            
            # Check if credentials already exist
            existing_cred = self.db_session.query(TwitterCredential).filter(
                TwitterCredential.founder_id == user_id
            ).first()
            
            if existing_cred:
                # Update existing credentials
                existing_cred.access_token = self._encrypt_token(credentials['access_token'])
                existing_cred.refresh_token = self._encrypt_token(credentials.get('refresh_token'))
                existing_cred.token_type = credentials.get('token_type', 'Bearer')
                existing_cred.expires_at = credentials.get('expires_at')
                existing_cred.scope = credentials.get('scope')
                existing_cred.twitter_user_id = credentials.get('twitter_user_id')
                existing_cred.twitter_username = credentials.get('twitter_username')
                existing_cred.updated_at = datetime.utcnow()
            else:
                # Create new credentials
                new_cred = TwitterCredential(
                    founder_id=user_id,
                    access_token=self._encrypt_token(credentials['access_token']),
                    refresh_token=self._encrypt_token(credentials.get('refresh_token')),
                    token_type=credentials.get('token_type', 'Bearer'),
                    expires_at=credentials.get('expires_at'),
                    scope=credentials.get('scope'),
                    twitter_user_id=credentials.get('twitter_user_id'),
                    twitter_username=credentials.get('twitter_username')
                )
                self.db_session.add(new_cred)
            
            self.db_session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save Twitter credentials: {e}")
            self.db_session.rollback()
            return False
    
    def get_twitter_credentials(self, user_id: str) -> Optional[TwitterCredentials]:
        """Get Twitter credentials for user"""
        try:
            cred = self.db_session.query(TwitterCredential).filter(
                TwitterCredential.founder_id == user_id
            ).first()
            
            if not cred:
                return None
            
            return TwitterCredentials(
                founder_id=str(cred.founder_id),
                access_token=self._decrypt_token(cred.access_token),
                refresh_token=self._decrypt_token(cred.refresh_token),
                token_type=cred.token_type,
                expires_at=cred.expires_at,
                scope=cred.scope,
                twitter_user_id=cred.twitter_user_id,
                twitter_username=cred.twitter_username,
                created_at=cred.created_at,
                updated_at=cred.updated_at
            )
            
        except Exception as e:
            logger.error(f"Failed to get Twitter credentials: {e}")
            return None
    
    def delete_twitter_credentials(self, user_id: str) -> bool:
        """Delete Twitter credentials for user"""
        try:
            cred = self.db_session.query(TwitterCredential).filter(
                TwitterCredential.founder_id == user_id
            ).first()
            
            if cred:
                self.db_session.delete(cred)
                self.db_session.commit()
                return True
            
            return True  # No credentials to delete
            
        except Exception as e:
            logger.error(f"Failed to delete Twitter credentials: {e}")
            self.db_session.rollback()
            return False
    
    def _generate_user_id(self) -> str:
        """Generate unique user ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _hash_password(self, password: str) -> str:
        """Password hashing"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password"""
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    
    def _user_table_to_model(self, user: Founder) -> UserProfileData:
        """Convert database model to Pydantic model"""
        product_info = None
        if user.settings and 'product_info' in user.settings:
            try:
                product_info = ProductInfoData(**user.settings['product_info'])
            except Exception as e:
                logger.warning(f"Failed to parse product info: {e}")
        
        # Ensure settings exists and has default values
        if not user.settings:
            user.settings = {}
        
        return UserProfileData(
            founder_id=str(user.id),
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            company_name=user.company_name,
            role=user.settings.get('role'),
            timezone=user.settings.get('timezone', 'UTC'),
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            product_info=product_info
        )