from database.models import Founder
from database.repositories.base_repository import BaseRepository
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

class FounderRepository(BaseRepository):
    """Repository for Founder operations"""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, Founder)
    
    def get_by_email(self, email: str) -> Optional[Founder]:
        """Get founder by email"""
        try:
            return self.db_session.query(Founder).filter(
                Founder.email == email.lower()
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting founder by email: {e}")
            return None
    
    def create_founder(self, email: str, hashed_password: str, **kwargs) -> Optional[Founder]:
        """Create new founder"""
        return self.create(
            email=email.lower(),
            hashed_password=hashed_password,
            **kwargs
        )
    
    def update_settings(self, founder_id: str, settings: Dict[str, Any]) -> Optional[Founder]:
        """Update founder settings"""
        return self.update(founder_id, settings=settings)