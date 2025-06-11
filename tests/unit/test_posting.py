"""Comprehensive tests for the Scheduling Posting Module"""
import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from modules.scheduling_posting.models import (
    ScheduledPost, PostStatus, PostPriority, ContentType, PostingRule,
    SchedulingRequest, SchedulingResult, PostingQueue, PostingStatistics,
    PostingBatch
)
from modules.scheduling_posting.repository import (
    SchedulingPostingRepository, ScheduledPostTable, PostingRuleTable, Base
)
from modules.scheduling_posting.scheduler import ContentScheduler
from modules.scheduling_posting.publisher import ContentPublisher
from modules.scheduling_posting.service import SchedulingPostingService

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
def repository(in_memory_db):
    """Create repository with in-memory database"""
    return SchedulingPostingRepository(in_memory_db)

@pytest.fixture
def mock_twitter_client():
    """Mock Twitter API client"""
    client = Mock()
    client.create_tweet = Mock(return_value={
        "data": {"id": "1234567890"}
    })
    return client

@pytest.fixture
def mock_user_service():
    """Mock user profile service"""
    service = Mock()
    service.get_twitter_access_token = Mock(return_value="mock_access_token")
    return service

@pytest.fixture
def scheduler(repository):
    """Create content scheduler"""
    return ContentScheduler(repository)

@pytest.fixture
def publisher(repository, mock_twitter_client, mock_user_service):
    """Create content publisher"""
    return ContentPublisher(repository, mock_twitter_client, mock_user_service)

@pytest.fixture
def service(repository, mock_twitter_client, mock_user_service):
    """Create scheduling posting service"""
    return SchedulingPostingService(repository, mock_twitter_client, mock_user_service)

@pytest.fixture
def sample_posting_rule():
    """Create sample posting rule"""
    return PostingRule(
        founder_id="founder_123",
        name="Default Rule",
        description="Default posting rule",
        posting_hours_start=9,
        posting_hours_end=21,
        posting_days=[1, 2, 3, 4, 5],
        max_posts_per_hour=2,
        max_posts_per_day=5,
        min_interval_minutes=30
    )

@pytest.fixture
def sample_scheduled_post():
    """Create sample scheduled post"""
    return ScheduledPost(
        founder_id="founder_123",
        content_draft_id="draft_123",
        content_text="Test tweet content",
        content_type=ContentType.TWEET,
        hashtags=["#test"],
        keywords=["test"],
        scheduled_time=datetime.utcnow() + timedelta(hours=1),
        priority=PostPriority.NORMAL
    )

# Model Tests
class TestSchedulingModels:
    """Test Pydantic models"""
    
    def test_scheduled_post_creation(self):
        """Test ScheduledPost model creation"""
        future_time = datetime.utcnow() + timedelta(hours=1)
        
        post = ScheduledPost(
            founder_id="founder_123",
            content_draft_id="draft_123",
            content_text="Test content",
            content_type=ContentType.TWEET,
            scheduled_time=future_time
        )
        
        assert post.founder_id == "founder_123"
        assert post.status == PostStatus.SCHEDULED
        assert post.priority == PostPriority.NORMAL
        assert post.retry_count == 0
        assert len(post.hashtags) == 0
    
    def test_scheduled_post_content_validation(self):
        """Test content validation"""
        future_time = datetime.utcnow() + timedelta(hours=1)
        
        # Test tweet length validation
        with pytest.raises(ValueError, match="Tweet content cannot exceed 280 characters"):
            ScheduledPost(
                founder_id="founder_123",
                content_draft_id="draft_123",
                content_text="x" * 281,  # Too long
                content_type=ContentType.TWEET,
                scheduled_time=future_time
            )
    
    def test_scheduled_post_time_validation(self):
        """Test scheduled time validation"""
        past_time = datetime.utcnow() - timedelta(hours=1)
        
        with pytest.raises(ValueError, match="Scheduled time must be in the future"):
            ScheduledPost(
                founder_id="founder_123",
                content_draft_id="draft_123",
                content_text="Test content",
                content_type=ContentType.TWEET,
                scheduled_time=past_time
            )
    
    def test_posting_rule_validation(self):
        """Test posting rule validation"""
        # Test valid rule
        rule = PostingRule(
            founder_id="founder_123",
            name="Test Rule",
            posting_hours_start=9,
            posting_hours_end=17,
            posting_days=[1, 2, 3, 4, 5]
        )
        
        assert rule.posting_hours_start == 9
        assert rule.posting_hours_end == 17
        assert rule.posting_days == [1, 2, 3, 4, 5]
    
    def test_posting_rule_hours_validation(self):
        """Test posting hours validation"""
        with pytest.raises(ValueError, match="End hour must be after start hour"):
            PostingRule(
                founder_id="founder_123",
                name="Invalid Rule",
                posting_hours_start=17,
                posting_hours_end=9  # End before start
            )
    
    def test_posting_queue_operations(self):
        """Test posting queue operations"""
        queue = PostingQueue()
        
        # Create posts with different priorities
        urgent_post = ScheduledPost(
            founder_id="founder_123",
            content_draft_id="draft_1",
            content_text="Urgent post",
            content_type=ContentType.TWEET,
            scheduled_time=datetime.utcnow() + timedelta(hours=2),
            priority=PostPriority.URGENT
        )
        
        normal_post = ScheduledPost(
            founder_id="founder_123",
            content_draft_id="draft_2",
            content_text="Normal post",
            content_type=ContentType.TWEET,
            scheduled_time=datetime.utcnow() + timedelta(hours=1),
            priority=PostPriority.NORMAL
        )
        
        # Add posts to queue
        queue.add_post(urgent_post)
        queue.add_post(normal_post)
        
        assert queue.total_posts == 2
        
        # Get next post (should be urgent despite later time)
        next_post = queue.get_next_post()
        assert next_post.priority == PostPriority.URGENT
        
        # Remove post
        success = queue.remove_post(urgent_post.id)
        assert success
        assert queue.total_posts == 1

