"""OAuth认证处理""" 
from typing import Dict, Optional, Tuple
import requests
from requests.auth import HTTPBasicAuth
import logging
import secrets
import base64
import hashlib
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class TwitterAuth:
    """Handles Twitter API authentication"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
    
    def get_authorization_url(self, redirect_uri: str, scopes: list = None) -> Tuple[str, str, str]:
        """Generate OAuth 2.0 authorization URL with PKCE"""
        if scopes is None:
            scopes = ['tweet.read', 'users.read', 'follows.read', 'follows.write']
            
        # Generate PKCE parameters
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        # Generate state parameter
        state = secrets.token_urlsafe(32)
        
        # Build authorization URL
        auth_params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'scope': ' '.join(scopes),
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        auth_url = f"https://x.com/i/oauth2/authorize?{urlencode(auth_params)}"
        return auth_url, state, code_verifier
    
    def exchange_code_for_token(self, code: str, code_verifier: str, redirect_uri: str) -> Optional[Dict]:
        """Exchange authorization code for access token"""
        url = 'https://api.x.com/2/oauth2/token'
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'code': code,
            'redirect_uri': redirect_uri,
            'code_verifier': code_verifier
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                data=data,
                auth=HTTPBasicAuth(self.client_id, self.client_secret)
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to exchange code for token: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text}")
            return None
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict]:
        """Refresh access token using refresh token"""
        url = 'https://api.x.com/2/oauth2/token'
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                data=data,
                auth=HTTPBasicAuth(self.client_id, self.client_secret)
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to refresh token: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text}")
            return None
    
    def revoke_token(self, token: str) -> bool:
        """Revoke access token or refresh token"""
        url = 'https://api.x.com/2/oauth2/revoke'
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'token': token,
            'client_id': self.client_id
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                data=data,
                auth=HTTPBasicAuth(self.client_id, self.client_secret)
            )
            
            response.raise_for_status()
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to revoke token: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text}")
            return False
    
    def validate_user_token(self, user_access_token: str) -> bool:
        """Validate a user access token"""
        url = "https://api.x.com/2/users/me"
        
        headers = {
            'Authorization': f'Bearer {user_access_token}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            return response.status_code == 200
            
        except requests.RequestException:
            return False
    
    @staticmethod
    def create_auth_headers(access_token: str) -> Dict[str, str]:
        """Create authorization headers for API requests"""
        return {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }