"""Data access layer""" 
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text, JSON
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from cryptography.fernet import Fernet
from typing import Optional
import os
import json
from datetime import datetime
import hashlib
import secrets
import bcrypt

from .models import UserProfileData, ProductInfoData, TwitterCredentials, UserRegistrationRequest

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
    
    def __init__(self, db_session: Session, encryption_key: Optional[str] = None):
        self.db_session = db_session
        # Initialize encryption key
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode())
        else:
            # Get from environment variable or generate new key
            key = os.getenv('ENCRYPTION_KEY')
            if not key:
                key = Fernet.generate_key().decode()
                # In actual deployment, this key should be stored securely
                print(f"Generated new encryption key: {key}")
            self.cipher = Fernet(key.encode())
    
    def create_user(self, user_data: UserRegistrationRequest) -> Optional[str]:
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
    
    def save_twitter_credentials(self, user_id: str, credentials: TwitterCredentials) -> bool:
        """Save Twitter authentication credentials (encrypted)"""
        try:
            # Encrypt sensitive information
            encrypted_access_token = self.cipher.encrypt(credentials.access_token.encode()).decode()
            encrypted_refresh_token = None
            if credentials.refresh_token:
                encrypted_refresh_token = self.cipher.encrypt(credentials.refresh_token.encode()).decode()
            
            # Check if already exists
            existing = self.db_session.query(TwitterCredentialsTable).filter(
                TwitterCredentialsTable.user_id == user_id
            ).first()
            
            if existing:
                # Update existing record
                existing.encrypted_access_token = encrypted_access_token
                existing.encrypted_refresh_token = encrypted_refresh_token
                existing.expires_at = credentials.expires_at
                existing.scope = credentials.scope
                existing.twitter_user_id = credentials.twitter_user_id
                existing.twitter_username = credentials.twitter_username
                existing.updated_at = datetime.utcnow()
            else:
                # Create new record
                cred = TwitterCredentialsTable(
                    user_id=user_id,
                    encrypted_access_token=encrypted_access_token,
                    encrypted_refresh_token=encrypted_refresh_token,
                    token_type=credentials.token_type,
                    expires_at=credentials.expires_at,
                    scope=credentials.scope,
                    twitter_user_id=credentials.twitter_user_id,
                    twitter_username=credentials.twitter_username
                )
                self.db_session.add(cred)
            
            self.db_session.commit()
            return True
            
        except Exception as e:
            self.db_session.rollback()
            print(f"Failed to save Twitter credentials: {e}")
            return False
    
    def get_twitter_credentials(self, user_id: str) -> Optional[TwitterCredentials]:
        """Get Twitter authentication credentials (decrypted)"""
        cred = self.db_session.query(TwitterCredentialsTable).filter(
            TwitterCredentialsTable.user_id == user_id
        ).first()
        
        if not cred:
            return None
        
        try:
            # Decrypt sensitive information
            access_token = self.cipher.decrypt(cred.encrypted_access_token.encode()).decode()
            refresh_token = None
            if cred.encrypted_refresh_token:
                refresh_token = self.cipher.decrypt(cred.encrypted_refresh_token.encode()).decode()
            
            return TwitterCredentials(
                user_id=user_id,
                access_token=access_token,
                refresh_token=refresh_token,
                token_type=cred.token_type,
                expires_at=cred.expires_at,
                scope=cred.scope,
                twitter_user_id=cred.twitter_user_id,
                twitter_username=cred.twitter_username,
                created_at=cred.created_at,
                updated_at=cred.updated_at
            )
            
        except Exception as e:
            print(f"Failed to decrypt Twitter credentials: {e}")
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