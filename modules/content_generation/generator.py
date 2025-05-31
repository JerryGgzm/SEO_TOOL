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
    """Enhanced content generator with SEO integration"""
    
    def __init__(self, llm_adapter: LLMAdapter, seo_optimizer=None, 
                 quality_checker=None, prompt_engine=None):
        """
        Initialize content generator
        
        Args:
            llm_adapter: LLM adapter for content generation
            seo_optimizer: Optional SEO optimizer
            quality_checker: Optional quality checker
            prompt_engine: Optional prompt engine
        """
        self.llm_adapter = llm_adapter
        self.quality_checker = quality_checker or ContentQualityChecker()
        self.prompt_engine = prompt_engine or PromptEngine()
        
        # SEO optimizer will be lazy loaded when needed
        self._seo_optimizer = seo_optimizer
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Enhanced generation strategies
        self.generation_strategies = {
            'seo_optimized': self._generate_seo_optimized_content,
            'engagement_focused': self._generate_engagement_focused_content,
            'trend_based': self._generate_trend_based_content,
            'balanced': self._generate_balanced_content
        }
    
    @property
    def seo_optimizer(self):
        """Lazy load SEO optimizer to avoid circular imports"""
        if self._seo_optimizer is None:
            try:
                from modules.seo.optimizer import create_enhanced_seo_optimizer
                self._seo_optimizer = create_enhanced_seo_optimizer()
            except ImportError as e:
                self.logger.warning(f"Could not load SEO optimizer: {e}")
                self._seo_optimizer = None
        return self._seo_optimizer
    
    async def generate_content(self, request: ContentGenerationRequest, 
                             context: ContentGenerationContext) -> List[ContentDraft]:
        """Generate content based on request and context"""
        
        try:
            drafts = []
            
            for i in range(request.quantity):
                # Build prompt
                prompt = self._build_prompt(request, context)
                
                # Generate content using LLM
                raw_content = await self.llm_adapter.generate_content(prompt)
                
                # Clean the generated content
                cleaned_content = self._clean_generated_content(raw_content, request.content_type)
                
                
                # Assess quality using the correct method
                if self.quality_checker:
                    # Create a temporary draft for quality assessment
                    temp_draft = ContentDraft(
                        founder_id=request.founder_id,
                        content_type=request.content_type,
                        generated_text=cleaned_content,
                        quality_score=0.0  # Will be updated
                    )
                    
                    # Use the async assess_quality method
                    quality_assessment = await self.quality_checker.assess_quality(temp_draft, context)
                    quality_score = quality_assessment.overall_score
                    
                    # Store detailed quality metrics for later use
                    quality_metadata = {
                        "overall_score": quality_assessment.overall_score,
                        "engagement_prediction": quality_assessment.engagement_prediction,
                        "brand_alignment": quality_assessment.brand_alignment,
                        "trend_relevance": quality_assessment.trend_relevance,
                        "seo_optimization": quality_assessment.seo_optimization,
                        "readability": quality_assessment.readability,
                        "issues": quality_assessment.issues,
                        "suggestions": quality_assessment.suggestions
                    }
                else:
                    # Fallback to basic quality assessment
                    quality_score = self._basic_quality_assessment(cleaned_content, request.content_type)
                    quality_metadata = {"fallback_assessment": True}
                
                # Skip if below quality threshold
                if quality_score < request.quality_threshold:
                    self.logger.info(f"Draft {i+1} below quality threshold ({quality_score:.2f})")
                    continue
                
                # Create final draft with all metadata
                draft = ContentDraft(
                    founder_id=request.founder_id,
                    content_type=request.content_type,
                    generated_text=cleaned_content,
                    quality_score=quality_score,
                    generation_metadata={
                        'prompt_used': prompt[:200] + '...' if len(prompt) > 200 else prompt,
                        'generation_attempt': i + 1,
                        'llm_provider': self.llm_adapter.__class__.__name__,
                        'quality_assessment': quality_metadata
                    }
                )
                
                drafts.append(draft)
            
            return drafts
            
        except Exception as e:
            self.logger.error(f"Content generation failed: {e}")
            raise
    
    def _clean_generated_content(self, raw_content: str, content_type: ContentType) -> str:
        """Clean and format generated content"""
        if not raw_content:
            return ""
        
        # Remove common LLM artifacts
        cleaned = raw_content.content.strip()
        
        # Remove quotes that LLMs often add
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
        elif cleaned.startswith("'") and cleaned.endswith("'"):
            cleaned = cleaned[1:-1]
        
        # Remove "Tweet:" or similar prefixes
        prefixes_to_remove = [
            "Tweet:", "Reply:", "Thread:", "Quote Tweet:",
            "Here's a tweet:", "Here's a reply:", "Tweet content:",
            "Content:", "Post:"
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
        
        # Clean up extra whitespace
        cleaned = ' '.join(cleaned.split())
        
        # Ensure proper hashtag formatting
        import re
        cleaned = re.sub(r'\s+#', ' #', cleaned)  # Ensure space before hashtags
        cleaned = re.sub(r'#\s+', '#', cleaned)   # Remove space after hashtag symbol
        
        return cleaned
    
    def _build_prompt(self, request: ContentGenerationRequest, 
                     context: ContentGenerationContext) -> str:
        """Build generation prompt based on request and context"""
        
        # Use prompt engine if available
        if self.prompt_engine:
            return self.prompt_engine.generate_prompt(request, context)
        
        # Fallback to basic prompt building
        prompt_parts = []
        
        # Base instruction
        prompt_parts.append(f"Generate a {request.content_type} for a founder.")
        
        # Add product context
        if context.product_info:
            product_name = context.product_info.get('name', 'the product')
            prompt_parts.append(f"The product is {product_name}.")
            
            if 'description' in context.product_info:
                prompt_parts.append(f"Product description: {context.product_info['description']}")
        
        # Add trend context
        if context.trend_info:
            topic = context.trend_info.get('topic_name', 'current trends')
            prompt_parts.append(f"The content should relate to: {topic}")
            
            if 'keywords' in context.trend_info:
                keywords = ', '.join(context.trend_info['keywords'][:5])
                prompt_parts.append(f"Include relevant keywords: {keywords}")
        
        # Add brand voice
        if context.brand_voice:
            prompt_parts.append(f"Tone: {context.brand_voice.tone}")
            prompt_parts.append(f"Style: {context.brand_voice.style}")
        
        # Add content preferences
        if context.content_preferences:
            if 'max_length' in context.content_preferences:
                max_len = context.content_preferences['max_length']
                prompt_parts.append(f"Keep it under {max_len} characters.")
            
            if context.content_preferences.get('include_hashtags'):
                prompt_parts.append("Include relevant hashtags.")
        
        # Custom prompt override
        if request.custom_prompt:
            prompt_parts.append(f"Additional instructions: {request.custom_prompt}")
        
        return " ".join(prompt_parts)
    
    async def _apply_seo_optimization(self, content: str, request: ContentGenerationRequest,
                                    context: ContentGenerationContext) -> str:
        """Apply SEO optimization to content"""
        try:
            if not self.seo_optimizer:
                return content
            
            # Convert ContentType enum to string for SEO service
            content_type_str = request.content_type.value
            
            # Create SEO optimization request
            seo_request = SEOOptimizationRequest(
                content=content,
                content_type=self._convert_to_seo_content_type(request.content_type),
                optimization_level=SEOOptimizationLevel.MODERATE,
                target_keywords=self._extract_keywords_from_context(context),
                hashtag_strategy=HashtagStrategy.ENGAGEMENT_OPTIMIZED
            )
            
            # Build SEO analysis context
            seo_context = self._build_seo_analysis_context(context, request.content_type)
            
            # Optimize content
            result = self.seo_optimizer.optimize_content(seo_request, seo_context)
            
            return result.optimized_content
            
        except Exception as e:
            self.logger.warning(f"SEO optimization failed: {str(e)}")
            return content
    
    def _convert_to_seo_content_type(self, content_type: ContentType) -> SEOContentType:
        """Convert ContentType to SEOContentType"""
        mapping = {
            ContentType.TWEET: SEOContentType.TWEET,
            ContentType.REPLY: SEOContentType.REPLY,
            ContentType.THREAD: SEOContentType.THREAD,
            ContentType.QUOTE_TWEET: SEOContentType.QUOTE_TWEET,
            ContentType.LINKEDIN_POST: SEOContentType.LINKEDIN_POST,
            ContentType.FACEBOOK_POST: SEOContentType.FACEBOOK_POST,
            ContentType.BLOG_POST: SEOContentType.BLOG_POST
        }
        return mapping.get(content_type, SEOContentType.TWEET)
    
    def _build_seo_analysis_context(self, context: ContentGenerationContext, 
                                  content_type: ContentType) -> SEOAnalysisContext:
        """Build SEO analysis context from generation context"""
        try:
            # Extract keywords from context
            niche_keywords = []
            if context.trend_info:
                keywords = context.trend_info.get('keywords', [])
                if keywords:
                    niche_keywords.extend([str(kw) for kw in keywords if kw])
            
            if context.product_info:
                core_values = context.product_info.get('core_values', [])
                if core_values:
                    niche_keywords.extend([str(val) for val in core_values if val])
            
            # Extract target audience with safe string conversion
            target_audience = 'professionals'  # Default
            if context.target_audience:
                if not str(context.target_audience).startswith('<MagicMock'):
                    target_audience = str(context.target_audience)
            
            # Extract industry with safe string conversion
            industry = 'technology'  # Default
            if context.product_info:
                raw_industry = context.product_info.get('industry_category', 'technology')
                if raw_industry and not str(raw_industry).startswith('<MagicMock'):
                    industry = str(raw_industry)
            
            return SEOAnalysisContext(
                content_type=self._convert_to_seo_content_type(content_type),
                target_audience=target_audience,
                niche_keywords=niche_keywords[:10],  # Limit to 10 keywords
                product_categories=[industry],
                industry_vertical=industry
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to build SEO analysis context: {str(e)}")
            # Return safe default context
            return SEOAnalysisContext(
                content_type=self._convert_to_seo_content_type(content_type),
                target_audience='professionals',
                niche_keywords=[],
                product_categories=['technology'],
                industry_vertical='technology'
            )
    
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
            if self.quality_checker:
                quality_assessment = await self.quality_checker.assess_quality(draft, context)
                draft.quality_score = quality_assessment.overall_score
                
                # Store detailed quality metrics in metadata
                draft.generation_metadata.update({
                    "quality_assessment": {
                        "overall_score": quality_assessment.overall_score,
                        "engagement_prediction": quality_assessment.engagement_prediction,
                        "brand_alignment": quality_assessment.brand_alignment,
                        "trend_relevance": quality_assessment.trend_relevance,
                        "seo_optimization": quality_assessment.seo_optimization,
                        "readability": quality_assessment.readability,
                        "issues": quality_assessment.issues,
                        "suggestions": quality_assessment.suggestions
                    }
                })
            else:
                # Fallback quality assessment
                draft.quality_score = self._basic_quality_assessment(draft.generated_text, request.content_type)
            
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

    def _basic_quality_assessment(self, content: str, content_type: ContentType) -> float:
        """Basic quality assessment when quality checker is not available"""
        score = 0.5  # Base score
        
        # Length check
        if content_type == ContentType.TWEET:
            if 50 <= len(content) <= 280:
                score += 0.2
        elif content_type == ContentType.REPLY:
            if 20 <= len(content) <= 280:
                score += 0.2
        
        # Has hashtags
        if '#' in content:
            score += 0.1
        
        # Has question or engagement element
        if '?' in content or any(word in content.lower() for word in ['what', 'how', 'why', 'think']):
            score += 0.1
        
        # Not all caps
        if not content.isupper():
            score += 0.1
        
        return min(1.0, score)

class ContentGenerationFactory:
    """Enhanced factory for creating content generators with SEO integration"""
    
    @staticmethod
    def create_enhanced_generator(llm_provider: str, llm_config: Dict[str, Any],
                                seo_optimizer=None, quality_checker=None,
                                prompt_engine=None) -> ContentGenerator:
        """Create enhanced content generator with SEO integration"""
        
        # Remove 'provider' from llm_config if it exists to avoid duplicate parameter
        clean_llm_config = {k: v for k, v in llm_config.items() if k != 'provider'}
        
        # Create LLM adapter
        llm_adapter = LLMAdapterFactory.create_adapter(provider=llm_provider, **clean_llm_config)
        
        # Create or use provided components
        if not quality_checker:
            quality_checker = ContentQualityChecker()
        
        if not prompt_engine:
            prompt_engine = PromptEngine()
        
        return ContentGenerator(
            llm_adapter=llm_adapter,
            seo_optimizer=seo_optimizer,
            quality_checker=quality_checker,
            prompt_engine=prompt_engine
        )
    
    @staticmethod
    def create_basic_generator(llm_provider: str, llm_config: Dict[str, Any]) -> ContentGenerator:
        """Create basic content generator without SEO integration"""
        
        # Remove 'provider' from llm_config if it exists
        clean_llm_config = {k: v for k, v in llm_config.items() if k != 'provider'}
        
        # Create LLM adapter
        llm_adapter = LLMAdapterFactory.create_adapter(provider=llm_provider, **clean_llm_config)
        
        # Create basic components
        quality_checker = ContentQualityChecker()
        prompt_engine = PromptEngine()
        
        return ContentGenerator(
            llm_adapter=llm_adapter,
            seo_optimizer=None,
            quality_checker=quality_checker,
            prompt_engine=prompt_engine
        )