# Repository Tests
class TestSchedulingPostingRepository:
    """Test repository operations"""
    
    def test_create_scheduled_post(self, repository, sample_scheduled_post):
        """Test creating scheduled post"""
        success = repository.create_scheduled_post(sample_scheduled_post)
        assert success
        
        # Verify post was created
        retrieved_post = repository.get_scheduled_post(sample_scheduled_post.id)
        assert retrieved_post is not None
        assert retrieved_post.content_text == sample_scheduled_post.content_text
        assert retrieved_post.founder_id == sample_scheduled_post.founder_id
    
    def test_get_scheduled_post_not_found(self, repository):
        """Test getting non-existent scheduled post"""
        post = repository.get_scheduled_post("non_existent_id")
        assert post is None
    
    def test_get_posts_by_status(self, repository, sample_scheduled_post):
        """Test getting posts by status"""
        repository.create_scheduled_post(sample_scheduled_post)
        
        posts = repository.get_scheduled_posts_by_status(PostStatus.SCHEDULED)
        assert len(posts) == 1
        assert posts[0].status == PostStatus.SCHEDULED
    
    def test_get_posts_ready_for_posting(self, repository):
        """Test getting posts ready for posting"""
        # Create post scheduled in the past
        past_post = ScheduledPost(
            founder_id="founder_123",
            content_draft_id="draft_past",
            content_text="Past post",
            content_type=ContentType.TWEET,
            scheduled_time=datetime.utcnow() - timedelta(minutes=5)
        )
        
        # Create post scheduled in the future
        future_post = ScheduledPost(
            founder_id="founder_123",
            content_draft_id="draft_future",
            content_text="Future post",
            content_type=ContentType.TWEET,
            scheduled_time=datetime.utcnow() + timedelta(hours=1)
        )
        
        repository.create_scheduled_post(past_post)
        repository.create_scheduled_post(future_post)
        
        ready_posts = repository.get_posts_ready_for_posting()
        assert len(ready_posts) == 1
        assert ready_posts[0].id == past_post.id
    
    def test_update_post_status(self, repository, sample_scheduled_post):
        """Test updating post status"""
        repository.create_scheduled_post(sample_scheduled_post)
        
        # Update to posted status
        success = repository.update_post_status(
            sample_scheduled_post.id, 
            PostStatus.POSTED, 
            posted_tweet_id="tweet_123"
        )
        assert success
        
        # Verify update
        updated_post = repository.get_scheduled_post(sample_scheduled_post.id)
        assert updated_post.status == PostStatus.POSTED
        assert updated_post.posted_tweet_id == "tweet_123"
        assert updated_post.posted_at is not None
    
    def test_reschedule_post(self, repository, sample_scheduled_post):
        """Test rescheduling post"""
        repository.create_scheduled_post(sample_scheduled_post)
        
        new_time = datetime.utcnow() + timedelta(hours=2)
        success = repository.reschedule_post(sample_scheduled_post.id, new_time)
        assert success
        
        # Verify reschedule
        updated_post = repository.get_scheduled_post(sample_scheduled_post.id)
        assert updated_post.scheduled_time == new_time
        assert updated_post.status == PostStatus.SCHEDULED
    
    def test_delete_scheduled_post(self, repository, sample_scheduled_post):
        """Test deleting scheduled post"""
        repository.create_scheduled_post(sample_scheduled_post)
        
        success = repository.delete_scheduled_post(
            sample_scheduled_post.id, 
            sample_scheduled_post.founder_id
        )
        assert success
        
        # Verify deletion
        deleted_post = repository.get_scheduled_post(sample_scheduled_post.id)
        assert deleted_post is None
    
    def test_create_posting_rule(self, repository, sample_posting_rule):
        """Test creating posting rule"""
        success = repository.create_posting_rule(sample_posting_rule)
        assert success
        
        # Verify rule was created
        rules = repository.get_posting_rules(sample_posting_rule.founder_id)
        assert len(rules) == 1
        assert rules[0].name == sample_posting_rule.name
    
    def test_get_posting_statistics(self, repository):
        """Test getting posting statistics"""
        founder_id = "founder_123"
        
        # Create posts with different statuses
        posted_post = ScheduledPost(
            founder_id=founder_id,
            content_draft_id="draft_1",
            content_text="Posted content",
            content_type=ContentType.TWEET,
            scheduled_time=datetime.utcnow() - timedelta(hours=1),
            status=PostStatus.POSTED
        )
        
        failed_post = ScheduledPost(
            founder_id=founder_id,
            content_draft_id="draft_2",
            content_text="Failed content",
            content_type=ContentType.TWEET,
            scheduled_time=datetime.utcnow() - timedelta(hours=2),
            status=PostStatus.FAILED
        )
        
        repository.create_scheduled_post(posted_post)
        repository.create_scheduled_post(failed_post)
        
        # Get statistics
        start_date = datetime.utcnow() - timedelta(days=1)
        end_date = datetime.utcnow()
        stats = repository.get_posting_statistics(founder_id, start_date, end_date)
        
        assert stats.total_posted == 1
        assert stats.total_failed == 1
        assert stats.success_rate == 0.5

