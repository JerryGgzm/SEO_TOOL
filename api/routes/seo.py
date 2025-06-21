"""SEO Module API Routes

This module implements the FastAPI routes for the SEO optimization system,
handling content optimization. The primary focus is on a comprehensive
optimization endpoint.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body, status
from fastapi.responses import JSONResponse
import logging

from database import get_data_flow_manager, DataFlowManager
from api.middleware import get_current_user, User
from modules.seo.service_integration import SEOService, create_enhanced_seo_service
from modules.seo.models import SEOContentType, SEOOptimizationLevel

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/seo", tags=["seo-optimization"])

# Dependency to get SEO service
async def get_seo_service(
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager)
) -> SEOService:
    """
    Initializes and returns the SEO service.
    Note: In a real application, dependencies like clients would be managed
    more robustly, perhaps via a centralized dependency injection system.
    """
    try:
        return create_enhanced_seo_service(
            twitter_client=None,
            user_service=None,
            data_flow_manager=data_flow_manager,
            llm_client=None, # The service should handle LLM client creation internally
            config={'llm_optimization_mode': 'comprehensive'}
        )
    except Exception as e:
        logger.error(f"Failed to create SEO service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SEO service initialization failed"
        )

@router.post("/optimize", summary="Optimize a single piece of content")
async def optimize_content(
    content: str = Body(..., description="Content to optimize"),
    content_type: SEOContentType = Body(default=SEOContentType.TWEET),
    optimization_level: SEOOptimizationLevel = Body(default=SEOOptimizationLevel.MODERATE),
    target_keywords: List[str] = Body(default=[], description="Target keywords to focus on"),
    current_user: User = Depends(get_current_user),
    service: SEOService = Depends(get_seo_service)
):
    """
    Optimizes a single piece of content for SEO.

    This is the primary endpoint for the SEO module. It takes raw content
    and applies a comprehensive set of SEO enhancements based on LLM analysis,
    including keyword integration and hashtag generation.
    """
    try:
        # Build the context required by the service
        context = await service._build_seo_context(current_user.id, content_type)
        context.niche_keywords = target_keywords
        
        # Call the core optimization logic from the service
        optimized_result = await service.enhance_content(
            content=content,
            context=context,
            optimization_level=optimization_level
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=optimized_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content optimization failed for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during content optimization: {e}"
        )

@router.post("/batch/optimize", summary="Optimize multiple pieces of content")
async def batch_optimize_content(
    content_list: List[Dict[str, Any]] = Body(..., description="List of content items to optimize. Each item should be a dict with 'content' and 'content_type' keys."),
    optimization_level: SEOOptimizationLevel = Body(default=SEOOptimizationLevel.MODERATE),
    current_user: User = Depends(get_current_user),
    service: SEOService = Depends(get_seo_service)
):
    """
    Optimizes a batch of content items in a single request.

    This endpoint is efficient for processing multiple pieces of content,
    such as optimizing a series of tweets or blog post drafts at once.
    """
    try:
        # Build a generic context for the batch job
        # Individual items could have more specific contexts if the model supports it
        base_context = await service._build_seo_context(current_user.id, 'tweet') # default type
        
        optimization_requests = []
        for item in content_list:
            # You could potentially customize context per item here
            item_context = base_context.copy(update={"niche_keywords": item.get("keywords", [])})
            optimization_requests.append({
                "content": item["content"],
                "context": item_context
            })
            
        results = await service.batch_enhance_content(
            requests=optimization_requests,
            optimization_level=optimization_level
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Batch optimization completed.",
                "results": results,
                "total_items": len(results)
            }
        )
    except Exception as e:
        logger.error(f"Batch content optimization failed for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during batch optimization: {e}"
        )

@router.get("/health", summary="Health check for the SEO service")
async def health_check():
    """
    A simple health check endpoint to verify that the service is running.
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ok", "service": "seo-optimization"}
    )