from database.models import Product
from database.repositories.base_repository import BaseRepository
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

class ProductRepository(BaseRepository):
    """Repository for Product operations"""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, Product)
    
    def get_by_founder_id(self, founder_id: str) -> List[Product]:
        """Get all products for a founder"""
        try:
            return self.db_session.query(Product).filter(
                Product.founder_id == founder_id
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting products by founder: {e}")
            return []
    
    def create_product(self, founder_id: str, product_name: str, 
                      description: str, **kwargs) -> Optional[Product]:
        """Create new product"""
        return self.create(
            founder_id=founder_id,
            product_name=product_name,
            description=description,
            **kwargs
        )
    
    def update_niche_definition(self, product_id: str, 
                              niche_definition: Dict[str, Any]) -> Optional[Product]:
        """Update product niche definition"""
        return self.update(product_id, niche_definition=niche_definition)