"""SEO优化模块 - SEO Optimization Module

This module provides comprehensive SEO optimization capabilities for social media content:
1. Hashtag generation and optimization based on trending analysis
2. Keyword research and optimization with semantic analysis
3. Content enhancement for better engagement and discoverability
4. Platform-specific optimization (Twitter, LinkedIn, Facebook)
5. Performance tracking and optimization recommendations

Main Components:
- optimizer.py: Main SEO optimization orchestrator
- hashtag_generator.py: Advanced hashtag generation and analysis
- keyword_analyzer.py: Keyword research and optimization
- content_enhancer.py: Content structure and readability optimization
- models.py: Data models and structures

Integration Points:
- ContentGenerationModule: Provides SEO suggestions during content creation
- TrendAnalysisModule: Uses trending data for hashtag optimization
- AnalyticsModule: Tracks SEO performance metrics
- UserProfileModule: Customizes optimization based on user niche

Data Flow Integration:
- Receives content optimization requests from ContentGenerationModule
- Fetches trending data from TrendAnalysisModule for hashtag optimization
- Provides optimized content with hashtag and keyword suggestions
- Tracks optimization performance through AnalyticsModule
"""

from .models import (
    # Core models
    SEOOptimizationRequest,
    SEOOptimizationResult,
    ContentOptimizationSuggestions,
    SEOAnalysisContext,
    
    # Hashtag models
    HashtagMetrics,
    HashtagGenerationRequest,
    HashtagStrategy,
    TrendingHashtagsData,
    CompetitorHashtagAnalysis,
    
    # Keyword models
    KeywordAnalysis,
    KeywordOptimizationRequest,
    KeywordDifficulty,
    
    # Configuration models
    SEOConfiguration,
    SEOContentType,
    SEOOptimizationLevel,
    SEOPerformanceMetrics
)

from .optimizer import SEOOptimizer
from .hashtag_generator import HashtagGenerator
from .keyword_analyzer import KeywordAnalyzer
from .content_enhancer import ContentEnhancer

__all__ = [
    # Core models
    'SEOOptimizationRequest',
    'SEOOptimizationResult', 
    'ContentOptimizationSuggestions',
    'SEOAnalysisContext',
    
    # Hashtag models
    'HashtagMetrics',
    'HashtagGenerationRequest',
    'HashtagStrategy',
    'TrendingHashtagsData',
    'CompetitorHashtagAnalysis',
    
    # Keyword models
    'KeywordAnalysis',
    'KeywordOptimizationRequest',
    'KeywordDifficulty',
    
    # Configuration models
    'SEOConfiguration',
    'SEOContentType',
    'SEOOptimizationLevel',
    'SEOPerformanceMetrics',
    
    # Core components
    'SEOOptimizer',
    'HashtagGenerator',
    'KeywordAnalyzer',
    'ContentEnhancer'
]

# Version info
__version__ = '1.0.0'
__author__ = 'Ideation System'
__description__ = 'Comprehensive SEO optimization module for social media content'

# Default configuration
DEFAULT_SEO_CONFIG = {
    'optimization_level': SEOOptimizationLevel.MODERATE,
    'hashtag_strategy': HashtagStrategy.ENGAGEMENT_OPTIMIZED,
    'max_hashtags_per_tweet': 5,
    'max_hashtags_per_thread': 3,
    'max_hashtags_per_reply': 2,
    'keyword_density_target': 0.02,
    'cache_duration_hours': 6,
    'performance_tracking_enabled': True
}