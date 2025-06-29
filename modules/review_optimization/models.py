"""Review Optimization Module - Data Models

This module defines the data models for the review and optimization process
where founders can review, edit, and approve content drafts before posting.
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from enum import Enum
import uuid

class ReviewDecision(str, Enum):
    """Review decisions available to founders"""
    APPROVE = "approve"
    APPROVE_FOR_LATER = "approve_for_later"
    EDIT_AND_APPROVE = "edit_and_approve"
    EDIT_AND_APPROVE_FOR_LATER = "edit_and_approve_for_later"
    REJECT = "reject"

class DraftStatus(str, Enum):
    """Status of content drafts in the review process"""
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    APPROVED_PENDING_SCHEDULE = "approved_pending_schedule"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"
    POSTED = "posted"
    EDITING = "editing"

class ContentPriority(str, Enum):
    """Priority levels for content drafts"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ReviewFeedback(BaseModel):
    """Feedback provided during review process"""
    feedback_text: str = Field(..., description="Detailed feedback text")
    improvement_suggestions: List[str] = Field(default=[], description="Specific improvement suggestions")
    style_preferences: Dict[str, Any] = Field(default={}, description="Style preferences for future content")
    tone_adjustments: Optional[str] = Field(None, description="Tone adjustment requests")
    target_audience_notes: Optional[str] = Field(None, description="Target audience considerations")

class ContentEdit(BaseModel):
    """Edit information for content drafts"""
    original_content: str = Field(..., description="Original generated content")
    edited_content: str = Field(..., description="User-edited content")
    edit_reason: Optional[str] = Field(None, description="Reason for editing")
    edit_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When edit was made")
    editor_id: str = Field(..., description="ID of person who made the edit")

class ReviewDecisionRequest(BaseModel):
    """Request model for review decisions"""
    decision: ReviewDecision = Field(..., description="Review decision")
    edited_content: Optional[str] = Field(None, description="Edited content if decision is edit_and_approve")
    feedback: Optional[str] = Field(None, description="Optional feedback")
    tags: List[str] = Field(default=[], description="Tags for categorization")
    priority: Optional[ContentPriority] = Field(None, description="Content priority")
    schedule_time: Optional[datetime] = Field(None, description="Scheduled posting time")
    reviewer_notes: Optional[str] = Field(None, description="Internal reviewer notes")

    @model_validator(mode='after')
    def validate_edited_content(self):
        """Validate that edited content is provided when decision is edit_and_approve"""
        if self.decision == ReviewDecision.EDIT_AND_APPROVE and not self.edited_content:
            raise ValueError('edited_content is required')
        return self

class BatchReviewDecision(BaseModel):
    """Individual decision in batch review"""
    draft_id: str = Field(..., description="Draft ID")
    decision: ReviewDecision = Field(..., description="Review decision")
    edited_content: Optional[str] = Field(None, description="Edited content")
    feedback: Optional[str] = Field(None, description="Feedback")
    tags: List[str] = Field(default=[], description="Tags")
    priority: Optional[ContentPriority] = Field(None, description="Priority")

class BatchReviewRequest(BaseModel):
    """Request model for batch review decisions"""
    decisions: List[BatchReviewDecision] = Field(..., description="List of decisions")
    
    @field_validator('decisions')
    @classmethod
    def validate_batch_size(cls, v):
        """Validate batch size"""
        if len(v) > 50:  # Reasonable batch limit
            raise ValueError('Batch size cannot exceed 50 decisions')
        return v

class ContentRegenerationRequest(BaseModel):
    """Request model for content regeneration"""
    feedback: Optional[str] = Field(None, description="Feedback for regeneration")
    style_preferences: Dict[str, Any] = Field(default={}, description="Style preferences")
    target_improvements: List[str] = Field(default=[], description="Specific improvements needed")
    keep_elements: List[str] = Field(default=[], description="Elements to keep from original")
    avoid_elements: List[str] = Field(default=[], description="Elements to avoid")

class StatusUpdateRequest(BaseModel):
    """Request model for status updates"""
    status: DraftStatus = Field(..., description="New status")
    updated_content: Optional[str] = Field(None, description="Updated content")
    reviewer_notes: Optional[str] = Field(None, description="Reviewer notes")
    schedule_time: Optional[datetime] = Field(None, description="Schedule time if status is scheduled")

