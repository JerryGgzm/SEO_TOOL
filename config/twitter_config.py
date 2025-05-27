import os
from typing import Dict, Any

class TwitterConfig:
    """Twitter API configuration settings"""
    
    # API Credentials
    CLIENT_ID = os.getenv('TWITTER_CLIENT_ID')
    CLIENT_SECRET = os.getenv('TWITTER_CLIENT_SECRET')
    
    # API URLs (configurable for future changes)
    API_BASE_URL_V2 = os.getenv('TWITTER_API_V2_URL', 'https://api.twitter.com/2')
    API_BASE_URL_V1_1 = os.getenv('TWITTER_API_V1_1_URL', 'https://api.twitter.com/1.1')
    
    # Rate Limiting Settings
    DEFAULT_RATE_LIMIT_WINDOW = 900  # 15 minutes
    DEFAULT_RATE_LIMIT_REQUESTS = 300
    
    # Request Settings
    REQUEST_TIMEOUT = int(os.getenv('TWITTER_REQUEST_TIMEOUT', '30'))
    MAX_RETRIES = int(os.getenv('TWITTER_MAX_RETRIES', '3'))
    RETRY_DELAY = int(os.getenv('TWITTER_RETRY_DELAY', '5'))
    
    # Tweet Settings
    MAX_TWEET_LENGTH = 280
    MAX_POLL_OPTIONS = 4
    MIN_POLL_OPTIONS = 2
    MAX_POLL_DURATION_MINUTES = 10080  # 7 days
    MIN_POLL_DURATION_MINUTES = 5
    
    # Search Settings
    MAX_SEARCH_RESULTS = 100
    MIN_SEARCH_RESULTS = 10
    DEFAULT_SEARCH_RESULTS = 50
    
    # Field Presets
    DEFAULT_TWEET_FIELDS = [
        'id', 'text', 'created_at', 'author_id', 'public_metrics',
        'context_annotations', 'conversation_id', 'in_reply_to_user_id',
        'referenced_tweets', 'reply_settings'
    ]
    
    DEFAULT_USER_FIELDS = [
        'id', 'name', 'username', 'verified', 'public_metrics',
        'description', 'location', 'url', 'profile_image_url'
    ]
    
    DEFAULT_EXPANSIONS = [
        'author_id', 'referenced_tweets.id', 'referenced_tweets.id.author_id'
    ]
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """Validate Twitter configuration"""
        errors = []
        warnings = []
        
        # Check required credentials
        if not cls.CLIENT_ID:
            errors.append("TWITTER_CLIENT_ID environment variable is required")
        
        if not cls.CLIENT_SECRET:
            errors.append("TWITTER_CLIENT_SECRET environment variable is required")
        
        # Check optional settings
        if cls.REQUEST_TIMEOUT < 10:
            warnings.append("REQUEST_TIMEOUT is very low, may cause timeout errors")
        
        if cls.MAX_RETRIES > 5:
            warnings.append("MAX_RETRIES is high, may cause long delays")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @classmethod
    def get_search_query_limits(cls) -> Dict[str, int]:
        """Get search query limits and recommendations"""
        return {
            'max_results_per_request': cls.MAX_SEARCH_RESULTS,
            'min_results_per_request': cls.MIN_SEARCH_RESULTS,
            'recommended_results': cls.DEFAULT_SEARCH_RESULTS,
            'max_query_length': 1024,  # Twitter API limit
            'max_operators': 50  # Practical limit for complex queries
        }

# Configuration instance
twitter_config = TwitterConfig()