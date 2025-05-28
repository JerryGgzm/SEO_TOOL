import time
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from threading import Lock
import logging

from .endpoints import APIEndpoint

logger = logging.getLogger(__name__)

class RateLimitInfo:
    """Rate limit information for an endpoint"""
    
    def __init__(self, limit: int, remaining: int, reset_time: int):
        self.limit = limit
        self.remaining = remaining
        self.reset_time = reset_time
        self.last_updated = datetime.utcnow()
    
    def is_exhausted(self) -> bool:
        """Check if rate limit is exhausted"""
        return self.remaining <= 0
    
    def time_until_reset(self) -> int:
        """Get seconds until rate limit resets"""
        current_time = int(time.time())
        return max(0, self.reset_time - current_time)
    
    def should_wait(self, safety_margin: int = 1) -> bool:
        """Check if we should wait before making request"""
        return self.remaining <= safety_margin

class TwitterRateLimiter:
    """Manages Twitter API rate limiting"""
    
    def __init__(self):
        self._rate_limits: Dict[str, RateLimitInfo] = {}
        self._lock = Lock()
    
    def check_rate_limit(self, endpoint_key: str, endpoint: APIEndpoint) -> Optional[int]:
        """
        Check if request can be made without hitting rate limit
        Returns: None if OK, otherwise seconds to wait
        """
        with self._lock:
            rate_info = self._rate_limits.get(endpoint_key)
            
            if not rate_info:
                # No rate limit info yet, assume we can proceed
                return None
            
            if rate_info.should_wait():
                wait_time = rate_info.time_until_reset()
                logger.warning(f"Rate limit reached for {endpoint_key}. Wait {wait_time} seconds.")
                return wait_time
            
            return None
    
    def update_rate_limit(self, endpoint_key: str, response_headers: Dict[str, str]) -> None:
        """Update rate limit info from response headers"""
        try:
            # Twitter API v2 rate limit headers
            limit = int(response_headers.get('x-rate-limit-limit', 0))
            remaining = int(response_headers.get('x-rate-limit-remaining', 0))
            reset_time = int(response_headers.get('x-rate-limit-reset', 0))
            
            with self._lock:
                self._rate_limits[endpoint_key] = RateLimitInfo(limit, remaining, reset_time)
                
            logger.debug(f"Updated rate limit for {endpoint_key}: {remaining}/{limit} remaining")
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse rate limit headers for {endpoint_key}: {e}")
    
    def wait_if_needed(self, endpoint_key: str, endpoint: APIEndpoint) -> None:
        """Wait if rate limit requires it"""
        wait_time = self.check_rate_limit(endpoint_key, endpoint)
        if wait_time and wait_time > 0:
            logger.info(f"Waiting {wait_time} seconds for rate limit reset on {endpoint_key}")
            time.sleep(wait_time)
    
    def get_rate_limit_status(self, endpoint_key: str) -> Optional[Dict[str, Any]]:
        """Get current rate limit status for an endpoint"""
        with self._lock:
            rate_info = self._rate_limits.get(endpoint_key)
            if not rate_info:
                return None
            
            return {
                'limit': rate_info.limit,
                'remaining': rate_info.remaining,
                'reset_time': rate_info.reset_time,
                'time_until_reset': rate_info.time_until_reset(),
                'last_updated': rate_info.last_updated
            }