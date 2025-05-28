"""
Database Repositories Module

This module provides data access layer repositories for all database operations.
Each repository encapsulates the database logic for a specific domain model.
"""

from .repositories.base_repository import BaseRepository
from .repositories.founder_repository import FounderRepository
from .repositories.product_repository import ProductRepository
from .repositories.trend_repository import TrendRepository
from .repositories.content_repository import ContentRepository
from .repositories.analytics_repository import AnalyticsRepository

__all__ = [
    'BaseRepository',
    'FounderRepository',
    'ProductRepository', 
    'TrendRepository',
    'ContentRepository',
    'AnalyticsRepository'
]