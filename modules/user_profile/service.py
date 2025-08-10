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
import logging

from .repository import UserProfileRepository
from .models import UserProfileData, ProductInfoData, TwitterCredentials, UserRegistration, UserLogin
from database.dataflow_manager import DataFlowManager
from modules.twitter_api import TwitterAPIClient

logger = logging.getLogger(__name__)

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
    
    def get_user_profile(self, founder_id: str) -> Optional[UserProfileData]:
        """Get user profile"""
        return self.repository.get_user_by_id(founder_id)
    
    def get_product_info(self, founder_id: str) -> Optional[ProductInfoData]:
        """Get product information"""
        user = self.repository.get_user_by_id(founder_id)
        return user.product_info if user else None
    
    def update_product_info(self, founder_id: str, product_info: ProductInfoData) -> bool:
        """Update product information"""
        return self.repository.update_product_info(founder_id, product_info)
    
    def get_twitter_access_token(self, founder_id: str) -> Optional[str]:
        """Get Twitter access token for user"""
        try:
            credentials = self.repository.get_twitter_credentials(founder_id)
            if not credentials:
                logger.warning(f"No Twitter credentials found for user {founder_id}")
                return None
            
            if credentials.is_expired():
                logger.warning(f"Twitter credentials expired for user {founder_id}")
                return None
            
            return credentials.access_token
        except Exception as e:
            logger.error(f"Failed to get Twitter access token for user {founder_id}: {e}")
            return None
    
    def get_twitter_auth_url(self, founder_id: str) -> Tuple[str, str]:
        """获取Twitter授权URL"""
        try:
            twitter_client = TwitterAPIClient(
                client_id=self.twitter_client_id,
                client_secret=self.twitter_client_secret
            )
            
            # 生成授权URL和PKCE参数
            auth_url, state, code_verifier = twitter_client.auth.get_authorization_url(
                redirect_uri=self.twitter_redirect_uri,
                scopes=['tweet.read', 'tweet.write', 'users.read', 'follows.read', 'follows.write', 'offline.access']
            )
            
            # 存储code_verifier（安全：不发送给客户端）
            self._store_code_verifier(state, code_verifier, founder_id)
            
            # 只返回auth_url和state给客户端，不返回code_verifier
            return auth_url, state
            
        except Exception as e:
            raise TwitterOAuthError(f"Failed to generate Twitter auth URL: {str(e)}")
    
    def handle_twitter_callback(self, code: str, state: str) -> Dict[str, Any]:
        """处理Twitter OAuth回调"""
        try:
            # 获取code_verifier和user_id
            verifier_data = self._get_code_verifier_data(state)
            if not verifier_data:
                raise TwitterOAuthError("Invalid state parameter")
            
            code_verifier = verifier_data['code_verifier']
            founder_id = verifier_data['founder_id']
            
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
            
            # 获取用户信息 - 优化版本，减少API调用
            user_info = None
            try:
                # 只尝试一次API调用，如果失败就使用默认值
                logger.info("尝试获取Twitter用户信息...")
                user_info = twitter_client._make_request(
                    twitter_client.endpoints.GET_ME,
                    token_info['access_token']
                )
                logger.info(f"成功获取Twitter用户信息: {user_info.get('data', {}).get('username')}")
                
            except Exception as e:
                logger.warning(f"获取Twitter用户信息失败，使用默认值: {e}")
                # 不再进行重试，直接使用默认信息以避免429错误
                user_info = {
                    "data": {
                        "id": "temp_" + str(int(time.time())),  # 临时ID
                        "username": "twitter_user_" + founder_id[:8]  # 基于用户ID的临时用户名
                    }
                }
                logger.info("使用临时用户信息继续OAuth流程")

            # 确保user_info始终有值
            if user_info is None or not user_info.get("data"):
                logger.warning("user_info无效，使用fallback值")
                user_info = {
                    "data": {
                        "id": "fallback_" + str(int(time.time())),
                        "username": "twitter_user_" + founder_id[:8]
                    }
                }
            
            # 准备保存的凭证数据
            credentials_data = {
                "access_token": token_info["access_token"],
                "refresh_token": token_info.get("refresh_token"),
                "token_type": "Bearer",
                "expires_at": datetime.utcnow() + timedelta(seconds=token_info.get("expires_in", 7200)),
                "scope": token_info.get("scope"),
                "twitter_user_id": user_info.get("data", {}).get("id"),
                "twitter_username": user_info.get("data", {}).get("username")
            }
            
            # 保存Twitter凭证到数据库
            success = self.repository.save_twitter_credentials(founder_id, credentials_data)
            if not success:
                logger.error(f"Failed to save Twitter credentials for user {founder_id}")
                raise TwitterOAuthError("Failed to save Twitter credentials")
            
            logger.info(f"Successfully saved Twitter credentials for user {founder_id}")
            
            # 清理code_verifier
            self._remove_code_verifier(state)
            
            # 清理该用户的token验证缓存，因为现在有新的token
            try:
                from api.middleware import clear_token_cache
                clear_token_cache(founder_id)
                logger.info(f"Cleared token validation cache for user {founder_id}")
            except ImportError:
                logger.warning("Could not import clear_token_cache function")
            
            return {
                "access_token": token_info["access_token"],
                "refresh_token": token_info.get("refresh_token"),
                "expires_at": datetime.utcnow() + timedelta(seconds=token_info.get("expires_in", 7200)),
                "twitter_user_id": user_info.get("data", {}).get("id"),
                "twitter_username": user_info.get("data", {}).get("username")
            }
            
        except Exception as e:
            raise TwitterOAuthError(f"Failed to handle Twitter callback: {str(e)}")
    
    def refresh_twitter_token(self, founder_id: str) -> Optional[Dict[str, Any]]:
        """刷新Twitter访问令牌"""
        try:
            credentials = self.repository.get_twitter_credentials(founder_id)
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
            
            self.repository.save_twitter_credentials(founder_id, credentials)
            
            # 清理token验证缓存，因为有新的token
            try:
                from api.middleware import clear_token_cache
                clear_token_cache(founder_id)
                logger.info(f"Cleared token validation cache after refresh for user {founder_id}")
            except ImportError:
                logger.warning("Could not import clear_token_cache function")
            
            return {
                "access_token": credentials.access_token,
                "refresh_token": credentials.refresh_token,
                "expires_at": credentials.expires_at
            }
            
        except Exception as e:
            logger.error(f"Failed to refresh Twitter token: {e}")
            return None
    
    def revoke_twitter_token(self, founder_id: str) -> bool:
        """撤销Twitter访问令牌"""
        try:
            credentials = self.repository.get_twitter_credentials(founder_id)
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
            self.repository.delete_twitter_credentials(founder_id)
            
            # 清理token验证缓存
            try:
                from api.middleware import clear_token_cache
                clear_token_cache(founder_id)
                logger.info(f"Cleared token validation cache after revocation for user {founder_id}")
            except ImportError:
                logger.warning("Could not import clear_token_cache function")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke Twitter token: {e}")
            return False

    def get_twitter_connection_status(self, founder_id: str) -> Dict[str, Any]:
        """获取Twitter连接状态详情 - 优化版本，减少API调用"""
        try:
            credentials = self.repository.get_twitter_credentials(founder_id)
            
            if not credentials:
                return {
                    "connected": False,
                    "has_valid_token": False,
                    "message": "Twitter账户未连接",
                    "debug_info": "No credentials found in database"
                }
            
            # 检查令牌是否过期（基于数据库中的过期时间）
            is_expired = credentials.is_expired()
            
            # 优化的令牌验证 - 减少API调用
            if is_expired:
                # 如果数据库显示已过期，直接返回，不需要API验证
                return {
                    "connected": True,
                    "has_valid_token": False,
                    "twitter_username": credentials.twitter_username,
                    "expires_at": credentials.expires_at.isoformat() if credentials.expires_at else None,
                    "is_expired": True,
                    "message": "Twitter令牌已过期",
                    "debug_info": {
                        "founder_id": founder_id,
                        "has_access_token": bool(credentials.access_token),
                        "has_refresh_token": bool(credentials.refresh_token),
                        "token_length": len(credentials.access_token) if credentials.access_token else 0,
                        "created_at": credentials.created_at.isoformat() if credentials.created_at else None,
                        "updated_at": credentials.updated_at.isoformat() if credentials.updated_at else None,
                        "validation_method": "database_expiry_check"
                    }
                }
            
            # 对于未过期的令牌，使用缓存验证机制
            try:
                from api.middleware import should_validate_twitter_token, cache_token_validation, _token_validation_cache
                
                # 检查是否需要进行API验证
                if should_validate_twitter_token(founder_id):
                    logger.info(f"执行Twitter状态API验证 (缓存过期或首次检查)")
                    twitter_client = TwitterAPIClient(
                        client_id=self.twitter_client_id,
                        client_secret=self.twitter_client_secret
                    )
                    is_valid = twitter_client.auth.validate_user_token(credentials.access_token)
                    cache_token_validation(founder_id, is_valid)
                else:
                    # 使用缓存的验证结果
                    cached_valid, cached_time = _token_validation_cache.get(founder_id, (False, datetime.min))
                    is_valid = cached_valid
                    logger.info(f"使用缓存的Twitter状态验证结果: {is_valid} (缓存时间: {cached_time})")
                    
            except ImportError:
                # 如果无法导入缓存函数，进行单次API验证
                logger.warning("无法导入缓存函数，执行单次API验证")
                try:
                    twitter_client = TwitterAPIClient(
                        client_id=self.twitter_client_id,
                        client_secret=self.twitter_client_secret
                    )
                    is_valid = twitter_client.auth.validate_user_token(credentials.access_token)
                except Exception as e:
                    logger.error(f"Twitter令牌验证失败: {e}")
                    is_valid = False
            except Exception as e:
                logger.error(f"验证Twitter令牌失败: {e}")
                is_valid = False
                
            return {
                "connected": True,
                "has_valid_token": is_valid,
                "twitter_username": credentials.twitter_username,
                "expires_at": credentials.expires_at.isoformat() if credentials.expires_at else None,
                "is_expired": is_expired,
                "message": "Twitter账户已连接" if is_valid else "Twitter令牌可能无效",
                "debug_info": {
                    "founder_id": founder_id,
                    "has_access_token": bool(credentials.access_token),
                    "has_refresh_token": bool(credentials.refresh_token),
                    "token_length": len(credentials.access_token) if credentials.access_token else 0,
                    "created_at": credentials.created_at.isoformat() if credentials.created_at else None,
                    "updated_at": credentials.updated_at.isoformat() if credentials.updated_at else None,
                    "validation_method": "cached_api_check" if not is_expired else "database_only"
                }
            }
            
        except Exception as e:
            logger.error(f"获取Twitter状态失败: {e}")
            return {
                "connected": False,
                "has_valid_token": False,
                "message": "获取Twitter状态失败",
                "debug_info": f"Error: {str(e)}"
            }
    
    # 改进的临时存储实现
    _code_verifiers = {}
    
    def _store_code_verifier(self, state: str, code_verifier: str, founder_id: str):
        """Store code verifier for PKCE flow"""
        self._code_verifiers[state] = {
            'code_verifier': code_verifier,
            'founder_id': founder_id,
            'created_at': datetime.utcnow()
        }
        # Clean up old entries
        self._cleanup_expired_verifiers()
    
    def _get_code_verifier(self, state: str) -> Optional[str]:
        """获取code_verifier并验证是否过期"""
        data = self._get_code_verifier_data(state)
        return data['code_verifier'] if data else None
    
    def _get_code_verifier_data(self, state: str) -> Optional[Dict[str, Any]]:
        """Get code verifier data for PKCE flow"""
        if state in self._code_verifiers:
            data = self._code_verifiers[state]
            # Check if expired (10 minutes)
            if (datetime.utcnow() - data['created_at']).total_seconds() < 600:
                return data
            else:
                # Remove expired entry
                del self._code_verifiers[state]
        return None
    
    def _remove_code_verifier(self, state: str):
        """删除code_verifier"""
        self._code_verifiers.pop(state, None)
    
    def _cleanup_expired_verifiers(self):
        """Clean up expired code verifiers"""
        current_time = datetime.utcnow()
        expired_states = [
            state for state, data in self._code_verifiers.items()
            if (current_time - data['created_at']).total_seconds() > 600
        ]
        for state in expired_states:
            del self._code_verifiers[state]

    def diagnose_twitter_credentials_saving(self, founder_id: str) -> Dict[str, Any]:
        """诊断Twitter凭证保存问题"""
        try:
            # 检查用户是否存在
            user = self.repository.get_user_by_id(founder_id)
            if not user:
                return {
                    "error": "User not found",
                    "founder_id": founder_id
                }
            
            # 检查现有凭证
            existing_cred = self.repository.get_twitter_credentials(founder_id)
            
            return {
                "user_exists": True,
                "user_email": user.email,
                "user_username": user.username,
                "has_existing_credentials": existing_cred is not None,
                "existing_credentials_info": {
                    "has_access_token": bool(existing_cred.access_token) if existing_cred else False,
                    "has_refresh_token": bool(existing_cred.refresh_token) if existing_cred else False,
                    "twitter_username": existing_cred.twitter_username if existing_cred else None,
                    "expires_at": existing_cred.expires_at.isoformat() if existing_cred and existing_cred.expires_at else None
                } if existing_cred else None,
                "encryption_key_configured": bool(os.getenv('ENCRYPTION_KEY')),
                "encryption_key_length": len(os.getenv('ENCRYPTION_KEY', ''))
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "founder_id": founder_id
            }