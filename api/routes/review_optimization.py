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

from api.middleware import get_current_user, User

from modules.review_optimization.service import ReviewOptimizationService
from modules.review_optimization.models import (
    ContentDraftReview, ReviewDecisionRequest, BatchReviewRequest,
    ContentRegenerationRequest, StatusUpdateRequest, ReviewHistoryItem,
    ReviewSummary, ReviewAnalytics, RegenerationResult, ReviewQueue,
    DraftStatus
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
            # This would be properly injected in a real application
            content_generation_service = ContentGenerationService(
                data_flow_manager=data_flow_manager,
                seo_service=None,  # Would be injected
                llm_config={'provider': 'openai'}  # Would come from config
            )
        except Exception as e:
            logger.warning(f"Content generation service not available: {e}")
        
        # ...existing code...
        return ReviewOptimizationService(
            data_flow_manager=data_flow_manager,
            content_generation_service=content_generation_service,
            analytics_collector=None
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

@router.get("/draft/{draft_id}", response_model=ContentDraftReview)
async def get_draft_details(
    draft_id: str = Path(..., description="Draft ID"),
    current_user: User = Depends(get_current_user),
    service: ReviewOptimizationService = Depends(get_review_service)
):
    """
    Get detailed information about a specific draft
    
    Returns comprehensive information about the draft including
    generation metadata, quality scores, and review history.
    """
    try:
        # Get draft details
        draft = await service.get_draft_details(draft_id, current_user.id)
        
        if not draft:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found or access denied"
            )
        
        logger.info(f"Retrieved draft details for {draft_id}")
        return draft
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get draft details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve draft details"
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
        
        # Submit batch decisions
        results = await service.submit_batch_review_decisions(
            current_user.id, batch_request
        )
        
        # Count successes and failures
        successful_count = sum(1 for success in results.values() if success)
        failed_count = len(results) - successful_count
        
        logger.info(f"Processed batch review: {successful_count} successful, {failed_count} failed")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Batch review decisions processed",
                "total_decisions": len(batch_request.decisions),
                "successful_decisions": successful_count,
                "failed_decisions": failed_count,
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
    
    Returns a paginated list of previously reviewed content
    with filtering options by status.
    """
    try:
        # Validate user access
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Validate status filter
        if status and status not in [s.value for s in DraftStatus]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter: {status}"
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
    
    Creates new content based on the original draft and user feedback,
    maintaining the context while addressing specific improvement areas.
    """
    try:
        # Regenerate content
        result = await service.regenerate_content(
            draft_id, current_user.id, regeneration_request
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to regenerate content. Check if draft exists and regeneration limit not exceeded."
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
    
    Retrieves the newly generated content and metadata
    for a previously regenerated draft.
    """
    try:
        # Get original draft to find regeneration info
        original_draft = await service.get_draft_details(draft_id, current_user.id)
        
        if not original_draft:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Original draft not found"
            )
        
        # Check if draft was regenerated
        regeneration_info = original_draft.generation_metadata.get('regeneration_info')
        if not regeneration_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No regeneration found for this draft"
            )
        
        # Get new draft
        new_draft_id = regeneration_info.get('new_draft_id')
        if not new_draft_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Regeneration result not available"
            )
        
        new_draft = await service.get_draft_details(new_draft_id, current_user.id)
        if not new_draft:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Regenerated draft not found"
            )
        
        # Create regeneration result
        result = RegenerationResult(
            draft_id=draft_id,
            new_content=new_draft.current_content,
            improvements_made=regeneration_info.get('improvements_made', []),
            generation_metadata=new_draft.generation_metadata,
            quality_score=new_draft.quality_score,
            seo_suggestions=new_draft.seo_suggestions
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

@router.put("/status/{draft_id}")
async def update_draft_status(
    draft_id: str = Path(..., description="Draft ID"),
    status_request: StatusUpdateRequest = ...,
    current_user: User = Depends(get_current_user),
    service: ReviewOptimizationService = Depends(get_review_service)
):
    """
    Update draft status
    
    Updates the status of a content draft and records
    any associated metadata or notes.
    """
    try:
        # Update draft status
        success = await service.update_draft_status(
            draft_id, current_user.id, status_request
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update draft status"
            )
        
        logger.info(f"Updated status for draft {draft_id} to {status_request.status}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "draft_id": draft_id,
                    "new_status": status_request.status.value,
                    "updated_at": "2024-01-15T10:00:00Z"
                },
                "message": "草稿状态已更新",
                "timestamp": "2024-01-15T10:00:00Z"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update draft status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update draft status"
        )
        