from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Optional, List, Dict, Any, Type, TypeVar
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()
T = TypeVar('T')

class BaseRepository(ABC):
    """Base repository class with common CRUD operations"""
    
    def __init__(self, db_session: Session, model_class: Type[T]):
        self.db_session = db_session
        self.model_class = model_class
    
    def create(self, **kwargs) -> Optional[T]:
        """Create a new record"""
        try:
            instance = self.model_class(**kwargs)
            self.db_session.add(instance)
            self.db_session.commit()
            self.db_session.refresh(instance)
            return instance
        except IntegrityError as e:
            self.db_session.rollback()
            logger.error(f"Integrity error creating {self.model_class.__name__}: {e}")
            return None
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error creating {self.model_class.__name__}: {e}")
            return None
    
    def get_by_id(self, record_id: Any) -> Optional[T]:
        """Get record by ID"""
        try:
            return self.db_session.query(self.model_class).filter(
                self.model_class.id == record_id
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting {self.model_class.__name__} by ID: {e}")
            return None
    
    def update(self, record_id: Any, **kwargs) -> Optional[T]:
        """Update record by ID"""
        try:
            instance = self.get_by_id(record_id)
            if not instance:
                return None
            
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            self.db_session.commit()
            self.db_session.refresh(instance)
            return instance
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error updating {self.model_class.__name__}: {e}")
            return None
    
    def delete(self, record_id: Any) -> bool:
        """Delete record by ID"""
        try:
            instance = self.get_by_id(record_id)
            if not instance:
                return False
            
            self.db_session.delete(instance)
            self.db_session.commit()
            return True
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error deleting {self.model_class.__name__}: {e}")
            return False
    
    def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """List all records with pagination"""
        try:
            return self.db_session.query(self.model_class).offset(offset).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error listing {self.model_class.__name__}: {e}")
            return []