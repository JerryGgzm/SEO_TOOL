"""Scheduling and Posting Module - Service Layer

This service handles the business logic for content scheduling and publishing,
integrating with Twitter API, Rules Engine, and Data Flow Manager.
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
import logging
import json
from concurrent.futures import ThreadPoolExecutor
import time

from database import DataFlowManager
from modules.twitter_api import TwitterAPIClient, TwitterAPIError
from modules.user_profile import UserProfileService

from .rules_engine import InternalRulesEngine
from .models import (
    ScheduledContent, PublishStatus, ScheduleRequest, BatchScheduleRequest,
    PublishRequest, BatchPublishRequest, StatusUpdateRequest,
    PublishingHistoryItem, PublishingAnalytics, RuleCheckRequest,
    RuleCheckResult, SchedulingQueueInfo, AutoScheduleSettings,
    PublishingConfiguration, PublishingMetrics, SchedulingRule,
    ContentQueueItem, ScheduleResponse, PublishResponse,
    BatchOperationResponse, PublishingError, SchedulingPreferences
)

logger = logging.getLogger(__name__)

class SchedulingPostingService:
    """
    Service for handling content scheduling and publishing workflows
    """
    
    def __init__(self, 
                 data_flow_manager: DataFlowManager,
                 twitter_client: TwitterAPIClient,
                 user_profile_service: UserProfileService,
                 analytics_collector=None):
        
        self.data_flow_manager = data_flow_manager
        self.twitter_client = twitter_client
        self.user_profile_service = user_profile_service
        self.analytics_collector = analytics_collector
        
        # Initialize internal rules engine
        self.rules_engine = InternalRulesEngine(data_flow_manager)
        
        # Configuration
        self.config = PublishingConfiguration()
        
        # Thread pool for concurrent publishing
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_publishes)
        
        # Queue processing state
        self._queue_processing = False
        self._queue_lock = asyncio.Lock()
    
    # ==================== Content Scheduling ====================
    
    async def get_pending_content(self, user_id: str, status: Optional[str] = None,
                                limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get pending content for publishing
        
        Args:
            user_id: User ID
            status: Optional status filter ('approved', 'scheduled')
            limit: Maximum number of items
            offset: Offset for pagination
            
        Returns:
            List of pending content items
        """
        try:
            logger.info(f"Getting pending content for user {user_id}")
            
            # Get content drafts that are ready for publishing
            if status:
                status_filter = [status]
            else:
                status_filter = ['approved', 'scheduled']
            
            pending_content = []
            
            # Get from content drafts table
            drafts = self.data_flow_manager.get_content_drafts_by_status(
                user_id, status_filter, limit, offset
            )
            
            for draft in drafts:
                # Get associated scheduled content if exists
                scheduled_info = self.data_flow_manager.get_scheduled_content_by_draft_id(
                    str(draft.id)
                )
                
                content_item = {
                    'content_id': str(draft.id),
                    'content_type': draft.content_type,
                    'content_text': draft.final_text,
                    'status': draft.status,
                    'quality_score': getattr(draft, 'quality_score', None),
                    'created_at': draft.created_at.isoformat(),
                    'tags': getattr(draft, 'tags', []) or [],
                    'scheduled_info': None
                }
                
                if scheduled_info:
                    content_item['scheduled_info'] = {
                        'scheduled_content_id': str(scheduled_info.id),
                        'scheduled_time': scheduled_info.scheduled_time.isoformat(),
                        'status': scheduled_info.status,
                        'retry_count': scheduled_info.retry_count,
                        'posted_tweet_id': scheduled_info.posted_tweet_id
                    }
                
                pending_content.append(content_item)
            
            return pending_content
            
        except Exception as e:
            logger.error(f"Failed to get pending content: {e}")
            return []
    
    async def schedule_content(self, user_id: str, schedule_request: ScheduleRequest) -> ScheduleResponse:
        """
        Schedule content for publishing at a specific time
        
        Args:
            user_id: User ID
            schedule_request: Scheduling request
            
        Returns:
            Scheduling response
        """
        try:
            logger.info(f"Scheduling content {schedule_request.content_id} for user {user_id}")
            
            # Validate content exists and belongs to user
            content_draft = self.data_flow_manager.get_content_draft_by_id(schedule_request.content_id)
            if not content_draft or str(content_draft.founder_id) != str(user_id):
                return ScheduleResponse(
                    success=False,
                    message="Content not found or access denied"
                )
            
            # Check if content is in valid status for scheduling
            if content_draft.status not in ['approved']:
                return ScheduleResponse(
                    success=False,
                    message=f"Content status '{content_draft.status}' is not valid for scheduling"
                )
            
            # Check publishing rules
            rule_check = await self.check_publishing_rules(
                user_id, schedule_request.content_id, schedule_request.scheduled_time
            )
            
            if not rule_check.can_publish:
                return ScheduleResponse(
                    success=False,
                    message="Scheduling violates publishing rules",
                    rule_violations=rule_check.violations
                )
            
            # Create scheduled content entry
            scheduled_content = ScheduledContent(
                content_draft_id=schedule_request.content_id,
                founder_id=user_id,
                scheduled_time=schedule_request.scheduled_time,
                status=PublishStatus.SCHEDULED,
                created_by=user_id,
                priority=schedule_request.priority,
                tags=schedule_request.tags
            )
            
            # Save to database
            saved_id = self.data_flow_manager.create_scheduled_content(scheduled_content.dict())
            
            if saved_id:
                # Update content draft status
                self.data_flow_manager.update_content_draft(
                    schedule_request.content_id,
                    {'status': 'scheduled', 'scheduled_post_time': schedule_request.scheduled_time}
                )
                
                # Record analytics
                await self._record_scheduling_analytics(user_id, 'content_scheduled')
                
                return ScheduleResponse(
                    success=True,
                    scheduled_content_id=saved_id,
                    scheduled_time=schedule_request.scheduled_time,
                    message="Content scheduled successfully"
                )
            else:
                return ScheduleResponse(
                    success=False,
                    message="Failed to save scheduled content"
                )
                
        except Exception as e:
            logger.error(f"Failed to schedule content: {e}")
            return ScheduleResponse(
                success=False,
                message=f"Scheduling failed: {str(e)}"
            )
    
    async def cancel_scheduled_content(self, user_id: str, content_id: str) -> bool:
        """Cancel scheduled content"""
        try:
            # Get scheduled content
            scheduled_content = self.data_flow_manager.get_scheduled_content_by_draft_id(content_id)
            
            if not scheduled_content or scheduled_content.founder_id != user_id:
                return False
            
            # Check if already published
            if scheduled_content.status == PublishStatus.POSTED:
                logger.warning(f"Cannot cancel already published content {content_id}")
                return False
            
            # Update status to cancelled
            success = self.data_flow_manager.update_scheduled_content(
                str(scheduled_content.id),
                {
                    'status': PublishStatus.CANCELLED.value,
                    'updated_at': datetime.utcnow()
                }
            )
            
            if success:
                # Update content draft status back to approved
                self.data_flow_manager.update_content_draft(
                    content_id,
                    {'status': 'approved', 'scheduled_post_time': None}
                )
                
                # Record analytics
                await self._record_scheduling_analytics(user_id, 'content_cancelled')
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to cancel scheduled content: {e}")
            return False
    
    async def batch_schedule_content(self, user_id: str, 
                                   batch_request: BatchScheduleRequest) -> BatchOperationResponse:
        """Schedule multiple content items"""
        try:
            logger.info(f"Batch scheduling {len(batch_request.content_ids)} items for user {user_id}")
            
            results = {}
            successful_items = 0
            
            for i, content_id in enumerate(batch_request.content_ids):
                try:
                    # Calculate staggered time
                    if batch_request.schedule_time:
                        scheduled_time = batch_request.schedule_time + timedelta(
                            minutes=i * batch_request.stagger_minutes
                        )
                    else:
                        # Auto-schedule based on preferences
                        scheduled_time = await self._calculate_optimal_schedule_time(
                            user_id, content_id
                        )
                    
                    # Create individual schedule request
                    schedule_request = ScheduleRequest(
                        content_id=content_id,
                        scheduled_time=scheduled_time,
                        timezone=batch_request.timezone
                    )
                    
                    # Schedule individual item
                    result = await self.schedule_content(user_id, schedule_request)
                    results[content_id] = result
                    
                    if result.success:
                        successful_items += 1
                        
                except Exception as e:
                    logger.error(f"Failed to schedule content {content_id}: {e}")
                    results[content_id] = ScheduleResponse(
                        success=False,
                        message=f"Scheduling failed: {str(e)}"
                    )
            
            return BatchOperationResponse(
                total_items=len(batch_request.content_ids),
                successful_items=successful_items,
                failed_items=len(batch_request.content_ids) - successful_items,
                results=results,
                message=f"Batch scheduling completed: {successful_items}/{len(batch_request.content_ids)} successful"
            )
            
        except Exception as e:
            logger.error(f"Batch scheduling failed: {e}")
            return BatchOperationResponse(
                total_items=len(batch_request.content_ids),
                successful_items=0,
                failed_items=len(batch_request.content_ids),
                results={},
                message=f"Batch scheduling failed: {str(e)}"
            )
    
    # ==================== Content Publishing ====================
    
    async def publish_content_immediately(self, user_id: str, 
                                        publish_request: PublishRequest) -> PublishResponse:
        """
        Publish content immediately
        
        Args:
            user_id: User ID
            publish_request: Publishing request
            
        Returns:
            Publishing response
        """
        try:
            logger.info(f"Publishing content {publish_request.content_id} immediately for user {user_id}")
            
            # Validate content
            content_draft = self.data_flow_manager.get_content_draft_by_id(publish_request.content_id)
            if not content_draft or content_draft.founder_id != user_id:
                return PublishResponse(
                    success=False,
                    message="Content not found or access denied"
                )
            
            # Check publishing rules (unless skipped)
            if not publish_request.skip_rules_check:
                rule_check = await self.check_publishing_rules(
                    user_id, publish_request.content_id, datetime.utcnow()
                )
                
                if not rule_check.can_publish and not publish_request.force_publish:
                    return PublishResponse(
                        success=False,
                        message="Publishing violates rules. Use force_publish to override."
                    )
            
            # Perform the actual publishing
            publish_result = await self._publish_to_twitter(user_id, content_draft, publish_request)
            
            return publish_result
            
        except Exception as e:
            logger.error(f"Failed to publish content immediately: {e}")
            return PublishResponse(
                success=False,
                message=f"Publishing failed: {str(e)}",
                error_code="PUBLISH_ERROR"
            )
    
    async def batch_publish_content(self, user_id: str,
                                  batch_request: BatchPublishRequest) -> BatchOperationResponse:
        """Publish multiple content items"""
        try:
            logger.info(f"Batch publishing {len(batch_request.content_ids)} items for user {user_id}")
            
            results = {}
            successful_items = 0
            
            for i, content_id in enumerate(batch_request.content_ids):
                try:
                    # Add stagger delay for batch operations
                    if i > 0:
                        await asyncio.sleep(batch_request.stagger_minutes * 60)
                    
                    # Create individual publish request
                    publish_request = PublishRequest(
                        content_id=content_id,
                        force_publish=batch_request.force_publish
                    )
                    
                    # Publish individual item
                    if batch_request.schedule_time:
                        # Schedule for later
                        scheduled_time = batch_request.schedule_time + timedelta(
                            minutes=i * batch_request.stagger_minutes
                        )
                        schedule_request = ScheduleRequest(
                            content_id=content_id,
                            scheduled_time=scheduled_time
                        )
                        result = await self.schedule_content(user_id, schedule_request)
                    else:
                        # Publish immediately
                        result = await self.publish_content_immediately(user_id, publish_request)
                    
                    results[content_id] = result
                    
                    if result.success:
                        successful_items += 1
                        
                except Exception as e:
                    logger.error(f"Failed to publish content {content_id}: {e}")
                    results[content_id] = PublishResponse(
                        success=False,
                        message=f"Publishing failed: {str(e)}",
                        error_code="BATCH_PUBLISH_ERROR"
                    )
            
            return BatchOperationResponse(
                total_items=len(batch_request.content_ids),
                successful_items=successful_items,
                failed_items=len(batch_request.content_ids) - successful_items,
                results=results,
                message=f"Batch publishing completed: {successful_items}/{len(batch_request.content_ids)} successful"
            )
            
        except Exception as e:
            logger.error(f"Batch publishing failed: {e}")
            return BatchOperationResponse(
                total_items=len(batch_request.content_ids),
                successful_items=0,
                failed_items=len(batch_request.content_ids),
                results={},
                message=f"Batch publishing failed: {str(e)}"
            )
    
    async def update_publishing_status(self, user_id: str, content_id: str,
                                     status_request: StatusUpdateRequest) -> bool:
        """
        Update publishing status
        
        Args:
            user_id: User ID
            content_id: Content ID
            status_request: Status update request
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get scheduled content
            scheduled_content = self.data_flow_manager.get_scheduled_content_by_draft_id(content_id)
            
            if not scheduled_content or scheduled_content.founder_id != user_id:
                logger.warning(f"Scheduled content not found for {content_id}")
                return False
            
            # Prepare update data
            update_data = {
                'status': status_request.status.value,
                'updated_at': datetime.utcnow()
            }
            
            # Handle successful posting
            if status_request.status == PublishStatus.POSTED:
                update_data['posted_at'] = datetime.utcnow()
                if status_request.posted_tweet_id:
                    update_data['posted_tweet_id'] = status_request.posted_tweet_id
                
                # Update content draft status
                self.data_flow_manager.update_content_draft(
                    content_id,
                    {
                        'status': 'posted',
                        'posted_at': datetime.utcnow(),
                        'posted_tweet_id': status_request.posted_tweet_id
                    }
                )
            
            # Handle failed publishing
            elif status_request.status == PublishStatus.FAILED:
                error_info = PublishingError(
                    error_code=status_request.error_code or "UNKNOWN_ERROR",
                    error_message=status_request.error_message or "Publishing failed",
                    retry_count=scheduled_content.retry_count + 1,
                    last_retry_at=datetime.utcnow(),
                    technical_details=status_request.technical_details
                )
                
                update_data['error_info'] = error_info.dict()
                update_data['retry_count'] = scheduled_content.retry_count + 1
                
                # Schedule retry if appropriate
                if (scheduled_content.retry_count < scheduled_content.max_retries and 
                    status_request.retry_scheduled):
                    update_data['status'] = PublishStatus.RETRY_PENDING.value
                    
                    # Calculate retry time
                    retry_delay = self._calculate_retry_delay(scheduled_content.retry_count)
                    retry_time = datetime.utcnow() + timedelta(minutes=retry_delay)
                    update_data['scheduled_time'] = retry_time
            
            # Update scheduled content
            success = self.data_flow_manager.update_scheduled_content(
                str(scheduled_content.id), update_data
            )
            
            if success:
                # Record analytics
                await self._record_publishing_analytics(
                    user_id, status_request.status.value, content_id
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update publishing status: {e}")
            return False
    
    # ==================== Publishing History and Analytics ====================
    
    async def get_publishing_history(self, user_id: str, limit: int = 20, 
                                   offset: int = 0) -> List[PublishingHistoryItem]:
        """Get publishing history for a user"""
        try:
            # Get scheduled content with associated draft information
            history_data = self.data_flow_manager.get_publishing_history(user_id, limit, offset)
            
            history_items = []
            for item in history_data:
                try:
                    # Get content preview
                    content_draft = self.data_flow_manager.get_content_draft_by_id(
                        item.content_draft_id
                    )
                    content_preview = ""
                    if content_draft:
                        content_text = content_draft.final_text
                        content_preview = content_text[:100] + "..." if len(content_text) > 100 else content_text
                    
                    history_item = PublishingHistoryItem(
                        content_id=item.content_draft_id,
                        scheduled_content_id=str(item.id),
                        content_preview=content_preview,
                        scheduled_time=item.scheduled_time,
                        posted_at=item.posted_at,
                        status=PublishStatus(item.status),
                        posted_tweet_id=item.posted_tweet_id,
                        platform=getattr(item, 'platform', 'twitter'),
                        error_message=item.error_info.get('error_message') if item.error_info else None,
                        retry_count=getattr(item, 'retry_count', 0),
                        tags=getattr(item, 'tags', []) or []
                    )
                    history_items.append(history_item)
                    
                except Exception as e:
                    logger.warning(f"Failed to convert history item: {e}")
                    continue
            
            return history_items
            
        except Exception as e:
            logger.error(f"Failed to get publishing history: {e}")
            return []
    
    async def get_publishing_analytics(self, user_id: str, days: int = 30) -> PublishingAnalytics:
        """Get publishing analytics for a user"""
        try:
            # Get analytics data from database
            analytics_data = self.data_flow_manager.get_publishing_analytics(user_id, days)
            
            total_scheduled = analytics_data.get('total_scheduled', 0)
            total_published = analytics_data.get('total_published', 0)
            total_failed = analytics_data.get('total_failed', 0)
            
            success_rate = (total_published / max(total_scheduled, 1)) * 100
            
            # Calculate average delay
            publish_delays = analytics_data.get('publish_delays', [])
            avg_delay = sum(publish_delays) / max(len(publish_delays), 1)
            
            # Get error breakdown
            error_counts = analytics_data.get('error_breakdown', {})
            most_common_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
            most_common_errors = [error[0] for error in most_common_errors[:5]]
            
            # Get time distribution
            time_distribution = analytics_data.get('time_distribution', {})
            
            # Platform breakdown
            platform_breakdown = analytics_data.get('platform_breakdown', {'twitter': total_published})
            
            return PublishingAnalytics(
                total_scheduled=total_scheduled,
                total_published=total_published,
                total_failed=total_failed,
                success_rate=round(success_rate, 2),
                avg_publish_delay_minutes=round(avg_delay, 2),
                most_common_errors=most_common_errors,
                publishing_times_distribution=time_distribution,
                platform_breakdown=platform_breakdown
            )
            
        except Exception as e:
            logger.error(f"Failed to get publishing analytics: {e}")
            return PublishingAnalytics(
                total_scheduled=0,
                total_published=0,
                total_failed=0,
                success_rate=0.0
            )
    
    # ==================== Rules Engine Integration ====================
    
    async def check_publishing_rules(self, user_id: str, content_id: Optional[str] = None,
                                   proposed_time: Optional[datetime] = None,
                                   content_type: Optional[str] = None) -> RuleCheckResult:
        """
        Check publishing rules for content using internal rules engine
        
        Args:
            user_id: User ID
            content_id: Optional content ID
            proposed_time: Proposed publishing time
            content_type: Optional content type
            
        Returns:
            Rule check result
        """
        try:
            logger.info(f"Checking publishing rules for user {user_id}")
            
            # Use internal rules engine for validation
            return await self.rules_engine.validate_publishing_rules(
                user_id=user_id,
                content_id=content_id,
                proposed_time=proposed_time
            )
            
        except Exception as e:
            logger.error(f"Failed to check publishing rules: {e}")
            return RuleCheckResult(
                can_publish=False,
                violations=[f"Rule check failed: {str(e)}"],
                recommendations=["Please try again later"]
            )
    
    # ==================== Queue Management ====================
    
    async def get_queue_info(self, user_id: str) -> SchedulingQueueInfo:
        """Get information about the publishing queue"""
        try:
            # Get queue statistics
            queue_stats = self.data_flow_manager.get_queue_statistics(user_id)
            
            total_pending = queue_stats.get('pending_count', 0)
            total_scheduled = queue_stats.get('scheduled_count', 0)
            upcoming_24h = queue_stats.get('upcoming_24h', 0)
            overdue_count = queue_stats.get('overdue_count', 0)
            retry_queue_size = queue_stats.get('retry_pending_count', 0)
            
            # Get next publish time
            next_scheduled = self.data_flow_manager.get_next_scheduled_time(user_id)
            
            # Get status breakdown
            status_breakdown = queue_stats.get('status_breakdown', {})
            
            return SchedulingQueueInfo(
                total_pending=total_pending,
                total_scheduled=total_scheduled,
                next_publish_time=next_scheduled,
                queue_by_status=status_breakdown,
                upcoming_24h=upcoming_24h,
                overdue_count=overdue_count,
                retry_queue_size=retry_queue_size
            )
            
        except Exception as e:
            logger.error(f"Failed to get queue info: {e}")
            return SchedulingQueueInfo(
                total_pending=0,
                total_scheduled=0
            )
    
    async def process_publishing_queue(self) -> Dict[str, Any]:
        """
        Process the publishing queue (background task)
        
        Returns:
            Processing statistics
        """
        if self._queue_processing:
            return {'status': 'already_processing'}
        
        async with self._queue_lock:
            self._queue_processing = True
            
            try:
                logger.info("Starting queue processing")
                
                processed_count = 0
                success_count = 0
                error_count = 0
                
                # Get items ready for publishing
                ready_items = self.data_flow_manager.get_ready_for_publishing(
                    limit=self.config.max_concurrent_publishes
                )
                
                # Process items concurrently
                tasks = []
                for item in ready_items:
                    task = self._process_queue_item(item)
                    tasks.append(task)
                
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in results:
                        processed_count += 1
                        if isinstance(result, Exception):
                            error_count += 1
                            logger.error(f"Queue processing error: {result}")
                        elif result.get('success', False):
                            success_count += 1
                        else:
                            error_count += 1
                
                logger.info(f"Queue processing completed: {processed_count} processed, "
                           f"{success_count} successful, {error_count} errors")
                
                return {
                    'status': 'completed',
                    'processed_count': processed_count,
                    'success_count': success_count,
                    'error_count': error_count
                }
                
            finally:
                self._queue_processing = False
    
    # ==================== Helper Methods ====================
    
    async def _publish_to_twitter(self, user_id: str, content_draft, 
                                publish_request: PublishRequest) -> PublishResponse:
        """Perform actual Twitter publishing"""
        try:
            # Get user's Twitter access token
            access_token = self.user_profile_service.get_twitter_access_token(user_id)
            if not access_token:
                return PublishResponse(
                    success=False,
                    message="Twitter account not connected",
                    error_code="NO_ACCESS_TOKEN"
                )
            
            # Prepare tweet content
            tweet_text = publish_request.custom_message or content_draft.final_text
            
            # Validate tweet length
            if len(tweet_text) > 280:
                return PublishResponse(
                    success=False,
                    message="Tweet text exceeds 280 character limit",
                    error_code="TWEET_TOO_LONG"
                )
            
            # Create tweet via Twitter API
            try:
                tweet_result = self.twitter_client.create_tweet(
                    user_token=access_token,
                    text=tweet_text
                )
                
                if tweet_result and 'data' in tweet_result:
                    tweet_id = tweet_result['data']['id']
                    
                    # Update content draft status
                    self.data_flow_manager.update_content_draft(
                        publish_request.content_id,
                        {
                            'status': 'posted',
                            'posted_at': datetime.utcnow(),
                            'posted_tweet_id': tweet_id
                        }
                    )
                    
                    # Record analytics
                    await self._record_publishing_analytics(user_id, 'posted', publish_request.content_id)
                    
                    return PublishResponse(
                        success=True,
                        posted_tweet_id=tweet_id,
                        posted_at=datetime.utcnow(),
                        message="Content published successfully"
                    )
                else:
                    return PublishResponse(
                        success=False,
                        message="Unexpected response from Twitter API",
                        error_code="TWITTER_API_ERROR"
                    )
                    
            except TwitterAPIError as e:
                logger.error(f"Twitter API error: {e}")
                return PublishResponse(
                    success=False,
                    message=f"Twitter API error: {str(e)}",
                    error_code="TWITTER_API_ERROR"
                )
                
        except Exception as e:
            logger.error(f"Failed to publish to Twitter: {e}")
            return PublishResponse(
                success=False,
                message=f"Publishing failed: {str(e)}",
                error_code="PUBLISH_ERROR"
            )
    
    async def _process_queue_item(self, queue_item: ContentQueueItem) -> Dict[str, Any]:
        """Process a single queue item"""
        try:
            # Get content draft
            content_draft = self.data_flow_manager.get_content_draft_by_id(queue_item.content_draft_id)
            if not content_draft:
                return {'success': False, 'error': 'Content draft not found'}
            
            # Create publish request
            publish_request = PublishRequest(
                content_id=queue_item.content_draft_id,
                force_publish=True  # Queue items already passed validation
            )
            
            # Perform publishing
            result = await self._publish_to_twitter(queue_item.founder_id, content_draft, publish_request)
            
            # Update scheduled content status
            if result.success:
                await self.update_publishing_status(
                    queue_item.founder_id,
                    queue_item.content_draft_id,
                    StatusUpdateRequest(
                        status=PublishStatus.POSTED,
                        posted_tweet_id=result.posted_tweet_id
                    )
                )
            else:
                await self.update_publishing_status(
                    queue_item.founder_id,
                    queue_item.content_draft_id,
                    StatusUpdateRequest(
                        status=PublishStatus.FAILED,
                        error_message=result.message,
                        error_code=result.error_code,
                        retry_scheduled=queue_item.should_retry
                    )
                )
            
            return {'success': result.success, 'tweet_id': result.posted_tweet_id}
            
        except Exception as e:
            logger.error(f"Failed to process queue item: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _get_user_scheduling_preferences(self, user_id: str) -> SchedulingPreferences:
        """Get user's scheduling preferences"""
        try:
            # Try to get from database
            prefs_data = self.data_flow_manager.get_user_scheduling_preferences(user_id)
            
            if prefs_data:
                return SchedulingPreferences(**prefs_data)
            else:
                # Return default preferences
                return SchedulingPreferences(founder_id=user_id)
                
        except Exception as e:
            logger.warning(f"Failed to get scheduling preferences: {e}")
            return SchedulingPreferences(founder_id=user_id)
    
    async def _calculate_optimal_schedule_time(self, user_id: str, content_id: str) -> datetime:
        """Calculate optimal scheduling time based on user preferences"""
        try:
            preferences = await self._get_user_scheduling_preferences(user_id)
            
            # Start with current time + minimum interval
            base_time = datetime.utcnow() + timedelta(minutes=preferences.min_interval_minutes)
            
            # Adjust for preferred posting times
            if preferences.preferred_posting_times:
                # Find next preferred time
                current_time = base_time.time()
                preferred_times = [
                    datetime.strptime(t, "%H:%M").time() 
                    for t in preferences.preferred_posting_times
                ]
                
                # Find next available preferred time
                for pref_time in sorted(preferred_times):
                    if pref_time > current_time:
                        return base_time.replace(
                            hour=pref_time.hour,
                            minute=pref_time.minute,
                            second=0,
                            microsecond=0
                        )
                
                # If no time today, use first preferred time tomorrow
                tomorrow = base_time + timedelta(days=1)
                first_pref_time = min(preferred_times)
                return tomorrow.replace(
                    hour=first_pref_time.hour,
                    minute=first_pref_time.minute,
                    second=0,
                    microsecond=0
                )
            
            return base_time
            
        except Exception as e:
            logger.warning(f"Failed to calculate optimal schedule time: {e}")
            return datetime.utcnow() + timedelta(hours=1)
    
    # Rule management methods - delegate to internal rules engine
    
    async def create_custom_rule(self, user_id: str, rule: SchedulingRule) -> bool:
        """Create a custom publishing rule for a user"""
        return await self.rules_engine.create_custom_rule(user_id, rule)
    
    async def update_rule(self, user_id: str, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing publishing rule"""
        return await self.rules_engine.update_rule(user_id, rule_id, updates)
    
    async def delete_rule(self, user_id: str, rule_id: str) -> bool:
        """Delete a publishing rule"""
        return await self.rules_engine.delete_rule(user_id, rule_id)
    
    async def get_rule_violations_summary(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Get summary of rule violations for analytics"""
        return await self.rules_engine.get_rule_violations_summary(user_id, days)
    
    def _calculate_retry_delay(self, retry_count: int) -> int:
        """Calculate retry delay in minutes"""
        if retry_count < len(self.config.retry_delays_minutes):
            return self.config.retry_delays_minutes[retry_count]
        else:
            # Exponential backoff for additional retries
            return min(self.config.retry_delays_minutes[-1] * (2 ** (retry_count - len(self.config.retry_delays_minutes))), 1440)  # Max 24 hours
    
    async def _record_scheduling_analytics(self, user_id: str, event_type: str) -> None:
        """Record scheduling analytics"""
        try:
            if self.analytics_collector:
                analytics_data = {
                    'event_type': event_type,
                    'user_id': user_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'module': 'scheduling_posting'
                }
                
                await self.analytics_collector.record_event(analytics_data)
        except Exception as e:
            logger.warning(f"Failed to record scheduling analytics: {e}")
    
    async def _record_publishing_analytics(self, user_id: str, event_type: str, content_id: str) -> None:
        """Record publishing analytics"""
        try:
            if self.analytics_collector:
                analytics_data = {
                    'event_type': event_type,
                    'user_id': user_id,
                    'content_id': content_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'module': 'scheduling_posting'
                }
                
                await self.analytics_collector.record_event(analytics_data)
        except Exception as e:
            logger.warning(f"Failed to record publishing analytics: {e}")