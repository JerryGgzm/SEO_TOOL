"""Content Generation API Routes

This module implements the FastAPI routes for the content generation system,
handling AI-powered content creation, optimization, and management workflows.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse
import logging

from database import get_data_flow_manager, DataFlowManager
from modules.seo.service_integration import SEOService
from auth import get_current_user, User

from modules.content_generation.service import ContentGenerationService
from modules.content_generation.models import (
    ContentGenerationRequest, ContentType, GenerationMode,
    ContentDraft, BrandVoice, SEOSuggestions
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/content", tags=["content-generation"])

# Dependency to get content generation service
async def get_content_service(
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager),
    current_user: User = Depends(get_current_user)
) -> ContentGenerationService:
    """Get content generation service with dependencies"""
    try:
        # Initialize SEO service (if available)
        seo_service = None
        try:
            # This would be properly injected in a real application
            seo_service = SEOService(
                twitter_client=None,  # Would be injected
                user_service=None,    # Would be injected
                data_flow_manager=data_flow_manager,
                llm_client=None       # Would come from config
            )
        except Exception as e:
            logger.warning(f"SEO service not available: {e}")
        
        return ContentGenerationService(
            data_flow_manager=data_flow_manager,
            seo_service=seo_service,
            llm_config={'provider': 'openai'}  # Would come from config
        )
    except Exception as e:
        logger.error(f"Failed to create content service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize content generation service"
        )

@router.post("/generate", response_model=List[str])
async def generate_content(
    request: ContentGenerationRequest,
    current_user: User = Depends(get_current_user),
    service: ContentGenerationService = Depends(get_content_service)
):
    """
    Generate AI-powered content based on trends and user context
    
    Creates content drafts using LLM and SEO optimization based on:
    - User's product information and brand voice
    - Current trending topics
    - SEO best practices
    - Content type specifications
    """
    try:
        # Validate user access
        if current_user.id != request.founder_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Generate content
        draft_ids = await service.generate_content_for_founder(
            request.founder_id, request
        )
        
        if not draft_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to generate content. Check your request parameters."
            )
        
        logger.info(f"Generated {len(draft_ids)} content drafts for user {request.founder_id}")
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Content generated successfully",
                "draft_ids": draft_ids,
                "count": len(draft_ids),
                "founder_id": request.founder_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content generation failed"
        )

@router.post("/generate/seo-optimized")
async def generate_seo_optimized_content(
    founder_id: str = Query(..., description="Founder ID"),
    content_type: ContentType = Query(default=ContentType.TWEET),
    trend_id: Optional[str] = Query(None, description="Specific trend to base content on"),
    optimization_level: str = Query(default="moderate", description="SEO optimization level"),
    quantity: int = Query(default=3, ge=1, le=10, description="Number of variations"),
    current_user: User = Depends(get_current_user),
    service: ContentGenerationService = Depends(get_content_service)
):
    """
    Generate SEO-optimized content with specific optimization level
    
    Uses advanced SEO optimization strategies including:
    - Keyword research and integration
    - Hashtag optimization
    - Trending topic alignment
    - Engagement optimization
    """
    try:
        # Validate user access
        if current_user.id != founder_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Generate SEO-optimized content
        draft_ids = await service.generate_seo_optimized_content(
            founder_id=founder_id,
            trend_id=trend_id,
            content_type=content_type,
            optimization_level=optimization_level,
            quantity=quantity
        )
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "SEO-optimized content generated successfully",
                "draft_ids": draft_ids,
                "count": len(draft_ids),
                "optimization_level": optimization_level,
                "content_type": content_type.value
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SEO-optimized content generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SEO-optimized content generation failed"
        )

@router.post("/generate/custom")
async def generate_custom_content(
    founder_id: str = Query(..., description="Founder ID"),
    content_type: ContentType = Query(..., description="Content type"),
    custom_keywords: List[str] = Query(..., description="Custom keywords"),
    custom_hashtags: List[str] = Query(..., description="Custom hashtags"),
    quantity: int = Query(default=2, ge=1, le=5, description="Number of variations"),
    current_user: User = Depends(get_current_user),
    service: ContentGenerationService = Depends(get_content_service)
):
    """
    Generate content with custom SEO parameters
    
    Allows users to specify exact keywords and hashtags for targeted content creation.
    """
    try:
        # Validate user access
        if current_user.id != founder_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Validate input
        if not custom_keywords and not custom_hashtags:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one keyword or hashtag must be provided"
            )
        
        # Generate custom content
        draft_ids = await service.generate_content_with_custom_seo(
            founder_id=founder_id,
            content_type=content_type,
            custom_keywords=custom_keywords,
            custom_hashtags=custom_hashtags,
            quantity=quantity
        )
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Custom content generated successfully",
                "draft_ids": draft_ids,
                "custom_keywords": custom_keywords,
                "custom_hashtags": custom_hashtags
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Custom content generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Custom content generation failed"
        )

@router.get("/drafts/{draft_id}")
async def get_draft(
    draft_id: str = Path(..., description="Draft ID"),
    current_user: User = Depends(get_current_user),
    service: ContentGenerationService = Depends(get_content_service)
):
    """
    Get content draft by ID
    
    Returns the full content draft including generation metadata,
    quality scores, and SEO suggestions.
    """
    try:
        # Get draft from database
        draft_data = service.data_flow_manager.content_repo.get_by_id(draft_id)
        
        if not draft_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        # Check user access
        if current_user.id != draft_data.founder_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Convert to response format
        return {
            "draft_id": draft_id,
            "content": draft_data.generated_text,
            "content_type": draft_data.content_type,
            "founder_id": draft_data.founder_id,
            "quality_score": draft_data.ai_generation_metadata.get('quality_score', 0),
            "seo_suggestions": draft_data.seo_suggestions,
            "generation_metadata": draft_data.ai_generation_metadata,
            "created_at": draft_data.created_at.isoformat(),
            "status": getattr(draft_data, 'status', 'draft')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get draft: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve draft"
        )

@router.post("/regenerate/{draft_id}")
async def regenerate_content(
    draft_id: str = Path(..., description="Draft ID"),
    feedback: str = Query(..., description="Feedback for regeneration"),
    seo_improvements: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    service: ContentGenerationService = Depends(get_content_service)
):
    """
    Regenerate content based on feedback
    
    Creates new content based on the original draft and user feedback,
    with optional SEO improvements.
    """
    try:
        # Regenerate content
        new_draft_id = await service.regenerate_content_with_seo_feedback(
            draft_id=draft_id,
            founder_id=current_user.id,
            feedback=feedback,
            seo_improvements=seo_improvements
        )
        
        if not new_draft_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to regenerate content"
            )
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Content regenerated successfully",
                "original_draft_id": draft_id,
                "new_draft_id": new_draft_id,
                "feedback_applied": feedback
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content regeneration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content regeneration failed"
        )

@router.get("/analytics/{founder_id}")
async def get_content_analytics(
    founder_id: str = Path(..., description="Founder ID"),
    days: int = Query(default=30, ge=1, le=90, description="Analysis period in days"),
    current_user: User = Depends(get_current_user),
    service: ContentGenerationService = Depends(get_content_service)
):
    """
    Get content generation analytics
    
    Returns comprehensive analytics including:
    - Generation statistics
    - Quality metrics
    - SEO performance
    - Approval rates
    """
    try:
        # Validate user access
        if current_user.id != founder_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get analytics
        analytics = service.get_seo_content_analytics(founder_id, days)
        
        return {
            "founder_id": founder_id,
            "period_days": days,
            "analytics": analytics,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content analytics retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve content analytics"
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
    current_user: User = Depends(get_current_user),
    service: ContentGenerationService = Depends(get_content_service)
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
        ideas = []
        for i in range(count):
            ideas.append({
                "id": f"idea_{i+1}",
                "title": f"Content idea {i+1}",
                "description": "AI-generated content idea based on current trends",
                "suggested_keywords": ["innovation", "technology", "growth"],
                "suggested_hashtags": ["#innovation", "#tech", "#startup"],
                "estimated_engagement": "high"
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