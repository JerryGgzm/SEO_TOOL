"""Streamlined content generation service"""
import asyncio
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from .generator import ContentGenerator, ContentGenerationFactory
from .models import (
    ContentDraft, ContentType, ContentGenerationRequest,
    ContentGenerationContext, BrandVoice, GenerationMode
)
from .database_adapter import ContentGenerationDatabaseAdapter

logger = logging.getLogger(__name__)

class ContentGenerationService:
    """
    Streamlined content generation service focused on content creation
    """
    
    def __init__(self, 
                 llm_config: Dict[str, Any],
                 database_adapter: ContentGenerationDatabaseAdapter):
        
        self.database_adapter = database_adapter
        
        # Initialize content generator
        self.generator = ContentGenerationFactory.create_generator(
            llm_provider=llm_config.get('provider', 'openai'),
            llm_config=llm_config
        )
        
        self.logger = logging.getLogger(__name__)
    
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
    
    async def get_drafts_by_founder(self, founder_id: str, limit: int = 20) -> List[ContentDraft]:
        """Get recent drafts for a founder"""
        try:
            return await self.database_adapter.get_drafts_by_founder(founder_id, limit)
        except Exception as e:
            logger.error(f"Failed to get drafts for founder {founder_id}: {e}")
            return []
    
    async def update_draft_quality_score(self, draft_id: str, quality_score: float) -> bool:
        """Update quality score for a draft"""
        try:
            return await self.database_adapter.update_draft_quality_score(draft_id, quality_score)
        except Exception as e:
            logger.error(f"Failed to update quality score for draft {draft_id}: {e}")
            return False