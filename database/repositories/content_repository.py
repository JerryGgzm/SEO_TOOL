from database.models import GeneratedContentDraft
from database.repositories.base_repository import BaseRepository
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

class ContentRepository(BaseRepository):
    """Repository for content generation operations"""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, GeneratedContentDraft)
    
    def get_pending_review(self, founder_id: str) -> List[GeneratedContentDraft]:
        """Get content pending review"""
        try:
            return self.db_session.query(GeneratedContentDraft).filter(
                GeneratedContentDraft.founder_id == founder_id,
                GeneratedContentDraft.status == 'pending_review'
            ).order_by(
                GeneratedContentDraft.created_at.desc()
            ).all()
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting pending content: {e}")
            return []
    
    def get_scheduled_content(self, limit: int = 50) -> List[GeneratedContentDraft]:
        """Get content scheduled for posting"""
        try:
            return self.db_session.query(GeneratedContentDraft).filter(
                GeneratedContentDraft.status == 'scheduled',
                GeneratedContentDraft.scheduled_post_time <= func.now()
            ).limit(limit).all()
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting scheduled content: {e}")
            return []
    
    def update_status(self, content_id: str, status: str, **kwargs) -> Optional[GeneratedContentDraft]:
        """Update content status"""
        return self.update(content_id, status=status, **kwargs)
    
    def create_content_draft(self, founder_id: str, content_type: str,
                           generated_text: str, **kwargs) -> Optional[GeneratedContentDraft]:
        """Create new content draft"""
        return self.create(
            founder_id=founder_id,
            content_type=content_type,
            generated_text=generated_text,
            **kwargs
        )