"""Main content generation orchestrator"""
"""Enhanced content generation with full SEO integration"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Dict
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

# Import SEO components
from modules.seo.optimizer import SEOOptimizer
from modules.seo.models import (
    SEOOptimizationRequest, SEOAnalysisContext, SEOContentType,
    SEOOptimizationLevel, HashtagStrategy
)

logger = logging.getLogger(__name__)

class ContentGenerator:
    """Content generator with full SEO integration"""
    
    def __init__(self, llm_adapter: LLMAdapter, seo_optimizer: SEOOptimizer = None):
        self.llm_adapter = llm_adapter
        self.seo_optimizer = seo_optimizer  # SEO module integration
        self.prompt_engine = PromptEngine()
        self.quality_checker = ContentQualityChecker()
        self.content_factory = ContentTypeFactory()
        
        # Enhanced generation strategies
        self.generation_strategies = {
            'seo_optimized': self._generate_seo_optimized_content,
            'engagement_focused': self._generate_engagement_focused_content,
            'trend_based': self._generate_trend_based_content,
            'balanced': self._generate_balanced_content
        }
    
    async def generate_content(self, request: ContentGenerationRequest, 
                             context: ContentGenerationContext) -> List[ContentDraft]:
        """
        Enhanced content generation with SEO optimization
        
        Args:
            request: Content generation request
            context: Generation context with user/product/trend info
            
        Returns:
            List of SEO-optimized content drafts
        """
        try:
            logger.info(f"Generating {request.content_type} content with SEO optimization")
            
            # Step 1: Get SEO suggestions (enhanced)
            seo_suggestions = await self._get_enhanced_seo_suggestions(context, request.content_type)
            
            # Step 2: Create SEO-enhanced context
            enhanced_context = self._enhance_context_with_seo(context, seo_suggestions)
            
            # Step 3: Generate content using appropriate strategy
            strategy = request.generation_strategy if hasattr(request, 'generation_strategy') else 'balanced'
            generation_method = self.generation_strategies.get(strategy, self._generate_balanced_content)
            
            # Step 4: Generate multiple content variations
            if request.quantity == 1:
                drafts = await generation_method(request, enhanced_context, seo_suggestions)
            else:
                all_drafts = []
                for i in range(request.quantity):
                    batch_drafts = await generation_method(request, enhanced_context, seo_suggestions)
                    all_drafts.extend(batch_drafts)
                drafts = all_drafts[:request.quantity]
            
            # Step 5: Apply SEO optimization to each draft
            optimized_drafts = []
            for draft in drafts:
                optimized_draft = await self._apply_seo_optimization(draft, enhanced_context)
                if optimized_draft:
                    optimized_drafts.append(optimized_draft)
            
            # Step 6: Filter by quality threshold
            quality_drafts = []
            for draft in optimized_drafts:
                if (draft.quality_score and 
                    draft.quality_score.overall_score >= request.quality_threshold):
                    quality_drafts.append(draft)
            
            logger.info(f"Generated {len(quality_drafts)}/{len(drafts)} quality SEO-optimized drafts")
            return quality_drafts
            
        except Exception as e:
            logger.error(f"Enhanced content generation failed: {e}")
            return []
    
    async def _get_enhanced_seo_suggestions(self, context: ContentGenerationContext, 
                                          content_type: ContentType) -> SEOSuggestions:
        """Get enhanced SEO suggestions using SEO module"""
        
        if not self.seo_optimizer:
            return self._generate_fallback_seo_suggestions(context, content_type)
        
        try:
            # Build trend info for SEO module
            trend_info = context.trend_info or {}
            
            # Build product info for SEO module
            product_info = context.product_info or {}
            
            # Convert content type to SEO content type
            seo_content_type = self._convert_to_seo_content_type(content_type)
            
            # Get SEO suggestions from SEO module
            seo_suggestions = await self.seo_optimizer.get_content_suggestions(
                trend_info=trend_info,
                product_info=product_info,
                content_type=seo_content_type
            )
            
            # Convert SEO suggestions to content generation format
            return SEOSuggestions(
                hashtags=seo_suggestions.recommended_hashtags,
                keywords=seo_suggestions.primary_keywords + seo_suggestions.secondary_keywords,
                mentions=getattr(seo_suggestions, 'recommended_mentions', []),
                trending_tags=seo_suggestions.trending_terms,
                optimal_length=seo_suggestions.optimal_length
            )
            
        except Exception as e:
            logger.warning(f"SEO module failed, using fallback: {e}")
            return self._generate_fallback_seo_suggestions(context, content_type)
    
    def _enhance_context_with_seo(self, context: ContentGenerationContext,
                                 seo_suggestions: SEOSuggestions) -> ContentGenerationContext:
        """Enhance generation context with SEO data"""
        
        enhanced_context = context.model_copy()
        
        # Add SEO suggestions to content preferences
        enhanced_context.content_preferences = {
            **enhanced_context.content_preferences,
            "seo_hashtags": seo_suggestions.hashtags,
            "seo_keywords": seo_suggestions.keywords,
            "trending_tags": seo_suggestions.trending_tags,
            "optimal_length": seo_suggestions.optimal_length,
            "seo_enhanced": True
        }
        
        return enhanced_context
    
    async def _generate_seo_optimized_content(self, request: ContentGenerationRequest,
                                            context: ContentGenerationContext,
                                            seo_suggestions: SEOSuggestions) -> List[ContentDraft]:
        """Generate content with primary focus on SEO optimization"""
        
        # Create SEO-focused prompt
        seo_prompt = self._create_seo_focused_prompt(request, context, seo_suggestions)
        
        # Generate content
        llm_response = await self.llm_adapter.generate_content(seo_prompt, temperature=0.7)
        
        # Process response
        draft = await self._process_llm_response(
            llm_response, request, context, seo_suggestions, 0
        )
        
        return [draft] if draft else []
    
    async def _generate_engagement_focused_content(self, request: ContentGenerationRequest,
                                                 context: ContentGenerationContext,
                                                 seo_suggestions: SEOSuggestions) -> List[ContentDraft]:
        """Generate content with primary focus on engagement"""
        
        # Create engagement-focused prompt
        engagement_prompt = self._create_engagement_focused_prompt(request, context, seo_suggestions)
        
        # Generate content
        llm_response = await self.llm_adapter.generate_content(engagement_prompt, temperature=0.8)
        
        # Process response
        draft = await self._process_llm_response(
            llm_response, request, context, seo_suggestions, 0
        )
        
        return [draft] if draft else []
    
    async def _generate_trend_based_content(self, request: ContentGenerationRequest,
                                          context: ContentGenerationContext,
                                          seo_suggestions: SEOSuggestions) -> List[ContentDraft]:
        """Generate content with primary focus on trending topics"""
        
        if not context.trend_info:
            # Fallback to balanced approach if no trend info
            return await self._generate_balanced_content(request, context, seo_suggestions)
        
        # Create trend-focused prompt
        trend_prompt = self._create_trend_focused_prompt(request, context, seo_suggestions)
        
        # Generate content
        llm_response = await self.llm_adapter.generate_content(trend_prompt, temperature=0.8)
        
        # Process response
        draft = await self._process_llm_response(
            llm_response, request, context, seo_suggestions, 0
        )
        
        return [draft] if draft else []
    
    async def _generate_balanced_content(self, request: ContentGenerationRequest,
                                       context: ContentGenerationContext,
                                       seo_suggestions: SEOSuggestions) -> List[ContentDraft]:
        """Generate content with balanced approach (SEO + engagement + trends)"""
        
        # Create balanced prompt
        balanced_prompt = self._create_balanced_prompt(request, context, seo_suggestions)
        
        # Generate content
        llm_response = await self.llm_adapter.generate_content(balanced_prompt, temperature=0.75)
        
        # Process response
        draft = await self._process_llm_response(
            llm_response, request, context, seo_suggestions, 0
        )
        
        return [draft] if draft else []
    
    def _create_seo_focused_prompt(self, request: ContentGenerationRequest,
                                 context: ContentGenerationContext,
                                 seo_suggestions: SEOSuggestions) -> str:
        """Create SEO-focused generation prompt"""
        
        base_prompt = self.prompt_engine.generate_prompt(request.content_type, context)
        
        # Add SEO-specific instructions
        seo_instructions = f"""
        
