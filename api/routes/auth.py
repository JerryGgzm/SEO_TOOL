"""认证路由"""
from fastapi import APIRouter, HTTPException, status, Request, Query
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, EmailStr
import jwt
from datetime import datetime, timedelta
import os
from typing import Optional

from modules.twitter_api.auth import TwitterAuth

router = APIRouter(prefix="/auth", tags=["auth"])

# 数据模型
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    username: str

# 模拟用户数据库
users_db = {}

# TODO: Twitter OAuth状态存储（生产环境应使用Redis或数据库）
oauth_states = {}

def create_access_token(user_id: str) -> str:
    """创建JWT访问令牌"""
    secret_key = os.getenv("SECRET_KEY", "your-secret-key")
    expires_delta = timedelta(hours=24)
    
    expire = datetime.utcnow() + expires_delta
    to_encode = {
        "sub": user_id,
        "exp": expire
    }
    
    return jwt.encode(to_encode, secret_key, algorithm="HS256")

@router.post("/register")
async def register(user_data: UserRegister):
    """用户注册"""
    if user_data.email in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 在实际应用中，这里应该对密码进行哈希处理
    user_id = f"user_{len(users_db) + 1}"
    users_db[user_data.email] = {
        "id": user_id,
        "email": user_data.email,
        "username": user_data.username,
        "password": user_data.password  # 注意：实际应用中应该存储哈希后的密码
    }
    
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "User registered successfully",
            "user_id": user_id
        }
    )

@router.post("/login")
async def login(user_data: UserLogin):
    """用户登录"""
    user = users_db.get(user_data.email)
    if not user or user["password"] != user_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = create_access_token(user["id"])
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Login successful",
            "access_token": access_token,
            "user_id": user["id"]
        }
    )

@router.get("/twitter/authorize")
async def twitter_authorize(user_id: str = Query(..., description="用户ID")):
    """启动Twitter OAuth 2.0授权流程"""
    try:
        client_id = os.getenv('TWITTER_CLIENT_ID')
        client_secret = os.getenv('TWITTER_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Twitter API credentials not configured"
            )
        
        twitter_auth = TwitterAuth(client_id, client_secret)
        
        # 回调URL - 根据你的部署环境调整
        redirect_uri = os.getenv('TWITTER_CALLBACK_URL', 'http://localhost:8000/auth/twitter/callback')
        
        # 获取授权URL和相关参数
        auth_url, state, code_verifier = twitter_auth.get_authorization_url(
            redirect_uri=redirect_uri,
            scopes=['tweet.read', 'tweet.write', 'users.read', 'follows.read', 'offline.access']
        )
        
        # 存储OAuth状态（生产环境应使用更安全的存储方式）
        oauth_states[state] = {
            'user_id': user_id,
            'code_verifier': code_verifier,
            'redirect_uri': redirect_uri,
            'timestamp': datetime.utcnow()
        }
        
        # 重定向到Twitter授权页面
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate Twitter authorization: {str(e)}"
        )

@router.get("/twitter/callback")
async def twitter_callback(
    code: str = Query(..., description="授权码"),
    state: str = Query(..., description="状态参数"),
    error: Optional[str] = Query(None, description="错误信息")
):
    """处理Twitter OAuth回调"""
    try:
        # 检查是否有错误
        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Twitter authorization error: {error}"
            )
        
        # 验证state参数
        if state not in oauth_states:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state parameter"
            )
        
        oauth_state = oauth_states[state]
        user_id = oauth_state['user_id']
        code_verifier = oauth_state['code_verifier']
        redirect_uri = oauth_state['redirect_uri']
        
        # 清理已使用的state
        del oauth_states[state]
        
        # 初始化Twitter认证客户端
        client_id = os.getenv('TWITTER_CLIENT_ID')
        client_secret = os.getenv('TWITTER_CLIENT_SECRET')
        twitter_auth = TwitterAuth(client_id, client_secret)
        
        # 交换授权码获取访问令牌
        token_data = twitter_auth.exchange_code_for_token(
            code=code,
            code_verifier=code_verifier,
            redirect_uri=redirect_uri
        )
        
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code for access token"
            )
        
        # TODO: 存储用户的Twitter访问令牌（实际应用中应存储到数据库）
        # 这里只是示例，你需要根据你的用户系统来实现
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        
        # TODO: 将Twitter访问令牌保存到用户记录中
        users_db[user_id]['twitter_access_token'] = access_token
        users_db[user_id]['twitter_refresh_token'] = refresh_token
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Twitter authorization successful",
                "user_id": user_id,
                "access_token": access_token,
                "token_type": token_data.get('token_type', 'bearer'),
                "expires_in": token_data.get('expires_in'),
                "has_refresh_token": bool(refresh_token)
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process Twitter callback: {str(e)}"
        ) 