"""Unit tests for review optimization module"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from typing import List, Optional
import uuid
import logging

from review_optimization.models import (
    ReviewItem, ReviewStatus, ReviewAction, ReviewFeedback,
    ContentEdit, ReviewStatistics, ReviewFilterRequest,
    ReviewBatchRequest
)
from review_optimization.repository import (
    ReviewOptimizationRepository, ReviewItemTable
)
from review_optimization.service import ReviewOptimizationService

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestReviewModels:
    """Test data models"""
    
    def test_review_item_creation(self):
        """Test ReviewItem model creation"""
        logger.info("Starting test_review_item_creation")
        
        item = ReviewItem(
            id="test-id",
            content_draft_id="draft-123",
            founder_id="founder-456",
            content_type="tweet",
            original_content="Original tweet content",
            current_content="Current tweet content",
            generation_reason="AI generated trending content"
        )
        
        logger.debug(f"Created ReviewItem with id: {item.id}")
        logger.debug(f"ReviewItem status: {item.status}")
        logger.debug(f"ReviewItem priority: {item.review_priority}")
        
        assert item.id == "test-id"
        assert item.content_type == "tweet"
        assert item.status == ReviewStatus.PENDING
        assert item.review_priority == 5
        assert isinstance(item.created_at, datetime)
        
        logger.info("test_review_item_creation completed successfully")
    
    def test_content_edit_model(self):
        """Test ContentEdit model"""
        logger.info("Starting test_content_edit_model")
        
        edit = ContentEdit(
            field="content",
            old_value="Old content",
            new_value="New content",
            edited_by="user-123"
        )
        
        logger.debug(f"Created ContentEdit for field: {edit.field}")
        logger.debug(f"Edit timestamp: {edit.edited_at}")
        
        assert edit.field == "content"
        assert edit.old_value == "Old content"
        assert edit.new_value == "New content"
        assert isinstance(edit.edited_at, datetime)
        
        logger.info("test_content_edit_model completed successfully")
    
    def test_review_feedback_model(self):
        """Test ReviewFeedback model"""
        logger.info("Starting test_review_feedback_model")
        
        feedback = ReviewFeedback(
            rating=4,
            comments="Content quality is very good",
            improvement_suggestions=["Add more hashtags", "Optimize SEO keywords"],
            seo_feedback={"keyword_density": "good", "readability": "excellent"}
        )
        
        logger.debug(f"Created ReviewFeedback with rating: {feedback.rating}")
        logger.debug(f"Number of improvement suggestions: {len(feedback.improvement_suggestions)}")
        
        assert feedback.rating == 4
        assert feedback.comments == "Content quality is very good"
        assert len(feedback.improvement_suggestions) == 2
        
        logger.info("test_review_feedback_model completed successfully")
    
    def test_tweet_content_length_validation(self):
        """Test tweet content length validation"""
        logger.info("Starting test_tweet_content_length_validation")
        
        long_content = "x" * 300  # Over 280 characters
        logger.debug(f"Testing with content length: {len(long_content)}")
        
        with pytest.raises(ValueError, match="Tweet content cannot exceed 280 characters"):
            logger.debug("Attempting to create ReviewItem with content over 280 characters")
            ReviewItem(
                id="test-id",
                content_draft_id="draft-123",
                founder_id="founder-456",
                content_type="tweet",
                original_content=long_content,
                current_content=long_content,
                generation_reason="Test"
            )
        
        logger.info("test_tweet_content_length_validation completed successfully - validation error caught as expected")
    
    def test_review_filter_request(self):
        """Test filter request model"""
        logger.info("Starting test_review_filter_request")
        
        filter_req = ReviewFilterRequest(
            status=ReviewStatus.PENDING,
            content_type="tweet",
            priority_min=3,
            priority_max=8,
            limit=100,
            offset=20
        )
        
        logger.debug(f"Created filter request with status: {filter_req.status}")
        logger.debug(f"Filter limit: {filter_req.limit}, offset: {filter_req.offset}")
        
        assert filter_req.status == ReviewStatus.PENDING
        assert filter_req.limit == 100
        assert filter_req.offset == 20
        
        logger.info("test_review_filter_request completed successfully")
    
    def test_batch_request_model(self):
        """Test batch operation request model"""
        logger.info("Starting test_batch_request_model")
        
        batch_req = ReviewBatchRequest(
            item_ids=["id1", "id2", "id3"],
            action=ReviewAction.APPROVE,
            feedback=ReviewFeedback(rating=5, comments="Batch approval")
        )
        
        logger.debug(f"Created batch request with {len(batch_req.item_ids)} items")
        logger.debug(f"Batch action: {batch_req.action}")
        
        assert len(batch_req.item_ids) == 3
        assert batch_req.action == ReviewAction.APPROVE
        assert batch_req.feedback.rating == 5
        
        logger.info("test_batch_request_model completed successfully")


class TestReviewOptimizationRepository:
    """Test repository layer"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        logger.debug("Creating mock database session")
        return Mock()
    
    @pytest.fixture
    def repository(self, mock_db_session):
        """Create repository instance"""
        logger.debug("Creating ReviewOptimizationRepository instance")
        return ReviewOptimizationRepository(mock_db_session)
    
    @pytest.fixture
    def sample_review_item(self):
        """Sample review item"""
        logger.debug("Creating sample review item")
        return ReviewItem(
            id="test-123",
            content_draft_id="draft-456",
            founder_id="founder-789",
            content_type="tweet",
            original_content="Original content",
            current_content="Current content",
            generation_reason="AI generated"
        )
    
    def test_create_review_item_success(self, repository, mock_db_session, sample_review_item):
        """Test successful review item creation"""
        logger.info("Starting test_create_review_item_success")
        
        mock_db_session.commit = Mock()
        mock_db_session.add = Mock()
        mock_db_session.rollback = Mock()
        
        logger.debug("Mocked database session methods")
        logger.debug(f"Attempting to create review item: {sample_review_item.id}")
        
        result = repository.create_review_item(sample_review_item)
        
        logger.debug(f"Repository create_review_item returned: {result}")
        
        assert result is True
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        
        logger.info("test_create_review_item_success completed successfully")
    
    def test_create_review_item_failure(self, repository, mock_db_session, sample_review_item):
        """Test review item creation failure"""
        logger.info("Starting test_create_review_item_failure")
        
        from sqlalchemy.exc import IntegrityError
        mock_db_session.add = Mock(side_effect=IntegrityError("", "", ""))
        mock_db_session.rollback = Mock()
        
        logger.debug("Configured mock to raise IntegrityError")
        
        result = repository.create_review_item(sample_review_item)
        
        logger.debug(f"Repository create_review_item returned: {result}")
        
        assert result is False
        mock_db_session.rollback.assert_called_once()
        
        logger.info("test_create_review_item_failure completed successfully - error handled as expected")
    
    def test_get_review_item_found(self, repository, mock_db_session):
        """Test getting existing review item"""
        logger.info("Starting test_get_review_item_found")
        
        # Mock database return
        mock_db_item = Mock(spec=ReviewItemTable)
        mock_db_item.id = "test-123"
        mock_db_item.content_draft_id = "draft-456"
        mock_db_item.founder_id = "founder-789"
        mock_db_item.content_type = "tweet"
        mock_db_item.original_content = "Original content"
        mock_db_item.current_content = "Current content"
        mock_db_item.trend_context = {}
        mock_db_item.generation_reason = "AI generated"
        mock_db_item.ai_confidence_score = 0.8
        mock_db_item.seo_suggestions = {}
        mock_db_item.hashtags = []
        mock_db_item.keywords = []
        mock_db_item.status = ReviewStatus.PENDING
        mock_db_item.review_priority = 5
        mock_db_item.created_at = datetime.utcnow()
        mock_db_item.updated_at = datetime.utcnow()
        mock_db_item.reviewed_at = None
        mock_db_item.reviewed_by = None
        mock_db_item.edit_history = []
        mock_db_item.scheduled_time = None
        mock_db_item.feedback = None
        
        logger.debug(f"Created mock database item with id: {mock_db_item.id}")
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_db_item
        mock_db_session.query.return_value = mock_query
        
        logger.debug("Configured mock database query to return item")
        
        result = repository.get_review_item("test-123")
        
        logger.debug(f"Repository returned item: {result.id if result else None}")
        
        assert result is not None
        assert result.id == "test-123"
        assert result.content_type == "tweet"
        assert result.status == ReviewStatus.PENDING
        
        logger.info("test_get_review_item_found completed successfully")
    
    def test_get_review_item_not_found(self, repository, mock_db_session):
        """Test getting non-existent review item"""
        logger.info("Starting test_get_review_item_not_found")
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        logger.debug("Configured mock database query to return None")
        
        result = repository.get_review_item("nonexistent")
        
        logger.debug(f"Repository returned: {result}")
        
        assert result is None
        
        logger.info("test_get_review_item_not_found completed successfully")
    
    def test_get_review_items_with_filter(self, repository, mock_db_session):
        """Test getting filtered review items list"""
        logger.info("Starting test_get_review_items_with_filter")
        
        # Mock query results
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = []
        mock_db_session.query.return_value = mock_query
        
        logger.debug("Configured mock database query chain")
        
        filter_request = ReviewFilterRequest(
            status=ReviewStatus.PENDING,
            content_type="tweet",
            limit=10
        )
        
        logger.debug(f"Using filter request: status={filter_request.status}, limit={filter_request.limit}")
        
        result = repository.get_review_items("founder-123", filter_request)
        
        logger.debug(f"Repository returned {len(result)} items")
        
        assert isinstance(result, list)
        mock_db_session.query.assert_called_once()
        
        logger.info("test_get_review_items_with_filter completed successfully")
    
    def test_update_review_item_success(self, repository, mock_db_session):
        """Test successful review item update"""
        logger.info("Starting test_update_review_item_success")
        
        mock_db_item = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_db_item
        mock_db_session.query.return_value = mock_query
        mock_db_session.commit = Mock()
        
        logger.debug("Configured mock database item and query")
        
        updates = {"status": ReviewStatus.APPROVED, "reviewed_by": "user-123"}
        logger.debug(f"Updating item with: {updates}")
        
        result = repository.update_review_item("test-123", updates)
        
        logger.debug(f"Update result: {result}")
        
        assert result is True
        mock_db_session.commit.assert_called_once()
        assert hasattr(mock_db_item, 'updated_at')
        
        logger.info("test_update_review_item_success completed successfully")
    
    def test_add_edit_history_success(self, repository, mock_db_session):
        """Test successful addition of edit history"""
        logger.info("Starting test_add_edit_history_success")
        
        mock_db_item = Mock()
        mock_db_item.edit_history = []
        mock_db_item.current_content = "Old content"
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_db_item
        mock_db_session.query.return_value = mock_query
        mock_db_session.commit = Mock()
        
        logger.debug("Configured mock database item with empty edit history")
        
        edit = ContentEdit(
            field="content",
            old_value="Old content",
            new_value="New content",
            edited_by="user-123"
        )
        
        logger.debug(f"Adding edit: {edit.field} from '{edit.old_value}' to '{edit.new_value}'")
        
        result = repository.add_edit_history("test-123", edit)
        
        logger.debug(f"Add edit history result: {result}")
        logger.debug(f"Edit history length after addition: {len(mock_db_item.edit_history)}")
        
        assert result is True
        assert len(mock_db_item.edit_history) == 1
        mock_db_session.commit.assert_called_once()
        
        logger.info("test_add_edit_history_success completed successfully")
    
    def test_get_review_statistics(self, repository, mock_db_session):
        """Test getting review statistics"""
        logger.info("Starting test_get_review_statistics")
        
        # Mock database query results
        mock_items = []
        for i in range(10):
            mock_item = Mock()
            mock_item.status = ReviewStatus.APPROVED if i < 7 else ReviewStatus.PENDING
            mock_item.ai_confidence_score = 0.8
            mock_item.created_at = datetime.utcnow() - timedelta(days=1)
            mock_item.reviewed_at = datetime.utcnow() if i < 7 else None
            mock_item.edit_history = [{"field": "content"}] if i < 3 else []
            mock_item.feedback = {"rating": 4} if i < 5 else None
            mock_items.append(mock_item)
        
        logger.debug(f"Created {len(mock_items)} mock items for statistics")
        logger.debug(f"Approved items: {sum(1 for item in mock_items if item.status == ReviewStatus.APPROVED)}")
        logger.debug(f"Pending items: {sum(1 for item in mock_items if item.status == ReviewStatus.PENDING)}")
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = mock_items
        mock_db_session.query.return_value = mock_query
        
        stats = repository.get_review_statistics("founder-123", 30)
        
        logger.debug(f"Statistics: total={stats.total_items}, approved={stats.approved_items}, pending={stats.pending_items}")
        
        assert isinstance(stats, ReviewStatistics)
        assert stats.total_items == 10
        assert stats.approved_items == 7
        assert stats.pending_items == 3
        assert stats.time_period_days == 30
        
        logger.info("test_get_review_statistics completed successfully")


