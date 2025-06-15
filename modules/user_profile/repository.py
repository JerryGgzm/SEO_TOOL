"""Data access layer""" 
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text, JSON
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from cryptography.fernet import Fernet
from typing import Optional, Dict, Any
import os
import json
from datetime import datetime
import hashlib
import secrets
import bcrypt
import base64
import logging

from .models import UserProfileData, ProductInfoData, TwitterCredentials, UserRegistration

logger = logging.getLogger(__name__)

Base = declarative_base()

class UserProfileTable(Base):
    """User profile table"""
    __tablename__ = 'user_profiles'
    
    user_id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    company_name = Column(String(100))
    role = Column(String(50))
    timezone = Column(String(50), default='UTC')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    product_info = Column(JSON)  # Store serialized product information

class TwitterCredentialsTable(Base):
    """Twitter authentication credentials table"""
    __tablename__ = 'twitter_credentials'
    
    user_id = Column(String(36), primary_key=True)
    encrypted_access_token = Column(Text, nullable=False)
    encrypted_refresh_token = Column(Text)
    token_type = Column(String(20), default='Bearer')
    expires_at = Column(DateTime)
    scope = Column(String(500))
    twitter_user_id = Column(String(50))
    twitter_username = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserProfileRepository:
    """User profile data access layer"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.model_class = TwitterCredentialsTable
        
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
            
            user = UserProfileTable(
                user_id=user_id,
                email=user_data.email,
                username=user_data.username,
                password_hash=password_hash,
                full_name=user_data.full_name,
                company_name=user_data.company_name
            )
            
            self.db_session.add(user)
            self.db_session.commit()
            return user_id
            
        except IntegrityError:
            self.db_session.rollback()
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[UserProfileData]:
        """Get user information by user ID"""
        user = self.db_session.query(UserProfileTable).filter(
            UserProfileTable.user_id == user_id,
            UserProfileTable.is_active == True
        ).first()
        
        if not user:
            return None
            
        return self._user_table_to_model(user)
    
    def get_user_by_email(self, email: str) -> Optional[UserProfileData]:
        """Get user information by email"""
        user = self.db_session.query(UserProfileTable).filter(
            UserProfileTable.email == email,
            UserProfileTable.is_active == True
        ).first()
        
        if not user:
            return None
            
        return self._user_table_to_model(user)
    
    def verify_password(self, email: str, password: str) -> Optional[str]:
        """Verify user password, return user ID"""
        user = self.db_session.query(UserProfileTable).filter(
            UserProfileTable.email == email,
            UserProfileTable.is_active == True
        ).first()
        
        if not user:
            return None
            
        if self._verify_password(password, user.password_hash):
            return user.user_id
        return None
    
    def update_product_info(self, user_id: str, product_info: ProductInfoData) -> bool:
        """Update user product information"""
        try:
            user = self.db_session.query(UserProfileTable).filter(
                UserProfileTable.user_id == user_id
            ).first()
            
            if not user:
                return False
            
            user.product_info = product_info.dict()
            user.updated_at = datetime.utcnow()
            
            self.db_session.commit()
            return True
            
        except Exception:
            self.db_session.rollback()
            return False
    
    def save_twitter_credentials(self, user_id: str, credentials: Dict[str, Any]) -> bool:
        """保存Twitter凭证"""
        try:
            # 加密令牌
            encrypted_access_token = self._encrypt_token(credentials.get('access_token'))
            encrypted_refresh_token = self._encrypt_token(credentials.get('refresh_token'))
            
            # 创建或更新记录
            existing = self.db_session.query(self.model_class).filter_by(user_id=user_id).first()
            if existing:
                existing.encrypted_access_token = encrypted_access_token
                existing.encrypted_refresh_token = encrypted_refresh_token
                existing.token_type = credentials.get('token_type', 'Bearer')
                existing.expires_at = credentials.get('expires_at')
                existing.scope = credentials.get('scope')
                existing.twitter_user_id = credentials.get('twitter_user_id')
                existing.twitter_username = credentials.get('twitter_username')
                existing.updated_at = datetime.utcnow()
            else:
                new_credentials = self.model_class(
                    user_id=user_id,
                    encrypted_access_token=encrypted_access_token,
                    encrypted_refresh_token=encrypted_refresh_token,
                    token_type=credentials.get('token_type', 'Bearer'),
                    expires_at=credentials.get('expires_at'),
                    scope=credentials.get('scope'),
                    twitter_user_id=credentials.get('twitter_user_id'),
                    twitter_username=credentials.get('twitter_username')
                )
                self.db_session.add(new_credentials)
            
            self.db_session.commit()
            return True
            
        except Exception as e:
            logger.error(f"保存Twitter凭证失败: {e}")
            self.db_session.rollback()
            return False
    
    def get_twitter_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取Twitter凭证"""
        try:
            credentials = self.db_session.query(self.model_class).filter_by(user_id=user_id).first()
            if not credentials:
                return None
            
            # 解密令牌
            access_token = self._decrypt_token(credentials.encrypted_access_token)
            refresh_token = self._decrypt_token(credentials.encrypted_refresh_token)
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': credentials.token_type,
                'expires_at': credentials.expires_at,
                'scope': credentials.scope,
                'twitter_user_id': credentials.twitter_user_id,
                'twitter_username': credentials.twitter_username,
                'created_at': credentials.created_at,
                'updated_at': credentials.updated_at
            }
            
        except Exception as e:
            logger.error(f"获取Twitter凭证失败: {e}")
            return None
    
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
    
    def _user_table_to_model(self, user: UserProfileTable) -> UserProfileData:
        """Convert database model to Pydantic model"""
        product_info = None
        if user.product_info:
            try:
                product_info = ProductInfoData(**user.product_info)
            except Exception:
                pass  # If product info format has issues, ignore
        
        return UserProfileData(
            user_id=user.user_id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            company_name=user.company_name,
            role=user.role,
            timezone=user.timezone,
            created_at=user.created_at,
            updated_at=user.updated_at,
            is_active=user.is_active,
            product_info=product_info
        )