SEO OPTIMIZATION REQUIREMENTS:
- Primary Keywords: {', '.join(seo_suggestions.keywords[:3])}
- Target Hashtags: {', '.join(f'#{tag}' for tag in seo_suggestions.hashtags[:5])}
- Optimal Length: {seo_suggestions.optimal_length or 'platform optimal'} characters
- Include trending terms: {', '.join(seo_suggestions.trending_tags[:3])}

IMPORTANT: Naturally integrate these SEO elements while maintaining readability and authenticity.
"""
        
        return base_prompt + seo_instructions
    
    def _create_engagement_focused_prompt(self, request: ContentGenerationRequest,
                                        context: ContentGenerationContext,
                                        seo_suggestions: SEOSuggestions) -> str:
        """Create engagement-focused generation prompt"""
        
        base_prompt = self.prompt_engine.generate_prompt(request.content_type, context)
        
        # Add engagement-specific instructions
        engagement_instructions = f"""
        
ENGAGEMENT OPTIMIZATION REQUIREMENTS:
- Include a compelling question or call-to-action
- Use emotional triggers and personal language
- Add numbers or statistics for attention
- Include relevant hashtags: {', '.join(f'#{tag}' for tag in seo_suggestions.hashtags[:3])}
- Target length: {seo_suggestions.optimal_length or 'platform optimal'} characters

