"""Main content generation orchestrator"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime

from .models import (
    ContentDraft, ContentType, ContentGenerationRequest, 
    ContentGenerationContext, ContentQualityScore, SEOSuggestions
)
from .llm_adapter import LLMAdapter, LLMAdapterFactory
from .prompts import PromptEngine
from .content_types import ContentTypeFactory
from .quality_checker import ContentQualityChecker

logger = logging.getLogger(__name__)

class ContentGenerator:
    """Main content generation orchestrator"""
    
    def __init__(self, llm_adapter: LLMAdapter, seo_module=None):
        self.llm_adapter = llm_adapter
        self.seo_module = seo_module  # Will be injected when SEOModule is ready
        self.prompt_engine = PromptEngine()
        self.quality_checker = ContentQualityChecker()
        self.content_factory = ContentTypeFactory()
    
    async def generate_content(self, request: ContentGenerationRequest, 
                             context: ContentGenerationContext) -> List[ContentDraft]:
        """
        Main content generation method following DFD 3 steps 4-7
        
        Args:
            request: Content generation request
            context: Generation context with user/product/trend info
            
        Returns:
            List of generated content drafts
        """
        try:
            logger.info(f"Generating {request.content_type} content for founder {request.founder_id}")
            
            # Step 4-5: Get SEO suggestions (DFD 3)
            seo_suggestions = await self._get_seo_suggestions(context, request.content_type)
            
            # Generate prompt based on context
            prompt = self._create_generation_prompt(request, context, seo_suggestions)
            
            # Step 6-7: Generate content using LLM (DFD 3)
            if request.quantity == 1:
                llm_response = await self.llm_adapter.generate_content(prompt)
                llm_responses = [llm_response]
            else:
                llm_responses = await self.llm_adapter.generate_multiple(
                    prompt, request.quantity
                )
            
            # Process each response into content drafts
            drafts = []
            for i, response in enumerate(llm_responses):
                try:
                    draft = await self._process_llm_response(
                        response, request, context, seo_suggestions, i
                    )
                    if draft:
                        drafts.append(draft)
                except Exception as e:
                    logger.error(f"Failed to process LLM response {i}: {e}")
                    continue
            
            # Filter by quality threshold
            quality_drafts = []
            for draft in drafts:
                if (draft.quality_score and 
                    draft.quality_score.overall_score >= request.quality_threshold):
                    quality_drafts.append(draft)
            
            logger.info(f"Generated {len(quality_drafts)}/{len(drafts)} quality drafts")
            return quality_drafts
            
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            return []
    
    async def generate_single_content(self, request: ContentGenerationRequest,
                                    context: ContentGenerationContext) -> Optional[ContentDraft]:
        """Generate a single piece of content"""
        drafts = await self.generate_content(request, context)
        return drafts[0] if drafts else None
    
    async def _get_seo_suggestions(self, context: ContentGenerationContext, 
                                 content_type: ContentType) -> SEOSuggestions:
        """Get SEO suggestions from SEO module (DFD 3 steps 4-5)"""
        
        # If SEO module is available, use it
        if self.seo_module:
            try:
                return await self.seo_module.get_content_suggestions(
                    trend_info=context.trend_info,
                    product_info=context.product_info,
                    content_type=content_type
                )
            except Exception as e:
                logger.warning(f"SEO module failed, using fallback: {e}")
        
        # Fallback SEO suggestions based on context
        return self._generate_fallback_seo_suggestions(context, content_type)
    
    def _generate_fallback_seo_suggestions(self, context: ContentGenerationContext,
                                         content_type: ContentType) -> SEOSuggestions:
        """Generate basic SEO suggestions when SEO module unavailable"""
        
        hashtags = []
        keywords = []
        
        # Extract from trend info
        if context.trend_info:
            trend_name = context.trend_info.get("topic_name", "")
            if trend_name.startswith("#"):
                hashtags.append(trend_name[1:])
            
            # Add pain points as keywords
            pain_points = context.trend_info.get("pain_points", [])
            for point in pain_points[:3]:
                # Extract key terms from pain points
                words = point.lower().split()
                keywords.extend([w for w in words if len(w) > 4])
        
        # Extract from product info
        product_info = context.product_info
        if product_info:
            # Add product category hashtags
            category = product_info.get("industry_category", "")
            if category:
                hashtags.append(category.replace(" ", ""))
            
            # Add core values as keywords
            core_values = product_info.get("core_values", [])
            keywords.extend(core_values[:2])
        
        # Content type specific suggestions
        if content_type == ContentType.TWEET:
            hashtags = hashtags[:3]  # Max 3 hashtags for tweets
        elif content_type == ContentType.REPLY:
            hashtags = hashtags[:1]  # Max 1 hashtag for replies
        
        return SEOSuggestions(
            hashtags=list(set(hashtags))[:5],
            keywords=list(set(keywords))[:10],
            trending_tags=[],
            mentions=[]
        )
    
    def _create_generation_prompt(self, request: ContentGenerationRequest,
                                context: ContentGenerationContext,
                                seo_suggestions: SEOSuggestions) -> str:
        """Create generation prompt based on request and context"""
        
        # Add SEO suggestions to context
        enhanced_context = context.model_copy()
        enhanced_context.content_preferences = {
            **enhanced_context.content_preferences,
            "seo_hashtags": seo_suggestions.hashtags,
            "seo_keywords": seo_suggestions.keywords
        }
        
        # Handle custom prompts
        if request.custom_prompt:
            return self.prompt_engine.create_custom_prompt(
                request.custom_prompt, enhanced_context
            )
        
        # Handle reply-specific context
        if request.content_type == ContentType.REPLY and request.source_tweet_id:
            enhanced_context.content_preferences["original_tweet"] = (
                request.source_tweet_id  # In real implementation, fetch actual tweet
            )
        
        # Generate prompt using prompt engine
        prompt = self.prompt_engine.generate_prompt(
            request.content_type, enhanced_context
        )
        
        # Optimize for LLM provider
        llm_provider = getattr(self.llm_adapter, 'model_name', 'unknown')
        if 'gpt' in llm_provider.lower():
            provider = 'openai'
        elif 'claude' in llm_provider.lower():
            provider = 'claude'
        else:
            provider = 'local'
        
        return self.prompt_engine.optimize_prompt_for_llm(prompt, provider)
    
    async def _process_llm_response(self, llm_response, request: ContentGenerationRequest,
                                  context: ContentGenerationContext, 
                                  seo_suggestions: SEOSuggestions,
                                  response_index: int) -> Optional[ContentDraft]:
        """Process LLM response into content draft"""
        
        try:
            # Create initial draft
            draft = ContentDraft(
                founder_id=request.founder_id,
                content_type=request.content_type,
                generated_text=llm_response.content,
                trend_id=request.trend_id,
                source_tweet_id=request.source_tweet_id,
                seo_suggestions=seo_suggestions,
                generation_metadata={
                    "llm_confidence": llm_response.confidence,
                    "llm_reasoning": llm_response.reasoning,
                    "alternatives": llm_response.alternatives,
                    "response_index": response_index,
                    "generation_timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Validate and optimize content
            is_valid, issues, optimized_text = self.content_factory.validate_and_optimize(draft)
            
            if not is_valid:
                logger.warning(f"Content validation failed: {issues}")
                # Try to fix common issues
                fixed_text = self._attempt_content_fixes(draft.generated_text, issues)
                if fixed_text != draft.generated_text:
                    draft.generated_text = fixed_text
                    is_valid, issues, optimized_text = self.content_factory.validate_and_optimize(draft)
            
            if is_valid:
                draft.generated_text = optimized_text
            
            # Assess content quality
            quality_score = await self.quality_checker.assess_quality(draft, context)
            draft.quality_score = quality_score
            
            # Add quality issues to generation metadata
            if quality_score.issues:
                draft.generation_metadata["quality_issues"] = quality_score.issues
            
            return draft
            
        except Exception as e:
            logger.error(f"Failed to process LLM response: {e}")
            return None
    
    def _attempt_content_fixes(self, text: str, issues: List[str]) -> str:
        """Attempt to fix common content issues"""
        fixed_text = text
        
        for issue in issues:
            if "exceeds" in issue and "characters" in issue:
                # Truncate text intelligently
                if len(fixed_text) > 280:
                    # Try to truncate at sentence boundary
                    sentences = fixed_text.split('. ')
                    truncated = ""
                    for sentence in sentences:
                        if len(truncated + sentence + '. ') <= 275:  # Leave room for ellipsis
                            truncated += sentence + '. '
                        else:
                            break
                    
                    if truncated:
                        fixed_text = truncated.rstrip('. ') + "..."
                    else:
                        # Hard truncate with ellipsis
                        fixed_text = fixed_text[:277] + "..."
            
            elif "Too many hashtags" in issue:
                # Remove excess hashtags
                import re
                hashtags = re.findall(r'#\w+', fixed_text)
                if len(hashtags) > 5:
                    # Keep first 3 hashtags
                    for hashtag in hashtags[3:]:
                        fixed_text = fixed_text.replace(hashtag, '', 1)
            
            elif "Too many mentions" in issue:
                # Remove excess mentions
                import re
                mentions = re.findall(r'@\w+', fixed_text)
                if len(mentions) > 3:
                    # Keep first 2 mentions
                    for mention in mentions[2:]:
                        fixed_text = fixed_text.replace(mention, '', 1)
        
        return fixed_text.strip()
    
    async def regenerate_content(self, original_draft: ContentDraft, 
                               context: ContentGenerationContext,
                               feedback: str = "") -> Optional[ContentDraft]:
        """Regenerate content based on feedback"""
        
        try:
            # Create modified prompt with feedback
            base_prompt = self._create_generation_prompt(
                ContentGenerationRequest(
                    founder_id=original_draft.founder_id,
                    content_type=original_draft.content_type,
                    trend_id=original_draft.trend_id,
                    source_tweet_id=original_draft.source_tweet_id
                ),
                context,
                original_draft.seo_suggestions
            )
            
            feedback_prompt = f"{base_prompt}\n\nPrevious attempt: {original_draft.generated_text}\n\nFeedback: {feedback}\n\nPlease create an improved version addressing the feedback."
            
            # Generate new content
            llm_response = await self.llm_adapter.generate_content(feedback_prompt)
            
            # Process response
            new_draft = await self._process_llm_response(
                llm_response,
                ContentGenerationRequest(
                    founder_id=original_draft.founder_id,
                    content_type=original_draft.content_type,
                    trend_id=original_draft.trend_id,
                    source_tweet_id=original_draft.source_tweet_id
                ),
                context,
                original_draft.seo_suggestions,
                0
            )
            
            if new_draft:
                new_draft.generation_metadata["regeneration_feedback"] = feedback
                new_draft.generation_metadata["original_draft_id"] = original_draft.id
            
            return new_draft
            
        except Exception as e:
            logger.error(f"Content regeneration failed: {e}")
            return None
    
    def get_generation_statistics(self) -> Dict[str, Any]:
        """Get content generation statistics"""
        # This would be implemented with actual tracking
        return {
            "total_generated": 0,
            "success_rate": 0.0,
            "avg_quality_score": 0.0,
            "popular_content_types": {},
            "common_issues": []
        }

class ContentGenerationFactory:
    """Factory for creating content generators with different LLM providers"""
    
    @staticmethod
    def create_generator(llm_provider: str, llm_config: Dict[str, Any], 
                        seo_module=None) -> ContentGenerator:
        """Create content generator with specified LLM provider"""
        
        # Create LLM adapter
        llm_adapter = LLMAdapterFactory.create_adapter(llm_provider, **llm_config)
        
        # Create and return generator
        return ContentGenerator(llm_adapter, seo_module)
    
    @staticmethod
    def create_multi_provider_generator(providers_config: List[Dict[str, Any]], 
                                      seo_module=None) -> 'MultiProviderContentGenerator':
        """Create generator that can use multiple LLM providers"""
        
        generators = {}
        for config in providers_config:
            provider = config.pop('provider')
            generators[provider] = ContentGenerationFactory.create_generator(
                provider, config, seo_module
            )
        
        return MultiProviderContentGenerator(generators, seo_module)

class MultiProviderContentGenerator:
    """Content generator that can use multiple LLM providers"""
    
    def __init__(self, generators: Dict[str, ContentGenerator], seo_module=None):
        self.generators = generators
        self.seo_module = seo_module
        self.default_provider = list(generators.keys())[0] if generators else None
    
    async def generate_content(self, request: ContentGenerationRequest,
                             context: ContentGenerationContext,
                             preferred_provider: str = None) -> List[ContentDraft]:
        """Generate content using specified or default provider"""
        
        provider = preferred_provider or self.default_provider
        generator = self.generators.get(provider)
        
        if not generator:
            raise ValueError(f"Provider {provider} not available")
        
        return await generator.generate_content(request, context)
    
    async def generate_with_fallback(self, request: ContentGenerationRequest,
                                   context: ContentGenerationContext) -> List[ContentDraft]:
        """Generate content with automatic fallback to other providers"""
        
        for provider, generator in self.generators.items():
            try:
                logger.info(f"Attempting content generation with {provider}")
                drafts = await generator.generate_content(request, context)
                if drafts:
                    return drafts
            except Exception as e:
                logger.warning(f"Provider {provider} failed: {e}")
                continue
        
        logger.error("All providers failed to generate content")
        return []