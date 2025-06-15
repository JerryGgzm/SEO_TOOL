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
        "exp": datetime.utcnow() + JWT_EXPIRATION
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

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
        service = UserProfileService(data_flow_manager)
        user = await service.register_user(registration)
        
        # Generate JWT token
        token = generate_jwt_token(user.id)
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "User registered successfully",
                "user_id": user.id,
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
        service = UserProfileService(data_flow_manager)
        user = await service.authenticate_user(login_data.email, login_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Generate JWT token
        token = generate_jwt_token(user.id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Login successful",
                "user_id": user.id,
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
        service = UserProfileService(data_flow_manager)
        profile = await service.get_user_profile(current_user.id)
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
    try:
        service = UserProfileService(data_flow_manager)
        success = await service.update_product_info(current_user.id, product_info)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update product info"
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Product information updated successfully",
                "product_info": product_info
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
        service = UserProfileService(data_flow_manager)
        product_info = await service.get_product_info(current_user.id)
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
    """获取Twitter连接状态"""
    try:
        # 从数据库获取Twitter凭证
        from modules.user_profile.repository import UserProfileRepository
        repository = UserProfileRepository(data_flow_manager.db_session)
        service = UserProfileService(repository, data_flow_manager)
        credentials = service.repository.get_twitter_credentials(current_user.id)
        
        if not credentials:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "connected": False,
                    "has_valid_token": False,
                    "message": "Twitter账户未连接"
                }
            )
            
        # 检查令牌是否过期
        is_expired = credentials.is_expired()
        
        # 如果令牌未过期，验证令牌有效性
        if not is_expired:
            try:
                # 使用Twitter API验证令牌
                twitter_client = TwitterAPIClient(
                    client_id=os.getenv('TWITTER_CLIENT_ID'),
                    client_secret=os.getenv('TWITTER_CLIENT_SECRET')
                )
                is_valid = twitter_client.auth.validate_user_token(credentials.access_token)
            except Exception as e:
                is_valid = False
                logger.error(f"验证Twitter令牌失败: {e}")
        else:
            is_valid = False
            
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "connected": True,
                "has_valid_token": is_valid,
                "twitter_username": credentials.twitter_username,
                "expires_at": credentials.expires_at.isoformat() if credentials.expires_at else None,
                "message": "Twitter账户已连接" if is_valid else "Twitter令牌已过期"
            }
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
        auth_url, state, code_verifier = service.get_twitter_auth_url(current_user.id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "auth_url": auth_url,
                "state": state,
                "code_verifier": code_verifier
            }
        )
    except Exception as e:
        logger.error(f"获取Twitter授权URL失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Twitter授权URL失败: {str(e)}"
        )

@router.post("/profile/twitter/callback")
async def twitter_callback(
    code: str = Body(...),
    state: str = Body(...),
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager)
):
    """处理Twitter OAuth回调"""
    try:
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
        service = UserProfileService(data_flow_manager)
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

@router.post("/profile/twitter/revoke")
async def revoke_twitter_token(
    current_user: User = Depends(get_current_user),
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager)
):
    """撤销Twitter访问令牌"""
    try:
        service = UserProfileService(data_flow_manager)
        success = service.revoke_twitter_token(current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="撤销Twitter令牌失败"
            )
            
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Twitter令牌已撤销"
            }
        )
        
    except Exception as e:
        logger.error(f"撤销Twitter令牌失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"撤销Twitter令牌失败: {str(e)}"
        )