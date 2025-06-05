"""
Comprehensive tests for the Review Optimization Module
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from modules.review_optimization.models import (
    ReviewItem, ReviewStatus, ReviewAction, ReviewFeedback,
    ContentEdit, ReviewStatistics, ReviewFilterRequest,
    ReviewBatchRequest
)
from modules.review_optimization.repository import (
    ReviewOptimizationRepository, ReviewItemTable
)
from modules.review_optimization.service import ReviewOptimizationService
from database import Base


# Test fixtures
@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


@pytest.fixture
def mock_content_service():
    """Mock content generation service"""
    service = Mock()
    # Mock draft data
    mock_draft = Mock()
    mock_draft.id = "draft_123"
    mock_draft.founder_id = "founder_123"
    mock_draft.content_type = "tweet"
    mock_draft.generated_text = "Test tweet content"
    mock_draft.quality_score = 0.8
    mock_draft.trend_context = {"trend_id": "trend_123", "relevance": 0.9}
    mock_draft.generation_metadata = {"reason": "trending_topic"}
    mock_draft.seo_suggestions = {
        "hashtags": ["#test", "#content"],
        "keywords": ["test", "content"]
    }
    
    service.get_draft.return_value = mock_draft
    service.request_revision.return_value = "new_draft_456"
    return service


@pytest.fixture
def mock_scheduling_service():
    """Mock scheduling service"""
    service = Mock()
    service.add_to_queue.return_value = True
    return service


@pytest.fixture
def repository(in_memory_db):
    """Create repository with in-memory database"""
    return ReviewOptimizationRepository(in_memory_db)


@pytest.fixture
def service(repository, mock_content_service, mock_scheduling_service):
    """Create service with mocked dependencies"""
    return ReviewOptimizationService(
        repository=repository,
        content_service=mock_content_service,
        scheduling_service=mock_scheduling_service
    )


@pytest.fixture
def sample_review_item():
    """Create sample review item"""
    return ReviewItem(
        id=str(uuid.uuid4()),
        content_draft_id="draft_123",
        founder_id="founder_123",
        content_type="tweet",
        original_content="Original test content",
        current_content="Original test content",
        trend_context={"trend_id": "trend_123"},
        generation_reason="trending_topic",
        ai_confidence_score=0.8,
        seo_suggestions={"hashtags": ["#test"]},
        hashtags=["#test"],
        keywords=["test"],
        review_priority=7
    )


# Model Tests
class TestReviewModels:
    """Test Pydantic models"""
    
    def test_review_item_creation(self):
        """Test ReviewItem model creation"""
        item = ReviewItem(
            id="test_id",
            content_draft_id="draft_123",
            founder_id="founder_123",
            content_type="tweet",
            original_content="Test content",
            current_content="Test content",
            generation_reason="test",
            ai_confidence_score=0.8
        )
        
        assert item.id == "test_id"
        assert item.status == ReviewStatus.PENDING
        assert item.review_priority == 5  # default
        assert len(item.edit_history) == 0
    
    def test_review_item_content_validation(self):
        """Test content length validation for tweets"""
        with pytest.raises(ValueError, match="Tweet content cannot exceed 280 characters"):
            ReviewItem(
                id="test_id",
                content_draft_id="draft_123",
                founder_id="founder_123",
                content_type="tweet",
                original_content="x" * 281,  # Too long
                current_content="x" * 281,
                generation_reason="test",
                ai_confidence_score=0.8
            )
    
    def test_review_feedback_model(self):
        """Test ReviewFeedback model"""
        feedback = ReviewFeedback(
            rating=4,
            comments="Good content",
            improvement_suggestions=["Add more hashtags"],
            seo_feedback={"score": 0.8}
        )
        
        assert feedback.rating == 4
        assert len(feedback.improvement_suggestions) == 1
    
    def test_content_edit_model(self):
        """Test ContentEdit model"""
        edit = ContentEdit(
            field="content",
            old_value="old text",
            new_value="new text",
            edited_by="user_123"
        )
        
        assert edit.field == "content"
        assert isinstance(edit.edited_at, datetime)
    
    def test_review_filter_request(self):
        """Test filter request validation"""
        filter_req = ReviewFilterRequest(
            status=ReviewStatus.PENDING,
            priority_min=1,
            priority_max=10,
            limit=100,
            offset=0
        )
        
        assert filter_req.status == ReviewStatus.PENDING
        assert filter_req.limit == 100
    
    def test_batch_request_model(self):
        """Test batch request model"""
        batch_req = ReviewBatchRequest(
            item_ids=["id1", "id2", "id3"],
            action=ReviewAction.APPROVE,
            feedback=ReviewFeedback(rating=5, comments="Batch approved")
        )
        
        assert len(batch_req.item_ids) == 3
        assert batch_req.action == ReviewAction.APPROVE


# Repository Tests
class TestReviewOptimizationRepository:
    """Test repository operations"""
    
    def test_create_review_item(self, repository, sample_review_item):
        """Test creating review item"""
        success = repository.create_review_item(sample_review_item)
        assert success is True
        
        # Verify item was created
        retrieved_item = repository.get_review_item(sample_review_item.id)
        assert retrieved_item is not None
        assert retrieved_item.id == sample_review_item.id
        assert retrieved_item.founder_id == sample_review_item.founder_id
    
    def test_get_review_item_not_found(self, repository):
        """Test getting non-existent review item"""
        item = repository.get_review_item("non_existent_id")
        assert item is None
    
    def test_get_review_items_with_filter(self, repository, sample_review_item):
        """Test getting review items with filters"""
        # Create test item
        repository.create_review_item(sample_review_item)
        
        # Test status filter
        filter_req = ReviewFilterRequest(
            status=ReviewStatus.PENDING,
            limit=10
        )
        items = repository.get_review_items(
            sample_review_item.founder_id, 
            filter_req
        )
        
        assert len(items) == 1
        assert items[0].status == ReviewStatus.PENDING
    
    def test_get_review_items_priority_filter(self, repository, sample_review_item):
        """Test priority filtering"""
        repository.create_review_item(sample_review_item)
        
        # Filter by priority range
        filter_req = ReviewFilterRequest(
            priority_min=5,
            priority_max=8,
            limit=10
        )
        items = repository.get_review_items(
            sample_review_item.founder_id,
            filter_req
        )
        
        assert len(items) == 1
        assert 5 <= items[0].review_priority <= 8
    
    def test_update_review_item(self, repository, sample_review_item):
        """Test updating review item"""
        repository.create_review_item(sample_review_item)
        
        # Update status
        updates = {
            "status": ReviewStatus.APPROVED,
            "reviewed_by": "reviewer_123"
        }
        
        success = repository.update_review_item(sample_review_item.id, updates)
        assert success is True
        
        # Verify update
        updated_item = repository.get_review_item(sample_review_item.id)
        assert updated_item.status == ReviewStatus.APPROVED
        assert updated_item.reviewed_by == "reviewer_123"
    
    def test_add_edit_history(self, repository, sample_review_item):
        """Test adding edit history"""
        repository.create_review_item(sample_review_item)
        
        edit = ContentEdit(
            field="content",
            old_value="old content",
            new_value="new content",
            edited_by="editor_123"
        )
        
        success = repository.add_edit_history(sample_review_item.id, edit)
        assert success is True
        
        # Verify edit was added
        updated_item = repository.get_review_item(sample_review_item.id)
        assert len(updated_item.edit_history) == 1
        assert updated_item.edit_history[0].field == "content"
        assert updated_item.edit_history[0].edited_by == "editor_123"
    
    def test_get_review_statistics(self, repository):
        """Test getting review statistics"""
        # Create some test items with different statuses
        founder_id = "founder_123"
        
        # Create approved item
        approved_item = ReviewItem(
            id=str(uuid.uuid4()),
            content_draft_id="draft_1",
            founder_id=founder_id,
            content_type="tweet",
            original_content="content 1",
            current_content="content 1",
            generation_reason="test",
            ai_confidence_score=0.8,
            status=ReviewStatus.APPROVED
        )
        
        # Create rejected item
        rejected_item = ReviewItem(
            id=str(uuid.uuid4()),
            content_draft_id="draft_2",
            founder_id=founder_id,
            content_type="tweet",
            original_content="content 2",
            current_content="content 2",
            generation_reason="test",
            ai_confidence_score=0.6,
            status=ReviewStatus.REJECTED
        )
        
        repository.create_review_item(approved_item)
        repository.create_review_item(rejected_item)
        
        # Get statistics
        stats = repository.get_review_statistics(founder_id, days=30)
        
        assert stats.total_items == 2
        assert stats.approved_items == 1
        assert stats.rejected_items == 1
        assert stats.approval_rate == 0.5


# Service Tests
class TestReviewOptimizationService:
    """Test service business logic"""
    
    def test_create_review_item_from_draft(self, service, mock_content_service):
        """Test creating review item from draft"""
        draft_id = "draft_123"
        founder_id = "founder_123"
        
        item_id = service.create_review_item_from_draft(draft_id, founder_id)
        
        assert item_id is not None
        mock_content_service.get_draft.assert_called_once_with(draft_id)
        
        # Verify item was created
        item = service.get_review_item(item_id, founder_id)
        assert item is not None
        assert item.content_draft_id == draft_id
        assert item.founder_id == founder_id
    
    def test_create_review_item_draft_not_found(self, service, mock_content_service):
        """Test creating review item when draft not found"""
        mock_content_service.get_draft.return_value = None
        
        item_id = service.create_review_item_from_draft("nonexistent", "founder_123")
        assert item_id is None
    
    def test_create_review_item_access_denied(self, service, mock_content_service):
        """Test creating review item with access denied"""
        # Mock draft with different founder
        mock_draft = Mock()
        mock_draft.founder_id = "different_founder"
        mock_content_service.get_draft.return_value = mock_draft
        
        item_id = service.create_review_item_from_draft("draft_123", "founder_123")
        assert item_id is None
    
    def test_get_review_queue(self, service, repository, sample_review_item):
        """Test getting review queue"""
        repository.create_review_item(sample_review_item)
        
        items = service.get_review_queue(sample_review_item.founder_id)
        assert len(items) == 1
        assert items[0].id == sample_review_item.id
    
    def test_update_content(self, service, repository, sample_review_item):
        """Test updating content"""
        repository.create_review_item(sample_review_item)
        
        new_content = "Updated content"
        success = service.update_content(
            sample_review_item.id,
            sample_review_item.founder_id,
            new_content,
            "editor_123"
        )
        
        assert success is True
        
        # Verify content was updated
        updated_item = service.get_review_item(
            sample_review_item.id,
            sample_review_item.founder_id
        )
        assert updated_item.current_content == new_content
        assert updated_item.status == ReviewStatus.EDITED
        assert len(updated_item.edit_history) == 1
    
    def test_update_seo_elements(self, service, repository, sample_review_item):
        """Test updating SEO elements"""
        repository.create_review_item(sample_review_item)
        
        new_hashtags = ["#new", "#hashtags"]
        new_keywords = ["new", "keywords"]
        
        success = service.update_seo_elements(
            sample_review_item.id,
            sample_review_item.founder_id,
            hashtags=new_hashtags,
            keywords=new_keywords,
            editor_id="editor_123"
        )
        
        assert success is True
        
        # Verify SEO elements were updated
        updated_item = service.get_review_item(
            sample_review_item.id,
            sample_review_item.founder_id
        )
        assert updated_item.hashtags == new_hashtags
        assert updated_item.keywords == new_keywords
        assert updated_item.status == ReviewStatus.EDITED
        assert len(updated_item.edit_history) == 2  # One for hashtags, one for keywords
    
    def test_perform_action_approve(self, service, repository, sample_review_item, mock_scheduling_service):
        """Test approve action"""
        repository.create_review_item(sample_review_item)
        
        feedback = ReviewFeedback(rating=5, comments="Excellent content")
        
        success, message = service.perform_action(
            sample_review_item.id,
            sample_review_item.founder_id,
            ReviewAction.APPROVE,
            feedback=feedback,
            reviewer_id="reviewer_123"
        )
        
        assert success is True
        assert "completed successfully" in message
        mock_scheduling_service.add_to_queue.assert_called_once()
        
        # Verify status was updated
        updated_item = service.get_review_item(
            sample_review_item.id,
            sample_review_item.founder_id
        )
        assert updated_item.status == ReviewStatus.APPROVED
        assert updated_item.reviewed_by == "reviewer_123"
        assert updated_item.feedback.rating == 5
    
    def test_perform_action_reject(self, service, repository, sample_review_item):
        """Test reject action"""
        repository.create_review_item(sample_review_item)
        
        feedback = ReviewFeedback(rating=2, comments="Poor quality")
        
        success, message = service.perform_action(
            sample_review_item.id,
            sample_review_item.founder_id,
            ReviewAction.REJECT,
            feedback=feedback,
            reviewer_id="reviewer_123"
        )
        
        assert success is True
        
        # Verify status was updated
        updated_item = service.get_review_item(
            sample_review_item.id,
            sample_review_item.founder_id
        )
        assert updated_item.status == ReviewStatus.REJECTED
        assert updated_item.feedback.rating == 2
    
    def test_perform_action_schedule(self, service, repository, sample_review_item, mock_scheduling_service):
        """Test schedule action"""
        repository.create_review_item(sample_review_item)
        
        scheduled_time = datetime.utcnow() + timedelta(hours=2)
        
        success, message = service.perform_action(
            sample_review_item.id,
            sample_review_item.founder_id,
            ReviewAction.SCHEDULE,
            scheduled_time=scheduled_time,
            reviewer_id="reviewer_123"
        )
        
        assert success is True
        mock_scheduling_service.add_to_queue.assert_called_once()
        
        # Verify scheduling
        updated_item = service.get_review_item(
            sample_review_item.id,
            sample_review_item.founder_id
        )
        assert updated_item.status == ReviewStatus.SCHEDULED
        assert updated_item.scheduled_time == scheduled_time
    
    def test_perform_action_schedule_without_time(self, service, repository, sample_review_item):
        """Test schedule action without scheduled time"""
        repository.create_review_item(sample_review_item)
        
        success, message = service.perform_action(
            sample_review_item.id,
            sample_review_item.founder_id,
            ReviewAction.SCHEDULE,
            reviewer_id="reviewer_123"
        )
        
        assert success is False
        assert "Scheduled time required" in message
    
    def test_perform_action_request_revision(self, service, repository, sample_review_item, mock_content_service):
        """Test request revision action"""
        repository.create_review_item(sample_review_item)
        
        feedback = ReviewFeedback(
            rating=3,
            comments="Needs improvement",
            improvement_suggestions=["Add more context", "Improve tone"]
        )
        
        success, message = service.perform_action(
            sample_review_item.id,
            sample_review_item.founder_id,
            ReviewAction.REQUEST_REVISION,
            feedback=feedback,
            reviewer_id="reviewer_123"
        )
        
        assert success is True
        mock_content_service.request_revision.assert_called_once()
        
        # Verify status was updated to rejected
        updated_item = service.get_review_item(
            sample_review_item.id,
            sample_review_item.founder_id
        )
        assert updated_item.status == ReviewStatus.REJECTED
    
    def test_batch_review(self, service, repository):
        """Test batch review operations"""
        # Create multiple items
        founder_id = "founder_123"
        item_ids = []
        
        for i in range(3):
            item = ReviewItem(
                id=str(uuid.uuid4()),
                content_draft_id=f"draft_{i}",
                founder_id=founder_id,
                content_type="tweet",
                original_content=f"content {i}",
                current_content=f"content {i}",
                generation_reason="test",
                ai_confidence_score=0.8
            )
            repository.create_review_item(item)
            item_ids.append(item.id)
        
        # Create batch request
        batch_request = ReviewBatchRequest(
            item_ids=item_ids,
            action=ReviewAction.APPROVE,
            feedback=ReviewFeedback(rating=4, comments="Batch approved")
        )
        
        results = service.batch_review(batch_request, founder_id, "reviewer_123")
        
        assert results['total'] == 3
        assert len(results['successful']) == 3
        assert len(results['failed']) == 0
    
    def test_calculate_review_priority(self, service):
        """Test priority calculation logic"""
        # Mock draft with high confidence
        mock_draft = Mock()
        mock_draft.quality_score = 0.9
        mock_draft.trend_context = {"trend_score": 0.8, "is_emerging": True}
        mock_draft.content_type = "reply"
        
        priority = service._calculate_review_priority(mock_draft)
        
        # Base (5) + high confidence (2) + high trend score (2) + emerging (1) + reply (1) = 11
        # But max is 10
        assert priority == 10
    
    def test_get_review_statistics(self, service, repository):
        """Test getting review statistics"""
        founder_id = "founder_123"
        
        # Create test items
        for i in range(5):
            item = ReviewItem(
                id=str(uuid.uuid4()),
                content_draft_id=f"draft_{i}",
                founder_id=founder_id,
                content_type="tweet",
                original_content=f"content {i}",
                current_content=f"content {i}",
                generation_reason="test",
                ai_confidence_score=0.8,
                status=ReviewStatus.APPROVED if i < 3 else ReviewStatus.REJECTED
            )
            repository.create_review_item(item)
        
        stats = service.get_review_statistics(founder_id, days=30)
        
        assert stats.total_items == 5
        assert stats.approved_items == 3
        assert stats.rejected_items == 2
        assert stats.approval_rate == 0.6


# Integration Tests
class TestReviewOptimizationIntegration:
    """Test integration between components"""
    
    def test_full_review_workflow(self, service, repository, mock_content_service, mock_scheduling_service):
        """Test complete review workflow"""
        # 1. Create review item from draft
        draft_id = "draft_123"
        founder_id = "founder_123"
        
        item_id = service.create_review_item_from_draft(draft_id, founder_id)
        assert item_id is not None
        
        # 2. Edit content
        new_content = "Edited content"
        success = service.update_content(item_id, founder_id, new_content, "editor_123")
        assert success is True
        
        # 3. Update SEO elements
        success = service.update_seo_elements(
            item_id, founder_id,
            hashtags=["#edited"], keywords=["edited"],
            editor_id="editor_123"
        )
        assert success is True
        
        # 4. Approve the item
        feedback = ReviewFeedback(rating=5, comments="Great content")
        success, message = service.perform_action(
            item_id, founder_id, ReviewAction.APPROVE,
            feedback=feedback, reviewer_id="reviewer_123"
        )
        assert success is True
        
        # 5. Verify final state
        final_item = service.get_review_item(item_id, founder_id)
        assert final_item.status == ReviewStatus.APPROVED
        assert final_item.current_content == new_content
        assert final_item.hashtags == ["#edited"]
        assert len(final_item.edit_history) == 3  # content + hashtags + keywords
        assert final_item.feedback.rating == 5
        
        # 6. Verify scheduling service was called
        mock_scheduling_service.add_to_queue.assert_called_once()
    
    def test_review_queue_filtering_integration(self, service, repository):
        """Test review queue with complex filtering"""
        founder_id = "founder_123"
        
        # Create items with different properties
        items_data = [
            {"priority": 8, "status": ReviewStatus.PENDING, "confidence": 0.9},
            {"priority": 3, "status": ReviewStatus.APPROVED, "confidence": 0.5},
            {"priority": 7, "status": ReviewStatus.PENDING, "confidence": 0.8},
            {"priority": 2, "status": ReviewStatus.REJECTED, "confidence": 0.3},
        ]
        
        for i, data in enumerate(items_data):
            item = ReviewItem(
                id=str(uuid.uuid4()),
                content_draft_id=f"draft_{i}",
                founder_id=founder_id,
                content_type="tweet",
                original_content=f"content {i}",
                current_content=f"content {i}",
                generation_reason="test",
                ai_confidence_score=data["confidence"],
                status=data["status"],
                review_priority=data["priority"]
            )
            repository.create_review_item(item)
        
        # Test complex filter
        filter_req = ReviewFilterRequest(
            status=ReviewStatus.PENDING,
            priority_min=5,
            ai_confidence_min=0.7,
            limit=10
        )
        
        items = service.get_review_queue(founder_id, filter_req)
        
        # Should return only items that match all criteria
        assert len(items) == 2  # Items 0 and 2
        for item in items:
            assert item.status == ReviewStatus.PENDING
            assert item.review_priority >= 5
            assert item.ai_confidence_score >= 0.7


# Error Handling Tests
class TestReviewOptimizationErrorHandling:
    """Test error handling scenarios"""
    
    def test_invalid_item_access(self, service, repository, sample_review_item):
        """Test accessing item with wrong founder_id"""
        repository.create_review_item(sample_review_item)
        
        # Try to access with different founder_id
        item = service.get_review_item(sample_review_item.id, "wrong_founder")
        assert item is None
    
    def test_update_nonexistent_item(self, service):
        """Test updating non-existent item"""
        success = service.update_content(
            "nonexistent_id", "founder_123", "new content", "editor_123"
        )
        assert success is False
    
    def test_perform_action_on_nonexistent_item(self, service):
        """Test performing action on non-existent item"""
        success, message = service.perform_action(
            "nonexistent_id", "founder_123", ReviewAction.APPROVE, reviewer_id="reviewer_123"
        )
        assert success is False
        assert "not found" in message
    
    def test_scheduling_service_failure(self, service, repository, sample_review_item, mock_scheduling_service):
        """Test handling scheduling service failure"""
        repository.create_review_item(sample_review_item)
        mock_scheduling_service.add_to_queue.return_value = False
        
        success, message = service.perform_action(
            sample_review_item.id,
            sample_review_item.founder_id,
            ReviewAction.APPROVE,
            reviewer_id="reviewer_123"
        )
        
        assert success is False
        assert "Failed to add to scheduling queue" in message
    
    def test_repository_database_error(self, service, repository, sample_review_item):
        """Test handling database errors"""
        repository.create_review_item(sample_review_item)
        
        # Mock database session to raise an exception
        with patch.object(repository.db_session, 'commit', side_effect=Exception("DB Error")):
            success = service.update_content(
                sample_review_item.id,
                sample_review_item.founder_id,
                "new content",
                "editor_123"
            )
            assert success is False


if __name__ == "__main__":
    pytest.main(["-v", __file__])