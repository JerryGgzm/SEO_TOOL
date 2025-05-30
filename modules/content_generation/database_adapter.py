"""Database adapter for content generation models"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from .models import ContentDraft, ContentType, SEOSuggestions, ContentQualityScore

class ContentGenerationDatabaseAdapter:
    """Converts between ContentGeneration models and database format"""
    
    @staticmethod
    def to_database_format(draft: ContentDraft) -> Dict[str, Any]:
        """Convert ContentDraft to database format for DataFlowManager"""
        
        # Prepare SEO suggestions
        seo_data = {
            'hashtags': draft.seo_suggestions.hashtags,
            'keywords': draft.seo_suggestions.keywords,
            'mentions': draft.seo_suggestions.mentions,
            'trending_tags': draft.seo_suggestions.trending_tags,
            'optimal_length': draft.seo_suggestions.optimal_length
        }
        
        # Prepare generation metadata
        metadata = draft.generation_metadata.copy()
        
        # Add quality score to metadata if available
        if draft.quality_score:
            metadata['quality_score'] = draft.quality_score.overall_score
            metadata['quality_breakdown'] = {
                'engagement_prediction': draft.quality_score.engagement_prediction,
                'brand_alignment': draft.quality_score.brand_alignment,
                'trend_relevance': draft.quality_score.trend_relevance,
                'seo_optimization': draft.quality_score.seo_optimization,
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
            'seo_suggestions': seo_data,
            'ai_generation_metadata': metadata,
            'scheduled_post_time': None  # Will be set during review process
        }
    
    @staticmethod
    def from_database_format(db_data: Any) -> ContentDraft:
        """Convert database model to ContentDraft"""
        
        # Extract SEO suggestions
        seo_data = db_data.seo_suggestions or {}
        seo_suggestions = SEOSuggestions(
            hashtags=seo_data.get('hashtags', []),
            keywords=seo_data.get('keywords', []),
            mentions=seo_data.get('mentions', []),
            trending_tags=seo_data.get('trending_tags', []),
            optimal_length=seo_data.get('optimal_length')
        )
        
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
                seo_optimization=breakdown.get('seo_optimization', 0.5),
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
            seo_suggestions=seo_suggestions,
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