"""User Profile API Routes

This module implements the FastAPI routes for user profile management,
handling authentication, profile updates and Twitter integration.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, Body
from fastapi.responses import JSONResponse
import logging
from datetime import datetime, timedelta
import jwt
import os
import secrets
import base64
import hashlib
from urllib.parse import urlencode
import requests

from database import get_data_flow_manager, DataFlowManager
from api.middleware import get_current_user, User

from modules.user_profile.service import UserProfileService
from modules.user_profile.models import (
    UserRegistration, UserLogin, ProductInfoData,
    TwitterAuthResponse, TwitterStatus
)
from modules.twitter_api import TwitterAPIClient

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/user", tags=["user-profile"])

# JWT configuration
JWT_SECRET = os.getenv("SECRET_KEY", "your-secret-key-here")  # 使用环境变量
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = timedelta(days=1)

def generate_jwt_token(user_id: str) -> str:
    """Generate JWT token for user"""
    payload = {
        "user_id": user_id,
        "sub": user_id,  # 添加标准的sub字段
        "exp": datetime.utcnow() + JWT_EXPIRATION,
        "iat": datetime.utcnow()
    }
    logger.info(f"生成JWT token - user_id: {user_id}")
    logger.info(f"JWT payload: {payload}")
    logger.info(f"JWT secret (first 10 chars): {JWT_SECRET[:10]}...")
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    logger.info(f"生成的token (first 50 chars): {token[:50]}...")
    return token

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@router.post("/register")
async def register(
    registration: UserRegistration = Body(...),
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager)
):
    """Register a new user"""
    try:
        # 创建repository实例
        from modules.user_profile.repository import UserProfileRepository
        repository = UserProfileRepository(data_flow_manager.db_session)
        service = UserProfileService(repository, data_flow_manager)
        result, message = service.register_user(registration)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        # message is the user_id when successful
        user_id = message
        
        # Generate JWT token
        token = generate_jwt_token(user_id)
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "User registered successfully",
                "user_id": user_id,
                "token": token
            }
        )
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed"
        )

@router.post("/login")
async def login(
    login_data: UserLogin = Body(...),
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager)
):
    """Login user"""
    try:
        # 创建repository实例
        from modules.user_profile.repository import UserProfileRepository
        repository = UserProfileRepository(data_flow_manager.db_session)
        service = UserProfileService(repository, data_flow_manager)
        user_id = service.authenticate_user(login_data)
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Generate JWT token
        token = generate_jwt_token(user_id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Login successful",
                "user_id": user_id,
                "token": token
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user),
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager)
):
    """Get user profile"""
    try:
        # 创建repository实例
        from modules.user_profile.repository import UserProfileRepository
        repository = UserProfileRepository(data_flow_manager.db_session)
        service = UserProfileService(repository, data_flow_manager)
        profile = service.get_user_profile(current_user.id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Profile retrieved successfully",
                "profile": profile
            }
        )
    except Exception as e:
        logger.error(f"Failed to get profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile"
        )

@router.put("/profile/product")
async def update_product_info(
    product_info: ProductInfoData = Body(...),
    current_user: User = Depends(get_current_user),
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager)
):
    """Update product information"""
    logger.info(f"update_product_info: {product_info}")
    try:
        # 创建repository实例
        from modules.user_profile.repository import UserProfileRepository
        repository = UserProfileRepository(data_flow_manager.db_session)
        service = UserProfileService(repository, data_flow_manager)
        success = service.update_product_info(current_user.id, product_info)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update product info"
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Product information updated successfully",
                "product_info": product_info.dict()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update product info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product information"
        )

@router.get("/profile/product")
async def get_product_info(
    current_user: User = Depends(get_current_user),
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager)
):
    """Get product information"""
    try:
        # 创建repository实例
        from modules.user_profile.repository import UserProfileRepository
        repository = UserProfileRepository(data_flow_manager.db_session)
        service = UserProfileService(repository, data_flow_manager)
        product_info = service.get_product_info(current_user.id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Product information retrieved successfully",
                "product_info": product_info
            }
        )
    except Exception as e:
        logger.error(f"Failed to get product info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve product information"
        )

@router.get("/profile/twitter/status")
async def get_twitter_status(
    current_user: User = Depends(get_current_user),
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager)
):
    """获取Twitter连接状态 - 优化版本"""
    try:
        # 使用service中的优化方法，避免重复API调用
        from modules.user_profile.repository import UserProfileRepository
        repository = UserProfileRepository(data_flow_manager.db_session)
        service = UserProfileService(repository, data_flow_manager)
        
        # 使用优化的连接状态检查方法
        status_info = service.get_twitter_connection_status(current_user.id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=status_info
        )
        
    except Exception as e:
        logger.error(f"获取Twitter状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取Twitter状态失败"
        )

@router.get("/profile/twitter/auth_url")
async def get_twitter_auth_url(
    current_user: User = Depends(get_current_user),
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager)
):
    """获取Twitter授权URL"""
    try:
        from modules.user_profile.repository import UserProfileRepository
        repository = UserProfileRepository(data_flow_manager.db_session)
        service = UserProfileService(repository, data_flow_manager)
        logger.info(f"current_user.id: {current_user.id}")
        auth_url, state = service.get_twitter_auth_url(current_user.id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "auth_url": auth_url,
                "state": state
                # 注意：出于安全考虑，不返回code_verifier
            }
        )
    except Exception as e:
        logger.error(f"get_twitter_auth_url获取Twitter授权URL失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"get_twitter_auth_url获取Twitter授权URL失败: {str(e)}"
        )

@router.post("/profile/twitter/callback")
async def twitter_callback(
    request_data: dict = Body(...),
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager)
):
    """处理Twitter OAuth回调"""
    try:
        code = request_data.get('code')
        state = request_data.get('state')
        
        if not code or not state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required parameters: code and state"
            )
        
        from modules.user_profile.repository import UserProfileRepository
        repository = UserProfileRepository(data_flow_manager.db_session)
        service = UserProfileService(repository, data_flow_manager)
        token_info = service.handle_twitter_callback(code, state)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Twitter账户连接成功",
                "twitter_username": token_info.get("twitter_username")
            }
        )
        
    except Exception as e:
        logger.error(f"处理Twitter回调失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"处理Twitter回调失败: {str(e)}"
        )

@router.post("/profile/twitter/refresh")
async def refresh_twitter_token(
    current_user: User = Depends(get_current_user),
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager)
):
    """刷新Twitter访问令牌"""
    try:
        # 创建repository实例
        from modules.user_profile.repository import UserProfileRepository
        repository = UserProfileRepository(data_flow_manager.db_session)
        service = UserProfileService(repository, data_flow_manager)
        token_info = service.refresh_twitter_token(current_user.id)
        
        if not token_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法刷新Twitter令牌，请重新授权"
            )
            
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Twitter令牌刷新成功",
                "expires_at": token_info["expires_at"].isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"刷新Twitter令牌失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刷新Twitter令牌失败: {str(e)}"
        )

@router.get("/profile/twitter/cache-status")
async def get_twitter_cache_status(
    current_user: User = Depends(get_current_user)
):
    """获取Twitter token验证缓存状态 - 调试用"""
    try:
        from api.middleware import get_token_cache_status
        cache_status = get_token_cache_status()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Token缓存状态获取成功",
                "user_id": current_user.id,
                "cache_status": cache_status
            }
        )
        
    except Exception as e:
        logger.error(f"获取缓存状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取缓存状态失败"
        )

@router.post("/profile/twitter/revoke")
async def revoke_twitter_token(
    current_user: User = Depends(get_current_user),
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager)
):
    """撤销Twitter访问令牌"""
    try:
        # 创建repository实例
        from modules.user_profile.repository import UserProfileRepository
        repository = UserProfileRepository(data_flow_manager.db_session)
        service = UserProfileService(repository, data_flow_manager)
        success = service.revoke_twitter_token(current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="撤销Twitter令牌失败"
            )
            
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Twitter令牌已撤销，缓存已清理"
            }
        )
        
    except Exception as e:
        logger.error(f"撤销Twitter令牌失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"撤销Twitter令牌失败: {str(e)}"
        )

@router.get("/profile/twitter/debug")
async def debug_twitter_credentials(
    current_user: User = Depends(get_current_user),
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager)
):
    """调试Twitter凭证状态 - 详细信息"""
    try:
        from modules.user_profile.repository import UserProfileRepository
        repository = UserProfileRepository(data_flow_manager.db_session)
        
        # 直接从数据库获取Twitter凭证
        credentials = repository.get_twitter_credentials(current_user.id)
        
        debug_info = {
            "user_id": current_user.id,
            "username": current_user.username,
            "middleware_access_token": current_user.access_token,
            "database_credentials_found": credentials is not None
        }
        
        if credentials:
            debug_info.update({
                "has_access_token": bool(credentials.access_token),
                "access_token_length": len(credentials.access_token) if credentials.access_token else 0,
                "access_token_preview": credentials.access_token[:20] + "..." if credentials.access_token else None,
                "has_refresh_token": bool(credentials.refresh_token),
                "token_type": credentials.token_type,
                "expires_at": credentials.expires_at.isoformat() if credentials.expires_at else None,
                "is_expired": credentials.is_expired(),
                "created_at": credentials.created_at.isoformat() if credentials.created_at else None,
                "updated_at": credentials.updated_at.isoformat() if credentials.updated_at else None,
                "twitter_user_id": credentials.twitter_user_id,
                "twitter_username": credentials.twitter_username,
                "scope": credentials.scope
            })
        
        # 检查缓存状态
        try:
            from api.middleware import get_token_cache_status
            cache_status = get_token_cache_status()
            debug_info["cache_status"] = cache_status
        except Exception as e:
            debug_info["cache_error"] = str(e)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Twitter凭证调试信息",
                "debug_info": debug_info
            }
        )
        
    except Exception as e:
        logger.error(f"调试Twitter凭证失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"调试失败: {str(e)}"
        )

@router.get("/profile/twitter/diagnose-saving")
async def diagnose_twitter_credentials_saving(
    current_user: User = Depends(get_current_user),
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager)
):
    """诊断Twitter凭证保存系统 - 深度检查"""
    try:
        from modules.user_profile.repository import UserProfileRepository
        repository = UserProfileRepository(data_flow_manager.db_session)
        service = UserProfileService(repository, data_flow_manager)
        
        # 运行诊断
        diagnosis = service.diagnose_twitter_credentials_saving(current_user.id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Twitter凭证保存系统诊断完成",
                "diagnosis": diagnosis
            }
        )
        
    except Exception as e:
        logger.error(f"Twitter凭证保存诊断失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"诊断失败: {str(e)}"
        )

@router.get("/profile/twitter/reauth-check")
async def check_reauth_needed(
    current_user: User = Depends(get_current_user),
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager)
):
    """检查是否需要重新授权Twitter"""
    try:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "needs_reauth": current_user.should_reauth,
                "has_access_token": bool(current_user.access_token),
                "user_id": current_user.id,
                "message": "需要重新授权Twitter账户" if current_user.should_reauth else "Twitter授权正常",
                "access_token": current_user.access_token
            }
        )
        
    except Exception as e:
        logger.error(f"检查重新授权状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="检查授权状态失败"
        )

@router.post("/profile/twitter/start-reauth")
async def start_twitter_reauth(
    current_user: User = Depends(get_current_user),
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager)
):
    """开始Twitter重新授权流程"""
    try:
        # 如果用户不需要重新授权，返回当前状态
        if not current_user.should_reauth and current_user.access_token:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message": "用户已授权，无需重新授权",
                    "needs_reauth": False
                }
            )
        
        # 清除现有的无效凭证
        from modules.user_profile.repository import UserProfileRepository
        repository = UserProfileRepository(data_flow_manager.db_session)
        service = UserProfileService(repository, data_flow_manager)
        
        # 删除旧的凭证
        repository.delete_twitter_credentials(current_user.id)
        
        # 清除令牌验证缓存
        try:
            from api.middleware import clear_token_cache
            clear_token_cache(current_user.id)
        except ImportError:
            pass
        
        # 生成新的授权URL
        auth_url, state = service.get_twitter_auth_url(current_user.id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "重新授权流程已启动",
                "auth_url": auth_url,
                "state": state,
                "needs_reauth": True,
                "instructions": "请访问提供的URL完成Twitter重新授权"
            }
        )
        
    except Exception as e:
        logger.error(f"启动重新授权失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动重新授权失败: {str(e)}"
        )