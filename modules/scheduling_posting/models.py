"""Scheduling and Posting Module - Data Models

This module defines the data models for content scheduling and publishing workflows.
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid

class PublishStatus(str, Enum):
    """Status of content publishing"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    POSTED = "posted"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY_PENDING = "retry_pending"

class ScheduleFrequency(str, Enum):
    """Frequency options for automated scheduling"""
    IMMEDIATE = "immediate"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"

class PublishingRule(str, Enum):
    """Types of publishing rules"""
    TIME_WINDOW = "time_window"
    FREQUENCY_LIMIT = "frequency_limit"
    CONTENT_SPACING = "content_spacing"
    PLATFORM_SPECIFIC = "platform_specific"

class TimeZoneInfo(BaseModel):
    """Timezone information for scheduling"""
    timezone: str = Field(default="UTC", description="Timezone identifier")
    offset_hours: int = Field(default=0, description="UTC offset in hours")
    dst_active: bool = Field(default=False, description="Daylight saving time active")

class SchedulingPreferences(BaseModel):
    """User preferences for content scheduling"""
    founder_id: str = Field(..., min_length=1, description="Founder ID")
    default_timezone: str = Field(default="UTC", description="Default timezone")
    auto_schedule_enabled: bool = Field(default=False, description="Enable automatic scheduling")
    preferred_posting_times: List[str] = Field(default=[], description="Preferred posting times (HH:MM format)")
    max_posts_per_day: int = Field(default=5, description="Maximum posts per day")
    min_interval_minutes: int = Field(default=60, description="Minimum interval between posts")
    avoid_weekends: bool = Field(default=False, description="Avoid posting on weekends")
    quiet_hours_start: Optional[str] = Field(None, description="Quiet hours start time (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="Quiet hours end time (HH:MM)")

class PublishingError(BaseModel):
    """Error information for failed publishing attempts"""
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Human-readable error message")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    last_retry_at: Optional[datetime] = Field(None, description="Last retry timestamp")
    is_retryable: bool = Field(default=True, description="Whether error is retryable")
    technical_details: Dict[str, Any] = Field(default={}, description="Technical error details")

# ScheduledContent model deprecated - functionality moved to GeneratedContentDraft
# This class is kept for API compatibility but maps to GeneratedContentDraft internally
class ScheduledContent(BaseModel):
    """
    DEPRECATED: Scheduled content item - now maps to GeneratedContentDraft
    
    This model is maintained for backward compatibility but all data is stored
    in the generated_content_drafts table. New code should work directly with
    GeneratedContentDraft objects.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Content draft ID (same as content_draft_id)")
    content_draft_id: str = Field(..., description="ID of the content draft (same as id)")
    founder_id: str = Field(..., description="Founder ID")
    scheduled_time: datetime = Field(..., description="Scheduled publishing time")
    timezone_info: TimeZoneInfo = Field(default_factory=TimeZoneInfo)
    status: PublishStatus = Field(default=PublishStatus.SCHEDULED)
    
    # Publishing details  
    posted_at: Optional[datetime] = Field(None, description="Actual posting time")
    posted_tweet_id: Optional[str] = Field(None, description="Posted tweet ID")
    platform: str = Field(default="twitter", description="Publishing platform")
    
    # Error handling
    error_info: Optional[PublishingError] = Field(None, description="Error information if failed")
    retry_count: int = Field(default=0, description="Current retry count")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="User who scheduled the content")
    priority: int = Field(default=5, description="Publishing priority (1-10)")
    tags: List[str] = Field(default=[], description="Content tags")
    
    @classmethod
    def from_content_draft(cls, draft) -> "ScheduledContent":
        """Create ScheduledContent from GeneratedContentDraft for compatibility"""
        return cls(
            id=str(draft.id),
            content_draft_id=str(draft.id),
            founder_id=str(draft.founder_id),
            scheduled_time=draft.scheduled_post_time,
            status=PublishStatus(draft.status) if hasattr(PublishStatus, draft.status.upper()) else PublishStatus.SCHEDULED,
            posted_at=getattr(draft, 'posted_at', None),
            posted_tweet_id=getattr(draft, 'posted_tweet_id', None),
            platform=getattr(draft, 'platform', 'twitter'),
            retry_count=getattr(draft, 'retry_count', 0),
            max_retries=getattr(draft, 'max_retries', 3),
            created_at=draft.created_at,
            updated_at=getattr(draft, 'updated_at', draft.created_at),
            created_by=str(getattr(draft, 'created_by', draft.founder_id)),
            priority=getattr(draft, 'priority', 5),
            tags=getattr(draft, 'tags_list', []) if hasattr(draft, 'tags_list') else []
        )

class ScheduleRequest(BaseModel):
    """Request to schedule content for publishing"""
    content_id: str = Field(..., description="Content draft ID")
    scheduled_time: datetime = Field(..., description="Scheduled publishing time")
    timezone: str = Field(default="UTC", description="Timezone for scheduling")
    priority: int = Field(default=5, ge=1, le=10, description="Publishing priority")
    tags: List[str] = Field(default=[], description="Optional tags")
    skip_rules_check: bool = Field(default=False, description="Skip publishing rules validation for demo purposes")
    
    @field_validator('scheduled_time')
    @classmethod
    def validate_future_time(cls, v):
        """Ensure scheduled time is in the future"""
        if v <= datetime.utcnow():
            raise ValueError('Scheduled time must be in the future')
        return v

class BatchScheduleRequest(BaseModel):
    """Request to schedule multiple content items"""
    content_ids: List[str] = Field(..., description="List of content draft IDs")
    schedule_time: Optional[datetime] = Field(None, description="Common schedule time")
    schedule_pattern: Optional[Dict[str, Any]] = Field(None, description="Scheduling pattern")
    timezone: str = Field(default="UTC", description="Timezone for scheduling")
    stagger_minutes: int = Field(default=0, description="Minutes to stagger between posts")
    
    @field_validator('content_ids')
    @classmethod
    def validate_batch_size(cls, v):
        """Validate batch size"""
        if len(v) > 50:
            raise ValueError('Batch size cannot exceed 50 items')
        return v

class PublishRequest(BaseModel):
    """Request to immediately publish content"""
    content_id: str = Field(..., description="Content draft ID")
    force_publish: bool = Field(default=False, description="Force publish ignoring rules")
    skip_rules_check: bool = Field(default=False, description="Skip publishing rules validation")
    custom_message: Optional[str] = Field(None, description="Custom message override")

class BatchPublishRequest(BaseModel):
    """Request to publish multiple content items"""
    content_ids: List[str] = Field(..., description="List of content draft IDs")
    schedule_time: Optional[datetime] = Field(None, description="Optional scheduled time")
    force_publish: bool = Field(default=False, description="Force publish ignoring rules")
    stagger_minutes: int = Field(default=5, description="Minutes between publications")

class StatusUpdateRequest(BaseModel):
    """Request to update publishing status"""
    status: PublishStatus = Field(..., description="New status")
    posted_tweet_id: Optional[str] = Field(None, description="Posted tweet ID if successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    technical_details: Dict[str, Any] = Field(default={}, description="Technical details")
    retry_scheduled: bool = Field(default=False, description="Whether retry is scheduled")

class PublishingHistoryItem(BaseModel):
    """Item in publishing history"""
    content_id: str = Field(..., description="Content draft ID")
    scheduled_content_id: str = Field(..., description="Scheduled content ID")
    content_preview: str = Field(..., description="Content preview")
    scheduled_time: datetime = Field(..., description="Originally scheduled time")
    posted_at: Optional[datetime] = Field(None, description="Actual posting time")
    status: PublishStatus = Field(..., description="Final status")
    posted_tweet_id: Optional[str] = Field(None, description="Posted tweet ID")
    platform: str = Field(..., description="Publishing platform")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(default=0, description="Number of retries")
    tags: List[str] = Field(default=[], description="Content tags")

class PublishingAnalytics(BaseModel):
    """Publishing analytics data"""
    total_scheduled: int = Field(..., description="Total scheduled items")
    total_published: int = Field(..., description="Total published items")
    total_failed: int = Field(..., description="Total failed items")
    success_rate: float = Field(..., description="Publishing success rate")
    avg_publish_delay_minutes: float = Field(default=0.0, description="Average delay from scheduled time")
    most_common_errors: List[str] = Field(default=[], description="Most common error types")
    publishing_times_distribution: Dict[str, int] = Field(default={}, description="Distribution by hour")
    platform_breakdown: Dict[str, int] = Field(default={}, description="Publishing by platform")

class RuleCheckRequest(BaseModel):
    """Request to check publishing rules"""
    user_id: str = Field(..., description="User ID")
    content_type: Optional[str] = Field(None, description="Content type to check")
    proposed_time: Optional[datetime] = Field(None, description="Proposed publishing time")
    content_id: Optional[str] = Field(None, description="Specific content ID")

class RuleCheckResult(BaseModel):
    """Result of publishing rules check"""
    can_publish: bool = Field(..., description="Whether content can be published")
    violations: List[str] = Field(default=[], description="Rule violations found")
    recommendations: List[str] = Field(default=[], description="Publishing recommendations")
    suggested_times: List[datetime] = Field(default=[], description="Suggested optimal times")
    next_available_slot: Optional[datetime] = Field(None, description="Next available publishing slot")
    current_daily_count: int = Field(default=0, description="Current daily post count")
    daily_limit: int = Field(default=0, description="Daily posting limit")

class SchedulingQueueInfo(BaseModel):
    """Information about the scheduling queue"""
    total_pending: int = Field(..., description="Total pending items")
    total_scheduled: int = Field(..., description="Total scheduled items")
    next_publish_time: Optional[datetime] = Field(None, description="Next scheduled publish time")
    queue_by_status: Dict[str, int] = Field(default={}, description="Queue breakdown by status")
    upcoming_24h: int = Field(default=0, description="Items scheduled in next 24 hours")
    overdue_count: int = Field(default=0, description="Overdue items count")
    retry_queue_size: int = Field(default=0, description="Items in retry queue")

class AutoScheduleSettings(BaseModel):
    """Settings for automatic content scheduling"""
    enabled: bool = Field(default=False, description="Enable auto-scheduling")
    frequency: ScheduleFrequency = Field(default=ScheduleFrequency.DAILY)
    preferred_times: List[str] = Field(default=[], description="Preferred posting times")
    content_types: List[str] = Field(default=[], description="Content types to auto-schedule")
    min_quality_score: float = Field(default=0.7, description="Minimum quality score for auto-scheduling")
    max_daily_posts: int = Field(default=3, description="Maximum posts per day")
    respect_quiet_hours: bool = Field(default=True, description="Respect user's quiet hours")
    stagger_minutes: int = Field(default=60, description="Minutes between auto-scheduled posts")

class PublishingConfiguration(BaseModel):
    """Configuration for the publishing system"""
    max_concurrent_publishes: int = Field(default=5, description="Max concurrent publishing operations")
    retry_delays_minutes: List[int] = Field(default=[5, 15, 60], description="Retry delay intervals")
    default_max_retries: int = Field(default=3, description="Default maximum retry attempts")
    publish_timeout_seconds: int = Field(default=30, description="Publishing timeout")
    queue_check_interval_seconds: int = Field(default=60, description="Queue processing interval")
    enable_rule_validation: bool = Field(default=True, description="Enable publishing rule validation")
    enable_analytics_tracking: bool = Field(default=True, description="Enable analytics tracking")
    platform_configs: Dict[str, Dict[str, Any]] = Field(default={}, description="Platform-specific configurations")

class PublishingMetrics(BaseModel):
    """Real-time publishing metrics"""
    queue_size: int = Field(..., description="Current queue size")
    publishing_rate_per_hour: float = Field(..., description="Publishing rate per hour")
    success_rate_24h: float = Field(..., description="Success rate in last 24 hours")
    avg_processing_time_seconds: float = Field(..., description="Average processing time")
    active_publishers: int = Field(..., description="Number of active publishing workers")
    last_successful_publish: Optional[datetime] = Field(None, description="Last successful publish time")
    last_failed_publish: Optional[datetime] = Field(None, description="Last failed publish time")
    error_rate_24h: float = Field(..., description="Error rate in last 24 hours")

class SchedulingRule(BaseModel):
    """Scheduling rule definition"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Rule name")
    rule_type: PublishingRule = Field(..., description="Type of rule")
    enabled: bool = Field(default=True, description="Whether rule is active")
    priority: int = Field(default=5, description="Rule priority")
    conditions: Dict[str, Any] = Field(..., description="Rule conditions")
    actions: Dict[str, Any] = Field(..., description="Rule actions")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ContentQueueItem(BaseModel):
    """Item in the content publishing queue"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content_draft_id: str = Field(..., description="Content draft ID")
    founder_id: str = Field(..., description="Founder ID")
    scheduled_time: datetime = Field(..., description="Scheduled time")
    priority: int = Field(default=5, description="Queue priority")
    status: PublishStatus = Field(default=PublishStatus.PENDING)
    platform: str = Field(default="twitter", description="Target platform")
    retry_count: int = Field(default=0, description="Current retry count")
    last_attempt_at: Optional[datetime] = Field(None, description="Last attempt timestamp")
    lock_acquired_at: Optional[datetime] = Field(None, description="Lock acquisition time")
    lock_acquired_by: Optional[str] = Field(None, description="Worker that acquired lock")
    
    @property
    def is_due(self) -> bool:
        """Check if item is due for publishing"""
        return self.scheduled_time <= datetime.utcnow()
    
    @property
    def is_overdue(self) -> bool:
        """Check if item is overdue"""
        return self.scheduled_time < datetime.utcnow() - timedelta(minutes=5)
    
    @property
    def should_retry(self) -> bool:
        """Check if item should be retried"""
        return (self.status == PublishStatus.FAILED and 
                self.retry_count < 3 and
                self.last_attempt_at and
                self.last_attempt_at < datetime.utcnow() - timedelta(minutes=5))

# Response Models
class ScheduleResponse(BaseModel):
    """Response for scheduling operations"""
    success: bool = Field(..., description="Operation success")
    scheduled_content_id: Optional[str] = Field(None, description="Scheduled content ID")
    scheduled_time: Optional[datetime] = Field(None, description="Scheduled time")
    message: str = Field(..., description="Response message")
    rule_violations: List[str] = Field(default=[], description="Any rule violations")

class PublishResponse(BaseModel):
    """Response for publishing operations"""
    success: bool = Field(..., description="Operation success")
    posted_tweet_id: Optional[str] = Field(None, description="Posted tweet ID")
    posted_at: Optional[datetime] = Field(None, description="Posting timestamp")
    message: str = Field(..., description="Response message")
    error_code: Optional[str] = Field(None, description="Error code if failed")

class BatchOperationResponse(BaseModel):
    """Response for batch operations"""
    total_items: int = Field(..., description="Total items processed")
    successful_items: int = Field(..., description="Successfully processed items")
    failed_items: int = Field(..., description="Failed items")
    results: Dict[str, Union[ScheduleResponse, PublishResponse]] = Field(..., description="Individual results")
    message: str = Field(..., description="Overall operation message")