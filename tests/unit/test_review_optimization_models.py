"""Test cases for Review Optimization Module - Models

This module tests all the data models used in the review optimization process,
including validation logic, enum behaviors, and model relationships.
"""
import pytest
from datetime import datetime, timezone
from typing import List
import uuid

from modules.review_optimization.models import (
    ReviewDecision, DraftStatus, ContentPriority,
    ReviewFeedback, ContentEdit, ReviewDecisionRequest,
    BatchReviewRequest, BatchReviewDecision, ContentRegenerationRequest,
    StatusUpdateRequest, ContentDraftReview, ReviewHistoryItem,
    ReviewSummary, ReviewAnalytics, RegenerationResult, ReviewQueue,
    ReviewPreferences, ContentComparisonResult
)


class TestEnums:
    """Test enum values and behavior"""
    
    def test_review_decision_enum(self):
        """Test ReviewDecision enum values"""
        assert ReviewDecision.APPROVE == "approve"
        assert ReviewDecision.EDIT_AND_APPROVE == "edit_and_approve"
        assert ReviewDecision.REJECT == "reject"
        
        # Test all valid values
        valid_values = ["approve", "edit_and_approve", "reject"]
        for value in valid_values:
            decision = ReviewDecision(value)
            assert decision.value == value
    
    def test_draft_status_enum(self):
        """Test DraftStatus enum values"""
        expected_statuses = [
            "pending_review", "approved", "rejected", 
            "scheduled", "posted", "editing"
        ]
        
        for status in expected_statuses:
            draft_status = DraftStatus(status)
            assert draft_status.value == status
    
    def test_content_priority_enum(self):
        """Test ContentPriority enum values"""
        assert ContentPriority.HIGH == "high"
        assert ContentPriority.MEDIUM == "medium"
        assert ContentPriority.LOW == "low"


class TestReviewFeedback:
    """Test ReviewFeedback model"""
    
    def test_create_basic_feedback(self):
        """Test creating basic feedback"""
        feedback = ReviewFeedback(feedback_text="This content is very good")
        
        assert feedback.feedback_text == "This content is very good"
        assert feedback.improvement_suggestions == []
        assert feedback.style_preferences == {}
        assert feedback.tone_adjustments is None
        assert feedback.target_audience_notes is None
    
    def test_create_detailed_feedback(self):
        """Test creating detailed feedback"""
        feedback = ReviewFeedback(
            feedback_text="Content quality is high, but needs some improvements",
            improvement_suggestions=["Add more data support", "Optimize title"],
            style_preferences={"tone": "professional", "length": "medium"},
            tone_adjustments="Make it more formal",
            target_audience_notes="Mainly for tech entrepreneurs"
        )
        
        assert feedback.feedback_text == "Content quality is high, but needs some improvements"
        assert len(feedback.improvement_suggestions) == 2
        assert feedback.style_preferences["tone"] == "professional"
        assert feedback.tone_adjustments == "Make it more formal"
        assert feedback.target_audience_notes == "Mainly for tech entrepreneurs"


class TestContentEdit:
    """Test ContentEdit model"""
    
    def test_create_content_edit(self):
        """Test creating content edit"""
        now = datetime.utcnow()
        edit = ContentEdit(
            original_content="Original content",
            edited_content="Edited content",
            edit_reason="Improve readability",
            edit_timestamp=now,
            editor_id="user_123"
        )
        
        assert edit.original_content == "Original content"
        assert edit.edited_content == "Edited content"
        assert edit.edit_reason == "Improve readability"
        assert edit.edit_timestamp == now
        assert edit.editor_id == "user_123"
    
    def test_edit_with_default_timestamp(self):
        """Test edit with auto-generated timestamp"""
        edit = ContentEdit(
            original_content="Original content",
            edited_content="New content",
            editor_id="user_123"
        )
        
        assert edit.edit_timestamp is not None
        assert isinstance(edit.edit_timestamp, datetime)


