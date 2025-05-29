"""Twitter API Client""" 
import requests
import json
import time
from typing import Dict, List, Optional, Any, Union
import logging
from urllib.parse import urlencode

from .endpoints import TwitterAPIEndpoints, APIEndpoint
from .rate_limiter import TwitterRateLimiter
from .auth import TwitterAuth
from .exceptions import (
    TwitterAPIError, RateLimitError, AuthenticationError,
    TwitterAPINotFoundError, TwitterAPIBadRequestError, TwitterAPIServerError
)

logger = logging.getLogger(__name__)

class TwitterAPIClient:
    """Main Twitter API client for interacting with Twitter API v2"""
    
    def __init__(self, client_id: str, client_secret: str, 
                 rate_limiter: Optional[TwitterRateLimiter] = None):
        self.auth = TwitterAuth(client_id, client_secret)
        self.rate_limiter = rate_limiter or TwitterRateLimiter()
        self.endpoints = TwitterAPIEndpoints()
        
        # Configure session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Ideation-Twitter-Client/1.0'
        })
    
    def _make_request(self, endpoint: APIEndpoint, user_token: str, 
                     params: Optional[Dict] = None, json_body: Optional[Dict] = None,
                     **path_params) -> Dict[str, Any]:
        """
        Core method for making API requests with rate limiting and error handling
        """
        endpoint_key = f"{endpoint.method}:{endpoint.path}"
        
        # Check rate limit before making request
        self.rate_limiter.wait_if_needed(endpoint_key, endpoint)
        
        # Build URL
        url = self.endpoints.get_full_url(endpoint, **path_params)
        
        # Prepare headers
        headers = TwitterAuth.create_auth_headers(user_token)
        
        # Prepare request parameters
        request_kwargs = {
            'headers': headers,
            'timeout': 30
        }
        
        if params:
            request_kwargs['params'] = params
        
        if json_body:
            request_kwargs['json'] = json_body
        
        # Log request details
        logger.info(f"Making {endpoint.method} request to {url}")
        logger.debug(f"Request params: {params}, body: {json_body}")
        
        try:
            # Make the request
            response = self.session.request(endpoint.method, url, **request_kwargs)
            
            # Update rate limit info
            self.rate_limiter.update_rate_limit(endpoint_key, response.headers)
            
            # Handle response
            return self._handle_response(response, endpoint_key)
            
        except requests.RequestException as e:
            logger.error(f"Network error during API request: {e}")
            raise TwitterAPIError(f"Network error: {str(e)}")
    
    def _handle_response(self, response: requests.Response, endpoint_key: str) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions"""
        
        # Log response details
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")
        
        # Handle successful responses
        if 200 <= response.status_code < 300:
            try:
                return response.json()
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON response for {endpoint_key}")
                return {'success': True}
        
        # Handle error responses
        try:
            error_data = response.json()
        except json.JSONDecodeError:
            error_data = {'detail': response.text}
        
        # Extract error information
        error_message = self._extract_error_message(error_data, response.status_code)
        
        # Raise specific exceptions based on status code
        if response.status_code == 400:
            validation_errors = self._extract_validation_errors(error_data)
            raise TwitterAPIBadRequestError(error_message, validation_errors)
        elif response.status_code == 401:
            raise AuthenticationError(error_message)
        elif response.status_code == 404:
            raise TwitterAPINotFoundError(error_message)
        elif response.status_code == 429:
            reset_time = int(response.headers.get('x-rate-limit-reset', 0))
            remaining = int(response.headers.get('x-rate-limit-remaining', 0))
            raise RateLimitError(error_message, reset_time, remaining)
        elif response.status_code >= 500:
            raise TwitterAPIServerError(error_message)
        else:
            raise TwitterAPIError(
                error_message, 
                status_code=response.status_code,
                response_data=error_data
            )
    
    def _extract_error_message(self, error_data: Dict, status_code: int) -> str:
        """Extract error message from API response"""
        if 'detail' in error_data:
            return error_data['detail']
        elif 'errors' in error_data and error_data['errors']:
            # Handle Twitter API v2 error format
            errors = error_data['errors']
            if isinstance(errors, list) and errors:
                return errors[0].get('message', f'API error (HTTP {status_code})')
            return str(errors)
        elif 'title' in error_data:
            return error_data['title']
        else:
            return f'API error (HTTP {status_code})'
    
    def _extract_validation_errors(self, error_data: Dict) -> List[str]:
        """Extract validation errors from API response"""
        validation_errors = []
        
        if 'errors' in error_data:
            errors = error_data['errors']
            if isinstance(errors, list):
                for error in errors:
                    if isinstance(error, dict) and 'message' in error:
                        validation_errors.append(error['message'])
        
        return validation_errors
    
    # ==================== Tweet Operations ====================
    
    def create_tweet(self, user_token: str, text: str, 
                    reply_settings: Optional[str] = None,
                    in_reply_to_tweet_id: Optional[str] = None,
                    quote_tweet_id: Optional[str] = None,
                    media_ids: Optional[List[str]] = None,
                    poll_options: Optional[List[str]] = None,
                    poll_duration_minutes: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a new tweet
        
        Args:
            user_token: User's access token
            text: Tweet text content
            reply_settings: Who can reply ('everyone', 'mentionedUsers', 'followers')
            in_reply_to_tweet_id: ID of tweet being replied to
            quote_tweet_id: ID of tweet being quoted
            media_ids: List of media IDs to attach
            poll_options: List of poll options (2-4 options)
            poll_duration_minutes: Poll duration in minutes (5-10080)
        """
        if not text or len(text) > 280:
            raise TwitterAPIBadRequestError("Tweet text must be 1-280 characters")
        
        tweet_data = {
            'text': text
        }
        
        # Add reply information
        if in_reply_to_tweet_id:
            tweet_data['reply'] = {
                'in_reply_to_tweet_id': in_reply_to_tweet_id
            }
        
        # Add quote tweet
        if quote_tweet_id:
            tweet_data['quote_tweet_id'] = quote_tweet_id
        
        # Add media
        if media_ids:
            tweet_data['media'] = {
                'media_ids': media_ids
            }
        
        # Add poll
        if poll_options and len(poll_options) >= 2:
            poll_data = {
                'options': poll_options
            }
            if poll_duration_minutes:
                poll_data['duration_minutes'] = min(max(poll_duration_minutes, 5), 10080)
            else:
                poll_data['duration_minutes'] = 1440  # Default 24 hours
            
            tweet_data['poll'] = poll_data
        
        # Add reply settings
        if reply_settings and reply_settings in ['everyone', 'mentionedUsers', 'followers']:
            tweet_data['reply_settings'] = reply_settings
        
        return self._make_request(
            self.endpoints.CREATE_TWEET,
            user_token,
            json_body=tweet_data
        )
    
    def delete_tweet(self, user_token: str, tweet_id: str) -> Dict[str, Any]:
        """Delete a tweet"""
        return self._make_request(
            self.endpoints.DELETE_TWEET,
            user_token,
            tweet_id=tweet_id
        )
    
    def fetch_tweet_by_id(self, user_token: str, tweet_id: str, 
                         fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Fetch a tweet by ID
        
        Args:
            user_token: User's access token
            tweet_id: Tweet ID to fetch
            fields: List of tweet fields to include
        """
        params = {}
        
        if fields:
            # Default tweet fields
            default_fields = ['id', 'text', 'created_at', 'author_id', 'public_metrics']
            tweet_fields = list(set(default_fields + fields))
            params['tweet.fields'] = ','.join(tweet_fields)
            params['expansions'] = 'author_id'
            params['user.fields'] = 'id,name,username,verified'
        
        return self._make_request(
            self.endpoints.GET_TWEET,
            user_token,
            params=params,
            tweet_id=tweet_id
        )
    
    def search_tweets(self, user_token: str, query: str, 
                     start_time: Optional[str] = None,
                     end_time: Optional[str] = None,
                     since_id: Optional[str] = None,
                     until_id: Optional[str] = None,
                     max_results: int = 100,
                     next_token: Optional[str] = None,
                     tweet_fields: Optional[List[str]] = None,
                     user_fields: Optional[List[str]] = None,
                     expansions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Search for tweets
        
        Args:
            user_token: User's access token
            query: Search query using Twitter search operators
            start_time: Earliest tweet creation time (ISO 8601)
            end_time: Latest tweet creation time (ISO 8601)
            since_id: Return tweets after this tweet ID
            until_id: Return tweets before this tweet ID
            max_results: Maximum number of results (10-100)
            next_token: Pagination token
            tweet_fields: List of tweet fields to include
            user_fields: List of user fields to include
            expansions: List of expansion fields
        """
        if not query:
            raise TwitterAPIBadRequestError("Query parameter is required")
        
        max_results = min(max(max_results, 10), 100)
        
        params = {
            'query': query,
            'max_results': max_results
        }
        
        # Add time filters
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time
        if since_id:
            params['since_id'] = since_id
        if until_id:
            params['until_id'] = until_id
        if next_token:
            params['next_token'] = next_token
        
        # Add field specifications
        default_tweet_fields = ['id', 'text', 'created_at', 'author_id', 'public_metrics']
        if tweet_fields:
            tweet_fields = list(set(default_tweet_fields + tweet_fields))
        else:
            tweet_fields = default_tweet_fields
        params['tweet.fields'] = ','.join(tweet_fields)
        
        default_user_fields = ['id', 'name', 'username', 'verified']
        if user_fields:
            user_fields = list(set(default_user_fields + user_fields))
        else:
            user_fields = default_user_fields
        params['user.fields'] = ','.join(user_fields)
        
        default_expansions = ['author_id']
        if expansions:
            expansions = list(set(default_expansions + expansions))
        else:
            expansions = default_expansions
        params['expansions'] = ','.join(expansions)
        
        return self._make_request(
            self.endpoints.SEARCH_RECENT_TWEETS,
            user_token,
            params=params
        )
    
    # ==================== Retweet Operations ====================
    
    def create_retweet(self, user_token: str, authenticating_user_id: str, 
                      target_tweet_id: str) -> Dict[str, Any]:
        """Create a retweet"""
        json_body = {
            'tweet_id': target_tweet_id
        }
        
        return self._make_request(
            self.endpoints.CREATE_RETWEET,
            user_token,
            json_body=json_body,
            user_id=authenticating_user_id
        )
    
    def delete_retweet(self, user_token: str, authenticating_user_id: str, 
                      source_tweet_id: str) -> Dict[str, Any]:
        """Delete a retweet"""
        return self._make_request(
            self.endpoints.DELETE_RETWEET,
            user_token,
            user_id=authenticating_user_id,
            source_tweet_id=source_tweet_id
        )
    
    # ==================== Like Operations ====================
    
    def like_tweet(self, user_token: str, user_id: str, tweet_id: str) -> Dict[str, Any]:
        """Like a tweet"""
        json_body = {
            'tweet_id': tweet_id
        }
        
        return self._make_request(
            self.endpoints.LIKE_TWEET,
            user_token,
            json_body=json_body,
            user_id=user_id
        )
    
    def unlike_tweet(self, user_token: str, user_id: str, tweet_id: str) -> Dict[str, Any]:
        """Unlike a tweet"""
        return self._make_request(
            self.endpoints.UNLIKE_TWEET,
            user_token,
            user_id=user_id,
            tweet_id=tweet_id
        )
    
    # ==================== User Operations ====================
    
    def get_user_by_id(self, user_token: str, user_id: str, 
                      user_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get user information by user ID"""
        params = {}
        
        if user_fields:
            default_fields = ['id', 'name', 'username', 'verified', 'public_metrics']
            user_fields = list(set(default_fields + user_fields))
            params['user.fields'] = ','.join(user_fields)
        
        return self._make_request(
            self.endpoints.GET_USER_BY_ID,
            user_token,
            params=params,
            user_id=user_id
        )
    
    def get_user_by_username(self, user_token: str, username: str,
                           user_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get user information by username"""
        params = {}
        
        if user_fields:
            default_fields = ['id', 'name', 'username', 'verified', 'public_metrics']
            user_fields = list(set(default_fields + user_fields))
            params['user.fields'] = ','.join(user_fields)
        
        return self._make_request(
            self.endpoints.GET_USER_BY_USERNAME,
            user_token,
            params=params,
            username=username
        )
    
    def get_me(self, user_token: str) -> Dict[str, Any]:
        """Get current authenticated user information"""
        params = {
            'user.fields': 'id,name,username,verified,public_metrics,description'
        }
        
        return self._make_request(
            self.endpoints.GET_ME,
            user_token,
            params=params
        )
    
    # ==================== Trends Operations ====================
    
    def get_trends_for_location(self, user_token: str, location_id: str = "1") -> List[Dict[str, Any]]:
        """
        Get trending topics for a location
        
        Args:
            user_token: User's access token  
            location_id: WOEID (Where On Earth ID). "1" = Global
        """
        # Use v1.1 API as it's more reliable for trends
        endpoint = self.endpoints.GET_TRENDS
        url = f"{self.endpoints.BASE_URL_V1_1}{endpoint.path}"
        
        params = {
            'id': location_id
        }
        
        headers = TwitterAuth.create_auth_headers(user_token)
        
        endpoint_key = f"{endpoint.method}:{endpoint.path}"
        self.rate_limiter.wait_if_needed(endpoint_key, endpoint)
        
        try:
            response = self.session.get(url, headers=headers, params=params, timeout=30)
            
            # Update rate limit info
            self.rate_limiter.update_rate_limit(endpoint_key, response.headers)
            
            if response.status_code == 200:
                data = response.json()
                # Twitter trends API returns array of locations, get first one
                if data and len(data) > 0:
                    return data[0].get('trends', [])
                return []
            else:
                error_data = response.json() if response.content else {}
                error_message = self._extract_error_message(error_data, response.status_code)
                raise TwitterAPIError(error_message, response.status_code, response_data=error_data)
                
        except requests.RequestException as e:
            logger.error(f"Network error getting trends: {e}")
            raise TwitterAPIError(f"Network error: {str(e)}")
    
    # ==================== Utility Methods ====================
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status for all endpoints"""
        status = {}
        
        # Common endpoint keys
        endpoint_keys = [
            "POST:/tweets",
            "GET:/tweets/search/recent", 
            "GET:/users/me",
            "POST:/users/{user_id}/retweets",
            "GET:/trends/place.json"
        ]
        
        for key in endpoint_keys:
            limit_info = self.rate_limiter.get_rate_limit_status(key)
            if limit_info:
                status[key] = limit_info
        
        return status
    
    def close(self):
        """Close the HTTP session"""
        self.session.close()