class TestReviewOptimizationService:
    """Test service layer"""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock repository"""
        logger.debug("Creating mock repository")
        return Mock(spec=ReviewOptimizationRepository)
    
    @pytest.fixture
    def mock_content_service(self):
        """Mock content generation service"""
        logger.debug("Creating mock content service")
        return Mock()
    
    @pytest.fixture
    def mock_scheduling_service(self):
        """Mock scheduling service"""
        logger.debug("Creating mock scheduling service")
        return Mock()
    
    @pytest.fixture
    def service(self, mock_repository, mock_content_service, mock_scheduling_service):
        """Create service instance"""
        logger.debug("Creating ReviewOptimizationService instance")
        return ReviewOptimizationService(
            repository=mock_repository,
            content_service=mock_content_service,
            scheduling_service=mock_scheduling_service
        )
    
    @pytest.fixture
    def sample_draft(self):
        """Sample draft"""
        logger.debug("Creating sample draft")
        draft = Mock()
        draft.founder_id = "founder-123"
        draft.content_type = "tweet"
        draft.generated_text = "AI generated tweet content"
        draft.trend_context = {"trend_score": 0.8}
        draft.generation_metadata = {"reason": "trending_topic"}
        draft.quality_score = 0.8
        draft.seo_suggestions = {
            "hashtags": ["#AI", "#Technology"],
            "keywords": ["artificial intelligence", "technology"]
        }
        return draft
    
    def test_create_review_item_from_draft_success(self, service, mock_repository, 
                                                 mock_content_service, sample_draft):
        """Test successful creation of review item from draft"""
        logger.info("Starting test_create_review_item_from_draft_success")
        
        mock_content_service.get_draft.return_value = sample_draft
        mock_repository.create_review_item.return_value = True
        
        logger.debug(f"Mock content service will return draft for founder: {sample_draft.founder_id}")
        logger.debug("Mock repository will return True for create_review_item")
        
        with patch('uuid.uuid4', return_value=Mock(hex='test-uuid')):
            logger.debug("Patched uuid.uuid4 to return 'test-uuid'")
            result = service.create_review_item_from_draft("draft-123", "founder-123")
        
        logger.debug(f"Service returned review item ID: {result}")
        
        assert result == 'test-uuid'
        mock_content_service.get_draft.assert_called_once_with("draft-123")
        mock_repository.create_review_item.assert_called_once()
        
        logger.info("test_create_review_item_from_draft_success completed successfully")
    
    def test_create_review_item_from_draft_access_denied(self, service, mock_content_service):
        """Test access denied when creating review item"""
        logger.info("Starting test_create_review_item_from_draft_access_denied")
        
        draft = Mock()
        draft.founder_id = "other-founder"
        mock_content_service.get_draft.return_value = draft
        
        logger.debug(f"Mock draft has founder_id: {draft.founder_id}")
        logger.debug("Requesting founder_id: founder-123 (different - should be denied)")
        
        result = service.create_review_item_from_draft("draft-123", "founder-123")
        
        logger.debug(f"Service returned: {result} (should be None for access denied)")
        
        assert result is None
        
        logger.info("test_create_review_item_from_draft_access_denied completed successfully - access denied as expected")
    
    def test_create_review_item_from_draft_not_found(self, service, mock_content_service):
        """Test creating review item when draft doesn't exist"""
        logger.info("Starting test_create_review_item_from_draft_not_found")
        
        mock_content_service.get_draft.return_value = None
        
        logger.debug("Mock content service will return None (draft not found)")
        
        result = service.create_review_item_from_draft("draft-123", "founder-123")
        
        logger.debug(f"Service returned: {result} (should be None for not found)")
        
        assert result is None
        
        logger.info("test_create_review_item_from_draft_not_found completed successfully - not found handled correctly")
    
    def test_get_review_queue(self, service, mock_repository):
        """Test getting review queue"""
        logger.info("Starting test_get_review_queue")
        
        mock_items = [Mock(), Mock(), Mock()]
        mock_repository.get_review_items.return_value = mock_items
        
        logger.debug(f"Mock repository will return {len(mock_items)} items")
        
        filter_request = ReviewFilterRequest(status=ReviewStatus.PENDING)
        logger.debug(f"Using filter request with status: {filter_request.status}")
        
        result = service.get_review_queue("founder-123", filter_request)
        
        logger.debug(f"Service returned {len(result)} items")
        
        assert len(result) == 3
        mock_repository.get_review_items.assert_called_once_with("founder-123", filter_request)
        
        logger.info("test_get_review_queue completed successfully")
    
    def test_get_review_item_success(self, service, mock_repository):
        """Test successful review item retrieval"""
        logger.info("Starting test_get_review_item_success")
        
        mock_item = Mock()
        mock_item.founder_id = "founder-123"
        mock_repository.get_review_item.return_value = mock_item
        
        logger.debug(f"Mock item has founder_id: {mock_item.founder_id}")
        
        result = service.get_review_item("item-123", "founder-123")
        
        logger.debug(f"Service returned item: {result}")
        
        assert result == mock_item
        mock_repository.get_review_item.assert_called_once_with("item-123")
        
        logger.info("test_get_review_item_success completed successfully")
    
    def test_get_review_item_access_denied(self, service, mock_repository):
        """Test access denied when getting review item"""
        logger.info("Starting test_get_review_item_access_denied")
        
        mock_item = Mock()
        mock_item.founder_id = "other-founder"
        mock_repository.get_review_item.return_value = mock_item
        
        logger.debug(f"Mock item has founder_id: {mock_item.founder_id}")
        logger.debug("Requesting founder_id: founder-123 (different - should be denied)")
        
        result = service.get_review_item("item-123", "founder-123")
        
        logger.debug(f"Service returned: {result} (should be None for access denied)")
        
        assert result is None
        
        logger.info("test_get_review_item_access_denied completed successfully - access denied as expected")
    
    def test_update_content_success(self, service, mock_repository):
        """Test successful content update"""
        logger.info("Starting test_update_content_success")
        
        mock_item = Mock()
        mock_item.founder_id = "founder-123"
        mock_item.current_content = "Old content"
        mock_repository.get_review_item.return_value = mock_item
        mock_repository.add_edit_history.return_value = True
        mock_repository.update_review_item.return_value = True
        
        logger.debug(f"Mock item current content: {mock_item.current_content}")
        logger.debug("New content: 'New content'")
        
        result = service.update_content("item-123", "founder-123", "New content", "editor-123")
        
        logger.debug(f"Update content result: {result}")
        
        assert result is True
        mock_repository.add_edit_history.assert_called_once()
        mock_repository.update_review_item.assert_called_once()
        
        logger.info("test_update_content_success completed successfully")
    
    def test_update_seo_elements_success(self, service, mock_repository):
        """Test successful SEO elements update"""
        logger.info("Starting test_update_seo_elements_success")
        
        mock_item = Mock()
        mock_item.founder_id = "founder-123"
        mock_item.hashtags = ["#old_hashtag"]
        mock_item.keywords = ["old_keyword"]
        mock_repository.get_review_item.return_value = mock_item
        mock_repository.add_edit_history.return_value = True
        mock_repository.update_review_item.return_value = True
        
        logger.debug(f"Current hashtags: {mock_item.hashtags}")
        logger.debug(f"Current keywords: {mock_item.keywords}")
        
        new_hashtags = ["#new_hashtag1", "#new_hashtag2"]
        new_keywords = ["new_keyword1", "new_keyword2"]
        
        logger.debug(f"New hashtags: {new_hashtags}")
        logger.debug(f"New keywords: {new_keywords}")
        
        result = service.update_seo_elements(
            "item-123", "founder-123", new_hashtags, new_keywords, "editor-123"
        )
        
        logger.debug(f"Update SEO elements result: {result}")
        
        assert result is True
        assert mock_repository.add_edit_history.call_count == 2  # Once for hashtags and once for keywords
        mock_repository.update_review_item.assert_called_once()
        
        logger.info("test_update_seo_elements_success completed successfully")
    
    def test_perform_action_approve_success(self, service, mock_repository, mock_scheduling_service):
        """Test successful approval action execution"""
        logger.info("Starting test_perform_action_approve_success")
        
        mock_item = Mock()
        mock_item.founder_id = "founder-123"
        mock_item.content_draft_id = "draft-123"
        mock_item.current_content = "Content"
        mock_item.content_type = "tweet"
        mock_item.hashtags = ["#hashtag"]
        mock_repository.get_review_item.return_value = mock_item
        mock_repository.update_review_item.return_value = True
        mock_scheduling_service.add_to_queue.return_value = True
        
        logger.debug(f"Mock item: {mock_item.content_draft_id}, type: {mock_item.content_type}")
        logger.debug("Performing APPROVE action")
        
        feedback = ReviewFeedback(rating=5, comments="Great content")
        success, message = service.perform_action(
            "item-123", "founder-123", ReviewAction.APPROVE, feedback, None, "reviewer-123"
        )
        
        logger.debug(f"Action result: success={success}, message='{message}'")
        
        assert success is True
        assert "successfully" in message
        mock_scheduling_service.add_to_queue.assert_called_once()
        mock_repository.update_review_item.assert_called_once()
        
        logger.info("test_perform_action_approve_success completed successfully")
    
    def test_perform_action_reject(self, service, mock_repository):
        """Test rejection action execution"""
        logger.info("Starting test_perform_action_reject")
        
        mock_item = Mock()
        mock_item.founder_id = "founder-123"
        mock_repository.get_review_item.return_value = mock_item
        mock_repository.update_review_item.return_value = True
        
        logger.debug("Performing REJECT action")
        
        feedback = ReviewFeedback(rating=2, comments="Content quality does not meet requirements")
        success, message = service.perform_action(
            "item-123", "founder-123", ReviewAction.REJECT, feedback, None, "reviewer-123"
        )
        
        logger.debug(f"Reject action result: success={success}, message='{message}'")
        
        assert success is True
        mock_repository.update_review_item.assert_called_once()
        
        logger.info("test_perform_action_reject completed successfully")
    
    def test_perform_action_schedule(self, service, mock_repository, mock_scheduling_service):
        """Test schedule action execution"""
        logger.info("Starting test_perform_action_schedule")
        
        mock_item = Mock()
        mock_item.founder_id = "founder-123"
        mock_item.content_draft_id = "draft-123"
        mock_item.current_content = "Content"
        mock_item.content_type = "tweet"
        mock_item.hashtags = ["#hashtag"]
        mock_repository.get_review_item.return_value = mock_item
        mock_repository.update_review_item.return_value = True
        mock_scheduling_service.add_to_queue.return_value = True
        
        scheduled_time = datetime.utcnow() + timedelta(hours=2)
        logger.debug(f"Scheduling for: {scheduled_time}")
        
        success, message = service.perform_action(
            "item-123", "founder-123", ReviewAction.SCHEDULE, None, scheduled_time, "reviewer-123"
        )
        
        logger.debug(f"Schedule action result: success={success}, message='{message}'")
        
        assert success is True
        mock_scheduling_service.add_to_queue.assert_called_once()
        mock_repository.update_review_item.assert_called_once()
        
        logger.info("test_perform_action_schedule completed successfully")
    
    def test_perform_action_request_revision(self, service, mock_repository, mock_content_service):
        """Test request revision action execution"""
        logger.info("Starting test_perform_action_request_revision")
        
        mock_item = Mock()
        mock_item.founder_id = "founder-123"
        mock_item.content_draft_id = "draft-123"
        mock_repository.get_review_item.return_value = mock_item
        mock_repository.update_review_item.return_value = True
        mock_content_service.request_revision.return_value = "new-draft-456"
        
        # Mock create_review_item_from_draft method
        service.create_review_item_from_draft = Mock(return_value="new-review-item")
        
        logger.debug("Performing REQUEST_REVISION action")
        logger.debug("Mock content service will return new-draft-456")
        
        feedback = ReviewFeedback(
            rating=3,
            comments="Needs improvement",
            improvement_suggestions=["Add more details", "Improve tone"]
        )
        
        success, message = service.perform_action(
            "item-123", "founder-123", ReviewAction.REQUEST_REVISION, feedback, None, "reviewer-123"
        )
        
        logger.debug(f"Request revision result: success={success}, message='{message}'")
        
        assert success is True
        mock_content_service.request_revision.assert_called_once()
        service.create_review_item_from_draft.assert_called_once_with("new-draft-456", "founder-123")
        
        logger.info("test_perform_action_request_revision completed successfully")
    
    def test_batch_review_success(self, service):
        """Test successful batch review execution"""
        logger.info("Starting test_batch_review_success")
        
        # Mock perform_action method
        service.perform_action = Mock(return_value=(True, "Success"))
        
        batch_request = ReviewBatchRequest(
            item_ids=["item1", "item2", "item3"],
            action=ReviewAction.APPROVE,
            feedback=ReviewFeedback(rating=5, comments="Batch approval")
        )
        
        logger.debug(f"Batch processing {len(batch_request.item_ids)} items")
        logger.debug(f"Batch action: {batch_request.action}")
        
        results = service.batch_review(batch_request, "founder-123", "reviewer-123")
        
        logger.debug(f"Batch results: total={results['total']}, successful={len(results['successful'])}, failed={len(results['failed'])}")
        
        assert results['total'] == 3
        assert len(results['successful']) == 3
        assert len(results['failed']) == 0
        assert service.perform_action.call_count == 3
        
        logger.info("test_batch_review_success completed successfully")
    
    def test_batch_review_mixed_results(self, service):
        """Test batch review with mixed results"""
        logger.info("Starting test_batch_review_mixed_results")
        
        # Mock perform_action method to return different results
        def mock_perform_action(*args, **kwargs):
            item_id = args[0]
            logger.debug(f"Processing batch item: {item_id}")
            if item_id == "item2":
                logger.debug(f"Simulating failure for {item_id}")
                return False, "Operation failed"
            logger.debug(f"Simulating success for {item_id}")
            return True, "Success"
        
        service.perform_action = Mock(side_effect=mock_perform_action)
        
        batch_request = ReviewBatchRequest(
            item_ids=["item1", "item2", "item3"],
            action=ReviewAction.APPROVE
        )
        
        results = service.batch_review(batch_request, "founder-123", "reviewer-123")
        
        logger.debug(f"Mixed results: total={results['total']}, successful={len(results['successful'])}, failed={len(results['failed'])}")
        logger.debug(f"Failed items: {[item['item_id'] for item in results['failed']]}")
        
        assert results['total'] == 3
        assert len(results['successful']) == 2
        assert len(results['failed']) == 1
        assert results['failed'][0]['item_id'] == "item2"
        
        logger.info("test_batch_review_mixed_results completed successfully")
    
    def test_get_review_statistics(self, service, mock_repository):
        """Test getting review statistics"""
        logger.info("Starting test_get_review_statistics")
        
        mock_stats = ReviewStatistics(
            total_items=100,
            pending_items=20,
            approved_items=70,
            rejected_items=10,
            approval_rate=0.7,
            time_period_days=30
        )
        mock_repository.get_review_statistics.return_value = mock_stats
        
        logger.debug(f"Mock repository will return stats: total={mock_stats.total_items}, approval_rate={mock_stats.approval_rate}")
        
        result = service.get_review_statistics("founder-123", 30)
        
        logger.debug(f"Service returned stats: total={result.total_items}, approval_rate={result.approval_rate}")
        
        assert result == mock_stats
        mock_repository.get_review_statistics.assert_called_once_with("founder-123", 30)
        
        logger.info("test_get_review_statistics completed successfully")
    
    def test_calculate_review_priority_high_confidence(self, service):
        """Test calculating review priority with high confidence"""
        logger.info("Starting test_calculate_review_priority_high_confidence")
        
        draft = Mock()
        draft.quality_score = 0.9
        draft.trend_context = {"trend_score": 0.8}
        draft.content_type = "reply"
        
        logger.debug(f"Draft quality_score: {draft.quality_score}")
        logger.debug(f"Draft trend_score: {draft.trend_context.get('trend_score')}")
        logger.debug(f"Draft content_type: {draft.content_type}")
        
        priority = service._calculate_review_priority(draft)
        
        logger.debug(f"Calculated priority: {priority}")
        logger.debug("Expected: Base 5 + high confidence 2 + high trend 2 + reply 1 = 10")
        
        # Base 5 + high confidence 2 + high trend 2 + reply 1 = 10
        assert priority == 10
        
        logger.info("test_calculate_review_priority_high_confidence completed successfully")
    
    def test_calculate_review_priority_low_confidence(self, service):
        """Test calculating review priority with low confidence"""
        logger.info("Starting test_calculate_review_priority_low_confidence")
        
        draft = Mock()
        draft.quality_score = 0.3
        draft.trend_context = {}
        draft.content_type = "thread"
        
        logger.debug(f"Draft quality_score: {draft.quality_score}")
        logger.debug(f"Draft trend_context: {draft.trend_context}")
        logger.debug(f"Draft content_type: {draft.content_type}")
        
        priority = service._calculate_review_priority(draft)
        
        logger.debug(f"Calculated priority: {priority}")
        logger.debug("Expected: Base 5 - low confidence 1 - thread 1 = 3")
        
        # Base 5 - low confidence 1 - thread 1 = 3
        assert priority == 3
        
        logger.info("test_calculate_review_priority_low_confidence completed successfully")
    
    def test_calculate_review_priority_bounds(self, service):
        """Test priority calculation boundary values"""
        logger.info("Starting test_calculate_review_priority_bounds")
        
        # Test minimum priority
        logger.debug("Testing minimum priority boundary")
        draft = Mock()
        draft.quality_score = 0.1
        draft.trend_context = {}
        draft.content_type = "thread"
        
        priority = service._calculate_review_priority(draft)
        logger.debug(f"Low priority result: {priority} (should be >= 1)")
        assert priority >= 1  # Minimum is 1
        
        # Test maximum priority doesn't exceed 10
        logger.debug("Testing maximum priority boundary")
        draft.quality_score = 1.0
        draft.trend_context = {"trend_score": 1.0, "is_emerging": True}
        draft.content_type = "reply"
        
        priority = service._calculate_review_priority(draft)
        logger.debug(f"High priority result: {priority} (should be <= 10)")
        assert priority <= 10  # Maximum is 10
        
        logger.info("test_calculate_review_priority_bounds completed successfully")


