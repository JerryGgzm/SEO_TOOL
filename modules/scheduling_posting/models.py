"""Scheduling and posting data models"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from enum import Enum
import uuid

class PostStatus(str, Enum):
    """Post status enumeration"""
    SCHEDULED = "scheduled"
    POSTING = "posting"
    POSTED = "posted"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class PostPriority(str, Enum):
    """Post priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class ContentType(str, Enum):
    """Content types for posting"""
    TWEET = "tweet"
    REPLY = "reply"
    THREAD = "thread"
    QUOTE_TWEET = "quote_tweet"

class PostingRule(BaseModel):
    """Posting rule configuration"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    founder_id: str
    name: str = Field(..., description="Rule name")
    description: Optional[str] = None
    is_active: bool = Field(default=True)
    
    # Time constraints
    posting_hours_start: int = Field(default=9, ge=0, le=23, description="Start hour (24h format)")
    posting_hours_end: int = Field(default=21, ge=0, le=23, description="End hour (24h format)")
    posting_days: List[int] = Field(default=[1, 2, 3, 4, 5], description="Days of week (1=Monday)")
    timezone: str = Field(default="UTC")
    
    # Frequency constraints
    max_posts_per_hour: int = Field(default=2, ge=1, le=10)
    max_posts_per_day: int = Field(default=5, ge=1, le=50)
    min_interval_minutes: int = Field(default=30, ge=5, le=1440)
    
    # Content type restrictions
    allowed_content_types: List[ContentType] = Field(default=[ContentType.TWEET, ContentType.REPLY])
    
    # Priority handling
    priority_boost_hours: List[int] = Field(default=[], description="Hours when priority is boosted")
    high_priority_override: bool = Field(default=True, description="Allow high priority to override rules")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('posting_hours_end')
    def validate_posting_hours(cls, v, values):
        start = values.get('posting_hours_start', 0)
        if v <= start:
            raise ValueError("End hour must be after start hour")
        return v
    
    @validator('posting_days')
    def validate_posting_days(cls, v):
        if not v:
            raise ValueError("At least one posting day must be specified")
        if any(day < 1 or day > 7 for day in v):
            raise ValueError("Posting days must be between 1 (Monday) and 7 (Sunday)")
        return sorted(list(set(v)))

class ScheduledPost(BaseModel):
    """Scheduled post data model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    founder_id: str
    content_draft_id: str
    
    # Content details
    content_text: str = Field(..., min_length=1, max_length=10000)
    content_type: ContentType
    hashtags: List[str] = Field(default=[])
    keywords: List[str] = Field(default=[])
    
    # Scheduling information
    scheduled_time: datetime
    priority: PostPriority = Field(default=PostPriority.NORMAL)
    status: PostStatus = Field(default=PostStatus.SCHEDULED)
    
    # Metadata
    generation_metadata: Dict[str, Any] = Field(default={})
    posting_rules_applied: List[str] = Field(default=[], description="IDs of rules that affected scheduling")
    
    # Posting results
    posted_at: Optional[datetime] = None
    posted_tweet_id: Optional[str] = None
    posting_error: Optional[str] = None
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    
    # Thread/reply specific
    parent_tweet_id: Optional[str] = None  # For replies
    thread_position: Optional[int] = None  # For threads
    thread_id: Optional[str] = None  # Group threads together
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('scheduled_time')
    def validate_scheduled_time(cls, v):
        if v <= datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")
        return v
    
    @validator('content_text')
    def validate_content_length(cls, v, values):
        content_type = values.get('content_type')
        if content_type == ContentType.TWEET and len(v) > 280:
            raise ValueError("Tweet content cannot exceed 280 characters")
        return v

class PostingQueue(BaseModel):
    """Posting queue with multiple priority levels"""
    urgent_posts: List[ScheduledPost] = Field(default=[])
    high_priority_posts: List[ScheduledPost] = Field(default=[])
    normal_priority_posts: List[ScheduledPost] = Field(default=[])
    low_priority_posts: List[ScheduledPost] = Field(default=[])
    
    @property
    def total_posts(self) -> int:
        return (len(self.urgent_posts) + len(self.high_priority_posts) + 
                len(self.normal_priority_posts) + len(self.low_priority_posts))
    
    def get_next_post(self) -> Optional[ScheduledPost]:
        """Get the next post to publish based on priority"""
        # Check each priority level in order
        for queue in [self.urgent_posts, self.high_priority_posts, 
                     self.normal_priority_posts, self.low_priority_posts]:
            if queue:
                # Return the earliest scheduled post in this priority level
                return min(queue, key=lambda p: p.scheduled_time)
        return None
    
    def add_post(self, post: ScheduledPost):
        """Add post to appropriate priority queue"""
        if post.priority == PostPriority.URGENT:
            self.urgent_posts.append(post)
        elif post.priority == PostPriority.HIGH:
            self.high_priority_posts.append(post)
        elif post.priority == PostPriority.NORMAL:
            self.normal_priority_posts.append(post)
        else:
            self.low_priority_posts.append(post)
    
    def remove_post(self, post_id: str) -> bool:
        """Remove post from queue by ID"""
        for queue in [self.urgent_posts, self.high_priority_posts, 
                     self.normal_priority_posts, self.low_priority_posts]:
            for i, post in enumerate(queue):
                if post.id == post_id:
                    queue.pop(i)
                    return True
        return False

class SchedulingRequest(BaseModel):
    """Request to schedule content for posting"""
    content_draft_id: str
    founder_id: str
    priority: PostPriority = Field(default=PostPriority.NORMAL)
    preferred_time: Optional[datetime] = None
    force_schedule: bool = Field(default=False, description="Override posting rules if needed")
    custom_delay_minutes: Optional[int] = Field(None, ge=0, le=10080, description="Custom delay in minutes")

class SchedulingResult(BaseModel):
    """Result of scheduling operation"""
    success: bool
    scheduled_post_id: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    message: str
    rules_violations: List[str] = Field(default=[])
    adjusted_from_preferred: bool = Field(default=False)

class PostingStatistics(BaseModel):
    """Posting statistics for a founder"""
    founder_id: str
    period_start: datetime
    period_end: datetime
    
    total_scheduled: int = 0
    total_posted: int = 0
    total_failed: int = 0
    total_cancelled: int = 0
    
    posts_by_hour: Dict[int, int] = Field(default={})
    posts_by_day: Dict[str, int] = Field(default={})
    posts_by_content_type: Dict[str, int] = Field(default={})
    
    avg_posting_delay_minutes: float = 0.0
    success_rate: float = 0.0
    
    peak_posting_hours: List[int] = Field(default=[])
    most_active_days: List[str] = Field(default=[])

class PostingBatch(BaseModel):
    """Batch posting operation"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    founder_id: str
    batch_name: str
    content_draft_ids: List[str]
    
    # Batch scheduling options
    start_time: datetime
    interval_minutes: int = Field(default=60, ge=5, le=1440)
    priority: PostPriority = Field(default=PostPriority.NORMAL)
    
    # Results
    scheduled_posts: List[str] = Field(default=[])
    failed_schedules: List[str] = Field(default=[])
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('content_draft_ids')
    def validate_content_draft_ids(cls, v):
        if not v:
            raise ValueError("At least one content draft ID must be provided")
        if len(v) > 50:
            raise ValueError("Batch cannot exceed 50 items")
        return v