class TestReviewDecisionRequest:
    """Test ReviewDecisionRequest model and validation"""
    
    def test_approve_decision(self):
        """Test approve decision request"""
        request = ReviewDecisionRequest(
            decision=ReviewDecision.APPROVE,
            feedback="Content is very good",
            tags=["AI", "startup"]
        )
        
        assert request.decision == ReviewDecision.APPROVE
        assert request.edited_content is None
        assert request.feedback == "Content is very good"
        assert request.tags == ["AI", "startup"]
    
    def test_edit_and_approve_decision_valid(self):
        """Test valid edit_and_approve decision"""
        request = ReviewDecisionRequest(
            decision=ReviewDecision.EDIT_AND_APPROVE,
            edited_content="This is the edited content",
            feedback="Modified the format"
        )
        
        assert request.decision == ReviewDecision.EDIT_AND_APPROVE
        assert request.edited_content == "This is the edited content"
    
    def test_edit_and_approve_validation_error(self):
        """Test validation error when edited_content is missing"""
        with pytest.raises(ValueError, match="edited_content is required"):
            ReviewDecisionRequest(
                decision=ReviewDecision.EDIT_AND_APPROVE,
                feedback="Needs editing"
                # edited_content is missing
            )
    
    def test_reject_decision(self):
        """Test reject decision request"""
        request = ReviewDecisionRequest(
            decision=ReviewDecision.REJECT,
            feedback="Content does not meet requirements",
            reviewer_notes="Need to regenerate"
        )
        
        assert request.decision == ReviewDecision.REJECT
        assert request.feedback == "Content does not meet requirements"
        assert request.reviewer_notes == "Need to regenerate"


class TestBatchReviewRequest:
    """Test BatchReviewRequest model and validation"""
    
    def test_valid_batch_request(self):
        """Test valid batch review request"""
        decisions = [
            BatchReviewDecision(
                draft_id="draft_1",
                decision=ReviewDecision.APPROVE,
                feedback="Very good"
            ),
            BatchReviewDecision(
                draft_id="draft_2",
                decision=ReviewDecision.EDIT_AND_APPROVE,
                edited_content="Edited content",
                feedback="Needs minor changes"
            )
        ]
        
        batch_request = BatchReviewRequest(decisions=decisions)
        
        assert len(batch_request.decisions) == 2
        assert batch_request.decisions[0].draft_id == "draft_1"
        assert batch_request.decisions[1].decision == ReviewDecision.EDIT_AND_APPROVE
    
    def test_batch_size_limit_validation(self):
        """Test batch size limit validation"""
        # Create more than 50 decisions
        decisions = [
            BatchReviewDecision(
                draft_id=f"draft_{i}",
                decision=ReviewDecision.APPROVE
            )
            for i in range(51)
        ]
        
        with pytest.raises(ValueError, match="Batch size cannot exceed 50"):
            BatchReviewRequest(decisions=decisions)


class TestContentDraftReview:
    """Test ContentDraftReview model"""
    
    def test_create_basic_draft(self):
        """Test creating basic draft review"""
        draft = ContentDraftReview(
            founder_id="user_123",
            content_type="trend_analysis",
            original_content="This is the original generated content",
            current_content="This is the current content"
        )
        
        assert draft.founder_id == "user_123"
        assert draft.content_type == "trend_analysis"
        assert draft.status == DraftStatus.PENDING_REVIEW
        assert draft.priority == ContentPriority.MEDIUM
        assert len(draft.id) > 0  # UUID generated
        assert isinstance(draft.created_at, datetime)
        assert isinstance(draft.updated_at, datetime)
    
    def test_draft_with_custom_id(self):
        """Test draft with custom ID"""
        custom_id = str(uuid.uuid4())
        draft = ContentDraftReview(
            id=custom_id,
            founder_id="user_123",
            content_type="experience_sharing",
            original_content="Content",
            current_content="Content"
        )
        
        assert draft.id == custom_id
    
    def test_draft_with_edit_history(self):
        """Test draft with edit history"""
        edit1 = ContentEdit(
            original_content="Original",
            edited_content="Edit 1",
            editor_id="user_123"
        )
        edit2 = ContentEdit(
            original_content="Edit 1",
            edited_content="Edit 2",
            editor_id="user_123"
        )
        
        draft = ContentDraftReview(
            founder_id="user_123",
            content_type="trend_analysis",
            original_content="Original",
            current_content="Edit 2",
            edit_history=[edit1, edit2]
        )
        
        assert len(draft.edit_history) == 2
        assert draft.edit_history[0].edited_content == "Edit 1"
        assert draft.edit_history[1].edited_content == "Edit 2"
    
    def test_draft_with_review_info(self):
        """Test draft with review information"""
        feedback = ReviewFeedback(feedback_text="Needs improvement")
        review_time = datetime.utcnow()
        
        draft = ContentDraftReview(
            founder_id="user_123",
            content_type="trend_analysis",
            original_content="Content",
            current_content="Content",
            reviewed_at=review_time,
            reviewer_id="reviewer_456",
            review_decision=ReviewDecision.EDIT_AND_APPROVE,
            review_feedback=feedback
        )
        
        assert draft.reviewed_at == review_time
        assert draft.reviewer_id == "reviewer_456"
        assert draft.review_decision == ReviewDecision.EDIT_AND_APPROVE
        assert draft.review_feedback.feedback_text == "Needs improvement"


