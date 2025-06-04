"""API endpoints for review optimization"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from flask import request
import jwt
import os
import logging

from ...review_optimization.models import (
    ReviewItem, ReviewStatus, ReviewAction, ReviewFeedback,
    ReviewStatistics, ReviewFilterRequest, ReviewBatchRequest
)
from ...review_optimization.service import ReviewOptimizationService
from ...database import get_db_session
from modules.user_profile import UserProfileService, UserProfileRepository
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

router = APIRouter(prefix="/api/review", tags=["review"])

# database config
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/ideation_db')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_user_service() -> UserProfileService:
    """Get user service instance"""
    db_session = SessionLocal()
    repository = UserProfileRepository(db_session)
    return UserProfileService(repository)

def verify_jwt_token(token: str) -> dict:
    """Validate JWT token"""
    try:
        secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return {'error': 'Token has expired'}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token'}

class CurrentUser:
    """Current user information class"""
    def __init__(self, user_id: str, email: str = None, username: str = None):
        self.id = user_id
        self.email = email
        self.username = username

def get_current_user_with_profile() -> Optional[CurrentUser]:
    """Get current user (with complete profile information)"""
    try:
        # first validate the token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header[7:]
        payload = verify_jwt_token(token)
        if 'error' in payload:
            return None
        
        user_id = payload.get('user_id')
        if not user_id:
            return None
        
        # Get user info from database
        try:
            user_service = get_user_service()
            user_profile = user_service.get_user_profile(user_id)
            
            if user_profile:
                return CurrentUser(
                    user_id=user_id,
                    email=user_profile.email,
                    username=user_profile.username or user_profile.email.split('@')[0]
                )
            else:
                # user exists in token but not found in database, use basic info
                return CurrentUser(
                    user_id=user_id,
                    email=payload.get('email'),
                    username=payload.get('username')
                )
                
        except Exception as db_error:
            logging.warning(f"Failed to get user profile from database: {db_error}")
            # fallback to token info
            return CurrentUser(
                user_id=user_id,
                email=payload.get('email'),
                username=payload.get('username')
            )
        
    except Exception as e:
        logging.error(f"Error getting current user with profile: {e}")
        return None

def get_review_service(db_session = Depends(get_db_session)) -> ReviewOptimizationService:
    """Dependency to get review service"""
    from ...review_optimization.repository import ReviewOptimizationRepository
    return ReviewOptimizationService(
        repository=ReviewOptimizationRepository(db_session),
        content_service=None,  # Would be injected
        scheduling_service=None  # Would be injected
    )

@router.post("/items/create-from-draft/{draft_id}")
async def create_review_item(
    draft_id: str,
    current_user = Depends(get_current_user_with_profile),
    service: ReviewOptimizationService = Depends(get_review_service)
):
    """Create review item from content draft"""
    item_id = service.create_review_item_from_draft(draft_id, current_user.id)
    if not item_id:
        raise HTTPException(status_code=400, detail="Failed to create review item")
    
    return {"item_id": item_id, "message": "Review item created successfully"}

@router.get("/queue", response_model=List[ReviewItem])
async def get_review_queue(
    status: Optional[ReviewStatus] = None,
    content_type: Optional[str] = None,
    priority_min: Optional[int] = Query(None, ge=1, le=10),
    priority_max: Optional[int] = Query(None, ge=1, le=10),
    ai_confidence_min: Optional[float] = Query(None, ge=0, le=1),
    ai_confidence_max: Optional[float] = Query(None, ge=0, le=1),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_user_with_profile),
    service: ReviewOptimizationService = Depends(get_review_service)
):
    """Get review queue with filtering"""
    filter_request = ReviewFilterRequest(
        status=status,
        content_type=content_type,
        priority_min=priority_min,
        priority_max=priority_max,
        ai_confidence_min=ai_confidence_min,
        ai_confidence_max=ai_confidence_max,
        limit=limit,
        offset=offset
    )
    
    return service.get_review_queue(current_user.id, filter_request)

@router.get("/items/{item_id}", response_model=ReviewItem)
async def get_review_item(
    item_id: str,
    current_user = Depends(get_current_user_with_profile),
    service: ReviewOptimizationService = Depends(get_review_service)
):
    """Get specific review item"""
    item = service.get_review_item(item_id, current_user.id)
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
    
    return item

@router.put("/items/{item_id}/content")
async def update_content(
    item_id: str,
    content: str,
    current_user = Depends(get_current_user_with_profile),
    service: ReviewOptimizationService = Depends(get_review_service)
):
    """Update content of review item"""
    success = service.update_content(item_id, current_user.id, content, current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update content")
    
    return {"message": "Content updated successfully"}

@router.put("/items/{item_id}/seo")
async def update_seo_elements(
    item_id: str,
    hashtags: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    current_user = Depends(get_current_user_with_profile),
    service: ReviewOptimizationService = Depends(get_review_service)
):
    """Update SEO elements of review item"""
    success = service.update_seo_elements(
        item_id, current_user.id, hashtags, keywords, current_user.id
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update SEO elements")
    
    return {"message": "SEO elements updated successfully"}

@router.post("/items/{item_id}/action")
async def perform_review_action(
    item_id: str,
    action: ReviewAction,
    feedback: Optional[ReviewFeedback] = None,
    scheduled_time: Optional[datetime] = None,
    current_user = Depends(get_current_user_with_profile),
    service: ReviewOptimizationService = Depends(get_review_service)
):
    """Perform review action on item"""
    success, message = service.perform_action(
        item_id, current_user.id, action, feedback, scheduled_time, current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message}

@router.post("/batch")
async def batch_review(
    batch_request: ReviewBatchRequest,
    current_user = Depends(get_current_user_with_profile),
    service: ReviewOptimizationService = Depends(get_review_service)
):
    """Perform batch review operations"""
    results = service.batch_review(batch_request, current_user.id, current_user.id)
    return results

@router.get("/statistics", response_model=ReviewStatistics)
async def get_review_statistics(
    days: int = Query(30, ge=1, le=365),
    current_user = Depends(get_current_user_with_profile),
    service: ReviewOptimizationService = Depends(get_review_service)
):
    """Get review statistics"""
    return service.get_review_statistics(current_user.id, days)