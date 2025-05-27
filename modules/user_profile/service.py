"""User profile service logic""" 
from typing import Optional, Tuple
import requests
from requests_oauthlib import OAuth2Session
from urllib.parse import urlencode
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
import os

from .repository import UserProfileRepository
from .models import UserProfileData, ProductInfoData, TwitterCredentials, UserRegistrationRequest, UserLoginRequest

class TwitterOAuthError(Exception):
    """Twitter OAuth related exception"""
    pass

class UserProfileService:
    """User profile service"""
    
    def __init__(self, repository: UserProfileRepository):
        self.repository = repository
        self.twitter_client_id = os.getenv('TWITTER_CLIENT_ID')
        self.twitter_client_secret = os.getenv('TWITTER_CLIENT_SECRET')
        self.twitter_redirect_uri = os.getenv('TWITTER_REDIRECT_URI', 'http://localhost:8000/auth/twitter/callback')
        
        if not self.twitter_client_id or not self.twitter_client_secret:
            raise ValueError("Twitter API credentials not configured")
    
    def register_user(self, user_data: UserRegistrationRequest) -> Tuple[bool, Optional[str]]:
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
    
    def authenticate_user(self, login_data: UserLoginRequest) -> Optional[str]:
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
        """Get Twitter OAuth authorization URL (using PKCE)"""
        # Generate PKCE parameters
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        # Generate state parameter for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Build authorization URL
        auth_params = {
            'response_type': 'code',
            'client_id': self.twitter_client_id,
            'redirect_uri': self.twitter_redirect_uri,
            'scope': 'tweet.read tweet.write users.read offline.access',
            'state': f"{state}:{user_id}",  # Encode user_id into state
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        auth_url = f"https://twitter.com/i/oauth2/authorize?{urlencode(auth_params)}"
        
        # Temporarily store code_verifier (should use Redis or database in actual applications)
        # Simplified handling here, should have expiration mechanism in practice
        self._store_code_verifier(state, code_verifier)
        
        return auth_url, state
    
    def handle_twitter_callback(self, authorization_code: str, state: str) -> Tuple[bool, Optional[str]]:
        """Handle Twitter OAuth callback"""
        try:
            # Validate state and extract user_id
            if ':' not in state:
                return False, "Invalid state parameter"
            
            state_token, user_id = state.split(':', 1)
            code_verifier = self._get_code_verifier(state_token)
            
            if not code_verifier:
                return False, "Invalid authorization state"
            
            # Get access token
            token_data = self._exchange_code_for_token(authorization_code, code_verifier)
            
            if not token_data:
                return False, "Failed to get access token"
            
            # Get user information
            user_info = self._get_twitter_user_info(token_data['access_token'])
            
            # Create credentials object
            expires_at = None
            if 'expires_in' in token_data:
                expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
            
            credentials = TwitterCredentials(
                user_id=user_id,
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token'),
                expires_at=expires_at,
                scope=token_data.get('scope'),
                twitter_user_id=user_info.get('id'),
                twitter_username=user_info.get('username')
            )
            
            # Save credentials
            success = self.repository.save_twitter_credentials(user_id, credentials)
            
            if success:
                # Clean up temporarily stored code_verifier
                self._remove_code_verifier(state_token)
                return True, "Twitter account connected successfully"
            else:
                return False, "Failed to save Twitter credentials"
                
        except Exception as e:
            print(f"Failed to handle Twitter callback: {e}")
            return False, f"Failed to handle callback: {str(e)}"
    
    def get_twitter_access_token(self, user_id: str) -> Optional[str]:
        """Get valid Twitter access token (auto refresh)"""
        credentials = self.repository.get_twitter_credentials(user_id)
        
        if not credentials:
            return None
        
        # Check if token is about to expire (refresh 5 minutes early)
        if credentials.expires_at and credentials.expires_at <= datetime.utcnow() + timedelta(minutes=5):
            if credentials.refresh_token:
                # Try to refresh token
                new_credentials = self._refresh_access_token(credentials)
                if new_credentials:
                    self.repository.save_twitter_credentials(user_id, new_credentials)
                    return new_credentials.access_token
                else:
                    return None  # Refresh failed, need re-authorization
        
        return credentials.access_token
    
    def _exchange_code_for_token(self, authorization_code: str, code_verifier: str) -> Optional[dict]:
        """Exchange authorization code for access token"""
        token_url = "https://api.twitter.com/2/oauth2/token"
        
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': self.twitter_client_id,
            'code': authorization_code,
            'redirect_uri': self.twitter_redirect_uri,
            'code_verifier': code_verifier
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Use Basic authentication
        auth = (self.twitter_client_id, self.twitter_client_secret)
        
        try:
            response = requests.post(token_url, data=token_data, headers=headers, auth=auth)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to get access token: {e}")
            return None
    
    def _refresh_access_token(self, credentials: TwitterCredentials) -> Optional[TwitterCredentials]:
        """Refresh access token"""
        if not credentials.refresh_token:
            return None
        
        token_url = "https://api.twitter.com/2/oauth2/token"
        
        token_data = {
            'grant_type': 'refresh_token',
            'refresh_token': credentials.refresh_token,
            'client_id': self.twitter_client_id
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        auth = (self.twitter_client_id, self.twitter_client_secret)
        
        try:
            response = requests.post(token_url, data=token_data, headers=headers, auth=auth)
            response.raise_for_status()
            token_data = response.json()
            
            # Update credentials
            expires_at = None
            if 'expires_in' in token_data:
                expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
            
            credentials.access_token = token_data['access_token']
            credentials.refresh_token = token_data.get('refresh_token', credentials.refresh_token)
            credentials.expires_at = expires_at
            credentials.updated_at = datetime.utcnow()
            
            return credentials
            
        except requests.RequestException as e:
            print(f"Failed to refresh access token: {e}")
            return None
    
    def _get_twitter_user_info(self, access_token: str) -> dict:
        """Get Twitter user information"""
        url = "https://api.twitter.com/2/users/me"
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get('data', {})
        except requests.RequestException as e:
            print(f"Failed to get Twitter user information: {e}")
            return {}
    
    # Simplified temporary storage implementation (should use Redis etc. in actual applications)
    _code_verifiers = {}
    
    def _store_code_verifier(self, state: str, code_verifier: str):
        """Temporarily store code_verifier"""
        self._code_verifiers[state] = code_verifier
    
    def _get_code_verifier(self, state: str) -> Optional[str]:
        """Get code_verifier"""
        return self._code_verifiers.get(state)
    
    def _remove_code_verifier(self, state: str):
        """Remove code_verifier"""
        self._code_verifiers.pop(state, None)