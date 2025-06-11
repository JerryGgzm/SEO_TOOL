"""Review Optimization Module - Database Adapter

This module handles the conversion between review service models and database models,
ensuring proper data mapping and type conversion for the review optimization process.
"""
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import json
import logging

from .models import (
    ContentDraftReview, ReviewDecision, DraftStatus, ContentPriority,
    ReviewFeedback, ContentEdit
)

logger = logging.getLogger(__name__)

class ReviewOptimizationDatabaseAdapter:
    """Converts between review service models and database format"""
    
    @staticmethod
    def to_database_format(draft_review: ContentDraftReview) -> Dict[str, Any]:
        """Convert ContentDraftReview to database format"""
        
        try:
            # Prepare review feedback
            review_feedback_data = None
            if draft_review.review_feedback:
                review_feedback_data = {
                    'feedback_text': draft_review.review_feedback.feedback_text,
                    'improvement_suggestions': draft_review.review_feedback.improvement_suggestions,
                    'style_preferences': draft_review.review_feedback.style_preferences,
                    'tone_adjustments': draft_review.review_feedback.tone_adjustments,
                    'target_audience_notes': draft_review.review_feedback.target_audience_notes
                }
            
            # Prepare edit history
            edit_history_data = []
            for edit in draft_review.edit_history:
                edit_data = {
                    'original_content': edit.original_content,
                    'edited_content': edit.edited_content,
                    'edit_reason': edit.edit_reason,
                    'edit_timestamp': edit.edit_timestamp.isoformat() if edit.edit_timestamp else None,
                    'editor_id': edit.editor_id
                }
                edit_history_data.append(edit_data)
            
            # Prepare generation metadata
            generation_metadata = draft_review.generation_metadata.copy()
            if draft_review.quality_score is not None:
                generation_metadata['quality_score'] = draft_review.quality_score
            
            # Map to database schema
            db_data = {
                'id': draft_review.id,
                'founder_id': draft_review.founder_id,
                'content_type': draft_review.content_type,
                'generated_text': draft_review.original_content,
                'current_content': draft_review.current_content,
                'status': draft_review.status.value,
                'priority': draft_review.priority.value,
                
                # Review information
                'reviewed_at': draft_review.reviewed_at,
                'reviewer_id': draft_review.reviewer_id,
                'review_decision': draft_review.review_decision.value if draft_review.review_decision else None,
                'review_feedback': review_feedback_data,
                
                # Edit history
                'edit_history': edit_history_data,
                
                # Metadata
                'tags': draft_review.tags,
                'analyzed_trend_id': draft_review.trend_id,
                'ai_generation_metadata': generation_metadata,
                'seo_suggestions': draft_review.seo_suggestions,
                'quality_score': draft_review.quality_score,
                
                # Scheduling
                'scheduled_post_time': draft_review.scheduled_time,
                'posted_at': draft_review.posted_at,
                'posted_tweet_id': draft_review.posted_tweet_id,
                
                # Timestamps
                'created_at': draft_review.created_at,
                'updated_at': draft_review.updated_at
            }
            
            return db_data
            
        except Exception as e:
            logger.error(f"Failed to convert to database format: {e}")
            raise
    
    @staticmethod
    def from_database_format(db_data: Any) -> ContentDraftReview:
        """Convert database model to ContentDraftReview"""
        
        try:
            # Handle review feedback
            review_feedback = None
            if hasattr(db_data, 'review_feedback') and db_data.review_feedback:
                feedback_data = db_data.review_feedback
                if isinstance(feedback_data, str):
                    # Handle simple string feedback
                    review_feedback = ReviewFeedback(
                        feedback_text=feedback_data,
                        improvement_suggestions=[],
                        style_preferences={},
                        tone_adjustments=None,
                        target_audience_notes=None
                    )
                elif isinstance(feedback_data, dict):
                    # Handle structured feedback
                    review_feedback = ReviewFeedback(
                        feedback_text=feedback_data.get('feedback_text', ''),
                        improvement_suggestions=feedback_data.get('improvement_suggestions', []),
                        style_preferences=feedback_data.get('style_preferences', {}),
                        tone_adjustments=feedback_data.get('tone_adjustments'),
                        target_audience_notes=feedback_data.get('target_audience_notes')
                    )
            
            # Handle edit history
            edit_history = []
            if hasattr(db_data, 'edit_history') and db_data.edit_history:
                for edit_data in db_data.edit_history:
                    try:
                        edit = ContentEdit(
                            original_content=edit_data.get('original_content', ''),
                            edited_content=edit_data.get('edited_content', ''),
                            edit_reason=edit_data.get('edit_reason'),
                            edit_timestamp=datetime.fromisoformat(edit_data['edit_timestamp']) if edit_data.get('edit_timestamp') else datetime.utcnow(),
                            editor_id=edit_data.get('editor_id', '')
                        )
                        edit_history.append(edit)
                    except Exception as e:
                        logger.warning(f"Failed to parse edit history item: {e}")
                        continue
            
            # Extract metadata safely
            generation_metadata = {}
            if hasattr(db_data, 'ai_generation_metadata') and db_data.ai_generation_metadata:
                generation_metadata = db_data.ai_generation_metadata
            
            seo_suggestions = {}
            if hasattr(db_data, 'seo_suggestions') and db_data.seo_suggestions:
                seo_suggestions = db_data.seo_suggestions
            
            # Handle status conversion
            try:
                status = DraftStatus(db_data.status) if hasattr(db_data, 'status') and db_data.status else DraftStatus.PENDING_REVIEW
            except ValueError:
                logger.warning(f"Invalid status value: {db_data.status}")
                status = DraftStatus.PENDING_REVIEW
            
            # Handle priority conversion
            try:
                priority = ContentPriority(db_data.priority) if hasattr(db_data, 'priority') and db_data.priority else ContentPriority.MEDIUM
            except ValueError:
                logger.warning(f"Invalid priority value: {db_data.priority}")
                priority = ContentPriority.MEDIUM
            
            # Handle review decision conversion
            review_decision = None
            if hasattr(db_data, 'review_decision') and db_data.review_decision:
                try:
                    review_decision = ReviewDecision(db_data.review_decision)
                except ValueError:
                    logger.warning(f"Invalid review decision value: {db_data.review_decision}")
            
            # Create ContentDraftReview object
            draft_review = ContentDraftReview(
                id=str(db_data.id),
                founder_id=str(db_data.founder_id),
                content_type=db_data.content_type,
                original_content=db_data.generated_text or '',
                current_content=getattr(db_data, 'current_content', db_data.generated_text) or '',
                status=status,
                priority=priority,
                
                # Review information
                reviewed_at=getattr(db_data, 'reviewed_at', None),
                reviewer_id=getattr(db_data, 'reviewer_id', None),
                review_decision=review_decision,
                review_feedback=review_feedback,
                
                # Edit history
                edit_history=edit_history,
                
                # Metadata
                tags=getattr(db_data, 'tags', []) or [],
                trend_id=str(db_data.analyzed_trend_id) if getattr(db_data, 'analyzed_trend_id', None) else None,
                generation_metadata=generation_metadata,
                seo_suggestions=seo_suggestions,
                quality_score=getattr(db_data, 'quality_score', None),
                
                # Scheduling
                scheduled_time=getattr(db_data, 'scheduled_post_time', None),
                posted_at=getattr(db_data, 'posted_at', None),
                posted_tweet_id=getattr(db_data, 'posted_tweet_id', None),
                
                # Timestamps
                created_at=getattr(db_data, 'created_at', datetime.utcnow()),
                updated_at=getattr(db_data, 'updated_at', datetime.utcnow())
            )
            
            return draft_review
            
        except Exception as e:
            logger.error(f"Failed to convert from database format: {e}")
            raise
    
    @staticmethod
    def batch_to_database_format(drafts: List[ContentDraftReview]) -> List[Dict[str, Any]]:
        """Convert multiple drafts to database format"""
        try:
            return [
                ReviewOptimizationDatabaseAdapter.to_database_format(draft)
                for draft in drafts
            ]
        except Exception as e:
            logger.error(f"Failed to convert batch to database format: {e}")
            return []
    
    @staticmethod
    def batch_from_database_format(db_data_list: List[Any]) -> List[ContentDraftReview]:
        """Convert multiple database records to service models"""
        try:
            drafts = []
            for db_data in db_data_list:
                try:
                    draft = ReviewOptimizationDatabaseAdapter.from_database_format(db_data)
                    drafts.append(draft)
                except Exception as e:
                    logger.warning(f"Failed to convert database record: {e}")
                    continue
            return drafts
        except Exception as e:
            logger.error(f"Failed to convert batch from database format: {e}")
            return []
    
    @staticmethod
    def extract_review_analytics_data(db_data: Any) -> Dict[str, Any]:
        """Extract analytics data from database record"""
        try:
            analytics_data = {
                'draft_id': str(db_data.id),
                'founder_id': str(db_data.founder_id),
                'content_type': db_data.content_type,
                'status': db_data.status,
                'review_decision': getattr(db_data, 'review_decision', None),
                'quality_score': getattr(db_data, 'quality_score', None),
                'created_at': getattr(db_data, 'created_at', None),
                'reviewed_at': getattr(db_data, 'reviewed_at', None),
                'updated_at': getattr(db_data, 'updated_at', None),
                'tags': getattr(db_data, 'tags', []) or [],
                'priority': getattr(db_data, 'priority', 'medium')
            }
            
            # Calculate review time if both timestamps are available
            if analytics_data['created_at'] and analytics_data['reviewed_at']:
                time_diff = analytics_data['reviewed_at'] - analytics_data['created_at']
                analytics_data['review_time_minutes'] = time_diff.total_seconds() / 60
            
            return analytics_data
            
        except Exception as e:
            logger.error(f"Failed to extract analytics data: {e}")
            return {}
    
    @staticmethod
    def prepare_status_update_data(status_request) -> Dict[str, Any]:
        """Prepare status update data for database"""
        try:
            update_data = {
                'status': status_request.status.value,
                'updated_at': datetime.utcnow()
            }
            
            if status_request.updated_content:
                update_data['current_content'] = status_request.updated_content
            
            if status_request.reviewer_notes:
                update_data['reviewer_notes'] = status_request.reviewer_notes
            
            if status_request.schedule_time:
                update_data['scheduled_post_time'] = status_request.schedule_time
            
            return update_data
            
        except Exception as e:
            logger.error(f"Failed to prepare status update data: {e}")
            return {}
    
    @staticmethod
    def prepare_batch_update_data(batch_decisions: List) -> List[Dict[str, Any]]:
        """Prepare batch update data for database"""
        try:
            batch_updates = []
            
            for decision in batch_decisions:
                update_data = {
                    'draft_id': decision.draft_id,
                    'review_decision': decision.decision.value,
                    'reviewed_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                
                # Handle decision-specific updates
                if decision.decision == ReviewDecision.APPROVE:
                    update_data['status'] = DraftStatus.APPROVED.value
                elif decision.decision == ReviewDecision.EDIT_AND_APPROVE:
                    update_data['status'] = DraftStatus.APPROVED.value
                    if decision.edited_content:
                        update_data['current_content'] = decision.edited_content
                elif decision.decision == ReviewDecision.REJECT:
                    update_data['status'] = DraftStatus.REJECTED.value
                
                # Add optional fields
                if decision.feedback:
                    update_data['review_feedback'] = decision.feedback
                
                if decision.tags:
                    update_data['tags'] = decision.tags
                
                if decision.priority:
                    update_data['priority'] = decision.priority.value
                
                batch_updates.append(update_data)
            
            return batch_updates
            
        except Exception as e:
            logger.error(f"Failed to prepare batch update data: {e}")
            return []
    
    @staticmethod
    def format_review_history_item(db_data: Any) -> Dict[str, Any]:
        """Format database record for review history"""
        try:
            # Get content preview
            content = getattr(db_data, 'current_content', '') or getattr(db_data, 'generated_text', '')
            content_preview = content[:100] + "..." if len(content) > 100 else content
            
            return {
                'draft_id': str(db_data.id),
                'content_preview': content_preview,
                'status': db_data.status,
                'decision': getattr(db_data, 'review_decision', None),
                'reviewed_at': getattr(db_data, 'reviewed_at', db_data.updated_at),
                'content_type': db_data.content_type,
                'tags': getattr(db_data, 'tags', []) or [],
                'quality_score': getattr(db_data, 'quality_score', None),
                'priority': getattr(db_data, 'priority', 'medium'),
                'created_at': getattr(db_data, 'created_at', None)
            }
            
        except Exception as e:
            logger.error(f"Failed to format review history item: {e}")
            return {}
    
    @staticmethod
    def aggregate_review_summary_data(db_records: List[Any]) -> Dict[str, Any]:
        """Aggregate data for review summary"""
        try:
            summary_data = {
                'total_pending': 0,
                'total_approved': 0,
                'total_rejected': 0,
                'total_edited': 0,
                'quality_scores': [],
                'tags': [],
                'review_times': []
            }
            
            for record in db_records:
                status = getattr(record, 'status', '')
                
                if status == DraftStatus.PENDING_REVIEW.value:
                    summary_data['total_pending'] += 1
                elif status == DraftStatus.APPROVED.value:
                    decision = getattr(record, 'review_decision', '')
                    if decision == ReviewDecision.EDIT_AND_APPROVE.value:
                        summary_data['total_edited'] += 1
                    else:
                        summary_data['total_approved'] += 1
                elif status == DraftStatus.REJECTED.value:
                    summary_data['total_rejected'] += 1
                
                # Collect quality scores
                quality_score = getattr(record, 'quality_score', None)
                if quality_score is not None:
                    summary_data['quality_scores'].append(quality_score)
                
                # Collect tags
                tags = getattr(record, 'tags', []) or []
                summary_data['tags'].extend(tags)
                
                # Calculate review time if possible
                created_at = getattr(record, 'created_at', None)
                reviewed_at = getattr(record, 'reviewed_at', None)
                if created_at and reviewed_at:
                    time_diff = (reviewed_at - created_at).total_seconds() / 60
                    summary_data['review_times'].append(time_diff)
            
            return summary_data
            
        except Exception as e:
            logger.error(f"Failed to aggregate review summary data: {e}")
            return {}
    
    @staticmethod
    def format_analytics_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format raw analytics data for service consumption"""
        try:
            formatted_data = {
                'total_reviews': raw_data.get('total_reviews', 0),
                'decision_breakdown': {},
                'content_type_breakdown': {},
                'avg_review_time_minutes': 0.0,
                'quality_trend': [],
                'top_rejection_reasons': [],
                'productivity_metrics': {}
            }
            
            # Process decision breakdown
            decisions = raw_data.get('decisions', [])
            for decision in decisions:
                formatted_data['decision_breakdown'][decision] = decisions.count(decision)
            
            # Process content type breakdown
            content_types = raw_data.get('content_types', [])
            for content_type in set(content_types):
                formatted_data['content_type_breakdown'][content_type] = content_types.count(content_type)
            
            # Calculate average review time
            review_times = raw_data.get('review_times', [])
            if review_times:
                formatted_data['avg_review_time_minutes'] = sum(review_times) / len(review_times)
            
            # Process quality trend
            quality_scores = raw_data.get('quality_scores_by_date', {})
            for date, scores in quality_scores.items():
                if scores:
                    avg_score = sum(scores) / len(scores)
                    formatted_data['quality_trend'].append({
                        'date': date,
                        'avg_quality_score': avg_score,
                        'review_count': len(scores)
                    })
            
            # Process rejection reasons
            rejection_reasons = raw_data.get('rejection_feedback', [])
            # Simple keyword extraction from feedback
            reason_keywords = {}
            for feedback in rejection_reasons:
                if feedback:
                    words = feedback.lower().split()
                    for word in words:
                        if len(word) > 4:  # Only consider meaningful words
                            reason_keywords[word] = reason_keywords.get(word, 0) + 1
            
            # Get top reasons
            top_reasons = sorted(reason_keywords.items(), key=lambda x: x[1], reverse=True)
            formatted_data['top_rejection_reasons'] = [reason[0] for reason in top_reasons[:5]]
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"Failed to format analytics data: {e}")
            return {}
    
    @staticmethod
    def validate_draft_data(draft_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate draft data before database operations"""
        try:
            errors = []
            
            # Required fields
            required_fields = ['founder_id', 'content_type', 'generated_text']
            for field in required_fields:
                if not draft_data.get(field):
                    errors.append(f"Missing required field: {field}")
            
            # Validate status
            status = draft_data.get('status')
            if status and status not in [s.value for s in DraftStatus]:
                errors.append(f"Invalid status: {status}")
            
            # Validate priority
            priority = draft_data.get('priority')
            if priority and priority not in [p.value for p in ContentPriority]:
                errors.append(f"Invalid priority: {priority}")
            
            # Validate review decision
            decision = draft_data.get('review_decision')
            if decision and decision not in [d.value for d in ReviewDecision]:
                errors.append(f"Invalid review decision: {decision}")
            
            # Validate content length
            content = draft_data.get('generated_text', '')
            if len(content) > 5000:  # Reasonable upper limit
                errors.append("Content too long (max 5000 characters)")
            
            # Validate edit history format
            edit_history = draft_data.get('edit_history', [])
            if edit_history and not isinstance(edit_history, list):
                errors.append("Edit history must be a list")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"Failed to validate draft data: {e}")
            return False, [f"Validation error: {str(e)}"]
    
    @staticmethod
    def sanitize_content(content: str) -> str:
        """Sanitize content for database storage"""
        try:
            if not content:
                return ""
            
            # Remove null bytes and control characters
            sanitized = content.replace('\x00', '').replace('\r', '').strip()
            
            # Limit length
            if len(sanitized) > 5000:
                sanitized = sanitized[:4997] + "..."
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Failed to sanitize content: {e}")
            return content or ""
    
    @staticmethod
    def extract_metadata_for_search(draft_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract searchable metadata from draft data"""
        try:
            metadata = {
                'content_keywords': [],
                'hashtags': [],
                'mentions': [],
                'has_question': False,
                'has_link': False,
                'content_length': 0,
                'word_count': 0
            }
            
            content = draft_data.get('current_content') or draft_data.get('generated_text', '')
            
            if content:
                # Extract basic metrics
                metadata['content_length'] = len(content)
                words = content.split()
                metadata['word_count'] = len(words)
                
                # Extract hashtags
                hashtags = [word[1:] for word in words if word.startswith('#')]
                metadata['hashtags'] = hashtags
                
                # Extract mentions
                mentions = [word[1:] for word in words if word.startswith('@')]
                metadata['mentions'] = mentions
                
                # Check for questions
                metadata['has_question'] = '?' in content
                
                # Check for links
                metadata['has_link'] = 'http' in content.lower()
                
                # Extract keywords (simple approach)
                stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
                keywords = [word.lower().strip('.,!?;:') for word in words 
                           if len(word) > 3 and word.lower() not in stop_words 
                           and not word.startswith('#') and not word.startswith('@')]
                metadata['content_keywords'] = list(set(keywords))[:10]  # Top 10 unique keywords
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to extract metadata: {e}")
            return {}