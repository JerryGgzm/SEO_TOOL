"""Test cases for analytics API endpoints"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import json
from api import create_app
from database.models import PostAnalytic

# Test data
MOCK_USER_ID = "test_user_123"
MOCK_TWEET_ID = "tweet_123"
MOCK_ANALYTICS_DATA = {
    "impressions": 1000,
    "likes": 50,
    "retweets": 30,
    "replies": 20,
    "quote_tweets": 10,
    "engagement_rate": 0.1,
    "link_clicks": 100,
    "profile_visits_from_tweet": 200,
    "posted_at": datetime.now().isoformat(),
    "last_updated_at": datetime.now().isoformat()
}

@pytest.fixture
def app():
    """Create test Flask app"""
    app = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def mock_db_session():
    """Mock database session"""
    with patch('api.routes.analytics.get_db_context') as mock:
        session = Mock()
        mock.return_value.__enter__.return_value = session
        yield session

@pytest.fixture
def mock_post_analytics():
    """Create mock PostAnalytic object"""
    analytics = Mock(spec=PostAnalytic)
    analytics.posted_tweet_id = MOCK_TWEET_ID
    analytics.founder_id = MOCK_USER_ID
    analytics.impressions = MOCK_ANALYTICS_DATA["impressions"]
    analytics.likes = MOCK_ANALYTICS_DATA["likes"]
    analytics.retweets = MOCK_ANALYTICS_DATA["retweets"]
    analytics.replies = MOCK_ANALYTICS_DATA["replies"]
    analytics.quote_tweets = MOCK_ANALYTICS_DATA["quote_tweets"]
    analytics.engagement_rate = MOCK_ANALYTICS_DATA["engagement_rate"]
    analytics.link_clicks = MOCK_ANALYTICS_DATA["link_clicks"]
    analytics.profile_visits_from_tweet = MOCK_ANALYTICS_DATA["profile_visits_from_tweet"]
    analytics.posted_at = datetime.fromisoformat(MOCK_ANALYTICS_DATA["posted_at"])
    analytics.last_updated_at = datetime.fromisoformat(MOCK_ANALYTICS_DATA["last_updated_at"])
    
    # Mock total_engagements property
    analytics.total_engagements = (
        analytics.likes + 
        analytics.retweets + 
        analytics.replies + 
        analytics.quote_tweets
    )
    
    return analytics

class TestAnalyticsDashboard:
    """Test analytics dashboard endpoints"""
    
    def test_get_dashboard_7d(self, client, mock_db_session, mock_post_analytics):
        """Test getting dashboard data for last 7 days"""
        # Setup mock data
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_post_analytics]
        
        # Make request
        response = client.get(
            f'/api/analytics/dashboard/{MOCK_USER_ID}',
            query_string={'date_range': '7d'},
            headers={'Authorization': 'Bearer test_token'}
        )
        
        # Assert response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'data' in data
        assert data['data']['total_impressions'] == MOCK_ANALYTICS_DATA['impressions']
        assert data['data']['total_engagements'] == mock_post_analytics.total_engagements
        assert data['data']['average_engagement_rate'] == MOCK_ANALYTICS_DATA['engagement_rate']
        assert data['data']['posts_analyzed'] == 1
    
    def test_get_dashboard_custom_date_range(self, client, mock_db_session, mock_post_analytics):
        """Test getting dashboard data with custom date range"""
        # Setup mock data
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_post_analytics]
        
        # Make request
        response = client.get(
            f'/api/analytics/dashboard/{MOCK_USER_ID}',
            query_string={
                'date_range': 'custom',
                'start_date': '2024-01-01',
                'end_date': '2024-01-31'
            },
            headers={'Authorization': 'Bearer test_token'}
        )
        
        # Assert response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'data' in data
    
    def test_get_dashboard_missing_auth(self, client):
        """Test getting dashboard data without authentication"""
        response = client.get(f'/api/analytics/dashboard/{MOCK_USER_ID}')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data

class TestPostAnalytics:
    """Test post analytics endpoints"""
    
    def test_get_post_analytics(self, client, mock_db_session, mock_post_analytics):
        """Test getting single post analytics"""
        # Setup mock data
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_post_analytics
        
        # Make request
        response = client.get(
            f'/api/analytics/posts/{MOCK_TWEET_ID}',
            headers={'Authorization': 'Bearer test_token'}
        )
        
        # Assert response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['data']['tweet_id'] == MOCK_TWEET_ID
        assert data['data']['impressions'] == MOCK_ANALYTICS_DATA['impressions']
    
    def test_get_post_analytics_not_found(self, client, mock_db_session):
        """Test getting non-existent post analytics"""
        # Setup mock data
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Make request
        response = client.get(
            f'/api/analytics/posts/{MOCK_TWEET_ID}',
            headers={'Authorization': 'Bearer test_token'}
        )
        
        # Assert response
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data

class TestUserPostsAnalytics:
    """Test user posts analytics endpoints"""
    
    def test_get_user_posts_analytics(self, client, mock_db_session, mock_post_analytics):
        """Test getting all user's posts analytics"""
        # Setup mock data
        mock_db_session.query.return_value.filter.return_value.count.return_value = 1
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_post_analytics]
        
        # Make request
        response = client.get(
            '/api/analytics/posts',
            query_string={
                'user_id': MOCK_USER_ID,
                'limit': 20,
                'offset': 0,
                'sort_by': 'date'
            },
            headers={'Authorization': 'Bearer test_token'}
        )
        
        # Assert response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['data']['total'] == 1
        assert len(data['data']['posts']) == 1
        assert data['data']['posts'][0]['tweet_id'] == MOCK_TWEET_ID
    
    def test_get_user_posts_analytics_missing_user_id(self, client):
        """Test getting posts analytics without user_id"""
        response = client.get(
            '/api/analytics/posts',
            headers={'Authorization': 'Bearer test_token'}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

class TestAnalyticsCollection:
    """Test analytics collection endpoints"""
    
    def test_collect_tweet_analytics(self, client):
        """Test collecting single tweet analytics"""
        response = client.post(
            f'/api/analytics/collect/{MOCK_TWEET_ID}',
            headers={'Authorization': 'Bearer test_token'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['data']['status'] == 'collection_started'
        assert data['data']['tweet_id'] == MOCK_TWEET_ID
    
    def test_collect_batch_analytics(self, client):
        """Test collecting batch analytics"""
        response = client.post(
            '/api/analytics/collect/batch',
            json={'tweet_ids': [MOCK_TWEET_ID, 'tweet_456']},
            headers={'Authorization': 'Bearer test_token'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['data']['status'] == 'batch_collection_started'
        assert len(data['data']['tweet_ids']) == 2
    
    def test_collect_batch_analytics_missing_tweet_ids(self, client):
        """Test collecting batch analytics without tweet_ids"""
        response = client.post(
            '/api/analytics/collect/batch',
            json={},
            headers={'Authorization': 'Bearer test_token'}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

class TestAnalyticsOverview:
    """Test analytics overview endpoints"""
    
    def test_get_analytics_overview_daily(self, client, mock_db_session, mock_post_analytics):
        """Test getting daily analytics overview"""
        # Setup mock data
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_post_analytics]
        
        # Make request
        response = client.get(
            f'/api/analytics/overview/{MOCK_USER_ID}',
            query_string={'period': 'daily'},
            headers={'Authorization': 'Bearer test_token'}
        )
        
        # Assert response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['data']['period'] == 'daily'
        assert data['data']['total_posts'] == 1
        assert data['data']['total_impressions'] == MOCK_ANALYTICS_DATA['impressions']
    
    def test_get_analytics_overview_invalid_period(self, client):
        """Test getting analytics overview with invalid period"""
        response = client.get(
            f'/api/analytics/overview/{MOCK_USER_ID}',
            query_string={'period': 'invalid'},
            headers={'Authorization': 'Bearer test_token'}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data 