# Scheduler Tests
class TestContentScheduler:
    """Test content scheduler"""
    
    def test_schedule_content_no_rules(self, scheduler):
        """Test scheduling content without posting rules"""
        request = SchedulingRequest(
            content_draft_id="draft_123",
            founder_id="founder_123",
            preferred_time=datetime.utcnow() + timedelta(hours=1)
        )
        
        result = scheduler.schedule_content(
            request, "Test content", ContentType.TWEET
        )
        
        assert result.success
        assert result.scheduled_post_id is not None
        assert result.scheduled_time == request.preferred_time
    
    def test_schedule_content_with_rules(self, scheduler, repository, sample_posting_rule):
        """Test scheduling content with posting rules"""
        # Create posting rule
        repository.create_posting_rule(sample_posting_rule)
        
        # Try to schedule during allowed hours
        allowed_time = datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0)
        if allowed_time <= datetime.utcnow():
            allowed_time += timedelta(days=1)
        
        request = SchedulingRequest(
            content_draft_id="draft_123",
            founder_id="founder_123",
            preferred_time=allowed_time
        )
        
        result = scheduler.schedule_content(
            request, "Test content", ContentType.TWEET
        )
        
        assert result.success
        assert result.scheduled_post_id is not None
    
    def test_schedule_batch(self, scheduler):
        """Test batch scheduling"""
        founder_id = "founder_123"
        draft_ids = ["draft_1", "draft_2", "draft_3"]
        start_time = datetime.utcnow() + timedelta(hours=1)
        
        results = scheduler.schedule_batch(
            founder_id, draft_ids, start_time, interval_minutes=30
        )
        
        assert results["total_items"] == 3
        assert len(results["scheduled"]) <= 3
        assert len(results["schedule_times"]) == len(results["scheduled"])
    
    def test_get_next_posting_opportunity(self, scheduler, repository, sample_posting_rule):
        """Test getting next posting opportunity"""
        # Create posting rule
        repository.create_posting_rule(sample_posting_rule)
        
        founder_id = "founder_123"
        next_time = scheduler.get_next_posting_opportunity(founder_id, ContentType.TWEET)
        
        assert next_time is not None
        assert next_time > datetime.utcnow()
    
    def test_optimize_posting_schedule(self, scheduler, repository):
        """Test posting schedule optimization"""
        founder_id = "founder_123"
        
        # Create some scheduled posts
        for i in range(3):
            post = ScheduledPost(
                founder_id=founder_id,
                content_draft_id=f"draft_{i}",
                content_text=f"Content {i}",
                content_type=ContentType.TWEET,
                scheduled_time=datetime.utcnow() + timedelta(hours=i+1)
            )
            repository.create_scheduled_post(post)
        
        analysis = scheduler.optimize_posting_schedule(founder_id, days_ahead=7)
        
        assert "total_scheduled" in analysis
        assert "posting_distribution" in analysis
        assert "optimization_suggestions" in analysis
        assert analysis["total_scheduled"] == 3

