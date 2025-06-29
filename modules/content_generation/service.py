"""Streamlined content generation service"""
import asyncio
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import traceback

from .generator import ContentGenerator, ContentGenerationFactory
from .models import (
    ContentDraft, ContentType, ContentGenerationRequest,
    ContentGenerationContext, BrandVoice, GenerationMode
)
from .database_adapter import ContentGenerationDatabaseAdapter
from .llm_adapter import LLMAdapterFactory
from config.llm_config import LLM_CONFIG, DEFAULT_LLM_PROVIDER

logger = logging.getLogger(__name__)

class ContentGenerationService:
    """
    Streamlined content generation service focused on content creation
    """
    
    def __init__(self, data_flow_manager, user_service, llm_provider: str = DEFAULT_LLM_PROVIDER):
        """Initialize service
        
        Args:
            data_flow_manager: Data flow manager instance
            user_service: User profile service instance
            llm_provider: LLM provider to use (default: from config)
        """
        self.data_flow_manager = data_flow_manager
        self.user_service = user_service
        
        # Initialize LLM adapter
        llm_config = LLM_CONFIG.get(llm_provider)
        if not llm_config:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")
            
        self.llm_adapter = LLMAdapterFactory.create_adapter(
            llm_provider=llm_provider,
            api_key=llm_config["api_key"],
            model_name=llm_config["model_name"]
        )
        
        # Initialize content generator
        self.generator = ContentGenerator(self.llm_adapter)
        
        self.database_adapter = ContentGenerationDatabaseAdapter(data_flow_manager)
    
    async def generate_content(self, founder_id: str, trend_id: str = None,
                             content_type: ContentType = ContentType.TWEET,
                             generation_mode: GenerationMode = GenerationMode.STANDARD,
                             quantity: int = 1) -> List[str]:
        """
        Generate content drafts for a founder
        """
        
        try:
            # Build generation request
            request = ContentGenerationRequest(
                founder_id=founder_id,
                content_type=content_type,
                generation_mode=generation_mode,
                trend_id=trend_id,
                quantity=quantity,
                quality_threshold=0.6
            )
            
            # Build generation context
            context = await self._build_generation_context(founder_id, trend_id)
            
            # Generate content
            drafts = await self.generator.generate_content(request, context)
            
            # Store drafts in database
            draft_ids = []
            for draft in drafts:
                draft_id = await self._store_draft(draft)
                draft_ids.append(draft_id)
            
            logger.info(f"Generated and stored {len(draft_ids)} drafts for founder {founder_id}")
            return draft_ids
            
        except Exception as e:
            logger.error(f"Content generation failed for founder {founder_id}: {e}")
            raise
    
    async def generate_viral_focused_content(self, founder_id: str, trend_id: str = None,
                                          content_type: ContentType = ContentType.TWEET,
                                          quantity: int = 3) -> List[str]:
        """Generate content with viral optimization focus"""
        return await self.generate_content(
            founder_id=founder_id,
            trend_id=trend_id, 
            content_type=content_type,
            generation_mode=GenerationMode.VIRAL_FOCUSED,
            quantity=quantity
        )
    
    async def generate_brand_focused_content(self, founder_id: str, 
                                          custom_brand_voice: BrandVoice = None,
                                          content_type: ContentType = ContentType.TWEET,
                                          quantity: int = 2) -> List[str]:
        """Generate content with brand alignment focus"""
        
        request = ContentGenerationRequest(
            founder_id=founder_id,
            content_type=content_type,
            generation_mode=GenerationMode.BRAND_FOCUSED,
            quantity=quantity
        )
        
        context = await self._build_generation_context(founder_id)
        if custom_brand_voice:
            context.brand_voice = custom_brand_voice
        
        drafts = await self.generator.generate_content(request, context)
        
        # Store drafts
        draft_ids = []
        for draft in drafts:
            draft_id = await self._store_draft(draft)
            draft_ids.append(draft_id)
        
        return draft_ids
    
    async def _build_generation_context(self, founder_id: str, 
                                      trend_id: str = None) -> ContentGenerationContext:
        """
        Build generation context from available data
        """
        
        try:
            # Get founder profile information
            founder_profile = await self._get_founder_profile(founder_id)
            
            # Get product information
            product_info = await self._get_product_info(founder_id)
            
            # Get trend information if specified
            trend_info = None
            if trend_id:
                trend_info = await self._get_trend_info(trend_id)
            
            # Get content preferences
            content_preferences = await self._get_content_preferences(founder_id)
            
            # Get successful content patterns
            successful_patterns = await self._get_successful_patterns(founder_id)
            
            # Build brand voice from founder profile
            brand_voice = self._build_brand_voice(founder_profile)
            
            return ContentGenerationContext(
                trend_info=trend_info,
                product_info=product_info,
                brand_voice=brand_voice,
                recent_content=await self._get_recent_content(founder_id),
                successful_patterns=successful_patterns,
                target_audience=founder_profile.get('target_audience'),
                content_preferences=content_preferences
            )
            
        except Exception as e:
            logger.warning(f"Failed to build complete context for founder {founder_id}: {e}")
            # Return minimal context
            return ContentGenerationContext(
                product_info={'name': 'Product'},
                brand_voice=BrandVoice()
            )
    
    async def _get_founder_profile(self, founder_id: str) -> Dict[str, Any]:
        """Get founder profile information"""
        try:
            return await self.database_adapter.get_founder_profile(founder_id)
        except Exception as e:
            logger.warning(f"Failed to get founder profile for {founder_id}: {e}")
            return {}
    
    async def _get_product_info(self, founder_id: str) -> Dict[str, Any]:
        """Get product information for founder"""
        try:
            return await self.database_adapter.get_product_info(founder_id)
        except Exception as e:
            logger.warning(f"Failed to get product info for {founder_id}: {e}")
            return {'name': 'Product'}
    
    async def _get_trend_info(self, trend_id: str) -> Optional[Dict[str, Any]]:
        """Get trend information by ID"""
        try:
            return await self.database_adapter.get_trend_info(trend_id)
        except Exception as e:
            logger.warning(f"Failed to get trend info for {trend_id}: {e}")
            return None
    
    async def _get_content_preferences(self, founder_id: str) -> Dict[str, Any]:
        """Get content generation preferences"""
        try:
            return await self.database_adapter.get_content_preferences(founder_id)
        except Exception as e:
            logger.warning(f"Failed to get content preferences for {founder_id}: {e}")
            return {}
    
    async def _get_successful_patterns(self, founder_id: str) -> List[Dict[str, Any]]:
        """Get patterns from successful content"""
        try:
            return await self.database_adapter.get_successful_patterns(founder_id)
        except Exception as e:
            logger.warning(f"Failed to get successful patterns for {founder_id}: {e}")
            return []
    
    async def _get_recent_content(self, founder_id: str) -> List[str]:
        """Get recent content to avoid repetition"""
        try:
            return await self.database_adapter.get_recent_content(founder_id, limit=10)
        except Exception as e:
            logger.warning(f"Failed to get recent content for {founder_id}: {e}")
            return []
    
    def _build_brand_voice(self, founder_profile: Dict[str, Any]) -> BrandVoice:
        """Build brand voice from founder profile"""
        return BrandVoice(
            tone=founder_profile.get('preferred_tone', 'professional'),
            style=founder_profile.get('writing_style', 'informative'),
            personality_traits=founder_profile.get('personality_traits', []),
            avoid_words=founder_profile.get('avoid_words', []),
            preferred_phrases=founder_profile.get('preferred_phrases', []),
            formality_level=founder_profile.get('formality_level', 0.5)
        )
    
    async def _store_draft(self, draft: ContentDraft) -> str:
        """Store content draft in database"""
        try:
            return await self.database_adapter.store_draft(draft)
        except Exception as e:
            logger.error(f"Failed to store draft: {e}")
            raise
    
    async def get_draft(self, draft_id: str) -> Optional[ContentDraft]:
        """Get content draft by ID"""
        try:
            return await self.database_adapter.get_draft(draft_id)
        except Exception as e:
            logger.error(f"Failed to get draft {draft_id}: {e}")
            return None
    
    def get_drafts_by_founder(self, founder_id: str, limit: int = 20) -> List[ContentDraft]:
        """Get recent drafts for a founder"""
        try:
            return self.database_adapter.get_drafts_by_founder(founder_id, limit)
        except Exception as e:
            logger.error(f"Failed to get drafts for founder {founder_id}: {e}")
            return []
    
    async def update_draft_quality_score(self, draft_id: str, quality_score: float) -> bool:
        """Update draft quality score"""
        try:
            return await self.database_adapter.update_draft_quality_score(draft_id, quality_score)
        except Exception as e:
            logger.error(f"Failed to update draft quality score: {e}")
            return False
    
    async def regenerate_content_with_seo_feedback(self, original_draft_id: str, founder_id: str,
                                                 feedback: str, improvement_options: Dict[str, Any], quality_threshold: float = 0.4) -> List[str]:
        """
        Regenerate content based on SEO feedback and improvement suggestions
        
        Args:
            original_draft_id: ID of the original draft
            founder_id: Founder ID
            feedback: Review feedback
            improvement_options: Options for improvement
            
        Returns:
            List of new draft IDs
        """
        try:
            logger.info(f"[CONTENT_GEN] Step 1: Start regenerate_content_with_seo_feedback for draft {original_draft_id}")
            
            # Get original draft
            original_draft = await self.get_draft(original_draft_id)
            logger.info(f"[CONTENT_GEN] Step 2: Got original_draft: {original_draft}")
            if not original_draft:
                logger.error(f"Original draft {original_draft_id} not found")
                return []
            
            # Build enhanced generation context with feedback
            logger.info(f"[CONTENT_GEN] Step 3: Building generation context for founder_id={founder_id}, trend_id={original_draft.trend_id}")
            context = await self._build_generation_context(founder_id, original_draft.trend_id)
            logger.info(f"[CONTENT_GEN] Step 4: Built context: {context}")
            
            # Enhance context with feedback and improvement options
            logger.info(f"[CONTENT_GEN] Step 5: Enhancing context with feedback")
            enhanced_context = self._enhance_context_with_feedback(
                context, feedback, improvement_options, original_draft
            )
            logger.info(f"[CONTENT_GEN] Step 6: Enhanced context: {enhanced_context}")
            
            # Create regeneration request
            logger.info(f"[CONTENT_GEN] Step 7: Creating ContentGenerationRequest")
            request = ContentGenerationRequest(
                founder_id=founder_id,
                content_type=original_draft.content_type,
                generation_mode=GenerationMode.STANDARD,  # Use standard mode for regeneration
                trend_id=original_draft.trend_id,
                quantity=1,
                quality_threshold=quality_threshold,  # Lowered threshold
                custom_prompt=feedback
            )
            logger.info(f"[CONTENT_GEN] Step 8: Created request: {request}")
            
            # Generate new content
            logger.info(f"[CONTENT_GEN] Step 9: Calling generator.generate_content")
            new_drafts = await self.generator.generate_content(request, enhanced_context)
            logger.info(f"[CONTENT_GEN] Step 10: Generated {len(new_drafts)} drafts")
            
            # Store new drafts
            new_draft_ids = []
            for i, draft in enumerate(new_drafts, 1):
                logger.info(f"[CONTENT_GEN] Step 11.{i}: Processing draft {i}")
                try:
                    # Ensure metadata exists
                    draft.generation_metadata = draft.generation_metadata or {}
                    
                    # Add regeneration-specific metadata
                    draft.generation_metadata.update({
                        'is_regeneration': True,
                        'original_draft_id': original_draft_id,
                        'regeneration_feedback': feedback,
                        'improvement_options': improvement_options,
                        'regeneration_info': {
                            'regeneration_timestamp': datetime.utcnow().isoformat(),
                            'regenerated': True,
                            'new_draft_id': None,  # Will be set by review service
                            'improvements_made': []
                        }
                    })
                    
                    # Save draft to database
                    saved_draft_id = await self._store_draft(draft)
                    if saved_draft_id:
                        new_draft_ids.append(saved_draft_id)
                        logger.info(f"[CONTENT_GEN] Step 11.{i}.1: Saved draft {i} with ID {saved_draft_id}")
                    else:
                        logger.error(f"[CONTENT_GEN] Step 11.{i}.1: Failed to save draft {i}")
                        
                except Exception as e:
                    logger.error(f"[CONTENT_GEN] Step 11.{i}.2: Failed to process draft {i}: {e}")
                    continue
            
            logger.info(f"Regenerated {len(new_draft_ids)} drafts for {original_draft_id}")
            return new_draft_ids
            
        except Exception as e:
            logger.error(f"Failed to regenerate content: {e}\n{traceback.format_exc()}")
            return []
    
    def _enhance_context_with_feedback(self, context: ContentGenerationContext, 
                                     feedback: str, improvement_options: Dict[str, Any],
                                     original_draft: ContentDraft) -> ContentGenerationContext:
        """Enhance generation context with feedback and improvement options"""
        try:
            # Create enhanced context
            enhanced_context = ContentGenerationContext(
                trend_info=context.trend_info,
                product_info=context.product_info,
                brand_voice=context.brand_voice,
                recent_content=context.recent_content,
                successful_patterns=context.successful_patterns,
                target_audience=context.target_audience,
                content_preferences=context.content_preferences
            )
            
            # Add feedback to context
            enhanced_context.feedback = feedback
            
            # Apply style preferences
            style_prefs = improvement_options.get('style_preferences', {})
            if style_prefs:
                if 'tone' in style_prefs:
                    enhanced_context.brand_voice.tone = style_prefs['tone']
                if 'style' in style_prefs:
                    enhanced_context.brand_voice.style = style_prefs['style']
                if 'personality' in style_prefs:
                    enhanced_context.brand_voice.personality = style_prefs['personality']
            
            # Add target improvements
            target_improvements = improvement_options.get('target_improvements', [])
            if target_improvements:
                enhanced_context.target_improvements = target_improvements
            
            # Add elements to keep/avoid
            keep_elements = improvement_options.get('keep_elements', [])
            avoid_elements = improvement_options.get('avoid_elements', [])
            
            if keep_elements:
                enhanced_context.keep_elements = keep_elements
            if avoid_elements:
                enhanced_context.avoid_elements = avoid_elements
            
            # Add original content for reference
            enhanced_context.original_content = original_draft.generated_text
            
            return enhanced_context
            
        except Exception as e:
            logger.warning(f"Failed to enhance context with feedback: {e}")
            return context