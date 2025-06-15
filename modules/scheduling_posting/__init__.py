"""Scheduling and Posting Module - Content Publishing and Queue Management

This module provides comprehensive content scheduling and publishing capabilities:

1. **Content Scheduling**: Schedule approved content for automatic publishing
2. **Immediate Publishing**: Publish content directly to Twitter
3. **Batch Operations**: Handle multiple content items simultaneously
4. **Queue Management**: Automated queue processing with retry handling
5. **Rules Engine Integration**: Validate against publishing rules and preferences
6. **Analytics and Reporting**: Track publishing performance and metrics
7. **Error Handling**: Robust error handling with automatic retry mechanisms

Main Components:
- models.py: Data models for scheduling and publishing
- service.py: Business logic and workflow management
- routes.py: FastAPI endpoints for API access
- queue_processor.py: Background queue processing (would be implemented)
- database_operations.py: Database interaction layer (would be implemented)

Key Features:
- Automated scheduling based on user preferences
- Real-time publishing with Twitter API integration
- Comprehensive rule validation and compliance
- Detailed analytics and performance tracking
- Retry mechanisms for failed publications
- Batch processing for efficient operations
- Queue management with priority handling

Integration Points:
- TwitterAPIModule: Direct publishing to Twitter
- RulesEngineModule: Publishing rule validation
- UserProfileModule: User preferences and tokens
- DataFlowManager: Content and scheduling data
- AnalyticsModule: Event tracking and metrics
"""

from .models import (
    # Core publishing models
    PublishStatus,
    ScheduleFrequency,
    PublishingRule,
    TimeZoneInfo,
    
    # User preferences and configuration
    SchedulingPreferences,
    AutoScheduleSettings,
    PublishingConfiguration,
    
    # Content and scheduling models
    ScheduledContent,
    ContentQueueItem,
    PublishingError,
    SchedulingRule,
    
    # Request/Response models
    ScheduleRequest,
    BatchScheduleRequest,
    PublishRequest,
    BatchPublishRequest,
    StatusUpdateRequest,
    RuleCheckRequest,
    
    # Analytics and reporting models
    PublishingHistoryItem,
    PublishingAnalytics,
    PublishingMetrics,
    SchedulingQueueInfo,
    
    # Response models
    ScheduleResponse,
    PublishResponse,
    BatchOperationResponse,
    RuleCheckResult
)

from .service import SchedulingPostingService
from .rules_engine import InternalRulesEngine, RuleSeverity, RuleViolation

__all__ = [
    # Enums
    'PublishStatus',
    'ScheduleFrequency', 
    'PublishingRule',
    
    # Configuration models
    'TimeZoneInfo',
    'SchedulingPreferences',
    'AutoScheduleSettings',
    'PublishingConfiguration',
    
    # Core models
    'ScheduledContent',
    'ContentQueueItem',
    'PublishingError',
    'SchedulingRule',
    
    # Request models
    'ScheduleRequest',
    'BatchScheduleRequest',
    'PublishRequest',
    'BatchPublishRequest',
    'StatusUpdateRequest',
    'RuleCheckRequest',
    
    # Response models
    'ScheduleResponse',
    'PublishResponse',
    'BatchOperationResponse',
    'RuleCheckResult',
    
    # Analytics models
    'PublishingHistoryItem',
    'PublishingAnalytics',
    'PublishingMetrics',
    'SchedulingQueueInfo',
    
    # Service
    'SchedulingPostingService',
    
    # Internal Rules Engine
    'InternalRulesEngine',
    'RuleSeverity', 
    'RuleViolation'
]

# Module version and metadata
__version__ = "1.0.0"
__author__ = "Ideation Platform Team"
__description__ = "Content scheduling and publishing module with Twitter integration"

# Configuration constants
DEFAULT_RETRY_DELAYS = [5, 15, 60]  # minutes
DEFAULT_MAX_RETRIES = 3
DEFAULT_QUEUE_CHECK_INTERVAL = 60  # seconds
DEFAULT_PUBLISH_TIMEOUT = 30  # seconds
DEFAULT_MAX_CONCURRENT_PUBLISHES = 5
DEFAULT_DAILY_POST_LIMIT = 5
DEFAULT_MIN_INTERVAL_MINUTES = 60

# Supported platforms
SUPPORTED_PLATFORMS = ['twitter']

# Publishing status priorities (for queue processing)
STATUS_PRIORITIES = {
    PublishStatus.RETRY_PENDING: 1,  # Highest priority
    PublishStatus.SCHEDULED: 2,
    PublishStatus.PENDING: 3,
    PublishStatus.PUBLISHING: 4,
    PublishStatus.POSTED: 5,
    PublishStatus.FAILED: 6,
    PublishStatus.CANCELLED: 7  # Lowest priority
}

# Error codes for common publishing failures
ERROR_CODES = {
    'NO_ACCESS_TOKEN': 'Twitter access token not available',
    'TWEET_TOO_LONG': 'Tweet content exceeds character limit',
    'TWITTER_API_ERROR': 'Twitter API returned an error',
    'RATE_LIMIT_EXCEEDED': 'Twitter API rate limit exceeded',
    'NETWORK_ERROR': 'Network connection error',
    'CONTENT_NOT_FOUND': 'Content draft not found',
    'PERMISSION_DENIED': 'Insufficient permissions',
    'RULE_VIOLATION': 'Publishing rule violation',
    'DUPLICATE_CONTENT': 'Duplicate content detected',
    'INVALID_SCHEDULE_TIME': 'Invalid scheduling time',
    'QUEUE_PROCESSING_ERROR': 'Queue processing error'
}

# Default time windows for optimal posting
DEFAULT_OPTIMAL_TIMES = [
    "09:00",  # 9 AM
    "13:00",  # 1 PM  
    "17:00",  # 5 PM
    "19:00"   # 7 PM
]

# Weekend handling options
WEEKEND_HANDLING = {
    'ALLOW': 'allow',
    'SKIP': 'skip',
    'MOVE_TO_MONDAY': 'move_to_monday'
}

def create_scheduling_service(data_flow_manager, twitter_client, user_service, 
                            analytics_collector=None):
    """
    Factory function to create a SchedulingPostingService instance
    
    Args:
        data_flow_manager: DataFlowManager instance
        twitter_client: TwitterAPIClient instance
        user_service: UserProfileService instance
        analytics_collector: Optional AnalyticsCollector instance
        
    Returns:
        SchedulingPostingService instance
    """
    return SchedulingPostingService(
        data_flow_manager=data_flow_manager,
        twitter_client=twitter_client,
        user_profile_service=user_service,
        analytics_collector=analytics_collector
    )

def get_default_scheduling_preferences(user_id: str) -> SchedulingPreferences:
    """
    Get default scheduling preferences for a new user
    
    Args:
        user_id: User ID
        
    Returns:
        Default scheduling preferences
    """
    return SchedulingPreferences(
        founder_id=user_id,
        default_timezone="UTC",
        auto_schedule_enabled=False,
        preferred_posting_times=DEFAULT_OPTIMAL_TIMES,
        max_posts_per_day=DEFAULT_DAILY_POST_LIMIT,
        min_interval_minutes=DEFAULT_MIN_INTERVAL_MINUTES,
        avoid_weekends=False,
        quiet_hours_start="22:00",
        quiet_hours_end="08:00"
    )