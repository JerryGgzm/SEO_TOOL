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
- repository.py: Database operations
- service.py: Business logic
- api.py: REST API endpoints
- frontend/: UI components
"""

from .models import (
    ReviewItem,
    ReviewStatus,
    ReviewAction,
    ReviewFeedback,
    ContentEdit,
    ReviewStatistics
)

from .service import ReviewOptimizationService
from .repository import ReviewOptimizationRepository

__all__ = [
    'ReviewItem',
    'ReviewStatus',
    'ReviewAction',
    'ReviewFeedback',
    'ContentEdit',
    'ReviewStatistics',
    'ReviewOptimizationService',
    'ReviewOptimizationRepository'
]