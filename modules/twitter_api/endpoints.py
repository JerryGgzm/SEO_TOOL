from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class APIEndpoint:
    """Configuration for a Twitter API endpoint"""
    path: str
    method: str
    version: str = "2"
    rate_limit_window: int = 900  # 15 minutes in seconds
    rate_limit_requests: int = 300  # Default rate limit per window
    requires_auth: bool = True

class TwitterAPIEndpoints:
    """Twitter API v2 endpoint configurations"""
    
    BASE_URL_V2 = "https://api.x.com/2"
    BASE_URL_V1_1 = "https://api.x.com/1.1"
    
    # Tweet endpoints
    CREATE_TWEET = APIEndpoint(
        path="/tweets",
        method="POST",
        rate_limit_requests=300
    )
    
    DELETE_TWEET = APIEndpoint(
        path="/tweets/{tweet_id}",
        method="DELETE",
        rate_limit_requests=300
    )
    
    GET_TWEET = APIEndpoint(
        path="/tweets/{tweet_id}",
        method="GET",
        rate_limit_requests=300
    )
    
    SEARCH_RECENT_TWEETS = APIEndpoint(
        path="/tweets/search/recent",
        method="GET",
        rate_limit_requests=300
    )
    
    # User endpoints
    GET_USER_BY_ID = APIEndpoint(
        path="/users/{user_id}",
        method="GET",
        rate_limit_requests=300
    )
    
    GET_USER_BY_USERNAME = APIEndpoint(
        path="/users/by/username/{username}",
        method="GET",
        rate_limit_requests=300
    )
    
    GET_ME = APIEndpoint(
        path="/users/me",
        method="GET",
        rate_limit_requests=75
    )
    
    # Retweet endpoints
    CREATE_RETWEET = APIEndpoint(
        path="/users/{user_id}/retweets",
        method="POST",
        rate_limit_requests=300
    )
    
    DELETE_RETWEET = APIEndpoint(
        path="/users/{user_id}/retweets/{source_tweet_id}",
        method="DELETE",
        rate_limit_requests=300
    )
    
    # Like endpoints
    LIKE_TWEET = APIEndpoint(
        path="/users/{user_id}/likes",
        method="POST",
        rate_limit_requests=300
    )
    
    UNLIKE_TWEET = APIEndpoint(
        path="/users/{user_id}/likes/{tweet_id}",
        method="DELETE",
        rate_limit_requests=300
    )
    
    # Trends endpoints
    GET_TRENDS = APIEndpoint(
        path="/trends/place.json",
        method="GET",
        version="1.1",
        rate_limit_requests=75
    )
    
    # Personalized trends endpoint (v2 - user context required)
    GET_PERSONALIZED_TRENDS = APIEndpoint(
        path="/users/personalized_trends",
        method="GET",
        version="2",
        rate_limit_requests=75
    )
    
    @classmethod
    def get_full_url(cls, endpoint: APIEndpoint, **path_params) -> str:
        """Get full URL for an endpoint with path parameters"""
        base_url = cls.BASE_URL_V2 if endpoint.version == "2" else cls.BASE_URL_V1_1
        path = endpoint.path.format(**path_params)
        return f"{base_url}{path}"