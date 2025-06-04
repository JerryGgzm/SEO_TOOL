"""Business logic for review optimization"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import uuid
import logging

from .repository import ReviewOptimizationRepository
from .models import (
    ReviewItem, ReviewStatus, ReviewAction, ReviewFeedback,
    ContentEdit, ReviewStatistics, ReviewFilterRequest,
    ReviewBatchRequest
)
from modules.content_generation import ContentGenerationService
from modules.scheduling_posting import SchedulingPostingService

logger = logging.getLogger(__name__)

class ReviewOptimizationService:
    """Service for content review and optimization"""
    
    def __init__(self, 
                 repository: ReviewOptimizationRepository,
                 content_service: ContentGenerationService,
                 scheduling_service: SchedulingPostingService):
        self.repository = repository
        self.content_service = content_service
        self.scheduling_service = scheduling_service
    
    def create_review_item_from_draft(self, draft_id: str, founder_id: str) -> Optional[str]:
        """Create review item from content draft"""
        try:
            # Get draft from content generation service
            draft = self.content_service.get_draft(draft_id)
            if not draft or draft.founder_id != founder_id:
                logger.error(f"Draft {draft_id} not found or access denied")
                return None
            
            # Determine priority based on AI confidence and trend relevance
            priority = self._calculate_review_priority(draft)
            
            # Create review item
            review_item = ReviewItem(
                id=str(uuid.uuid4()),
                content_draft_id=draft_id,
                founder_id=founder_id,
                content_type=draft.content_type,
                original_content=draft.generated_text,
                current_content=draft.generated_text,
                trend_context=draft.trend_context or {},
                generation_reason=draft.generation_metadata.get('reason', 'AI generated'),
                ai_confidence_score=draft.quality_score or 0.5,
                seo_suggestions=draft.seo_suggestions or {},
                hashtags=draft.seo_suggestions.get('hashtags', []) if draft.seo_suggestions else [],
                keywords=draft.seo_suggestions.get('keywords', []) if draft.seo_suggestions else [],
                review_priority=priority
            )
            
            # Save to repository
            if self.repository.create_review_item(review_item):
                logger.info(f"Created review item {review_item.id} for draft {draft_id}")
                return review_item.id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to create review item from draft: {e}")
            return None
    
    def get_review_queue(self, founder_id: str, 
                        filter_request: Optional[ReviewFilterRequest] = None) -> List[ReviewItem]:
        """Get review queue for founder"""
        return self.repository.get_review_items(founder_id, filter_request)
    
    def get_review_item(self, item_id: str, founder_id: str) -> Optional[ReviewItem]:
        """Get specific review item"""
        item = self.repository.get_review_item(item_id)
        if item and item.founder_id == founder_id:
            return item
        return None
    
    def update_content(self, item_id: str, founder_id: str, 
                      new_content: str, editor_id: str) -> bool:
        """Update content of review item"""
        try:
            # Get item
            item = self.get_review_item(item_id, founder_id)
            if not item:
                return False
            
            # Create edit record
            edit = ContentEdit(
                field='content',
                old_value=item.current_content,
                new_value=new_content,
                edited_by=editor_id
            )
            
            # Add to history
            if not self.repository.add_edit_history(item_id, edit):
                return False
            
            # Update current content
            updates = {
                'current_content': new_content,
                'status': ReviewStatus.EDITED
            }
            
            return self.repository.update_review_item(item_id, updates)
            
        except Exception as e:
            logger.error(f"Failed to update content: {e}")
            return False
    
    def update_seo_elements(self, item_id: str, founder_id: str,
                           hashtags: Optional[List[str]] = None,
                           keywords: Optional[List[str]] = None,
                           editor_id: str = None) -> bool:
        """Update SEO elements of review item"""
        try:
            # Get item
            item = self.get_review_item(item_id, founder_id)
            if not item:
                return False
            
            updates = {}
            
            # Update hashtags
            if hashtags is not None:
                edit = ContentEdit(
                    field='hashtags',
                    old_value=str(item.hashtags),
                    new_value=str(hashtags),
                    edited_by=editor_id
                )
                self.repository.add_edit_history(item_id, edit)
                updates['hashtags'] = hashtags
            
            # Update keywords
            if keywords is not None:
                edit = ContentEdit(
                    field='keywords',
                    old_value=str(item.keywords),
                    new_value=str(keywords),
                    edited_by=editor_id
                )
                self.repository.add_edit_history(item_id, edit)
                updates['keywords'] = keywords
            
            if updates:
                updates['status'] = ReviewStatus.EDITED
                return self.repository.update_review_item(item_id, updates)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update SEO elements: {e}")
            return False
    
    def perform_action(self, item_id: str, founder_id: str, action: ReviewAction,
                      feedback: Optional[ReviewFeedback] = None,
                      scheduled_time: Optional[datetime] = None,
                      reviewer_id: str = None) -> Tuple[bool, Optional[str]]:
        """Perform review action on item"""
        try:
            # Get item
            item = self.get_review_item(item_id, founder_id)
            if not item:
                return False, "Item not found"
            
            # Prepare updates
            updates = {
                'reviewed_at': datetime.utcnow(),
                'reviewed_by': reviewer_id
            }
            
            if feedback:
                updates['feedback'] = feedback.dict()
            
            # Handle different actions
            if action == ReviewAction.APPROVE:
                updates['status'] = ReviewStatus.APPROVED
                
                # Send to scheduling module
                success = self.scheduling_service.add_to_queue(
                    content_draft_id=item.content_draft_id,
                    content_text=item.current_content,
                    content_type=item.content_type,
                    hashtags=item.hashtags,
                    scheduled_time=scheduled_time
                )
                
                if not success:
                    return False, "Failed to add to scheduling queue"
                
                if scheduled_time:
                    updates['status'] = ReviewStatus.SCHEDULED
                    updates['scheduled_time'] = scheduled_time
            
            elif action == ReviewAction.REJECT:
                updates['status'] = ReviewStatus.REJECTED
            
            elif action == ReviewAction.SCHEDULE:
                if not scheduled_time:
                    return False, "Scheduled time required for schedule action"
                
                updates['status'] = ReviewStatus.SCHEDULED
                updates['scheduled_time'] = scheduled_time
                
                # Send to scheduling module
                success = self.scheduling_service.add_to_queue(
                    content_draft_id=item.content_draft_id,
                    content_text=item.current_content,
                    content_type=item.content_type,
                    hashtags=item.hashtags,
                    scheduled_time=scheduled_time
                )
                
                if not success:
                    return False, "Failed to schedule content"
            
            elif action == ReviewAction.REQUEST_REVISION:
                # Send back to content generation for revision
                if feedback and feedback.improvement_suggestions:
                    revision_request = {
                        'draft_id': item.content_draft_id,
                        'feedback': feedback.comments,
                        'suggestions': feedback.improvement_suggestions
                    }
                    
                    new_draft_id = self.content_service.request_revision(
                        item.content_draft_id, revision_request
                    )
                    
                    if new_draft_id:
                        # Create new review item for revised draft
                        self.create_review_item_from_draft(new_draft_id, founder_id)
                        updates['status'] = ReviewStatus.REJECTED
                    else:
                        return False, "Failed to request revision"
                else:
                    return False, "Feedback with suggestions required for revision request"
            
            # Update item
            if self.repository.update_review_item(item_id, updates):
                return True, f"Action {action.value} completed successfully"
            
            return False, "Failed to update item"
            
        except Exception as e:
            logger.error(f"Failed to perform action: {e}")
            return False, str(e)
    
    def batch_review(self, batch_request: ReviewBatchRequest, 
                    founder_id: str, reviewer_id: str) -> Dict[str, Any]:
        """Perform batch review operations"""
        results = {
            'successful': [],
            'failed': [],
            'total': len(batch_request.item_ids)
        }
        
        for item_id in batch_request.item_ids:
            success, message = self.perform_action(
                item_id=item_id,
                founder_id=founder_id,
                action=batch_request.action,
                feedback=batch_request.feedback,
                scheduled_time=batch_request.scheduled_time,
                reviewer_id=reviewer_id
            )
            
            if success:
                results['successful'].append(item_id)
            else:
                results['failed'].append({
                    'item_id': item_id,
                    'error': message
                })
        
        return results
    
    def get_review_statistics(self, founder_id: str, days: int = 30) -> ReviewStatistics:
        """Get review statistics"""
        return self.repository.get_review_statistics(founder_id, days)
    
    def _calculate_review_priority(self, draft: Any) -> int:
        """Calculate review priority based on various factors"""
        priority = 5  # Base priority
        
        # Increase priority for high confidence scores
        if hasattr(draft, 'quality_score') and draft.quality_score:
           if draft.quality_score > 0.8:
               priority += 2
           elif draft.quality_score > 0.6:
               priority += 1
           elif draft.quality_score < 0.4:
               priority -= 1
       
        # Increase priority for trending content
        if hasattr(draft, 'trend_context') and draft.trend_context:
            if draft.trend_context.get('trend_score', 0) > 0.7:
                priority += 2
            elif draft.trend_context.get('is_emerging', False):
                priority += 1
        
        # Adjust for content type
        if hasattr(draft, 'content_type'):
            if draft.content_type == 'reply':
                priority += 1  # Replies often need quick review
            elif draft.content_type == 'thread':
                priority -= 1  # Threads can take more time
        
        # Ensure priority stays within bounds
        return max(1, min(10, priority))