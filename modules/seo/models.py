"""SEO optimization data models"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum

class SEOContentType(str, Enum):
    """Content types for SEO optimization"""
    TWEET = "tweet"
    REPLY = "reply"
    THREAD = "thread"
    QUOTE_TWEET = "quote_tweet"
    BIO = "bio"
    PROFILE = "profile"

class SEOOptimizationLevel(str, Enum):
    """SEO optimization levels"""
    BASIC = "basic"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"

class HashtagStrategy(str, Enum):
    """Hashtag optimization strategies"""
    TRENDING_FOCUS = "trending_focus"
    NICHE_SPECIFIC = "niche_specific"
    ENGAGEMENT_OPTIMIZED = "engagement_optimized"
    BRAND_BUILDING = "brand_building"
    DISCOVERY_FOCUSED = "discovery_focused"

class KeywordDifficulty(str, Enum):
    """Keyword competition difficulty levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class HashtagMetrics(BaseModel):
    """Metrics for hashtag analysis"""
    hashtag: str = Field(..., description="Hashtag without # symbol")
    usage_count: int = Field(..., ge=0, description="Number of recent uses")
    growth_rate: float = Field(..., description="Growth rate percentage")
    engagement_rate: float = Field(..., ge=0, description="Average engagement rate")
    competition_level: KeywordDifficulty = Field(..., description="Competition level")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance to content")
    trend_momentum: float = Field(..., ge=0, le=1, description="Trending momentum")
    optimal_timing: Optional[Dict[str, Any]] = Field(None, description="Best posting times")

class KeywordAnalysis(BaseModel):
    """Keyword analysis result"""
    keyword: str = Field(..., description="Target keyword")
    search_volume: int = Field(..., ge=0, description="Estimated search volume")
    difficulty: KeywordDifficulty = Field(..., description="Competition difficulty")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance to niche")
    semantic_variations: List[str] = Field(default=[], description="Related keyword variations")
    sentiment_association: str = Field(default="neutral", description="Common sentiment")
    trending_status: bool = Field(default=False, description="Currently trending")
    suggested_usage: List[str] = Field(default=[], description="Usage suggestions")

class ContentOptimizationSuggestions(BaseModel):
    """Content optimization suggestions"""
    recommended_hashtags: List[str] = Field(default=[], description="Recommended hashtags")
    primary_keywords: List[str] = Field(default=[], description="Primary keywords to include")
    secondary_keywords: List[str] = Field(default=[], description="Secondary keywords")
    semantic_keywords: List[str] = Field(default=[], description="Semantic variations")
    trending_terms: List[str] = Field(default=[], description="Currently trending terms")
    optimal_length: Optional[int] = Field(None, description="Recommended character count")
    call_to_action: Optional[str] = Field(None, description="Suggested CTA")
    timing_recommendation: Optional[str] = Field(None, description="Best posting time")
    engagement_tactics: List[str] = Field(default=[], description="Engagement improvement tactics")

class SEOAnalysisContext(BaseModel):
    """Context for SEO analysis"""
    content_type: SEOContentType = Field(..., description="Type of content")
    target_audience: str = Field(..., description="Target audience description")
    niche_keywords: List[str] = Field(default=[], description="Niche-specific keywords")
    product_categories: List[str] = Field(default=[], description="Product categories")
    brand_voice: Dict[str, Any] = Field(default={}, description="Brand voice characteristics")
    competitor_analysis: Dict[str, Any] = Field(default={}, description="Competitor insights")
    trend_context: Dict[str, Any] = Field(default={}, description="Current trend context")
    geographic_target: Optional[str] = Field(None, description="Geographic target")
    industry_vertical: Optional[str] = Field(None, description="Industry vertical")

class SEOOptimizationRequest(BaseModel):
    """Request for SEO optimization"""
    content: str = Field(..., min_length=1, description="Content to optimize")
    content_type: SEOContentType = Field(..., description="Content type")
    optimization_level: SEOOptimizationLevel = Field(default=SEOOptimizationLevel.MODERATE)
    hashtag_strategy: HashtagStrategy = Field(default=HashtagStrategy.ENGAGEMENT_OPTIMIZED)
    max_hashtags: int = Field(default=5, ge=1, le=30, description="Maximum hashtags to suggest")
    max_keywords: int = Field(default=10, ge=1, le=50, description="Maximum keywords to suggest")
    context: SEOAnalysisContext = Field(..., description="Analysis context")
    preserve_original_tone: bool = Field(default=True, description="Maintain original tone")
    include_trending_tags: bool = Field(default=True, description="Include trending hashtags")

class SEOOptimizationResult(BaseModel):
    """Result of SEO optimization"""
    original_content: str = Field(..., description="Original content")
    optimized_content: str = Field(..., description="SEO optimized content")
    optimization_score: float = Field(..., ge=0, le=1, description="Overall optimization score")
    improvements_made: List[str] = Field(default=[], description="List of improvements made")
    suggestions: ContentOptimizationSuggestions = Field(..., description="Optimization suggestions")
    hashtag_analysis: List[HashtagMetrics] = Field(default=[], description="Hashtag analysis")
    keyword_analysis: List[KeywordAnalysis] = Field(default=[], description="Keyword analysis")
    seo_score_breakdown: Dict[str, float] = Field(default={}, description="Detailed score breakdown")
    estimated_reach_improvement: float = Field(default=0.0, description="Estimated reach improvement %")
    optimization_metadata: Dict[str, Any] = Field(default={}, description="Optimization metadata")

