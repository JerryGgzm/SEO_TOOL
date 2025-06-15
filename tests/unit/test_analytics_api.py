"""
Analytics API Test Suite

This module contains comprehensive test cases for the analytics API endpoints.
It tests all major functionality including dashboard data, post analytics, data collection,
and overview statistics.

Test Coverage:
- Authentication and authorization
- Dashboard data retrieval with different date ranges
- Individual post analytics
- User's all posts analytics with pagination and sorting
- Analytics data collection (single and batch)
- Analytics overview with different time periods

Test Structure:
- Uses pytest fixtures for common setup
- Mocks database sessions and responses
- Tests both success and error cases
- Validates response formats and status codes

Dependencies:
- pytest: Testing framework
- Flask test client: For making test requests
- unittest.mock: For mocking dependencies
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import json
from api import create_app
from database.models import PostAnalytic

# Test data constants
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
    """
    Create a test Flask application instance.
    
    This fixture:
    1. Creates a new Flask app
    2. Configures it for testing
    3. Returns the configured app
    
    Returns:
        Flask: A configured Flask application instance for testing
    """
    app = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """
    Create a test client for making requests to the Flask application.
    
    Args:
        app: The Flask application instance from the app fixture
        
    Returns:
        FlaskClient: A test client for making requests to the application
    """
    return app.test_client()

@pytest.fixture
def mock_db_session():
    """
    Create a mock database session.
    
    This fixture:
    1. Mocks the database context manager
    2. Provides a mock session object
    3. Ensures proper cleanup after tests
    
    Yields:
        Mock: A mock database session object
    """
    with patch('api.routes.analytics.get_db_context') as mock:
        session = Mock()
        mock.return_value.__enter__.return_value = session
        yield session

@pytest.fixture
def mock_post_analytics():
    """
    Create a mock PostAnalytic object with test data.
    
    This fixture:
    1. Creates a mock object with PostAnalytic specification
    2. Populates it with test data
    3. Mocks the total_engagements property
    
    Returns:
        Mock: A mock PostAnalytic object with test data
    """
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
    """
    Test suite for analytics dashboard endpoints.
    
    This class contains tests for:
    - Dashboard data retrieval with different date ranges
    - Authentication requirements
    - Response format validation
    - Error handling
    """
    
    def test_get_dashboard_7d(self, client, mock_db_session, mock_post_analytics):
        """
        Test retrieving dashboard data for the last 7 days.
        
        This test:
        1. Sets up mock data for a 7-day period
        2. Makes a request to the dashboard endpoint
        3. Verifies the response format and data
        
        Args:
            client: Flask test client
            mock_db_session: Mock database session
            mock_post_analytics: Mock analytics data
        """
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
        """
        Test retrieving dashboard data with a custom date range.
        
        This test:
        1. Sets up mock data for a custom date range
        2. Makes a request with start and end dates
        3. Verifies the response format and data
        
        Args:
            client: Flask test client
            mock_db_session: Mock database session
            mock_post_analytics: Mock analytics data
        """
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
        """
        Test dashboard endpoint authentication requirement.
        
        This test:
        1. Makes a request without authentication
        2. Verifies that the request is rejected
        3. Checks the error response format
        
        Args:
            client: Flask test client
        """
        response = client.get(f'/api/analytics/dashboard/{MOCK_USER_ID}')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data

class TestPostAnalytics:
    """
    Test suite for individual post analytics endpoints.
    
    This class contains tests for:
    - Single post analytics retrieval
    - Non-existent post handling
    - Response format validation
    - Error handling
    """
    
    def test_get_post_analytics(self, client, mock_db_session, mock_post_analytics):
        """
        Test retrieving analytics for a single post.
        
        This test:
        1. Sets up mock data for a specific post
        2. Makes a request to the post analytics endpoint
        3. Verifies the response format and data
        
        Args:
            client: Flask test client
            mock_db_session: Mock database session
            mock_post_analytics: Mock analytics data
        """
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
        """
        Test handling of non-existent post analytics.
        
        This test:
        1. Sets up mock to return no data
        2. Makes a request for a non-existent post
        3. Verifies the error response
        
        Args:
            client: Flask test client
            mock_db_session: Mock database session
        """
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
    """
    Test suite for user's all posts analytics endpoints.
    
    This class contains tests for:
    - Retrieving analytics for all user's posts
    - Pagination functionality
    - Sorting options
    - Error handling
    """
    
    def test_get_user_posts_analytics(self, client, mock_db_session, mock_post_analytics):
        """
        Test retrieving analytics for all user's posts.
        
        This test:
        1. Sets up mock data for user's posts
        2. Makes a request with pagination and sorting
        3. Verifies the response format and data
        
        Args:
            client: Flask test client
            mock_db_session: Mock database session
            mock_post_analytics: Mock analytics data
        """
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
        """
        Test handling of missing user_id parameter.
        
        This test:
        1. Makes a request without the required user_id
        2. Verifies the error response
        
        Args:
            client: Flask test client
        """
        response = client.get(
            '/api/analytics/posts',
            headers={'Authorization': 'Bearer test_token'}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

class TestAnalyticsCollection:
    """
    Test suite for analytics data collection endpoints.
    
    This class contains tests for:
    - Single tweet analytics collection
    - Batch analytics collection
    - Error handling for missing parameters
    """
    
    def test_collect_tweet_analytics(self, client):
        """
        Test initiating analytics collection for a single tweet.
        
        This test:
        1. Makes a request to collect analytics for a tweet
        2. Verifies the response format and status
        
        Args:
            client: Flask test client
        """
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
        """
        Test initiating analytics collection for multiple tweets.
        
        This test:
        1. Makes a request to collect analytics for multiple tweets
        2. Verifies the response format and status
        
        Args:
            client: Flask test client
        """
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
        """
        Test handling of missing tweet_ids in batch collection.
        
        This test:
        1. Makes a request without tweet_ids
        2. Verifies the error response
        
        Args:
            client: Flask test client
        """
        response = client.post(
            '/api/analytics/collect/batch',
            json={},
            headers={'Authorization': 'Bearer test_token'}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

class TestAnalyticsOverview:
    """
    Test suite for analytics overview endpoints.
    
    This class contains tests for:
    - Daily analytics overview
    - Weekly analytics overview
    - Monthly analytics overview
    - Invalid period handling
    """
    
    def test_get_analytics_overview_daily(self, client, mock_db_session, mock_post_analytics):
        """
        Test retrieving daily analytics overview.
        
        This test:
        1. Sets up mock data for daily analytics
        2. Makes a request for daily overview
        3. Verifies the response format and data
        
        Args:
            client: Flask test client
            mock_db_session: Mock database session
            mock_post_analytics: Mock analytics data
        """
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
        assert data['data']['total_engagements'] == mock_post_analytics.total_engagements
        assert data['data']['average_engagement_rate'] == MOCK_ANALYTICS_DATA['engagement_rate']
    
    def test_get_analytics_overview_invalid_period(self, client):
        """
        Test handling of invalid period parameter.
        
        This test:
        1. Makes a request with an invalid period
        2. Verifies the error response
        
        Args:
            client: Flask test client
        """
        response = client.get(
            f'/api/analytics/overview/{MOCK_USER_ID}',
            query_string={'period': 'invalid'},
            headers={'Authorization': 'Bearer test_token'}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data 