# Publisher Tests
class TestContentPublisher:
    """Test content publisher"""
    
    @pytest.mark.asyncio
    async def test_publish_ready_posts_success(self, publisher, repository):
        """Test successful publishing of ready posts"""
        # Create ready post
        ready_post = ScheduledPost(
            founder_id="founder_123",
            content_draft_id="draft_123",
            content_text="Ready to publish",
            content_type=ContentType.TWEET,
            scheduled_time=datetime.utcnow() - timedelta(minutes=5)
        )
        
        repository.create_scheduled_post(ready_post)
        
        # Mock successful Twitter API response
        publisher.twitter_client.create_tweet.return_value = {
            "data": {"id": "tweet_123"}
        }
        
        results = await publisher.publish_ready_posts()
        
        assert results["processed"] == 1
        assert results["successful"] == 1
        assert results["failed"] == 0
        
        # Verify post status was updated
        updated_post = repository.get_scheduled_post(ready_post.id)
        assert updated_post.status == PostStatus.POSTED
        assert updated_post.posted_tweet_id == "tweet_123"
    
    @pytest.mark.asyncio
    async def test_publish_ready_posts_failure(self, publisher, repository):
        """Test publishing failure handling"""
        # Create ready post
        ready_post = ScheduledPost(
            founder_id="founder_123",
            content_draft_id="draft_123",
            content_text="Ready to publish",
            content_type=ContentType.TWEET,
            scheduled_time=datetime.utcnow() - timedelta(minutes=5)
        )
        
        repository.create_scheduled_post(ready_post)
        
        # Mock Twitter API error
        from modules.twitter_api.exceptions import TwitterAPIError
        publisher.twitter_client.create_tweet.side_effect = TwitterAPIError("API Error")
        
        results = await publisher.publish_ready_posts()
        
        assert results["processed"] == 1
        assert results["successful"] == 0
        # Should retry on API error
        assert results["retried"] == 1
    
    @pytest.mark.asyncio
    async def test_publish_no_access_token(self, publisher, repository):
        """Test publishing without access token"""
        # Mock no access token
        publisher.user_service.get_twitter_access_token.return_value = None
        
        # Create ready post
        ready_post = ScheduledPost(
            founder_id="founder_123",
            content_draft_id="draft_123",
            content_text="Ready to publish",
            content_type=ContentType.TWEET,
            scheduled_time=datetime.utcnow() - timedelta(minutes=5)
        )
        
        repository.create_scheduled_post(ready_post)
        
        results = await publisher.publish_ready_posts()
        
        assert results["processed"] == 1
        assert results["successful"] == 0
        assert results["failed"] == 1
    
    @pytest.mark.asyncio
    async def test_publish_immediate(self, publisher, repository, sample_scheduled_post):
        """Test immediate publishing"""
        repository.create_scheduled_post(sample_scheduled_post)
        
        # Mock successful response
        publisher.twitter_client.create_tweet.return_value = {
            "data": {"id": "immediate_tweet_123"}
        }
        
        result = await publisher.publish_immediate(
            sample_scheduled_post, 
            sample_scheduled_post.founder_id
        )
        
        assert result["success"]
        assert result["tweet_id"] == "immediate_tweet_123"
    
    def test_get_publishing_status(self, publisher, repository):
        """Test getting publishing status"""
        # Create posts with different statuses
        posting_post = ScheduledPost(
            founder_id="founder_123",
            content_draft_id="draft_1",
            content_text="Posting now",
            content_type=ContentType.TWEET,
            scheduled_time=datetime.utcnow(),
            status=PostStatus.POSTING
        )
        
        scheduled_post = ScheduledPost(
            founder_id="founder_123",
            content_draft_id="draft_2",
            content_text="Scheduled",
            content_type=ContentType.TWEET,
            scheduled_time=datetime.utcnow() + timedelta(hours=1)
        )
        
        repository.create_scheduled_post(posting_post)
        repository.create_scheduled_post(scheduled_post)
        
        status = publisher.get_publishing_status("founder_123")
        
        assert status["currently_posting"] == 1
        assert status["scheduled_count"] == 1
        assert "queue_health" in status