class TestContentRegenerationRequest:
    """Test ContentRegenerationRequest model"""
    
    def test_basic_regeneration_request(self):
        """Test basic regeneration request"""
        request = ContentRegenerationRequest(
            feedback="Needs more technical details",
            style_preferences={"tone": "technical", "length": "long"}
        )
        
        assert request.feedback == "Needs more technical details"
        assert request.style_preferences["tone"] == "technical"
        assert request.target_improvements == []
        assert request.keep_elements == []
        assert request.avoid_elements == []
    
    def test_detailed_regeneration_request(self):
        """Test detailed regeneration request"""
        request = ContentRegenerationRequest(
            feedback="Overall direction is good, but needs optimization",
            style_preferences={"tone": "conversational"},
            target_improvements=["Add specific examples", "Optimize structure"],
            keep_elements=["Core viewpoints", "Data support"],
            avoid_elements=["Overly technical terms", "Long sentences"]
        )
        
        assert len(request.target_improvements) == 2
        assert len(request.keep_elements) == 2
        assert len(request.avoid_elements) == 2
        assert "Add specific examples" in request.target_improvements
        assert "Core viewpoints" in request.keep_elements
        assert "Overly technical terms" in request.avoid_elements


class TestStatusUpdateRequest:
    """Test StatusUpdateRequest model"""
    
    def test_basic_status_update(self):
        """Test basic status update"""
        request = StatusUpdateRequest(
            status=DraftStatus.APPROVED,
            reviewer_notes="Content quality is very high"
        )
        
        assert request.status == DraftStatus.APPROVED
        assert request.updated_content is None
        assert request.reviewer_notes == "Content quality is very high"
        assert request.schedule_time is None
    
    def test_status_update_with_content(self):
        """Test status update with content changes"""
        schedule_time = datetime.utcnow()
        
        request = StatusUpdateRequest(
            status=DraftStatus.SCHEDULED,
            updated_content="This is the updated content",
            reviewer_notes="Scheduled for publication",
            schedule_time=schedule_time
        )
        
        assert request.status == DraftStatus.SCHEDULED
        assert request.updated_content == "This is the updated content"
        assert request.schedule_time == schedule_time


