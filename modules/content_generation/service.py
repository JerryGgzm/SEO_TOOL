"""Content generation service - Database integration layer"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from database import DataFlowManager
from modules.user_profile import UserProfileService

from .models import (
    ContentDraft, ContentType, ContentGenerationRequest, 
    ContentGenerationContext, BrandVoice, SEOSuggestions
)
from .generator import ContentGenerator, ContentGenerationFactory
from .database_adapter import ContentGenerationDatabaseAdapter

logger = logging.getLogger(__name__)

class ContentGenerationService:
    """
    High-level content generation service following DFD 3 data flow
    Orchestrates the complete content generation and storage workflow
    """
    
    def __init__(self, data_flow_manager: DataFlowManager,
                 user_profile_service: UserProfileService,
                 llm_config: Dict[str, Any],
                 seo_module=None):
        
        self.data_flow_manager = data_flow_manager
        self.user_profile_service = user_profile_service
        self.seo_module = seo_module
        
        # Initialize content generator
        self.content_generator = ContentGenerationFactory.create_generator(
            llm_provider=llm_config.get('provider', 'openai'),
            llm_config=llm_config,
            seo_module=seo_module
        )
        
        # Database adapter for converting models
        self.db_adapter = ContentGenerationDatabaseAdapter()
    
    async def generate_content_for_founder(self, founder_id: str, 
                                         request: ContentGenerationRequest) -> List[str]:
        """
        Main content generation workflow following DFD 3 steps 1-8
        
        Args:
            founder_id: Founder's ID
            request: Content generation request
            
        Returns:
            List of created draft IDs
        """
        try:
            logger.info(f"Starting content generation for founder {founder_id}")
            
            # DFD 3 Step 2: Get user context from UserProfileModule
            generation_context = await self._build_generation_context(founder_id, request)
            if not generation_context:
                logger.warning(f"Could not build generation context for founder {founder_id}")
                return []
            
            # DFD 3 Steps 4-7: Generate content (includes SEO integration and LLM calls)
            content_drafts = await self.content_generator.generate_content(request, generation_context)
            
            if not content_drafts:
                logger.warning(f"No content generated for founder {founder_id}")
                return []
            
            # DFD 3 Step 8: Store drafts in database with pending_review status
            draft_ids = []
            for draft in content_drafts:
                try:
                    # Convert to database format
                    draft_data = self.db_adapter.to_database_format(draft)
                    
                    # Store in database via DataFlowManager
                    draft_id = self.data_flow_manager.store_generated_content_draft(draft_data)
                    if draft_id:
                        draft_ids.append(draft_id)
                        
                except Exception as e:
                    logger.error(f"Failed to store content draft: {e}")
                    continue
            
            logger.info(f"Generated and stored {len(draft_ids)} content drafts for founder {founder_id}")
            return draft_ids
            
        except Exception as e:
            logger.error(f"Content generation failed for founder {founder_id}: {e}")
            return []
    
    async def generate_trend_based_content(self, founder_id: str, trend_id: str,
                                         content_type: ContentType = ContentType.TWEET,
                                         quantity: int = 3) -> List[str]:
        """Generate content based on specific trend"""
        
        request = ContentGenerationRequest(
            founder_id=founder_id,
            content_type=content_type,
            trend_id=trend_id,
            quantity=quantity,
            include_seo=True
        )
        
        return await self.generate_content_for_founder(founder_id, request)
    
    async def generate_reply_content(self, founder_id: str, source_tweet_id: str,
                                   quantity: int = 2) -> List[str]:
        """Generate reply content for specific tweet"""
        
        request = ContentGenerationRequest(
            founder_id=founder_id,
            content_type=ContentType.REPLY,
            source_tweet_id=source_tweet_id,
            quantity=quantity,
            include_seo=False  # Replies typically don't need heavy SEO
        )
        
        return await self.generate_content_for_founder(founder_id, request)
    
    async def _build_generation_context(self, founder_id: str, 
                                      request: ContentGenerationRequest) -> Optional[ContentGenerationContext]:
        """
        Build comprehensive generation context following DFD 3 steps 2-3
        
        DFD 3 Step 2: Get product info, user profile, content style preferences from UserProfileModule
        DFD 3 Step 3: Get analyzed trends data from database
        """
        try:
            # Get founder context from DataFlowManager (includes product info, settings, etc.)
            founder_context = self.data_flow_manager.get_content_generation_context(
                founder_id, request.trend_id
            )
            
            if not founder_context:
                logger.error(f"No founder context found for {founder_id}")
                return None
            
            # Extract product information
            product_info = {}
            if founder_context.get('products'):
                # Use first product for now (could be enhanced to select best match)
                product = founder_context['products'][0]
                product_info = {
                    'name': product['name'],
                    'description': product['description'],
                    'core_values': product.get('core_values', []),
                    'target_audience': product.get('target_audience', ''),
                    'niche_definition': product.get('niche_definition', {}),
                    'industry_category': product.get('niche_definition', {}).get('category', 'technology')
                }
            
            # Build brand voice from founder settings and product info
            brand_voice = self._build_brand_voice(founder_context, product_info)
            
            # Get trend information if specified
            trend_info = founder_context.get('trend_info')
            
            # Get recent content to avoid repetition
            recent_content = founder_context.get('recent_topics', [])
            
            # Get successful content patterns
            successful_patterns = founder_context.get('successful_content_patterns', [])
            
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
                content_preferences=founder_context.get('content_generation_preferences', {})
            )
            
        except Exception as e:
            logger.error(f"Failed to build generation context: {e}")
            return None
    
    def _build_brand_voice(self, founder_context: Dict[str, Any], 
                          product_info: Dict[str, Any]) -> BrandVoice:
        """Build brand voice configuration from context"""
        
        # Get settings from founder context
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
    
    def get_pending_content_for_review(self, founder_id: str) -> List[Dict[str, Any]]:
        """
        Get content pending review for founder (supports DFD 3 step 9)
        """
        return self.data_flow_manager.get_pending_content_for_review(founder_id)
    
    async def regenerate_content_with_feedback(self, draft_id: str, founder_id: str,feedback: str) -> Optional[str]:
       """Regenerate content based on user feedback"""
       
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
           
           generation_context = await self._build_generation_context(founder_id, request)
           if not generation_context:
               return None
           
           # Regenerate with feedback
           new_draft = await self.content_generator.regenerate_content(
               original_draft, generation_context, feedback
           )
           
           if not new_draft:
               return None
           
           # Store new draft
           draft_data = self.db_adapter.to_database_format(new_draft)
           return self.data_flow_manager.store_generated_content_draft(draft_data)
           
       except Exception as e:
           logger.error(f"Content regeneration failed: {e}")
           return None
   
    def approve_content_for_publishing(self, draft_id: str, founder_id: str, 
                                     edited_text: str = None) -> bool:
        """Approve content for publishing"""
        try:
            # get draft
            draft = self.db_adapter.get_content_draft(draft_id)
            if not draft:
                logger.warning(f"Draft {draft_id} not found")
                return False
            
            # Validate permission
            if draft.founder_id != founder_id:
                logger.warning(f"Founder {founder_id} not authorized for draft {draft_id}")
                return False
            
            # update draft status
            update_data = {
                'status': 'approved',
                'approved_at': datetime.utcnow()
            }
            
            # if edited text is provided, update content
            if edited_text:
                update_data['content'] = edited_text
            
            # update database
            success = self.db_adapter.update_content_draft(draft_id, update_data)
            
            if success:
                logger.info(f"Content draft {draft_id} approved for publishing")
                
                # optional: trigger publishing workflow
                self._trigger_publishing_workflow(draft_id)
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to approve content {draft_id}: {e}")
            return False
    
    def reject_content(self, draft_id: str, founder_id: str) -> bool:
        """Reject content draft"""
        return self.data_flow_manager.process_content_review_decision(
            draft_id, founder_id, 'rejected'
        )
    
    def get_content_generation_statistics(self, founder_id: str, 
                                        days: int = 30) -> Dict[str, Any]:
        """Get content generation statistics for a founder"""
        
        try:
            # Get recent drafts
            from datetime import datetime, UTC
            since_date = datetime.now(UTC) - timedelta(days=days)
            
            recent_drafts = self.data_flow_manager.db_session.query(
                self.data_flow_manager.db_session.query(
                    self.data_flow_manager.content_repo.model_class
                ).filter(
                    self.data_flow_manager.content_repo.model_class.founder_id == founder_id,
                    self.data_flow_manager.content_repo.model_class.created_at >= since_date
                ).all()
            )
            
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
    
    async def bulk_generate_content(self, founder_id: str, 
                                    content_requests: List[ContentGenerationRequest]) -> Dict[str, List[str]]:
        """Generate multiple content pieces efficiently"""
        
        results = {}
        
        # Group requests by type for efficient processing
        requests_by_type = {}
        for request in content_requests:
            content_type = request.content_type
            if content_type not in requests_by_type:
                requests_by_type[content_type] = []
            requests_by_type[content_type].append(request)
        
        # Process each content type group
        for content_type, requests in requests_by_type.items():
            try:
                # Generate content for all requests of this type
                tasks = [
                    self.generate_content_for_founder(founder_id, request)
                    for request in requests
                ]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Collect successful results
                type_draft_ids = []
                for result in batch_results:
                    if isinstance(result, list):
                        type_draft_ids.extend(result)
                    elif isinstance(result, Exception):
                        logger.error(f"Batch generation error: {result}")
                
                results[content_type.value] = type_draft_ids
                
            except Exception as e:
                logger.error(f"Bulk generation failed for {content_type}: {e}")
                results[content_type.value] = []
        
        return results
    
    def schedule_automated_content_generation(self, founder_id: str, 
                                            schedule_config: Dict[str, Any]) -> bool:
        """
        Schedule automated content generation (integration point for future scheduler)
        """
        try:
            # This would integrate with a task scheduler (Celery, etc.)
            logger.info(f"Scheduling automated content generation for founder {founder_id}")
            
            # Store schedule configuration in database
            automation_rule_data = {
                'rule_name': f'Automated Content Generation - {founder_id}',
                'trigger_conditions': {
                    'schedule': schedule_config.get('schedule', 'daily'),
                    'content_types': schedule_config.get('content_types', ['tweet']),
                    'min_trend_relevance': schedule_config.get('min_trend_relevance', 0.5)
                },
                'action_to_take': {
                    'action': 'generate_content',
                    'quantity': schedule_config.get('quantity_per_trigger', 2),
                    'auto_approve_threshold': schedule_config.get('auto_approve_threshold', 0.8)
                }
            }
            
            rule_id = self.data_flow_manager.create_automation_rule(founder_id, automation_rule_data)
            return rule_id is not None
            
        except Exception as e:
            logger.error(f"Failed to schedule automated content generation: {e}")
            return False
    
    def get_content_performance_insights(self, founder_id: str) -> Dict[str, Any]:
        """Get insights on content performance to improve future generation"""
        
        try:
            # Get published content with analytics
            published_content = self.data_flow_manager.db_session.query(
                self.data_flow_manager.content_repo.model_class
            ).filter(
                self.data_flow_manager.content_repo.model_class.founder_id == founder_id,
                self.data_flow_manager.content_repo.model_class.status == 'posted',
                self.data_flow_manager.content_repo.model_class.posted_tweet_id.isnot(None)
            ).all()
            
            if not published_content:
                return {'message': 'No published content with analytics available yet'}
            
            # Analyze performance patterns
            performance_insights = {
                'best_performing_content_types': {},
                'optimal_content_length': {},
                'top_performing_trends': [],
                'engagement_patterns': {},
                'recommendations': []
            }
            
            # Group by content type and analyze
            type_performance = {}
            for content in published_content:
                content_type = content.content_type
                if content_type not in type_performance:
                    type_performance[content_type] = []
                
                # Get analytics data
                if hasattr(content, 'post_analytics') and content.post_analytics:
                    engagement_rate = content.post_analytics.engagement_rate or 0
                    type_performance[content_type].append({
                        'engagement_rate': engagement_rate,
                        'content_length': len(content.final_text),
                        'trend_topic': content.analyzed_trend.topic_name if content.analyzed_trend else None
                    })
            
            # Calculate averages and insights
            for content_type, performances in type_performance.items():
                if performances:
                    avg_engagement = sum(p['engagement_rate'] for p in performances) / len(performances)
                    performance_insights['best_performing_content_types'][content_type] = {
                        'avg_engagement_rate': round(avg_engagement, 3),
                        'total_posts': len(performances)
                    }
                    
                    # Optimal length analysis
                    lengths_and_engagement = [(p['content_length'], p['engagement_rate']) for p in performances]
                    if lengths_and_engagement:
                        # Find length range with best engagement
                        sorted_by_engagement = sorted(lengths_and_engagement, key=lambda x: x[1], reverse=True)
                        top_performers = sorted_by_engagement[:len(sorted_by_engagement)//3]  # Top third
                        avg_length = sum(p[0] for p in top_performers) / len(top_performers)
                        performance_insights['optimal_content_length'][content_type] = int(avg_length)
            
            # Generate recommendations
            recommendations = []
            
            # Content type recommendations
            if performance_insights['best_performing_content_types']:
                best_type = max(
                    performance_insights['best_performing_content_types'].items(),
                    key=lambda x: x[1]['avg_engagement_rate']
                )
                recommendations.append(f"Focus more on {best_type[0]} content (avg engagement: {best_type[1]['avg_engagement_rate']:.1%})")
            
            # Length recommendations
            for content_type, optimal_length in performance_insights['optimal_content_length'].items():
                recommendations.append(f"Optimal {content_type} length: around {optimal_length} characters")
            
            performance_insights['recommendations'] = recommendations
            
            return performance_insights
            
        except Exception as e:
            logger.error(f"Failed to get performance insights: {e}")
            return {'error': 'Failed to analyze content performance'}

class ContentGenerationOrchestrator:
    """
    High-level orchestrator for managing multiple content generation services
    Useful for enterprises with multiple brands or A/B testing different approaches
    """
    
    def __init__(self):
        self.services = {}  # founder_id -> ContentGenerationService
        self.default_service = None
    
    def register_service(self, founder_id: str, service: ContentGenerationService):
        """Register content generation service for specific founder"""
        self.services[founder_id] = service
    
    def set_default_service(self, service: ContentGenerationService):
        """Set default service for founders without specific service"""
        self.default_service = service
    
    def get_service(self, founder_id: str) -> Optional[ContentGenerationService]:
        """Get content generation service for founder"""
        return self.services.get(founder_id, self.default_service)
    
    async def generate_content_for_founder(self, founder_id: str, 
                                            request: ContentGenerationRequest) -> List[str]:
        """Generate content using appropriate service"""
        service = self.get_service(founder_id)
        if not service:
            raise ValueError(f"No content generation service available for founder {founder_id}")
        
        return await service.generate_content_for_founder(founder_id, request)
    
    async def generate_content_for_multiple_founders(self, 
                                                    requests: List[Tuple[str, ContentGenerationRequest]]) -> Dict[str, List[str]]:
        """Generate content for multiple founders concurrently"""
        
        tasks = []
        founder_ids = []
        
        for founder_id, request in requests:
            service = self.get_service(founder_id)
            if service:
                tasks.append(service.generate_content_for_founder(founder_id, request))
                founder_ids.append(founder_id)
        
        if not tasks:
            return {}
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        founder_results = {}
        for i, result in enumerate(results):
            founder_id = founder_ids[i]
            if isinstance(result, list):
                founder_results[founder_id] = result
            else:
                logger.error(f"Content generation failed for founder {founder_id}: {result}")
                founder_results[founder_id] = []
        
        return founder_results