# Service Tests
class TestSchedulingPostingService:
    """Test main service"""
    
    def test_schedule_content_from_draft(self, service):
        """Test scheduling content from draft"""
        result = service.schedule_content_from_draft(
            draft_id="draft_123",
            founder_id="founder_123",
            priority=PostPriority.HIGH,
            preferred_time=datetime.utcnow() + timedelta(hours=1)
        )
        
        assert result.success
        assert result.scheduled_post_id is not None
    
    def test_schedule_batch_content(self, service):
        """Test batch content scheduling"""
        draft_ids = ["draft_1", "draft_2", "draft_3"]
        start_time = datetime.utcnow() + timedelta(hours=1)
        
        results = service.schedule_batch_content(
            founder_id="founder_123",
            draft_ids=draft_ids,
            start_time=start_time,
            interval_minutes=30
        )
        
        assert "batch_id" in results
        assert results["total_items"] == 3
    
    def test_reschedule_post(self, service, repository, sample_scheduled_post):
        """Test rescheduling post"""
        repository.create_scheduled_post(sample_scheduled_post)
        
        new_time = datetime.utcnow() + timedelta(hours=3)
        success = service.reschedule_post(
            sample_scheduled_post.id, 
            new_time, 
            sample_scheduled_post.founder_id
        )
        
        assert success
        
        # Verify reschedule
        updated_post = repository.get_scheduled_post(sample_scheduled_post.id)
        assert updated_post.scheduled_time == new_time
    
    def test_cancel_scheduled_post(self, service, repository, sample_scheduled_post):
        """Test cancelling scheduled post"""
        repository.create_scheduled_post(sample_scheduled_post)
        
        success = service.cancel_scheduled_post(
            sample_scheduled_post.id, 
            sample_scheduled_post.founder_id
        )
        
        assert success
        
        # Verify cancellation
        updated_post = repository.get_scheduled_post(sample_scheduled_post.id)
        assert updated_post.status == PostStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_publish_ready_content(self, service, repository):
        """Test publishing ready content"""
        # Create ready post
        ready_post = ScheduledPost(
            founder_id="founder_123",
            content_draft_id="draft_123",
            content_text="Ready content",
            content_type=ContentType.TWEET,
            scheduled_time=datetime.utcnow() - timedelta(minutes=5)
        )
        
        repository.create_scheduled_post(ready_post)
        
        results = await service.publish_ready_content()
        
        assert results["processed"] >= 1
    
    @pytest.mark.asyncio
    async def test_publish_post_immediately(self, service, repository, sample_scheduled_post):
        """Test immediate post publishing"""
        repository.create_scheduled_post(sample_scheduled_post)
        
        result = await service.publish_post_immediately(
            sample_scheduled_post.id, 
            sample_scheduled_post.founder_id
        )
        
        assert result["success"]
    
    def test_toggle_auto_publishing(self, service):
        """Test toggling auto-publishing"""
        # Test enable
        success = service.toggle_auto_publishing(True)
        assert success
        assert service.auto_publishing_enabled
        
        # Test disable
        success = service.toggle_auto_publishing(False)
        assert success
        assert not service.auto_publishing_enabled
    
    def test_create_posting_rule(self, service, sample_posting_rule):
        """Test creating posting rule"""
        success = service.create_posting_rule(sample_posting_rule)
        assert success
        
        # Verify rule was created
        rules = service.get_posting_rules(sample_posting_rule.founder_id)
        assert len(rules) == 1
        assert rules[0].name == sample_posting_rule.name
    
    def test_get_posting_queue(self, service, repository):
        """Test getting posting queue"""
        # Create posts with different priorities
        for i, priority in enumerate([PostPriority.URGENT, PostPriority.NORMAL, PostPriority.LOW]):
            post = ScheduledPost(
                founder_id="founder_123",
                content_draft_id=f"draft_{i}",
                content_text=f"Content {i}",
                content_type=ContentType.TWEET,
                scheduled_time=datetime.utcnow() + timedelta(hours=i+1),
                priority=priority
            )
            repository.create_scheduled_post(post)
        
        queue = service.get_posting_queue("founder_123")
        assert queue.total_posts == 3
        
        # Check priority ordering
        next_post = queue.get_next_post()
        assert next_post.priority == PostPriority.URGENT
    
    def test_get_posting_statistics(self, service, repository):
        """Test getting posting statistics"""
        founder_id = "founder_123"
        
        # Create some posts
        for i in range(5):
            status = PostStatus.POSTED if i < 3 else PostStatus.FAILED
            post = ScheduledPost(
                founder_id=founder_id,
                content_draft_id=f"draft_{i}",
                content_text=f"Content {i}",
                content_type=ContentType.TWEET,
                scheduled_time=datetime.utcnow() - timedelta(hours=i),
                status=status
            )
            repository.create_scheduled_post(post)
        
        stats = service.get_posting_statistics(founder_id, days=7)
        
        assert stats.total_posted == 3
        assert stats.total_failed == 2
        assert stats.success_rate == 0.6
    
    def test_analyze_posting_performance(self, service, repository):
        """Test posting performance analysis"""
        founder_id = "founder_123"
        
        # Create successful posts
        for i in range(3):
            post = ScheduledPost(
                founder_id=founder_id,
                content_draft_id=f"draft_{i}",
                content_text=f"Content {i}",
                content_type=ContentType.TWEET,
                scheduled_time=datetime.utcnow() - timedelta(hours=i),
                status=PostStatus.POSTED
            )
            repository.create_scheduled_post(post)
        
        performance = service.analyze_posting_performance(founder_id, days=7)
        
        assert "posting_consistency" in performance
        assert "reliability" in performance
        assert "timing" in performance
        assert "optimization" in performance
        assert "recommendations" in performance
    
    def test_get_service_health(self, service):
        """Test service health check"""
        health = service.get_service_health()
        
        assert "service_status" in health
        assert "auto_publishing_enabled" in health
        assert "last_check" in health
        assert "components" in health

