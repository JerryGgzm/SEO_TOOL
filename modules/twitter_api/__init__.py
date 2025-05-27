"""Twitter API交互模块""" 
"""
TwitterAPIModule - Twitter API Interaction Layer

This module provides a comprehensive interface to Twitter API v2 with:
1. Rate limiting management
2. Comprehensive error handling
3. OAuth 2.0 authentication
4. Configurable endpoints
5. Full tweet, user, and trend operations

Main Components:
- client.py: Main API client with all operations
- auth.py: Authentication handling
- endpoints.py: API endpoint configurations
- rate_limiter.py: Rate limiting management
- exceptions.py: Custom exception classes
"""

from .client import TwitterAPIClient
from .auth import TwitterAuth
from .endpoints import TwitterAPIEndpoints, APIEndpoint
from .rate_limiter import TwitterRateLimiter, RateLimitInfo
from .exceptions import (
    TwitterAPIError,
    RateLimitError,
    AuthenticationError,
    TwitterAPINotFoundError,
    TwitterAPIBadRequestError,
    TwitterAPIServerError
)

__all__ = [
    'TwitterAPIClient',
    'TwitterAuth',
    'TwitterAPIEndpoints',
    'APIEndpoint',
    'TwitterRateLimiter',
    'RateLimitInfo',
    'TwitterAPIError',
    'RateLimitError',
    'AuthenticationError',
    'TwitterAPINotFoundError',
    'TwitterAPIBadRequestError',
    'TwitterAPIServerError'
]
