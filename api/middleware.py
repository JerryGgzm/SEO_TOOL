"""API middleware"""

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any, Tuple
import jwt
from jwt.exceptions import InvalidTokenError
import os
from datetime import datetime, timedelta, UTC
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modules.user_profile import UserProfileService, UserProfileRepository
from modules.twitter_api import TwitterAPIClient
import logging
import random

logger = logging.getLogger(__name__)

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")  # 设置默认值
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security scheme
security = HTTPBearer()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./ideation_db.sqlite')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Token validation cache
_token_validation_cache: Dict[str, Tuple[bool, datetime]] = {}
TOKEN_VALIDATION_INTERVAL = timedelta(minutes=5)  # 5分钟内不重复验证

def should_validate_twitter_token(user_id: str) -> bool:
    """检查是否需要验证Twitter token"""
    if user_id not in _token_validation_cache:
        return True
    
    is_valid, last_validated = _token_validation_cache[user_id]
    if datetime.now(UTC) - last_validated > TOKEN_VALIDATION_INTERVAL:
        return True
    
    return not is_valid  # 如果上次验证失败，需要重新验证

def cache_token_validation(user_id: str, is_valid: bool):
    """缓存令牌验证结果"""
    _token_validation_cache[user_id] = (is_valid, datetime.now(UTC))

def clear_token_cache(user_id: str = None):
    """清除令牌验证缓存"""
    global _token_validation_cache
    if user_id:
        _token_validation_cache.pop(user_id, None)
        logger.info(f"清除用户 {user_id} 的令牌验证缓存")
    else:
        _token_validation_cache.clear()
        logger.info("清除所有令牌验证缓存")

def cleanup_expired_token_cache():
    """清理过期的token验证缓存"""
    global _token_validation_cache
    current_time = datetime.now(UTC)
    expired_users = []
    
    for user_id, (is_valid, last_validated) in _token_validation_cache.items():
        if current_time - last_validated > TOKEN_VALIDATION_INTERVAL * 2:  # 超过2倍间隔时间
            expired_users.append(user_id)
    
    for user_id in expired_users:
        del _token_validation_cache[user_id]
        
    if expired_users:
        logger.info(f"Cleaned up {len(expired_users)} expired token cache entries")

def get_token_cache_status() -> Dict[str, Any]:
    """获取令牌缓存状态"""
    return {
        "cache_size": len(_token_validation_cache),
        "cached_users": list(_token_validation_cache.keys()),
        "cache_data": {
            user_id: {"is_valid": is_valid, "cached_at": cached_at.isoformat()}
            for user_id, (is_valid, cached_at) in _token_validation_cache.items()
        }
    }

class User(BaseModel):
    """User model for authentication"""
    id: str
    username: str
    email: str
    is_active: bool = True
    is_admin: bool = False  # 管理员标志
    access_token: Optional[str] = None
    should_reauth: bool = False  # 标记是否需要重新授权Twitter
    
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
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
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
        # 定期清理过期缓存 (每10次请求清理一次)
        if random.randint(1, 10) == 1:
            cleanup_expired_token_cache()
        
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
                # DEV ONLY: mock user for testing
                if user_id == '11111111-1111-1111-1111-111111111111':
                    logger.info(f"创建mock用户用于测试: {user_id}")
                    return User(
                        id=user_id,
                        username='demo_user',
                        email=f'{user_id}@admin.com',
                        is_active=True,
                        is_admin=True,
                        access_token=None,
                        should_reauth=False
                    )
                logger.error(f"User not found for ID: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
                
            # Get Twitter credentials if available
            access_token = None
            should_reauth = False
            
            try:
                logger.info(f"开始获取用户 {user_id} 的Twitter凭证...")
                twitter_creds = service.repository.get_twitter_credentials(user_id)
                
                if not twitter_creds:
                    logger.info(f"用户 {user_id} 没有Twitter凭证记录")
                    access_token = None
                    should_reauth = True  # 没有凭证，需要授权
                elif not hasattr(twitter_creds, 'access_token') or not twitter_creds.access_token:
                    logger.info(f"用户 {user_id} 的Twitter凭证中没有access_token")
                    access_token = None
                    should_reauth = True  # 没有token，需要授权
                else:
                    access_token = twitter_creds.access_token
                    logger.info(f"用户 {user_id} 找到Twitter access_token，长度: {len(access_token)}")
                    
                    # 优化的Twitter令牌验证 - 使用缓存和时间间隔
                    if access_token:
                        # 检查令牌是否过期（数据库中的过期时间）
                        if twitter_creds.is_expired():
                            logger.info(f"用户 {user_id} 的Twitter令牌已过期，过期时间: {twitter_creds.expires_at}")
                            access_token = None
                            # 标记需要重新授权
                            should_reauth = True
                        elif should_validate_twitter_token(user_id):
                            # 只在必要时进行API验证
                            try:
                                logger.info(f"执行用户 {user_id} 的Twitter令牌API验证 (缓存过期)")
                                twitter_client = TwitterAPIClient(
                                    client_id=os.getenv('TWITTER_CLIENT_ID'),
                                    client_secret=os.getenv('TWITTER_CLIENT_SECRET')
                                )
                                is_valid = twitter_client.auth.validate_user_token(access_token)
                                cache_token_validation(user_id, is_valid)
                                
                                if not is_valid:
                                    logger.error(f"用户 {user_id} 的Twitter令牌验证失败")
                                    access_token = None
                                    # 标记需要重新授权
                                    should_reauth = True
                                else:
                                    logger.info(f"用户 {user_id} 的Twitter令牌验证成功")
                                    should_reauth = False
                                    
                            except Exception as e:
                                logger.error(f"验证用户 {user_id} 的Twitter令牌时发生错误: {e}")
                                cache_token_validation(user_id, False)
                                access_token = None
                                should_reauth = True
                        else:
                            # 使用缓存的验证结果
                            cached_valid, cached_time = _token_validation_cache.get(user_id, (False, datetime.min))
                            if not cached_valid:
                                access_token = None
                                should_reauth = True
                                logger.info(f"用户 {user_id} 使用缓存的Twitter令牌验证结果: 无效 (缓存时间: {cached_time})")
                            else:
                                should_reauth = False
                                logger.info(f"用户 {user_id} 使用缓存的Twitter令牌验证结果: 有效 (缓存时间: {cached_time})")
                    else:
                        should_reauth = False
            except Exception as e:
                logger.error(f"获取用户 {user_id} 的Twitter凭证失败: {e}")
                access_token = None
                should_reauth = True  # 获取凭证失败，需要重新授权
            
            # 简单的管理员判断逻辑 - 可以根据需要修改
            is_admin = user_data.username == 'demo_user' or user_data.email.endswith('@admin.com')
            
            logger.info(f"创建User对象 - id: {user_data.user_id}, username: {user_data.username}, twitter access token: {access_token}")
            return User(
                id=user_data.user_id,
                username=user_data.username,
                email=user_data.email,
                is_active=user_data.is_active,
                is_admin=is_admin,
                access_token=access_token,
                should_reauth=should_reauth
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
        'exp': datetime.now(UTC) + timedelta(hours=24),
        'iat': datetime.now(UTC)
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