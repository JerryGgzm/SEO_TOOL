"""Database adapter for content generation models"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from .models import ContentDraft, ContentType, ContentQualityScore

class ContentGenerationDatabaseAdapter:
    """Converts between ContentGeneration models and database format"""
    
    def __init__(self, data_flow_manager=None):
        """Initialize database adapter with data flow manager"""
        self.data_flow_manager = data_flow_manager
    
    @staticmethod
    def to_database_format(draft: ContentDraft) -> Dict[str, Any]:
        """Convert ContentDraft to database format for DataFlowManager"""
        
        # Prepare generation metadata
        metadata = draft.generation_metadata.copy()
        
        # Add quality score to metadata if available
        if draft.quality_score:
            metadata['quality_score'] = draft.quality_score.overall_score
            metadata['quality_breakdown'] = {
                'engagement_prediction': draft.quality_score.engagement_prediction,
                'brand_alignment': draft.quality_score.brand_alignment,
                'trend_relevance': draft.quality_score.trend_relevance,
                'readability': draft.quality_score.readability
            }
            metadata['quality_issues'] = draft.quality_score.issues
            metadata['quality_suggestions'] = draft.quality_score.suggestions
        
        return {
            'founder_id': draft.founder_id,
            'content_type': draft.content_type.value,
            'generated_text': draft.generated_text,
            'analyzed_trend_id': draft.trend_id,
            'source_tweet_id_for_reply': draft.source_tweet_id,
            'ai_generation_metadata': metadata,
            'scheduled_post_time': None  # Will be set during review process
        }
    
    @staticmethod
    def from_database_format(db_data: Any) -> ContentDraft:
        """Convert database model to ContentDraft"""
        
        # Extract quality score if available
        quality_score = None
        metadata = db_data.ai_generation_metadata or {}
        if 'quality_score' in metadata:
            breakdown = metadata.get('quality_breakdown', {})
            quality_score = ContentQualityScore(
                overall_score=metadata['quality_score'],
                engagement_prediction=breakdown.get('engagement_prediction', 0.5),
                brand_alignment=breakdown.get('brand_alignment', 0.5),
                trend_relevance=breakdown.get('trend_relevance', 0.5),
                readability=breakdown.get('readability', 0.5),
                issues=metadata.get('quality_issues', []),
                suggestions=metadata.get('quality_suggestions', [])
            )
        
        return ContentDraft(
            id=str(db_data.id),
            founder_id=str(db_data.founder_id),
            content_type=ContentType(db_data.content_type),
            generated_text=db_data.generated_text,
            trend_id=str(db_data.analyzed_trend_id) if db_data.analyzed_trend_id else None,
            source_tweet_id=db_data.source_tweet_id_for_reply,
            quality_score=quality_score,
            generation_metadata=metadata,
            created_at=db_data.created_at
        )
    
    @staticmethod
    def batch_to_database_format(drafts: List[ContentDraft]) -> List[Dict[str, Any]]:
        """Convert multiple drafts to database format"""
        return [
            ContentGenerationDatabaseAdapter.to_database_format(draft)
            for draft in drafts
        ]
    
    # Database interaction methods
    async def get_founder_profile(self, founder_id: str) -> Dict[str, Any]:
        """Get founder profile information"""
        if not self.data_flow_manager:
            return {}
        
        try:
            # Get founder profile from database
            founder = await self.data_flow_manager.get_founder_by_id(founder_id)
            if not founder:
                return {}
            
            return {
                'preferred_tone': getattr(founder, 'preferred_tone', 'professional'),
                'writing_style': getattr(founder, 'writing_style', 'informative'),
                'personality_traits': getattr(founder, 'personality_traits', []),
                'avoid_words': getattr(founder, 'avoid_words', []),
                'preferred_phrases': getattr(founder, 'preferred_phrases', []),
                'formality_level': getattr(founder, 'formality_level', 0.5),
                'target_audience': getattr(founder, 'target_audience', 'professionals')
            }
        except Exception as e:
            print(f"Error getting founder profile: {e}")
            return {}
    
    async def get_product_info(self, founder_id: str) -> Dict[str, Any]:
        """Get product information for founder"""
        if not self.data_flow_manager:
            return {'name': 'Demo Product'}
        
        try:
            # Get product info from database
            products = await self.data_flow_manager.get_products_by_founder(founder_id)
            if not products:
                return {'name': 'Demo Product'}
            
            # Use first product for now
            product = products[0]
            return {
                'name': getattr(product, 'name', 'Demo Product'),
                'description': getattr(product, 'description', ''),
                'industry': getattr(product, 'industry', 'technology'),
                'target_market': getattr(product, 'target_market', 'professionals'),
                'core_values': getattr(product, 'core_values', []),
                'key_features': getattr(product, 'key_features', [])
            }
        except Exception as e:
            print(f"Error getting product info: {e}")
            return {'name': 'Demo Product'}
    
    async def get_trend_info(self, trend_id: str) -> Dict[str, Any]:
        """Get trend information"""
        if not self.data_flow_manager or not trend_id:
            return {}
        
        try:
            # Get trend info from database
            trend = await self.data_flow_manager.get_trend_by_id(trend_id)
            if not trend:
                return {}
            
            return {
                'topic_name': getattr(trend, 'topic_name', ''),
                'keywords': getattr(trend, 'keywords', []),
                'sentiment': getattr(trend, 'sentiment', 'neutral'),
                'relevance_score': getattr(trend, 'relevance_score', 0.5),
                'pain_points': getattr(trend, 'pain_points', []),
                'questions': getattr(trend, 'questions', []),
                'focus_points': getattr(trend, 'focus_points', [])
            }
        except Exception as e:
            print(f"Error getting trend info: {e}")
            return {}
    
    async def get_content_preferences(self, founder_id: str) -> Dict[str, Any]:
        """Get content preferences for founder"""
        if not self.data_flow_manager:
            return {}
        
        try:
            # Get content preferences from database
            preferences = await self.data_flow_manager.get_content_preferences(founder_id)
            return preferences or {}
        except Exception as e:
            print(f"Error getting content preferences: {e}")
            return {}
    
    async def get_successful_patterns(self, founder_id: str) -> List[Dict[str, Any]]:
        """Get successful content patterns for founder"""
        if not self.data_flow_manager:
            return []
        
        try:
            # Get successful patterns from database
            patterns = await self.data_flow_manager.get_successful_content_patterns(founder_id)
            return patterns or []
        except Exception as e:
            print(f"Error getting successful patterns: {e}")
            return []
    
    async def get_recent_content(self, founder_id: str, limit: int = 10) -> List[str]:
        """Get recent content for founder"""
        if not self.data_flow_manager:
            return []
        
        try:
            # Get recent content from database
            recent_drafts = await self.data_flow_manager.get_recent_drafts(founder_id, limit)
            return [draft.generated_text for draft in recent_drafts] if recent_drafts else []
        except Exception as e:
            print(f"Error getting recent content: {e}")
            return []
    
    async def store_draft(self, draft: ContentDraft) -> str:
        """Store content draft in database"""
        if not self.data_flow_manager:
            return f"mock_draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Convert to database format
            db_data = self.to_database_format(draft)
            
            # Store in database
            stored_draft = await self.data_flow_manager.create_content_draft(db_data)
            return str(stored_draft.id)
        except Exception as e:
            print(f"Error storing draft: {e}")
            return None
    
    async def get_draft(self, draft_id: str) -> Optional[ContentDraft]:
        """Get draft by ID"""
        if not self.data_flow_manager:
            return None
        
        try:
            # Get from database
            db_draft = await self.data_flow_manager.get_draft_by_id(draft_id)
            if not db_draft:
                return None
            
            # Convert from database format
            return self.from_database_format(db_draft)
        except Exception as e:
            print(f"Error getting draft: {e}")
            return None
    
    async def get_drafts_by_founder(self, founder_id: str, limit: int = 20) -> List[ContentDraft]:
        """Get drafts by founder ID"""
        if not self.data_flow_manager:
            return []
        
        try:
            # Get from database
            db_drafts = await self.data_flow_manager.get_drafts_by_founder(founder_id, limit)
            if not db_drafts:
                return []
            
            # Convert from database format
            return [self.from_database_format(draft) for draft in db_drafts]
        except Exception as e:
            print(f"Error getting drafts by founder: {e}")
            return []
    
    async def update_draft_quality_score(self, draft_id: str, quality_score: float) -> bool:
        """Update quality score for a draft"""
        if not self.data_flow_manager:
            return False
        
        try:
            # Update in database
            success = await self.data_flow_manager.update_draft_quality_score(draft_id, quality_score)
            return success
        except Exception as e:
            print(f"Error updating draft quality score: {e}")
            return False