class ContentDraftReview(BaseModel):
    """Content draft with review information"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    founder_id: str = Field(..., description="Founder ID")
    content_type: str = Field(..., description="Type of content")
    original_content: str = Field(..., description="Original generated content")
    current_content: str = Field(..., description="Current content (may be edited)")
    status: DraftStatus = Field(default=DraftStatus.PENDING_REVIEW)
    priority: ContentPriority = Field(default=ContentPriority.MEDIUM)
    
    # Review information
    reviewed_at: Optional[datetime] = Field(None, description="When review was completed")
    reviewer_id: Optional[str] = Field(None, description="ID of reviewer")
    review_decision: Optional[ReviewDecision] = Field(None, description="Review decision")
    review_feedback: Optional[ReviewFeedback] = Field(None, description="Review feedback")
    
    # Edit history
    edit_history: List[ContentEdit] = Field(default=[], description="History of edits")
    
    # Metadata
    tags: List[str] = Field(default=[], description="Content tags")
    trend_id: Optional[str] = Field(None, description="Associated trend ID")
    generation_metadata: Dict[str, Any] = Field(default={}, description="Generation metadata")
    seo_suggestions: Dict[str, Any] = Field(default={}, description="SEO suggestions")
    quality_score: Optional[float] = Field(None, description="Content quality score")
    
    # Scheduling
    scheduled_time: Optional[datetime] = Field(None, description="Scheduled posting time")
    posted_at: Optional[datetime] = Field(None, description="When content was posted")
    posted_tweet_id: Optional[str] = Field(None, description="Posted tweet ID")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ReviewHistoryItem(BaseModel):
    """Item in review history"""
    draft_id: str = Field(..., description="Draft ID")
    content_preview: str = Field(..., description="Content preview (first 100 chars)")
    status: DraftStatus = Field(..., description="Final status")
    decision: Optional[ReviewDecision] = Field(None, description="Review decision")
    reviewed_at: datetime = Field(..., description="Review timestamp")
    content_type: str = Field(..., description="Content type")
    tags: List[str] = Field(default=[], description="Content tags")
    quality_score: Optional[float] = Field(None, description="Quality score")

class ReviewSummary(BaseModel):
    """Summary of review activities"""
    total_pending: int = Field(..., description="Total pending reviews")
    total_approved: int = Field(..., description="Total approved content")
    total_rejected: int = Field(..., description="Total rejected content")
    total_edited: int = Field(..., description="Total edited content")
    avg_quality_score: float = Field(default=0.0, description="Average quality score")
    approval_rate: float = Field(default=0.0, description="Approval rate percentage")
    most_common_tags: List[str] = Field(default=[], description="Most commonly used tags")
    review_velocity: float = Field(default=0.0, description="Reviews per day")

class ReviewAnalytics(BaseModel):
    """Analytics for review process"""
    period_days: int = Field(..., description="Analysis period in days")
    total_reviews: int = Field(..., description="Total reviews in period")
    decision_breakdown: Dict[str, int] = Field(default={}, description="Breakdown by decision type")
    content_type_breakdown: Dict[str, int] = Field(default={}, description="Breakdown by content type")
    average_review_time_minutes: float = Field(default=0.0, description="Average time to review")
    quality_trend: List[Dict[str, Any]] = Field(default=[], description="Quality score trend over time")
    top_rejection_reasons: List[str] = Field(default=[], description="Most common rejection reasons")
    productivity_metrics: Dict[str, float] = Field(default={}, description="Productivity metrics")

class RegenerationResult(BaseModel):
    """Result of content regeneration"""
    draft_id: str = Field(..., description="Original draft ID")
    new_draft_id: Optional[str] = Field(None, description="Newly created draft ID")
    new_content: str = Field(..., description="Newly generated content")
    improvements_made: List[str] = Field(default=[], description="Improvements made")
    generation_metadata: Dict[str, Any] = Field(default={}, description="Generation metadata")
    quality_score: Optional[float] = Field(None, description="Quality score of new content")
    seo_suggestions: Dict[str, Any] = Field(default={}, description="SEO suggestions")
    regeneration_timestamp: datetime = Field(default_factory=datetime.utcnow)

class ReviewQueue(BaseModel):
    """Review queue information"""
    founder_id: str = Field(..., description="Founder ID")
    pending_drafts: List[ContentDraftReview] = Field(default=[], description="Pending drafts")
    high_priority_count: int = Field(default=0, description="High priority drafts")
    medium_priority_count: int = Field(default=0, description="Medium priority drafts")
    low_priority_count: int = Field(default=0, description="Low priority drafts")
    oldest_pending_hours: Optional[float] = Field(None, description="Hours since oldest pending draft")
    estimated_review_time_minutes: float = Field(default=0.0, description="Estimated total review time")

class ReviewPreferences(BaseModel):
    """User preferences for review process"""
    founder_id: str = Field(..., description="Founder ID")
    auto_approve_threshold: float = Field(default=0.8, description="Quality threshold for auto-approval")
    preferred_review_schedule: List[str] = Field(default=[], description="Preferred review times")
    notification_preferences: Dict[str, bool] = Field(default={}, description="Notification settings")
    default_tags: List[str] = Field(default=[], description="Default tags to apply")
    review_checklist: List[str] = Field(default=[], description="Custom review checklist")
    style_guidelines: Dict[str, Any] = Field(default={}, description="Personal style guidelines")

class ContentComparisonResult(BaseModel):
    """Result of comparing original vs edited content"""
    draft_id: str = Field(..., description="Draft ID")
    original_content: str = Field(..., description="Original content")
    edited_content: str = Field(..., description="Edited content")
    changes_summary: Dict[str, Any] = Field(default={}, description="Summary of changes")
    improvement_score: float = Field(default=0.0, description="Improvement score")
    seo_impact: Dict[str, Any] = Field(default={}, description="SEO impact of changes")
    readability_impact: Dict[str, Any] = Field(default={}, description="Readability impact")
    engagement_prediction: Dict[str, Any] = Field(default={}, description="Predicted engagement impact")