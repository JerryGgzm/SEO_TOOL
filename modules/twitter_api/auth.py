"""OAuth认证处理""" 
from typing import Dict, Optional
import requests
from requests.auth import HTTPBasicAuth
import logging

logger = logging.getLogger(__name__)

class TwitterAuth:
    """Handles Twitter API authentication"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
    
    def get_bearer_token(self) -> Optional[str]:
        """Get application-only bearer token (for app-only endpoints)"""
        url = 'https://api.twitter.com/oauth2/token'
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
        }
        
        data = {
            'grant_type': 'client_credentials'
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                data=data,
                auth=HTTPBasicAuth(self.client_id, self.client_secret)
            )
            
            response.raise_for_status()
            token_data = response.json()
            
            return token_data.get('access_token')
            
        except requests.RequestException as e:
            logger.error(f"Failed to get bearer token: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text}")
            return None
    
    def validate_user_token(self, user_access_token: str) -> bool:
        """Validate a user access token"""
        url = "https://api.twitter.com/2/users/me"
        
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