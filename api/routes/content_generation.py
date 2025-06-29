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
from config.llm_config import LLM_CONFIG, DEFAULT_LLM_PROVIDER

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
    
    # 初始化真实数据库的data_flow_manager
    data_flow_manager = get_data_flow_manager()
    return ContentGenerationService(
        data_flow_manager=data_flow_manager,
        user_service=None,
        llm_provider=llm_provider
    )

@router.post("/generate")
async def generate_content(
    request: ContentGenerationRequest,
    llm_provider: str = DEFAULT_LLM_PROVIDER,
    current_user: User = Depends(get_current_user),
    service: ContentGenerationService = Depends(get_content_service)
) -> Dict[str, Any]:
    """Generate content based on request with unified API
    
    Args:
        request: Content generation request with generation_mode
        llm_provider: LLM provider to use (default: from config)
        current_user: Current authenticated user
        service: Content generation service
        
    Returns:
        Response with generated content draft IDs and metadata
    """
    try:
        # Validate user access
        if current_user.id != request.founder_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Generate content based on mode
        if request.generation_mode == GenerationMode.VIRAL_FOCUSED:
            draft_ids = await service.generate_viral_focused_content(
                founder_id=request.founder_id,
                trend_id=request.trend_id,
                content_type=request.content_type,
                quantity=request.quantity
            )
        elif request.generation_mode == GenerationMode.BRAND_FOCUSED:
            draft_ids = await service.generate_brand_focused_content(
                founder_id=request.founder_id,
                custom_brand_voice=request.custom_brand_voice,
                content_type=request.content_type,
                quantity=request.quantity
            )
        else:
            # Standard and other modes
            draft_ids = await service.generate_content(
                founder_id=request.founder_id,
                trend_id=request.trend_id,
                content_type=request.content_type,
                generation_mode=request.generation_mode,
                quantity=request.quantity
            )
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": f"{request.generation_mode.value.replace('_', ' ').title()} content generated successfully",
                "draft_ids": draft_ids,
                "count": len(draft_ids),
                "generation_mode": request.generation_mode.value,
                "content_type": request.content_type.value,
                "founder_id": request.founder_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content generation failed: {str(e)}"
        )

@router.get("/drafts/{draft_id}")
async def get_draft(
    draft_id: str = Path(..., description="Draft ID"),
    current_user: User = Depends(get_current_user),
    service: ContentGenerationService = Depends(get_content_service)
):
    """
    Get content draft by ID - Unified draft management
    
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

@router.put("/drafts/{draft_id}")
async def update_draft(
    draft_id: str = Path(..., description="Draft ID"),
    update_data: Dict[str, Any] = ...,
    current_user: User = Depends(get_current_user),
    service: ContentGenerationService = Depends(get_content_service)
):
    """
    Update draft - Unified draft management
    
    Supports updating quality score, content, metadata, and status.
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
        
        # Handle different update types
        success = False
        update_type = update_data.get("update_type", "quality_score")
        
        if update_type == "quality_score":
            quality_score = update_data.get("quality_score")
            if quality_score is not None:
                success = await service.update_draft_quality_score(draft_id, quality_score)
        elif update_type == "status":
            # This would integrate with review optimization module
            status = update_data.get("status")
            if status:
                # TODO: Implement status update
                success = True
        elif update_type == "content":
            # This would allow content editing
            content = update_data.get("content")
            if content:
                # TODO: Implement content update
                success = True
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update draft"
            )
        
        return {
            "message": "Draft updated successfully",
            "draft_id": draft_id,
            "update_type": update_type,
            "updated_fields": list(update_data.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update draft: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update draft"
        )

@router.delete("/drafts/{draft_id}")
async def delete_draft(
    draft_id: str = Path(..., description="Draft ID"),
    current_user: User = Depends(get_current_user),
    service: ContentGenerationService = Depends(get_content_service)
):
    """
    Delete draft - Unified draft management
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
        
        # TODO: Implement draft deletion
        success = True  # Placeholder
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete draft"
            )
        
        return {
            "message": "Draft deleted successfully",
            "draft_id": draft_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete draft: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete draft"
        )

@router.post("/drafts/{draft_id}/duplicate")
async def duplicate_draft(
    draft_id: str = Path(..., description="Draft ID"),
    current_user: User = Depends(get_current_user),
    service: ContentGenerationService = Depends(get_content_service)
):
    """
    Duplicate draft - Unified draft management
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
        
        # TODO: Implement draft duplication
        new_draft_id = f"duplicate_{draft_id}"  # Placeholder
        
        return {
            "message": "Draft duplicated successfully",
            "original_draft_id": draft_id,
            "new_draft_id": new_draft_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to duplicate draft: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to duplicate draft"
        )

@router.get("/drafts/founder/{founder_id}")
async def get_founder_drafts(
    founder_id: str = Path(..., description="Founder ID"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of drafts"),
    content_type: Optional[ContentType] = Query(None, description="Filter by content type"),
    quality_threshold: Optional[float] = Query(None, ge=0, le=1, description="Filter by quality threshold"),
    current_user: User = Depends(get_current_user),
    service: ContentGenerationService = Depends(get_content_service)
):
    """
    Get founder's drafts - Unified draft management
    
    Returns a list of drafts for a founder with optional filtering.
    """
    try:
        # Validate user access
        if current_user.id != founder_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get drafts
        drafts = service.get_drafts_by_founder(founder_id, limit)
        
        # Apply filters
        if content_type:
            drafts = [d for d in drafts if d.content_type == content_type]
        
        if quality_threshold is not None:
            drafts = [d for d in drafts if d.quality_score >= quality_threshold]
        
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
            "limit": limit,
            "filters": {
                "content_type": content_type.value if content_type else None,
                "quality_threshold": quality_threshold
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get founder drafts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve drafts"
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

# 保留原有的质量评分更新API作为兼容性
@router.put("/drafts/{draft_id}/quality-score")
async def update_draft_quality_score(
    draft_id: str = Path(..., description="Draft ID"),
    quality_score: float = Query(..., ge=0, le=1, description="Quality score"),
    current_user: User = Depends(get_current_user),
    service: ContentGenerationService = Depends(get_content_service)
):
    """
    Update quality score for a draft (Legacy API for compatibility)
    """
    return await update_draft(
        draft_id=draft_id,
        update_data={"update_type": "quality_score", "quality_score": quality_score},
        current_user=current_user,
        service=service
    )