FOCUS: Maximum engagement while incorporating: {', '.join(seo_suggestions.keywords[:2])}
"""
        
        return base_prompt + engagement_instructions
    
    def _create_trend_focused_prompt(self, request: ContentGenerationRequest,
                                   context: ContentGenerationContext,
                                   seo_suggestions: SEOSuggestions) -> str:
        """Create trend-focused generation prompt"""
        
        base_prompt = self.prompt_engine.generate_prompt(request.content_type, context)
        
        # Extract trend information
        trend_info = context.trend_info or {}
        trend_name = trend_info.get('topic_name', 'current trends')
        pain_points = trend_info.get('pain_points', [])
        
        # Add trend-specific instructions
        trend_instructions = f"""
        
TREND OPTIMIZATION REQUIREMENTS:
- Focus on trending topic: {trend_name}
- Address key pain points: {', '.join(pain_points[:2])}
- Include trending hashtags: {', '.join(f'#{tag}' for tag in seo_suggestions.trending_tags[:3])}
- Incorporate keywords: {', '.join(seo_suggestions.keywords[:3])}

GOAL: Capitalize on trend momentum while maintaining brand relevance.
"""
        
        return base_prompt + trend_instructions
    
    def _create_balanced_prompt(self, request: ContentGenerationRequest,
                              context: ContentGenerationContext,
                              seo_suggestions: SEOSuggestions) -> str:
        """Create balanced generation prompt"""
        
        base_prompt = self.prompt_engine.generate_prompt(request.content_type, context)
        
        # Add balanced instructions
        balanced_instructions = f"""
        
BALANCED OPTIMIZATION REQUIREMENTS:
- SEO Keywords (natural integration): {', '.join(seo_suggestions.keywords[:2])}
- Engagement elements: question or compelling hook
- Relevant hashtags: {', '.join(f'#{tag}' for tag in seo_suggestions.hashtags[:3])}
- Target length: {seo_suggestions.optimal_length or 'platform optimal'} characters

