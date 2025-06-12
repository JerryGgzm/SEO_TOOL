"""ContentGenerationModule - Streamlined Content Generation Engine

This module handles intelligent content generation based on trend analysis:
1. Context-aware content generation using LLM
2. Multi-type content support (tweets, replies, threads)
3. Brand voice and style consistency
4. Quality assessment and filtering
5. Database integration for draft storage

Main Components:
- generator.py: Main content generation orchestrator
- llm_adapter.py: LLM integration abstraction layer
- prompts.py: Prompt engineering and templates
- content_types.py: Content type definitions and validation
- quality_checker.py: Content quality assessment
- service.py: Database integration service

Data Flow Integration:
- Receives analyzed trends from TrendAnalysisModule
- Gets user context from UserProfileModule  
- Stores drafts via database adapter
- Feeds ReviewOptimizationModule

Note: SEO optimization is handled by the dedicated SEO module.
This module focuses purely on content generation and quality assessment.
"""

from .models import (
    ContentDraft,
    ContentType,
    ContentGenerationRequest,
    ContentGenerationContext,
    ContentQualityScore,
    BrandVoice
)

from .generator import ContentGenerator
from .llm_adapter import LLMAdapter, OpenAIAdapter, ClaudeAdapter, LLMAdapterFactory
from .prompts import PromptEngine, ContentPromptTemplates
from .content_types import ContentTypeFactory, TweetContent, ReplyContent, ThreadContent
from .quality_checker import ContentQualityChecker
from .service import ContentGenerationService
from .database_adapter import ContentGenerationDatabaseAdapter

__all__ = [
    # Models
    'ContentDraft',
    'ContentType', 
    'ContentGenerationRequest',
    'ContentGenerationContext',
    'ContentQualityScore',
    'BrandVoice',
    
    # Core components
    'ContentGenerator',
    'LLMAdapter',
    'LLMAdapterFactory',
    'OpenAIAdapter', 
    'ClaudeAdapter',
    'PromptEngine',
    'ContentPromptTemplates',
    'ContentTypeFactory',
    'TweetContent',
    'ReplyContent',
    'ThreadContent',
    'ContentQualityChecker',
    'ContentGenerationService',
    'ContentGenerationDatabaseAdapter'
]

# Version info
__version__ = "2.0.0"

# Module configuration
DEFAULT_CONFIG = {
    'quality_threshold': 0.6,
    'max_drafts_per_request': 10,
    'content_length_limits': {
        'tweet': 280,
        'reply': 280,
        'thread': 280,
        'quote_tweet': 280
    },
    'generation_timeout_seconds': 30
}

# Module initialization
import logging
logger = logging.getLogger(__name__)
logger.info(f"Content Generation Module v{__version__} initialized")
logger.info("Module focus: Pure content generation without SEO optimization")