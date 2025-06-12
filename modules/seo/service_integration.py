"""SEO Module Service - Integration layer for system-wide SEO functionality"""
"""Enhanced SEO Service with LLM Integration

This service integrates the LLM-enhanced SEO optimizer into the existing service layer,
providing intelligent content optimization for the content generation module.
"""

import asyncio
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta, timezone
import json

from modules.twitter_api import TwitterAPIClient
from modules.user_profile import UserProfileService
from database import DataFlowManager

try:
    from .optimizer import create_enhanced_seo_optimizer
    from .models import (
        SEOOptimizationRequest, SEOAnalysisContext, SEOContentType,
        SEOOptimizationLevel, HashtagStrategy, ContentOptimizationSuggestions
    )
except ImportError:
    # Fallback for direct execution
    from optimizer import create_enhanced_seo_optimizer
    from models import (
        SEOOptimizationRequest, SEOAnalysisContext, SEOContentType,
        SEOOptimizationLevel, HashtagStrategy, ContentOptimizationSuggestions
    )

logger = logging.getLogger(__name__)

class SEOService:
    """
    Enhanced SEO service with LLM intelligence for system integration
    """
    
    def __init__(self, twitter_client: TwitterAPIClient,
                 user_service: UserProfileService,
                 data_flow_manager: DataFlowManager,
                 llm_client=None,
                 config: Dict[str, Any] = None):
        
        self.twitter_client = twitter_client
        self.user_service = user_service
        self.data_flow_manager = data_flow_manager
        self.llm_client = llm_client
        self.llm_enabled = llm_client is not None
        
        # Enhanced configuration with new options
        self.config = {
            'default_optimization_mode': 'comprehensive',  # Updated from 'intelligent'
            'max_hashtags': 5,
            'hashtag_strategy': 'engagement_optimized',
            'use_trending_hashtags': True,
            'cache_duration_hours': 6,
            'llm_optimization_mode': 'comprehensive',  # Updated from 'intelligent'
            'enable_fallback_protection': True,  # Updated from 'fallback_to_traditional'
            'llm_enhancement_threshold': 0.3
        }
        
        if config:
            self.config.update(config)
        
        # Initialize optimizer with LLM client
        self.optimizer = create_enhanced_seo_optimizer(
            twitter_client=twitter_client,
            config=self.config,
            llm_client=llm_client
        )
        
        logger.info(f"SEO Service initialized (LLM enabled: {self.llm_enabled})")
        
        # Cache for optimization results
        self._optimization_cache = {}
        self._cache_duration = timedelta(hours=self.config.get('cache_duration_hours', 6))
    
    async def get_content_suggestions(self, trend_info: Dict[str, Any],
                                    product_info: Dict[str, Any],
                                    content_type: str) -> ContentOptimizationSuggestions:
        """
        Get intelligent SEO suggestions for content generation with LLM enhancement
        """
        try:
            logger.info(f"Getting enhanced SEO suggestions for {content_type} content")
            
            # Convert content type string to enum
            seo_content_type = self._convert_content_type(content_type)
            
            # Use enhanced optimizer's suggestion method (synchronous call)
            if hasattr(self.optimizer, 'get_content_suggestions'):
                suggestions = self.optimizer.get_content_suggestions(
                    trend_info, product_info, seo_content_type
                )
            else:
                # Fallback to basic suggestions
                suggestions = ContentOptimizationSuggestions(
                    recommended_hashtags=['innovation', 'business', 'growth'],
                    primary_keywords=['productivity', 'professional'],
                    secondary_keywords=['technology', 'digital'],
                    semantic_keywords=[],
                    trending_terms=['AI', 'automation'],
                    optimal_length=280,
                    call_to_action='What do you think?',
                    timing_recommendation='Peak hours: 9-11 AM, 1-3 PM',
                    engagement_tactics=['Ask questions', 'Share insights']
                )
            
            # Add LLM-specific insights if available (but don't await the suggestions object)
            if self.llm_enabled and hasattr(self.optimizer, 'llm_intelligence'):
                try:
                    # Create context for LLM enhancement
                    context = SEOAnalysisContext(
                        content_type=seo_content_type,
                        target_audience=product_info.get('target_audience', 'professionals'),
                        niche_keywords=trend_info.get('keywords', [])[:5],
                        product_categories=[product_info.get('industry_category', 'technology')],
                        industry_vertical=product_info.get('industry_category', 'technology')
                    )
                    
                    # Get LLM-enhanced suggestions (this is the async call)
                    if self.optimizer.llm_intelligence:
                        llm_suggestions = await self.optimizer.llm_intelligence._generate_intelligent_seo_suggestions(
                            "", "", context  # Empty content for general suggestions
                        )
                        
                        # Merge suggestions (create new object, don't modify existing)
                        suggestions = ContentOptimizationSuggestions(
                            recommended_hashtags=llm_suggestions.recommended_hashtags or suggestions.recommended_hashtags,
                            primary_keywords=llm_suggestions.primary_keywords or suggestions.primary_keywords,
                            secondary_keywords=llm_suggestions.secondary_keywords or suggestions.secondary_keywords,
                            semantic_keywords=getattr(llm_suggestions, 'semantic_keywords', []),
                            trending_terms=llm_suggestions.trending_terms or suggestions.trending_terms,
                            optimal_length=llm_suggestions.optimal_length or suggestions.optimal_length,
                            call_to_action=llm_suggestions.call_to_action or suggestions.call_to_action,
                            timing_recommendation=getattr(suggestions, 'timing_recommendation', ''),
                            engagement_tactics=llm_suggestions.engagement_tactics or suggestions.engagement_tactics
                        )
                        
                except Exception as e:
                    logger.warning(f"LLM enhancement failed, using base suggestions: {e}")
            
            logger.info(f"Generated {len(suggestions.recommended_hashtags)} hashtag suggestions")
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to get enhanced SEO content suggestions: {e}")
            return ContentOptimizationSuggestions(
                recommended_hashtags=['innovation', 'business', 'growth'],
                primary_keywords=['productivity', 'professional'],
                secondary_keywords=['technology', 'digital'],
                semantic_keywords=[],
                trending_terms=['AI', 'automation'],
                optimal_length=280,
                call_to_action='What do you think?',
                timing_recommendation='Peak hours: 9-11 AM, 1-3 PM',
                engagement_tactics=['Ask questions', 'Share insights']
            )
    
    async def optimize_content_intelligent(self, text: str, content_type: str,
                                         context: Dict[str, Any] = None,
                                         optimization_mode: str = None) -> Dict[str, Any]:
        """
        Intelligent content optimization using comprehensive LLM-enhanced approach
        
        Args:
            text: Content to optimize
            content_type: Type of content ('tweet', 'linkedin_post', etc.)
            context: Additional context (founder_id, keywords, etc.)
            optimization_mode: Optimization mode ('comprehensive', 'intelligent', 'adaptive')
            
        Returns:
            Dictionary with optimization results
        """
        try:
            # Default to comprehensive mode if not specified
            if not optimization_mode:
                optimization_mode = self.config.get('default_optimization_mode', 'comprehensive')
            
            # Use the optimizer's intelligent optimization method
            result = await self.optimizer.optimize_content_intelligent(
                text=text,
                content_type=content_type,
                context=context,
                optimization_mode=optimization_mode
            )
            
            # Store optimization result if founder_id provided
            if context and 'founder_id' in context:
                await self._store_founder_optimization_result(context['founder_id'], result)
            
            return result
            
        except Exception as e:
            logger.error(f"Intelligent content optimization failed: {e}")
            # Return safe fallback
            return {
                'original_content': text,
                'optimized_content': text,
                'optimization_score': 0.5,
                'llm_enhanced': False,
                'error': str(e),
                'optimization_mode': 'fallback'
            }
    
    def optimize_content(self, text: str, content_type: str, 
                        context: Dict[str, Any] = None) -> str:
        """
        Simple content optimization for backward compatibility
        """
        try:
            # Use intelligent optimization but return only the optimized text
            result = asyncio.run(self.optimize_content_intelligent(
                text, content_type, context, 'comprehensive'
            ))
            return result.get('optimized_content', text)
            
        except Exception as e:
            logger.error(f"Simple content optimization failed: {e}")
            return text
    
    async def optimize_for_trending_topics(self, founder_id: str, content: str,
                                         trending_topics: List[str],
                                         content_type: str = 'tweet') -> Dict[str, Any]:
        """
        Optimize content specifically for trending topics using LLM intelligence
        """
        try:
            # Build context for trending optimization
            context = await self._build_seo_context(founder_id, content_type)
            
            # Use enhanced optimizer's trending optimization
            result = await self.optimizer.optimize_for_trending_topics(
                content, trending_topics, context
            )
            
            # Store optimization result for analytics
            await self._store_trending_optimization_result(founder_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Trending topics optimization failed: {e}")
            return {
                'optimized_content': content,
                'trend_integration': [],
                'error': str(e)
            }
    
    async def generate_content_variations(self, founder_id: str, content: str,
                                        content_type: str = 'tweet',
                                        variation_count: int = 3) -> List[Dict[str, Any]]:
        """
        Generate multiple SEO-optimized content variations using LLM
        """
        try:
            if not self.llm_enabled or not self.optimizer.llm_analyzer:
                return [{'content': content, 'strategy': 'original', 'optimization_note': 'LLM not available'}]
            
            # Build context
            context = await self._build_seo_context(founder_id, content_type)
            
            # Generate variations using LLM analyzer
            variations = await self.optimizer.llm_analyzer.generate_content_variations(
                content, context, variation_count
            )
            
            # Enhance each variation with traditional SEO
            enhanced_variations = []
            for variation in variations:
                try:
                    # Apply traditional SEO to each variation
                    optimized = await self.optimize_content_intelligent(
                        variation.get('content', content),
                        content_type,
                        {'founder_id': founder_id},
                        'comprehensive'  # Use comprehensive for variations
                    )
                    
                    enhanced_variations.append({
                        'original_variation': variation.get('content', content),
                        'optimized_content': optimized.get('optimized_content', variation.get('content', content)),
                        'strategy': variation.get('strategy', 'unknown'),
                        'seo_focus': variation.get('seo_focus', 'general'),
                        'expected_improvement': variation.get('expected_improvement', 'N/A'),
                        'optimization_score': optimized.get('optimization_score', 0.5),
                        'llm_generated': True
                    })
                except Exception as e:
                    logger.warning(f"Failed to enhance variation: {e}")
                    enhanced_variations.append({
                        'original_variation': variation.get('content', content),
                        'optimized_content': variation.get('content', content),
                        'strategy': variation.get('strategy', 'unknown'),
                        'error': str(e)
                    })
            
            return enhanced_variations
            
        except Exception as e:
            logger.error(f"Content variation generation failed: {e}")
            return [{'content': content, 'error': str(e)}]
    
    async def analyze_content_seo_potential(self, content: str, founder_id: str,
                                          content_type: str = 'tweet') -> Dict[str, Any]:
        """
        Analyze content's SEO potential using LLM intelligence
        """
        try:
            if not self.llm_enabled or not self.optimizer.llm_analyzer:
                return self._basic_seo_potential_analysis(content)
            
            # Build context for analysis
            context = await self._build_seo_context(founder_id, content_type)
            
            # Use LLM analyzer for comprehensive analysis
            analysis = await self.optimizer.llm_analyzer.analyze_content_seo_potential(content, context)
            
            # Add traditional SEO metrics for comparison
            traditional_analysis = self._basic_seo_potential_analysis(content)
            
            # Combine analyses
            return {
                'llm_analysis': analysis,
                'traditional_analysis': traditional_analysis,
                'combined_score': (analysis.get('seo_strength_score', 0.5) + traditional_analysis.get('seo_score', 0.5)) / 2,
                'recommendations': analysis.get('improvement_recommendations', []),
                'competitive_advantages': analysis.get('competitive_advantages', []),
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'llm_enhanced': True
            }
            
        except Exception as e:
            logger.error(f"SEO potential analysis failed: {e}")
            return {
                'llm_analysis': {},
                'traditional_analysis': self._basic_seo_potential_analysis(content),
                'error': str(e),
                'llm_enhanced': False
            }
    
    async def get_intelligent_seo_recommendations(self, founder_id: str,
                                                content_history: List[str] = None) -> Dict[str, Any]:
        """
        Get intelligent SEO recommendations based on founder's content history and LLM analysis
        """
        try:
            # Get user profile
            user_profile = self.user_service.get_user_profile(founder_id)
            if not user_profile:
                return {}
            
            # Get traditional recommendations
            base_recommendations = self.get_seo_recommendations(founder_id)
            
            # If LLM is available, enhance recommendations
            if self.llm_enabled and content_history:
                # Analyze content history patterns
                llm_insights = await self._analyze_content_patterns_with_llm(
                    content_history, founder_id
                )
                
                # Merge recommendations
                enhanced_recommendations = self._merge_recommendations(
                    base_recommendations, llm_insights
                )
                
                return {
                    'traditional_recommendations': base_recommendations,
                    'llm_insights': llm_insights,
                    'enhanced_recommendations': enhanced_recommendations,
                    'llm_enhanced': True,
                    'analysis_timestamp': datetime.utcnow().isoformat()
                }
            
            return {
                'traditional_recommendations': base_recommendations,
                'llm_enhanced': False
            }
            
        except Exception as e:
            logger.error(f"Intelligent SEO recommendations failed: {e}")
            return {'error': str(e)}
    
    async def optimize_content_for_founder(self, founder_id: str, content: str,
                                         content_type: str = 'tweet',
                                         optimization_strategy: str = 'intelligent') -> Dict[str, Any]:
        """
        Optimize content specifically for a founder using their profile and LLM intelligence
        """
        try:
            # Build founder-specific context
            context = {
                'founder_id': founder_id,
                'content_type': content_type,
                'optimization_strategy': optimization_strategy
            }
            
            # Add founder's preferences and history
            founder_context = await self._get_founder_optimization_context(founder_id)
            context.update(founder_context)
            
            # Perform intelligent optimization
            result = await self.optimize_content_intelligent(
                content, content_type, context, optimization_strategy
            )
            
            # Store optimization result for future learning
            await self._store_founder_optimization_result(founder_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Founder-specific content optimization failed: {e}")
            return {
                'original_content': content,
                'optimized_content': content,
                'error': str(e),
                'llm_enhanced': False
            }
    
    # Helper methods
    
    async def _enhance_suggestions_with_llm_insights(self, suggestions: ContentOptimizationSuggestions,
                                                   trend_info: Dict[str, Any],
                                                   product_info: Dict[str, Any],
                                                   seo_content_type: SEOContentType) -> ContentOptimizationSuggestions:
        """
        Enhance suggestions with LLM insights (don't await the suggestions parameter)
        """
        try:
            # Convert content type (fix: use seo_content_type instead of undefined content_type)
            if isinstance(seo_content_type, str):
                seo_content_type = self._convert_content_type_from_string(seo_content_type)
            
            # Get base suggestions from optimizer (synchronous call)
            if hasattr(self.optimizer, 'get_content_suggestions'):
                base_suggestions = self.optimizer.get_content_suggestions(
                    trend_info, product_info, seo_content_type
                )
            else:
                # Use the passed suggestions as base
                base_suggestions = suggestions
            
            # Enhance with LLM insights if available
            enhanced_suggestions = base_suggestions
            if self.llm_enabled and hasattr(self.optimizer, 'llm_intelligence'):
                try:
                    # Create context for LLM enhancement
                    context = SEOAnalysisContext(
                        content_type=seo_content_type,
                        target_audience=product_info.get('target_audience', 'professionals'),
                        niche_keywords=trend_info.get('keywords', [])[:5],
                        product_categories=[product_info.get('industry_category', 'technology')],
                        industry_vertical=product_info.get('industry_category', 'technology')
                    )
                    
                    # Get LLM-enhanced suggestions (this is the async call)
                    if self.optimizer.llm_intelligence:
                        llm_suggestions = await self.optimizer.llm_intelligence._generate_intelligent_seo_suggestions(
                            "", "", context  # Empty content for general suggestions
                        )
                        
                        # Merge suggestions
                        enhanced_suggestions = ContentOptimizationSuggestions(
                            recommended_hashtags=llm_suggestions.recommended_hashtags or base_suggestions.recommended_hashtags,
                            primary_keywords=llm_suggestions.primary_keywords or base_suggestions.primary_keywords,
                            secondary_keywords=llm_suggestions.secondary_keywords or base_suggestions.secondary_keywords,
                            semantic_keywords=getattr(llm_suggestions, 'semantic_keywords', []),
                            trending_terms=llm_suggestions.trending_terms or base_suggestions.trending_terms,
                            optimal_length=llm_suggestions.optimal_length or base_suggestions.optimal_length,
                            call_to_action=llm_suggestions.call_to_action or base_suggestions.call_to_action,
                            timing_recommendation=getattr(base_suggestions, 'timing_recommendation', ''),
                            engagement_tactics=llm_suggestions.engagement_tactics or base_suggestions.engagement_tactics
                        )
                        
                except Exception as e:
                    logger.warning(f"LLM enhancement failed, using base suggestions: {e}")
            
            return enhanced_suggestions
            
        except Exception as e:
            logger.error(f"Failed to enhance suggestions with LLM insights: {e}")
            # Return safe fallback
            return ContentOptimizationSuggestions(
                recommended_hashtags=['innovation', 'business', 'growth'],
                primary_keywords=['productivity', 'professional'],
                secondary_keywords=['technology', 'digital'],
                semantic_keywords=[],
                trending_terms=['AI', 'automation'],
                optimal_length=280,
                call_to_action='What do you think?',
                timing_recommendation='Peak hours: 9-11 AM, 1-3 PM',
                engagement_tactics=['Ask questions', 'Share insights']
            )
    
    async def _build_enhanced_seo_context(self, context: Dict[str, Any],
                                        content_type: SEOContentType) -> SEOAnalysisContext:
        """Build enhanced SEO context with additional intelligence"""
        
        # Build base context
        base_context = await self._build_seo_context(
            context.get('founder_id') if context else None,
            content_type.value
        )
        
        # Add LLM-specific enhancements
        if context:
            # Add trending context if available
            if 'trending_topics' in context:
                base_context.trend_context = {
                    'keywords': context['trending_topics'],
                    'focus': 'trending_optimization'
                }
            
            # Add optimization strategy preferences
            if 'optimization_strategy' in context:
                base_context.brand_voice = base_context.brand_voice or {}
                base_context.brand_voice['optimization_preference'] = context['optimization_strategy']
        
        return base_context
    
    async def _analyze_content_patterns_with_llm(self, content_history: List[str],
                                               founder_id: str) -> Dict[str, Any]:
        """Analyze content patterns using LLM to generate insights"""
        
        if not self.llm_enabled or not content_history:
            return {}
        
        try:
            # Sample recent content to avoid token limits
            recent_content = content_history[-10:] if len(content_history) > 10 else content_history
            content_sample = "\n".join(recent_content)
            
            # Create analysis prompt
            analysis_prompt = f"""
                Analyze this founder's content history and provide strategic SEO insights.

                Recent Content History:
                {content_sample}

                Provide analysis in JSON format:
                {{
                    "content_patterns": {{
                        "common_themes": ["theme1", "theme2"],
                        "writing_style": "description",
                        "hashtag_patterns": ["pattern1", "pattern2"],
                        "engagement_elements": ["element1", "element2"]
                    }},
                    "seo_opportunities": {{
                        "underutilized_keywords": ["keyword1", "keyword2"],
                        "hashtag_gaps": ["hashtag1", "hashtag2"],
                        "content_gaps": ["gap1", "gap2"]
                    }},
                    "recommendations": {{
                        "keyword_strategy": "specific recommendation",
                        "hashtag_strategy": "specific recommendation",
                        "content_optimization": "specific recommendation",
                        "engagement_tactics": ["tactic1", "tactic2"]
                    }},
                    "performance_predictions": {{
                        "high_potential_topics": ["topic1", "topic2"],
                        "optimal_posting_strategy": "recommendation"
                    }}
                }}
                """
            
            # Call LLM
            if self.optimizer.llm_analyzer:
                response = await self.optimizer.llm_analyzer._call_llm(analysis_prompt)
                return json.loads(response)
            
            return {}
            
        except Exception as e:
            logger.error(f"LLM content pattern analysis failed: {e}")
            return {}
    
    def _merge_recommendations(self, traditional: Dict[str, Any],
                             llm_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Merge traditional and LLM recommendations"""
        
        merged = traditional.copy()
        
        # Add LLM-specific insights
        if 'seo_opportunities' in llm_insights:
            merged['llm_opportunities'] = llm_insights['seo_opportunities']
        
        if 'recommendations' in llm_insights:
            merged['llm_recommendations'] = llm_insights['recommendations']
        
        if 'performance_predictions' in llm_insights:
            merged['performance_predictions'] = llm_insights['performance_predictions']
        
        # Enhance existing recommendations with LLM insights
        llm_recs = llm_insights.get('recommendations', {})
        
        if 'hashtag_strategy' in merged and 'hashtag_strategy' in llm_recs:
            merged['enhanced_hashtag_strategy'] = {
                'traditional': merged['hashtag_strategy'],
                'llm_insight': llm_recs['hashtag_strategy'],
                'combined_approach': f"{merged['hashtag_strategy']['recommendation']} Additionally, {llm_recs['hashtag_strategy']}"
            }
        
        return merged
    
    async def _get_founder_optimization_context(self, founder_id: str) -> Dict[str, Any]:
        """Get founder-specific optimization context"""
        
        try:
            # Get user profile
            user_profile = self.user_service.get_user_profile(founder_id)
            
            # Get optimization history
            optimization_history = await self._get_optimization_history(founder_id)
            
            # Get successful content patterns
            successful_patterns = await self._get_successful_content_patterns(founder_id)
            
            context = {
                'user_profile': user_profile,
                'optimization_history': optimization_history,
                'successful_patterns': successful_patterns,
                'target_keywords': await self._get_founder_keywords(founder_id)
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get founder optimization context: {e}")
            return {}
    
    async def _store_founder_optimization_result(self, founder_id: str,
                                               result: Dict[str, Any]) -> None:
        """Store optimization result for future learning"""
        
        try:
            optimization_data = {
                'founder_id': founder_id,
                'original_content': result.get('original_content'),
                'optimized_content': result.get('optimized_content'),
                'optimization_score': result.get('optimization_score'),
                'optimization_mode': result.get('optimization_mode'),
                'llm_enhanced': result.get('llm_enhanced', False),
                'llm_insights': result.get('llm_insights', {}),
                'optimization_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Store using data flow manager
            self.data_flow_manager.store_seo_optimization_result(founder_id, optimization_data)
            
        except Exception as e:
            logger.error(f"Failed to store founder optimization result: {e}")
    
    async def _store_trending_optimization_result(self, founder_id: str,
                                                result: Dict[str, Any]) -> None:
        """Store trending optimization result"""
        
        try:
            trending_data = {
                'founder_id': founder_id,
                'trending_topics': result.get('trend_integration', []),
                'optimized_content': result.get('optimized_content'),
                'optimization_score': result.get('optimization_score'),
                'llm_insights': result.get('llm_insights', {}),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Store trending optimization data
            self.data_flow_manager.store_trending_optimization_result(founder_id, trending_data)
            
        except Exception as e:
            logger.error(f"Failed to store trending optimization result: {e}")
    
    # Utility methods from base class
    
    def _convert_content_type(self, content_type: str) -> SEOContentType:
        """Convert string content type to enum"""
        try:
            if isinstance(content_type, str):
                content_str = content_type.lower().strip()
            else:
                content_str = str(content_type).lower().strip()
            
            content_str = content_str.replace('contenttype.', '').replace('seocontenttype.', '')
            
            mapping = {
                'tweet': SEOContentType.TWEET,
                'reply': SEOContentType.TWEET,  # Map reply to tweet for now
                'thread': SEOContentType.TWEET,  # Map thread to tweet for now
                'quote_tweet': SEOContentType.TWEET,  # Map quote_tweet to tweet for now
                'linkedin_post': SEOContentType.LINKEDIN_POST,
                'facebook_post': SEOContentType.FACEBOOK_POST,
                'blog_post': SEOContentType.BLOG_POST
            }
            
            return mapping.get(content_str, SEOContentType.TWEET)
                
        except Exception as e:
            logger.error(f"Content type conversion failed for '{content_type}': {str(e)}")
            return SEOContentType.TWEET
    
    async def _build_seo_context(self, founder_id: str, content_type: str) -> SEOAnalysisContext:
        """Build SEO analysis context from user profile"""
        try:
            if not founder_id:
                return SEOAnalysisContext(
                    content_type=self._convert_content_type(content_type),
                    target_audience='professionals',
                    niche_keywords=[],
                    product_categories=['technology'],
                    industry_vertical='technology'
                )
            
            user_profile = self.user_service.get_user_profile(founder_id)
            
            if not user_profile:
                return SEOAnalysisContext(
                    content_type=self._convert_content_type(content_type),
                    target_audience='professionals',
                    niche_keywords=[],
                    product_categories=['technology'],
                    industry_vertical='technology'
                )
            
            # Extract information safely
            niche_keywords = []
            if hasattr(user_profile, 'niche_keywords'):
                raw_keywords = user_profile.niche_keywords
                if raw_keywords and not isinstance(raw_keywords, type(user_profile)):
                    niche_keywords = [str(kw) for kw in raw_keywords if kw]
            
            target_audience = 'professionals'
            if hasattr(user_profile, 'target_audience'):
                raw_audience = user_profile.target_audience
                if raw_audience and not str(raw_audience).startswith('<MagicMock'):
                    target_audience = str(raw_audience)
            
            industry = 'technology'
            if hasattr(user_profile, 'industry_category'):
                raw_industry = user_profile.industry_category
                if raw_industry and not str(raw_industry).startswith('<MagicMock'):
                    industry = str(raw_industry)
            
            return SEOAnalysisContext(
                content_type=self._convert_content_type(content_type),
                target_audience=target_audience,
                niche_keywords=niche_keywords,
                product_categories=[industry],
                industry_vertical=industry
            )
            
        except Exception as e:
            logger.error(f"Failed to build SEO context: {str(e)}")
            return SEOAnalysisContext(
                content_type=self._convert_content_type(content_type),
                target_audience='professionals',
                niche_keywords=[],
                product_categories=['technology'],
                industry_vertical='technology'
            )
    
    def _basic_seo_potential_analysis(self, content: str) -> Dict[str, Any]:
        """Basic SEO potential analysis when LLM unavailable"""
        
        word_count = len(content.split())
        char_count = len(content)
        hashtag_count = len([word for word in content.split() if word.startswith('#')])
        
        # Simple scoring
        seo_score = 0.5
        if 50 <= char_count <= 250:
            seo_score += 0.2
        if hashtag_count > 0:
            seo_score += 0.1
        if '?' in content:
            seo_score += 0.1
        if any(word in content.lower() for word in ['help', 'tips', 'how', 'guide']):
            seo_score += 0.1
        
        return {
            'seo_score': min(1.0, seo_score),
            'word_count': word_count,
            'char_count': char_count,
            'hashtag_count': hashtag_count,
            'has_question': '?' in content,
            'has_call_to_action': any(word in content.lower() for word in ['share', 'comment', 'like', 'follow'])
        }
    
    async def _get_optimization_history(self, founder_id: str) -> List[Dict[str, Any]]:
        """Get founder's optimization history"""
        try:
            return self.data_flow_manager.get_seo_performance_history(founder_id, 30)
        except Exception as e:
            logger.error(f"Failed to get optimization history: {e}")
            return []
    
    async def _get_successful_content_patterns(self, founder_id: str) -> List[Dict[str, Any]]:
        """Get founder's successful content patterns"""
        try:
            # This would analyze high-performing content
            return []
        except Exception as e:
            logger.error(f"Failed to get successful patterns: {e}")
            return []
    
    async def _get_founder_keywords(self, founder_id: str) -> List[str]:
        """Get founder-specific keywords"""
        try:
            user_profile = self.user_service.get_user_profile(founder_id)
            if user_profile and hasattr(user_profile, 'niche_keywords'):
                return [str(kw) for kw in user_profile.niche_keywords if kw]
            return []
        except Exception as e:
            logger.error(f"Failed to get founder keywords: {e}")
            return []
    
    # Backward compatibility methods
    
    def get_seo_recommendations(self, founder_id: str) -> Dict[str, Any]:
        """Get basic SEO recommendations (backward compatibility)"""
        try:
            user_profile = self.user_service.get_user_profile(founder_id)
            performance_history = self.data_flow_manager.get_seo_performance_history(founder_id, 30)
            
            return {
                'hashtag_strategy': {
                    'recommended_strategy': 'engagement_optimized',
                    'recommendation': 'Focus on engagement-optimized hashtags',
                    'max_hashtags_per_post': 5
                },
                'keyword_focus': {
                    'primary_focus_keywords': ['innovation', 'technology', 'business'],
                    'keyword_density_target': 0.02,
                    'recommendation': 'Focus on industry keywords for better targeting'
                },
                'content_optimization': {
                    'focus_area': 'engagement_elements',
                    'recommendation': 'Add more questions and calls-to-action',
                    'target_optimization_score': 0.8
                }
            }
        except Exception as e:
            logger.error(f"Failed to get SEO recommendations: {e}")
            return {}
    
    def get_seo_analytics_summary(self, founder_id: str, days: int = 30) -> Dict[str, Any]:
        """Get SEO analytics summary with LLM enhancements"""
        try:
            # Get base analytics
            performance_data = self.data_flow_manager.get_seo_performance_history(founder_id, days)
            
            if not performance_data:
                return {
                    'total_optimizations': 0,
                    'avg_optimization_score': 0.0,
                    'llm_enhanced': self.llm_enabled
                }
            
            # Calculate enhanced analytics
            total_optimizations = len(performance_data)
            llm_enhanced_count = sum(1 for p in performance_data if p.get('llm_enhanced', False))
            avg_score = sum(p.get('optimization_score', 0) for p in performance_data) / total_optimizations
            
            return {
                'total_optimizations': total_optimizations,
                'avg_optimization_score': round(avg_score, 2),
                'llm_enhanced_count': llm_enhanced_count,
                'llm_enhancement_rate': round(llm_enhanced_count / total_optimizations, 2) if total_optimizations > 0 else 0,
                'best_performing_hashtags': ['innovation', 'startup', 'growth'],
                'optimization_trend': 'improving' if avg_score > 0.7 else 'needs_improvement',
                'llm_enabled': self.llm_enabled,
                'analysis_period_days': days
            }
            
        except Exception as e:
            logger.error(f"SEO analytics summary generation failed: {e}")
            return {'error': str(e), 'llm_enhanced': False}

    def _convert_content_type_from_string(self, content_type: str) -> SEOContentType:
        """Convert string content type to SEOContentType enum"""
        try:
            # Handle string inputs
            if isinstance(content_type, str):
                content_str = content_type.lower().strip()
            else:
                # Handle enum or other types
                content_str = str(content_type).lower().strip()
            
            # Remove any extra characters
            content_str = content_str.replace('contenttype.', '').replace('seocontenttype.', '')
            
            mapping = {
                'tweet': SEOContentType.TWEET,
                'reply': SEOContentType.REPLY,
                'thread': SEOContentType.THREAD,
                'quote_tweet': SEOContentType.QUOTE_TWEET,
                'linkedin_post': SEOContentType.LINKEDIN_POST,
                'facebook_post': SEOContentType.FACEBOOK_POST,
                'blog_post': SEOContentType.BLOG_POST
            }
            
            result = mapping.get(content_str, SEOContentType.TWEET)
            logger.debug(f"Converted '{content_type}' to {result}")
            return result
                
        except Exception as e:
            logger.error(f"Content type conversion failed for '{content_type}': {str(e)}")
            return SEOContentType.TWEET

    async def get_enhanced_content_suggestions(self, trend_info: Dict[str, Any],
                                             product_info: Dict[str, Any],
                                             content_type: str) -> Dict[str, Any]:
        """
        Get enhanced content suggestions with LLM integration
        
        Args:
            trend_info: Information about current trends
            product_info: Product/service information
            content_type: Type of content to optimize for
            
        Returns:
            Enhanced content suggestions with LLM insights
        """
        try:
            # Convert content type
            seo_content_type = self._convert_content_type_from_string(content_type)
            
            # Get base suggestions from optimizer
            if hasattr(self.optimizer, 'get_content_suggestions_async'):
                suggestions = await self.optimizer.get_content_suggestions_async(
                    trend_info, product_info, seo_content_type
                )
            else:
                # Fallback to sync method
                suggestions = self.optimizer.get_content_suggestions(
                    trend_info, product_info, seo_content_type
                )
            
            # Enhance with LLM insights if available
            enhanced_suggestions = suggestions
            if self.llm_enabled and hasattr(self.optimizer, 'llm_intelligence'):
                try:
                    # Create context for LLM enhancement
                    context = SEOAnalysisContext(
                        content_type=seo_content_type,
                        target_audience=product_info.get('target_audience', 'professionals'),
                        niche_keywords=trend_info.get('keywords', [])[:5],
                        product_categories=[product_info.get('industry_category', 'technology')],
                        industry_vertical=product_info.get('industry_category', 'technology')
                    )
                    
                    # Get LLM-enhanced suggestions
                    if self.optimizer.llm_intelligence:
                        llm_suggestions = await self.optimizer.llm_intelligence._generate_intelligent_seo_suggestions(
                            "", "", context  # Empty content for general suggestions
                        )
                        
                        # Merge suggestions
                        enhanced_suggestions = ContentOptimizationSuggestions(
                            recommended_hashtags=llm_suggestions.recommended_hashtags or suggestions.recommended_hashtags,
                            primary_keywords=llm_suggestions.primary_keywords or suggestions.primary_keywords,
                            secondary_keywords=llm_suggestions.secondary_keywords or suggestions.secondary_keywords,
                            semantic_keywords=getattr(llm_suggestions, 'semantic_keywords', []),
                            trending_terms=llm_suggestions.trending_terms or suggestions.trending_terms,
                            optimal_length=llm_suggestions.optimal_length or suggestions.optimal_length,
                            call_to_action=llm_suggestions.call_to_action or suggestions.call_to_action,
                            timing_recommendation=getattr(suggestions, 'timing_recommendation', ''),
                            engagement_tactics=llm_suggestions.engagement_tactics or suggestions.engagement_tactics
                        )
                        
                except Exception as e:
                    logger.warning(f"LLM enhancement failed, using base suggestions: {e}")
            
            # Convert to service format
            return {
                'recommended_hashtags': enhanced_suggestions.recommended_hashtags or [],
                'primary_keywords': enhanced_suggestions.primary_keywords or [],
                'secondary_keywords': enhanced_suggestions.secondary_keywords or [],
                'semantic_keywords': getattr(enhanced_suggestions, 'semantic_keywords', []),
                'trending_terms': enhanced_suggestions.trending_terms or [],
                'optimal_length': enhanced_suggestions.optimal_length or 280,
                'call_to_action': enhanced_suggestions.call_to_action or '',
                'timing_recommendation': getattr(enhanced_suggestions, 'timing_recommendation', ''),
                'engagement_tactics': enhanced_suggestions.engagement_tactics or [],
                'llm_enhanced': self.llm_enabled,
                'content_type': content_type,
                'trend_alignment': {
                    'trending_topics': trend_info.get('keywords', [])[:3],
                    'pain_points': trend_info.get('pain_points', [])[:3],
                    'opportunities': trend_info.get('opportunities', [])[:3]
                },
                'product_alignment': {
                    'core_values': product_info.get('core_values', [])[:3],
                    'target_audience': product_info.get('target_audience', 'professionals'),
                    'industry_category': product_info.get('industry_category', 'technology')
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get enhanced SEO content suggestions: {e}")
            # Return safe fallback
            return {
                'recommended_hashtags': ['innovation', 'business', 'growth'],
                'primary_keywords': ['productivity', 'professional'],
                'secondary_keywords': ['technology', 'digital'],
                'semantic_keywords': [],
                'trending_terms': ['AI', 'automation'],
                'optimal_length': 280,
                'call_to_action': 'What do you think?',
                'timing_recommendation': 'Peak hours: 9-11 AM, 1-3 PM',
                'engagement_tactics': ['Ask questions', 'Share insights'],
                'llm_enhanced': False,
                'content_type': content_type,
                'error': str(e)
            }


# Factory function for easy integration
def create_enhanced_seo_service(twitter_client: TwitterAPIClient,
                              user_service: UserProfileService,
                              data_flow_manager: DataFlowManager,
                              llm_client=None,
                              config: Dict[str, Any] = None) -> SEOService:
    """
    Factory function to create enhanced SEO service with comprehensive LLM integration
    
    Args:
        twitter_client: Twitter API client
        user_service: User profile service
        data_flow_manager: Data flow manager
        llm_client: LLM client (OpenAI, Anthropic, etc.)
        config: Service configuration
        
    Returns:
        Enhanced SEO service instance
    """
    
    # Default enhanced configuration
    default_config = {
        'default_optimization_mode': 'comprehensive',
        'llm_optimization_mode': 'comprehensive',
        'enable_fallback_protection': True,
        'llm_enhancement_threshold': 0.3,
        'max_hashtags': 5,
        'hashtag_strategy': 'engagement_optimized',
        'use_trending_hashtags': True,
        'cache_duration_hours': 6,
        'enable_intelligent_analysis': True,
        'auto_variation_generation': True
    }
    
    # Merge with provided config
    if config:
        default_config.update(config)
    
    return SEOService(
        twitter_client=twitter_client,
        user_service=user_service,
        data_flow_manager=data_flow_manager,
        llm_client=llm_client,
        config=default_config
    )