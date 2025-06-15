"""ReviewOptimizationModule - Human Review and Optimization Interface

This module provides:
1. Review dashboard for AI-generated content
2. Content editing and optimization tools
3. Approval/rejection workflow
4. SEO optimization editing
5. Batch operations support
6. Performance tracking for approved content

Main Components:
- models.py: Data models for review items
- database_adapter.py: Database operations adapter
- service.py: Business logic
- api.py: REST API endpoints
"""

from .models import (
    ReviewDecision,
    DraftStatus,
    ContentPriority,
    ReviewFeedback,
    ContentEdit,
    ReviewDecisionRequest,
    BatchReviewRequest,
    BatchReviewDecision,
    ContentRegenerationRequest,
    StatusUpdateRequest,
    ContentDraftReview,
    ReviewHistoryItem,
    ReviewSummary,
    ReviewAnalytics,
    RegenerationResult,
    ReviewQueue,
    ReviewPreferences,
    ContentComparisonResult
)

from .service import ReviewOptimizationService
from .database_adapter import ReviewOptimizationDatabaseAdapter

__all__ = [
    'ReviewDecision',
    'DraftStatus',
    'ContentPriority',
    'ReviewFeedback',
    'ContentEdit',
    'ReviewDecisionRequest',
    'BatchReviewRequest',
    'BatchReviewDecision',
    'ContentRegenerationRequest',
    'StatusUpdateRequest',
    'ContentDraftReview',
    'ReviewHistoryItem',
    'ReviewSummary',
    'ReviewAnalytics',
    'RegenerationResult',
    'ReviewQueue',
    'ReviewPreferences',
    'ContentComparisonResult',
    'ReviewOptimizationService',
    'ReviewOptimizationDatabaseAdapter'
]