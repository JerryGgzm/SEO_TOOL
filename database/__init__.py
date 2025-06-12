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

from sqlalchemy import create_engine, inspect
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
    print(f"🔨 Initializing database with URL: {database_url}")
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    print("🔨 Database initialized successfully")
    
    if create_tables:
        # 确保导入所有模型
        from .models import Base
        Base.metadata.create_all(bind=_engine)
        print("🔨 Tables created successfully")
        
        # 验证表是否真的被创建
        inspector = inspect(_engine)
        tables = inspector.get_table_names()
        print(f"🔨 Created tables: {tables}")

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Get a database session context manager
    """
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    db = _SessionLocal()
    try:
        print("🔨 Getting database session")
        yield db
        print("🔨 Committing database changes")
        db.commit()
    except Exception:
        print("🔨 Database commit failed")
        db.rollback()
        raise
    finally:
        print("🔨 Closing database session")
        db.close()

def get_db_session() -> Session:
    """
    Get a database session
    """
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    return _SessionLocal()

def health_check() -> bool:
    """
    Check database health and connectivity
    """
    try:
        if _SessionLocal is None:
            print("🔨 Database not initialized")
            return False
            
        print("🔨 Checking database health...")
        
        # Create a database session
        db = _SessionLocal()
        try:
            # Use SQLAlchemy to execute a simple query
            from sqlalchemy import text
            result = db.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            
            if row and row[0] == 1:
                print("🔨 Database is healthy")
                return True
            else:
                print("🔨 Database query returned unexpected result")
                return False
                
        except Exception as e:
            print(f"🔨 Database query failed: {e}")
            return False
        finally:
            db.close()
            
    except Exception as e:
        print(f"🔨 Database health check failed: {e}")
        return False

def get_db_manager():
    """Get the database manager instance"""
    class DatabaseManager:
        def get_session(self):
            return get_db_session()
        
        def get_context(self):
            return get_db_context()
        
        def get_connection_info(self):
            """Get database connection information"""
            return {
                'pool_size': 5,
                'max_overflow': 10,
                'echo': False
            }
        
        def drop_tables(self):
            """Drop all tables"""
            if _engine:
                Base.metadata.drop_all(bind=_engine)
        
        def create_tables(self):
            """Create all tables"""
            if _engine:
                Base.metadata.create_all(bind=_engine)
    
    return DatabaseManager()

def get_data_flow_manager():
    """
    Get a DataFlowManager instance with database session
    
    Returns:
        DataFlowManager: Configured data flow manager
    """
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    # Create a database session for the DataFlowManager
    db_session = get_db_session()
    return DataFlowManager(db_session)

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
    'get_db_session',
    'get_db_manager',
    'get_data_flow_manager',
    'health_check'
]