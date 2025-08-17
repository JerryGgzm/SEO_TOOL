"""Business logic for review optimization"""
"""Review Optimization Module - Service Layer

This service handles the business logic for content review and optimization,
integrating with the content generation module and data flow manager.
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
import logging
import json

from database import DataFlowManager
from modules.content_generation.service import ContentGenerationService
from modules.content_generation.models import ContentGenerationRequest, ContentType


from .models import (
    ContentDraftReview, ReviewDecision, DraftStatus, ContentPriority,
    ReviewDecisionRequest, BatchReviewRequest, ContentRegenerationRequest,
    StatusUpdateRequest, ReviewHistoryItem, ReviewSummary, ReviewAnalytics,
    RegenerationResult, ReviewQueue, ReviewPreferences, ContentEdit,
    ReviewFeedback, ContentComparisonResult
)
from .database_adapter import ReviewOptimizationDatabaseAdapter

logger = logging.getLogger(__name__)

class ReviewOptimizationService:
    """
    Service for handling content review and optimization workflows
    """
    
    def __init__(self, data_flow_manager: DataFlowManager,
                 content_generation_service: ContentGenerationService = None,
                 analytics_collector = None):
        
        self.data_flow_manager = data_flow_manager
        self.content_generation_service = content_generation_service

        
        # Database adapter for converting between service and database models
        self.db_adapter = ReviewOptimizationDatabaseAdapter()
        
        # Review process configuration
        self.config = {
            'auto_approve_threshold': 0.85,
            'max_pending_days': 7,
            'batch_size_limit': 50,
            'regeneration_attempts_limit': 3
        }
    
    async def get_pending_drafts(self, founder_id: str, limit: int = 10, 
                               offset: int = 0) -> List[ContentDraftReview]:
        """
        Get pending content drafts for review
        
        Args:
            founder_id: Founder's ID
            limit: Maximum number of drafts to return
            offset: Offset for pagination
            
        Returns:
            List of pending content drafts
        """
        try:
            logger.info(f"Getting pending drafts for founder {founder_id}")
            
            # Query database for pending drafts
            db_drafts = self.data_flow_manager.get_pending_content_drafts(
                founder_id, limit, offset
            )
            
            if not db_drafts:
                return []
            
            # Convert database models to service models
            pending_drafts = []
            for db_draft in db_drafts:
                try:
                    draft_review = self.db_adapter.from_database_format(db_draft)
                    pending_drafts.append(draft_review)
                except Exception as e:
                    logger.error(f"Failed to convert draft {db_draft.id}: {e}")
                    continue
            
            # Sort by priority and creation time
            pending_drafts.sort(
                key=lambda x: (
                    0 if x.priority == ContentPriority.HIGH else
                    1 if x.priority == ContentPriority.MEDIUM else 2,
                    x.created_at
                )
            )
            
            return pending_drafts
            
        except Exception as e:
            logger.error(f"Failed to get pending drafts: {e}")
            return []
    
    async def get_draft_details(self, draft_id: str, founder_id: str) -> Optional[ContentDraftReview]:
        """
        Get detailed information about a specific draft
        
        Args:
            draft_id: Draft ID
            founder_id: Founder ID for access control
            
        Returns:
            Draft details or None if not found/no access
        """
        try:
            # Get draft from database
            db_draft = self.data_flow_manager.get_content_draft_by_id(draft_id)
            
            if not db_draft or db_draft.founder_id != founder_id:
                logger.warning(f"Draft {draft_id} not found or access denied for founder {founder_id}")
                return None
            
            # Convert to service model
            draft_review = self.db_adapter.from_database_format(db_draft)
            
            # Enrich with additional information
            await self._enrich_draft_details(draft_review)
            
            return draft_review
            
        except Exception as e:
            logger.error(f"Failed to get draft details for {draft_id}: {e}")
            return None
    
    async def submit_review_decision(self, draft_id: str, founder_id: str,
                                   decision_request: ReviewDecisionRequest) -> bool:
        """
        Submit a review decision for a content draft
        
        Args:
            draft_id: Draft ID
            founder_id: Founder ID
            decision_request: Review decision details
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Processing review decision for draft {draft_id}")
            
            # Get current draft
            db_draft = self.data_flow_manager.get_content_draft_by_id(draft_id)
            if not db_draft or db_draft.founder_id != founder_id:
                logger.error(f"Draft {draft_id} not found or access denied")
                return False
            
            # Process decision
            success = await self._process_review_decision(
                db_draft, decision_request, founder_id
            )
            
            if success:
                # Record analytics
                await self._record_review_analytics(
                    founder_id, decision_request.decision, draft_id
                )
                
                # Trigger downstream processes if approved
                if decision_request.decision in [ReviewDecision.APPROVE, ReviewDecision.EDIT_AND_APPROVE]:
                    await self._trigger_post_approval_processes(draft_id, decision_request)
                
                # For "approve for later" decisions, just record but don't trigger scheduling
                elif decision_request.decision in [ReviewDecision.APPROVE_FOR_LATER, ReviewDecision.EDIT_AND_APPROVE_FOR_LATER]:
                    logger.info(f"Content {draft_id} approved for later scheduling - no immediate publishing actions triggered")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to submit review decision: {e}")
            return False
    
    async def submit_batch_review_decisions(self, founder_id: str,
                                          batch_request: BatchReviewRequest) -> Dict[str, bool]:
        """
        Submit batch review decisions
        
        Args:
            founder_id: Founder ID
            batch_request: Batch review request
            
        Returns:
            Dictionary mapping draft_id to success status
        """
        try:
            logger.info(f"Processing batch review for {len(batch_request.decisions)} drafts")
            
            results = {}
            
            # Process each decision
            for decision in batch_request.decisions:
                try:
                    # Convert batch decision to individual decision request
                    individual_request = ReviewDecisionRequest(
                        decision=decision.decision,
                        edited_content=decision.edited_content,
                        feedback=decision.feedback,
                        tags=decision.tags,
                        priority=decision.priority
                    )
                    
                    # Submit individual decision
                    success = await self.submit_review_decision(
                        decision.draft_id, founder_id, individual_request
                    )
                    results[decision.draft_id] = success
                    
                except Exception as e:
                    logger.error(f"Failed to process batch decision for {decision.draft_id}: {e}")
                    results[decision.draft_id] = False
            
            # Record batch analytics
            await self._record_batch_review_analytics(founder_id, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to submit batch review decisions: {e}")
            return {}
    
    async def get_review_history(self, founder_id: str, status: Optional[str] = None,
                               limit: int = 20, offset: int = 0) -> List[ReviewHistoryItem]:
        """
        Get review history for a founder
        
        Args:
            founder_id: Founder ID
            status: Optional status filter
            limit: Maximum number of items
            offset: Offset for pagination
            
        Returns:
            List of review history items
        """
        try:
            # Get review history from database
            db_history = self.data_flow_manager.get_review_history(
                founder_id, status, limit, offset
            )
            
            history_items = []
            for db_item in db_history:
                try:
                    # Convert to history item
                    history_item = ReviewHistoryItem(
                        draft_id=str(db_item.id),
                        content_preview=db_item.current_content[:100] + "..." if len(db_item.current_content) > 100 else db_item.current_content,
                        status=DraftStatus(db_item.status),
                        decision=ReviewDecision(db_item.review_decision) if db_item.review_decision else None,
                        reviewed_at=db_item.reviewed_at or db_item.updated_at,
                        content_type=db_item.content_type,
                        tags=db_item.tags or [],
                        quality_score=db_item.quality_score
                    )
                    history_items.append(history_item)
                except Exception as e:
                    logger.error(f"Failed to convert history item: {e}")
                    continue
            
            return history_items
            
        except Exception as e:
            logger.error(f"Failed to get review history: {e}")
            return []
    
    async def regenerate_content(self, draft_id: str, founder_id: str,
                               regeneration_request: ContentRegenerationRequest) -> Optional[RegenerationResult]:
        """
        Regenerate content based on feedback
        
        Args:
            draft_id: Original draft ID
            founder_id: Founder ID
            regeneration_request: Regeneration parameters
            
        Returns:
            Regeneration result or None if failed
        """
        try:
            logger.info(f"Regenerating content for draft {draft_id}")
            
            # Get original draft
            db_draft = self.data_flow_manager.get_content_draft_by_id(draft_id)
            if not db_draft or db_draft.founder_id != founder_id:
                return None
            
            # Check regeneration attempts limit
            regeneration_count = db_draft.generation_metadata.get('regeneration_count', 0)
            if regeneration_count >= self.config['regeneration_attempts_limit']:
                logger.warning(f"Regeneration limit reached for draft {draft_id}")
                return None
            
            # Prepare regeneration context
            regeneration_context = await self._prepare_regeneration_context(
                db_draft, regeneration_request
            )
            
            # Generate new content
            if self.content_generation_service:
                new_draft_ids = await self._regenerate_with_content_service(
                    db_draft, regeneration_context
                )
                
                if new_draft_ids:
                    new_draft_id = new_draft_ids[0]
                    new_db_draft = self.data_flow_manager.get_content_draft_by_id(new_draft_id)
                    
                    if new_db_draft:
                        # Create regeneration result
                        result = RegenerationResult(
                            draft_id=draft_id,
                            new_content=new_db_draft.generated_text,
                            improvements_made=self._identify_improvements(
                                db_draft.generated_text,
                                new_db_draft.generated_text,
                                regeneration_request
                            ),
                            generation_metadata=new_db_draft.ai_generation_metadata or {},
                            quality_score=getattr(new_db_draft, 'quality_score', None)
                        )
                        
                        # Update original draft with regeneration info
                        await self._update_regeneration_metadata(draft_id, new_draft_id)
                        
                        return result
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to regenerate content: {e}")
            return None
    
    async def update_draft_status(self, draft_id: str, founder_id: str,
                                status_request: StatusUpdateRequest) -> bool:
        """
        Update draft status
        
        Args:
            draft_id: Draft ID
            founder_id: Founder ID
            status_request: Status update request
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current draft
            db_draft = self.data_flow_manager.get_content_draft_by_id(draft_id)
            if not db_draft or db_draft.founder_id != founder_id:
                return False
            
            # Validate status transition
            if not self._is_valid_status_transition(db_draft.status, status_request.status):
                logger.warning(f"Invalid status transition from {db_draft.status} to {status_request.status}")
                return False
            
            # Update status
            update_data = {
                'status': status_request.status.value,
                'updated_at': datetime.utcnow()
            }
            
            if status_request.updated_content:
                update_data['current_content'] = status_request.updated_content
            
            if status_request.reviewer_notes:
                update_data['reviewer_notes'] = status_request.reviewer_notes
            
            if status_request.schedule_time:
                update_data['scheduled_time'] = status_request.schedule_time
            
            success = self.data_flow_manager.update_content_draft(draft_id, update_data)
            
            if success:
                # Record status change analytics
                await self._record_status_change_analytics(
                    founder_id, draft_id, status_request.status
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update draft status: {e}")
            return False
    
    async def get_review_summary(self, founder_id: str, days: int = 30) -> ReviewSummary:
        """
        Get review summary for a founder
        
        Args:
            founder_id: Founder ID
            days: Number of days to analyze
            
        Returns:
            Review summary
        """
        try:
            # Get review data from database
            review_data = self.data_flow_manager.get_review_summary_data(founder_id, days)
            
            # Calculate summary metrics
            total_pending = review_data.get('pending_count', 0)
            total_approved = review_data.get('approved_count', 0)
            total_rejected = review_data.get('rejected_count', 0)
            total_edited = review_data.get('edited_count', 0)
            
            total_reviewed = total_approved + total_rejected + total_edited
            approval_rate = (total_approved + total_edited) / max(total_reviewed, 1) * 100
            
            avg_quality_score = review_data.get('avg_quality_score', 0.0)
            most_common_tags = review_data.get('common_tags', [])[:5]
            review_velocity = total_reviewed / max(days, 1)
            
            return ReviewSummary(
                total_pending=total_pending,
                total_approved=total_approved,
                total_rejected=total_rejected,
                total_edited=total_edited,
                avg_quality_score=round(avg_quality_score, 2),
                approval_rate=round(approval_rate, 1),
                most_common_tags=most_common_tags,
                review_velocity=round(review_velocity, 2)
            )
            
        except Exception as e:
            logger.error(f"Failed to get review summary: {e}")
            return ReviewSummary(
                total_pending=0,
                total_approved=0,
                total_rejected=0,
                total_edited=0
            )
    
    async def get_review_queue(self, founder_id: str) -> ReviewQueue:
        """
        Get current review queue status
        
        Args:
            founder_id: Founder ID
            
        Returns:
            Review queue information
        """
        try:
            # Get pending drafts
            pending_drafts = await self.get_pending_drafts(founder_id, limit=100)
            
            # Count by priority
            high_priority = sum(1 for d in pending_drafts if d.priority == ContentPriority.HIGH)
            medium_priority = sum(1 for d in pending_drafts if d.priority == ContentPriority.MEDIUM)
            low_priority = sum(1 for d in pending_drafts if d.priority == ContentPriority.LOW)
            
            # Calculate oldest pending time
            oldest_pending_hours = None
            if pending_drafts:
                oldest_draft = min(pending_drafts, key=lambda x: x.created_at)
                oldest_pending_hours = (datetime.utcnow() - oldest_draft.created_at).total_seconds() / 3600
            
            # Estimate review time (2 minutes per draft on average)
            estimated_review_time = len(pending_drafts) * 2
            
            return ReviewQueue(
                founder_id=founder_id,
                pending_drafts=pending_drafts,
                high_priority_count=high_priority,
                medium_priority_count=medium_priority,
                low_priority_count=low_priority,
                oldest_pending_hours=oldest_pending_hours,
                estimated_review_time_minutes=estimated_review_time
            )
            
        except Exception as e:
            logger.error(f"Failed to get review queue: {e}")
            return ReviewQueue(founder_id=founder_id)
    
    async def get_approved_pending_schedule(self, founder_id: str, limit: int = 20, 
                                          offset: int = 0) -> List[ContentDraftReview]:
        """
        Get content that is approved but pending scheduling
        
        Args:
            founder_id: Founder's ID
            limit: Maximum number of drafts to return
            offset: Offset for pagination
            
        Returns:
            List of approved pending schedule drafts
        """
        try:
            logger.info(f"Getting approved pending schedule drafts for founder {founder_id}")
            
            # Query database for approved pending schedule drafts
            db_drafts = self.data_flow_manager.get_content_drafts_by_status(
                founder_id, ['approved_pending_schedule'], limit, offset
            )
            
            if not db_drafts:
                return []
            
            # Convert database models to service models
            pending_drafts = []
            for db_draft in db_drafts:
                try:
                    draft_review = self.db_adapter.from_database_format(db_draft)
                    pending_drafts.append(draft_review)
                except Exception as e:
                    logger.error(f"Failed to convert draft {db_draft.get('id')}: {e}")
                    continue
            
            # Sort by priority and creation time
            pending_drafts.sort(
                key=lambda x: (
                    0 if x.priority == ContentPriority.HIGH else
                    1 if x.priority == ContentPriority.MEDIUM else 2,
                    x.created_at
                )
            )
            
            return pending_drafts
            
        except Exception as e:
            logger.error(f"Failed to get approved pending schedule drafts: {e}")
            return []
    
    # Helper methods
    
    async def _enrich_draft_details(self, draft: ContentDraftReview) -> None:
        """Enrich draft with additional details"""
        try:
            # Add trend information if available
            if draft.trend_id:
                trend_info = self.data_flow_manager.get_trend_by_id(draft.trend_id)
                if trend_info:
                    draft.generation_metadata['trend_info'] = {
                        'topic_name': trend_info.topic_name,
                        'relevance_score': trend_info.relevance_score
                    }
            
            # Add quality analysis
            if draft.quality_score is None and self.content_generation_service:
                # Could calculate quality score here if needed
                pass
                
        except Exception as e:
            logger.warning(f"Failed to enrich draft details: {e}")
    
    async def _process_review_decision(self, db_draft, decision_request: ReviewDecisionRequest,
                                     reviewer_id: str) -> bool:
        """Process a review decision"""
        try:
            # Prepare update data
            update_data = {
                'review_decision': decision_request.decision.value,
                'reviewed_at': datetime.utcnow(),
                'reviewer_id': reviewer_id,
                'updated_at': datetime.utcnow()
            }
            
            # Handle different decision types
            if decision_request.decision == ReviewDecision.APPROVE:
                update_data['status'] = DraftStatus.APPROVED.value
                
            elif decision_request.decision == ReviewDecision.APPROVE_FOR_LATER:
                update_data['status'] = DraftStatus.APPROVED_PENDING_SCHEDULE.value
                
            elif decision_request.decision == ReviewDecision.EDIT_AND_APPROVE:
                update_data['status'] = DraftStatus.APPROVED.value
                update_data['current_content'] = decision_request.edited_content
                
                # Record edit in history
                edit_record = {
                    'original_content': db_draft.generated_text,
                    'edited_content': decision_request.edited_content,
                    'edit_reason': decision_request.feedback,
                    'edit_timestamp': datetime.utcnow(),
                    'editor_id': reviewer_id
                }
                
                # Add to edit history
                existing_history = db_draft.edit_history or []
                existing_history.append(edit_record)
                update_data['edit_history'] = existing_history
                
            elif decision_request.decision == ReviewDecision.EDIT_AND_APPROVE_FOR_LATER:
                update_data['status'] = DraftStatus.APPROVED_PENDING_SCHEDULE.value
                update_data['current_content'] = decision_request.edited_content
                
                # Record edit in history
                edit_record = {
                    'original_content': db_draft.generated_text,
                    'edited_content': decision_request.edited_content,
                    'edit_reason': decision_request.feedback,
                    'edit_timestamp': datetime.utcnow(),
                    'editor_id': reviewer_id
                }
                
                # Add to edit history
                existing_history = db_draft.edit_history or []
                existing_history.append(edit_record)
                update_data['edit_history'] = existing_history
                
            elif decision_request.decision == ReviewDecision.REJECT:
                update_data['status'] = DraftStatus.REJECTED.value
            
            # Add feedback if provided
            if decision_request.feedback:
                update_data['review_feedback'] = decision_request.feedback
            
            # Add tags if provided
            if decision_request.tags:
                update_data['tags'] = decision_request.tags
            
            # Set priority if provided
            if decision_request.priority:
                update_data['priority'] = decision_request.priority.value
            
            # Set schedule time if provided
            if decision_request.schedule_time:
                update_data['scheduled_time'] = decision_request.schedule_time
                update_data['status'] = DraftStatus.SCHEDULED.value
            
            # Add reviewer notes
            if decision_request.reviewer_notes:
                update_data['reviewer_notes'] = decision_request.reviewer_notes
            
            # Update in database
            success = self.data_flow_manager.update_content_draft(str(db_draft.id), update_data)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to process review decision: {e}")
            return False
    
    async def _trigger_post_approval_processes(self, draft_id: str, 
                                             decision_request: ReviewDecisionRequest) -> None:
        """Trigger processes that should run after content approval"""
        try:
            # If scheduled, add to scheduling queue
            if decision_request.schedule_time:
                await self._add_to_scheduling_queue(draft_id, decision_request.schedule_time)
            
            # Update content performance predictions
            await self._update_performance_predictions(draft_id)
            
            # Notify scheduling module of new approved content
            await self._notify_scheduling_module(draft_id)
            
        except Exception as e:
            logger.warning(f"Post-approval processes failed for {draft_id}: {e}")
    
    async def _prepare_regeneration_context(self, db_draft, 
                                          regeneration_request: ContentRegenerationRequest) -> Dict[str, Any]:
        """Prepare context for content regeneration"""
        try:
            context = {
                'original_content': db_draft.generated_text,
                'content_type': db_draft.content_type,
                'founder_id': db_draft.founder_id,
                'trend_id': db_draft.analyzed_trend_id,
                'feedback': regeneration_request.feedback,
                'style_preferences': regeneration_request.style_preferences,
                'target_improvements': regeneration_request.target_improvements,
                'keep_elements': regeneration_request.keep_elements,
                'avoid_elements': regeneration_request.avoid_elements,
                'original_metadata': db_draft.ai_generation_metadata or {}
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to prepare regeneration context: {e}")
            return {}
    
    async def _regenerate_with_content_service(self, db_draft, context: Dict[str, Any]) -> List[str]:
        """Regenerate content using content generation service"""
        try:
            if not self.content_generation_service:
                return []
            
            # Create regeneration request
            regeneration_request = ContentGenerationRequest(
                founder_id=db_draft.founder_id,
                content_type=ContentType(db_draft.content_type),
                trend_id=db_draft.analyzed_trend_id,
                custom_prompt=context.get('feedback'),
                quantity=1,
                quality_threshold=0.7
            )
            
            # Generate new content
            new_draft_ids = await self.content_generation_service.regenerate_content_with_seo_feedback(
                str(db_draft.id),
                db_draft.founder_id,
                context.get('feedback', ''),
                {
                    'style_preferences': context.get('style_preferences', {}),
                    'target_improvements': context.get('target_improvements', []),
                    'keep_elements': context.get('keep_elements', []),
                    'avoid_elements': context.get('avoid_elements', [])
                }
            )
            
            return new_draft_ids if new_draft_ids else []
            
        except Exception as e:
            logger.error(f"Failed to regenerate with content service: {e}")
            return []
    
    def _identify_improvements(self, original_content: str, new_content: str,
                             regeneration_request: ContentRegenerationRequest) -> List[str]:
        """Identify improvements made in regenerated content"""
        improvements = []
        
        try:
            # Length comparison
            if len(new_content) > len(original_content):
                improvements.append("Expanded content with additional context")
            elif len(new_content) < len(original_content):
                improvements.append("Made content more concise")
            
            # Hashtag analysis
            original_hashtags = len([word for word in original_content.split() if word.startswith('#')])
            new_hashtags = len([word for word in new_content.split() if word.startswith('#')])
            
            if new_hashtags > original_hashtags:
                improvements.append("Added more relevant hashtags")
            elif new_hashtags < original_hashtags:
                improvements.append("Optimized hashtag usage")
            
            # Question/engagement analysis
            if '?' in new_content and '?' not in original_content:
                improvements.append("Added engaging question")
            
            # Based on target improvements
            for improvement in regeneration_request.target_improvements:
                if improvement.lower() in new_content.lower():
                    improvements.append(f"Addressed: {improvement}")
            
            # Style improvements
            style_prefs = regeneration_request.style_preferences
            if style_prefs.get('tone') and style_prefs['tone'].lower() in new_content.lower():
                improvements.append(f"Adjusted tone to be more {style_prefs['tone']}")
            
            return improvements
            
        except Exception as e:
            logger.warning(f"Failed to identify improvements: {e}")
            return ["Content regenerated based on feedback"]
    
    async def _update_regeneration_metadata(self, original_draft_id: str, new_draft_id: str) -> None:
        """Update metadata for regeneration tracking"""
        try:
            # Update original draft
            original_metadata = {
                'regenerated': True,
                'regeneration_timestamp': datetime.utcnow().isoformat(),
                'new_draft_id': new_draft_id
            }
            
            self.data_flow_manager.update_content_draft_metadata(
                original_draft_id, {'regeneration_info': original_metadata}
            )
            
            # Update new draft
            new_metadata = {
                'is_regeneration': True,
                'original_draft_id': original_draft_id,
                'regeneration_timestamp': datetime.utcnow().isoformat()
            }
            
            self.data_flow_manager.update_content_draft_metadata(
                new_draft_id, {'regeneration_source': new_metadata}
            )
            
        except Exception as e:
            logger.warning(f"Failed to update regeneration metadata: {e}")
    
    def _is_valid_status_transition(self, current_status: str, new_status: DraftStatus) -> bool:
        """Validate status transitions"""
        valid_transitions = {
            DraftStatus.PENDING_REVIEW: [DraftStatus.APPROVED, DraftStatus.APPROVED_PENDING_SCHEDULE, DraftStatus.REJECTED, DraftStatus.EDITING, DraftStatus.SCHEDULED],
            DraftStatus.APPROVED: [DraftStatus.SCHEDULED, DraftStatus.POSTED, DraftStatus.EDITING],
            DraftStatus.APPROVED_PENDING_SCHEDULE: [DraftStatus.SCHEDULED, DraftStatus.POSTED, DraftStatus.EDITING, DraftStatus.APPROVED],
            DraftStatus.REJECTED: [DraftStatus.PENDING_REVIEW, DraftStatus.EDITING],
            DraftStatus.SCHEDULED: [DraftStatus.POSTED, DraftStatus.APPROVED, DraftStatus.EDITING],
            DraftStatus.POSTED: [],  # Posted is final
            DraftStatus.EDITING: [DraftStatus.PENDING_REVIEW, DraftStatus.APPROVED, DraftStatus.APPROVED_PENDING_SCHEDULE, DraftStatus.REJECTED]
        }
        
        try:
            current_enum = DraftStatus(current_status)
            return new_status in valid_transitions.get(current_enum, [])
        except ValueError:
            return False
    

    

    

    
    async def _add_to_scheduling_queue(self, draft_id: str, schedule_time: datetime) -> None:
        """Add approved content to scheduling queue"""
        try:
            # This would integrate with the SchedulingPostingModule
            scheduling_data = {
                'draft_id': draft_id,
                'scheduled_time': schedule_time,
                'status': 'scheduled',
                'created_at': datetime.utcnow()
            }
            
            # Store in scheduling queue table
            self.data_flow_manager.add_to_scheduling_queue(scheduling_data)
            
        except Exception as e:
            logger.warning(f"Failed to add to scheduling queue: {e}")
    
    async def _update_performance_predictions(self, draft_id: str) -> None:
        """Update performance predictions for approved content"""
        try:
            # Get draft content
            db_draft = self.data_flow_manager.get_content_draft_by_id(draft_id)
            if not db_draft:
                return
            
            #TODO: Calculate performance prediction
            # This could integrate with analytics module for ML predictions
            prediction_score = 0.7  # Placeholder
            
            # Update draft with prediction
            self.data_flow_manager.update_content_draft_metadata(
                draft_id, {'performance_prediction': prediction_score}
            )
            
        except Exception as e:
            logger.warning(f"Failed to update performance predictions: {e}")
    
    async def _notify_scheduling_module(self, draft_id: str) -> None:
        """Notify scheduling module of new approved content"""
        try:
            # Get draft details to include in notification
            db_draft = self.data_flow_manager.get_content_draft_by_id(draft_id)
            if not db_draft:
                logger.warning(f"Draft {draft_id} not found for scheduling notification")
                return
            
            # Create notification data for scheduling module
            notification_data = {
                'event_type': 'content_approved',
                'draft_id': draft_id,
                'founder_id': db_draft.founder_id,
                'content_type': db_draft.content_type,
                'content_preview': db_draft.current_content[:100] if db_draft.current_content else '',
                'status': db_draft.status,
                'priority': getattr(db_draft, 'priority', 5),
                'created_at': db_draft.created_at.isoformat() if db_draft.created_at else None,
                'updated_at': db_draft.updated_at.isoformat() if db_draft.updated_at else None,
                'scheduled_time': db_draft.scheduled_post_time.isoformat() if db_draft.scheduled_post_time else None,
                'timestamp': datetime.utcnow().isoformat(),
                'source_module': 'review_optimization'
            }
            
            # Method 1: Direct integration with SchedulingPostingService
            # This is the most direct approach for your architecture
            try:
                # Import scheduling service (avoid circular imports by importing here)
                from modules.scheduling_posting.service import SchedulingPostingService
                from modules.twitter_api import get_twitter_client
                from modules.user_profile import get_user_service
                
                # Initialize scheduling service if not already available
                if not hasattr(self, '_scheduling_service'):
                    twitter_client = get_twitter_client()
                    user_service = get_user_service()
                    self._scheduling_service = SchedulingPostingService(
                        data_flow_manager=self.data_flow_manager,
                        twitter_client=twitter_client,
                        user_profile_service=user_service,
                        analytics_collector=self.analytics_collector
                    )
                
                # Check if content should be auto-scheduled
                if db_draft.scheduled_post_time:
                    # Content already has a scheduled time - add to queue
                    await self._add_content_to_scheduling_queue(notification_data)
                    logger.info(f"Added approved content {draft_id} to scheduling queue")
                elif await self._should_auto_schedule(db_draft.founder_id):
                    # Auto-schedule based on user preferences
                    await self._auto_schedule_approved_content(db_draft.founder_id, draft_id)
                    logger.info(f"Auto-scheduled approved content {draft_id}")
                else:
                    # Just notify that content is available for manual scheduling
                    await self._notify_content_available_for_scheduling(notification_data)
                    logger.info(f"Notified scheduling module about available content {draft_id}")
                
            except ImportError as import_error:
                logger.warning(f"Could not import scheduling service: {import_error}")
                # Fallback to data storage approach
                await self._store_scheduling_notification(notification_data)
                
            # Method 2: Event-based notification (if you have an event system)
            # This would be useful for decoupled architecture
            if hasattr(self, 'event_publisher'):
                await self.event_publisher.publish('content_approved', notification_data)
                logger.info(f"Published content_approved event for draft {draft_id}")
            
            # Method 3: Database-based notification queue
            # Store notification in database for scheduling module to pick up
            await self._store_scheduling_notification(notification_data)
            
            logger.info(f"Successfully notified scheduling module about approved content {draft_id}")
            
        except Exception as e:
            logger.warning(f"Failed to notify scheduling module: {e}")
    
    async def _add_content_to_scheduling_queue(self, notification_data: Dict[str, Any]) -> None:
        """Add content to scheduling queue for processing"""
        try:
            queue_data = {
                'draft_id': notification_data['draft_id'],
                'founder_id': notification_data['founder_id'],
                'scheduled_time': notification_data['scheduled_time'],
                'status': 'scheduled',
                'priority': notification_data.get('priority', 5),
                'content_type': notification_data['content_type'],
                'created_at': datetime.utcnow().isoformat(),
                'source': 'review_approval'
            }
            
            # Store in scheduling queue (implement this method if it doesn't exist)
            if hasattr(self.data_flow_manager, 'add_to_scheduling_queue'):
                self.data_flow_manager.add_to_scheduling_queue(queue_data)
            else:
                # Alternative: store in a generic scheduling events table
                await self._store_scheduling_event('content_queued', queue_data)
                
        except Exception as e:
            logger.error(f"Failed to add content to scheduling queue: {e}")
    
    async def _should_auto_schedule(self, founder_id: str) -> bool:
        """Check if user has auto-scheduling enabled"""
        try:
            # Get user preferences
            user_settings = self.data_flow_manager.get_founder_settings(founder_id)
            if user_settings:
                scheduling_prefs = user_settings.get('scheduling_preferences', {})
                return scheduling_prefs.get('auto_schedule_enabled', False)
            return False
        except Exception as e:
            logger.warning(f"Failed to check auto-schedule preference: {e}")
            return False
    
    async def _auto_schedule_approved_content(self, founder_id: str, draft_id: str) -> None:
        """Auto-schedule approved content based on user preferences"""
        try:
            if hasattr(self, '_scheduling_service'):
                # Use scheduling service to calculate optimal time
                optimal_time = await self._scheduling_service._calculate_optimal_schedule_time(
                    founder_id, draft_id
                )
                
                # Create schedule request
                from modules.scheduling_posting.models import ScheduleRequest
                schedule_request = ScheduleRequest(
                    content_id=draft_id,
                    scheduled_time=optimal_time,
                    timezone="UTC",
                    priority=5
                )
                
                # Schedule the content
                result = await self._scheduling_service.schedule_content(founder_id, schedule_request)
                if result.success:
                    logger.info(f"Successfully auto-scheduled content {draft_id}")
                else:
                    logger.warning(f"Auto-scheduling failed for {draft_id}: {result.message}")
                    
        except Exception as e:
            logger.error(f"Failed to auto-schedule content {draft_id}: {e}")
    
    async def _notify_content_available_for_scheduling(self, notification_data: Dict[str, Any]) -> None:
        """Notify that content is available for manual scheduling"""
        try:
            # Store notification for scheduling dashboard/UI to pick up
            notification_record = {
                'type': 'content_available',
                'draft_id': notification_data['draft_id'],
                'founder_id': notification_data['founder_id'],
                'content_preview': notification_data['content_preview'],
                'status': 'pending_schedule',
                'created_at': datetime.utcnow().isoformat(),
                'read': False
            }
            
            await self._store_scheduling_event('content_available', notification_record)
            
        except Exception as e:
            logger.error(f"Failed to notify content available: {e}")
    
    async def _store_scheduling_notification(self, notification_data: Dict[str, Any]) -> None:
        """Store scheduling notification in database"""
        try:
            # Create scheduling notifications table if it doesn't exist
            self.data_flow_manager.db_session.execute("""
                CREATE TABLE IF NOT EXISTS scheduling_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    draft_id TEXT NOT NULL,
                    founder_id TEXT NOT NULL,
                    notification_data TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    FOREIGN KEY (founder_id) REFERENCES founders(id),
                    FOREIGN KEY (draft_id) REFERENCES generated_content_drafts(id)
                )
            """)
            
            # Insert notification record
            self.data_flow_manager.db_session.execute("""
                INSERT INTO scheduling_notifications (
                    event_type, draft_id, founder_id, notification_data
                ) VALUES (?, ?, ?, ?)
            """, (
                notification_data['event_type'],
                notification_data['draft_id'],
                notification_data['founder_id'],
                json.dumps(notification_data)
            ))
            
            self.data_flow_manager.db_session.commit()
            logger.info(f"Stored scheduling notification for draft {notification_data['draft_id']}")
            
        except Exception as e:
            logger.error(f"Failed to store scheduling notification: {e}")
            if hasattr(self.data_flow_manager, 'db_session'):
                self.data_flow_manager.db_session.rollback()
    
    async def _store_scheduling_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Store scheduling event for processing"""
        try:
            # Create scheduling events table if it doesn't exist
            self.data_flow_manager.db_session.execute("""
                CREATE TABLE IF NOT EXISTS scheduling_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    founder_id TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    FOREIGN KEY (founder_id) REFERENCES founders(id)
                )
            """)
            
            # Insert event record
            self.data_flow_manager.db_session.execute("""
                INSERT INTO scheduling_events (
                    event_type, founder_id, event_data
                ) VALUES (?, ?, ?)
            """, (
                event_type,
                event_data.get('founder_id'),
                json.dumps(event_data)
            ))
            
            self.data_flow_manager.db_session.commit()
            logger.info(f"Stored scheduling event: {event_type}")
            
        except Exception as e:
            logger.error(f"Failed to store scheduling event: {e}")
            if hasattr(self.data_flow_manager, 'db_session'):
                self.data_flow_manager.db_session.rollback()
    
    # Public analytics methods
    
    async def get_review_analytics(self, founder_id: str, days: int = 30) -> ReviewAnalytics:
        """Get detailed review analytics"""
        try:
            # Get review data from database
            analytics_data = self.data_flow_manager.get_detailed_review_analytics(founder_id, days)
            
            # Calculate metrics
            total_reviews = analytics_data.get('total_reviews', 0)
            decision_breakdown = analytics_data.get('decision_breakdown', {})
            content_type_breakdown = analytics_data.get('content_type_breakdown', {})
            avg_review_time = analytics_data.get('avg_review_time_minutes', 0.0)
            quality_trend = analytics_data.get('quality_trend', [])
            rejection_reasons = analytics_data.get('top_rejection_reasons', [])
            
            # Calculate productivity metrics
            productivity_metrics = {
                'reviews_per_day': total_reviews / max(days, 1),
                'approval_rate': (decision_breakdown.get('approve', 0) + decision_breakdown.get('edit_and_approve', 0)) / max(total_reviews, 1),
                'edit_rate': decision_breakdown.get('edit_and_approve', 0) / max(total_reviews, 1),
                'rejection_rate': decision_breakdown.get('reject', 0) / max(total_reviews, 1)
            }
            
            return ReviewAnalytics(
                period_days=days,
                total_reviews=total_reviews,
                decision_breakdown=decision_breakdown,
                content_type_breakdown=content_type_breakdown,
                average_review_time_minutes=avg_review_time,
                quality_trend=quality_trend,
                top_rejection_reasons=rejection_reasons,
                productivity_metrics=productivity_metrics
            )
            
        except Exception as e:
            logger.error(f"Failed to get review analytics: {e}")
            return ReviewAnalytics(period_days=days, total_reviews=0)
    
    async def compare_content_versions(self, draft_id: str, founder_id: str) -> Optional[ContentComparisonResult]:
        """Compare original vs edited content versions"""
        try:
            # Get draft with edit history
            db_draft = self.data_flow_manager.get_content_draft_by_id(draft_id)
            if not db_draft or db_draft.founder_id != founder_id:
                return None
            
            # Get latest edit
            edit_history = db_draft.edit_history or []
            if not edit_history:
                return None
            
            latest_edit = edit_history[-1]
            original_content = latest_edit['original_content']
            edited_content = latest_edit['edited_content']
            
            # Analyze changes
            changes_summary = self._analyze_content_changes(original_content, edited_content)
            improvement_score = self._calculate_improvement_score(original_content, edited_content)
            seo_impact = self._analyze_seo_impact(original_content, edited_content)
            readability_impact = self._analyze_readability_impact(original_content, edited_content)
            engagement_prediction = self._predict_engagement_impact(original_content, edited_content)
            
            return ContentComparisonResult(
                draft_id=draft_id,
                original_content=original_content,
                edited_content=edited_content,
                changes_summary=changes_summary,
                improvement_score=improvement_score,
                seo_impact=seo_impact,
                readability_impact=readability_impact,
                engagement_prediction=engagement_prediction
            )
            
        except Exception as e:
            logger.error(f"Failed to compare content versions: {e}")
            return None
    
    def _analyze_content_changes(self, original: str, edited: str) -> Dict[str, Any]:
        """Analyze changes between original and edited content"""
        changes = {
            'length_change': len(edited) - len(original),
            'word_count_change': len(edited.split()) - len(original.split()),
            'hashtag_changes': 0,
            'question_added': False,
            'emoji_changes': 0
        }
        
        # Hashtag analysis
        original_hashtags = set([word for word in original.split() if word.startswith('#')])
        edited_hashtags = set([word for word in edited.split() if word.startswith('#')])
        changes['hashtag_changes'] = len(edited_hashtags) - len(original_hashtags)
        
        # Question analysis
        changes['question_added'] = '?' in edited and '?' not in original
        
        # Emoji analysis (simplified)
        import re
        original_emojis = len(re.findall(r'[^\w\s]', original))
        edited_emojis = len(re.findall(r'[^\w\s]', edited))
        changes['emoji_changes'] = edited_emojis - original_emojis
        
        return changes
    
    def _calculate_improvement_score(self, original: str, edited: str) -> float:
        """Calculate improvement score between versions"""
        score = 0.5  # Base score
        
        # Length optimization
        original_len = len(original)
        edited_len = len(edited)
        
        if 50 <= edited_len <= 280 and (edited_len > original_len or original_len > 280):
            score += 0.1
        
        # Engagement elements
        if '?' in edited and '?' not in original:
            score += 0.15
        
        # Hashtag optimization
        original_hashtags = len([w for w in original.split() if w.startswith('#')])
        edited_hashtags = len([w for w in edited.split() if w.startswith('#')])
        
        if 1 <= edited_hashtags <= 5 and edited_hashtags > original_hashtags:
            score += 0.1
        
        # Call to action
        cta_words = ['share', 'comment', 'think', 'thoughts', 'opinion']
        if any(word in edited.lower() for word in cta_words) and not any(word in original.lower() for word in cta_words):
            score += 0.1
        
        # Readability
        avg_word_length_original = sum(len(word) for word in original.split()) / max(len(original.split()), 1)
        avg_word_length_edited = sum(len(word) for word in edited.split()) / max(len(edited.split()), 1)
        
        if avg_word_length_edited < avg_word_length_original:
            score += 0.05
        
        return min(1.0, score)
    
    def _analyze_seo_impact(self, original: str, edited: str) -> Dict[str, Any]:
        """Analyze SEO impact of changes"""
        # Calculate keyword density changes
        keyword_density_change = self._calculate_keyword_density_change(original, edited)
        
        # Calculate other SEO metrics
        original_hashtags = len([w for w in original.split() if w.startswith('#')])
        edited_hashtags = len([w for w in edited.split() if w.startswith('#')])
        
        return {
            'keyword_density_change': keyword_density_change,
            'hashtag_optimization': edited_hashtags > original_hashtags,
            'hashtag_count_change': edited_hashtags - original_hashtags,
            'length_optimization': 50 <= len(edited) <= 280,
            'engagement_elements_added': '?' in edited and '?' not in original,
            'keyword_analysis': self._get_keyword_analysis(original, edited)
        }
    
    def _calculate_keyword_density_change(self, original: str, edited: str) -> float:
        """Calculate the change in keyword density between original and edited content"""
        try:
            import re
            from collections import Counter
            
            # Extract keywords (exclude common stop words and hashtags)
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
            }
            
            def extract_keywords(text: str) -> Counter:
                # Convert to lowercase and remove punctuation except hashtags
                cleaned_text = re.sub(r'[^\w\s#]', ' ', text.lower())
                words = cleaned_text.split()
                
                # Filter out stop words, very short words, and hashtags
                keywords = [
                    word for word in words 
                    if len(word) > 2 
                    and word not in stop_words 
                    and not word.startswith('#')
                    and word.isalpha()  # Only alphabetic words
                ]
                
                return Counter(keywords)
            
            def calculate_density(keyword_counts: Counter, total_words: int) -> Dict[str, float]:
                if total_words == 0:
                    return {}
                return {keyword: (count / total_words) * 100 for keyword, count in keyword_counts.items()}
            
            # Extract keywords from both texts
            original_keywords = extract_keywords(original)
            edited_keywords = extract_keywords(edited)
            
            # Calculate total word counts (excluding stop words)
            original_total = sum(original_keywords.values())
            edited_total = sum(edited_keywords.values())
            
            if original_total == 0 and edited_total == 0:
                return 0.0
            
            # Calculate keyword densities
            original_densities = calculate_density(original_keywords, original_total)
            edited_densities = calculate_density(edited_keywords, edited_total)
            
            # Calculate overall density change
            # Focus on top keywords from both versions
            all_keywords = set(original_keywords.keys()) | set(edited_keywords.keys())
            top_keywords = sorted(all_keywords, 
                                key=lambda k: max(original_keywords.get(k, 0), edited_keywords.get(k, 0)), 
                                reverse=True)[:10]  # Top 10 keywords
            
            total_density_change = 0.0
            keyword_changes = 0
            
            for keyword in top_keywords:
                original_density = original_densities.get(keyword, 0.0)
                edited_density = edited_densities.get(keyword, 0.0)
                density_change = edited_density - original_density
                
                if abs(density_change) > 0.1:  # Only count significant changes
                    total_density_change += density_change
                    keyword_changes += 1
            
            # Return average density change for significant keywords
            if keyword_changes > 0:
                return round(total_density_change / keyword_changes, 2)
            else:
                return 0.0
                
        except Exception as e:
            logger.warning(f"Failed to calculate keyword density change: {e}")
            return 0.0
    
    def _get_keyword_analysis(self, original: str, edited: str) -> Dict[str, Any]:
        """Get detailed keyword analysis"""
        try:
            import re
            from collections import Counter
            
            def extract_keywords_with_counts(text: str) -> tuple:
                stop_words = {
                    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
                }
                
                cleaned_text = re.sub(r'[^\w\s#]', ' ', text.lower())
                all_words = cleaned_text.split()
                total_words = len(all_words)
                
                keywords = [
                    word for word in all_words 
                    if len(word) > 2 
                    and word not in stop_words 
                    and not word.startswith('#')
                    and word.isalpha()
                ]
                
                return Counter(keywords), total_words
            
            original_keywords, original_total = extract_keywords_with_counts(original)
            edited_keywords, edited_total = extract_keywords_with_counts(edited)
            
            # Find top keywords in each version
            original_top = dict(original_keywords.most_common(5))
            edited_top = dict(edited_keywords.most_common(5))
            
            # Find new keywords (in edited but not in original)
            new_keywords = set(edited_keywords.keys()) - set(original_keywords.keys())
            
            # Find removed keywords (in original but not in edited)
            removed_keywords = set(original_keywords.keys()) - set(edited_keywords.keys())
            
            # Calculate density for top keywords
            original_densities = {k: round((v / max(original_total, 1)) * 100, 2) for k, v in original_top.items()}
            edited_densities = {k: round((v / max(edited_total, 1)) * 100, 2) for k, v in edited_top.items()}
            
            return {
                'original_top_keywords': original_densities,
                'edited_top_keywords': edited_densities,
                'new_keywords': list(new_keywords)[:5],  # Top 5 new keywords
                'removed_keywords': list(removed_keywords)[:5],  # Top 5 removed keywords
                'total_unique_keywords_original': len(original_keywords),
                'total_unique_keywords_edited': len(edited_keywords),
                'keyword_diversity_change': len(edited_keywords) - len(original_keywords)
            }
            
        except Exception as e:
            logger.warning(f"Failed to get keyword analysis: {e}")
            return {}
    
    def _analyze_readability_impact(self, original: str, edited: str) -> Dict[str, Any]:
        """Analyze readability impact of changes"""
        original_words = original.split()
        edited_words = edited.split()
        
        original_avg_word_length = sum(len(word) for word in original_words) / max(len(original_words), 1)
        edited_avg_word_length = sum(len(word) for word in edited_words) / max(len(edited_words), 1)
        
        return {
            'avg_word_length_change': edited_avg_word_length - original_avg_word_length,
            'sentence_count_change': edited.count('.') - original.count('.'),
            'readability_improved': edited_avg_word_length < original_avg_word_length and len(edited_words) <= len(original_words)
        }
    
    def _predict_engagement_impact(self, original: str, edited: str) -> Dict[str, Any]:
        """Predict engagement impact of changes"""
        engagement_score_change = 0.0
        
        # Question impact
        if '?' in edited and '?' not in original:
            engagement_score_change += 0.2
        
        # Call to action impact
        cta_words = ['share', 'comment', 'think', 'thoughts']
        if any(word in edited.lower() for word in cta_words) and not any(word in original.lower() for word in cta_words):
            engagement_score_change += 0.15
        
        # Length impact
        if 100 <= len(edited) <= 200:
            engagement_score_change += 0.1
        
        return {
            'predicted_engagement_change': engagement_score_change,
            'engagement_elements_added': ['questions', 'call_to_action'] if engagement_score_change > 0 else [],
            'confidence_level': 0.7  # Simplified confidence
        }