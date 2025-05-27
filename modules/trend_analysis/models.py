from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum
import re

class TrendSource(str, Enum):
    """Source of trend data"""
    TWITTER_TRENDING = "twitter_trending"
    KEYWORD_SEARCH = "keyword_search"
    MICRO_TREND_DETECTION = "micro_trend_detection"
    MANUAL = "manual"

class SentimentLabel(str, Enum):
    """Sentiment labels"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class EmotionLabel(str, Enum):
    """Emotion labels"""
    JOY = "joy"
    ANGER = "anger"
    FEAR = "fear"
    SADNESS = "sadness"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    TRUST = "trust"
    ANTICIPATION = "anticipation"

class SentimentBreakdown(BaseModel):
    """Sentiment analysis breakdown"""
    positive_score: float = Field(..., ge=0, le=1, description="Positive sentiment score")
    negative_score: float = Field(..., ge=0, le=1, description="Negative sentiment score")
    neutral_score: float = Field(..., ge=0, le=1, description="Neutral sentiment score")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    dominant_sentiment: SentimentLabel = Field(..., description="Dominant sentiment")
    dominant_emotion: Optional[EmotionLabel] = Field(None, description="Dominant emotion")
    
    @field_validator('positive_score', 'negative_score', 'neutral_score')
    @classmethod
    def validate_scores(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Scores must be between 0 and 1')
        return v

class TrendMetrics(BaseModel):
    """Metrics for trend analysis"""
    tweet_volume: int = Field(..., ge=0, description="Number of tweets analyzed")
    engagement_volume: int = Field(..., ge=0, description="Total engagement (likes + retweets + replies)")
    avg_engagement_rate: float = Field(..., ge=0, description="Average engagement per tweet")
    unique_users: int = Field(..., ge=0, description="Number of unique users participating")
    time_span_hours: float = Field(..., gt=0, description="Time span of analyzed data in hours")
    velocity_score: float = Field(..., ge=0, description="Growth velocity indicator")

class ExampleTweet(BaseModel):
    """Representative tweet example"""
    tweet_id: str
    text: str = Field(..., max_length=500)
    sentiment: SentimentLabel
    engagement_score: float = Field(..., ge=0)
    created_at: datetime
    author_username: Optional[str] = None
    why_selected: str = Field(..., description="Reason this tweet was selected as example")

class TopicCluster(BaseModel):
    """Identified topic cluster within a trend"""
    cluster_id: str
    name: str = Field(..., max_length=100)
    keywords: List[str] = Field(..., min_items=1)
    tweet_count: int = Field(..., ge=0)
    relevance_score: float = Field(..., ge=0, le=1)
    sentiment: SentimentBreakdown

class TweetData(BaseModel):
    """Tweet data structure"""
    tweet_id: str = Field(..., description="Tweet ID")
    text: str = Field(..., description="Tweet text")
    created_at: datetime = Field(..., description="Creation timestamp")
    author_id: str = Field(..., description="Author ID")
    public_metrics: Dict[str, int] = Field(default_factory=dict, description="Public metrics")
    context_annotations: Optional[List[Dict[str, Any]]] = Field(default=None, description="Context annotations")
    entities: Optional[Dict[str, Any]] = Field(default=None, description="Tweet entities")
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError('Tweet text cannot be empty')
        return v.strip()

class ProcessedTweetData(BaseModel):
    """Processed tweet data"""
    original_tweet: TweetData
    cleaned_text: str = Field(..., description="Cleaned tweet text")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    hashtags: List[str] = Field(default_factory=list, description="Extracted hashtags")
    mentions: List[str] = Field(default_factory=list, description="Extracted mentions")
    urls: List[str] = Field(default_factory=list, description="Extracted URLs")
    sentiment: Optional[SentimentBreakdown] = Field(None, description="Sentiment analysis")
    pain_points: List[str] = Field(default_factory=list, description="Identified pain points")
    questions: List[str] = Field(default_factory=list, description="Extracted questions")

class AnalyzedTrend(BaseModel):
    """Analyzed trend result"""
    trend_name: str = Field(..., description="Trend name")
    trend_type: str = Field(..., description="Trend type (trending/micro/niche)")
    tweet_volume: Optional[int] = Field(None, description="Tweet volume")
    velocity_score: float = Field(..., ge=0, description="Trend velocity score")
    sentiment_breakdown: SentimentBreakdown = Field(..., description="Overall sentiment")
    niche_relevance_score: float = Field(..., ge=0, le=1, description="Relevance to user's niche")
    trend_potential_score: float = Field(..., ge=0, le=1, description="Trend potential score")
    early_adopter_ratio: float = Field(..., ge=0, le=1, description="Early adopter ratio")
    engagement_metrics: Dict[str, float] = Field(default_factory=dict, description="Engagement metrics")
    sample_tweets: List[ProcessedTweetData] = Field(default_factory=list, description="Sample tweets")
    keywords: List[str] = Field(default_factory=list, description="Related keywords")
    pain_points: List[str] = Field(default_factory=list, description="Identified pain points")
    questions: List[str] = Field(default_factory=list, description="Common questions")
    is_micro_trend: bool = Field(False, description="Is this a micro-trend")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")
    
    @field_validator('trend_name')
    @classmethod
    def validate_trend_name(cls, v):
        if not v.strip():
            raise ValueError('Trend name cannot be empty')
        return v.strip()
    
    @field_validator('niche_relevance_score', 'trend_potential_score', 'early_adopter_ratio')
    @classmethod
    def validate_ratio_scores(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Score must be between 0 and 1')
        return v

class TrendAnalysisRequest(BaseModel):
    """Trend analysis request"""
    user_id: str = Field(..., min_length=1, description="User ID")
    focus_keywords: List[str] = Field(default_factory=list, description="Keywords to focus analysis on")
    location_id: Optional[int] = Field(1, description="Location ID for trending topics (WOEID)")
    max_trends_to_analyze: int = Field(10, ge=1, le=50, description="Maximum number of trends to analyze")
    tweet_sample_size: int = Field(100, ge=10, le=1000, description="Number of tweets to sample per trend")
    include_micro_trends: bool = Field(True, description="Include micro-trend detection")
    sentiment_analysis: bool = Field(True, description="Include sentiment analysis")
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not v.strip():
            raise ValueError('User ID cannot be empty')
        return v.strip()

class TrendAnalysisResult(BaseModel):
    """Complete trend analysis result"""
    user_id: str = Field(..., description="User ID")
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")
    location_woeid: int = Field(..., description="Location WOEID")
    trends: List[AnalyzedTrend] = Field(default_factory=list, description="Analyzed trends")
    micro_trends: List[AnalyzedTrend] = Field(default_factory=list, description="Detected micro-trends")
    niche_trends: List[AnalyzedTrend] = Field(default_factory=list, description="Niche-specific trends")
    overall_sentiment: Optional[SentimentBreakdown] = Field(None, description="Overall sentiment across all trends")
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict, description="Analysis metadata")
    
    @field_validator('trends', 'micro_trends', 'niche_trends')
    @classmethod
    def validate_trend_lists(cls, v):
        return v or []

class HashtagPattern(BaseModel):
    """Hashtag pattern validation"""
    hashtag: str = Field(..., description="Hashtag text")
    
    @field_validator('hashtag')
    @classmethod
    def validate_hashtag_format(cls, v):
        if not re.match(r'^#[a-zA-Z0-9_]+$', v):
            raise ValueError('Invalid hashtag format')
        return v

class TwitterHandle(BaseModel):
    """Twitter handle validation"""
    handle: str = Field(..., description="Twitter handle")
    
    @field_validator('handle')
    @classmethod
    def validate_handle_format(cls, v):
        if not re.match(r'^@[a-zA-Z0-9_]{1,15}$', v):
            raise ValueError('Invalid Twitter handle format')
        return v

class TrendAnalysisConfig(BaseModel):
    """Configuration for trend analysis"""
    max_trends_to_analyze: int = Field(10, ge=1, le=50, description="Maximum trends to analyze")
    max_tweets_per_trend: int = Field(100, ge=10, le=1000, description="Maximum tweets per trend")
    max_clusters: int = Field(5, ge=1, le=20, description="Maximum topic clusters")
    sentiment_threshold: float = Field(0.1, ge=0, le=1, description="Sentiment significance threshold")
    velocity_threshold: float = Field(2.0, ge=0, description="Velocity threshold for micro-trends")
    min_tweet_volume: int = Field(50, ge=1, description="Minimum tweet volume for analysis")
    early_adopter_threshold: float = Field(0.2, ge=0, le=1, description="Early adopter ratio threshold")
    niche_relevance_threshold: float = Field(0.3, ge=0, le=1, description="Niche relevance threshold")
    include_retweets: bool = Field(True, description="Include retweets in analysis")
    language_filter: Optional[str] = Field("en", description="Language filter for tweets")
    llm_model_name: str = Field("gpt-3.5-turbo", description="LLM model name for insights")
    
    @field_validator('max_trends_to_analyze', 'max_tweets_per_trend', 'max_clusters')
    @classmethod
    def validate_positive_integers(cls, v):
        if v <= 0:
            raise ValueError('Value must be positive')
        return v
    
