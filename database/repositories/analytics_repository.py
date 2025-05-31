from datetime import datetime, timedelta, UTC
from sqlalchemy import func, and_, or_
from typing import Dict, List, Optional, Tuple, Any
from database.models import PostAnalytic
from database.repositories.base_repository import BaseRepository
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

class AnalyticsRepository(BaseRepository):
    """Repository for analytics operations"""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, PostAnalytic)

    def track_hashtag_performance(self, hashtag: str, metrics: Dict[str, float]) -> bool:
        """Track individual hashtag performance"""
        # TODO: Implementation here
        
        
        
    def get_hashtag_performance_trends(self, founder_id: str, days: int = 30) -> List[Dict]:
        """Get hashtag performance trends"""
        # TODO: Implementation here
        
    
    def create_or_update_analytics(self, posted_tweet_id: str, 
                                 founder_id: str, **metrics) -> Optional[PostAnalytic]:
        """Create or update post analytics"""
        try:
            # Check if analytics record exists
            existing = self.db_session.query(PostAnalytic).filter(
                PostAnalytic.posted_tweet_id == posted_tweet_id
            ).first()
            
            if existing:
                # Update existing record
                for key, value in metrics.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                
                # Recalculate engagement rate
                if existing.impressions and existing.impressions > 0:
                    existing.engagement_rate = existing.calculate_engagement_rate()
                
                self.db_session.commit()
                return existing
            else:
                # Create new record
                analytics = PostAnalytic(
                    posted_tweet_id=posted_tweet_id,
                    founder_id=founder_id,
                    **metrics
                )
                
                # Calculate engagement rate
                if analytics.impressions and analytics.impressions > 0:
                    analytics.engagement_rate = analytics.calculate_engagement_rate()
                
                self.db_session.add(analytics)
                self.db_session.commit()
                return analytics
                
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error creating/updating analytics: {e}")
            return None
    
    def get_founder_analytics_summary(self, founder_id: str, 
                                    days: int = 30) -> Dict[str, Any]:
        """Get analytics summary for a founder"""
        try:
            since_date = datetime.now(UTC) - timedelta(days=days)
            
            # Get analytics data
            analytics = self.db_session.query(PostAnalytic).filter(
                PostAnalytic.founder_id == founder_id,
                PostAnalytic.posted_at >= since_date
            ).all()
            
            if not analytics:
                return {
                    'total_posts': 0,
                    'total_impressions': 0,
                    'total_engagements': 0,
                    'avg_engagement_rate': 0.0,
                    'best_performing_tweet': None,
                    'total_likes': 0,
                    'total_retweets': 0,
                    'total_replies': 0,
                    'period_days': days
                }
            
            # Calculate summary statistics
            total_posts = len(analytics)
            total_impressions = sum(a.impressions or 0 for a in analytics)
            total_likes = sum(a.likes or 0 for a in analytics)
            total_retweets = sum(a.retweets or 0 for a in analytics)
            total_replies = sum(a.replies or 0 for a in analytics)
            total_quote_tweets = sum(a.quote_tweets or 0 for a in analytics)
            
            total_engagements = total_likes + total_retweets + total_replies + total_quote_tweets
            
            # Calculate average engagement rate
            engagement_rates = [a.engagement_rate for a in analytics if a.engagement_rate]
            avg_engagement_rate = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0.0
            
            # Find best performing tweet
            best_tweet = max(analytics, key=lambda a: a.engagement_rate or 0) if analytics else None
            
            return {
                'total_posts': total_posts,
                'total_impressions': total_impressions,
                'total_engagements': total_engagements,
                'avg_engagement_rate': round(avg_engagement_rate, 2),
                'best_performing_tweet': {
                    'tweet_id': best_tweet.posted_tweet_id,
                    'engagement_rate': best_tweet.engagement_rate,
                    'total_engagements': best_tweet.total_engagements
                } if best_tweet else None,
                'total_likes': total_likes,
                'total_retweets': total_retweets,
                'total_replies': total_replies,
                'total_quote_tweets': total_quote_tweets,
                'period_days': days
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting analytics summary: {e}")
            return {}
    
    def get_engagement_trends(self, founder_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily engagement trends"""
        try:
            since_date = datetime.now(UTC) - timedelta(days=days)
            
            # Query daily aggregations
            daily_stats = self.db_session.query(
                func.date(PostAnalytic.posted_at).label('date'),
                func.count(PostAnalytic.posted_tweet_id).label('posts_count'),
                func.sum(PostAnalytic.impressions).label('total_impressions'),
                func.sum(PostAnalytic.likes + PostAnalytic.retweets + 
                        PostAnalytic.replies + PostAnalytic.quote_tweets).label('total_engagements'),
                func.avg(PostAnalytic.engagement_rate).label('avg_engagement_rate')
            ).filter(
                PostAnalytic.founder_id == founder_id,
                PostAnalytic.posted_at >= since_date
            ).group_by(
                func.date(PostAnalytic.posted_at)
            ).order_by(
                func.date(PostAnalytic.posted_at)
            ).all()
            
            return [
                {
                    'date': stat.date,
                    'posts_count': stat.posts_count,
                    'total_impressions': stat.total_impressions or 0,
                    'total_engagements': stat.total_engagements or 0,
                    'avg_engagement_rate': round(float(stat.avg_engagement_rate or 0), 2)
                }
                for stat in daily_stats
            ]
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting engagement trends: {e}")
            return []