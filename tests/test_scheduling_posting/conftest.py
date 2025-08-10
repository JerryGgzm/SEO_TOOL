"""Test configuration and fixtures for scheduling_posting module tests"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock
import uuid
import asyncio

from modules.scheduling_posting import (
    SchedulingPostingService, InternalRulesEngine,
    ScheduleRequest, PublishRequest, BatchScheduleRequest,
    ScheduledContent, PublishStatus, SchedulingPreferences
)
from modules.scheduling_posting.models import ContentQueueItem

# Mock classes
class MockDataFlowManager:
    """Mock data flow manager for testing"""
    
    def __init__(self):
        self.content_drafts = {}
        # Note: scheduled_content removed - now using content_drafts with scheduling fields
        self.user_preferences = {}
        self.analytics_data = {}
        self.call_log = []
    
    def get_content_draft_by_id(self, content_id):
        self.call_log.append(('get_content_draft_by_id', content_id))
        return self.content_drafts.get(content_id)
    
    def get_content_drafts_by_status(self, user_id, status_filter, limit, offset):
        self.call_log.append(('get_content_drafts_by_status', user_id, status_filter))
        drafts = [draft for draft in self.content_drafts.values() 
                 if draft.founder_id == user_id and draft.status in status_filter]
        return drafts[offset:offset+limit]
    
    def create_scheduled_content(self, scheduled_content_data):
        """DEPRECATED: Now updates content_drafts directly instead of separate scheduled_content"""
        self.call_log.append(('create_scheduled_content', scheduled_content_data))
        content_draft_id = scheduled_content_data['content_draft_id']
        
        # Update the content draft with scheduling information (unified table approach)
        if content_draft_id in self.content_drafts:
            self.content_drafts[content_draft_id].update({
                'status': 'scheduled',
                'scheduled_post_time': scheduled_content_data['scheduled_time'],
                'platform': scheduled_content_data.get('platform', 'twitter'),
                'priority': scheduled_content_data.get('priority', 5),
                'retry_count': scheduled_content_data.get('retry_count', 0),
                'max_retries': scheduled_content_data.get('max_retries', 3),
                'created_by': scheduled_content_data.get('created_by')
            })
            return content_draft_id
        return None
    
    def get_scheduled_content_by_draft_id(self, draft_id):
        """DEPRECATED: Now returns content_draft directly since tables are unified"""
        self.call_log.append(('get_scheduled_content_by_draft_id', draft_id))
        if draft_id in self.content_drafts:
            draft_data = self.content_drafts[draft_id]
            if draft_data.get('status') == 'scheduled':
                return MockScheduledContent(draft_data)
        return None
    
    def update_content_draft(self, content_id, updates):
        self.call_log.append(('update_content_draft', content_id, updates))
        if content_id in self.content_drafts:
            for key, value in updates.items():
                setattr(self.content_drafts[content_id], key, value)
            return True
        return False
    
    def update_scheduled_content(self, scheduled_id, updates):
        """DEPRECATED: Now updates content_drafts directly since scheduled_id == content_draft_id"""
        self.call_log.append(('update_scheduled_content', scheduled_id, updates))
        # scheduled_id is now the same as content_draft_id
        if scheduled_id in self.content_drafts:
            self.content_drafts[scheduled_id].update(updates)
            return True
        return False
    
    def get_user_scheduling_preferences(self, user_id):
        self.call_log.append(('get_user_scheduling_preferences', user_id))
        return self.user_preferences.get(user_id)
    
    def get_user_scheduling_rules(self, user_id):
        self.call_log.append(('get_user_scheduling_rules', user_id))
        return []
    
    def get_daily_post_count(self, user_id, date):
        self.call_log.append(('get_daily_post_count', user_id, date))
        return 0
    
    def get_last_post_time(self, user_id):
        self.call_log.append(('get_last_post_time', user_id))
        return None
    
    def get_recent_posts(self, user_id, days):
        self.call_log.append(('get_recent_posts', user_id, days))
        return []
    
    def get_publishing_history(self, user_id, limit, offset):
        self.call_log.append(('get_publishing_history', user_id, limit, offset))
        return []
    
    def get_publishing_analytics(self, user_id, days):
        self.call_log.append(('get_publishing_analytics', user_id, days))
        return {
            'total_scheduled': 0,
            'total_published': 0,
            'total_failed': 0,
            'publish_delays': [],
            'error_breakdown': {},
            'time_distribution': {},
            'platform_breakdown': {'twitter': 0}
        }
    
    def get_queue_statistics(self, user_id):
        self.call_log.append(('get_queue_statistics', user_id))
        return {
            'pending_count': 0,
            'scheduled_count': 0,
            'upcoming_24h': 0,
            'overdue_count': 0,
            'retry_pending_count': 0,
            'status_breakdown': {}
        }
    
    def get_next_scheduled_time(self, user_id):
        self.call_log.append(('get_next_scheduled_time', user_id))
        return None
    
    def get_ready_for_publishing(self, limit):
        self.call_log.append(('get_ready_for_publishing', limit))
        return []

class MockTwitterClient:
    """Mock Twitter client for testing"""
    
    def __init__(self):
        self.call_log = []
        self.should_succeed = True
        self.tweet_id_counter = 1000
    
    def create_tweet(self, user_token, text):
        self.call_log.append(('create_tweet', user_token, text))
        
        if not self.should_succeed:
            from modules.twitter_api import TwitterAPIError
            raise TwitterAPIError("Mock Twitter API error")
        
        tweet_id = str(self.tweet_id_counter)
        self.tweet_id_counter += 1
        
        return {
            'data': {
                'id': tweet_id,
                'text': text
            }
        }
    
    def set_should_succeed(self, should_succeed):
        self.should_succeed = should_succeed

class MockUserProfileService:
    """Mock user profile service for testing"""
    
    def __init__(self):
        self.access_tokens = {}
        self.call_log = []
    
    def get_twitter_access_token(self, user_id):
        self.call_log.append(('get_twitter_access_token', user_id))
        return self.access_tokens.get(user_id, 'mock_token_' + user_id)
    
    def set_access_token(self, user_id, token):
        self.access_tokens[user_id] = token

class MockAnalyticsCollector:
    """Mock analytics collector for testing"""
    
    def __init__(self):
        self.events = []
        self.call_log = []
    
    async def record_event(self, event_data):
        self.call_log.append(('record_event', event_data))
        self.events.append(event_data)

class MockContentDraft:
    """Mock content draft object"""
    
    def __init__(self, id, founder_id, status='approved', 
                 generated_text='Test content', current_content=None):
        self.id = id
        self.founder_id = founder_id
        self.status = status
        self.generated_text = generated_text
        self.current_content = current_content
        self.content_type = 'twitter_post'
        self.created_at = datetime.utcnow()
        self.quality_score = 0.8
        self.tags = ['test']

class MockScheduledContent:
    """Mock scheduled content object"""
    
    def __init__(self, data):
        # Unified approach: scheduled_id == content_draft_id
        self.id = data.get('id', str(uuid.uuid4()))
        if 'content_draft_id' in data:
            self.content_draft_id = data['content_draft_id']
            self.id = self.content_draft_id  # Unified tables
        else:
            self.content_draft_id = self.id
            
        self.founder_id = data['founder_id']
        self.scheduled_time = data['scheduled_time']
        self.scheduled_post_time = self.scheduled_time  # DB field name
        self.status = data.get('status', PublishStatus.SCHEDULED.value)
        self.retry_count = data.get('retry_count', 0)
        self.max_retries = data.get('max_retries', 3)
        self.posted_at = data.get('posted_at')
        self.posted_tweet_id = data.get('posted_tweet_id')
        self.error_info = data.get('error_info')
        
        # Additional fields from unified table
        self.content_type = data.get('content_type', 'tweet')
        self.generated_text = data.get('generated_text', 'Test content')
        self.platform = data.get('platform', 'twitter')
        self.priority = data.get('priority', 5)
        self.created_at = data.get('created_at', datetime.utcnow())
        self.updated_at = data.get('updated_at', datetime.utcnow())
        
    @property
    def final_text(self):
        """Get final text for compatibility"""
        return getattr(self, 'edited_text', None) or self.generated_text

# Fixtures
@pytest.fixture
def mock_data_flow_manager():
    """Create mock data flow manager"""
    return MockDataFlowManager()

@pytest.fixture
def mock_twitter_client():
    """Create mock Twitter client"""
    return MockTwitterClient()

@pytest.fixture
def mock_user_profile_service():
    """Create mock user profile service"""
    return MockUserProfileService()

@pytest.fixture
def mock_analytics_collector():
    """Create mock analytics collector"""
    return MockAnalyticsCollector()

@pytest.fixture
def scheduling_service(mock_data_flow_manager, mock_twitter_client, 
                      mock_user_profile_service, mock_analytics_collector):
    """Create scheduling posting service with mocks"""
    return SchedulingPostingService(
        data_flow_manager=mock_data_flow_manager,
        twitter_client=mock_twitter_client,
        user_profile_service=mock_user_profile_service,
        analytics_collector=mock_analytics_collector
    )

@pytest.fixture
def rules_engine(mock_data_flow_manager):
    """Create rules engine with mock data flow manager"""
    return InternalRulesEngine(mock_data_flow_manager)

@pytest.fixture
def test_user_id():
    """Test user ID"""
    return "test_user_123"

@pytest.fixture
def test_content_id():
    """Test content ID"""
    return "test_content_456"

@pytest.fixture
def test_content_draft(test_content_id, test_user_id):
    """Create test content draft"""
    return MockContentDraft(
        id=test_content_id,
        founder_id=test_user_id,
        status='approved',
        generated_text='This is a test tweet content'
    )

@pytest.fixture
def valid_schedule_request(test_content_id):
    """Create valid schedule request"""
    return ScheduleRequest(
        content_id=test_content_id,
        scheduled_time=datetime.utcnow() + timedelta(hours=1),
        timezone="UTC",
        priority=5
    )

@pytest.fixture
def valid_publish_request(test_content_id):
    """Create valid publish request"""
    return PublishRequest(
        content_id=test_content_id,
        force_publish=False,
        skip_rules_check=False
    )

@pytest.fixture
def test_scheduling_preferences(test_user_id):
    """Create test scheduling preferences"""
    return SchedulingPreferences(
        founder_id=test_user_id,
        default_timezone="UTC",
        auto_schedule_enabled=True,
        preferred_posting_times=["09:00", "13:00", "17:00"],
        max_posts_per_day=5,
        min_interval_minutes=60,
        avoid_weekends=False,
        quiet_hours_start="22:00",
        quiet_hours_end="08:00"
    )

@pytest.fixture
def setup_test_data(mock_data_flow_manager, test_content_draft, 
                   test_scheduling_preferences, test_user_id):
    """Setup test data in mock objects"""
    # Add content draft
    mock_data_flow_manager.content_drafts[test_content_draft.id] = test_content_draft
    
    # Add user preferences
    mock_data_flow_manager.user_preferences[test_user_id] = test_scheduling_preferences.dict()
    
    return mock_data_flow_manager

# Utility functions for tests
def create_content_drafts(mock_data_flow_manager, user_id, count=5):
    """Create multiple content drafts for testing"""
    drafts = []
    for i in range(count):
        draft_id = f"content_{i}_{uuid.uuid4().hex[:8]}"
        draft = MockContentDraft(
            id=draft_id,
            founder_id=user_id,
            status='approved',
            generated_text=f'Test content {i+1}'
        )
        mock_data_flow_manager.content_drafts[draft_id] = draft
        drafts.append(draft)
    return drafts

def create_scheduled_content(mock_data_flow_manager, user_id, draft_id, 
                           scheduled_time=None, status=PublishStatus.SCHEDULED):
    """
    Create scheduled content for testing
    
    Note: Since scheduled_content table is unified with content_drafts,
    this now updates the existing content draft with scheduling information.
    """
    if not scheduled_time:
        scheduled_time = datetime.utcnow() + timedelta(hours=1)
    
    scheduled_data = {
        'content_draft_id': draft_id,
        'founder_id': user_id,
        'scheduled_time': scheduled_time,
        'status': status.value,
        'retry_count': 0,
        'platform': 'twitter',
        'priority': 5
    }
    
    # This now updates the content draft instead of creating separate scheduled content
    scheduled_id = mock_data_flow_manager.create_scheduled_content(scheduled_data)
    return scheduled_id  # Returns content_draft_id since tables are unified

async def wait_for_condition(condition_func, timeout=5.0, interval=0.1):
    """Wait for a condition to become true"""
    start_time = datetime.utcnow()
    while (datetime.utcnow() - start_time).total_seconds() < timeout:
        if await condition_func() if asyncio.iscoroutinefunction(condition_func) else condition_func():
            return True
        await asyncio.sleep(interval)
    return False 