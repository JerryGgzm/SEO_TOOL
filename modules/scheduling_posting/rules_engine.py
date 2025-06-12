"""Scheduling and Posting Module - Internal Rules Engine

This module provides internal rules engine functionality for content publishing validation.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, time
import logging
from enum import Enum

from .models import (
    SchedulingPreferences, PublishingRule, RuleCheckResult,
    SchedulingRule, PublishStatus
)

logger = logging.getLogger(__name__)

class RuleSeverity(str, Enum):
    """Rule violation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class RuleViolation:
    """Represents a rule violation"""
    def __init__(self, rule_name: str, severity: RuleSeverity, message: str, 
                 blocking: bool = False, suggestion: Optional[str] = None):
        self.rule_name = rule_name
        self.severity = severity
        self.message = message
        self.blocking = blocking
        self.suggestion = suggestion

class InternalRulesEngine:
    """
    Internal rules engine for scheduling and publishing validation
    """
    
    def __init__(self, data_flow_manager):
        self.data_flow_manager = data_flow_manager
        self.default_rules = self._initialize_default_rules()
    
    def _initialize_default_rules(self) -> List[SchedulingRule]:
        """Initialize default publishing rules"""
        return [
            SchedulingRule(
                name="Daily Posting Limit",
                rule_type=PublishingRule.FREQUENCY_LIMIT,
                enabled=True,
                priority=1,
                conditions={
                    "type": "daily_limit",
                    "max_posts_per_day": 5
                },
                actions={
                    "type": "block",
                    "message": "Daily posting limit exceeded"
                }
            ),
            SchedulingRule(
                name="Minimum Interval",
                rule_type=PublishingRule.CONTENT_SPACING,
                enabled=True,
                priority=2,
                conditions={
                    "type": "min_interval",
                    "min_minutes": 60
                },
                actions={
                    "type": "block",
                    "message": "Minimum interval between posts not met"
                }
            ),
            SchedulingRule(
                name="Quiet Hours",
                rule_type=PublishingRule.TIME_WINDOW,
                enabled=True,
                priority=3,
                conditions={
                    "type": "time_window",
                    "start_time": "22:00",
                    "end_time": "08:00"
                },
                actions={
                    "type": "warn",
                    "message": "Posting during quiet hours"
                }
            ),
            SchedulingRule(
                name="Weekend Restriction",
                rule_type=PublishingRule.TIME_WINDOW,
                enabled=False,  # Disabled by default
                priority=4,
                conditions={
                    "type": "weekend_restriction",
                    "allow_weekends": False
                },
                actions={
                    "type": "block",
                    "message": "Weekend posting is disabled"
                }
            ),
            SchedulingRule(
                name="Content Duplication",
                rule_type=PublishingRule.PLATFORM_SPECIFIC,
                enabled=True,
                priority=5,
                conditions={
                    "type": "duplicate_check",
                    "similarity_threshold": 0.8,
                    "check_period_days": 7
                },
                actions={
                    "type": "warn",
                    "message": "Similar content posted recently"
                }
            )
        ]
    
    async def validate_publishing_rules(self, user_id: str, content_id: Optional[str] = None,
                                      proposed_time: Optional[datetime] = None,
                                      preferences: Optional[SchedulingPreferences] = None) -> RuleCheckResult:
        """
        Validate publishing rules for content
        
        Args:
            user_id: User ID
            content_id: Optional content ID
            proposed_time: Proposed publishing time
            preferences: User scheduling preferences
            
        Returns:
            Rule check result
        """
        try:
            logger.info(f"Validating publishing rules for user {user_id}")
            
            violations = []
            recommendations = []
            can_publish = True
            
            # Get user preferences if not provided
            if not preferences:
                preferences = await self._get_user_preferences(user_id)
            
            # Get user-specific rules
            user_rules = await self._get_user_rules(user_id)
            active_rules = [rule for rule in user_rules if rule.enabled]
            
            # Validate against each rule
            for rule in active_rules:
                violation = await self._check_rule(rule, user_id, content_id, proposed_time, preferences)
                if violation:
                    violations.append(violation.message)
                    if violation.blocking:
                        can_publish = False
                    if violation.suggestion:
                        recommendations.append(violation.suggestion)
            
            # Generate suggested optimal times
            suggested_times = await self._generate_optimal_times(user_id, preferences)
            
            # Find next available slot
            next_slot = await self._find_next_available_slot(user_id, preferences)
            
            # Get current daily count
            current_daily_count = 0
            if proposed_time:
                current_daily_count = self.data_flow_manager.get_daily_post_count(
                    user_id, proposed_time.date()
                )
            
            return RuleCheckResult(
                can_publish=can_publish,
                violations=violations,
                recommendations=recommendations,
                suggested_times=suggested_times,
                next_available_slot=next_slot,
                current_daily_count=current_daily_count,
                daily_limit=preferences.max_posts_per_day
            )
            
        except Exception as e:
            logger.error(f"Failed to validate publishing rules: {e}")
            return RuleCheckResult(
                can_publish=False,
                violations=[f"Rule validation failed: {str(e)}"],
                recommendations=["Please try again later"]
            )
    
    async def _check_rule(self, rule: SchedulingRule, user_id: str, content_id: Optional[str],
                         proposed_time: Optional[datetime], 
                         preferences: SchedulingPreferences) -> Optional[RuleViolation]:
        """Check a specific rule"""
        try:
            rule_type = rule.conditions.get("type")
            
            if rule_type == "daily_limit":
                return await self._check_daily_limit_rule(rule, user_id, proposed_time, preferences)
            
            elif rule_type == "min_interval":
                return await self._check_min_interval_rule(rule, user_id, proposed_time, preferences)
            
            elif rule_type == "time_window":
                return await self._check_time_window_rule(rule, user_id, proposed_time, preferences)
            
            elif rule_type == "weekend_restriction":
                return await self._check_weekend_rule(rule, user_id, proposed_time, preferences)
            
            elif rule_type == "duplicate_check":
                return await self._check_duplicate_content_rule(rule, user_id, content_id)
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to check rule {rule.name}: {e}")
            return None
    
    async def _check_daily_limit_rule(self, rule: SchedulingRule, user_id: str,
                                    proposed_time: Optional[datetime],
                                    preferences: SchedulingPreferences) -> Optional[RuleViolation]:
        """Check daily posting limit rule"""
        if not proposed_time:
            return None
        
        max_posts = rule.conditions.get("max_posts_per_day", preferences.max_posts_per_day)
        daily_count = self.data_flow_manager.get_daily_post_count(user_id, proposed_time.date())
        
        if daily_count >= max_posts:
            return RuleViolation(
                rule_name=rule.name,
                severity=RuleSeverity.ERROR,
                message=f"Daily posting limit ({max_posts}) would be exceeded (current: {daily_count})",
                blocking=True,
                suggestion="Consider scheduling for tomorrow"
            )
        
        return None
    
    async def _check_min_interval_rule(self, rule: SchedulingRule, user_id: str,
                                     proposed_time: Optional[datetime],
                                     preferences: SchedulingPreferences) -> Optional[RuleViolation]:
        """Check minimum interval rule"""
        if not proposed_time:
            return None
        
        min_interval = rule.conditions.get("min_minutes", preferences.min_interval_minutes)
        last_post_time = self.data_flow_manager.get_last_post_time(user_id)
        
        if last_post_time:
            time_diff = (proposed_time - last_post_time).total_seconds() / 60
            if time_diff < min_interval:
                remaining_minutes = int(min_interval - time_diff)
                return RuleViolation(
                    rule_name=rule.name,
                    severity=RuleSeverity.ERROR,
                    message=f"Minimum interval ({min_interval} minutes) not met. {remaining_minutes} minutes remaining.",
                    blocking=True,
                    suggestion=f"Schedule for {last_post_time + timedelta(minutes=min_interval)}"
                )
        
        return None
    
    async def _check_time_window_rule(self, rule: SchedulingRule, user_id: str,
                                    proposed_time: Optional[datetime],
                                    preferences: SchedulingPreferences) -> Optional[RuleViolation]:
        """Check time window restrictions (quiet hours)"""
        if not proposed_time:
            return None
        
        # Use rule-specific times or fall back to preferences
        start_time_str = rule.conditions.get("start_time", preferences.quiet_hours_start)
        end_time_str = rule.conditions.get("end_time", preferences.quiet_hours_end)
        
        if not start_time_str or not end_time_str:
            return None
        
        publish_time = proposed_time.time()
        start_time = datetime.strptime(start_time_str, "%H:%M").time()
        end_time = datetime.strptime(end_time_str, "%H:%M").time()
        
        # Handle overnight quiet hours (e.g., 22:00 to 08:00)
        if start_time > end_time:
            if publish_time >= start_time or publish_time <= end_time:
                return RuleViolation(
                    rule_name=rule.name,
                    severity=RuleSeverity.WARNING,
                    message=f"Posting during quiet hours ({start_time_str} - {end_time_str})",
                    blocking=rule.actions.get("type") == "block",
                    suggestion="Consider scheduling during active hours"
                )
        else:
            if start_time <= publish_time <= end_time:
                return RuleViolation(
                    rule_name=rule.name,
                    severity=RuleSeverity.WARNING,
                    message=f"Posting during quiet hours ({start_time_str} - {end_time_str})",
                    blocking=rule.actions.get("type") == "block",
                    suggestion="Consider scheduling during active hours"
                )
        
        return None
    
    async def _check_weekend_rule(self, rule: SchedulingRule, user_id: str,
                                proposed_time: Optional[datetime],
                                preferences: SchedulingPreferences) -> Optional[RuleViolation]:
        """Check weekend posting restrictions"""
        if not proposed_time:
            return None
        
        allow_weekends = rule.conditions.get("allow_weekends", not preferences.avoid_weekends)
        
        if not allow_weekends and proposed_time.weekday() >= 5:  # Saturday=5, Sunday=6
            return RuleViolation(
                rule_name=rule.name,
                severity=RuleSeverity.ERROR,
                message="Weekend posting is disabled",
                blocking=True,
                suggestion="Schedule for a weekday"
            )
        
        return None
    
    async def _check_duplicate_content_rule(self, rule: SchedulingRule, user_id: str,
                                          content_id: Optional[str]) -> Optional[RuleViolation]:
        """Check for duplicate content"""
        if not content_id:
            return None
        
        try:
            # Get content text
            content_draft = self.data_flow_manager.get_content_draft_by_id(content_id)
            if not content_draft:
                return None
            
            content_text = content_draft.current_content or content_draft.generated_text
            
            # Check for similar content in the past week
            check_period = rule.conditions.get("check_period_days", 7)
            similarity_threshold = rule.conditions.get("similarity_threshold", 0.8)
            
            # Simple similarity check (would be more sophisticated in production)
            recent_posts = self.data_flow_manager.get_recent_posts(user_id, check_period)
            
            for post in recent_posts:
                if self._calculate_similarity(content_text, post.content) > similarity_threshold:
                    return RuleViolation(
                        rule_name=rule.name,
                        severity=RuleSeverity.WARNING,
                        message="Similar content was posted recently",
                        blocking=False,
                        suggestion="Consider modifying the content to make it more unique"
                    )
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to check duplicate content: {e}")
            return None
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity calculation"""
        try:
            # Simple word-based similarity
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            return intersection / union if union > 0 else 0.0
            
        except Exception:
            return 0.0
    
    async def _get_user_preferences(self, user_id: str) -> SchedulingPreferences:
        """Get user scheduling preferences"""
        try:
            # Try to get from database
            prefs_data = self.data_flow_manager.get_user_scheduling_preferences(user_id)
            
            if prefs_data:
                return SchedulingPreferences(**prefs_data)
            else:
                # Return default preferences
                return SchedulingPreferences(founder_id=user_id)
                
        except Exception as e:
            logger.warning(f"Failed to get scheduling preferences: {e}")
            return SchedulingPreferences(founder_id=user_id)
    
    async def _get_user_rules(self, user_id: str) -> List[SchedulingRule]:
        """Get user-specific rules, falling back to defaults"""
        try:
            # Try to get user-specific rules from database
            user_rules = self.data_flow_manager.get_user_scheduling_rules(user_id)
            
            if user_rules:
                return [SchedulingRule(**rule) for rule in user_rules]
            else:
                # Return default rules
                return self.default_rules
                
        except Exception as e:
            logger.warning(f"Failed to get user rules: {e}")
            return self.default_rules
    
    async def _generate_optimal_times(self, user_id: str, preferences: SchedulingPreferences) -> List[datetime]:
        """Generate suggested optimal posting times"""
        try:
            suggested_times = []
            base_time = datetime.utcnow()
            
            # Generate suggestions for next 7 days
            for day_offset in range(7):
                day = base_time + timedelta(days=day_offset)
                
                # Skip weekends if configured
                if preferences.avoid_weekends and day.weekday() >= 5:
                    continue
                
                # Use preferred times if available
                if preferences.preferred_posting_times:
                    for time_str in preferences.preferred_posting_times:
                        time_obj = datetime.strptime(time_str, "%H:%M").time()
                        suggested_time = day.replace(
                            hour=time_obj.hour,
                            minute=time_obj.minute,
                            second=0,
                            microsecond=0
                        )
                        
                        # Only suggest future times
                        if suggested_time > base_time:
                            suggested_times.append(suggested_time)
                else:
                    # Default suggestions: 9 AM, 1 PM, 5 PM
                    for hour in [9, 13, 17]:
                        suggested_time = day.replace(hour=hour, minute=0, second=0, microsecond=0)
                        if suggested_time > base_time:
                            suggested_times.append(suggested_time)
            
            return suggested_times[:10]  # Return top 10 suggestions
            
        except Exception as e:
            logger.warning(f"Failed to generate optimal times: {e}")
            return []
    
    async def _find_next_available_slot(self, user_id: str, preferences: SchedulingPreferences) -> Optional[datetime]:
        """Find the next available publishing slot"""
        try:
            current_time = datetime.utcnow()
            
            # Start checking from next hour
            check_time = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            
            # Check next 48 hours
            for _ in range(48):
                # Create a mock rule check for this time
                temp_result = await self.validate_publishing_rules(
                    user_id=user_id,
                    proposed_time=check_time,
                    preferences=preferences
                )
                
                if temp_result.can_publish:
                    return check_time
                
                check_time += timedelta(hours=1)
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to find next available slot: {e}")
            return None
    
    # Rule management methods
    
    async def create_custom_rule(self, user_id: str, rule: SchedulingRule) -> bool:
        """Create a custom rule for a user"""
        try:
            rule_data = rule.dict()
            rule_data['user_id'] = user_id
            
            return self.data_flow_manager.create_user_scheduling_rule(rule_data)
            
        except Exception as e:
            logger.error(f"Failed to create custom rule: {e}")
            return False
    
    async def update_rule(self, user_id: str, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing rule"""
        try:
            return self.data_flow_manager.update_user_scheduling_rule(user_id, rule_id, updates)
            
        except Exception as e:
            logger.error(f"Failed to update rule: {e}")
            return False
    
    async def delete_rule(self, user_id: str, rule_id: str) -> bool:
        """Delete a user rule"""
        try:
            return self.data_flow_manager.delete_user_scheduling_rule(user_id, rule_id)
            
        except Exception as e:
            logger.error(f"Failed to delete rule: {e}")
            return False
    
    async def get_rule_violations_summary(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Get summary of rule violations for analytics"""
        try:
            violations_data = self.data_flow_manager.get_rule_violations_summary(user_id, days)
            
            return {
                'total_violations': violations_data.get('total_violations', 0),
                'violations_by_rule': violations_data.get('violations_by_rule', {}),
                'violations_by_severity': violations_data.get('violations_by_severity', {}),
                'most_common_violations': violations_data.get('most_common_violations', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to get violations summary: {e}")
            return {
                'total_violations': 0,
                'violations_by_rule': {},
                'violations_by_severity': {},
                'most_common_violations': []
            } 