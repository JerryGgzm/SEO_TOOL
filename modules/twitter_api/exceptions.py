"""Twitter API specific exceptions""" 
from typing import Optional, Dict, Any
import json

class TwitterAPIError(Exception):
    """Base exception for Twitter API errors"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 error_code: Optional[str] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.response_data = response_data or {}
        super().__init__(self.message)
    
    def __str__(self):
        error_details = f"TwitterAPIError: {self.message}"
        if self.status_code:
            error_details += f" (HTTP {self.status_code})"
        if self.error_code:
            error_details += f" (Code: {self.error_code})"
        return error_details

class RateLimitError(TwitterAPIError):
    """Raised when API rate limit is exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded", 
                 reset_time: Optional[int] = None, remaining: int = 0):
        super().__init__(message, status_code=429)
        self.reset_time = reset_time
        self.remaining = remaining
    
    def __str__(self):
        import time
        from datetime import datetime, timedelta
        
        error_msg = f"TwitterAPIError: {self.message} (HTTP 429)"
        
        # Add rate limit details
        error_msg += f"\n📊 速率限制详情:"
        error_msg += f"\n  • 剩余请求次数: {self.remaining}"
        
        if self.reset_time and self.reset_time > 0:
            try:
                current_time = int(time.time())
                wait_seconds = self.reset_time - current_time
                
                if wait_seconds > 0:
                    # Convert to minutes and seconds
                    wait_minutes = wait_seconds // 60
                    wait_seconds_remainder = wait_seconds % 60
                    
                    reset_datetime = datetime.fromtimestamp(self.reset_time)
                    error_msg += f"\n  • 限制重置时间: {reset_datetime.strftime('%H:%M:%S')}"
                    
                    if wait_minutes > 0:
                        error_msg += f"\n  ⏰ 还需等待: {wait_minutes}分{wait_seconds_remainder}秒"
                    else:
                        error_msg += f"\n  ⏰ 还需等待: {wait_seconds_remainder}秒"
                        
                    error_msg += f"\n💡 建议: 请等待后重试，或使用调度功能分散发布时间"
                else:
                    error_msg += f"\n  ✅ 速率限制应该已重置，可以重试"
            except:
                error_msg += f"\n  ⏰ 重置时间戳: {self.reset_time}"
        else:
            error_msg += f"\n  ⏰ 建议等待15-30分钟后重试"
            
        return error_msg

class AuthenticationError(TwitterAPIError):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)

class TwitterAPINotFoundError(TwitterAPIError):
    """Raised when requested resource is not found"""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)

class TwitterAPIBadRequestError(TwitterAPIError):
    """Raised when request is malformed"""
    
    def __init__(self, message: str = "Bad request", validation_errors: Optional[list] = None):
        super().__init__(message, status_code=400)
        self.validation_errors = validation_errors or []

class TwitterAPIServerError(TwitterAPIError):
    """Raised when Twitter API returns server error"""
    
    def __init__(self, message: str = "Twitter API server error"):
        super().__init__(message, status_code=500)