"""Database operations for review optimization"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Text, JSON, Float, Integer, Boolean, Enum
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import json
import logging

from database import Base
from .models import (
    ReviewItem, ReviewStatus, ReviewFeedback, ContentEdit,
    ReviewStatistics, ReviewFilterRequest
)

logger = logging.getLogger(__name__)

class ReviewItemTable(Base):
    """Review item database table"""
    __tablename__ = 'review_items'
    
    id = Column(String(36), primary_key=True)
    content_draft_id = Column(String(36), nullable=False, index=True)
    founder_id = Column(String(36), nullable=False, index=True)
    
    # Content
    content_type = Column(String(50), nullable=False)
    original_content = Column(Text, nullable=False)
    current_content = Column(Text, nullable=False)
    
    # Context
    trend_context = Column(JSON, default={})
    generation_reason = Column(Text)
    ai_confidence_score = Column(Float, default=0.5)
    
    # SEO
    seo_suggestions = Column(JSON, default={})
    hashtags = Column(JSON, default=[])
    keywords = Column(JSON, default=[])
    
    # Review metadata
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING, index=True)
    review_priority = Column(Integer, default=5, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_at = Column(DateTime)
    reviewed_by = Column(String(36))
    
    # Edit history
    edit_history = Column(JSON, default=[])
    
    # Scheduling
    scheduled_time = Column(DateTime, index=True)
    
    # Feedback
    feedback = Column(JSON)

class ReviewOptimizationRepository:
    """Repository for review optimization operations"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    def create_review_item(self, item: ReviewItem) -> bool:
        """Create a new review item"""
        try:
            db_item = ReviewItemTable(
                id=item.id,
                content_draft_id=item.content_draft_id,
                founder_id=item.founder_id,
                content_type=item.content_type,
                original_content=item.original_content,
                current_content=item.current_content,
                trend_context=item.trend_context,
                generation_reason=item.generation_reason,
                ai_confidence_score=item.ai_confidence_score,
                seo_suggestions=item.seo_suggestions,
                hashtags=item.hashtags,
                keywords=item.keywords,
                status=item.status,
                review_priority=item.review_priority
            )
            
            self.db_session.add(db_item)
            self.db_session.commit()
            return True
            
        except IntegrityError:
            self.db_session.rollback()
            logger.error(f"Failed to create review item: {item.id}")
            return False
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error creating review item: {e}")
            return False
    
    def get_review_item(self, item_id: str) -> Optional[ReviewItem]:
        """Get review item by ID"""
        db_item = self.db_session.query(ReviewItemTable).filter(
            ReviewItemTable.id == item_id
        ).first()
        
        if not db_item:
            return None
        
        return self._db_to_model(db_item)
    
    def get_review_items(self, founder_id: str, 
                        filter_request: Optional[ReviewFilterRequest] = None) -> List[ReviewItem]:
        """Get review items with optional filtering"""
        query = self.db_session.query(ReviewItemTable).filter(
            ReviewItemTable.founder_id == founder_id
        )
        
        if filter_request:
            if filter_request.status:
                query = query.filter(ReviewItemTable.status == filter_request.status)
            
            if filter_request.content_type:
                query = query.filter(ReviewItemTable.content_type == filter_request.content_type)
            
            if filter_request.priority_min:
                query = query.filter(ReviewItemTable.review_priority >= filter_request.priority_min)
            
            if filter_request.priority_max:
                query = query.filter(ReviewItemTable.review_priority <= filter_request.priority_max)
            
            if filter_request.created_after:
                query = query.filter(ReviewItemTable.created_at >= filter_request.created_after)
            
            if filter_request.created_before:
                query = query.filter(ReviewItemTable.created_at <= filter_request.created_before)
            
            if filter_request.ai_confidence_min:
                query = query.filter(ReviewItemTable.ai_confidence_score >= filter_request.ai_confidence_min)
            
            if filter_request.ai_confidence_max:
                query = query.filter(ReviewItemTable.ai_confidence_score <= filter_request.ai_confidence_max)
            
            # Order by priority and creation time
            query = query.order_by(
                ReviewItemTable.review_priority.desc(),
                ReviewItemTable.created_at.asc()
            )
            
            # Apply pagination
            query = query.limit(filter_request.limit).offset(filter_request.offset)
        else:
            query = query.order_by(
                ReviewItemTable.review_priority.desc(),
                ReviewItemTable.created_at.asc()
            ).limit(50)
        
        items = query.all()
        return [self._db_to_model(item) for item in items]
    
    def update_review_item(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """Update review item"""
        try:
            db_item = self.db_session.query(ReviewItemTable).filter(
                ReviewItemTable.id == item_id
            ).first()
            
            if not db_item:
                return False
            
            # Update fields
            for field, value in updates.items():
                if hasattr(db_item, field):
                    setattr(db_item, field, value)
            
            db_item.updated_at = datetime.utcnow()
            
            self.db_session.commit()
            return True
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error updating review item: {e}")
            return False
    
    def add_edit_history(self, item_id: str, edit: ContentEdit) -> bool:
        """Add edit to item history"""
        try:
            db_item = self.db_session.query(ReviewItemTable).filter(
                ReviewItemTable.id == item_id
            ).first()
            
            if not db_item:
                return False
            
            # Get current history
            edit_history = db_item.edit_history or []
            edit_history.append(edit.dict())
            
            db_item.edit_history = edit_history
            db_item.current_content = edit.new_value if edit.field == 'content' else db_item.current_content
            db_item.updated_at = datetime.utcnow()
            
            self.db_session.commit()
            return True
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error adding edit history: {e}")
            return False
    
    def get_review_statistics(self, founder_id: str, days: int = 30) -> ReviewStatistics:
        """Get review statistics for founder"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Get all items in time period
            items = self.db_session.query(ReviewItemTable).filter(
                ReviewItemTable.founder_id == founder_id,
                ReviewItemTable.created_at >= since_date
            ).all()
            
            if not items:
                return ReviewStatistics(time_period_days=days)
            
            # Calculate statistics
            total_items = len(items)
            pending_items = sum(1 for item in items if item.status == ReviewStatus.PENDING)
            approved_items = sum(1 for item in items if item.status == ReviewStatus.APPROVED)
            rejected_items = sum(1 for item in items if item.status == ReviewStatus.REJECTED)
            
            # Calculate average review time
            review_times = []
            for item in items:
                if item.reviewed_at and item.created_at:
                    review_time = (item.reviewed_at - item.created_at).total_seconds() / 60
                    review_times.append(review_time)
            
            avg_review_time = sum(review_times) / len(review_times) if review_times else 0
            
            # Calculate average AI confidence
            ai_scores = [item.ai_confidence_score for item in items if item.ai_confidence_score]
            avg_ai_confidence = sum(ai_scores) / len(ai_scores) if ai_scores else 0
            
            # Calculate average feedback rating
            ratings = []
            for item in items:
                if item.feedback and 'rating' in item.feedback:
                    ratings.append(item.feedback['rating'])
            
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            
            # Calculate rates
            approval_rate = (approved_items / total_items) if total_items > 0 else 0
            edited_items = sum(1 for item in items if item.edit_history)
            edit_rate = (edited_items / total_items) if total_items > 0 else 0
            
            # Get top rejection reasons (simplified)
            rejection_reasons = []
            for item in items:
                if item.status == ReviewStatus.REJECTED and item.feedback:
                    if 'comments' in item.feedback:
                        rejection_reasons.append(item.feedback['comments'])
            
            # Count edit types
            edit_types = {}
            for item in items:
                if item.edit_history:
                    for edit in item.edit_history:
                        field = edit.get('field', 'unknown')
                        edit_types[field] = edit_types.get(field, 0) + 1
            
            top_edit_types = sorted(edit_types.keys(), key=lambda x: edit_types[x], reverse=True)[:5]
            
            return ReviewStatistics(
                total_items=total_items,
                pending_items=pending_items,
                approved_items=approved_items,
                rejected_items=rejected_items,
                avg_review_time_minutes=round(avg_review_time, 2),
                avg_ai_confidence=round(avg_ai_confidence, 3),
                avg_feedback_rating=round(avg_rating, 2),
                approval_rate=round(approval_rate, 3),
                edit_rate=round(edit_rate, 3),
                top_rejection_reasons=rejection_reasons[:5],
                top_edit_types=top_edit_types,
                time_period_days=days
            )
            
        except Exception as e:
            logger.error(f"Error calculating review statistics: {e}")
            return ReviewStatistics(time_period_days=days)
    
    def _db_to_model(self, db_item: ReviewItemTable) -> ReviewItem:
        """Convert database item to model"""
        feedback = None
        if db_item.feedback:
            feedback = ReviewFeedback(**db_item.feedback)
        
        edit_history = []
        if db_item.edit_history:
            for edit_data in db_item.edit_history:
                edit_history.append(ContentEdit(**edit_data))
        
        return ReviewItem(
            id=db_item.id,
            content_draft_id=db_item.content_draft_id,
            founder_id=db_item.founder_id,
            content_type=db_item.content_type,
            original_content=db_item.original_content,
            current_content=db_item.current_content,
            trend_context=db_item.trend_context or {},
            generation_reason=db_item.generation_reason,
            ai_confidence_score=db_item.ai_confidence_score,
            seo_suggestions=db_item.seo_suggestions or {},
            hashtags=db_item.hashtags or [],
            keywords=db_item.keywords or [],
            status=db_item.status,
            review_priority=db_item.review_priority,
            created_at=db_item.created_at,
            updated_at=db_item.updated_at,
            reviewed_at=db_item.reviewed_at,
            reviewed_by=db_item.reviewed_by,
            edit_history=edit_history,
            scheduled_time=db_item.scheduled_time,
            feedback=feedback
        )