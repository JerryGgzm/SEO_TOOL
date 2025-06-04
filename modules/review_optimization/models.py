"""Data models for review optimization"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

class ReviewStatus(str, Enum):
    """Status of content review"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"

class ReviewAction(str, Enum):
    """Available actions for review"""
    APPROVE = "approve"
    REJECT = "reject"
    EDIT = "edit"
    SCHEDULE = "schedule"
    REQUEST_REVISION = "request_revision"

class ContentEdit(BaseModel):
    """Content edit history"""
    field: str = Field(..., description="Field that was edited")
    old_value: str = Field(..., description="Previous value")
    new_value: str = Field(..., description="New value")
    edited_at: datetime = Field(default_factory=datetime.utcnow)
    edited_by: str = Field(..., description="User ID who made the edit")

class ReviewFeedback(BaseModel):
    """Feedback on reviewed content"""
    rating: int = Field(..., ge=1, le=5, description="Quality rating 1-5")
    comments: Optional[str] = Field(None, description="Review comments")
    improvement_suggestions: List[str] = Field(default=[], description="Improvement suggestions")
    seo_feedback: Optional[Dict[str, Any]] = Field(None, description="SEO-specific feedback")

class ReviewItem(BaseModel):
    """Review item model"""
    id: str = Field(..., description="Review item ID")
    content_draft_id: str = Field(..., description="Reference to content draft")
    founder_id: str = Field(..., description="Founder ID")
    
    # Content details
    content_type: str = Field(..., description="Type of content (tweet, reply, thread)")
    original_content: str = Field(..., description="Original AI-generated content")
    current_content: str = Field(..., description="Current content (after edits)")
    
    # Generation context
    trend_context: Dict[str, Any] = Field(default={}, description="Trend that triggered generation")
    generation_reason: str = Field(..., description="Why this content was generated")
    ai_confidence_score: float = Field(..., ge=0, le=1, description="AI confidence in content quality")
    
    # SEO information
    seo_suggestions: Dict[str, Any] = Field(default={}, description="SEO optimization suggestions")
    hashtags: List[str] = Field(default=[], description="Suggested hashtags")
    keywords: List[str] = Field(default=[], description="Target keywords")
    
    # Review metadata
    status: ReviewStatus = Field(default=ReviewStatus.PENDING)
    review_priority: int = Field(default=5, ge=1, le=10, description="Review priority (1=lowest, 10=highest)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = Field(None, description="When the review was completed")
    reviewed_by: Optional[str] = Field(None, description="User ID who reviewed")
    
    # Edit history
    edit_history: List[ContentEdit] = Field(default=[], description="History of edits")
    
    # Scheduling information
    scheduled_time: Optional[datetime] = Field(None, description="Scheduled publishing time")
    
    # Feedback
    feedback: Optional[ReviewFeedback] = Field(None, description="Review feedback")
    
    @validator('current_content')
    def validate_content_length(cls, v, values):
        """Validate content length based on type"""
        content_type = values.get('content_type', 'tweet')
        if content_type == 'tweet' and len(v) > 280:
            raise ValueError('Tweet content cannot exceed 280 characters')
        return v

class ReviewStatistics(BaseModel):
    """Statistics for review performance"""
    total_items: int = Field(default=0, description="Total items reviewed")
    pending_items: int = Field(default=0, description="Items pending review")
    approved_items: int = Field(default=0, description="Items approved")
    rejected_items: int = Field(default=0, description="Items rejected")
    
    avg_review_time_minutes: float = Field(default=0.0, description="Average time to review")
    avg_ai_confidence: float = Field(default=0.0, description="Average AI confidence score")
    avg_feedback_rating: float = Field(default=0.0, description="Average feedback rating")
    
    approval_rate: float = Field(default=0.0, description="Percentage of items approved")
    edit_rate: float = Field(default=0.0, description="Percentage of items edited before approval")
    
    top_rejection_reasons: List[str] = Field(default=[], description="Common rejection reasons")
    top_edit_types: List[str] = Field(default=[], description="Most edited fields")
    
    time_period_days: int = Field(default=30, description="Statistics time period")

class ReviewBatchRequest(BaseModel):
    """Batch review operations request"""
    item_ids: List[str] = Field(..., min_items=1, description="Items to process")
    action: ReviewAction = Field(..., description="Action to perform")
    feedback: Optional[ReviewFeedback] = Field(None, description="Batch feedback")
    scheduled_time: Optional[datetime] = Field(None, description="For batch scheduling")

class ReviewFilterRequest(BaseModel):
    """Filter request for review items"""
    status: Optional[ReviewStatus] = None
    content_type: Optional[str] = None
    priority_min: Optional[int] = Field(None, ge=1, le=10)
    priority_max: Optional[int] = Field(None, ge=1, le=10)
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    ai_confidence_min: Optional[float] = Field(None, ge=0, le=1)
    ai_confidence_max: Optional[float] = Field(None, ge=0, le=1)
    has_edits: Optional[bool] = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)