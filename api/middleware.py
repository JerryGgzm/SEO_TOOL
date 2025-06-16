"""API middleware"""

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import jwt
from jwt.exceptions import InvalidTokenError
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modules.user_profile import UserProfileService, UserProfileRepository
from modules.twitter_api import TwitterAPIClient
import logging

logger = logging.getLogger(__name__)

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")  # 设置默认值
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security scheme
security = HTTPBearer()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./test.db')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class User(BaseModel):
    """User model"""
    id: str
    username: str
    email: str
    is_active: bool = True
    twitter_access_token: Optional[str] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    """Token model"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Token data model"""
    username: Optional[str] = None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> TokenData:
    """Verify token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(username=username)
        return token_data
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        logger.info(f"收到认证token (first 50 chars): {token[:50]}...")
        logger.info(f"使用的SECRET_KEY (first 10 chars): {SECRET_KEY[:10]}...")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"解码后的JWT payload: {payload}")
        
        # 检查两种可能的字段名：sub（标准）和 user_id（我们使用的）
        user_id = payload.get("sub") or payload.get("user_id")
        logger.info(f"提取的user_id: {user_id}")
        
        if user_id is None:
            logger.error(f"Token payload missing user_id: {payload}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
            
        # Get user from database
        db = SessionLocal()
        try:
            from database import DataFlowManager
            # Create a data flow manager with the database session
            data_flow_manager = DataFlowManager(db)
            
            service = UserProfileService(UserProfileRepository(db), data_flow_manager)
            logger.info(f"Looking for user with ID: {user_id}")
            user_data = service.get_user_profile(user_id)
            logger.info(f"Found user data: {user_data}")
            if not user_data:
                logger.error(f"User not found for ID: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
                
            # Get Twitter credentials if available
            twitter_access_token = None
            try:
                twitter_creds = service.repository.get_twitter_credentials(user_id)
                if twitter_creds and hasattr(twitter_creds, 'access_token'):
                    twitter_access_token = twitter_creds.access_token
                    
                    # 验证Twitter令牌
                    if twitter_access_token:
                        try:
                            twitter_client = TwitterAPIClient(
                                client_id=os.getenv('TWITTER_CLIENT_ID'),
                                client_secret=os.getenv('TWITTER_CLIENT_SECRET')
                            )
                            is_valid = twitter_client.auth.validate_user_token(twitter_access_token)
                            if not is_valid:
                                twitter_access_token = None
                        except Exception as e:
                            logger.error(f"验证Twitter令牌失败: {e}")
                            twitter_access_token = None
            except Exception as e:
                logger.error(f"获取Twitter凭证失败: {e}")
                twitter_access_token = None
            
            logger.info(f"创建User对象 - id: {user_data.user_id}, username: {user_data.username}")
            return User(
                id=user_data.user_id,
                username=user_data.username,
                email=user_data.email,
                is_active=user_data.is_active,
                twitter_access_token=twitter_access_token
            )
        finally:
            db.close()
            
    except InvalidTokenError as e:
        logger.error(f"Invalid token error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Optional authentication function for endpoints that don't require authentication
def get_optional_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    """Get optional current user (allows anonymous access)"""
    if credentials is None:
        return None
    
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None

def get_user_service() -> UserProfileService:
    """Get user service instance"""
    db_session = SessionLocal()
    repository = UserProfileRepository(db_session)
    from database import DataFlowManager
    data_flow_manager = DataFlowManager(db_session)
    return UserProfileService(repository, data_flow_manager)

def generate_jwt_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return {'error': 'Token has expired'}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token'}

def require_auth(f):
    """Authentication decorator for FastAPI"""
    def decorated_function(*args, **kwargs):
        # Note: This decorator is for Flask compatibility
        # For FastAPI, use Depends(get_current_user) instead
        # This function is kept for backward compatibility
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def get_twitter_client() -> TwitterAPIClient:
    """Get configured Twitter API client"""
    client_id = os.getenv('TWITTER_CLIENT_ID')
    client_secret = os.getenv('TWITTER_CLIENT_SECRET')
    if not client_id or not client_secret:
        raise ValueError("Twitter API credentials not configured")
    return TwitterAPIClient(client_id, client_secret) 