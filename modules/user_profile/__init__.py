"""User Profile Module"""
"""
UserProfileModule - User Profile Module

This module is responsible for:
1. User registration, login, authentication
2. Product information management (CRUD operations)
3. Twitter OAuth 2.0 PKCE flow
4. Access token management and automatic refresh
5. Sensitive data encryption storage

Main components:
- models.py: Data model definitions
- repository.py: Data access layer
- service.py: Business logic service
- validators.py: Input validation
"""

from .models import (
    UserProfileData,
    ProductInfoData, 
    ProductKeywords,
    TwitterCredentials,
    UserRegistrationRequest,
    UserLoginRequest,
    ProductInfoUpdateRequest,
    ContentStylePreferences,
    CompetitorInfo,
    InfluencerReference
)

from .service import UserProfileService, TwitterOAuthError
from .repository import UserProfileRepository
from .validators import UserProfileValidators

__all__ = [
    'UserProfileData',
    'ProductInfoData',
    'ProductKeywords', 
    'TwitterCredentials',
    'UserRegistrationRequest',
    'UserLoginRequest',
    'ProductInfoUpdateRequest',
    'ContentStylePreferences',
    'CompetitorInfo',
    'InfluencerReference',
    'UserProfileService',
    'UserProfileRepository', 
    'UserProfileValidators',
    'TwitterOAuthError'
]