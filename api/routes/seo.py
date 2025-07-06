"""SEO Module API Routes

This module implements the FastAPI routes for the SEO optimization system.
It is aligned with the modern implementation demonstrated in the project's
demo scripts, using LLMSEOIntelligence directly.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import logging
import os
from dotenv import load_dotenv

from modules.llm.client import LLMClient
from config.llm_selector import llm_selector
from api.middleware import User
from modules.seo.llm_intelligence import LLMSEOIntelligence
from modules.seo.models import (
    SEOContentType,
    SEOOptimizationLevel,
    SEOAnalysisContext,
    SEOOptimizationRequest,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/seo", tags=["seo-optimization"])


# --- Dependency Override for Demo/Testing ---
async def override_get_current_user() -> User:
    """A mock dependency for demo purposes."""
    return User(
        id="demo-user-id", username="demouser", email="demo@example.com", is_admin=True
    )


# Dependency to get the core LLM-based SEO service
def get_seo_intelligence() -> LLMSEOIntelligence:
    """
    Initializes and returns the LLMSEOIntelligence service.

    This follows the pattern from `demo_integrated_workflow.py` and
    `demo_seo.py`, using the core intelligence module directly.
    """
    try:
        provider_name = llm_selector.get_preferred_provider()
        if not provider_name or not llm_selector.is_provider_available(provider_name):
            raise HTTPException(
                status_code=503, detail=f"LLM Provider '{provider_name}' not available according to selector."
            )

        # Get the API key AND model name and pass them to the client
        provider_config = llm_selector.get_provider_config(provider_name)
        api_key = os.getenv(provider_config.get('api_key_env'))
        
        # Use the specific model from .env if it exists, otherwise use config default
        model_name = provider_config.get('model')
        if provider_name == 'gemini':
            model_name = os.getenv('GEMINI_MODEL_NAME', model_name)

        llm_client = LLMClient(provider=provider_name, api_key=api_key, model_name=model_name)

        if not llm_client.is_available():
            raise HTTPException(
                status_code=503,
                detail=f"LLM client for '{provider_name}' failed to initialize. Check API keys.",
            )

        return LLMSEOIntelligence(
            llm_client=llm_client, llm_provider=provider_name
        )
    except HTTPException:
        raise  # Re-raise HTTPException directly to preserve status code and details
    except Exception as e:
        logger.error(f"Failed to create LLMSEOIntelligence service: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A critical error occurred during SEO service initialization.",
        )


@router.post("/optimize", summary="Optimize a single piece of content", response_model=Dict)
async def optimize_content(
    content: str = Body(..., description="Content to optimize"),
    content_type: SEOContentType = Body(default=SEOContentType.TWEET),
    optimization_level: SEOOptimizationLevel = Body(
        default=SEOOptimizationLevel.MODERATE
    ),
    target_keywords: List[str] = Body(
        default=[], description="Target keywords to focus on"
    ),
    current_user: User = Depends(override_get_current_user),
    service: LLMSEOIntelligence = Depends(get_seo_intelligence),
):
    """
    Optimizes a single piece of content for SEO using the core LLM intelligence.
    """
    try:
        # Build the context and request objects required by the service
        context = SEOAnalysisContext(
            content_type=content_type,
            target_audience="general",  # Placeholder, could be enhanced
            niche_keywords=target_keywords,
        )
        request = SEOOptimizationRequest(
            content=content,
            content_type=content_type,
            optimization_level=optimization_level,
            target_keywords=target_keywords,
        )

        optimized_result = await service.enhance_content_with_llm(request, context)
        
        # Use jsonable_encoder to handle Pydantic models in the response
        json_compatible_content = jsonable_encoder(optimized_result)
        return JSONResponse(status_code=status.HTTP_200_OK, content=json_compatible_content)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Content optimization failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during content optimization: {e}",
        )


@router.post("/batch/optimize", summary="Optimize multiple pieces of content", response_model=Dict)
async def batch_optimize_content(
    content_list: List[Dict[str, Any]] = Body(
        ...,
        description="List of content items. Each item must have 'content', and can have 'content_type' and 'keywords'.",
    ),
    optimization_level: SEOOptimizationLevel = Body(
        default=SEOOptimizationLevel.MODERATE
    ),
    current_user: User = Depends(override_get_current_user),
    service: LLMSEOIntelligence = Depends(get_seo_intelligence),
):
    """
    Optimizes a batch of content items in a single request.
    """
    results = []
    try:
        for item in content_list:
            if "content" not in item:
                # Skip invalid items or raise error? Raising is clearer.
                raise HTTPException(
                    status_code=422,
                    detail="Each item in content_list must have a 'content' key.",
                )

            # Safely get content_type with a default
            content_type_str = item.get("content_type", "tweet")
            
            # Create a context and request for each item
            context = SEOAnalysisContext(
                content_type=SEOContentType(content_type_str),
                target_audience="general", # Placeholder
                niche_keywords=item.get("keywords", []),
            )
            request = SEOOptimizationRequest(
                content=item["content"],
                content_type=SEOContentType(content_type_str),
                optimization_level=optimization_level,
                target_keywords=item.get("keywords", []),
            )
            
            # Await the optimization for each item
            result = await service.enhance_content_with_llm(request, context)
            results.append(result)

        # Use jsonable_encoder to handle Pydantic models in the results
        json_compatible_results = jsonable_encoder(results)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Batch optimization completed.",
                "results": json_compatible_results,
                "total_items": len(results),
            },
        )
    except Exception as e:
        logger.error(
            f"Batch content optimization failed for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during batch optimization: {e}",
        )


@router.get("/health", summary="Health check for the SEO service")
async def health_check():
    """
    A simple health check endpoint to verify that the service is running.
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ok", "service": "seo-optimization"},
    )