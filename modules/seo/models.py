"""SEO optimization data models"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, validator
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

class SEOContentType(Enum):
    TWEET = "tweet"
    LINKEDIN_POST = "linkedin_post"
    FACEBOOK_POST = "facebook_post"
    BLOG_POST = "blog_post"
    REPLY = "reply"
    THREAD = "thread"
    QUOTE_TWEET = "quote_tweet"


class SEOOptimizationLevel(Enum):
    LIGHT = "light"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

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
    """Request model for SEO optimization"""
    content: str = Field(..., description="Content to optimize")
    content_type: SEOContentType = Field(default=SEOContentType.TWEET)
    optimization_level: SEOOptimizationLevel = Field(default=SEOOptimizationLevel.MODERATE)
    target_keywords: List[str] = Field(default_factory=list)
    include_hashtags: bool = Field(default=True)
    include_trending_tags: bool = Field(default=True)
    max_length: Optional[int] = Field(default=None)

@dataclass
class SEOOptimizationResult:
    """Result of SEO optimization process"""
    original_content: str
    optimized_content: str
    optimization_score: float
    improvements_made: List[str]
    hashtag_analysis: List[str] = field(default_factory=list)
    keyword_analysis: List[str] = field(default_factory=list)
    estimated_reach_improvement: float = 0.0
    suggestions: List[str] = field(default_factory=list)
    optimization_metadata: Dict[str, Any] = field(default_factory=dict)

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

class ContentSuggestions(BaseModel):
    """Content suggestions for SEO optimization"""
    recommended_hashtags: List[str] = Field(default_factory=list)
    primary_keywords: List[str] = Field(default_factory=list)
    secondary_keywords: List[str] = Field(default_factory=list)
    optimal_length: int = Field(default=280)
    call_to_action: str = Field(default="")
    trending_topics: List[str] = Field(default_factory=list)