class TestAnalyticsModels:
    """Test analytics-related models"""
    
    def test_review_summary(self):
        """Test ReviewSummary model"""
        summary = ReviewSummary(
            total_pending=5,
            total_approved=20,
            total_rejected=3,
            total_edited=8,
            avg_quality_score=0.82,
            approval_rate=87.5,
            most_common_tags=["AI", "startup", "technology"],
            review_velocity=2.5
        )
        
        assert summary.total_pending == 5
        assert summary.total_approved == 20
        assert summary.approval_rate == 87.5
        assert len(summary.most_common_tags) == 3
        assert summary.review_velocity == 2.5
    
    def test_review_analytics(self):
        """Test ReviewAnalytics model"""
        analytics = ReviewAnalytics(
            period_days=30,
            total_reviews=50,
            decision_breakdown={
                "approve": 30,
                "edit_and_approve": 15,
                "reject": 5
            },
            content_type_breakdown={
                "trend_analysis": 25,
                "experience_sharing": 20,
                "news_commentary": 5
            },
            average_review_time_minutes=8.5,
            quality_trend=[
                {"date": "2024-01-01", "avg_quality_score": 0.75, "review_count": 5},
                {"date": "2024-01-02", "avg_quality_score": 0.82, "review_count": 7}
            ],
            top_rejection_reasons=["Content too short", "Lack of data support", "Inappropriate tone"],
            productivity_metrics={
                "reviews_per_day": 1.67,
                "approval_rate": 0.90,
                "edit_rate": 0.30
            }
        )
        
        assert analytics.period_days == 30
        assert analytics.total_reviews == 50
        assert analytics.decision_breakdown["approve"] == 30
        assert len(analytics.quality_trend) == 2
        assert len(analytics.top_rejection_reasons) == 3
        assert analytics.productivity_metrics["approval_rate"] == 0.90
    
    def test_review_queue(self):
        """Test ReviewQueue model"""
        draft1 = ContentDraftReview(
            founder_id="user_123",
            content_type="trend_analysis",
            original_content="Content 1",
            current_content="Content 1",
            priority=ContentPriority.HIGH
        )
        
        draft2 = ContentDraftReview(
            founder_id="user_123",
            content_type="experience_sharing",
            original_content="Content 2",
            current_content="Content 2",
            priority=ContentPriority.MEDIUM
        )
        
        queue = ReviewQueue(
            founder_id="user_123",
            pending_drafts=[draft1, draft2],
            high_priority_count=1,
            medium_priority_count=1,
            low_priority_count=0,
            oldest_pending_hours=12.5,
            estimated_review_time_minutes=20
        )
        
        assert queue.founder_id == "user_123"
        assert len(queue.pending_drafts) == 2
        assert queue.high_priority_count == 1
        assert queue.medium_priority_count == 1
        assert queue.oldest_pending_hours == 12.5
        assert queue.estimated_review_time_minutes == 20


class TestRegenerationResult:
    """Test RegenerationResult model"""
    
    def test_regeneration_result(self):
        """Test regeneration result model"""
        result = RegenerationResult(
            draft_id="original_draft_123",
            new_content="This is the regenerated content with more details and improvements.",
            improvements_made=[
                "Added specific data support",
                "Optimized paragraph structure",
                "Enhanced readability"
            ],
            generation_metadata={
                "model_version": "v2.1",
                "generation_time": 2.3,
                "confidence_score": 0.89
            },
            quality_score=0.92,
            seo_suggestions={
                "keywords": ["AI startup", "tech trends"],
                "hashtags": ["#AI", "#startup", "#technology"]
            }
        )
        
        assert result.draft_id == "original_draft_123"
        assert "regenerated content" in result.new_content
        assert len(result.improvements_made) == 3
        assert result.quality_score == 0.92
        assert result.generation_metadata["model_version"] == "v2.1"
        assert isinstance(result.regeneration_timestamp, datetime)


class TestContentComparisonResult:
    """Test ContentComparisonResult model"""
    
    def test_comparison_result(self):
        """Test content comparison result"""
        result = ContentComparisonResult(
            draft_id="draft_123",
            original_content="This is the original content",
            edited_content="This is the edited content with more details.",
            changes_summary={
                "length_change": 15,
                "word_count_change": 8,
                "hashtag_changes": 2,
                "question_added": True
            },
            improvement_score=0.75,
            seo_impact={
                "keyword_density_improved": True,
                "hashtag_optimization": True,
                "length_optimization": True
            },
            readability_impact={
                "avg_word_length_change": -0.3,
                "sentence_count_change": 1,
                "readability_improved": True
            },
            engagement_prediction={
                "predicted_engagement_change": 0.2,
                "engagement_elements_added": ["questions", "call_to_action"],
                "confidence_level": 0.8
            }
        )
        
        assert result.draft_id == "draft_123"
        assert result.improvement_score == 0.75
        assert result.changes_summary["question_added"] is True
        assert result.seo_impact["hashtag_optimization"] is True
        assert result.readability_impact["readability_improved"] is True
        assert len(result.engagement_prediction["engagement_elements_added"]) == 2


if __name__ == "__main__":
    pytest.main([__file__]) 