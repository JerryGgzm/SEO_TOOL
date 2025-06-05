"""
API tests for review optimization endpoints
"""
import pytest
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from api.routes.review_optimization import router as review_router
from modules.review_optimization.models import (
    ReviewItem, ReviewStatus, ReviewAction, ReviewFeedback,
    ReviewBatchRequest
)


@pytest.fixture
def mock_current_user():
    """Mock current user"""
    user = Mock()
    user.id = "test_user_123"
    user.email = "test@example.com"
    user.username = "testuser"
    return user


@pytest.fixture
def mock_review_service():
    """Mock review service"""
    service = Mock()
    
    # Mock sample review item
    sample_item = ReviewItem(
        id="review_123",
        content_draft_id="draft_123",
        founder_id="test_user_123",
        content_type="tweet",
        original_content="Original content",
        current_content="Original content",
        generation_reason="trending_topic",
        ai_confidence_score=0.8,
        hashtags=["#test"],
        keywords=["test"]
    )
    
    service.create_review_item_from_draft.return_value = "review_123"
    service.get_review_queue.return_value = [sample_item]
    service.get_review_item.return_value = sample_item
    service.update_content.return_value = True
    service.update_seo_elements.return_value = True
    service.perform_action.return_value = (True, "Action completed successfully")
    service.batch_review.return_value = {
        "successful": ["review_123"],
        "failed": [],
        "total": 1
    }
    service.get_review_statistics.return_value = Mock(
        total_items=10,
        pending_items=3,
        approved_items=7,
        approval_rate=0.7
    )
    
    return service


@pytest.fixture
def app(mock_review_service, mock_current_user):
    """Create FastAPI test app"""
    app = FastAPI()
    app.include_router(review_router)
    
    # Override dependencies
    def override_get_current_user():
        return mock_current_user
    
    def override_get_review_service():
        return mock_review_service
    
    app.dependency_overrides[review_router.get_current_user_with_profile] = override_get_current_user
    app.dependency_overrides[review_router.get_review_service] = override_get_review_service
    
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