# Integration test examples
class TestReviewOptimizationIntegration:
    """Integration tests"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all dependencies"""
        logger.debug("Creating mock dependencies for integration test")
        repository = Mock(spec=ReviewOptimizationRepository)
        content_service = Mock()
        scheduling_service = Mock()
        return repository, content_service, scheduling_service
    
    def test_full_review_workflow(self, mock_dependencies):
        """Test complete review workflow"""
        logger.info("Starting test_full_review_workflow - Integration Test")
        
        repository, content_service, scheduling_service = mock_dependencies
        service = ReviewOptimizationService(repository, content_service, scheduling_service)
        
        # 1. Create review item
        logger.debug("Step 1: Creating review item from draft")
        draft = Mock()
        draft.founder_id = "founder-123"
        draft.content_type = "tweet"
        draft.generated_text = "AI generated tweet"
        draft.trend_context = {"trend_score": 0.8}
        draft.generation_metadata = {"reason": "trending"}
        draft.quality_score = 0.8
        draft.seo_suggestions = {"hashtags": ["#AI"]}
        
        content_service.get_draft.return_value = draft
        repository.create_review_item.return_value = True
        
        logger.debug(f"Mock draft setup: type={draft.content_type}, quality={draft.quality_score}")
        
        with patch('uuid.uuid4', return_value=Mock(hex='review-123')):
            review_id = service.create_review_item_from_draft("draft-123", "founder-123")
        
        logger.debug(f"Created review item with ID: {review_id}")
        assert review_id == 'review-123'
        
        # 2. Get and edit content
        logger.debug("Step 2: Editing content")
        mock_item = Mock()
        mock_item.founder_id = "founder-123"
        mock_item.current_content = "AI generated tweet"
        repository.get_review_item.return_value = mock_item
        repository.add_edit_history.return_value = True
        repository.update_review_item.return_value = True
        
        edit_success = service.update_content(
            "review-123", "founder-123", "Edited tweet content", "editor-123"
        )
        logger.debug(f"Content edit success: {edit_success}")
        assert edit_success is True
        
        # 3. Approve content
        logger.debug("Step 3: Approving content")
        scheduling_service.add_to_queue.return_value = True
        
        feedback = ReviewFeedback(rating=5, comments="Excellent content")
        success, message = service.perform_action(
            "review-123", "founder-123", ReviewAction.APPROVE, feedback, None, "reviewer-123"
        )
        
        logger.debug(f"Approval result: success={success}, message='{message}'")
        
        assert success is True
        content_service.get_draft.assert_called_once()
        repository.create_review_item.assert_called_once()
        repository.add_edit_history.assert_called_once()
        scheduling_service.add_to_queue.assert_called_once()
        
        logger.info("test_full_review_workflow completed successfully - Full workflow tested")


if __name__ == "__main__":
    logger.info("Starting pytest execution for review optimization tests")
    pytest.main([__file__])
    logger.info("Pytest execution completed")