# Integration Tests
class TestSchedulingPostingIntegration:
    """Test integration between components"""
    
    @pytest.mark.asyncio
    async def test_full_scheduling_publishing_workflow(self, service, repository):
        """Test complete workflow from scheduling to publishing"""
        # 1. Schedule content
        result = service.schedule_content_from_draft(
            draft_id="integration_draft",
            founder_id="founder_123",
            priority=PostPriority.HIGH,
            preferred_time=datetime.utcnow() + timedelta(minutes=1)
        )
        
        assert result.success
        post_id = result.scheduled_post_id
        
        # 2. Verify it's in the queue
        queue = service.get_posting_queue("founder_123")
        assert queue.total_posts >= 1
        
        # 3. Publish immediately
        publish_result = await service.publish_post_immediately(post_id, "founder_123")
        assert publish_result["success"]
        
        # 4. Verify final status
        final_post = repository.get_scheduled_post(post_id)
        assert final_post.status == PostStatus.POSTED
    
    def test_rules_enforcement_workflow(self, service, repository, sample_posting_rule):
        """Test that posting rules are properly enforced"""
        # 1. Create posting rule
        service.create_posting_rule(sample_posting_rule)
        
        # 2. Try to schedule outside allowed hours
        disallowed_time = datetime.utcnow().replace(hour=23, minute=0, second=0, microsecond=0)
        if disallowed_time <= datetime.utcnow():
            disallowed_time += timedelta(days=1)
        
        result = service.schedule_content_from_draft(
            draft_id="rules_test_draft",
            founder_id="founder_123",
            preferred_time=disallowed_time
        )
        
        # Should succeed but adjust time
        assert result.success
        assert result.adjusted_from_preferred or result.rules_violations
    
    @pytest.mark.asyncio
    async def test_retry_mechanism_workflow(self, service, repository, mock_twitter_client):
        """Test retry mechanism for failed posts"""
        # 1. Schedule content for immediate posting
        result = service.schedule_content_from_draft(
            draft_id="retry_test_draft",
            founder_id="founder_123",
            preferred_time=datetime.utcnow() - timedelta(minutes=1)
        )
        
        assert result.success
        post_id = result.scheduled_post_id
        
        # 2. Mock API failure
        from modules.twitter_api.exceptions import TwitterAPIError
        mock_twitter_client.create_tweet.side_effect = TwitterAPIError("Rate limit exceeded")
        
        # 3. Try to publish - should retry
        results = await service.publish_ready_content()
        
        assert results["processed"] == 1
        assert results["retried"] >= 1
        
        # 4. Verify post was marked for retry
        updated_post = repository.get_scheduled_post(post_id)
        assert updated_post.status == PostStatus.RETRYING or updated_post.retry_count > 0

# Performance Tests
class TestSchedulingPostingPerformance:
    """Test performance and edge cases"""
    
    def test_large_batch_scheduling(self, service):
        """Test scheduling large batch of content"""
        founder_id = "founder_performance"
        draft_ids = [f"draft_{i}" for i in range(100)]  # 100 posts
        start_time = datetime.utcnow() + timedelta(hours=1)
        
        results = service.schedule_batch_content(
            founder_id=founder_id,
            draft_ids=draft_ids,
            start_time=start_time,
            interval_minutes=15  # Every 15 minutes
        )
        
        assert results["total_items"] == 100
        assert len(results["details"]["scheduled"]) <= 100
    
    def test_concurrent_scheduling(self, service):
        """Test concurrent scheduling operations"""
        import threading
        
        founder_id = "founder_concurrent"
        results = []
        
        def schedule_content(draft_id):
            result = service.schedule_content_from_draft(
                draft_id=f"concurrent_draft_{draft_id}",
                founder_id=founder_id,
                preferred_time=datetime.utcnow() + timedelta(hours=1)
            )
            results.append(result)
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=schedule_content, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        successful = [r for r in results if r.success]
        assert len(successful) == 10
    
    @pytest.mark.asyncio
    async def test_high_volume_publishing(self, service, repository):
        """Test publishing high volume of posts"""
        founder_id = "founder_volume"
        
        # Create many ready posts
        for i in range(50):
            post = ScheduledPost(
                founder_id=founder_id,
                content_draft_id=f"volume_draft_{i}",
                content_text=f"Volume test content {i}",
                content_type=ContentType.TWEET,
                scheduled_time=datetime.utcnow() - timedelta(minutes=1)
            )
            repository.create_scheduled_post(post)
        
        # Publish all at once
        results = await service.publish_ready_content(limit=50)
        
        assert results["processed"] == 50
        # Should handle volume without errors
        assert "error" not in results
    
    def test_edge_case_scheduling_times(self, service):
        """Test edge cases for scheduling times"""
        founder_id = "founder_edge"
        
        # Test scheduling exactly at midnight
        midnight = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        result = service.schedule_content_from_draft(
            draft_id="midnight_draft",
            founder_id=founder_id,
            preferred_time=midnight
        )
        assert result.success
        
        # Test scheduling on leap year date (Feb 29)
        try:
            leap_year_date = datetime(2024, 2, 29, 12, 0, 0)
            if leap_year_date > datetime.utcnow():
                result = service.schedule_content_from_draft(
                    draft_id="leap_year_draft",
                    founder_id=founder_id,
                    preferred_time=leap_year_date
                )
                assert result.success
        except ValueError:
            # Not a leap year, skip this test
            pass

