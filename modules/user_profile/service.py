"""User profile service logic""" 
from typing import Optional, Tuple, Dict, Any
import requests
from requests_oauthlib import OAuth2Session
from urllib.parse import urlencode
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
import os
import time

from .repository import UserProfileRepository
from .models import UserProfileData, ProductInfoData, TwitterCredentials, UserRegistration, UserLogin
from database.dataflow_manager import DataFlowManager
from modules.twitter_api import TwitterAPIClient

class TwitterOAuthError(Exception):
    """Twitter OAuth related exception"""
    pass

class UserProfileService:
    """User profile service"""
    
    def __init__(self, repository: UserProfileRepository, data_flow_manager: DataFlowManager):
        self.repository = repository
        self.data_flow_manager = data_flow_manager
        self.twitter_client_id = os.getenv('TWITTER_CLIENT_ID')
        self.twitter_client_secret = os.getenv('TWITTER_CLIENT_SECRET')
        self.twitter_redirect_uri = os.getenv('TWITTER_REDIRECT_URI', 'http://localhost:8000/api/user/profile/twitter/callback')
        
        if not self.twitter_client_id or not self.twitter_client_secret:
            raise ValueError("Twitter API credentials not configured")
    
    def register_user(self, user_data: UserRegistration) -> Tuple[bool, Optional[str]]:
        """User registration"""
        # Check if email already exists
        existing_user = self.repository.get_user_by_email(user_data.email)
        if existing_user:
            return False, "Email already registered"
        
        user_id = self.repository.create_user(user_data)
        if user_id:
            return True, user_id
        else:
            return False, "Registration failed, username may already be taken"
    
    def authenticate_user(self, login_data: UserLogin) -> Optional[str]:
        """User authentication login"""
        return self.repository.verify_password(login_data.email, login_data.password)
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfileData]:
        """Get user profile"""
        return self.repository.get_user_by_id(user_id)
    
    def get_product_info(self, user_id: str) -> Optional[ProductInfoData]:
        """Get product information"""
        user = self.repository.get_user_by_id(user_id)
        return user.product_info if user else None
    
    def update_product_info(self, user_id: str, product_info: ProductInfoData) -> bool:
        """Update product information"""
        return self.repository.update_product_info(user_id, product_info)
    
    def get_twitter_auth_url(self, user_id: str) -> Tuple[str, str]:
        """获取Twitter授权URL"""
        try:
            twitter_client = TwitterAPIClient(
                client_id=self.twitter_client_id,
                client_secret=self.twitter_client_secret
            )
            
            # 生成授权URL和PKCE参数
            auth_url, state, code_verifier = twitter_client.auth.get_authorization_url(
                redirect_uri=self.twitter_redirect_uri,
                scopes=['tweet.read', 'users.read', 'follows.read', 'follows.write', 'offline.access']
            )
            
            # 存储code_verifier（安全：不发送给客户端）
            self._store_code_verifier(state, code_verifier, user_id)
            
            # 只返回auth_url和state给客户端，不返回code_verifier
            return auth_url, state
            
        except Exception as e:
            raise TwitterOAuthError(f"Failed to generate Twitter auth URL: {str(e)}")
    
    def handle_twitter_callback(self, code: str, state: str) -> Dict[str, Any]:
        """处理Twitter OAuth回调"""
        try:
            # 获取code_verifier
            code_verifier = self._get_code_verifier(state)
            if not code_verifier:
                raise TwitterOAuthError("Invalid state parameter")
            
            # 交换访问令牌
            twitter_client = TwitterAPIClient(
                client_id=self.twitter_client_id,
                client_secret=self.twitter_client_secret
            )
            
            token_info = twitter_client.auth.exchange_code_for_token(
                code=code,
                code_verifier=code_verifier,
                redirect_uri=self.twitter_redirect_uri
            )
            
            if not token_info:
                raise TwitterOAuthError("Failed to exchange code for token")
            
            # 获取用户信息
            user_info_response = requests.get(
                "https://api.x.com/2/users/me",
                headers={"Authorization": f"Bearer {token_info['access_token']}"}
            )
            user_info_response.raise_for_status()
            user_info = user_info_response.json()
            
            # 清理code_verifier
            self._remove_code_verifier(state)
            
            return {
                "access_token": token_info["access_token"],
                "refresh_token": token_info.get("refresh_token"),
                "expires_at": datetime.utcnow() + timedelta(seconds=token_info.get("expires_in", 7200)),
                "twitter_user_id": user_info.get("data", {}).get("id"),
                "twitter_username": user_info.get("data", {}).get("username")
            }
            
        except Exception as e:
            raise TwitterOAuthError(f"Failed to handle Twitter callback: {str(e)}")
    
    def refresh_twitter_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """刷新Twitter访问令牌"""
        try:
            credentials = self.repository.get_twitter_credentials(user_id)
            if not credentials or not credentials.refresh_token:
                return None
            
            twitter_client = TwitterAPIClient(
                client_id=self.twitter_client_id,
                client_secret=self.twitter_client_secret
            )
            
            token_info = twitter_client.auth.refresh_token(credentials.refresh_token)
            if not token_info:
                return None
            
            # 更新凭证
            credentials.access_token = token_info['access_token']
            credentials.refresh_token = token_info.get('refresh_token', credentials.refresh_token)
            credentials.expires_at = datetime.utcnow() + timedelta(seconds=token_info.get('expires_in', 7200))
            credentials.updated_at = datetime.utcnow()
            
            self.repository.save_twitter_credentials(user_id, credentials)
            
            return {
                "access_token": credentials.access_token,
                "refresh_token": credentials.refresh_token,
                "expires_at": credentials.expires_at
            }
            
        except Exception as e:
            logger.error(f"Failed to refresh Twitter token: {e}")
            return None
    
    def revoke_twitter_token(self, user_id: str) -> bool:
        """撤销Twitter访问令牌"""
        try:
            credentials = self.repository.get_twitter_credentials(user_id)
            if not credentials:
                return True
            
            twitter_client = TwitterAPIClient(
                client_id=self.twitter_client_id,
                client_secret=self.twitter_client_secret
            )
            
            # 撤销访问令牌
            if credentials.access_token:
                twitter_client.auth.revoke_token(credentials.access_token)
            
            # 撤销刷新令牌
            if credentials.refresh_token:
                twitter_client.auth.revoke_token(credentials.refresh_token)
            
            # 删除凭证
            self.repository.delete_twitter_credentials(user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke Twitter token: {e}")
            return False
    
    # 改进的临时存储实现
    _code_verifiers = {}
    
    def _store_code_verifier(self, state: str, code_verifier: str, user_id: str):
        """安全存储code_verifier，包含过期时间"""
        self._code_verifiers[state] = {
            'code_verifier': code_verifier,
            'user_id': user_id,
            'expires_at': time.time() + 600  # 10分钟过期
        }
        # 清理过期的验证码
        self._cleanup_expired_verifiers()
    
    def _get_code_verifier(self, state: str) -> Optional[str]:
        """获取code_verifier并验证是否过期"""
        data = self._code_verifiers.get(state)
        if not data:
            return None
        
        # 检查是否过期
        if time.time() > data['expires_at']:
            self._code_verifiers.pop(state, None)
            return None
            
        return data['code_verifier']
    
    def _remove_code_verifier(self, state: str):
        """删除code_verifier"""
        self._code_verifiers.pop(state, None)
    
    def _cleanup_expired_verifiers(self):
        """清理过期的code_verifier"""
        current_time = time.time()
        expired_states = [
            state for state, data in self._code_verifiers.items()
            if current_time > data['expires_at']
        ]
        for state in expired_states:
            self._code_verifiers.pop(state, None)