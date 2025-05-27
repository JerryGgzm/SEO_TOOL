# ====================
# File: tests/unit/test_twitter_api.py (Unit Tests)
# ====================

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import requests
from datetime import datetime

from modules.twitter_api import (
    TwitterAPIClient, TwitterAuth, TwitterRateLimiter,
    TwitterAPIError, RateLimitError, AuthenticationError
)
from modules.twitter_api.endpoints import TwitterAPIEndpoints

class TestTwitterAuth:
    """Test Twitter authentication"""
    
    def test_create_auth_headers(self):
        """Test authorization header creation"""
        token = "test_access_token"
        headers = TwitterAuth.create_auth_headers(token)
        
        assert headers['Authorization'] == f'Bearer {token}'
        assert headers['Content-Type'] == 'application/json'
    
    @patch('requests.post')
    def test_get_bearer_token_success(self, mock_post):
        """Test successful bearer token retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = {'access_token': 'bearer_token_123'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        auth = TwitterAuth('client_id', 'client_secret')
        token = auth.get_bearer_token()
        
        assert token == 'bearer_token_123'
        mock_post.assert_called_once()
    
    @patch('requests.get')
    def test_validate_user_token_valid(self, mock_get):
        """Test valid user token validation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        auth = TwitterAuth('client_id', 'client_secret')
        is_valid = auth.validate_user_token('valid_token')
        
        assert is_valid == True
        mock_get.assert_called_once()

class TestTwitterRateLimiter:
    """Test rate limiting functionality"""
    
    def test_rate_limit_info_creation(self):
        """Test rate limit info object creation"""
        from modules.twitter_api.rate_limiter import RateLimitInfo
        
        rate_info = RateLimitInfo(limit=300, remaining=250, reset_time=1234567890)
        
        assert rate_info.limit == 300
        assert rate_info.remaining == 250
        assert rate_info.reset_time == 1234567890
        assert not rate_info.is_exhausted()
    
    def test_rate_limit_exhausted(self):
        """Test rate limit exhaustion detection"""
        from modules.twitter_api.rate_limiter import RateLimitInfo
        
        rate_info = RateLimitInfo(limit=300, remaining=0, reset_time=1234567890)
        
        assert rate_info.is_exhausted() == True
        assert rate_info.should_wait() == True
    
    def test_rate_limiter_update(self):
        """Test rate limiter update from headers"""
        limiter = TwitterRateLimiter()
        
        headers = {
            'x-rate-limit-limit': '300',
            'x-rate-limit-remaining': '250',
            'x-rate-limit-reset': '1234567890'
        }
        
        limiter.update_rate_limit('test_endpoint', headers)
        status = limiter.get_rate_limit_status('test_endpoint')
        
        assert status is not None
        assert status['limit'] == 300
        assert status['remaining'] == 250

class TestTwitterAPIClient:
    """Test Twitter API client"""
    
    @pytest.fixture
    def mock_rate_limiter(self):
        """Mock rate limiter"""
        limiter = Mock(spec=TwitterRateLimiter)
        limiter.wait_if_needed.return_value = None
        limiter.update_rate_limit.return_value = None
        return limiter
    
    @pytest.fixture
    def api_client(self, mock_rate_limiter):
        """Create API client with mocked rate limiter"""
        return TwitterAPIClient('test_client_id', 'test_client_secret', mock_rate_limiter)
    
    @patch('requests.Session')
    def test_create_tweet_success(self, mock_session_class, api_client):
        """Test successful tweet creation"""
        # Mock session and response
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'data': {
                'id': '1234567890',
                'text': 'Test tweet'
            }
        }
        mock_response.headers = {
            'x-rate-limit-limit': '300',
            'x-rate-limit-remaining': '299',
            'x-rate-limit-reset': '1234567890'
        }
        
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        api_client.session = mock_session
        
        result = api_client.create_tweet('user_token', 'Test tweet')
        
        assert result['data']['id'] == '1234567890'
        assert result['data']['text'] == 'Test tweet'
        mock_session.request.assert_called_once()
    
    def test_create_tweet_text_too_long(self, api_client):
        """Test tweet creation with text too long"""
        long_text = 'x' * 281  # Too long
        
        with pytest.raises(TwitterAPIError):
            api_client.create_tweet('user_token', long_text)
    
    @patch('requests.Session')
    def test_search_tweets_success(self, mock_session_class, api_client):
        """Test successful tweet search"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'id': '1234567890',
                    'text': 'Search result tweet',
                    'created_at': '2024-01-01T00:00:00.000Z'
                }
            ],
            'meta': {
                'result_count': 1
            }
        }
        mock_response.headers = {}
        
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        api_client.session = mock_session
        
        result = api_client.search_tweets('user_token', 'test query')
        
        assert len(result['data']) == 1
        assert result['data'][0]['text'] == 'Search result tweet'
        mock_session.request.assert_called_once()
    
    def test_search_tweets_empty_query(self, api_client):
        """Test search with empty query"""
        with pytest.raises(TwitterAPIError):
            api_client.search_tweets('user_token', '')
    
    @patch('requests.Session')
    def test_api_error_handling(self, mock_session_class, api_client):
        """Test API error response handling"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            'errors': [
                {
                    'message': 'Unauthorized',
                    'code': 'unauthorized'
                }
            ]
        }
        mock_response.headers = {}
        
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        api_client.session = mock_session
        
        with pytest.raises(AuthenticationError):
            api_client.create_tweet('invalid_token', 'Test tweet')
    
    @patch('requests.Session')
    def test_rate_limit_error_handling(self, mock_session_class, api_client):
        """Test rate limit error handling"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            'errors': [
                {
                    'message': 'Rate limit exceeded',
                    'code': 'too-many-requests'
                }
            ]
        }
        mock_response.headers = {
            'x-rate-limit-reset': '1234567890',
            'x-rate-limit-remaining': '0'
        }
        
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        api_client.session = mock_session
        
        with pytest.raises(RateLimitError) as exc_info:
            api_client.create_tweet('user_token', 'Test tweet')
        
        assert exc_info.value.reset_time == 1234567890
        assert exc_info.value.remaining == 0

class TestTwitterAPIEndpoints:
    """Test endpoint configurations"""
    
    def test_get_full_url_v2(self):
        """Test URL construction for v2 endpoints"""
        from modules.twitter_api.endpoints import TwitterAPIEndpoints
        
        endpoint = TwitterAPIEndpoints.CREATE_TWEET
        url = TwitterAPIEndpoints.get_full_url(endpoint)
        
        assert url == "https://api.twitter.com/2/tweets"
    
    def test_get_full_url_with_params(self):
        """Test URL construction with path parameters"""
        from modules.twitter_api.endpoints import TwitterAPIEndpoints
        
        endpoint = TwitterAPIEndpoints.GET_TWEET
        url = TwitterAPIEndpoints.get_full_url(endpoint, tweet_id="1234567890")
        
        assert url == "https://api.twitter.com/2/tweets/1234567890"
    
    def test_get_full_url_v1_1(self):
        """Test URL construction for v1.1 endpoints"""
        from modules.twitter_api.endpoints import TwitterAPIEndpoints
        
        endpoint = TwitterAPIEndpoints.GET_TRENDS
        url = TwitterAPIEndpoints.get_full_url(endpoint)
        
        assert url == "https://api.twitter.com/1.1/trends/place.json"