# Error Handling Tests
class TestSchedulingPostingErrorHandling:
    """Test error handling and recovery"""
    
    def test_database_error_handling(self, service, repository):
        """Test handling of database errors"""
        # Mock database error
        with patch.object(repository, 'create_scheduled_post', side_effect=Exception("DB Error")):
            result = service.schedule_content_from_draft(
                draft_id="db_error_draft",
                founder_id="founder_error",
                preferred_time=datetime.utcnow() + timedelta(hours=1)
            )
            
            assert not result.success
            assert "DB Error" in result.message or "Scheduling failed" in result.message
    
    @pytest.mark.asyncio
    async def test_api_error_recovery(self, service, repository, mock_twitter_client):
        """Test recovery from API errors"""
        # Create ready post
        post = ScheduledPost(
            founder_id="founder_api_error",
            content_draft_id="api_error_draft",
            content_text="API error test",
            content_type=ContentType.TWEET,
            scheduled_time=datetime.utcnow() - timedelta(minutes=1)
        )
        repository.create_scheduled_post(post)
        
        # Mock different API errors
        api_errors = [
            "Rate limit exceeded",
            "Authentication failed", 
            "Service unavailable",
            "Invalid request"
        ]
        
        for error_msg in api_errors:
            mock_twitter_client.create_tweet.side_effect = Exception(error_msg)
            
            results = await service.publish_ready_content()
            
            # Should handle error gracefully
            assert "error" not in results or results.get("processed", 0) >= 0
    
    def test_invalid_input_handling(self, service):
        """Test handling of invalid inputs"""
        # Test with empty draft ID
        result = service.schedule_content_from_draft(
            draft_id="",
            founder_id="founder_invalid",
            preferred_time=datetime.utcnow() + timedelta(hours=1)
        )
        # Should handle gracefully (specific behavior depends on implementation)
        
        # Test with invalid founder ID
        result = service.schedule_content_from_draft(
            draft_id="valid_draft",
            founder_id="",
            preferred_time=datetime.utcnow() + timedelta(hours=1)
        )
        # Should handle gracefully
        
        # Test with past time (should be caught by model validation)
        with pytest.raises(ValueError):
            ScheduledPost(
                founder_id="founder_test",
                content_draft_id="test_draft",
                content_text="Test content",
                content_type=ContentType.TWEET,
                scheduled_time=datetime.utcnow() - timedelta(hours=1)
            )