class CompetitorHashtagAnalysis(BaseModel):
    """Competitor hashtag analysis"""
    competitor_name: str = Field(..., description="Competitor identifier")
    top_hashtags: List[str] = Field(..., description="Top performing hashtags")
    hashtag_frequency: Dict[str, int] = Field(..., description="Hashtag usage frequency")
    engagement_correlation: Dict[str, float] = Field(..., description="Hashtag-engagement correlation")
    unique_hashtags: List[str] = Field(default=[], description="Unique hashtags not used by us")
    gap_opportunities: List[str] = Field(default=[], description="Hashtag gap opportunities")

class TrendingHashtagsData(BaseModel):
    """Current trending hashtags data"""
    global_trending: List[HashtagMetrics] = Field(default=[], description="Globally trending hashtags")
    niche_trending: List[HashtagMetrics] = Field(default=[], description="Niche-specific trending")
    location_trending: List[HashtagMetrics] = Field(default=[], description="Location-based trending")
    industry_trending: List[HashtagMetrics] = Field(default=[], description="Industry-specific trending")
    emerging_hashtags: List[HashtagMetrics] = Field(default=[], description="Emerging hashtags")
    data_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Data collection time")

class SEOPerformanceMetrics(BaseModel):
    """SEO performance tracking metrics"""
    content_id: str = Field(..., description="Content identifier")
    pre_optimization_metrics: Dict[str, float] = Field(..., description="Metrics before optimization")
    post_optimization_metrics: Dict[str, float] = Field(..., description="Metrics after optimization")
    improvement_percentage: float = Field(..., description="Percentage improvement")
    hashtag_performance: Dict[str, float] = Field(default={}, description="Individual hashtag performance")
    keyword_performance: Dict[str, float] = Field(default={}, description="Keyword performance tracking")
    reach_metrics: Dict[str, int] = Field(default={}, description="Reach-related metrics")
    engagement_metrics: Dict[str, float] = Field(default={}, description="Engagement metrics")
    tracking_period_days: int = Field(default=7, description="Tracking period in days")

class SEOConfiguration(BaseModel):
    """SEO module configuration"""
    default_optimization_level: SEOOptimizationLevel = Field(default=SEOOptimizationLevel.MODERATE)
    default_hashtag_strategy: HashtagStrategy = Field(default=HashtagStrategy.ENGAGEMENT_OPTIMIZED)
    max_hashtags_per_tweet: int = Field(default=5, ge=1, le=30)
    max_hashtags_per_thread: int = Field(default=3, ge=1, le=15)
    max_hashtags_per_reply: int = Field(default=2, ge=1, le=10)
    keyword_analysis_enabled: bool = Field(default=True)
    competitor_analysis_enabled: bool = Field(default=True)
    trending_analysis_enabled: bool = Field(default=True)
    auto_optimization_threshold: float = Field(default=0.7, ge=0, le=1)
    performance_tracking_enabled: bool = Field(default=True)
    cache_duration_hours: int = Field(default=6, ge=1, le=72)
    api_rate_limit_per_hour: int = Field(default=1000, ge=100)
    
    @field_validator('max_hashtags_per_tweet', 'max_hashtags_per_thread', 'max_hashtags_per_reply')
    @classmethod
    def validate_hashtag_limits(cls, v):
        if v <= 0:
            raise ValueError('Hashtag limits must be positive')
        return v

class HashtagGenerationRequest(BaseModel):
    """Request for hashtag generation"""
    content: str = Field(..., description="Content to generate hashtags for")
    content_type: SEOContentType = Field(..., description="Content type")
    niche_keywords: List[str] = Field(default=[], description="Niche keywords")
    max_hashtags: int = Field(default=5, ge=1, le=30)
    strategy: HashtagStrategy = Field(default=HashtagStrategy.ENGAGEMENT_OPTIMIZED)
    include_trending: bool = Field(default=True, description="Include trending hashtags")
    include_niche: bool = Field(default=True, description="Include niche-specific hashtags")
    exclude_hashtags: List[str] = Field(default=[], description="Hashtags to exclude")
    target_audience: Optional[str] = Field(None, description="Target audience")

class KeywordOptimizationRequest(BaseModel):
    """Request for keyword optimization"""
    content: str = Field(..., description="Content to optimize")
    target_keywords: List[str] = Field(default=[], description="Target keywords")
    semantic_enhancement: bool = Field(default=True, description="Include semantic variations")
    keyword_density_target: float = Field(default=0.02, ge=0, le=0.1, description="Target keyword density")
    preserve_readability: bool = Field(default=True, description="Maintain content readability")
    content_type: SEOContentType = Field(..., description="Content type")