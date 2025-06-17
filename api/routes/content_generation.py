"""Content Generation API Routes

This module implements the FastAPI routes for the content generation system,
handling AI-powered content creation and management workflows.

Note: SEO optimization is handled separately by the SEO module.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

from database import get_data_flow_manager, DataFlowManager
from api.middleware import get_current_user, User

from modules.content_generation.service import ContentGenerationService
from modules.content_generation.database_adapter import ContentGenerationDatabaseAdapter
from modules.content_generation.models import (
    ContentGenerationRequest, ContentType, GenerationMode,
    ContentDraft, BrandVoice
)
from config import LLM_CONFIG, DEFAULT_LLM_PROVIDER

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/content", tags=["content-generation"])

def get_content_service(llm_provider: str = DEFAULT_LLM_PROVIDER) -> ContentGenerationService:
    """Get content generation service instance
    
    Args:
        llm_provider: LLM provider to use (default: from config)
        
    Returns:
        ContentGenerationService instance
    """
    # Get LLM configuration
    llm_config = LLM_CONFIG.get(llm_provider)
    if not llm_config:
        raise HTTPException(status_code=400, detail=f"Unsupported LLM provider: {llm_provider}")
        
    # Initialize service
    return ContentGenerationService(
        data_flow_manager=None,  # TODO: Initialize with actual data flow manager
        user_service=None,  # TODO: Initialize with actual user service
        llm_provider=llm_provider
    )

@router.post("/generate")
async def generate_content(
    request: ContentGenerationRequest,
    llm_provider: str = DEFAULT_LLM_PROVIDER,
    service: ContentGenerationService = Depends(get_content_service)
) -> List[str]:
    """Generate content based on request
    
    Args:
        request: Content generation request
        llm_provider: LLM provider to use (default: from config)
        service: Content generation service
        
    Returns:
        List of generated content draft IDs
    """
    try:
        # Generate content
        draft_ids = await service.generate_content(
            founder_id=request.founder_id,
            trend_id=request.trend_id,
            content_type=request.content_type,
            count=request.count
        )
        
        return draft_ids
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/viral-focused")
async def generate_viral_content(
    founder_id: str = Query(..., description="Founder ID"),
    content_type: ContentType = Query(default=ContentType.TWEET),
    trend_id: Optional[str] = Query(None, description="Specific trend to base content on"),
    quantity: int = Query(default=3, ge=1, le=10, description="Number of variations"),
    current_user: User = Depends(get_current_user),
    service: ContentGenerationService = Depends(get_content_service)
):
    """
    Generate viral-focused content optimized for maximum engagement
    
    Uses strategies focused on:
    - Viral content patterns
    - Engagement optimization
    - Trending topic alignment
    - Shareable content elements
    """
    try:
        # Validate user access
        if current_user.id != founder_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Generate viral-focused content
        draft_ids = await service.generate_viral_focused_content(
            founder_id=founder_id,
            trend_id=trend_id,
            content_type=content_type,
            quantity=quantity
        )
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Viral-focused content generated successfully",
                "draft_ids": draft_ids,
                "count": len(draft_ids),
                "generation_mode": "viral_focused",
                "content_type": content_type.value
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Viral-focused content generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Viral-focused content generation failed"
        )

@router.post("/generate/brand-focused")
async def generate_brand_focused_content(
    founder_id: str = Query(..., description="Founder ID"),
    content_type: ContentType = Query(default=ContentType.TWEET),
    tone: Optional[str] = Query(None, description="Brand tone override"),
    style: Optional[str] = Query(None, description="Writing style override"),
    quantity: int = Query(default=2, ge=1, le=5, description="Number of variations"),
    current_user: User = Depends(get_current_user),
    service: ContentGenerationService = Depends(get_content_service)
):
    """
    Generate brand-focused content with strong brand alignment
    
    Focuses on:
    - Brand voice consistency
    - Brand messaging alignment
    - Professional tone
    - Brand value communication
    """
    try:
        # Validate user access
        if current_user.id != founder_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Create custom brand voice if overrides provided
        custom_brand_voice = None
        if tone or style:
            custom_brand_voice = BrandVoice(
                tone=tone or "professional",
                style=style or "informative"
            )
        
        # Generate brand-focused content
        draft_ids = await service.generate_brand_focused_content(
            founder_id=founder_id,
            custom_brand_voice=custom_brand_voice,
            content_type=content_type,
            quantity=quantity
        )
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Brand-focused content generated successfully",
                "draft_ids": draft_ids,
                "brand_overrides": {
                    "tone": tone,
                    "style": style
                } if (tone or style) else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Brand-focused content generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Brand-focused content generation failed"
        )

@router.get("/drafts/{draft_id}")
async def get_draft(
    draft_id: str = Path(..., description="Draft ID"),
    current_user: User = Depends(get_current_user),
    service: ContentGenerationService = Depends(get_content_service)
):
    """
    Get content draft by ID
    
    Returns the full content draft including generation metadata
    and quality scores.
    """
    try:
        # Get draft from service
        draft = await service.get_draft(draft_id)
        
        if not draft:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        # Check user access
        if current_user.id != draft.founder_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Convert to response format
        return {
            "draft_id": draft_id,
            "content": draft.generated_text,
            "content_type": draft.content_type.value,
            "founder_id": draft.founder_id,
            "quality_score": draft.quality_score,
            "generation_metadata": draft.generation_metadata,
            "created_at": draft.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get draft: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve draft"
        )

@router.get("/drafts/founder/{founder_id}")
async def get_founder_drafts(
    founder_id: str = Path(..., description="Founder ID"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of drafts"),
    current_user: User = Depends(get_current_user),
    service: ContentGenerationService = Depends(get_content_service)
):
    """
    Get recent drafts for a founder
    
    Returns list of recent content drafts with basic information.
    """
    try:
        # Validate user access
        if current_user.id != founder_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get drafts
        drafts = await service.get_drafts_by_founder(founder_id, limit)
        
        # Convert to response format
        draft_list = []
        for draft in drafts:
            draft_list.append({
                "draft_id": draft.id,
                "content": draft.generated_text[:100] + "..." if len(draft.generated_text) > 100 else draft.generated_text,
                "content_type": draft.content_type.value,
                "quality_score": draft.quality_score,
                "created_at": draft.created_at.isoformat()
            })
        
        return {
            "founder_id": founder_id,
            "drafts": draft_list,
            "count": len(draft_list),
            "limit": limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get founder drafts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve drafts"
        )

@router.put("/drafts/{draft_id}/quality-score")
async def update_draft_quality_score(
    draft_id: str = Path(..., description="Draft ID"),
    quality_score: float = Query(..., ge=0, le=1, description="Quality score"),
    current_user: User = Depends(get_current_user),
    service: ContentGenerationService = Depends(get_content_service)
):
    """
    Update quality score for a draft
    
    Allows manual quality score updates based on performance feedback.
    """
    try:
        # Get draft first to check ownership
        draft = await service.get_draft(draft_id)
        
        if not draft:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        # Check user access
        if current_user.id != draft.founder_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Update quality score
        success = await service.update_draft_quality_score(draft_id, quality_score)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update quality score"
            )
        
        return {
            "message": "Quality score updated successfully",
            "draft_id": draft_id,
            "new_quality_score": quality_score
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update quality score: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update quality score"
        )

@router.get("/templates/{content_type}")
async def get_content_templates(
    content_type: ContentType = Path(..., description="Content type"),
    current_user: User = Depends(get_current_user)
):
    """
    Get content templates for specific content type
    
    Returns available templates and prompts for content generation.
    """
    try:
        # This would integrate with your prompt engine
        templates = {
            ContentType.TWEET: [
                {
                    "name": "Product Announcement",
                    "description": "Template for announcing new products or features",
                    "variables": ["product_name", "key_benefit", "call_to_action"]
                },
                {
                    "name": "Thought Leadership",
                    "description": "Template for sharing industry insights",
                    "variables": ["topic", "insight", "question"]
                },
                {
                    "name": "Engagement Post",
                    "description": "Template for driving engagement",
                    "variables": ["topic", "question", "hashtags"]
                }
            ],
            ContentType.THREAD: [
                {
                    "name": "How-To Guide",
                    "description": "Template for educational thread content",
                    "variables": ["topic", "steps", "conclusion"]
                },
                {
                    "name": "Story Thread",
                    "description": "Template for narrative content",
                    "variables": ["story_topic", "key_points", "lesson"]
                }
            ],
            ContentType.REPLY: [
                {
                    "name": "Supportive Reply",
                    "description": "Template for supportive responses",
                    "variables": ["agreement_point", "additional_insight"]
                },
                {
                    "name": "Question Reply",
                    "description": "Template for asking follow-up questions",
                    "variables": ["question", "context"]
                }
            ]
        }
        
        return {
            "content_type": content_type.value,
            "templates": templates.get(content_type, []),
            "total_templates": len(templates.get(content_type, []))
        }
        
    except Exception as e:
        logger.error(f"Template retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve content templates"
        )

@router.get("/suggestions/content-ideas")
async def get_content_ideas(
    founder_id: str = Query(..., description="Founder ID"),
    trend_id: Optional[str] = Query(None, description="Specific trend ID"),
    content_type: ContentType = Query(default=ContentType.TWEET),
    count: int = Query(default=5, ge=1, le=20, description="Number of ideas"),
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-generated content ideas based on trends and user profile
    
    Returns content ideas without generating full drafts.
    """
    try:
        # Validate user access
        if current_user.id != founder_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get content ideas (this would use your content generation service)
        # For now, returning mock data - implement with actual AI generation
        ideas = []
        idea_templates = [
            "Share your experience with {topic}",
            "What's the biggest challenge in {industry}?",
            "Here's why {trend} matters for {audience}",
            "The future of {industry} in 3 key points",
            "Common mistakes in {field} and how to avoid them"
        ]
        
        for i in range(count):
            ideas.append({
                "id": f"idea_{i+1}",
                "title": f"Content idea {i+1}",
                "description": idea_templates[i % len(idea_templates)],
                "content_type": content_type.value,
                "estimated_engagement": ["low", "medium", "high"][i % 3]
            })
        
        return {
            "founder_id": founder_id,
            "content_type": content_type.value,
            "trend_id": trend_id,
            "ideas": ideas,
            "count": len(ideas)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content ideas generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate content ideas"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint for content generation service"""
    return {
        "status": "healthy",
        "service": "content-generation",
        "timestamp": datetime.utcnow().isoformat()
    }