class TestReviewAPIEndpoints:
    """Test review API endpoints"""
    
    def test_create_review_item(self, client, mock_review_service):
        """Test creating review item from draft"""
        draft_id = "draft_123"
        
        response = client.post(f"/api/review/items/create-from-draft/{draft_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "item_id" in data
        assert data["message"] == "Review item created successfully"
        mock_review_service.create_review_item_from_draft.assert_called_once_with(
            draft_id, "test_user_123"
        )
    
    def test_create_review_item_failure(self, client, mock_review_service):
        """Test creating review item failure"""
        mock_review_service.create_review_item_from_draft.return_value = None
        
        response = client.post("/api/review/items/create-from-draft/nonexistent")
        
        assert response.status_code == 400
        data = response.json()
        assert "Failed to create review item" in data["detail"]
    
    def test_get_review_queue(self, client, mock_review_service):
        """Test getting review queue"""
        response = client.get("/api/review/queue")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == "review_123"
    
    def test_get_review_queue_with_filters(self, client, mock_review_service):
        """Test getting review queue with filters"""
        params = {
            "status": "pending",
            "content_type": "tweet",
            "priority_min": 5,
            "priority_max": 10,
            "ai_confidence_min": 0.7,
            "limit": 20,
            "offset": 0
        }
        
        response = client.get("/api/review/queue", params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Verify service was called with correct filter
        mock_review_service.get_review_queue.assert_called_once()
        call_args = mock_review_service.get_review_queue.call_args
        filter_request = call_args[0][1]  # Second argument is filter_request
        
        assert filter_request.status.value == "pending"
        assert filter_request.content_type == "tweet"
        assert filter_request.priority_min == 5
        assert filter_request.ai_confidence_min == 0.7
        assert filter_request.limit == 20
    
    def test_get_review_item(self, client, mock_review_service):
        """Test getting specific review item"""
        item_id = "review_123"
        
        response = client.get(f"/api/review/items/{item_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "review_123"
        assert data["content_type"] == "tweet"
        mock_review_service.get_review_item.assert_called_once_with(
            item_id, "test_user_123"
        )
    
    def test_get_review_item_not_found(self, client, mock_review_service):
        """Test getting non-existent review item"""
        mock_review_service.get_review_item.return_value = None
        
        response = client.get("/api/review/items/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert "Review item not found" in data["detail"]
    
    def test_update_content(self, client, mock_review_service):
        """Test updating content"""
        item_id = "review_123"
        new_content = "Updated content"
        
        response = client.put(
            f"/api/review/items/{item_id}/content",
            json={"content": new_content}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Content updated successfully"
        mock_review_service.update_content.assert_called_once_with(
            item_id, "test_user_123", new_content, "test_user_123"
        )
    
    def test_update_content_failure(self, client, mock_review_service):
        """Test updating content failure"""
        mock_review_service.update_content.return_value = False
        
        response = client.put(
            "/api/review/items/review_123/content",
            json={"content": "new content"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Failed to update content" in data["detail"]
    
    def test_update_seo_elements(self, client, mock_review_service):
        """Test updating SEO elements"""
        item_id = "review_123"
        hashtags = ["#new", "#hashtags"]
        keywords = ["new", "keywords"]
        
        response = client.put(
            f"/api/review/items/{item_id}/seo",
            json={
                "hashtags": hashtags,
                "keywords": keywords
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "SEO elements updated successfully"
        mock_review_service.update_seo_elements.assert_called_once_with(
            item_id, "test_user_123", hashtags, keywords, "test_user_123"
        )
    
    def test_perform_review_action_approve(self, client, mock_review_service):
        """Test performing approve action"""
        item_id = "review_123"
        action_data = {
            "action": "approve",
            "feedback": {
                "rating": 5,
                "comments": "Excellent content",
                "improvement_suggestions": []
            }
        }
        
        response = client.post(
            f"/api/review/items/{item_id}/action",
            json=action_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Action completed successfully" in data["message"]
        
        # Verify service call
        mock_review_service.perform_action.assert_called_once()
        call_args = mock_review_service.perform_action.call_args[0]
        assert call_args[0] == item_id  # item_id
        assert call_args[1] == "test_user_123"  # founder_id
        assert call_args[2] == ReviewAction.APPROVE  # action
    
    def test_perform_review_action_schedule(self, client, mock_review_service):
        """Test performing schedule action"""
        item_id = "review_123"
        scheduled_time = (datetime.utcnow() + timedelta(hours=2)).isoformat()
        
        action_data = {
            "action": "schedule",
            "scheduled_time": scheduled_time
        }
        
        response = client.post(
            f"/api/review/items/{item_id}/action",
            json=action_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Action completed successfully" in data["message"]
    
    def test_perform_review_action_failure(self, client, mock_review_service):
        """Test performing action failure"""
        mock_review_service.perform_action.return_value = (False, "Action failed")
        
        action_data = {"action": "approve"}
        
        response = client.post(
            "/api/review/items/review_123/action",
            json=action_data
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Action failed" in data["detail"]
    
    def test_batch_review(self, client, mock_review_service):
        """Test batch review operations"""
        batch_data = {
            "item_ids": ["review_123", "review_456"],
            "action": "approve",
            "feedback": {
                "rating": 4,
                "comments": "Batch approved"
            }
        }
        
        response = client.post("/api/review/batch", json=batch_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "successful" in data
        assert "failed" in data
        assert "total" in data
        
        # Verify service call
        mock_review_service.batch_review.assert_called_once()
        call_args = mock_review_service.batch_review.call_args[0]
        assert call_args[1] == "test_user_123"  # founder_id
        assert call_args[2] == "test_user_123"  # reviewer_id
    
    def test_get_review_statistics(self, client, mock_review_service):
        """Test getting review statistics"""
        response = client.get("/api/review/statistics?days=30")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_items" in data
        assert "pending_items" in data
        assert "approval_rate" in data
        
        mock_review_service.get_review_statistics.assert_called_once_with(
            "test_user_123", 30
        )
    
    def test_get_review_statistics_custom_days(self, client, mock_review_service):
        """Test getting review statistics with custom days"""
        response = client.get("/api/review/statistics?days=7")
        
        assert response.status_code == 200
        mock_review_service.get_review_statistics.assert_called_once_with(
            "test_user_123", 7
        )


class TestAuthenticationAndAuthorization:
    """Test authentication and authorization"""
    
    def test_missing_authentication(self):
        """Test endpoints without authentication"""
        app = FastAPI()
        app.include_router(review_router)
        client = TestClient(app)
        
        # This should fail because no user is authenticated
        response = client.get("/api/review/queue")
        # Note: The actual behavior depends on your auth implementation
        # You might get 401, 403, or 422 depending on how dependencies are handled
        assert response.status_code in [401, 403, 422]
    
    def test_invalid_user_access(self, client, mock_review_service):
        """Test accessing items from different user"""
        # Mock service to return None (access denied)
        mock_review_service.get_review_item.return_value = None
        
        response = client.get("/api/review/items/someone_else_item")
        
        assert response.status_code == 404
        data = response.json()
        assert "Review item not found" in data["detail"]


class TestRequestValidation:
    """Test request validation"""
    
    def test_invalid_action_type(self, client):
        """Test invalid action type"""
        action_data = {"action": "invalid_action"}
        
        response = client.post(
            "/api/review/items/review_123/action",
            json=action_data
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_batch_request(self, client):
        """Test invalid batch request"""
        batch_data = {
            "item_ids": [],  # Empty list should fail validation
            "action": "approve"
        }
        
        response = client.post("/api/review/batch", json=batch_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_filter_parameters(self, client):
        """Test invalid filter parameters"""
        params = {
            "priority_min": 11,  # Outside valid range (1-10)
            "limit": 300  # Outside valid range (1-200)
        }
        
        response = client.get("/api/review/queue", params=params)
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_statistics_days(self, client):
        """Test invalid days parameter for statistics"""
        response = client.get("/api/review/statistics?days=400")  # Outside valid range
        
        assert response.status_code == 422  # Validation error


class TestEdgeCases:
    """Test edge cases and error scenarios"""
    
    def test_empty_content_update(self, client, mock_review_service):
        """Test updating with empty content"""
        response = client.put(
            "/api/review/items/review_123/content",
            json={"content": ""}
        )
        
        # This should still succeed at API level, validation happens in service
        assert response.status_code in [200, 400]
    
    def test_very_long_content(self, client, mock_review_service):
        """Test updating with very long content"""
        long_content = "x" * 1000  # Very long content
        
        response = client.put(
            "/api/review/items/review_123/content",
            json={"content": long_content}
        )
        
        # Should succeed at API level
        assert response.status_code in [200, 400]
    
    def test_concurrent_updates(self, client, mock_review_service):
        """Test handling concurrent updates"""
        import threading
        import time
        
        results = []
        
        def update_content(content_suffix):
            response = client.put(
                "/api/review/items/review_123/content",
                json={"content": f"Updated content {content_suffix}"}
            )
            results.append(response.status_code)
        
        # Simulate concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_content, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
    
    def test_malformed_json(self, client):
        """Test malformed JSON request"""
        response = client.post(
            "/api/review/items/review_123/action",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # JSON decode error


if __name__ == "__main__":
    pytest.main(["-v", __file__])