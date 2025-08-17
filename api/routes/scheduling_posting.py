"""Scheduling and Posting Module - FastAPI Routes

This module implements the FastAPI routes for the scheduling and posting system,
handling content scheduling, immediate publishing, and queue management.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, BackgroundTasks
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

from database import get_data_flow_manager, DataFlowManager
from modules.twitter_api import TwitterAPIClient
from modules.user_profile.service import UserProfileService
from api.middleware import get_twitter_client
from api.middleware import get_user_service
from api.middleware import get_current_user, User

from modules.scheduling_posting.service import SchedulingPostingService
from modules.scheduling_posting.models import (
    ScheduleRequest, BatchScheduleRequest, PublishRequest, BatchPublishRequest,
    StatusUpdateRequest, RuleCheckRequest, PublishStatus
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/scheduling", tags=["scheduling-posting"])

# Dependency to get scheduling service
async def get_scheduling_service(
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager),
    twitter_client: TwitterAPIClient = Depends(get_twitter_client),
    user_service: UserProfileService = Depends(get_user_service),
    current_user: User = Depends(get_current_user)
) -> SchedulingPostingService:
    """Get scheduling posting service with dependencies"""
    try:
        return SchedulingPostingService(
            data_flow_manager=data_flow_manager,
            twitter_client=twitter_client,
            user_profile_service=user_service,
            analytics_collector=None   # Optional parameter
        )
    except Exception as e:
        logger.error(f"Failed to create scheduling service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize scheduling service"
        )

@router.get("/pending")
async def get_pending_content(
    user_id: str = Query(..., description="User ID"),
    status: Optional[str] = Query(None, description="Status filter (approved, scheduled)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of items"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    service: SchedulingPostingService = Depends(get_scheduling_service)
):
    """
    Get pending content for publishing
    
    Returns content that is ready for scheduling or publishing,
    including approved drafts and scheduled items.
    """
    try:
        # Validate user access
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Validate status filter
        if status and status not in ['approved', 'scheduled']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status must be 'approved' or 'scheduled'"
            )
        
        # Get pending content
        pending_content = await service.get_pending_content(user_id, status, limit, offset)
        
        logger.info(f"Retrieved {len(pending_content)} pending items for user {user_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Pending content retrieved successfully",
                "user_id": user_id,
                "status_filter": status,
                "content": pending_content,
                "total_count": len(pending_content),
                "limit": limit,
                "offset": offset
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pending content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending content"
        )

@router.post("/publish/{content_id}")
async def publish_content_immediately(
    content_id: str = Path(..., description="Content ID to publish"),
    force_publish: bool = Query(default=False, description="Force publish ignoring rules"),
    skip_rules_check: bool = Query(default=False, description="Skip publishing rules validation"),
    custom_message: Optional[str] = Query(None, description="Custom message override"),
    current_user: User = Depends(get_current_user),
    service: SchedulingPostingService = Depends(get_scheduling_service)
):
    """
    Publish content immediately
    
    Publishes approved content directly to Twitter without scheduling.
    Can optionally force publish to bypass publishing rules.
    """
    try:
        # Create publish request
        publish_request = PublishRequest(
            content_id=content_id,
            force_publish=force_publish,
            skip_rules_check=skip_rules_check,
            custom_message=custom_message
        )
        
        # Perform immediate publishing
        result = await service.publish_content_immediately(current_user.id, publish_request)
        
        if result.success:
            logger.info(f"Content {content_id} published successfully for user {current_user.id}")
            
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "message": result.message,
                    "content_id": content_id,
                    "posted_tweet_id": result.posted_tweet_id,
                    "posted_at": result.posted_at.isoformat() if result.posted_at else None,
                    "success": True
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "message": result.message,
                    "content_id": content_id,
                    "error_code": result.error_code,
                    "success": False
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to publish content immediately: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish content"
        )

@router.post("/schedule/{content_id}")
async def schedule_content(
    schedule_request: ScheduleRequest,
    content_id: str = Path(..., description="Content ID to schedule"),
    current_user: User = Depends(get_current_user),
    service: SchedulingPostingService = Depends(get_scheduling_service)
):
    """
    Schedule content for publishing at a specific time
    
    Schedules approved content for automatic publishing at the specified time.
    Validates against publishing rules and user preferences.
    """
    try:
        # Ensure content_id matches the path parameter
        if schedule_request.content_id != content_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content ID in path must match request body"
            )
        
        # Schedule the content
        result = await service.schedule_content(current_user.id, schedule_request)
        
        if result.success:
            logger.info(f"Content {content_id} scheduled successfully for user {current_user.id}")
            
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "message": result.message,
                    "content_id": content_id,
                    "scheduled_content_id": result.scheduled_content_id,
                    "scheduled_time": result.scheduled_time.isoformat() if result.scheduled_time else None,
                    "timezone": schedule_request.timezone,
                    "success": True
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "message": result.message,
                    "content_id": content_id,
                    "rule_violations": result.rule_violations,
                    "success": False
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to schedule content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule content"
        )

@router.delete("/cancel/{content_id}")
async def cancel_scheduled_content(
    content_id: str = Path(..., description="Content ID to cancel"),
    current_user: User = Depends(get_current_user),
    service: SchedulingPostingService = Depends(get_scheduling_service)
):
    """
    Cancel scheduled content
    
    Cancels a previously scheduled content item, preventing it from being published.
    Only works for content that hasn't been published yet.
    """
    try:
        # Cancel the scheduled content
        success = await service.cancel_scheduled_content(current_user.id, content_id)
        
        if success:
            logger.info(f"Scheduled content {content_id} cancelled for user {current_user.id}")
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message": "Scheduled content cancelled successfully",
                    "content_id": content_id,
                    "cancelled_at": datetime.utcnow().isoformat(),
                    "success": True
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "message": "Failed to cancel scheduled content. Content may not exist, already be published, or access denied.",
                    "content_id": content_id,
                    "success": False
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel scheduled content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel scheduled content"
        )

@router.get("/rules/check")
async def check_publishing_rules(
    user_id: str = Query(..., description="User ID"),
    content_type: Optional[str] = Query(None, description="Content type"),
    content_id: Optional[str] = Query(None, description="Specific content ID"),
    proposed_time: Optional[datetime] = Query(None, description="Proposed publishing time"),
    current_user: User = Depends(get_current_user),
    service: SchedulingPostingService = Depends(get_scheduling_service)
):
    """
    Check publishing rules for content
    
    Validates whether content can be published at a specific time,
    checking against user preferences, daily limits, and other rules.
    """
    try:
        # Validate user access
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check publishing rules
        rule_result = await service.check_publishing_rules(
            user_id=user_id,
            content_id=content_id,
            proposed_time=proposed_time,
            content_type=content_type
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Publishing rules checked successfully",
                "user_id": user_id,
                "can_publish": rule_result.can_publish,
                "violations": rule_result.violations,
                "recommendations": rule_result.recommendations,
                "suggested_times": [t.isoformat() for t in rule_result.suggested_times],
                "next_available_slot": rule_result.next_available_slot.isoformat() if rule_result.next_available_slot else None,
                "current_daily_count": rule_result.current_daily_count,
                "daily_limit": rule_result.daily_limit
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check publishing rules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check publishing rules"
        )

@router.post("/publish/batch")
async def batch_publish_content(
    batch_request: BatchPublishRequest,
    current_user: User = Depends(get_current_user),
    service: SchedulingPostingService = Depends(get_scheduling_service)
):
    """
    Batch publish or schedule multiple content items
    
    Publishes or schedules multiple content items with optional staggering.
    Useful for bulk content management operations.
    """
    try:
        # Validate batch size
        if len(batch_request.content_ids) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size cannot exceed 50 items"
            )
        
        # Process batch operation
        result = await service.batch_publish_content(current_user.id, batch_request)
        
        logger.info(f"Batch publish completed for user {current_user.id}: "
                   f"{result.successful_items}/{result.total_items} successful")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": result.message,
                "total_items": result.total_items,
                "successful_items": result.successful_items,
                "failed_items": result.failed_items,
                "results": result.results,
                "batch_completed_at": datetime.utcnow().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch publish failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch publish operation failed"
        )

@router.post("/schedule/batch")
async def batch_schedule_content(
    batch_request: BatchScheduleRequest,
    current_user: User = Depends(get_current_user),
    service: SchedulingPostingService = Depends(get_scheduling_service)
):
    """
    Batch schedule multiple content items
    
    Schedules multiple content items with automatic time distribution
    and optional staggering between posts.
    """
    try:
        # Validate batch size
        if len(batch_request.content_ids) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size cannot exceed 50 items"
            )
        
        # Process batch scheduling
        result = await service.batch_schedule_content(current_user.id, batch_request)
        
        logger.info(f"Batch scheduling completed for user {current_user.id}: "
                   f"{result.successful_items}/{result.total_items} successful")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": result.message,
                "total_items": result.total_items,
                "successful_items": result.successful_items,
                "failed_items": result.failed_items,
                "results": result.results,
                "batch_completed_at": datetime.utcnow().isoformat(),
                "stagger_minutes": batch_request.stagger_minutes
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch scheduling failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch scheduling operation failed"
        )

@router.get("/history")
async def get_publishing_history(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of items"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    service: SchedulingPostingService = Depends(get_scheduling_service)
):
    """
    Get publishing history for a user
    
    Returns a paginated list of previously scheduled and published content
    with status information and timestamps.
    """
    try:
        # Validate user access
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get publishing history
        history = await service.get_publishing_history(user_id, limit, offset)
        
        # Convert to dict format for JSON response
        history_data = []
        for item in history:
            item_dict = {
                "content_id": item.content_id,
                "scheduled_content_id": item.scheduled_content_id,
                "content_preview": item.content_preview,
                "scheduled_time": item.scheduled_time.isoformat(),
                "posted_at": item.posted_at.isoformat() if item.posted_at else None,
                "status": item.status.value,
                "posted_tweet_id": item.posted_tweet_id,
                "platform": item.platform,
                "error_message": item.error_message,
                "retry_count": item.retry_count,
                "tags": item.tags
            }
            history_data.append(item_dict)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Publishing history retrieved successfully",
                "user_id": user_id,
                "history": history_data,
                "total_count": len(history_data),
                "limit": limit,
                "offset": offset
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get publishing history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve publishing history"
        )

@router.put("/status/{content_id}")
async def update_publishing_status(
    status_request: StatusUpdateRequest,
    content_id: str = Path(..., description="Content ID"),
    current_user: User = Depends(get_current_user),
    service: SchedulingPostingService = Depends(get_scheduling_service)
):
    """
    Update publishing status for content
    
    Updates the publishing status of scheduled content, typically used
    by background processes to report publishing results.
    """
    try:
        # Update publishing status
        success = await service.update_publishing_status(
            current_user.id, content_id, status_request
        )
        
        if success:
            logger.info(f"Publishing status updated for content {content_id}: {status_request.status}")
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message": "Publishing status updated successfully",
                    "content_id": content_id,
                    "new_status": status_request.status.value,
                    "posted_tweet_id": status_request.posted_tweet_id,
                    "updated_at": datetime.utcnow().isoformat(),
                    "success": True
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "message": "Failed to update publishing status",
                    "content_id": content_id,
                    "success": False
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update publishing status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update publishing status"
        )

@router.get("/queue/info")
async def get_queue_information(
    user_id: str = Query(..., description="User ID"),
    current_user: User = Depends(get_current_user),
    service: SchedulingPostingService = Depends(get_scheduling_service)
):
    """
    Get information about the publishing queue
    
    Returns statistics about pending, scheduled, and failed content
    in the publishing queue for the user.
    """
    try:
        # Validate user access
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get queue information
        queue_info = await service.get_queue_info(user_id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Queue information retrieved successfully",
                "user_id": user_id,
                "total_pending": queue_info.total_pending,
                "total_scheduled": queue_info.total_scheduled,
                "next_publish_time": queue_info.next_publish_time.isoformat() if queue_info.next_publish_time else None,
                "queue_by_status": queue_info.queue_by_status,
                "upcoming_24h": queue_info.upcoming_24h,
                "overdue_count": queue_info.overdue_count,
                "retry_queue_size": queue_info.retry_queue_size,
                "retrieved_at": datetime.utcnow().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get queue information: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve queue information"
        )



@router.post("/queue/process")
async def trigger_queue_processing(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: SchedulingPostingService = Depends(get_scheduling_service)
):
    """
    Trigger manual queue processing
    
    Manually triggers the publishing queue processing for immediate
    publication of due content. Normally runs automatically.
    """
    try:
        # Only admins can trigger manual queue processing
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Add queue processing to background tasks
        background_tasks.add_task(service.process_publishing_queue)
        
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "message": "Queue processing triggered successfully",
                "triggered_by": current_user.id,
                "triggered_at": datetime.utcnow().isoformat(),
                "status": "processing"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger queue processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger queue processing"
        )

@router.get("/health")
async def health_check():
    """
    Health check endpoint for scheduling service
    
    Returns service status and configuration information
    """
    try:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "healthy",
                "service": "scheduling-posting",
                "version": "1.0.0",
                "features": [
                    "content_scheduling",
                    "immediate_publishing",
                    "batch_operations",
                    "queue_management",
                    "rule_validation",
                    "publishing_analytics",
                    "retry_handling"
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service health check failed"
        )

@router.get("/status/{scheduled_id}")
async def get_scheduled_content_status(
    scheduled_id: str = Path(..., description="Scheduled content ID"),
    current_user: User = Depends(get_current_user),
    service: SchedulingPostingService = Depends(get_scheduling_service)
):
    """
    Get the status of scheduled content
    
    Returns current status, execution details, and any errors for scheduled content.
    Used to monitor the progress of scheduled publishing tasks.
    """
    try:
        # Get scheduled content from database
        scheduled_content = service.data_flow_manager.get_scheduled_content_by_id(scheduled_id)
        
        if not scheduled_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduled content not found"
            )
        
        # Verify user access
        if str(scheduled_content.founder_id) != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Note: scheduled_content is now GeneratedContentDraft itself (after table consolidation)
        # No need to fetch content_draft separately
        
        # Prepare response
        response_data = {
            "scheduled_id": scheduled_id,
            "status": scheduled_content.status,
            "scheduled_time": scheduled_content.scheduled_post_time.isoformat() if scheduled_content.scheduled_post_time else None,
            "created_at": scheduled_content.created_at.isoformat() if scheduled_content.created_at else None,
            "updated_at": scheduled_content.updated_at.isoformat() if hasattr(scheduled_content, 'updated_at') and scheduled_content.updated_at else None,
            "retry_count": getattr(scheduled_content, 'retry_count', 0),
            "posted_tweet_id": getattr(scheduled_content, 'posted_tweet_id', None),
            "error_message": getattr(scheduled_content, 'error_message', None),
            "priority": getattr(scheduled_content, 'priority', 5),
            "tags": getattr(scheduled_content, 'tags_list', [])
        }
        
        # Add content information (scheduled_content is the content draft)
        response_data["content_info"] = {
            "content_id": str(scheduled_content.id),
            "content_type": scheduled_content.content_type,
            "content_preview": (scheduled_content.final_text)[:100] + "..." 
                             if scheduled_content.final_text else "No content",
            "content_status": scheduled_content.status
        }
        
        logger.info(f"Retrieved status for scheduled content {scheduled_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scheduled content status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve scheduled content status"
        )