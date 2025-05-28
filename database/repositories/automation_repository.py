from typing import List, Optional, Dict, Any
from sqlalchemy import and_, or_
from datetime import datetime
import logging

from .base_repository import BaseRepository
from ..models import AutomationRule



class AutomationRepository(BaseRepository):
    """Repository for automation rules operations"""
    
    def __init__(self, db_session):
        super().__init__(db_session, AutomationRule)
    
    def get_active_rules(self, founder_id: str) -> List[AutomationRule]:
        """Get active automation rules for a founder"""
        try:
            return self.db_session.query(AutomationRule).filter(
                AutomationRule.founder_id == founder_id,
                AutomationRule.is_active == True
            ).order_by(AutomationRule.created_at.desc()).all()
            
        except Exception as e:
            logger.error(f"Failed to get active rules: {e}")
            return []
    
    def create_rule(self, founder_id: str, rule_name: str, 
                   trigger_conditions: Dict[str, Any], 
                   action_to_take: Dict[str, Any]) -> Optional[AutomationRule]:
        """Create new automation rule"""
        return self.create(
            founder_id=founder_id,
            rule_name=rule_name,
            trigger_conditions=trigger_conditions,
            action_to_take=action_to_take
        )
    
    def update_trigger_count(self, rule_id: str) -> bool:
        """Update rule trigger count and last triggered time"""
        try:
            rule = self.get_by_id(rule_id)
            if rule:
                rule.trigger_count = (rule.trigger_count or 0) + 1
                rule.last_triggered_at = datetime.utcnow()
                self.db_session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update trigger count: {e}")
            return False
    
    def deactivate_rule(self, rule_id: str, founder_id: str) -> bool:
        """Deactivate an automation rule"""
        try:
            rule = self.db_session.query(AutomationRule).filter(
                AutomationRule.id == rule_id,
                AutomationRule.founder_id == founder_id
            ).first()
            
            if rule:
                rule.is_active = False
                self.db_session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to deactivate rule: {e}")
            return False