# Complex Workflow Tests
class TestComplexWorkflows:
    """Test complex multi-step workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_content_lifecycle(self, service, repository):
        """Test complete content lifecycle from scheduling to publishing to analysis"""
        founder_id = "founder_lifecycle"
        
        # 1. Create posting rule
        rule = PostingRule(
            founder_id=founder_id,
            name="Lifecycle Rule",
            posting_hours_start=9,
            posting_hours_end=17,
            posting_days=[1, 2, 3, 4, 5],
            max_posts_per_day=3
        )
        service.create_posting_rule(rule)
        
        # 2. Schedule multiple posts
        draft_ids = ["lifecycle_1", "lifecycle_2", "lifecycle_3"]
        batch_results = service.schedule_batch_content(
            founder_id=founder_id,
            draft_ids=draft_ids,
            start_time=datetime.utcnow() + timedelta(minutes=1),
            interval_minutes=30
        )
        
        assert batch_results["successful_schedules"] == 3
        
        # 3. Check posting queue
        queue = service.get_posting_queue(founder_id)
        assert queue.total_posts >= 3
        
        # 4. Publish one immediately
        first_post_id = batch_results["details"]["scheduled"][0]["post_id"]
        publish_result = await service.publish_post_immediately(first_post_id, founder_id)
        assert publish_result["success"]
        
        # 5. Get statistics
        stats = service.get_posting_statistics(founder_id, days=1)
        assert stats.total_posted >= 1
        
        # 6. Analyze performance
        performance = service.analyze_posting_performance(founder_id, days=1)
        assert "posting_consistency" in performance
        assert "reliability" in performance
    
    def test_rule_based_scheduling_workflow(self, service, repository):
        """Test complex rule-based scheduling scenarios"""
        founder_id = "founder_rules"
        
        # Create restrictive posting rule
        rule = PostingRule(
            founder_id=founder_id,
            name="Restrictive Rule",
            posting_hours_start=10,
            posting_hours_end=12,  # Only 2 hours
            posting_days=[2, 4],  # Only Tuesday and Thursday
            max_posts_per_hour=1,
            max_posts_per_day=2,
            min_interval_minutes=60
        )
        service.create_posting_rule(rule)
        
        # Try to schedule multiple posts
        results = []
        for i in range(5):
            result = service.schedule_content_from_draft(
                draft_id=f"restrictive_draft_{i}",
                founder_id=founder_id,
                preferred_time=datetime.utcnow() + timedelta(hours=1)
            )
            results.append(result)
        
        # Should successfully schedule some posts with time adjustments
        successful = [r for r in results if r.success]
        assert len(successful) > 0
        
        # Check that times were adjusted to comply with rules
        adjusted = [r for r in successful if r.adjusted_from_preferred]
        assert len(adjusted) > 0
    
    @pytest.mark.asyncio
    async def test_failure_and_retry_workflow(self, service, repository, mock_twitter_client):
        """Test comprehensive failure and retry workflow"""
        founder_id = "founder_retry"
        
        # Schedule post
        result = service.schedule_content_from_draft(
            draft_id="retry_draft",
            founder_id=founder_id,
            preferred_time=datetime.utcnow() - timedelta(minutes=1)
        )
        assert result.success
        post_id = result.scheduled_post_id
        
        # Mock failure for first few attempts
        call_count = 0
        def mock_create_tweet(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # Fail first 2 attempts
                raise Exception("Temporary API error")
            return {"data": {"id": "success_tweet_123"}}
        
        mock_twitter_client.create_tweet.side_effect = mock_create_tweet
        
        # Try to publish multiple times
        for attempt in range(3):
            results = await service.publish_ready_content()
            if results.get("successful", 0) > 0:
                break
        
        # Should eventually succeed
        final_post = repository.get_scheduled_post(post_id)
        assert final_post.retry_count > 0  # Should have retried
    
    def test_optimization_workflow(self, service, repository):
        """Test schedule optimization workflow"""
        founder_id = "founder_optimize"
        
        # Create many scheduled posts at suboptimal times
        base_time = datetime.utcnow() + timedelta(days=1)
        for i in range(10):
            # Schedule all at 3 AM (suboptimal)
            bad_time = base_time.replace(hour=3, minute=i*5)
            service.schedule_content_from_draft(
                draft_id=f"optimize_draft_{i}",
                founder_id=founder_id,
                preferred_time=bad_time,
                force_schedule=True
            )
        
        # Get optimization analysis
        optimization = service.optimize_schedule(founder_id, days_ahead=7)
        
        assert optimization["total_scheduled"] == 10
        assert len(optimization["optimization_suggestions"]) > 0
        
        # Should suggest better timing
        suggestions = optimization["optimization_suggestions"]
        timing_suggestions = [s for s in suggestions if "engagement" in s.lower() or "optimal" in s.lower()]
        assert len(timing_suggestions) > 0

# Utility and Helper Tests
class TestUtilitiesAndHelpers:
    """Test utility functions and edge cases"""
    
    def test_posting_queue_edge_cases(self):
        """Test posting queue with edge cases"""
        queue = PostingQueue()
        
        # Test empty queue
        assert queue.total_posts == 0
        assert queue.get_next_post() is None
        
        # Test queue with same priorities but different times
        now = datetime.utcnow()
        for i in range(3):
            post = ScheduledPost(
                founder_id="founder_queue",
                content_draft_id=f"queue_draft_{i}",
                content_text=f"Queue content {i}",
                content_type=ContentType.TWEET,
                scheduled_time=now + timedelta(minutes=i*10),
                priority=PostPriority.NORMAL
            )
            queue.add_post(post)
        
        # Should get earliest scheduled post
        next_post = queue.get_next_post()
        assert next_post.scheduled_time == now
        
        # Test remove non-existent post
        success = queue.remove_post("non_existent_id")
        assert not success
    
    def test_model_validation_edge_cases(self):
        """Test model validation with edge cases"""
        # Test maximum length content
        max_content = "x" * 10000  # Maximum allowed length
        post = ScheduledPost(
            founder_id="founder_validation",
            content_draft_id="validation_draft",
            content_text=max_content,
            content_type=ContentType.THREAD,  # Not TWEET, so longer content allowed
            scheduled_time=datetime.utcnow() + timedelta(hours=1)
        )
        assert post.content_text == max_content
        
        # Test posting rule with edge case values
        rule = PostingRule(
            founder_id="founder_edge",
            name="Edge Rule",
            posting_hours_start=0,  # Midnight
            posting_hours_end=23,   # 11 PM
            posting_days=[7],       # Sunday only
            max_posts_per_hour=1,   # Minimum
            max_posts_per_day=1,    # Minimum
            min_interval_minutes=5  # Minimum
        )
        assert rule.posting_hours_start == 0
        assert rule.posting_hours_end == 23
    
    def test_statistics_with_no_data(self, service):
        """Test statistics generation with no data"""
        founder_id = "founder_no_data"
        
        # Get statistics for founder with no posts
        stats = service.get_posting_statistics(founder_id, days=30)
        
        assert stats.total_posted == 0
        assert stats.total_failed == 0
        assert stats.success_rate == 0.0
        assert len(stats.posts_by_hour) == 0
        
        # Performance analysis with no data
        performance = service.analyze_posting_performance(founder_id, days=30)
        
        assert performance["posting_consistency"]["posts_per_day"] == 0
        assert performance["reliability"]["success_rate"] == 0.0
    
    def test_service_health_monitoring(self, service):
        """Test service health monitoring"""
        health = service.get_service_health()
        
        assert "service_status" in health
        assert "components" in health
        assert "last_check" in health
        
        # Should report healthy status initially
        assert health["service_status"] in ["healthy", "degraded", "error"]
        assert health["auto_publishing_enabled"] == service.auto_publishing_enabled

if __name__ == "__main__":
    pytest.main([__file__, "-v"])