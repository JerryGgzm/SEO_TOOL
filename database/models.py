from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, 
    ForeignKey, Index, JSON, LargeBinary, TIMESTAMP
)
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from sqlalchemy.sql import func
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid
import json
from sqlalchemy.types import TypeDecorator, CHAR

Base = declarative_base()

# 使用 timezone.utc 替代 UTC
UTC = timezone.utc

class UUID(TypeDecorator):
    """Create a UUID type for SQLite for compatibility with PostgreSQL in tests"""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value)) if value else None
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value

class JSONType(TypeDecorator):
    """Create a JSON type for SQLite for compatibility with PostgreSQL in tests"""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        else:
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        else:
            try:
                return json.loads(value)
            except (ValueError, TypeError):
                return value

# ====================
# Core User and Product Models
# ====================

class Founder(Base):
    """Founders table - stores startup founder information"""
    __tablename__ = 'founders'
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment="Unique username for login")
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), comment="User's full name")
    company_name = Column(String(100), comment="User's company name")
    role = Column(String(50), comment="User's role in the company")
    timezone = Column(String(50), default='UTC', comment="User's timezone")
    is_active = Column(Boolean, default=True, comment="Whether the user account is active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    settings = Column(JSONType, default=dict, comment="User interface preferences, notification settings")
    
    # Relationships
    products = relationship("Product", back_populates="founder", cascade="all, delete-orphan")
    twitter_credentials = relationship("TwitterCredential", back_populates="founder", 
                                     cascade="all, delete-orphan", uselist=False)
    analyzed_trends = relationship("AnalyzedTrend", back_populates="founder", cascade="all, delete-orphan")
    generated_content_drafts = relationship("GeneratedContentDraft", back_populates="founder", 
                                          cascade="all, delete-orphan", foreign_keys="GeneratedContentDraft.founder_id")
    automation_rules = relationship("AutomationRule", back_populates="founder", cascade="all, delete-orphan")
    post_analytics = relationship("PostAnalytic", back_populates="founder", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Founder(id={self.id}, email={self.email}, username={self.username})>"

class Product(Base):
    """Products table - stores product information and niche definitions"""
    __tablename__ = 'products'
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    founder_id = Column(UUID(), ForeignKey('founders.id'), nullable=False, index=True)
    product_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    core_values = Column(Text, comment="JSON array of core values")
    target_audience_description = Column(Text, nullable=False)
    niche_definition = Column(JSONType, nullable=False, comment="Keywords, tags, exclusion terms")
    seo_keywords = Column(Text, comment="SEO-specific keywords")
    website_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    founder = relationship("Founder", back_populates="products")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name={self.product_name})>"
    
    @property
    def core_values_list(self) -> List[str]:
        """Get core values as a list"""
        if self.core_values:
            try:
                return json.loads(self.core_values)
            except json.JSONDecodeError:
                return []
        return []
    
    @core_values_list.setter
    def core_values_list(self, values: List[str]):
        """Set core values from a list"""
        self.core_values = json.dumps(values)

# ====================
# Twitter Integration Models
# ====================

class TwitterCredential(Base):
    """Twitter凭证模型"""
    __tablename__ = "twitter_credentials"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    founder_id = Column(UUID(), ForeignKey("founders.id"), nullable=False)  # 修复：应该引用 founders.id
    access_token = Column(String(255), nullable=False)
    refresh_token = Column(String(255))
    token_type = Column(String(50), default="Bearer")
    expires_at = Column(DateTime)
    scope = Column(String(255))
    twitter_user_id = Column(String(50))
    twitter_username = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 添加关系
    founder = relationship("Founder", back_populates="twitter_credentials")
    
    def is_expired(self) -> bool:
        """检查令牌是否过期"""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at

# ====================
# Trend Analysis Models
# ====================

class TrackedTrendRaw(Base):
    """Raw tracked trends table - for debugging and historical analysis"""
    __tablename__ = 'tracked_trends_raw'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trend_source_id = Column(String(100), index=True, comment="Twitter trend ID")
    name = Column(String(200), nullable=False, comment="Trend name/hashtag")
    location_woeid = Column(String(20), index=True, comment="Yahoo WOEID location")
    volume = Column(Integer, comment="Tweet volume if available")
    fetched_at = Column(TIMESTAMP(timezone=True), default=func.now())
    
    def __repr__(self):
        return f"<TrackedTrendRaw(id={self.id}, name={self.name})>"

class AnalyzedTrend(Base):
    """Analyzed trends table - stores comprehensive trend analysis results"""
    __tablename__ = 'analyzed_trends'
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    founder_id = Column(UUID(), ForeignKey('founders.id'), nullable=False, index=True)
    trend_source_id = Column(String(100), comment="Original Twitter trend ID")
    topic_name = Column(String(200), nullable=False, index=True)
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    niche_relevance_score = Column(Float, nullable=False, comment="0.0 to 1.0 relevance score")
    sentiment_scores = Column(JSONType, nullable=False, comment="SentimentBreakdown structure")
    extracted_pain_points = Column(Text, comment="JSON array of pain points")
    common_questions = Column(Text, comment="JSON array of common questions")
    discussion_focus_points = Column(Text, comment="JSON array of discussion themes")
    is_micro_trend = Column(Boolean, default=False, index=True)
    trend_velocity_score = Column(Float, comment="Growth velocity score")
    trend_potential_score = Column(Float, comment="Overall potential score")
    example_tweets_json = Column(JSONType, comment="Sample representative tweets")
    expires_at = Column(DateTime, comment="When analysis becomes stale")
    
    # Relationships
    founder = relationship("Founder", back_populates="analyzed_trends")
    generated_content_drafts = relationship("GeneratedContentDraft", back_populates="analyzed_trend")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_analyzed_trends_founder_micro', 'founder_id', 'is_micro_trend'),
        Index('idx_analyzed_trends_analyzed_at', 'analyzed_at'),
        Index('idx_analyzed_trends_potential_score', 'trend_potential_score'),
    )
    
    def __repr__(self):
        return f"<AnalyzedTrend(id={self.id}, topic={self.topic_name})>"
    
    @property
    def pain_points_list(self) -> List[str]:
        """Get pain points as a list"""
        if self.extracted_pain_points:
            try:
                return json.loads(self.extracted_pain_points)
            except json.JSONDecodeError:
                return []
        return []
    
    @property
    def questions_list(self) -> List[str]:
        """Get common questions as a list"""
        if self.common_questions:
            try:
                return json.loads(self.common_questions)
            except json.JSONDecodeError:
                return []
        return []
    
    @property
    def focus_points_list(self) -> List[str]:
        """Get discussion focus points as a list"""
        if self.discussion_focus_points:
            try:
                return json.loads(self.discussion_focus_points)
            except json.JSONDecodeError:
                return []
        return []

