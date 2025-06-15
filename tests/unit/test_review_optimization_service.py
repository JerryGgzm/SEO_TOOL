"""Test cases for Review Optimization Module - Service Layer

This module tests the business logic of the review optimization service,
including integration with dependencies and error handling.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import uuid

from modules.review_optimization.service import ReviewOptimizationService
from modules.review_optimization.models import (
    ContentDraftReview, ReviewDecision, DraftStatus, ContentPriority,
    ReviewDecisionRequest, BatchReviewRequest, BatchReviewDecision,
    ContentRegenerationRequest, StatusUpdateRequest, ReviewFeedback,
    ContentEdit, RegenerationResult
)
from database import DataFlowManager
from modules.content_generation.service import ContentGenerationService
from modules.analytics.collector import AnalyticsCollector


@pytest.fixture
def mock_data_flow_manager():
    """Mock DataFlowManager for testing"""
    mock = Mock()
    
    # Mock draft data
    mock_draft = Mock()
    mock_draft.id = "draft_123"
    mock_draft.founder_id = "user_123"
    mock_draft.content_type = "trend_analysis"
    mock_draft.generated_text = "This is the original generated content"
    mock_draft.current_content = "This is the current content"
    mock_draft.status = "pending_review"
    mock_draft.priority = "medium"
    mock_draft.created_at = datetime.utcnow()
    mock_draft.updated_at = datetime.utcnow()
    mock_draft.tags = ["AI", "startup"]
    mock_draft.analyzed_trend_id = "trend_456"
    mock_draft.ai_generation_metadata = {"quality_score": 0.8}
    mock_draft.seo_suggestions = {"keywords": ["AI", "startup"]}
    mock_draft.quality_score = 0.8
    mock_draft.edit_history = []
    mock_draft.review_feedback = None
    mock_draft.reviewed_at = None
    mock_draft.reviewer_id = None
    mock_draft.review_decision = None
    mock_draft.scheduled_post_time = None
    mock_draft.posted_at = None
    mock_draft.posted_tweet_id = None
    
    # Configure mock methods
    mock.get_pending_content_drafts.return_value = [mock_draft]
    mock.get_content_draft_by_id.return_value = mock_draft
    mock.update_content_draft.return_value = True
    mock.get_review_history.return_value = []
    mock.get_review_summary_data.return_value = {
        'pending_count': 5,
        'approved_count': 20,
        'rejected_count': 3,
        'edited_count': 8,
        'avg_quality_score': 0.82,
        'common_tags': ['AI', 'startup', 'technology']
    }
    mock.get_detailed_review_analytics.return_value = {
        'total_reviews': 50,
        'decision_breakdown': {'approve': 30, 'edit_and_approve': 15, 'reject': 5},
        'content_type_breakdown': {'trend_analysis': 25, 'experience_sharing': 20},
        'avg_review_time_minutes': 8.5,
        'quality_trend': [],
        'top_rejection_reasons': []
    }
    
    return mock


@pytest.fixture
def mock_content_generation_service():
    """Mock ContentGenerationService for testing"""
    mock = Mock()
    mock.regenerate_content_with_seo_feedback = AsyncMock(return_value=["new_draft_456"])
    return mock


@pytest.fixture
def mock_analytics_collector():
    """Mock AnalyticsCollector for testing"""
    mock = Mock()
    mock.record_event = AsyncMock()
    return mock


@pytest.fixture
def review_service(mock_data_flow_manager, mock_content_generation_service, mock_analytics_collector):
    """Create ReviewOptimizationService with mocked dependencies"""
    return ReviewOptimizationService(
        data_flow_manager=mock_data_flow_manager,
        content_generation_service=mock_content_generation_service,
        analytics_collector=mock_analytics_collector
    )


class TestGetPendingDrafts:
    """Test getting pending drafts"""
    
    @pytest.mark.asyncio
    async def test_get_pending_drafts_success(self, review_service, mock_data_flow_manager):
        """Test successful retrieval of pending drafts"""
        result = await review_service.get_pending_drafts("user_123", limit=10, offset=0)
        
        assert len(result) == 1
        assert result[0].founder_id == "user_123"
        assert result[0].status == DraftStatus.PENDING_REVIEW
        mock_data_flow_manager.get_pending_content_drafts.assert_called_once_with("user_123", 10, 0)
    
    @pytest.mark.asyncio
    async def test_get_pending_drafts_empty(self, review_service, mock_data_flow_manager):
        """Test handling of no pending drafts"""
        mock_data_flow_manager.get_pending_content_drafts.return_value = []
        
        result = await review_service.get_pending_drafts("user_123")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_pending_drafts_sorting(self, review_service, mock_data_flow_manager):
        """Test draft sorting by priority and creation time"""
        # Create multiple mock drafts with different priorities
        draft1 = Mock()
        draft1.id = "draft_1"
        draft1.founder_id = "user_123"
        draft1.content_type = "trend_analysis"
        draft1.generated_text = "Content 1"
        draft1.current_content = "Content 1"
        draft1.status = "pending_review"
        draft1.priority = "low"
        draft1.created_at = datetime.utcnow() - timedelta(hours=1)
        draft1.updated_at = datetime.utcnow()
        draft1.tags = []
        draft1.analyzed_trend_id = None
        draft1.ai_generation_metadata = {}
        draft1.seo_suggestions = {}
        draft1.quality_score = None
        draft1.edit_history = []
        draft1.review_feedback = None
        draft1.reviewed_at = None
        draft1.reviewer_id = None
        draft1.review_decision = None
        draft1.scheduled_post_time = None
        draft1.posted_at = None
        draft1.posted_tweet_id = None
        
        draft2 = Mock()
        draft2.id = "draft_2"
        draft2.founder_id = "user_123"
        draft2.content_type = "trend_analysis"
        draft2.generated_text = "Content 2"
        draft2.current_content = "Content 2"
        draft2.status = "pending_review"
        draft2.priority = "high"
        draft2.created_at = datetime.utcnow()
        draft2.updated_at = datetime.utcnow()
        draft2.tags = []
        draft2.analyzed_trend_id = None
        draft2.ai_generation_metadata = {}
        draft2.seo_suggestions = {}
        draft2.quality_score = None
        draft2.edit_history = []
        draft2.review_feedback = None
        draft2.reviewed_at = None
        draft2.reviewer_id = None
        draft2.review_decision = None
        draft2.scheduled_post_time = None
        draft2.posted_at = None
        draft2.posted_tweet_id = None
        
        mock_data_flow_manager.get_pending_content_drafts.return_value = [draft1, draft2]
        
        result = await review_service.get_pending_drafts("user_123")
        
        # High priority should come first
        assert len(result) == 2
        assert result[0].priority == ContentPriority.HIGH
        assert result[1].priority == ContentPriority.LOW


class TestGetDraftDetails:
    """Test getting draft details"""
    
    @pytest.mark.asyncio
    async def test_get_draft_details_success(self, review_service, mock_data_flow_manager):
        """Test successful retrieval of draft details"""
        result = await review_service.get_draft_details("draft_123", "user_123")
        
        assert result is not None
        assert result.id == "draft_123"
        assert result.founder_id == "user_123"
        mock_data_flow_manager.get_content_draft_by_id.assert_called_once_with("draft_123")
    
    @pytest.mark.asyncio
    async def test_get_draft_details_not_found(self, review_service, mock_data_flow_manager):
        """Test handling of draft not found"""
        mock_data_flow_manager.get_content_draft_by_id.return_value = None
        
        result = await review_service.get_draft_details("nonexistent", "user_123")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_draft_details_access_denied(self, review_service, mock_data_flow_manager):
        """Test access denied for wrong user"""
        result = await review_service.get_draft_details("draft_123", "wrong_user")
        
        assert result is None


class TestSubmitReviewDecision:
    """Test submitting review decisions"""
    
    @pytest.mark.asyncio
    async def test_submit_approve_decision(self, review_service, mock_data_flow_manager):
        """Test approve decision"""
        decision_request = ReviewDecisionRequest(
            decision=ReviewDecision.APPROVE,
            feedback="Content is very good",
            tags=["AI", "startup"]
        )
        
        result = await review_service.submit_review_decision("draft_123", "user_123", decision_request)
        
        assert result is True
        mock_data_flow_manager.update_content_draft.assert_called_once()
        
        # Check the update data
        call_args = mock_data_flow_manager.update_content_draft.call_args
        update_data = call_args[0][1]
        assert update_data['review_decision'] == ReviewDecision.APPROVE.value
        assert update_data['status'] == DraftStatus.APPROVED.value
    
    @pytest.mark.asyncio
    async def test_submit_edit_and_approve_decision(self, review_service, mock_data_flow_manager):
        """Test edit and approve decision"""
        decision_request = ReviewDecisionRequest(
            decision=ReviewDecision.EDIT_AND_APPROVE,
            edited_content="This is the edited content",
            feedback="Modified the format"
        )
        
        result = await review_service.submit_review_decision("draft_123", "user_123", decision_request)
        
        assert result is True
        
        # Check the update data
        call_args = mock_data_flow_manager.update_content_draft.call_args
        update_data = call_args[0][1]
        assert update_data['current_content'] == "This is the edited content"
        assert update_data['status'] == DraftStatus.APPROVED.value
        assert 'edit_history' in update_data
    
    @pytest.mark.asyncio
    async def test_submit_reject_decision(self, review_service, mock_data_flow_manager):
        """Test reject decision"""
        decision_request = ReviewDecisionRequest(
            decision=ReviewDecision.REJECT,
            feedback="Content does not meet requirements"
        )
        
        result = await review_service.submit_review_decision("draft_123", "user_123", decision_request)
        
        assert result is True
        
        # Check the update data
        call_args = mock_data_flow_manager.update_content_draft.call_args
        update_data = call_args[0][1]
        assert update_data['status'] == DraftStatus.REJECTED.value
    
    @pytest.mark.asyncio
    async def test_submit_decision_draft_not_found(self, review_service, mock_data_flow_manager):
        """Test decision submission when draft not found"""
        mock_data_flow_manager.get_content_draft_by_id.return_value = None
        
        decision_request = ReviewDecisionRequest(decision=ReviewDecision.APPROVE)
        result = await review_service.submit_review_decision("nonexistent", "user_123", decision_request)
        
        assert result is False


class TestBatchReviewDecisions:
    """Test batch review decisions"""
    
    @pytest.mark.asyncio
    async def test_submit_batch_decisions_success(self, review_service, mock_data_flow_manager):
        """Test successful batch review decisions"""
        decisions = [
            BatchReviewDecision(
                draft_id="draft_1",
                decision=ReviewDecision.APPROVE,
                feedback="Very good"
            ),
            BatchReviewDecision(
                draft_id="draft_2",
                decision=ReviewDecision.REJECT,
                feedback="Needs improvement"
            )
        ]
        
        batch_request = BatchReviewRequest(decisions=decisions)
        
        # Mock multiple drafts
        mock_draft_1 = Mock()
        mock_draft_1.id = "draft_1"
        mock_draft_1.founder_id = "user_123"
        mock_draft_1.generated_text = "Content 1"
        mock_draft_1.edit_history = []
        
        mock_draft_2 = Mock()
        mock_draft_2.id = "draft_2"
        mock_draft_2.founder_id = "user_123"
        mock_draft_2.generated_text = "Content 2"
        mock_draft_2.edit_history = []
        
        def mock_get_draft(draft_id):
            if draft_id == "draft_1":
                return mock_draft_1
            elif draft_id == "draft_2":
                return mock_draft_2
            return None
        
        mock_data_flow_manager.get_content_draft_by_id.side_effect = mock_get_draft
        
        result = await review_service.submit_batch_review_decisions("user_123", batch_request)
        
        assert len(result) == 2
        assert result["draft_1"] is True
        assert result["draft_2"] is True
        assert mock_data_flow_manager.update_content_draft.call_count == 2
    
    @pytest.mark.asyncio
    async def test_batch_decisions_partial_failure(self, review_service, mock_data_flow_manager):
        """Test batch decisions with some failures"""
        decisions = [
            BatchReviewDecision(
                draft_id="draft_exists",
                decision=ReviewDecision.APPROVE
            ),
            BatchReviewDecision(
                draft_id="draft_not_exists",
                decision=ReviewDecision.APPROVE
            )
        ]
        
        batch_request = BatchReviewRequest(decisions=decisions)
        
        def mock_get_draft(draft_id):
            if draft_id == "draft_exists":
                mock_draft = Mock()
                mock_draft.id = "draft_exists"
                mock_draft.founder_id = "user_123"
                mock_draft.edit_history = []
                return mock_draft
            return None
        
        mock_data_flow_manager.get_content_draft_by_id.side_effect = mock_get_draft
        
        result = await review_service.submit_batch_review_decisions("user_123", batch_request)
        
        assert len(result) == 2
        assert result["draft_exists"] is True
        assert result["draft_not_exists"] is False


class TestContentRegeneration:
    """Test content regeneration"""
    
    @pytest.mark.asyncio
    async def test_regenerate_content_success(self, review_service, mock_data_flow_manager, mock_content_generation_service):
        """Test successful content regeneration"""
        regeneration_request = ContentRegenerationRequest(
            feedback="Needs more technical details",
            style_preferences={"tone": "technical"}
        )
        
        # Setup original draft mock
        original_draft = mock_data_flow_manager.get_content_draft_by_id.return_value
        original_draft.generation_metadata = {"regeneration_count": 0}
        original_draft.generated_text = "Original content"
        
        # Mock regenerated draft
        mock_new_draft = Mock()
        mock_new_draft.id = "new_draft_456"
        mock_new_draft.generated_text = "This is the regenerated content"
        mock_new_draft.ai_generation_metadata = {"version": "v2.0"}
        mock_new_draft.quality_score = 0.9
        
        def mock_get_draft_by_id(draft_id):
            if draft_id == "draft_123":
                return original_draft
            elif draft_id == "new_draft_456":
                return mock_new_draft
            return None
        
        mock_data_flow_manager.get_content_draft_by_id.side_effect = mock_get_draft_by_id
        
        # Mock the content generation service to return new draft IDs
        async def mock_regenerate_with_service(db_draft, context):
            return ["new_draft_456"]
        
        review_service._regenerate_with_content_service = mock_regenerate_with_service
        
        result = await review_service.regenerate_content("draft_123", "user_123", regeneration_request)
        
        assert result is not None
        assert isinstance(result, RegenerationResult)
        assert result.draft_id == "draft_123"
        assert result.new_content == "This is the regenerated content"
        assert result.quality_score == 0.9
    
    @pytest.mark.asyncio
    async def test_regenerate_content_limit_exceeded(self, review_service, mock_data_flow_manager):
        """Test regeneration when limit is exceeded"""
        # Mock draft with too many regenerations
        mock_draft = mock_data_flow_manager.get_content_draft_by_id.return_value
        mock_draft.ai_generation_metadata = {"regeneration_count": 5}  # Exceeds limit
        
        regeneration_request = ContentRegenerationRequest(feedback="Needs improvement")
        
        result = await review_service.regenerate_content("draft_123", "user_123", regeneration_request)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_regenerate_content_without_service(self, mock_data_flow_manager, mock_analytics_collector):
        """Test regeneration without content generation service"""
        service = ReviewOptimizationService(
            data_flow_manager=mock_data_flow_manager,
            content_generation_service=None,  # No service
            analytics_collector=mock_analytics_collector
        )
        
        regeneration_request = ContentRegenerationRequest(feedback="Needs improvement")
        
        result = await service.regenerate_content("draft_123", "user_123", regeneration_request)
        
        assert result is None


class TestStatusUpdate:
    """Test status updates"""
    
    @pytest.mark.asyncio
    async def test_update_draft_status_success(self, review_service, mock_data_flow_manager):
        """Test successful status update"""
        status_request = StatusUpdateRequest(
            status=DraftStatus.APPROVED,
            reviewer_notes="Content quality is very high"
        )
        
        result = await review_service.update_draft_status("draft_123", "user_123", status_request)
        
        assert result is True
        mock_data_flow_manager.update_content_draft.assert_called_once()
        
        call_args = mock_data_flow_manager.update_content_draft.call_args
        update_data = call_args[0][1]
        assert update_data['status'] == DraftStatus.APPROVED.value
        assert update_data['reviewer_notes'] == "Content quality is very high"
    
    @pytest.mark.asyncio
    async def test_update_status_invalid_transition(self, review_service, mock_data_flow_manager):
        """Test invalid status transition"""
        # Mock draft that's already posted
        mock_draft = mock_data_flow_manager.get_content_draft_by_id.return_value
        mock_draft.status = "posted"
        
        status_request = StatusUpdateRequest(status=DraftStatus.PENDING_REVIEW)
        
        result = await review_service.update_draft_status("draft_123", "user_123", status_request)
        
        assert result is False
        mock_data_flow_manager.update_content_draft.assert_not_called()


class TestAnalytics:
    """Test analytics functionality"""
    
    @pytest.mark.asyncio
    async def test_get_review_summary(self, review_service, mock_data_flow_manager):
        """Test getting review summary"""
        result = await review_service.get_review_summary("user_123", days=30)
        
        assert result.total_pending == 5
        assert result.total_approved == 20
        assert result.total_rejected == 3
        assert result.total_edited == 8
        assert result.avg_quality_score == 0.82
        assert result.approval_rate > 0
        
        mock_data_flow_manager.get_review_summary_data.assert_called_once_with("user_123", 30)
    
    @pytest.mark.asyncio
    async def test_get_review_analytics(self, review_service, mock_data_flow_manager):
        """Test getting detailed review analytics"""
        result = await review_service.get_review_analytics("user_123", days=30)
        
        assert result.period_days == 30
        assert result.total_reviews == 50
        assert result.decision_breakdown["approve"] == 30
        assert result.average_review_time_minutes == 8.5
        
        mock_data_flow_manager.get_detailed_review_analytics.assert_called_once_with("user_123", 30)
    
    @pytest.mark.asyncio
    async def test_get_review_queue(self, review_service):
        """Test getting review queue"""
        result = await review_service.get_review_queue("user_123")
        
        assert result.founder_id == "user_123"
        assert len(result.pending_drafts) == 1
        assert result.estimated_review_time_minutes > 0


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_service_handles_database_errors(self, review_service, mock_data_flow_manager):
        """Test service gracefully handles database errors"""
        mock_data_flow_manager.get_pending_content_drafts.side_effect = Exception("Database error")
        
        result = await review_service.get_pending_drafts("user_123")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_service_handles_analytics_errors(self, review_service, mock_analytics_collector):
        """Test service continues when analytics fails"""
        mock_analytics_collector.record_event.side_effect = Exception("Analytics error")
        
        decision_request = ReviewDecisionRequest(decision=ReviewDecision.APPROVE)
        
        # Should not raise exception even if analytics fails
        result = await review_service.submit_review_decision("draft_123", "user_123", decision_request)
        
        assert result is True


class TestPrivateMethods:
    """Test private helper methods"""
    
    def test_is_valid_status_transition(self, review_service):
        """Test status transition validation"""
        # Valid transitions
        assert review_service._is_valid_status_transition("pending_review", DraftStatus.APPROVED) is True
        assert review_service._is_valid_status_transition("approved", DraftStatus.SCHEDULED) is True
        assert review_service._is_valid_status_transition("scheduled", DraftStatus.POSTED) is True
        
        # Invalid transitions
        assert review_service._is_valid_status_transition("posted", DraftStatus.PENDING_REVIEW) is False
        assert review_service._is_valid_status_transition("rejected", DraftStatus.POSTED) is False
    
    def test_identify_improvements(self, review_service):
        """Test improvement identification"""
        original = "This is the original content"
        new_content = "This is the improved content with more details and questions? This is much longer!"
        
        regeneration_request = ContentRegenerationRequest(
            target_improvements=["questions", "details"]
        )
        
        improvements = review_service._identify_improvements(original, new_content, regeneration_request)
        
        assert len(improvements) > 0
        # Should detect expanded content and added question
        expected_improvements = ["Expanded content with additional context", "Added engaging question"]
        assert any(exp in improvements for exp in expected_improvements)


if __name__ == "__main__":
    pytest.main([__file__]) 