"""Review Optimization Module - API Routes

This module implements the FastAPI routes for the review optimization system,
handling content review, approval, and optimization workflows.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse
import logging

from database import get_data_flow_manager, DataFlowManager
from modules.content_generation.service import ContentGenerationService
from modules.analytics.collector import AnalyticsCollector
from api.middleware import get_current_user, User

from modules.review_optimization.service import ReviewOptimizationService
from modules.review_optimization.models import (
    ContentDraftReview, ReviewDecisionRequest, BatchReviewRequest,
    ContentRegenerationRequest, ReviewHistoryItem,
    RegenerationResult, DraftStatus
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/review", tags=["review"])

# Dependency to get review service
async def get_review_service(
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager),
    current_user: User = Depends(get_current_user)
) -> ReviewOptimizationService:
    """Get review optimization service with dependencies"""
    try:
        # Initialize content generation service (if available)
        content_generation_service = None
        try:
            # user_service参数可为None或mock
            content_generation_service = ContentGenerationService(
                data_flow_manager=data_flow_manager,
                user_service=None  # 可根据需要注入真实user_service
            )
        except Exception as e:
            logger.warning(f"Content generation service not available: {e}")
        
        # Initialize analytics collector (if available)
        analytics_collector = None
        try:
            analytics_collector = AnalyticsCollector(data_flow_manager)
        except Exception as e:
            logger.warning(f"Analytics collector not available: {e}")
        
        return ReviewOptimizationService(
            data_flow_manager=data_flow_manager,
            content_generation_service=content_generation_service,
            analytics_collector=analytics_collector
        )
    except Exception as e:
        logger.error(f"Failed to create review service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize review service"
        )

@router.get("/pending", response_model=List[ContentDraftReview])
async def get_pending_drafts(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of drafts"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    service: ReviewOptimizationService = Depends(get_review_service)
):
    """
    Get pending content drafts for review
    
    Returns a list of content drafts that are pending review,
    sorted by priority and creation time.
    """
    try:
        # Validate user access
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get pending drafts
        pending_drafts = await service.get_pending_drafts(user_id, limit, offset)
        
        logger.info(f"Retrieved {len(pending_drafts)} pending drafts for user {user_id}")
        return pending_drafts
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pending drafts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending drafts"
        )

@router.post("/decision/batch")
async def submit_batch_review_decisions(
    batch_request: BatchReviewRequest = ...,
    current_user: User = Depends(get_current_user),
    service: ReviewOptimizationService = Depends(get_review_service)
):
    """
    Submit batch review decisions
    
    Processes multiple review decisions in a single request.
    Useful for bulk operations like reviewing a week's worth of content.
    """
    try:
        # Validate batch size
        if len(batch_request.decisions) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch request cannot be empty"
            )
        
        if len(batch_request.decisions) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size cannot exceed 50 decisions"
            )
        
        # Process batch decisions
        results = await service.submit_batch_review_decisions(
            batch_request, current_user.id
        )
        
        logger.info(f"Processed {len(results)} batch review decisions")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Batch review decisions processed",
                "processed_count": len(results),
                "results": results
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit batch review decisions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process batch review decisions"
        )

@router.post("/decision/{draft_id}")
async def submit_review_decision(
    draft_id: str = Path(..., description="Draft ID"),
    decision_request: ReviewDecisionRequest = ...,
    current_user: User = Depends(get_current_user),
    service: ReviewOptimizationService = Depends(get_review_service)
):
    """
    Submit a review decision for a content draft
    
    Processes the review decision (approve, edit_and_approve, reject)
    and triggers appropriate downstream workflows.
    """
    try:
        # Submit review decision
        success = await service.submit_review_decision(
            draft_id, current_user.id, decision_request
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to process review decision"
            )
        
        logger.info(f"Processed review decision for draft {draft_id}: {decision_request.decision}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Review decision processed successfully",
                "draft_id": draft_id,
                "decision": decision_request.decision.value
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit review decision: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process review decision"
        )

@router.get("/history", response_model=List[ReviewHistoryItem])
async def get_review_history(
    user_id: str = Query(..., description="User ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of items"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    service: ReviewOptimizationService = Depends(get_review_service)
):
    """
    Get review history for a user
    
    Returns a list of review history items including decisions,
    timestamps, and outcomes.
    """
    try:
        # Validate user access
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get review history
        history = await service.get_review_history(user_id, status, limit, offset)
        
        logger.info(f"Retrieved {len(history)} review history items for user {user_id}")
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get review history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve review history"
        )

@router.post("/regenerate/{draft_id}", response_model=RegenerationResult)
async def regenerate_content(
    draft_id: str = Path(..., description="Draft ID"),
    regeneration_request: ContentRegenerationRequest = ...,
    current_user: User = Depends(get_current_user),
    service: ReviewOptimizationService = Depends(get_review_service)
):
    """
    Regenerate content based on feedback
    
    Creates a new version of the content based on review feedback
    and improvement suggestions.
    """
    try:
        # Regenerate content
        result = await service.regenerate_content(
            draft_id, current_user.id, regeneration_request
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to regenerate content"
            )
        
        logger.info(f"Regenerated content for draft {draft_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to regenerate content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate content"
        )

@router.get("/new_result/{draft_id}")
async def get_regeneration_result(
    draft_id: str = Path(..., description="Original draft ID"),
    current_user: User = Depends(get_current_user),
    service: ReviewOptimizationService = Depends(get_review_service)
):
    """
    Get the result of content regeneration
    
    Returns the newly generated content and comparison with the original.
    """
    try:
        # Get regeneration result
        result = await service.get_regeneration_result(draft_id, current_user.id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Regeneration result not found"
            )
        
        logger.info(f"Retrieved regeneration result for draft {draft_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get regeneration result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve regeneration result"
        )
        