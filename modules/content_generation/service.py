"""Enhanced content generation service with SEO integration"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from database import DataFlowManager
from modules.user_profile import UserProfileService
from modules.seo.service_integration import SEOService

from .models import (
    ContentDraft, ContentType, ContentGenerationRequest, 
    ContentGenerationContext, BrandVoice, SEOSuggestions, GenerationMode
)
from .generator import ContentGenerator, ContentGenerationFactory
from .database_adapter import ContentGenerationDatabaseAdapter

logger = logging.getLogger(__name__)

class ContentGenerationService:
    """
    Enhanced content generation service with full SEO integration
    """
    
    def __init__(self, data_flow_manager: DataFlowManager,
                 seo_service: SEOService,
                 llm_config: Dict[str, Any]):
        
        self.data_flow_manager = data_flow_manager
        self.seo_service = seo_service
        
        # Initialize enhanced content generator with SEO integration
        self.generator = ContentGenerationFactory.create_enhanced_generator(
            llm_provider=llm_config.get('provider', 'openai'),
            llm_config=llm_config,
            seo_optimizer=seo_service.optimizer if seo_service else None
        )
        
        # Database adapter for converting models
        self.db_adapter = ContentGenerationDatabaseAdapter()
    
    async def generate_content_for_founder(self, founder_id: str, 
                                         request: ContentGenerationRequest) -> List[str]:
        """
        Enhanced content generation with SEO optimization
        
        Args:
            founder_id: Founder's ID
            request: Content generation request
            
        Returns:
            List of created draft IDs
        """
        try:
            logger.info(f"Starting enhanced content generation for founder {founder_id}")
            
            # Build generation context with SEO integration
            generation_context = await self._build_enhanced_generation_context(founder_id, request)
            if not generation_context:
                logger.warning(f"Could not build generation context for founder {founder_id}")
                return []
            
            # Generate SEO-optimized content
            content_drafts = await self.generator.generate_content(request, generation_context)
            
            if not content_drafts:
                logger.warning(f"No content generated for founder {founder_id}")
                return []
            
            # Store drafts and SEO optimization results
            draft_ids = []
            for draft in content_drafts:
                try:
                    # Store content draft
                    draft_data = self.db_adapter.to_database_format(draft)
                    draft_id = self.data_flow_manager.store_generated_content_draft(draft_data)
                    
                    if draft_id:
                        draft_ids.append(draft_id)
                        
                        # Store SEO optimization results for analytics
                        await self._store_seo_optimization_results(founder_id, draft, draft_id)
                        
                except Exception as e:
                    logger.error(f"Failed to store content draft: {e}")
                    continue
            
            logger.info(f"Generated and stored {len(draft_ids)} SEO-optimized drafts for founder {founder_id}")
            return draft_ids
            
        except Exception as e:
            logger.error(f"Enhanced content generation failed for founder {founder_id}: {e}")
            return []
    
    async def generate_seo_optimized_content(self, founder_id: str, trend_id: str = None,
                                           content_type: ContentType = ContentType.TWEET,
                                           optimization_level: str = "moderate",
                                           quantity: int = 3) -> List[str]:
        """Generate content with specific SEO optimization level"""
        
        request = ContentGenerationRequest(
            founder_id=founder_id,
            content_type=content_type,
            trend_id=trend_id,
            quantity=quantity,
            include_seo=True,
            generation_mode=GenerationMode.SEO_OPTIMIZED
        )
        
        return await self.generate_content_for_founder(founder_id, request)
    
    async def generate_content_with_custom_seo(self, founder_id: str,
                                             content_type: ContentType,
                                             custom_keywords: List[str],
                                             custom_hashtags: List[str],
                                             quantity: int = 2) -> List[str]:
        """Generate content with custom SEO parameters"""
        
        # Create custom SEO suggestions
        custom_seo = SEOSuggestions(
            hashtags=custom_hashtags,
            keywords=custom_keywords,
            mentions=[],
            trending_tags=[],
            optimal_length=None
        )
        
        request = ContentGenerationRequest(
            founder_id=founder_id,
            content_type=content_type,
            quantity=quantity,
            include_seo=True,
            custom_seo_suggestions=custom_seo
        )
        
        return await self.generate_content_for_founder(founder_id, request)
    
    async def _build_enhanced_generation_context(self, founder_id: str, 
                                               request: ContentGenerationRequest) -> Optional[ContentGenerationContext]:
        """
        Build enhanced generation context with SEO integration
        """
        try:
            # Get founder context from DataFlowManager
            founder_context = self.data_flow_manager.get_content_generation_context(
                founder_id, request.trend_id
            )
            
            if not founder_context:
                logger.error(f"No founder context found for {founder_id}")
                return None
            
            # Extract product information
            product_info = {}
            if founder_context.get('products'):
                product = founder_context['products'][0]
                product_info = {
                    'name': product['name'],
                    'description': product['description'],
                    'core_values': product.get('core_values', []),
                    'target_audience': product.get('target_audience', ''),
                    'niche_definition': product.get('niche_definition', {}),
                    'industry_category': product.get('niche_definition', {}).get('category', 'technology')
                }
            
            # Build enhanced brand voice
            brand_voice = self._build_brand_voice(founder_context, product_info)
            
            # Get trend information with SEO enhancement
            trend_info = founder_context.get('trend_info')
            if trend_info and self.seo_service:
                # Enhance trend info with SEO insights
                trend_info = await self._enhance_trend_info_with_seo(trend_info, product_info)
            
            # Get SEO-enhanced content preferences
            content_preferences = await self._get_seo_enhanced_preferences(
                founder_id, request.content_type, product_info, trend_info
            )
            
            # Get recent content to avoid repetition
            recent_content = founder_context.get('recent_topics', [])
            
            # Get successful content patterns with SEO metrics
            successful_patterns = await self._get_seo_enhanced_patterns(founder_id)
            
            # Build target audience description
            target_audience = product_info.get('target_audience', 'professionals in technology')
            
            return ContentGenerationContext(
                founder_id=founder_id,
                trend_info=trend_info,
                product_info=product_info,
                brand_voice=brand_voice,
                recent_content=recent_content,
                successful_patterns=successful_patterns,
                target_audience=target_audience,
                content_preferences=content_preferences
            )
            
        except Exception as e:
            logger.error(f"Failed to build enhanced generation context: {e}")
            return None
    
    async def _enhance_trend_info_with_seo(self, trend_info: Dict[str, Any], 
                                         product_info: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance trend info with SEO insights"""
        
        try:
            if not self.seo_service:
                return trend_info
            
            # Get SEO suggestions for the trend
            seo_suggestions = await self.seo_service.get_content_suggestions(
                trend_info=trend_info,
                product_info=product_info,
                content_type='tweet'
            )
            
            # Enhance trend info with SEO data
            enhanced_trend_info = trend_info.copy()
            enhanced_trend_info.update({
                'seo_keywords': seo_suggestions.primary_keywords + seo_suggestions.secondary_keywords,
                'seo_hashtags': seo_suggestions.recommended_hashtags,
                'trending_terms': seo_suggestions.trending_terms,
                'seo_enhanced': True
            })
            
            return enhanced_trend_info
            
        except Exception as e:
            logger.warning(f"Failed to enhance trend info with SEO: {e}")
            return trend_info
    
    async def _get_seo_enhanced_preferences(self, founder_id: str, content_type: ContentType,
                                          product_info: Dict[str, Any], 
                                          trend_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get content preferences enhanced with SEO data"""
        
        try:
            base_preferences = {}
            
            # Get SEO recommendations for this founder
            if self.seo_service:
                seo_recommendations = self.seo_service.get_seo_recommendations(founder_id)
                
                if seo_recommendations:
                    base_preferences.update({
                        'seo_strategy': seo_recommendations.get('hashtag_strategy', {}),
                        'keyword_focus': seo_recommendations.get('keyword_focus', {}),
                        'content_optimization': seo_recommendations.get('content_optimization', {}),
                        'seo_recommendations': seo_recommendations
                    })
            
            # Add trend-specific SEO preferences
            if trend_info and trend_info.get('seo_enhanced'):
                base_preferences.update({
                    'trend_seo_keywords': trend_info.get('seo_keywords', []),
                    'trend_seo_hashtags': trend_info.get('seo_hashtags', []),
                    'trending_terms': trend_info.get('trending_terms', [])
                })
            
            return base_preferences
            
        except Exception as e:
            logger.warning(f"Failed to get SEO enhanced preferences: {e}")
            return {}
    
    async def _get_seo_enhanced_patterns(self, founder_id: str) -> List[Dict[str, Any]]:
        """Get successful content patterns enhanced with SEO performance data"""
        
        try:
            # Get base successful patterns
            base_patterns = []
            
            # Get SEO performance history
            if self.seo_service:
                seo_analytics = self.seo_service.get_seo_analytics_summary(founder_id)
                
                if seo_analytics and seo_analytics.get('best_performing_hashtags'):
                    # Create patterns based on SEO performance
                    best_hashtags = seo_analytics['best_performing_hashtags']
                    
                    for hashtag in best_hashtags[:3]:
                        base_patterns.append({
                            'content_type': 'tweet',
                            'pattern_type': 'seo_hashtag',
                            'hashtag': hashtag,
                            'performance_score': 0.8,  # High performance indicator
                            'seo_optimized': True
                        })
            
            return base_patterns
            
        except Exception as e:
            logger.warning(f"Failed to get SEO enhanced patterns: {e}")
            return []
    
    async def _store_seo_optimization_results(self, founder_id: str, draft: ContentDraft, 
                                            draft_id: str) -> None:
        """Store SEO optimization results for analytics"""
        
        try:
            if not draft.generation_metadata.get('seo_optimized'):
                return
            
            # Prepare SEO optimization data
            optimization_data = {
                'content_draft_id': draft_id,
                'optimization_timestamp': datetime.utcnow().isoformat(),
                'seo_quality_score': draft.generation_metadata.get('seo_quality_score', 0.0),
                'keywords_used': draft.generation_metadata.get('seo_keywords_used', []),
                'hashtags_suggested': draft.generation_metadata.get('seo_hashtags_suggested', []),
                'content_type': draft.content_type.value,
                'optimization_method': 'integrated_generation',
                'overall_quality_score': draft.quality_score.overall_score if draft.quality_score else 0.0,
                'trend_id': draft.trend_id,
                'content_length': len(draft.generated_text)
            }
            
            # Store using DataFlowManager
            success = self.data_flow_manager.store_seo_optimization_result(founder_id, optimization_data)
            
            if success:
                logger.info(f"Stored SEO optimization results for draft {draft_id}")
            else:
                logger.warning(f"Failed to store SEO optimization results for draft {draft_id}")
                
        except Exception as e:
            logger.error(f"Error storing SEO optimization results: {e}")
    
    def _build_brand_voice(self, founder_context: Dict[str, Any], 
                          product_info: Dict[str, Any]) -> BrandVoice:
        """Build brand voice configuration from context"""
        
        settings = founder_context.get('founder_settings', {})
        content_prefs = settings.get('content_preferences', {})
        
        # Extract core values for personality traits
        core_values = product_info.get('core_values', [])
        personality_traits = core_values[:3] if core_values else ['professional', 'helpful']
        
        # Determine tone from product category and settings
        industry = product_info.get('industry_category', '').lower()
        if 'finance' in industry or 'legal' in industry:
            default_tone = 'professional'
        elif 'creative' in industry or 'design' in industry:
            default_tone = 'casual'
        else:
            default_tone = 'friendly'
        
        tone = content_prefs.get('tone', default_tone)
        
        return BrandVoice(
            tone=tone,
            style=content_prefs.get('style', 'informative'),
            personality_traits=personality_traits,
            avoid_words=content_prefs.get('avoid_words', []),
            preferred_phrases=content_prefs.get('preferred_phrases', []),
            formality_level=content_prefs.get('formality_level', 0.5)
        )
    
    async def regenerate_content_with_seo_feedback(self, draft_id: str, founder_id: str,
                                                  feedback: str, seo_improvements: Dict[str, Any] = None) -> Optional[str]:
        """Regenerate content with both regular and SEO feedback"""
        
        try:
            # Get original draft from database
            original_draft_data = self.data_flow_manager.content_repo.get_by_id(draft_id)
            if not original_draft_data or original_draft_data.founder_id != founder_id:
                logger.error(f"Draft {draft_id} not found or access denied")
                return None
            
            # Convert database model to service model
            original_draft = self.db_adapter.from_database_format(original_draft_data)
            
            # Build generation context
            request = ContentGenerationRequest(
                founder_id=founder_id,
                content_type=original_draft.content_type,
                trend_id=original_draft.trend_id,
                source_tweet_id=original_draft.source_tweet_id
            )
            
            generation_context = await self._build_enhanced_generation_context(founder_id, request)
            if not generation_context:
                return None
            
            # Apply SEO improvements if provided
            if seo_improvements:
                generation_context = self._apply_seo_improvements_to_context(
                    generation_context, seo_improvements
                )
            
            # Regenerate with enhanced feedback
            enhanced_feedback = feedback
            if seo_improvements:
                seo_feedback = self._create_seo_feedback_string(seo_improvements)
                enhanced_feedback = f"{feedback}\n\nSEO Improvements: {seo_feedback}"
            
            # Use the enhanced generator's regeneration method
            new_draft = await self.generator.regenerate_content(
                original_draft, generation_context, enhanced_feedback
            )
            
            if not new_draft:
                return None
            
            # Store new draft with regeneration metadata
            new_draft.generation_metadata.update({
                "regeneration_feedback": feedback,
                "seo_improvements_applied": seo_improvements or {},
                "original_draft_id": original_draft.id,
                "regeneration_timestamp": datetime.utcnow().isoformat()
            })
            
            # Store the new draft
            draft_data = self.db_adapter.to_database_format(new_draft)
            new_draft_id = self.data_flow_manager.store_generated_content_draft(draft_data)
            
            # Store SEO optimization results
            if new_draft_id:
                await self._store_seo_optimization_results(founder_id, new_draft, new_draft_id)
            
            return new_draft_id
            
        except Exception as e:
            logger.error(f"Content regeneration with SEO feedback failed: {e}")
            return None
    
    def _apply_seo_improvements_to_context(self, context: ContentGenerationContext,
                                         seo_improvements: Dict[str, Any]) -> ContentGenerationContext:
        """Apply SEO improvements to generation context"""
        
        enhanced_context = context.model_copy()
        
        # Update content preferences with SEO improvements
        enhanced_preferences = enhanced_context.content_preferences.copy()
        
        if 'additional_keywords' in seo_improvements:
            enhanced_preferences['additional_seo_keywords'] = seo_improvements['additional_keywords']
        
        if 'additional_hashtags' in seo_improvements:
            enhanced_preferences['additional_seo_hashtags'] = seo_improvements['additional_hashtags']
        
        if 'target_length' in seo_improvements:
            enhanced_preferences['target_length'] = seo_improvements['target_length']
        
        if 'optimization_focus' in seo_improvements:
            enhanced_preferences['seo_optimization_focus'] = seo_improvements['optimization_focus']
        
        enhanced_context.content_preferences = enhanced_preferences
        
        return enhanced_context
    
    def _create_seo_feedback_string(self, seo_improvements: Dict[str, Any]) -> str:
        """Create SEO feedback string from improvements dictionary"""
        
        feedback_parts = []
        
        if 'additional_keywords' in seo_improvements:
            keywords = ', '.join(seo_improvements['additional_keywords'])
            feedback_parts.append(f"Include these keywords: {keywords}")
        
        if 'additional_hashtags' in seo_improvements:
            hashtags = ', '.join(f"#{tag}" for tag in seo_improvements['additional_hashtags'])
            feedback_parts.append(f"Add these hashtags: {hashtags}")
        
        if 'target_length' in seo_improvements:
            target_length = seo_improvements['target_length']
            feedback_parts.append(f"Target length: {target_length} characters")
        
        if 'optimization_focus' in seo_improvements:
            focus = seo_improvements['optimization_focus']
            feedback_parts.append(f"Focus on: {focus}")
        
        return ". ".join(feedback_parts)
    
    def get_seo_content_analytics(self, founder_id: str, days: int = 30) -> Dict[str, Any]:
        """Get SEO-enhanced content analytics"""
        
        try:
            # Get base content statistics
            base_stats = self.get_content_generation_statistics(founder_id, days)
            
            # Get SEO performance data
            seo_performance = self.data_flow_manager.get_seo_performance_history(founder_id, days)
            
            # Combine analytics
            if seo_performance:
                # Calculate SEO metrics
                avg_seo_score = sum(p.get('seo_quality_score', 0) for p in seo_performance) / len(seo_performance)
                seo_optimized_count = sum(1 for p in seo_performance if p.get('seo_quality_score', 0) > 0.7)
                
                # Most used keywords and hashtags
                all_keywords = []
                all_hashtags = []
                
                for perf in seo_performance:
                    all_keywords.extend(perf.get('keywords_used', []))
                    all_hashtags.extend(perf.get('hashtags_suggested', []))
                
                from collections import Counter
                top_keywords = [kw for kw, count in Counter(all_keywords).most_common(10)]
                top_hashtags = [ht for ht, count in Counter(all_hashtags).most_common(10)]
                
                base_stats.update({
                    'seo_metrics': {
                        'avg_seo_quality_score': round(avg_seo_score, 3),
                        'seo_optimized_content_count': seo_optimized_count,
                        'seo_optimization_rate': round(seo_optimized_count / len(seo_performance), 3),
                        'top_performing_keywords': top_keywords,
                        'most_used_hashtags': top_hashtags,
                        'total_seo_optimizations': len(seo_performance)
                    }
                })
            
            return base_stats
            
        except Exception as e:
            logger.error(f"Failed to get SEO content analytics: {e}")
            return {}
    
    def get_content_generation_statistics(self, founder_id: str, days: int = 30) -> Dict[str, Any]:
        """Get content generation statistics for a founder"""
        
        try:
            # Get recent drafts
            from datetime import datetime, UTC
            since_date = datetime.now(UTC) - timedelta(days=days)
            
            recent_drafts = self.data_flow_manager.db_session.query(
                self.data_flow_manager.content_repo.model_class
            ).filter(
                self.data_flow_manager.content_repo.model_class.founder_id == founder_id,
                self.data_flow_manager.content_repo.model_class.created_at >= since_date
            ).all()
            
            if not recent_drafts:
                return {
                    'total_generated': 0,
                    'approval_rate': 0.0,
                    'avg_quality_score': 0.0,
                    'content_type_distribution': {},
                    'trend_based_content': 0
                }
            
            # Calculate statistics
            total_generated = len(recent_drafts)
            approved_count = sum(1 for d in recent_drafts if d.status in ['approved', 'posted', 'scheduled'])
            approval_rate = approved_count / total_generated if total_generated > 0 else 0.0
            
            # Content type distribution
            type_distribution = {}
            for draft in recent_drafts:
                content_type = draft.content_type
                type_distribution[content_type] = type_distribution.get(content_type, 0) + 1
            
            # Trend-based content count
            trend_based_count = sum(1 for d in recent_drafts if d.analyzed_trend_id)
            
            # Quality scores (if available in metadata)
            quality_scores = []
            for draft in recent_drafts:
                if draft.ai_generation_metadata and 'quality_score' in draft.ai_generation_metadata:
                    quality_scores.append(draft.ai_generation_metadata['quality_score'])
            
            avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            
            return {
                'total_generated': total_generated,
                'approval_rate': round(approval_rate, 3),
                'avg_quality_score': round(avg_quality_score, 3),
                'content_type_distribution': type_distribution,
                'trend_based_content': trend_based_count,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Failed to get content generation statistics: {e}")
            return {}