# ====================
# Content Generation Models
# ====================

class GeneratedContentDraft(Base):
    """Generated content drafts table - stores AI-generated content for review and scheduling"""
    __tablename__ = 'generated_content_drafts'
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    founder_id = Column(UUID(), ForeignKey('founders.id'), nullable=False, index=True)
    analyzed_trend_id = Column(UUID(), ForeignKey('analyzed_trends.id'), index=True)
    source_tweet_id_for_reply = Column(String(50), comment="Original tweet ID if this is a reply")
    content_type = Column(String(20), nullable=False, comment="tweet, reply, quote_tweet")
    generated_text = Column(Text, nullable=False, comment="AI-generated original text")
    seo_suggestions = Column(JSONType, comment="SEO keywords and hashtag suggestions")
    edited_text = Column(Text, comment="Founder-edited version")
    status = Column(String(20), nullable=False, default='pending_review', index=True,
                   comment="pending_review, approved, rejected, scheduled, posted, error")
    ai_generation_metadata = Column(JSONType, comment="AI reasoning for content generation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Scheduling fields (merged from scheduled_content)
    scheduled_post_time = Column(DateTime, comment="When to post if scheduled")
    posted_tweet_id = Column(String(50), index=True, comment="Twitter ID after posting")
    platform = Column(String(20), default='twitter', comment="Publishing platform")
    priority = Column(Integer, default=5, comment="Publishing priority (1-10)")
    
    # Error handling fields
    retry_count = Column(Integer, default=0, comment="Current retry count")
    max_retries = Column(Integer, default=1, comment="Maximum retry attempts")
    error_message = Column(Text, comment="Error message if failed")
    error_code = Column(String(50), comment="Error code if failed")
    
    # Publishing details
    posted_at = Column(DateTime, comment="Actual posting time")
    tags = Column(JSONType, default=list, comment="Content tags")
    created_by = Column(UUID(), ForeignKey('founders.id'), comment="User who created/scheduled the content")
    
    # Relationships
    founder = relationship("Founder", back_populates="generated_content_drafts", foreign_keys=[founder_id])
    analyzed_trend = relationship("AnalyzedTrend", back_populates="generated_content_drafts")
    post_analytics = relationship("PostAnalytic", back_populates="content_draft", uselist=False)
    creator = relationship("Founder", foreign_keys=[created_by], post_update=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_content_drafts_status_created', 'status', 'created_at'),
        Index('idx_content_drafts_scheduled_time', 'scheduled_post_time'),
        Index('idx_content_drafts_founder_status', 'founder_id', 'status'),
    )
    
    def __repr__(self):
        return f"<GeneratedContentDraft(id={self.id}, status={self.status})>"
    
    @property
    def final_text(self) -> str:
        """Get the final text (edited if available, otherwise generated)"""
        return self.edited_text if self.edited_text else self.generated_text
    
    @property
    def seo_hashtags(self) -> List[str]:
        """Get SEO suggested hashtags"""
        if self.seo_suggestions and 'hashtags' in self.seo_suggestions:
            return self.seo_suggestions['hashtags']
        return []
    
    @property
    def seo_keywords(self) -> List[str]:
        """Get SEO suggested keywords"""
        if self.seo_suggestions and 'keywords' in self.seo_suggestions:
            return self.seo_suggestions['keywords']
        return []
    
    # Scheduling-related properties (merged from ScheduledContent)
    @property
    def is_due(self) -> bool:
        """Check if content is due for publishing"""
        if not self.scheduled_post_time:
            return False
        return self.scheduled_post_time <= datetime.utcnow()
    
    @property
    def is_overdue(self) -> bool:
        """Check if content is overdue"""
        if not self.scheduled_post_time:
            return False
        from datetime import timedelta
        return self.scheduled_post_time < datetime.utcnow() - timedelta(minutes=5)
    
    @property
    def should_retry(self) -> bool:
        """Check if content should be retried"""
        return (self.status == 'error' and 
                self.retry_count < self.max_retries)
    
    @property
    def tags_list(self) -> List[str]:
        """Get tags as a list"""
        if self.tags:
            return self.tags if isinstance(self.tags, list) else []
        return []
    
    @tags_list.setter
    def tags_list(self, values: List[str]):
        """Set tags from a list"""
        self.tags = values

# ====================
# Automation Models
# ====================

class AutomationRule(Base):
    """Automation rules table - stores user-defined automation rules"""
    __tablename__ = 'automation_rules'
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    founder_id = Column(UUID(), ForeignKey('founders.id'), nullable=False, index=True)
    rule_name = Column(String(100), nullable=False)
    trigger_conditions = Column(JSONType, nullable=False, comment="Conditions that trigger this rule")
    action_to_take = Column(JSONType, nullable=False, comment="Actions to execute when triggered")
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered_at = Column(DateTime, comment="When rule was last executed")
    trigger_count = Column(Integer, default=0, comment="Number of times rule has been triggered")
    
    # Relationships
    founder = relationship("Founder", back_populates="automation_rules")
    
    def __repr__(self):
        return f"<AutomationRule(id={self.id}, name={self.rule_name})>"
    
    def can_trigger(self) -> bool:
        """Check if rule can be triggered (is active)"""
        return self.is_active

# ====================
# Analytics Models
# ====================

class PostAnalytic(Base):
    """Post analytics table - stores performance metrics for published content"""
    __tablename__ = 'post_analytics'
    
    posted_tweet_id = Column(String(50), primary_key=True, comment="Twitter tweet ID")
    founder_id = Column(UUID(), ForeignKey('founders.id'), nullable=False, index=True)
    content_draft_id = Column(UUID(), ForeignKey('generated_content_drafts.id'), index=True)
    impressions = Column(Integer, default=0, comment="Number of times tweet was viewed")
    likes = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    quote_tweets = Column(Integer, default=0)
    link_clicks = Column(Integer, default=0, comment="Clicks on links in tweet")
    profile_visits_from_tweet = Column(Integer, default=0, comment="Profile visits attributed to tweet")
    engagement_rate = Column(Float, comment="Calculated engagement rate")
    posted_at = Column(TIMESTAMP(timezone=True), comment="When tweet was originally posted")
    last_updated_at = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relationships
    founder = relationship("Founder", back_populates="post_analytics")
    content_draft = relationship("GeneratedContentDraft", back_populates="post_analytics")
    
    # Indexes for analytics queries
    __table_args__ = (
        Index('idx_post_analytics_founder_posted', 'founder_id', 'posted_at'),
        Index('idx_post_analytics_engagement_rate', 'engagement_rate'),
    )
    
    def __repr__(self):
        return f"<PostAnalytic(tweet_id={self.posted_tweet_id}, engagement_rate={self.engagement_rate})>"
    
    @property
    def total_engagements(self) -> int:
        """Calculate total engagements"""
        return (self.likes or 0) + (self.retweets or 0) + (self.replies or 0) + (self.quote_tweets or 0)
    
    def calculate_engagement_rate(self) -> float:
        """Calculate engagement rate based on impressions"""
        if self.impressions == 0:
            return 0.0
        return (self.total_engagements / self.impressions) * 100

# ====================
# Scheduling and Publishing Models  
# Note: ScheduledContent functionality has been merged into GeneratedContentDraft
# The ScheduledContent table has been deprecated and removed.
# All scheduling functionality is now handled by GeneratedContentDraft table.
# ====================

# ScheduledContent class removed - all functionality moved to GeneratedContentDraft
# See GeneratedContentDraft for scheduling fields:
# - scheduled_post_time: When to post if scheduled  
# - platform: Publishing platform
# - priority: Publishing priority (1-10)
# - retry_count: Current retry count
# - max_retries: Maximum retry attempts
# - error_message: Error message if failed
# - error_code: Error code if failed
# - posted_at: Actual posting time
# - tags: Content tags
# - created_by: User who created/scheduled the content