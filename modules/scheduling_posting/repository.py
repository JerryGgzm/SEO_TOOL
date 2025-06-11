"""Repository for scheduling and posting data access"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging
import json

from .models import (
    ScheduledPost, PostStatus, PostPriority, ContentType, PostingRule,
    SchedulingResult, PostingStatistics, PostingBatch
)

Base = declarative_base()
logger = logging.getLogger(__name__)

class ScheduledPostTable(Base):
    """Database table for scheduled posts"""
    __tablename__ = 'scheduled_posts'
    
    id = Column(String(36), primary_key=True)
    founder_id = Column(String(36), nullable=False, index=True)
    content_draft_id = Column(String(36), nullable=False, index=True)
    
    # Content details
    content_text = Column(Text, nullable=False)
    content_type = Column(String(20), nullable=False)
    hashtags = Column(JSON, default=[])
    keywords = Column(JSON, default=[])
    
    # Scheduling information
    scheduled_time = Column(DateTime, nullable=False, index=True)
    priority = Column(String(10), default='normal')
    status = Column(String(20), default='scheduled', index=True)
    
    # Metadata
    generation_metadata = Column(JSON, default={})
    posting_rules_applied = Column(JSON, default=[])
    
    # Posting results
    posted_at = Column(DateTime)
    posted_tweet_id = Column(String(50))
    posting_error = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Thread/reply specific
    parent_tweet_id = Column(String(50))
    thread_position = Column(Integer)
    thread_id = Column(String(36))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Add indexes for performance
    __table_args__ = (
        Index('idx_founder_status', 'founder_id', 'status'),
        Index('idx_scheduled_time_status', 'scheduled_time', 'status'),
        Index('idx_priority_scheduled_time', 'priority', 'scheduled_time'),
    )

class PostingRuleTable(Base):
    """Database table for posting rules"""
    __tablename__ = 'posting_rules'
    
    id = Column(String(36), primary_key=True)
    founder_id = Column(String(36), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Time constraints
    posting_hours_start = Column(Integer, default=9)
    posting_hours_end = Column(Integer, default=21)
    posting_days = Column(JSON, default=[1, 2, 3, 4, 5])
    timezone = Column(String(50), default='UTC')
    
    # Frequency constraints
    max_posts_per_hour = Column(Integer, default=2)
    max_posts_per_day = Column(Integer, default=5)
    min_interval_minutes = Column(Integer, default=30)
    
    # Content type restrictions
    allowed_content_types = Column(JSON, default=['tweet', 'reply'])
    
    # Priority handling
    priority_boost_hours = Column(JSON, default=[])
    high_priority_override = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PostingBatchTable(Base):
    """Database table for posting batches"""
    __tablename__ = 'posting_batches'
    
    id = Column(String(36), primary_key=True)
    founder_id = Column(String(36), nullable=False, index=True)
    batch_name = Column(String(100), nullable=False)
    content_draft_ids = Column(JSON, nullable=False)
    
    # Batch scheduling options
    start_time = Column(DateTime, nullable=False)
    interval_minutes = Column(Integer, default=60)
    priority = Column(String(10), default='normal')
    
    # Results
    scheduled_posts = Column(JSON, default=[])
    failed_schedules = Column(JSON, default=[])
    
    created_at = Column(DateTime, default=datetime.utcnow)

class SchedulingPostingRepository:
    """Repository for scheduling and posting operations"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    # ==================== Scheduled Posts Operations ====================
    
    def create_scheduled_post(self, post: ScheduledPost) -> bool:
        """Create a new scheduled post"""
        try:
            db_post = ScheduledPostTable(
                id=post.id,
                founder_id=post.founder_id,
                content_draft_id=post.content_draft_id,
                content_text=post.content_text,
                content_type=post.content_type.value,
                hashtags=post.hashtags,
                keywords=post.keywords,
                scheduled_time=post.scheduled_time,
                priority=post.priority.value,
                status=post.status.value,
                generation_metadata=post.generation_metadata,
                posting_rules_applied=post.posting_rules_applied,
                parent_tweet_id=post.parent_tweet_id,
                thread_position=post.thread_position,
                thread_id=post.thread_id,
                max_retries=post.max_retries
            )
            
            self.db_session.add(db_post)
            self.db_session.commit()
            return True
            
        except IntegrityError as e:
            self.db_session.rollback()
            logger.error(f"Failed to create scheduled post: {e}")
            return False
    
    def get_scheduled_post(self, post_id: str, founder_id: str = None) -> Optional[ScheduledPost]:
        """Get scheduled post by ID"""
        query = self.db_session.query(ScheduledPostTable).filter(
            ScheduledPostTable.id == post_id
        )
        
        if founder_id:
            query = query.filter(ScheduledPostTable.founder_id == founder_id)
        
        db_post = query.first()
        if not db_post:
            return None
        
        return self._db_post_to_model(db_post)
    
    def get_scheduled_posts_by_status(self, status: PostStatus, 
                                    founder_id: str = None,
                                    limit: int = 100) -> List[ScheduledPost]:
        """Get scheduled posts by status"""
        query = self.db_session.query(ScheduledPostTable).filter(
            ScheduledPostTable.status == status.value
        )
        
        if founder_id:
            query = query.filter(ScheduledPostTable.founder_id == founder_id)
        
        query = query.order_by(ScheduledPostTable.scheduled_time).limit(limit)
        
        return [self._db_post_to_model(db_post) for db_post in query.all()]
    
    def get_posts_ready_for_posting(self, limit: int = 50) -> List[ScheduledPost]:
        """Get posts that are ready to be posted"""
        now = datetime.utcnow()
        
        db_posts = self.db_session.query(ScheduledPostTable).filter(
            ScheduledPostTable.status == PostStatus.SCHEDULED.value,
            ScheduledPostTable.scheduled_time <= now
        ).order_by(
            # Order by priority first, then by scheduled time
            ScheduledPostTable.priority.desc(),
            ScheduledPostTable.scheduled_time
        ).limit(limit).all()
        
        return [self._db_post_to_model(db_post) for db_post in db_posts]
    
    def get_founder_posts_in_period(self, founder_id: str, 
                                  start_time: datetime, 
                                  end_time: datetime,
                                  statuses: List[PostStatus] = None) -> List[ScheduledPost]:
        """Get founder's posts in a specific time period"""
        query = self.db_session.query(ScheduledPostTable).filter(
            ScheduledPostTable.founder_id == founder_id,
            ScheduledPostTable.scheduled_time >= start_time,
            ScheduledPostTable.scheduled_time <= end_time
        )
        
        if statuses:
            status_values = [status.value for status in statuses]
            query = query.filter(ScheduledPostTable.status.in_(status_values))
        
        query = query.order_by(ScheduledPostTable.scheduled_time)
        
        return [self._db_post_to_model(db_post) for db_post in query.all()]
    
    def update_post_status(self, post_id: str, status: PostStatus, 
                          posted_tweet_id: str = None,
                          posting_error: str = None) -> bool:
        """Update post status and related fields"""
        try:
            db_post = self.db_session.query(ScheduledPostTable).filter(
                ScheduledPostTable.id == post_id
            ).first()
            
            if not db_post:
                return False
            
            db_post.status = status.value
            db_post.updated_at = datetime.utcnow()
            
            if status == PostStatus.POSTED:
                db_post.posted_at = datetime.utcnow()
                if posted_tweet_id:
                    db_post.posted_tweet_id = posted_tweet_id
            
            if status == PostStatus.FAILED:
                db_post.retry_count += 1
                if posting_error:
                    db_post.posting_error = posting_error
            
            if status == PostStatus.RETRYING:
                # Reset error for retry
                db_post.posting_error = None
            
            self.db_session.commit()
            return True
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to update post status: {e}")
            return False
    
    def reschedule_post(self, post_id: str, new_scheduled_time: datetime) -> bool:
        """Reschedule a post to a new time"""
        try:
            db_post = self.db_session.query(ScheduledPostTable).filter(
                ScheduledPostTable.id == post_id
            ).first()
            
            if not db_post:
                return False
            
            db_post.scheduled_time = new_scheduled_time
            db_post.status = PostStatus.SCHEDULED.value
            db_post.updated_at = datetime.utcnow()
            
            self.db_session.commit()
            return True
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to reschedule post: {e}")
            return False
    
    def delete_scheduled_post(self, post_id: str, founder_id: str) -> bool:
        """Delete a scheduled post"""
        try:
            deleted_count = self.db_session.query(ScheduledPostTable).filter(
                ScheduledPostTable.id == post_id,
                ScheduledPostTable.founder_id == founder_id
            ).delete()
            
            self.db_session.commit()
            return deleted_count > 0
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to delete scheduled post: {e}")
            return False
    
    # ==================== Posting Rules Operations ====================
    
    def create_posting_rule(self, rule: PostingRule) -> bool:
        """Create a new posting rule"""
        try:
            db_rule = PostingRuleTable(
                id=rule.id,
                founder_id=rule.founder_id,
                name=rule.name,
                description=rule.description,
                is_active=rule.is_active,
                posting_hours_start=rule.posting_hours_start,
                posting_hours_end=rule.posting_hours_end,
                posting_days=rule.posting_days,
                timezone=rule.timezone,
                max_posts_per_hour=rule.max_posts_per_hour,
                max_posts_per_day=rule.max_posts_per_day,
                min_interval_minutes=rule.min_interval_minutes,
                allowed_content_types=[ct.value for ct in rule.allowed_content_types],
                priority_boost_hours=rule.priority_boost_hours,
                high_priority_override=rule.high_priority_override
            )
            
            self.db_session.add(db_rule)
            self.db_session.commit()
            return True
            
        except IntegrityError as e:
            self.db_session.rollback()
            logger.error(f"Failed to create posting rule: {e}")
            return False
    
    def get_posting_rules(self, founder_id: str, active_only: bool = True) -> List[PostingRule]:
        """Get posting rules for a founder"""
        query = self.db_session.query(PostingRuleTable).filter(
            PostingRuleTable.founder_id == founder_id
        )
        
        if active_only:
            query = query.filter(PostingRuleTable.is_active == True)
        
        query = query.order_by(PostingRuleTable.created_at)
        
        return [self._db_rule_to_model(db_rule) for db_rule in query.all()]
    
    def update_posting_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update a posting rule"""
        try:
            db_rule = self.db_session.query(PostingRuleTable).filter(
                PostingRuleTable.id == rule_id
            ).first()
            
            if not db_rule:
                return False
            
            for field, value in updates.items():
                if hasattr(db_rule, field):
                    setattr(db_rule, field, value)
            
            db_rule.updated_at = datetime.utcnow()
            self.db_session.commit()
            return True
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to update posting rule: {e}")
            return False
    
    # ==================== Statistics Operations ====================
    
    def get_posting_statistics(self, founder_id: str, 
                             start_date: datetime, 
                             end_date: datetime) -> PostingStatistics:
        """Get posting statistics for a founder in a time period"""
        posts = self.get_founder_posts_in_period(founder_id, start_date, end_date)
        
        stats = PostingStatistics(
            founder_id=founder_id,
            period_start=start_date,
            period_end=end_date
        )
        
        if not posts:
            return stats
        
        # Count by status
        for post in posts:
            if post.status == PostStatus.SCHEDULED:
                stats.total_scheduled += 1
            elif post.status == PostStatus.POSTED:
                stats.total_posted += 1
            elif post.status == PostStatus.FAILED:
                stats.total_failed += 1
            elif post.status == PostStatus.CANCELLED:
                stats.total_cancelled += 1
        
        # Analyze posting patterns
        posted_posts = [p for p in posts if p.status == PostStatus.POSTED and p.posted_at]
        
        if posted_posts:
            # Posts by hour
            for post in posted_posts:
                hour = post.posted_at.hour
                stats.posts_by_hour[hour] = stats.posts_by_hour.get(hour, 0) + 1
            
            # Posts by day
            for post in posted_posts:
                day = post.posted_at.strftime('%A')
                stats.posts_by_day[day] = stats.posts_by_day.get(day, 0) + 1
            
            # Posts by content type
            for post in posted_posts:
                content_type = post.content_type.value
                stats.posts_by_content_type[content_type] = stats.posts_by_content_type.get(content_type, 0) + 1
            
            # Calculate success rate
            total_attempted = stats.total_posted + stats.total_failed
            if total_attempted > 0:
                stats.success_rate = stats.total_posted / total_attempted
            
            # Calculate average posting delay
            delays = []
            for post in posted_posts:
                if post.posted_at and post.scheduled_time:
                    delay = (post.posted_at - post.scheduled_time).total_seconds() / 60
                    delays.append(delay)
            
            if delays:
                stats.avg_posting_delay_minutes = sum(delays) / len(delays)
            
            # Find peak hours and days
            if stats.posts_by_hour:
                max_posts = max(stats.posts_by_hour.values())
                stats.peak_posting_hours = [hour for hour, count in stats.posts_by_hour.items() 
                                          if count == max_posts]
            
            if stats.posts_by_day:
                max_posts = max(stats.posts_by_day.values())
                stats.most_active_days = [day for day, count in stats.posts_by_day.items() 
                                        if count == max_posts]
        
        return stats
    
    # ==================== Batch Operations ====================
    
    def create_posting_batch(self, batch: PostingBatch) -> bool:
        """Create a posting batch"""
        try:
            db_batch = PostingBatchTable(
                id=batch.id,
                founder_id=batch.founder_id,
                batch_name=batch.batch_name,
                content_draft_ids=batch.content_draft_ids,
                start_time=batch.start_time,
                interval_minutes=batch.interval_minutes,
                priority=batch.priority.value,
                scheduled_posts=batch.scheduled_posts,
                failed_schedules=batch.failed_schedules
            )
            
            self.db_session.add(db_batch)
            self.db_session.commit()
            return True
            
        except IntegrityError as e:
            self.db_session.rollback()
            logger.error(f"Failed to create posting batch: {e}")
            return False
    
    def update_batch_results(self, batch_id: str, 
                           scheduled_posts: List[str], 
                           failed_schedules: List[str]) -> bool:
        """Update batch scheduling results"""
        try:
            db_batch = self.db_session.query(PostingBatchTable).filter(
                PostingBatchTable.id == batch_id
            ).first()
            
            if not db_batch:
                return False
            
            db_batch.scheduled_posts = scheduled_posts
            db_batch.failed_schedules = failed_schedules
            
            self.db_session.commit()
            return True
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to update batch results: {e}")
            return False
    
    # ==================== Helper Methods ====================
    
    def _db_post_to_model(self, db_post: ScheduledPostTable) -> ScheduledPost:
        """Convert database model to Pydantic model"""
        return ScheduledPost(
            id=db_post.id,
            founder_id=db_post.founder_id,
            content_draft_id=db_post.content_draft_id,
            content_text=db_post.content_text,
            content_type=ContentType(db_post.content_type),
            hashtags=db_post.hashtags or [],
            keywords=db_post.keywords or [],
            scheduled_time=db_post.scheduled_time,
            priority=PostPriority(db_post.priority),
            status=PostStatus(db_post.status),
            generation_metadata=db_post.generation_metadata or {},
            posting_rules_applied=db_post.posting_rules_applied or [],
            posted_at=db_post.posted_at,
            posted_tweet_id=db_post.posted_tweet_id,
            posting_error=db_post.posting_error,
            retry_count=db_post.retry_count,
            max_retries=db_post.max_retries,
            parent_tweet_id=db_post.parent_tweet_id,
            thread_position=db_post.thread_position,
            thread_id=db_post.thread_id
        )
    
    def _db_rule_to_model(self, db_rule: PostingRuleTable) -> PostingRule:
        """Convert database model to Pydantic model"""
        return PostingRule(
            id=db_rule.id,
            founder_id=db_rule.founder_id,
            name=db_rule.name,
            description=db_rule.description,
            is_active=db_rule.is_active,
            posting_hours_start=db_rule.posting_hours_start,
            posting_hours_end=db_rule.posting_hours_end,
            posting_days=db_rule.posting_days,
            timezone=db_rule.timezone,
            max_posts_per_hour=db_rule.max_posts_per_hour,
            max_posts_per_day=db_rule.max_posts_per_day,
            min_interval_minutes=db_rule.min_interval_minutes,
            allowed_content_types=[ContentType(ct) for ct in db_rule.allowed_content_types],
            priority_boost_hours=db_rule.priority_boost_hours,
            high_priority_override=db_rule.high_priority_override
        )
    
    # ==================== Additional Helper Methods ====================
    
    def get_last_post_time(self, founder_id: str) -> Optional[datetime]:
        """Get the timestamp of the last posted content for a founder"""
        try:
            last_post = self.db_session.query(ScheduledPostTable).filter(
                ScheduledPostTable.founder_id == founder_id,
                ScheduledPostTable.status == PostStatus.POSTED.value,
                ScheduledPostTable.posted_at.isnot(None)
            ).order_by(ScheduledPostTable.posted_at.desc()).first()
            
            return last_post.posted_at if last_post else None
            
        except Exception as e:
            logger.error(f"Error getting last post time for founder {founder_id}: {e}")
            return None
    
    def get_posts_count_today(self, founder_id: str) -> int:
        """Get the count of posts posted today for a founder"""
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            count = self.db_session.query(ScheduledPostTable).filter(
                ScheduledPostTable.founder_id == founder_id,
                ScheduledPostTable.status == PostStatus.POSTED.value,
                ScheduledPostTable.posted_at >= today_start,
                ScheduledPostTable.posted_at < today_end
            ).count()
            
            return count
            
        except Exception as e:
            logger.error(f"Error getting posts count today for founder {founder_id}: {e}")
            return 0
    
    def get_publishing_stats(self, founder_id: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """Get publishing statistics for performance monitoring"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            end_date = datetime.utcnow()
            
            query = self.db_session.query(ScheduledPostTable).filter(
                ScheduledPostTable.updated_at >= start_date,
                ScheduledPostTable.updated_at <= end_date
            )
            
            if founder_id:
                query = query.filter(ScheduledPostTable.founder_id == founder_id)
            
            posts = query.all()
            
            stats = {
                "total_posts": len(posts),
                "successful_posts": len([p for p in posts if p.status == PostStatus.POSTED.value]),
                "failed_posts": len([p for p in posts if p.status == PostStatus.FAILED.value]),
                "pending_posts": len([p for p in posts if p.status == PostStatus.SCHEDULED.value]),
                "success_rate": 0.0,
                "avg_engagement": 0.0,
                "top_performing_posts": []
            }
            
            # Calculate success rate
            attempted_posts = stats["successful_posts"] + stats["failed_posts"]
            if attempted_posts > 0:
                stats["success_rate"] = stats["successful_posts"] / attempted_posts
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting publishing stats: {e}")
            return {
                "total_posts": 0,
                "successful_posts": 0,
                "failed_posts": 0,
                "pending_posts": 0,
                "success_rate": 0.0,
                "avg_engagement": 0.0,
                "top_performing_posts": []
            }
    
    