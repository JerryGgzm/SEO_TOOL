"""SEO Module for content optimization and hashtag generation"""

from .base_optimizer import BaseSEOOptimizer
from .optimizer import SEOOptimizer
from .hashtag_generator import HashtagGenerator
from .content_enhancer import ContentEnhancer
from .service_integration import SEOService

# Models
from .models import (
    SEOOptimizationRequest,
    SEOOptimizationResult,
    SEOAnalysisContext,
    SEOContentType,
    SEOOptimizationLevel,
    HashtagStrategy,
    ContentSuggestions
)

# LLM Intelligence (avoid importing demo modules)
try:
    from .llm_intelligence import LLMSEOIntelligence, LLMSEOAnalyzer, LLMSEOOrchestrator
except ImportError:
    # LLM modules are optional
    pass

__all__ = [
    'BaseSEOOptimizer',
    'SEOOptimizer', 
    'HashtagGenerator',
    'ContentEnhancer',
    'SEOService',
    'SEOOptimizationRequest',
    'SEOOptimizationResult',
    'SEOAnalysisContext',
    'SEOContentType',
    'SEOOptimizationLevel',
    'HashtagStrategy',
    'ContentSuggestions'
]

# Factory function to create enhanced SEO optimizer
def create_enhanced_seo_optimizer(twitter_client=None, config: dict = None, 
                                llm_client=None):
    """Factory function to create enhanced SEO optimizer"""
    return SEOOptimizer(
        twitter_client=twitter_client,
        config=config,
        llm_client=llm_client
    )

# Version info
__version__ = "2.0.0"

# Default configuration
DEFAULT_SEO_CONFIG = {
    'llm_optimization_mode': 'comprehensive',
    'optimization_level': 'moderate',
    'hashtag_strategy': 'engagement_optimized',
    'max_hashtags_per_tweet': 5,
    'max_hashtags_per_thread': 3,
    'max_hashtags_per_reply': 2,
    'cache_duration_hours': 6,
    'llm_enabled': True,
    'enable_fallback_protection': True,
    'llm_enhancement_threshold': 0.3,
    'default_optimization_mode': 'comprehensive'
}

# Module initialization
import logging
logger = logging.getLogger(__name__)
logger.info(f"SEO Module v{__version__} initialized with LLM intelligence support")