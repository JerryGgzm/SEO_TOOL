"""Test cases for analytics module"""
import pytest
from flask import Flask, g
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import json
import jwt

from api.main import app
from modules.analytics import AnalyticsDashboard, AnalyticsCollector, ContentPerformanceAnalyzer
from database import DataFlowManager
from api.middleware import get_current_user, get_analytics_dashboard, get_analytics_collector, get_content_analyzer, inject_user, SECRET_KEY, ALGORITHM

# Test data
MOCK_USER_ID = "test_user_123"
MOCK_TWEET_ID = "tweet_123"
MOCK_ANALYTICS_DATA = {
    "impressions": 1000,
    "engagements": 100,
    "likes": 50,
    "retweets": 30,
    "replies": 20,
    "engagement_rate": 0.1
}

def create_test_token(user_id: str) -> str:
    """Create a test JWT token"""
    payload = {
        "sub": f"test_user_{user_id}@example.com",
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# Fixtures
@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    return app.test_client()

@pytest.fixture
def mock_current_user():
    """Mock current user"""
    return Mock(id=MOCK_USER_ID)

@pytest.fixture
def auth_headers():
    """Create authentication headers"""
    token = create_test_token(MOCK_USER_ID)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def mock_analytics_dashboard():
    """Mock analytics dashboard"""
    dashboard = Mock(spec=AnalyticsDashboard)
    dashboard.get_dashboard_data.return_value = {
        "real_time_metrics": {
            "today_posts": 5,
            "week_posts": 20,
            "pending_review": 3,
            "scheduled_posts": 2
        },
        "quick_analysis": {
            "overall_score": 85,
            "key_insights": ["Good engagement", "High reach"],
            "urgent_actions": ["Optimize timing"]
        }
    }
    return dashboard

@pytest.fixture
def mock_analytics_collector():
    """Mock analytics collector"""
    collector = Mock(spec=AnalyticsCollector)
    collector.get_detailed_tweet_analytics.return_value = MOCK_ANALYTICS_DATA
    return collector

@pytest.fixture
def mock_content_analyzer():
    """Mock content analyzer"""
    analyzer = Mock(spec=ContentPerformanceAnalyzer)
    analyzer._get_content_analytics.return_value = MOCK_ANALYTICS_DATA
    return analyzer

# Test cases
class TestAnalyticsDashboard:
    """Test analytics dashboard endpoints"""
    
    def test_get_dashboard(self, client, mock_current_user, mock_analytics_dashboard, auth_headers):
        """Test getting dashboard data"""
        with patch('api.middleware.get_current_user', return_value=mock_current_user), \
             patch('api.middleware.get_analytics_dashboard', return_value=mock_analytics_dashboard):
            with client:
                client.get('/')  # Create request context
                g.user = mock_current_user
                response = client.get(
                    f"/api/analytics/dashboard/{MOCK_USER_ID}",
                    headers=auth_headers
                )
                assert response.status_code == 200
                data = response.get_json()
                assert data["status"] == "success"
                assert "real_time_metrics" in data["data"]
                assert "quick_analysis" in data["data"]

class TestPostAnalytics:
    """Test post analytics endpoints"""
    
    def test_get_post_analytics(self, client, mock_current_user, mock_content_analyzer, auth_headers):
        """Test getting single post analytics"""
        with patch('api.middleware.get_current_user', return_value=mock_current_user), \
             patch('api.middleware.get_content_analyzer', return_value=mock_content_analyzer):
            with client:
                client.get('/')  # Create request context
                g.user = mock_current_user
                response = client.get(
                    f"/api/analytics/posts/{MOCK_TWEET_ID}",
                    headers=auth_headers
                )
                assert response.status_code == 200
                data = response.get_json()
                assert data["status"] == "success"
                assert data["data"] == MOCK_ANALYTICS_DATA
    
    def test_get_posts_analytics(self, client, mock_current_user, auth_headers):
        """Test getting all posts analytics"""
        with patch('api.middleware.get_current_user', return_value=mock_current_user):
            with client:
                client.get('/')  # Create request context
                g.user = mock_current_user
                response = client.get(
                    f"/api/analytics/posts?user_id={MOCK_USER_ID}&limit=20&offset=0&sort_by=date",
                    headers=auth_headers
                )
                assert response.status_code == 200
                data = response.get_json()
                assert data["status"] == "success"
                assert "summary" in data["data"]
                assert "trends" in data["data"]
                assert "pagination" in data["data"]

class TestAnalyticsCollection:
    """Test analytics collection endpoints"""
    
    def test_collect_post_analytics(self, client, mock_current_user, mock_analytics_collector, auth_headers):
        """Test collecting single post analytics"""
        with patch('api.middleware.get_current_user', return_value=mock_current_user), \
             patch('api.middleware.get_analytics_collector', return_value=mock_analytics_collector):
            with client:
                client.get('/')  # Create request context
                g.user = mock_current_user
                response = client.post(
                    f"/api/analytics/collect/{MOCK_TWEET_ID}",
                    headers=auth_headers
                )
                assert response.status_code == 200
                data = response.get_json()
                assert data["status"] == "success"
                assert data["data"] == MOCK_ANALYTICS_DATA
    
    def test_collect_batch_analytics(self, client, mock_current_user, mock_analytics_collector, auth_headers):
        """Test collecting batch analytics"""
        with patch('api.middleware.get_current_user', return_value=mock_current_user), \
             patch('api.middleware.get_analytics_collector', return_value=mock_analytics_collector):
            with client:
                client.get('/')  # Create request context
                g.user = mock_current_user
                response = client.post(
                    "/api/analytics/collect/batch",
                    json={"tweet_ids": [MOCK_TWEET_ID, "tweet_456"]},
                    headers=auth_headers
                )
                assert response.status_code == 200
                data = response.get_json()
                assert data["status"] == "success"
                assert len(data["data"]) == 2

class TestAnalyticsOverview:
    """Test analytics overview endpoints"""
    
    def test_get_analytics_overview(self, client, mock_current_user, auth_headers):
        """Test getting analytics overview"""
        with patch('api.middleware.get_current_user', return_value=mock_current_user):
            with client:
                client.get('/')  # Create request context
                g.user = mock_current_user
                response = client.get(
                    f"/api/analytics/overview/{MOCK_USER_ID}?period=daily",
                    headers=auth_headers
                )
                assert response.status_code == 200
                data = response.get_json()
                assert data["status"] == "success"
                assert "data" in data
                assert data["period"] == "daily"

# Error cases
class TestAnalyticsErrors:
    """Test error cases"""
    
    def test_invalid_user_access(self, client):
        """Test accessing with invalid user"""
        response = client.get(f"/api/analytics/dashboard/invalid_user")
        assert response.status_code in [401, 403]
    
    def test_invalid_tweet_id(self, client, mock_current_user, auth_headers):
        """Test accessing invalid tweet"""
        with patch('api.middleware.get_current_user', return_value=mock_current_user):
            with client:
                client.get('/')  # Create request context
                g.user = mock_current_user
                response = client.get(
                    "/api/analytics/posts/invalid_tweet",
                    headers=auth_headers
                )
                assert response.status_code == 404
    
    def test_invalid_date_range(self, client, mock_current_user, auth_headers):
        """Test invalid date range"""
        with patch('api.middleware.get_current_user', return_value=mock_current_user):
            with client:
                client.get('/')  # Create request context
                g.user = mock_current_user
                response = client.get(
                    f"/api/analytics/dashboard/{MOCK_USER_ID}?date_range=invalid",
                    headers=auth_headers
                )
                assert response.status_code == 422 