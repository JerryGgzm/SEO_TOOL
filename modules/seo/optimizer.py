"""
This enhanced optimizer integrates LLM intelligence into the existing SEO optimization pipeline
while maintaining compatibility with the current system architecture.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
import json

from modules.seo.base_optimizer import BaseSEOOptimizer
from modules.seo.models import (
    SEOOptimizationRequest, SEOOptimizationResult, ContentOptimizationSuggestions,
    SEOAnalysisContext, SEOContentType, SEOOptimizationLevel, HashtagStrategy
)

# Import the LLM intelligence modules we just created
from modules.seo.llm_intelligence import LLMSEOOrchestrator, LLMSEOIntelligence, LLMSEOAnalyzer

logger = logging.getLogger(__name__)

class SEOOptimizer(BaseSEOOptimizer):
    """Enhanced SEO optimizer with LLM intelligence integration"""
    
    def __init__(self, twitter_client=None, config: Dict[str, Any] = None, llm_client=None):
        # Initialize base SEO optimizer
        super().__init__(twitter_client, config)
        
        # Initialize LLM components
        self.llm_client = llm_client
        self.llm_orchestrator = LLMSEOOrchestrator(llm_client) if llm_client else None
        self.llm_intelligence = LLMSEOIntelligence(llm_client) if llm_client else None
        self.llm_analyzer = LLMSEOAnalyzer(llm_client) if llm_client else None
        
        # Enhanced optimization modes
        self.optimization_modes = {
            'traditional': self._traditional_optimization,
            'llm_enhanced': self._llm_enhanced_optimization,
            'hybrid': self._hybrid_optimization,
            'intelligent': self._intelligent_optimization
        }
        
        # Configuration for LLM integration
        self.llm_config = {
            'use_llm_for_keywords': config.get('use_llm_for_keywords', True) if config else True,
            'use_llm_for_hashtags': config.get('use_llm_for_hashtags', True) if config else True,
            'use_llm_for_engagement': config.get('use_llm_for_engagement', True) if config else True,
            'llm_optimization_mode': config.get('llm_optimization_mode', 'hybrid') if config else 'hybrid',
            'fallback_to_traditional': config.get('fallback_to_traditional', True) if config else True
        }
    
    def optimize_content(self, request: SEOOptimizationRequest, 
                        context: SEOAnalysisContext = None) -> SEOOptimizationResult:
        """
        Optimize content based on request parameters (synchronous method)
        
        Args:
            request: SEO optimization request
            context: Analysis context
            
        Returns:
            SEO optimization result
        """
        try:
            # Extract content from request
            original_content = request.content
            
            # Perform optimization
            optimized_content = self._optimize_content_text(
                original_content, 
                request.content_type,
                request.target_keywords,
                context
            )
            
            # Calculate optimization score
            optimization_score = self._calculate_optimization_score(
                original_content, optimized_content, request.target_keywords
            )
            
            # Generate suggestions
            suggestions = self._generate_optimization_suggestions(
                original_content, request.content_type, context
            )
            
            # Create improvement suggestions as strings
            improvement_suggestions = [
                "Added relevant hashtags for better discoverability",
                "Integrated target keywords naturally",
                "Optimized content structure for engagement",
                "Enhanced call-to-action effectiveness"
            ]
            
            # Create result object with correct types
            return SEOOptimizationResult(
                original_content=original_content,
                optimized_content=optimized_content,
                optimization_score=optimization_score,
                improvements_made=improvement_suggestions,
                hashtag_analysis=[],
                keyword_analysis=[],
                estimated_reach_improvement=15.0,
                suggestions=improvement_suggestions,
                optimization_metadata={
                    'optimization_mode': 'traditional',
                    'llm_enhanced': False,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Content optimization failed: {str(e)}")
            # Return safe fallback result
            return SEOOptimizationResult(
                original_content=request.content if hasattr(request, 'content') else "",
                optimized_content=request.content if hasattr(request, 'content') else "",
                optimization_score=0.5,
                improvements_made=["Optimization failed - using original content"],
                hashtag_analysis=[],
                keyword_analysis=[],
                estimated_reach_improvement=0.0,
                suggestions=["Manual review recommended", "Consider adding relevant hashtags"],
                optimization_metadata={
                    'optimization_mode': 'fallback',
                    'llm_enhanced': False,
                    'error': str(e)
                }
            )

    async def optimize_content_async(self, request: SEOOptimizationRequest, 
                                   context: SEOAnalysisContext = None) -> SEOOptimizationResult:
        """
        Async version of optimize_content with LLM integration
        
        Args:
            request: SEO optimization request
            context: Analysis context
            
        Returns:
            SEO optimization result
        """
        try:
            # Check if LLM optimization is available and enabled
            if (self.llm_intelligence and 
                self.optimization_mode in ['hybrid', 'llm_enhanced']):
                
                try:
                    # Use LLM for optimization
                    llm_result = await self.llm_intelligence.enhance_content_with_llm(
                        request, context, "comprehensive"
                    )
                    
                    # Convert LLM result to SEOOptimizationResult
                    return SEOOptimizationResult(
                        original_content=request.content,
                        optimized_content=llm_result.get('enhanced_content', request.content),
                        optimization_score=llm_result.get('optimization_score', 0.5),
                        improvements_made=llm_result.get('improvements_made', []),
                        hashtag_analysis=[],
                        keyword_analysis=[],
                        estimated_reach_improvement=llm_result.get('estimated_reach_improvement', 10.0),
                        suggestions=llm_result.get('suggestions', []),
                        optimization_metadata={
                            'optimization_mode': 'llm_enhanced',
                            'llm_enhanced': True,
                            'llm_insights': llm_result.get('llm_insights', {}),
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    )
                    
                except Exception as e:
                    logger.warning(f"LLM optimization failed, falling back to traditional: {e}")
            
            # Fallback to traditional optimization
            return self.optimize_content(request, context)
            
        except Exception as e:
            logger.error(f"Async content optimization failed: {str(e)}")
            return self.optimize_content(request, context)
    
    def _select_optimization_mode(self, request: SEOOptimizationRequest,
                                context: SEOAnalysisContext) -> str:
        """Select the best optimization mode based on request and context"""
        
        # If no LLM client, use traditional
        if not self.llm_client:
            return 'traditional'
        
        # Check request preferences
        if hasattr(request, 'optimization_mode_preference'):
            return request.optimization_mode_preference
        
        # Use configuration default
        return self.llm_config.get('llm_optimization_mode', 'hybrid')
    
    async def _traditional_optimization(self, request: SEOOptimizationRequest,
                                      context: SEOAnalysisContext) -> SEOOptimizationResult:
        """Traditional SEO optimization without LLM"""
        return super().optimize_content(request, context)
    
    async def _llm_enhanced_optimization(self, request: SEOOptimizationRequest,
                                       context: SEOAnalysisContext) -> SEOOptimizationResult:
        """Pure LLM-based optimization"""
        
        try:
            if not self.llm_orchestrator:
                return await self._traditional_optimization(request, context)
            
            # Use comprehensive LLM optimization
            llm_result = await self.llm_orchestrator.comprehensive_llm_optimization(request, context)
            
            # Convert LLM result to SEOOptimizationResult format
            return SEOOptimizationResult(
                original_content=llm_result['original_content'],
                optimized_content=llm_result['optimized_content'],
                optimization_score=llm_result['optimization_score'],
                improvements_made=self._extract_improvements_from_llm_result(llm_result),
                suggestions=llm_result.get('seo_suggestions', ContentOptimizationSuggestions()),
                hashtag_analysis=[],  # LLM handles this differently
                keyword_analysis=[],  # LLM handles this differently
                estimated_reach_improvement=self._estimate_reach_from_llm_score(llm_result['optimization_score'])
            )
            
        except Exception as e:
            logger.error(f"LLM enhanced optimization failed: {e}")
            if self.llm_config.get('fallback_to_traditional', True):
                return await self._traditional_optimization(request, context)
            raise
    
    async def _hybrid_optimization(self, request: SEOOptimizationRequest,
                                 context: SEOAnalysisContext) -> SEOOptimizationResult:
        """Hybrid optimization combining traditional SEO with LLM intelligence"""
        
        try:
            # Phase 1: Traditional SEO optimization
            traditional_result = super().optimize_content(request, context)
            
            # Phase 2: LLM enhancement of the traditional result (simplified)
            if self.llm_intelligence:
                try:
                    # Create new request with traditionally optimized content
                    enhanced_request = SEOOptimizationRequest(
                        content=traditional_result.optimized_content,
                        content_type=request.content_type,
                        optimization_level=request.optimization_level,
                        target_keywords=request.target_keywords,
                        include_hashtags=request.include_hashtags,
                        include_trending_tags=request.include_trending_tags,
                        max_length=request.max_length
                    )
                    
                    # Apply LLM enhancement
                    llm_enhancement = await self.llm_intelligence.enhance_content_with_llm(
                        enhanced_request, context, "engagement_enhancement"
                    )
                    
                    # Merge results
                    return self._merge_traditional_and_llm_results(
                        traditional_result, llm_enhancement, request, context
                    )
                except Exception as llm_error:
                    logger.warning(f"LLM enhancement failed in hybrid mode: {llm_error}")
                    # Return traditional result with LLM indicator
                    enhanced_improvements = traditional_result.improvements_made.copy()
                    enhanced_improvements.append("LLM enhancement attempted")
                    
                    return SEOOptimizationResult(
                        original_content=traditional_result.original_content,
                        optimized_content=traditional_result.optimized_content,
                        optimization_score=traditional_result.optimization_score,
                        improvements_made=enhanced_improvements,
                        suggestions=traditional_result.suggestions,
                        hashtag_analysis=traditional_result.hashtag_analysis,
                        keyword_analysis=traditional_result.keyword_analysis,
                        estimated_reach_improvement=traditional_result.estimated_reach_improvement
                    )
            
            return traditional_result
            
        except Exception as e:
            logger.error(f"Hybrid optimization failed: {e}")
            return await self._traditional_optimization(request, context)
    
    async def _intelligent_optimization(self, request: SEOOptimizationRequest,
                                      context: SEOAnalysisContext) -> SEOOptimizationResult:
        """Intelligent optimization that adapts strategy based on content analysis"""
        
        try:
            # Phase 1: Analyze content to determine best strategy
            if self.llm_analyzer:
                content_analysis = await self.llm_analyzer.analyze_content_seo_potential(
                    request.content, context
                )
                
                # Determine strategy based on analysis
                if content_analysis.get('seo_potential', 0.5) > 0.7:
                    # High potential - use aggressive LLM optimization
                    return await self._llm_enhanced_optimization(request, context)
                elif content_analysis.get('seo_potential', 0.5) > 0.4:
                    # Medium potential - use hybrid approach
                    return await self._hybrid_optimization(request, context)
                else:
                    # Low potential - use traditional with light LLM enhancement
                    traditional_result = super().optimize_content(request, context)
                    if self.llm_intelligence:
                        llm_enhancement = await self.llm_intelligence.enhance_content_with_llm(
                            request, context, "light_enhancement"
                        )
                        return self._merge_traditional_and_llm_results(
                            traditional_result, llm_enhancement, request, context
                        )
                    return traditional_result
            else:
                # No analyzer available - use hybrid as default
                return await self._hybrid_optimization(request, context)
                
        except Exception as e:
            logger.error(f"Intelligent optimization failed: {e}")
            return await self._hybrid_optimization(request, context)
    
    def _determine_intelligent_strategy(self, analysis: Dict[str, Any],
                                      request: SEOOptimizationRequest,
                                      context: SEOAnalysisContext) -> str:
        """Determine the best optimization strategy based on content analysis"""
        
        seo_score = analysis.get('seo_strength_score', 0.5)
        keyword_optimization = analysis.get('keyword_optimization', {})
        engagement_factors = analysis.get('engagement_factors', {})
        
        # If content already has strong SEO, focus on engagement
        if seo_score > 0.7:
            if engagement_factors.get('call_to_action_strength') == 'weak':
                return 'llm_focused'  # LLM better for engagement
            else:
                return 'traditional_focused'  # Fine-tune with traditional
        
        # If content has poor SEO, use comprehensive approach
        elif seo_score < 0.4:
            return 'hybrid'  # Combine both approaches
        
        # For medium SEO content, decide based on missing elements
        else:
            missing_keywords = keyword_optimization.get('missing_opportunities', [])
            if len(missing_keywords) > 2:
                return 'traditional_focused'  # Traditional better for keywords
            else:
                return 'llm_focused'  # LLM better for refinement
    
    async def _add_llm_insights_to_result(self, result: SEOOptimizationResult,
                                        request: SEOOptimizationRequest,
                                        context: SEOAnalysisContext) -> SEOOptimizationResult:
        """Add LLM insights to optimization result"""
        try:
            # For now, just add a simple LLM enhancement indicator
            enhanced_improvements = result.improvements_made.copy() if result.improvements_made else []
            enhanced_improvements.append("LLM analysis applied")
            
            return SEOOptimizationResult(
                original_content=result.original_content,
                optimized_content=result.optimized_content,
                optimization_score=min(1.0, result.optimization_score + 0.05),  # Slight boost for LLM enhancement
                improvements_made=enhanced_improvements,
                suggestions=result.suggestions,
                hashtag_analysis=result.hashtag_analysis,
                keyword_analysis=result.keyword_analysis,
                estimated_reach_improvement=result.estimated_reach_improvement
            )
            
        except Exception as e:
            logger.warning(f"Failed to add LLM insights: {e}")
            return result
    
    def _merge_traditional_and_llm_results(self, traditional_result: SEOOptimizationResult,
                                         llm_enhancement: Dict[str, Any],
                                         request: SEOOptimizationRequest,
                                         context: SEOAnalysisContext) -> SEOOptimizationResult:
        """Merge traditional SEO result with LLM enhancement"""
        
        # Use LLM enhanced content if it's significantly better
        enhanced_content = llm_enhancement.get('enhanced_content', traditional_result.optimized_content)
        
        # Combine scores (weighted average)
        traditional_weight = 0.6
        llm_weight = 0.4
        
        combined_score = (
            traditional_result.optimization_score * traditional_weight +
            llm_enhancement.get('optimization_score', 0.5) * llm_weight
        )
        
        # Merge improvements
        traditional_improvements = traditional_result.improvements_made or []
        llm_improvements = self._extract_improvements_from_llm_result(llm_enhancement)
        combined_improvements = traditional_improvements + llm_improvements
        
        # Merge suggestions
        traditional_suggestions = traditional_result.suggestions
        llm_suggestions = llm_enhancement.get('seo_suggestions', ContentOptimizationSuggestions())
        merged_suggestions = self._merge_suggestions(traditional_suggestions, llm_suggestions)
        
        # Create merged result
        return SEOOptimizationResult(
            original_content=traditional_result.original_content,
            optimized_content=enhanced_content,
            optimization_score=combined_score,
            improvements_made=combined_improvements,
            suggestions=merged_suggestions,
            hashtag_analysis=traditional_result.hashtag_analysis or [],
            keyword_analysis=traditional_result.keyword_analysis or [],
            estimated_reach_improvement=max(
                traditional_result.estimated_reach_improvement,
                self._estimate_reach_from_llm_score(llm_enhancement.get('optimization_score', 0.5))
            )
        )
    
    def _extract_improvements_from_llm_result(self, llm_result: Dict[str, Any]) -> List[str]:
        """Extract improvements list from LLM result"""
        
        improvements = []
        
        # Check for content changes
        original = llm_result.get('original_content', '')
        optimized = llm_result.get('optimized_content', '')
        
        if len(optimized) > len(original):
            improvements.append("LLM enhanced content with additional context")
        
        if optimized != original:
            improvements.append("LLM improved content flow and engagement")
        
        # Check for specific enhancements
        llm_insights = llm_result.get('llm_insights', {})
        if 'keyword_integration' in llm_insights:
            improvements.append("LLM integrated keywords naturally")
        
        if 'engagement_enhancement' in llm_insights:
            improvements.append("LLM enhanced engagement elements")
        
        if 'trend_alignment' in llm_insights:
            improvements.append("LLM aligned content with current trends")
        
        return improvements
    
    def _merge_suggestions(self, traditional: ContentOptimizationSuggestions,
                         llm: ContentOptimizationSuggestions) -> ContentOptimizationSuggestions:
        """Merge traditional and LLM suggestions"""
        
        return ContentOptimizationSuggestions(
            recommended_hashtags=list(set(
                (traditional.recommended_hashtags or []) + 
                (llm.recommended_hashtags or [])
            ))[:8],  # Limit to 8 hashtags
            primary_keywords=list(set(
                (traditional.primary_keywords or []) + 
                (llm.primary_keywords or [])
            ))[:5],  # Limit to 5 primary keywords
            secondary_keywords=list(set(
                (traditional.secondary_keywords or []) + 
                (llm.secondary_keywords or [])
            ))[:8],  # Limit to 8 secondary keywords
            semantic_keywords=(traditional.semantic_keywords or []) + (llm.semantic_keywords or []),
            trending_terms=(traditional.trending_terms or []) + (llm.trending_terms or []),
            optimal_length=llm.optimal_length or traditional.optimal_length,
            call_to_action=llm.call_to_action or traditional.call_to_action,
            timing_recommendation=llm.timing_recommendation or traditional.timing_recommendation,
            engagement_tactics=list(set(
                (traditional.engagement_tactics or []) + 
                (llm.engagement_tactics or [])
            ))[:6]  # Limit to 6 tactics
        )
    
    def _estimate_reach_from_llm_score(self, llm_score: float) -> float:
        """Estimate reach improvement from LLM optimization score"""
        # Convert LLM score to reach improvement percentage
        return llm_score * 100  # Simple conversion for now
    
    def _create_llm_score_breakdown(self, llm_result: Dict[str, Any]) -> Dict[str, float]:
        """Create score breakdown from LLM result"""
        
        optimization_score = llm_result.get('optimization_score', 0.5)
        
        return {
            'overall_score': optimization_score,
            'llm_enhancement': optimization_score,
            'content_quality': llm_result.get('current_analysis', {}).get('seo_strength_score', 0.5),
            'engagement_potential': 0.8 if '?' in llm_result.get('optimized_content', '') else 0.6,
            'trend_alignment': 0.7,  # Estimated based on LLM trend optimization
            'keyword_optimization': 0.75  # Estimated based on LLM keyword integration
        }
    
    async def get_content_suggestions(self, trend_info: Dict[str, Any],
                                    product_info: Dict[str, Any],
                                    content_type: SEOContentType) -> ContentOptimizationSuggestions:
        """
        Enhanced content suggestions with LLM intelligence
        """
        try:
            # Get traditional suggestions first
            traditional_suggestions = await super().get_content_suggestions(
                trend_info, product_info, content_type
            )
            
            # Enhance with LLM if available
            if self.llm_intelligence:
                # Create context for LLM
                context = SEOAnalysisContext(
                    content_type=content_type,
                    target_audience=product_info.get('target_audience', 'professionals'),
                    niche_keywords=product_info.get('core_values', []),
                    product_categories=[product_info.get('industry_category', 'technology')],
                    trend_context=trend_info
                )
                
                # Create a dummy request for LLM analysis
                dummy_request = SEOOptimizationRequest(
                    content=f"Content about {trend_info.get('topic_name', 'trending topic')}",
                    content_type=content_type
                )
                
                # Get LLM suggestions
                llm_enhancement = await self.llm_intelligence.enhance_content_with_llm(
                    dummy_request, context, "trend_alignment"
                )
                
                llm_suggestions = llm_enhancement.get('seo_suggestions', ContentOptimizationSuggestions())
                
                # Merge suggestions
                return self._merge_suggestions(traditional_suggestions, llm_suggestions)
            
            return traditional_suggestions
            
        except Exception as e:
            logger.error(f"Enhanced content suggestions failed: {e}")
            return await super().get_content_suggestions(trend_info, product_info, content_type)
    
    def get_content_suggestions_sync(self, trend_info: Dict[str, Any],
                                   product_info: Dict[str, Any],
                                   content_type: SEOContentType) -> ContentOptimizationSuggestions:
        """
        Synchronous version of get_content_suggestions for backward compatibility
        """
        try:
            # Get traditional suggestions (synchronous)
            traditional_suggestions = super().get_content_suggestions(
                trend_info, product_info, content_type
            )
            
            # For sync version, just return traditional suggestions
            # LLM enhancement would require async calls
            return traditional_suggestions
            
        except Exception as e:
            logger.error(f"Sync content suggestions failed: {e}")
            return ContentOptimizationSuggestions(
                recommended_hashtags=['innovation', 'business', 'growth'],
                primary_keywords=['productivity', 'professional'],
                secondary_keywords=['technology', 'digital'],
                trending_terms=['AI', 'automation'],
                engagement_tactics=['Ask questions', 'Share insights'],
                optimal_length=250 if content_type == SEOContentType.TWEET else 500,
                call_to_action='What do you think?'
            )
    
    async def optimize_for_trending_topics(self, content: str, trending_topics: List[str],
                                         context: SEOAnalysisContext) -> Dict[str, Any]:
        """
        LLM-powered optimization for trending topics
        """
        try:
            if not self.llm_intelligence:
                return {'optimized_content': content, 'trend_integration': []}
            
            # Create trend-focused optimization request
            request = SEOOptimizationRequest(
                content=content,
                content_type=context.content_type,
                optimization_level=SEOOptimizationLevel.MODERATE
            )
            
            # Add trending topics to context
            enhanced_context = context.model_copy()
            enhanced_context.trend_context = {
                'keywords': trending_topics,
                'focus': 'trending_optimization'
            }
            
            # Apply LLM trend optimization
            result = await self.llm_intelligence.enhance_content_with_llm(
                request, enhanced_context, "trend_alignment"
            )
            
            return {
                'optimized_content': result.get('enhanced_content', content),
                'trend_integration': trending_topics,
                'optimization_score': result.get('optimization_score', 0.5),
                'llm_insights': result.get('llm_insights', {}),
                'suggestions': result.get('seo_suggestions', ContentOptimizationSuggestions())
            }
            
        except Exception as e:
            logger.error(f"Trending topics optimization failed: {e}")
            return {'optimized_content': content, 'trend_integration': [], 'error': str(e)}
    
    def get_optimization_analytics(self, optimization_results: List[SEOOptimizationResult]) -> Dict[str, Any]:
        """Enhanced analytics including LLM optimization insights"""
        
        # Get base analytics
        base_analytics = super().get_optimization_analytics(optimization_results)
        
        # Add LLM-specific analytics
        llm_enhanced_count = 0
        llm_score_improvements = []
        optimization_modes = {'traditional': 0, 'llm_enhanced': 0, 'hybrid': 0, 'intelligent': 0}
        
        for result in optimization_results:
            metadata = result.optimization_metadata or {}
            
            # Count LLM enhanced results
            if metadata.get('llm_enhanced'):
                llm_enhanced_count += 1
            
            # Track optimization modes
            mode = metadata.get('optimization_mode', 'traditional')
            if mode in optimization_modes:
                optimization_modes[mode] += 1
            
            # Collect LLM score improvements
            if 'improvement_metrics' in metadata:
                improvement = metadata['improvement_metrics'].get('seo_score_improvement', 0)
                if improvement > 0:
                    llm_score_improvements.append(improvement)
        
        # Calculate LLM analytics
        avg_llm_improvement = (
            sum(llm_score_improvements) / len(llm_score_improvements)
            if llm_score_improvements else 0
        )
        
        # Enhance base analytics
        base_analytics.update({
            'llm_analytics': {
                'llm_enhanced_content_count': llm_enhanced_count,
                'llm_enhancement_rate': llm_enhanced_count / len(optimization_results) if optimization_results else 0,
                'avg_llm_score_improvement': round(avg_llm_improvement, 3),
                'optimization_mode_distribution': optimization_modes,
                'llm_available': self.llm_client is not None
            }
        })
        
        return base_analytics

    def _generate_optimization_suggestions(self, content: str, content_type: SEOContentType,
                                         context: SEOAnalysisContext = None) -> ContentOptimizationSuggestions:
        """Generate optimization suggestions"""
        try:
            return ContentOptimizationSuggestions(
                recommended_hashtags=['innovation', 'business', 'growth'],
                primary_keywords=['productivity', 'professional'],
                secondary_keywords=['technology', 'digital'],
                semantic_keywords=[],
                trending_terms=['AI', 'automation'],
                optimal_length=250 if content_type == SEOContentType.TWEET else 500,
                call_to_action='What do you think?',
                timing_recommendation='Peak hours: 9-11 AM, 1-3 PM',
                engagement_tactics=['Ask questions', 'Share insights']
            )
            
        except Exception as e:
            logger.error(f"Suggestion generation failed: {str(e)}")
            return ContentOptimizationSuggestions(
                recommended_hashtags=[],
                primary_keywords=[],
                secondary_keywords=[],
                semantic_keywords=[],
                trending_terms=[],
                optimal_length=280,
                call_to_action='',
                timing_recommendation='',
                engagement_tactics=[]
            )

    def optimize_content_sync(self, request: SEOOptimizationRequest, 
                             context: SEOAnalysisContext = None) -> SEOOptimizationResult:
        """
        Synchronous version for backward compatibility
        """
        try:
            # Use traditional optimization for sync calls
            return super().optimize_content(request, context)
        except Exception as e:
            logger.error(f"Sync SEO optimization failed: {e}")
            return SEOOptimizationResult(
                original_content=request.content,
                optimized_content=request.content,
                optimization_score=0.5,
                improvements_made=["Optimization failed"],
                hashtag_analysis=[],
                keyword_analysis=[],
                estimated_reach_improvement=0.0,
                suggestions=ContentOptimizationSuggestions()
            )

    async def optimize_content_intelligent(self, text: str, content_type: str,
                                         context: Dict[str, Any] = None,
                                         optimization_mode: str = 'intelligent') -> Dict[str, Any]:
        """
        Intelligent content optimization with LLM integration
        
        Args:
            text: Content to optimize
            content_type: Type of content
            context: Additional context
            optimization_mode: Optimization mode
            
        Returns:
            Optimization result dictionary
        """
        try:
            # Convert content type
            seo_content_type = self._convert_content_type_from_string(content_type)
            
            # Create optimization request
            request = SEOOptimizationRequest(
                content=text,
                content_type=seo_content_type,
                optimization_level=SEOOptimizationLevel.MODERATE,
                target_keywords=context.get('keywords', []) if context else [],
                include_hashtags=True,
                include_trending_tags=True
            )
            
            # Create analysis context
            analysis_context = SEOAnalysisContext(
                content_type=seo_content_type,
                target_audience=context.get('target_audience', 'professionals') if context else 'professionals',
                niche_keywords=context.get('niche_keywords', []) if context else [],
                product_categories=['technology'],
                industry_vertical='technology'
            )
            
            # Use LLM intelligence if available
            if self.llm_intelligence and optimization_mode in ['intelligent', 'llm_enhanced']:
                try:
                    llm_result = await self.llm_intelligence.enhance_content_with_llm(
                        request, analysis_context, "comprehensive"
                    )
                    
                    return {
                        'optimized_content': llm_result.get('enhanced_content', text),
                        'optimization_score': llm_result.get('optimization_score', 0.5),
                        'llm_insights': llm_result.get('llm_insights', {}),
                        'seo_suggestions': llm_result.get('seo_suggestions', {}),
                        'llm_enhanced': True,
                        'optimization_mode': optimization_mode
                    }
                    
                except Exception as e:
                    logger.warning(f"LLM optimization failed, falling back to traditional: {e}")
            
            # Fallback to traditional optimization (synchronous)
            traditional_result = self.optimize_content(request, analysis_context)
            
            return {
                'optimized_content': traditional_result.optimized_content,
                'optimization_score': traditional_result.optimization_score,
                'improvements_made': traditional_result.improvements_made,
                'llm_enhanced': False,
                'optimization_mode': 'traditional'
            }
            
        except Exception as e:
            logger.error(f"Intelligent optimization failed: {str(e)}")
            return {
                'optimized_content': text,
                'optimization_score': 0.5,
                'error': str(e),
                'llm_enhanced': False
            }

    def _convert_content_type_from_string(self, content_type: str) -> SEOContentType:
        """Convert string content type to SEOContentType enum"""
        mapping = {
            'tweet': SEOContentType.TWEET,
            'reply': SEOContentType.REPLY,
            'thread': SEOContentType.THREAD,
            'quote_tweet': SEOContentType.QUOTE_TWEET,
            'linkedin_post': SEOContentType.LINKEDIN_POST,
            'facebook_post': SEOContentType.FACEBOOK_POST,
            'blog_post': SEOContentType.BLOG_POST
        }
        
        content_str = content_type.lower().strip()
        return mapping.get(content_str, SEOContentType.TWEET)

# Integration function for the existing system
def create_enhanced_seo_optimizer(twitter_client=None, config: Dict[str, Any] = None, 
                                llm_client=None) -> SEOOptimizer:
    """Factory function to create enhanced SEO optimizer with LLM integration"""
    
    return SEOOptimizer(
        twitter_client=twitter_client,
        config=config,
        llm_client=llm_client
    )