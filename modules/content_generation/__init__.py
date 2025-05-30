"""ContentGenerationModule - AI-Powered Content Generation Engine

This module handles intelligent content generation based on trend analysis:
1. Context-aware content generation using LLM
2. Multi-type content support (tweets, replies, threads)
3. SEO optimization integration  
4. Brand voice and style consistency
5. Quality assessment and filtering
6. Database integration for draft storage

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
- Integrates with SEOModule for optimization
- Stores drafts via DataFlowManager
- Feeds ReviewOptimizationModule
"""

from .models import (
    ContentDraft,
    ContentType,
    ContentGenerationRequest,
    ContentGenerationContext,
    ContentQualityScore,
    SEOSuggestions,
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
    'SEOSuggestions',
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