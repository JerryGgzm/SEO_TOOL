from database.models import AnalyzedTrend
from database.repositories.base_repository import BaseRepository
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

class TrendRepository(BaseRepository):
    """Repository for trend analysis operations"""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, AnalyzedTrend)
    
    def get_trends_by_founder(self, founder_id: str, limit: int = 20,
                            include_expired: bool = False) -> List[AnalyzedTrend]:
        """Get trends for a founder"""
        try:
            query = self.db_session.query(AnalyzedTrend).filter(
                AnalyzedTrend.founder_id == founder_id
            )
            
            if not include_expired:
                query = query.filter(
                    (AnalyzedTrend.expires_at.is_(None)) |
                    (AnalyzedTrend.expires_at > func.now())
                )
            
            return query.order_by(
                AnalyzedTrend.analyzed_at.desc()
            ).limit(limit).all()
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting trends by founder: {e}")
            return []
    
    def get_micro_trends(self, founder_id: str, limit: int = 10) -> List[AnalyzedTrend]:
        """Get micro-trends for a founder"""
        try:
            return self.db_session.query(AnalyzedTrend).filter(
                AnalyzedTrend.founder_id == founder_id,
                AnalyzedTrend.is_micro_trend == True,
                (AnalyzedTrend.expires_at.is_(None)) |
                (AnalyzedTrend.expires_at > func.now())
            ).order_by(
                AnalyzedTrend.trend_potential_score.desc()
            ).limit(limit).all()
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting micro-trends: {e}")
            return []
    
    def create_analyzed_trend(self, founder_id: str, topic_name: str,
                            **kwargs) -> Optional[AnalyzedTrend]:
        """Create new analyzed trend"""
        return self.create(
            founder_id=founder_id,
            topic_name=topic_name,
            **kwargs
        )