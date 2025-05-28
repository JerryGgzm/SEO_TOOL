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
from .dataflow_manager import DataFlowManager
from .models import Base, Founder, Product, AnalyzedTrend, TwitterCredential, TrackedTrendRaw, AutomationRule, PostAnalytic, GeneratedContentDraft  

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
import os

# Global variables to store database engine and session factory
_engine = None
_SessionLocal = None

def init_database(database_url: str = None, create_tables: bool = False):
    """
    Initialize the database connection
    
    Args:
        database_url: The database connection URL
        create_tables: Whether to create tables
    """
    global _engine, _SessionLocal
    
    if database_url is None:
        database_url = os.getenv('DATABASE_URL', 'sqlite:///./test.db')
    
    _engine = create_engine(database_url, echo=False)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    
    if create_tables:
        Base.metadata.create_all(bind=_engine)

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Get a database session context manager
    """
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    db = _SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_db_session() -> Session:
    """
    Get a database session
    """
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    return _SessionLocal()

__all__ = [
    'BaseRepository',
    'FounderRepository',
    'ProductRepository', 
    'TrendRepository',
    'ContentRepository',
    'AnalyticsRepository',
    'DataFlowManager',
    'Base',
    'Founder',
    'Product',
    'AnalyzedTrend',
    'TwitterCredential',
    'TrackedTrendRaw',
    'AutomationRule',
    'PostAnalytic',
    'GeneratedContentDraft',
    'init_database',
    'get_db_context',
    'get_db_session'
]