BALANCE: Equal focus on SEO discoverability, audience engagement, and brand authenticity.
"""
        
        return base_prompt + balanced_instructions
    
    async def _apply_seo_optimization(self, draft: ContentDraft,
                                    context: ContentGenerationContext) -> Optional[ContentDraft]:
        """Apply additional SEO optimization to generated draft"""
        
        if not self.seo_optimizer:
            return draft
        
        try:
            # Convert content type
            seo_content_type = self._convert_to_seo_content_type(draft.content_type)
            
            # Apply SEO optimization
            optimized_text = self.seo_optimizer.optimize_content_simple(
                text=draft.generated_text,
                content_type=seo_content_type,
                context={
                    'seo_keywords': context.content_preferences.get('seo_keywords', []),
                    'target_audience': context.target_audience
                }
            )
            
            # Update draft with optimized content
            if optimized_text != draft.generated_text:
                draft.generated_text = optimized_text
                
                # Update metadata to track SEO optimization
                draft.generation_metadata["seo_optimized"] = True
                draft.generation_metadata["seo_optimization_timestamp"] = datetime.utcnow().isoformat()
            
            return draft
            
        except Exception as e:
            logger.warning(f"SEO optimization failed for draft: {e}")
            return draft
    
    async def _process_llm_response(self, llm_response, request: ContentGenerationRequest,
                                  context: ContentGenerationContext, 
                                  seo_suggestions: SEOSuggestions,
                                  response_index: int) -> Optional[ContentDraft]:
        """Enhanced LLM response processing with SEO data"""
        
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
                    "generation_timestamp": datetime.utcnow().isoformat(),
                    "seo_keywords_used": seo_suggestions.keywords,
                    "seo_hashtags_suggested": seo_suggestions.hashtags
                }
            )
            
            # Validate and optimize content
            is_valid, issues, optimized_text = self.content_factory.validate_and_optimize(
                draft, context=context.dict(), seo_optimizer=self.seo_optimizer
            )
            
            if not is_valid:
                logger.warning(f"Content validation failed: {issues}")
                # Try to fix common issues
                fixed_text = self._attempt_content_fixes(draft.generated_text, issues)
                if fixed_text != draft.generated_text:
                    draft.generated_text = fixed_text
                    is_valid, issues, optimized_text = self.content_factory.validate_and_optimize(draft)
            
            if is_valid:
                draft.generated_text = optimized_text
            
            # Assess content quality (now includes SEO factors)
            quality_score = await self.quality_checker.assess_quality(draft, context)
            draft.quality_score = quality_score
            
            # Add SEO quality metrics
            if self.seo_optimizer:
                seo_score = self._calculate_seo_quality_score(draft, seo_suggestions)
                draft.generation_metadata["seo_quality_score"] = seo_score
            
            return draft
            
        except Exception as e:
            logger.error(f"Failed to process LLM response: {e}")
            return None
    
    def _calculate_seo_quality_score(self, draft: ContentDraft, 
                                   seo_suggestions: SEOSuggestions) -> float:
        """Calculate SEO quality score for the draft"""
        
        score = 0.0
        content_lower = draft.generated_text.lower()
        
        # Keyword integration score (30%)
        keywords_found = 0
        for keyword in seo_suggestions.keywords[:5]:
            if keyword.lower() in content_lower:
                keywords_found += 1
        
        if seo_suggestions.keywords:
            keyword_score = keywords_found / min(len(seo_suggestions.keywords), 5)
            score += keyword_score * 0.3
        
        # Hashtag utilization score (25%)
        hashtags_in_content = len([tag for tag in seo_suggestions.hashtags if f'#{tag}' in draft.generated_text])
        if seo_suggestions.hashtags:
            hashtag_score = hashtags_in_content / min(len(seo_suggestions.hashtags), 5)
            score += hashtag_score * 0.25
        
        # Length optimization score (20%)
        if seo_suggestions.optimal_length:
            length_diff = abs(len(draft.generated_text) - seo_suggestions.optimal_length)
            length_score = max(0, 1 - (length_diff / seo_suggestions.optimal_length))
            score += length_score * 0.2
        else:
            score += 0.2  # Assume optimal if no target length
        
        # Trending terms usage (15%)
        trending_found = 0
        for term in seo_suggestions.trending_tags:
            if term.lower() in content_lower:
                trending_found += 1
        
        if seo_suggestions.trending_tags:
            trending_score = trending_found / len(seo_suggestions.trending_tags)
            score += trending_score * 0.15
        
        # Structure and readability (10%)
        structure_score = 0.8  # Base score for well-formed content
        if '?' in draft.generated_text or '!' in draft.generated_text:
            structure_score += 0.2
        
        score += min(1.0, structure_score) * 0.1
        
        return min(1.0, score)
    
    def _convert_to_seo_content_type(self, content_type: ContentType) -> SEOContentType:
        """Convert ContentType to SEOContentType"""
        mapping = {
            ContentType.TWEET: SEOContentType.TWEET,
            ContentType.REPLY: SEOContentType.REPLY,
            ContentType.THREAD: SEOContentType.THREAD,
            ContentType.QUOTE_TWEET: SEOContentType.QUOTE_TWEET
        }
        return mapping.get(content_type, SEOContentType.TWEET)
    
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
                words = point.lower().split()
                keywords.extend([w for w in words if len(w) > 4])
        
        # Extract from product info
        product_info = context.product_info
        if product_info:
            category = product_info.get("industry_category", "")
            if category:
                hashtags.append(category.replace(" ", ""))
            
            core_values = product_info.get("core_values", [])
            keywords.extend(core_values[:2])
        
        # Content type specific suggestions
        if content_type == ContentType.TWEET:
            hashtags = hashtags[:3]
        elif content_type == ContentType.REPLY:
            hashtags = hashtags[:1]
        
        return SEOSuggestions(
            hashtags=list(set(hashtags))[:5],
            keywords=list(set(keywords))[:10],
            trending_tags=[],
            mentions=[]
        )
    
    def _attempt_content_fixes(self, text: str, issues: List[str]) -> str:
        """Attempt to fix common content issues"""
        fixed_text = text
        
        for issue in issues:
            if "exceeds" in issue and "characters" in issue:
                # Truncate text intelligently
                if len(fixed_text) > 280:
                    sentences = fixed_text.split('. ')
                    truncated = ""
                    for sentence in sentences:
                        if len(truncated + sentence + '. ') <= 275:
                            truncated += sentence + '. '
                        else:
                            break
                    
                    if truncated:
                        fixed_text = truncated.rstrip('. ') + "..."
                    else:
                        fixed_text = fixed_text[:277] + "..."
            
            elif "Too many hashtags" in issue:
                import re
                hashtags = re.findall(r'#\w+', fixed_text)
                if len(hashtags) > 5:
                    for hashtag in hashtags[3:]:
                        fixed_text = fixed_text.replace(hashtag, '', 1)
        
        return fixed_text.strip()

class ContentGenerationFactory:
    """Enhanced factory for creating content generators with SEO integration"""
    
    @staticmethod
    def create_enhanced_generator(llm_provider: str, llm_config: Dict[str, Any], 
                                seo_optimizer: SEOOptimizer = None) -> ContentGenerator:
        """Create enhanced content generator with SEO integration"""
        
        # Create LLM adapter
        llm_adapter = LLMAdapterFactory.create_adapter(llm_provider, **llm_config)
        
        # Create and return enhanced generator
        return ContentGenerator(llm_adapter, seo_optimizer)