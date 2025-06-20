from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Float, Integer, Text, JSON, Boolean, or_
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import logging
import uuid

from .models import AnalyzedTrend, TrendAnalysisConfig

logger = logging.getLogger(__name__)
Base = declarative_base()

class AnalyzedTrendTable(Base):
    """Database table for storing analyzed trends"""
    __tablename__ = 'analyzed_trends'
    
    id = Column(String(100), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    trend_source = Column(String(50), nullable=False)
    trend_source_id = Column(String(100))
    topic_name = Column(String(200), nullable=False)
    topic_keywords = Column(JSON)
    analyzed_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Scoring
    niche_relevance_score = Column(Float, nullable=False)
    trend_potential_score = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    
    # Sentiment data
    overall_sentiment = Column(JSON, nullable=False)
    
    # Insights
    extracted_pain_points = Column(JSON)
    common_questions = Column(JSON)
    discussion_focus_points = Column(JSON)
    key_opportunities = Column(JSON)
    
    # Micro-trend data
    is_micro_trend = Column(Boolean, default=False, index=True)
    trend_velocity_score = Column(Float)
    early_adopter_ratio = Column(Float)
    
    # Topic clustering
    topic_clusters = Column(JSON)
    
    # Metrics
    metrics = Column(JSON, nullable=False)
    
    # Supporting data
    sample_tweet_ids_analyzed = Column(JSON)
    example_tweets = Column(JSON)
    
    # Metadata
    expires_at = Column(DateTime, index=True)
    tags = Column(JSON)
    
    # Additional fields for simple trending topics storage
    tweet_volume = Column(Integer, default=0)
    url = Column(String(500))
    location_id = Column(String(50))
    source = Column(String(100))
    trend_metadata = Column(JSON)

class TrendAnalysisRepository:
    """Repository for trend analysis data storage and retrieval"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    def save_analyzed_trend(self, trend: AnalyzedTrend) -> bool:
        """Save an analyzed trend to the database"""
        try:
            # Convert Pydantic model to database model
            trend_data = AnalyzedTrendTable(
                id=trend.id,
                user_id=trend.user_id,
                trend_source=trend.trend_source.value,
                trend_source_id=trend.trend_source_id,
                topic_name=trend.topic_name,
                topic_keywords=trend.topic_keywords,
                analyzed_at=trend.analyzed_at,
                niche_relevance_score=trend.niche_relevance_score,
                trend_potential_score=trend.trend_potential_score,
                confidence_score=trend.confidence_score,
                overall_sentiment=trend.overall_sentiment.dict(),
                extracted_pain_points=trend.extracted_pain_points,
                common_questions=trend.common_questions,
                discussion_focus_points=trend.discussion_focus_points,
                key_opportunities=trend.key_opportunities,
                is_micro_trend=trend.is_micro_trend,
                trend_velocity_score=trend.trend_velocity_score,
                early_adopter_ratio=trend.early_adopter_ratio,
                topic_clusters=[cluster.dict() for cluster in trend.topic_clusters],
                metrics=trend.metrics.dict(),
                sample_tweet_ids_analyzed=trend.sample_tweet_ids_analyzed,
                example_tweets=[tweet.dict() for tweet in trend.example_tweets],
                expires_at=trend.expires_at,
                tags=trend.tags
            )
            
            self.db_session.add(trend_data)
            self.db_session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save analyzed trend: {e}")
            self.db_session.rollback()
            return False
    
    async def store_trending_topic(self, user_id: str, topic_name: str, 
                                 tweet_volume: int = 0, url: str = None, 
                                 matching_keywords: List[str] = None,
                                 relevance_score: float = 0.0, 
                                 confidence_score: float = 0.0,
                                 location_id: str = "1", source: str = "twitter",
                                 metadata: Dict[str, Any] = None) -> Optional[AnalyzedTrendTable]:
        """Store a simple trending topic to the database"""
        try:
            # Create a simple trend entry
            trend_id = str(uuid.uuid4())
            
            # Create default sentiment and metrics
            default_sentiment = {
                "positive": 0.4,
                "negative": 0.2,
                "neutral": 0.4,
                "dominant_sentiment": "neutral"
            }
            
            default_metrics = {
                "tweet_volume": tweet_volume,
                "engagement_rate": 0.0,
                "reach": 0,
                "impressions": 0
            }
            
            trend_data = AnalyzedTrendTable(
                id=trend_id,
                user_id=user_id,
                trend_source="twitter",
                trend_source_id=f"twitter_{topic_name}",
                topic_name=topic_name,
                topic_keywords=matching_keywords or [],
                analyzed_at=datetime.utcnow(),
                niche_relevance_score=relevance_score,
                trend_potential_score=confidence_score,
                confidence_score=confidence_score,
                overall_sentiment=default_sentiment,
                extracted_pain_points=[],
                common_questions=[],
                discussion_focus_points=[],
                key_opportunities=[],
                is_micro_trend=False,
                trend_velocity_score=0.0,
                early_adopter_ratio=0.0,
                topic_clusters=[],
                metrics=default_metrics,
                sample_tweet_ids_analyzed=[],
                example_tweets=[],
                expires_at=datetime.utcnow() + timedelta(days=7),  # Expire in 7 days
                tags=[],
                tweet_volume=tweet_volume,
                url=url,
                location_id=location_id,
                source=source,
                trend_metadata=metadata or {}
            )
            
            self.db_session.add(trend_data)
            self.db_session.commit()
            return trend_data
            
        except Exception as e:
            logger.error(f"Failed to store trending topic: {e}")
            self.db_session.rollback()
            return None
    
    def get_latest_trends_for_user(self, user_id: str, limit: int = 10,
                                  include_expired: bool = False, 
                                  after_time: datetime = None) -> List[AnalyzedTrend]:
        """Get latest analyzed trends for a user"""
        try:
            query = self.db_session.query(AnalyzedTrendTable).filter(
                AnalyzedTrendTable.user_id == user_id
            )
            
            # Filter by time if specified
            if after_time:
                query = query.filter(AnalyzedTrendTable.analyzed_at >= after_time)
            
            # Filter out expired trends unless specifically requested
            if not include_expired:
                query = query.filter(
                    (AnalyzedTrendTable.expires_at.is_(None)) |
                    (AnalyzedTrendTable.expires_at > datetime.utcnow())
                )
            
            trends = query.order_by(
                AnalyzedTrendTable.analyzed_at.desc()
            ).limit(limit).all()
            
            return [self._table_to_model(trend) for trend in trends]
            
        except Exception as e:
            logger.error(f"Failed to get trends for user {user_id}: {e}")
            return []
    
    def get_micro_trends_for_user(self, user_id: str, limit: int = 5) -> List[AnalyzedTrend]:
        """Get micro-trends for a user"""
        try:
            trends = self.db_session.query(AnalyzedTrendTable).filter(
                AnalyzedTrendTable.user_id == user_id,
                AnalyzedTrendTable.is_micro_trend == True,
                (AnalyzedTrendTable.expires_at.is_(None)) |
                (AnalyzedTrendTable.expires_at > datetime.utcnow())
            ).order_by(
                AnalyzedTrendTable.trend_potential_score.desc()
            ).limit(limit).all()
            
            return [self._table_to_model(trend) for trend in trends]
            
        except Exception as e:
            logger.error(f"Failed to get micro-trends for user {user_id}: {e}")
            return []
    
    def get_trends_by_keywords(self, user_id: str, keywords: List[str],
                              limit: int = 10, after_time: datetime = None) -> List[AnalyzedTrend]:
        """Get trends that match specific keywords"""
        try:
            # Create search conditions for keywords
            keyword_conditions = []
            for keyword in keywords:
                keyword_conditions.append(
                    AnalyzedTrendTable.topic_name.ilike(f'%{keyword}%')
                )
            
            query = self.db_session.query(AnalyzedTrendTable).filter(
                AnalyzedTrendTable.user_id == user_id,
                or_(*keyword_conditions) if keyword_conditions else True,
                (AnalyzedTrendTable.expires_at.is_(None)) |
                (AnalyzedTrendTable.expires_at > datetime.utcnow())
            )
            
            # Filter by time if specified
            if after_time:
                query = query.filter(AnalyzedTrendTable.analyzed_at >= after_time)
            
            trends = query.order_by(
                AnalyzedTrendTable.niche_relevance_score.desc()
            ).limit(limit).all()
            
            return [self._table_to_model(trend) for trend in trends]
            
        except Exception as e:
            logger.error(f"Failed to search trends for keywords: {e}")
            return []
    
    async def delete_old_trends(self, user_id: str, before_time: datetime) -> int:
        """Delete old trends for a user"""
        try:
            deleted_count = self.db_session.query(AnalyzedTrendTable).filter(
                AnalyzedTrendTable.user_id == user_id,
                AnalyzedTrendTable.analyzed_at < before_time
            ).delete()
            
            self.db_session.commit()
            logger.info(f"Deleted {deleted_count} old trends for user {user_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete old trends: {e}")
            self.db_session.rollback()
            return 0
    
    async def get_user_trends_count(self, user_id: str) -> int:
        """Get total count of trends for a user"""
        try:
            count = self.db_session.query(AnalyzedTrendTable).filter(
                AnalyzedTrendTable.user_id == user_id,
                (AnalyzedTrendTable.expires_at.is_(None)) |
                (AnalyzedTrendTable.expires_at > datetime.utcnow())
            ).count()
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to get trends count for user {user_id}: {e}")
            return 0
    
    async def get_latest_trend_for_user(self, user_id: str) -> Optional[AnalyzedTrendTable]:
        """Get the latest trend for a user"""
        try:
            trend = self.db_session.query(AnalyzedTrendTable).filter(
                AnalyzedTrendTable.user_id == user_id
            ).order_by(
                AnalyzedTrendTable.analyzed_at.desc()
            ).first()
            
            return trend
            
        except Exception as e:
            logger.error(f"Failed to get latest trend for user {user_id}: {e}")
            return None
    
    def delete_expired_trends(self) -> int:
        """Delete expired trend analyses"""
        try:
            deleted_count = self.db_session.query(AnalyzedTrendTable).filter(
                AnalyzedTrendTable.expires_at < datetime.utcnow()
            ).delete()
            
            self.db_session.commit()
            logger.info(f"Deleted {deleted_count} expired trend analyses")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete expired trends: {e}")
            self.db_session.rollback()
            return 0
    
    def get_trend_statistics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get trend analysis statistics for a user"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            trends = self.db_session.query(AnalyzedTrendTable).filter(
                AnalyzedTrendTable.user_id == user_id,
                AnalyzedTrendTable.analyzed_at >= since_date
            ).all()
            
            if not trends:
                return {
                    'total_trends': 0,
                    'micro_trends': 0,
                    'avg_relevance_score': 0.0,
                    'avg_potential_score': 0.0,
                    'top_keywords': [],
                    'sentiment_distribution': {}
                }
            
            # Calculate statistics
            total_trends = len(trends)
            micro_trends = sum(1 for t in trends if t.is_micro_trend)
            avg_relevance = sum(t.niche_relevance_score for t in trends) / total_trends
            avg_potential = sum(t.trend_potential_score for t in trends) / total_trends
            
            # Extract top keywords
            all_keywords = []
            sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
            
            for trend in trends:
                if trend.topic_keywords:
                    all_keywords.extend(trend.topic_keywords)
                
                sentiment_data = trend.overall_sentiment
                if isinstance(sentiment_data, dict):
                    dominant = sentiment_data.get('dominant_sentiment', 'neutral')
                    sentiment_counts[dominant] = sentiment_counts.get(dominant, 0) + 1
            
            # Count keyword frequency
            from collections import Counter
            keyword_counts = Counter(all_keywords)
            top_keywords = [kw for kw, count in keyword_counts.most_common(10)]
            
            return {
                'total_trends': total_trends,
                'micro_trends': micro_trends,
                'avg_relevance_score': round(avg_relevance, 3),
                'avg_potential_score': round(avg_potential, 3),
                'top_keywords': top_keywords,
                'sentiment_distribution': sentiment_counts
            }
            
        except Exception as e:
            logger.error(f"Failed to get trend statistics: {e}")
            return {}
    
    def _table_to_model(self, trend_table: AnalyzedTrendTable) -> AnalyzedTrend:
        """Convert database table to Pydantic model"""
        from .models import (
            SentimentBreakdown, TrendMetrics, ExampleTweet, 
            TopicCluster, TrendSource
        )
        
        # Parse JSON fields
        overall_sentiment = SentimentBreakdown(**trend_table.overall_sentiment)
        metrics = TrendMetrics(**trend_table.metrics)
        
        example_tweets = []
        if trend_table.example_tweets:
            for tweet_data in trend_table.example_tweets:
                example_tweets.append(ExampleTweet(**tweet_data))
        
        topic_clusters = []
        if trend_table.topic_clusters:
            for cluster_data in trend_table.topic_clusters:
                topic_clusters.append(TopicCluster(**cluster_data))
        
        return AnalyzedTrend(
            id=trend_table.id,
            user_id=trend_table.user_id,
            trend_source=TrendSource(trend_table.trend_source),
            trend_source_id=trend_table.trend_source_id,
            topic_name=trend_table.topic_name,
            topic_keywords=trend_table.topic_keywords or [],
            analyzed_at=trend_table.analyzed_at,
            niche_relevance_score=trend_table.niche_relevance_score,
            trend_potential_score=trend_table.trend_potential_score,
            confidence_score=trend_table.confidence_score,
            overall_sentiment=overall_sentiment,
            extracted_pain_points=trend_table.extracted_pain_points or [],
            common_questions=trend_table.common_questions or [],
            discussion_focus_points=trend_table.discussion_focus_points or [],
            key_opportunities=trend_table.key_opportunities or [],
            is_micro_trend=trend_table.is_micro_trend,
            trend_velocity_score=trend_table.trend_velocity_score,
            early_adopter_ratio=trend_table.early_adopter_ratio,
            topic_clusters=topic_clusters,
            metrics=metrics,
            sample_tweet_ids_analyzed=trend_table.sample_tweet_ids_analyzed or [],
            example_tweets=example_tweets,
            expires_at=trend_table.expires_at,
            tags=trend_table.tags or []
        )
    
    # ===== 新增的方法，支持Gemini API端点 =====
    
    async def get_topics_count(self) -> int:
        """获取数据库中所有话题的总数"""
        try:
            count = self.db_session.query(AnalyzedTrendTable).count()
            return count
        except Exception as e:
            logger.error(f"Failed to get total topics count: {e}")
            return 0
    
    async def get_recent_topics_count(self, hours: int = 24) -> int:
        """获取最近N小时内的话题数量"""
        try:
            since_time = datetime.utcnow() - timedelta(hours=hours)
            count = self.db_session.query(AnalyzedTrendTable).filter(
                AnalyzedTrendTable.analyzed_at >= since_time
            ).count()
            return count
        except Exception as e:
            logger.error(f"Failed to get recent topics count: {e}")
            return 0
    
    async def get_recent_topics(self, limit: int = 10, user_id: str = None) -> List[AnalyzedTrendTable]:
        """获取最近的话题列表"""
        try:
            query = self.db_session.query(AnalyzedTrendTable)
            
            if user_id:
                query = query.filter(AnalyzedTrendTable.user_id == user_id)
            
            topics = query.order_by(
                AnalyzedTrendTable.analyzed_at.desc()
            ).limit(limit).all()
            
            return topics
        except Exception as e:
            logger.error(f"Failed to get recent topics: {e}")
            return []