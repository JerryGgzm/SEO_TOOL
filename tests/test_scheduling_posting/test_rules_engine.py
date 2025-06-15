"""Unit tests for InternalRulesEngine"""
import pytest
from datetime import datetime, timedelta, time
from unittest.mock import Mock

from modules.scheduling_posting.rules_engine import (
    InternalRulesEngine, RuleSeverity, RuleViolation
)
from modules.scheduling_posting.models import (
    SchedulingRule, PublishingRule, SchedulingPreferences, PublishStatus
)


class TestInternalRulesEngine:
    """Test cases for InternalRulesEngine"""

    @pytest.mark.asyncio
    async def test_validate_publishing_rules_success(self, rules_engine, test_user_id):
        """测试成功验证发布规则"""
        proposed_time = datetime.utcnow() + timedelta(hours=2)
        
        result = await rules_engine.validate_publishing_rules(
            test_user_id, 
            content_id="test_content",
            proposed_time=proposed_time
        )
        
        assert hasattr(result, 'can_publish')
        assert hasattr(result, 'violations')
        assert hasattr(result, 'recommendations')
        assert hasattr(result, 'suggested_times')

    @pytest.mark.asyncio
    async def test_daily_limit_rule_violation(self, rules_engine, mock_data_flow_manager, test_user_id):
        """测试每日限制规则违反"""
        # 设置用户已发布5篇，达到每日限制
        mock_data_flow_manager.get_daily_post_count = Mock(return_value=5)
        
        # 设置用户偏好
        preferences = SchedulingPreferences(
            founder_id=test_user_id,
            max_posts_per_day=5
        )
        mock_data_flow_manager.user_preferences[test_user_id] = preferences.dict()
        
        proposed_time = datetime.utcnow() + timedelta(hours=1)
        
        result = await rules_engine.validate_publishing_rules(
            test_user_id,
            proposed_time=proposed_time,
            preferences=preferences
        )
        
        # 应该被阻止发布
        assert result.can_publish is False
        assert any("Daily posting limit" in violation for violation in result.violations)

    @pytest.mark.asyncio
    async def test_minimum_interval_rule_violation(self, rules_engine, mock_data_flow_manager, test_user_id):
        """测试最小间隔规则违反"""
        # 设置最近发布时间为30分钟前
        last_post_time = datetime.utcnow() - timedelta(minutes=30)
        mock_data_flow_manager.get_last_post_time = Mock(return_value=last_post_time)
        
        # 设置最小间隔为60分钟
        preferences = SchedulingPreferences(
            founder_id=test_user_id,
            min_interval_minutes=60
        )
        
        proposed_time = datetime.utcnow() + timedelta(minutes=5)
        
        result = await rules_engine.validate_publishing_rules(
            test_user_id,
            proposed_time=proposed_time,
            preferences=preferences
        )
        
        # 应该被阻止发布
        assert result.can_publish is False
        assert any("Minimum interval" in violation for violation in result.violations)

    @pytest.mark.asyncio
    async def test_quiet_hours_rule_warning(self, rules_engine, test_user_id):
        """测试安静时间规则警告"""
        # 设置在安静时间内发布（晚上11点）
        proposed_time = datetime.utcnow().replace(hour=23, minute=0)
        
        preferences = SchedulingPreferences(
            founder_id=test_user_id,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00"
        )
        
        result = await rules_engine.validate_publishing_rules(
            test_user_id,
            proposed_time=proposed_time,
            preferences=preferences
        )
        
        # 应该允许发布但有警告
        assert result.can_publish is True
        assert any("quiet hours" in violation.lower() for violation in result.violations)

    @pytest.mark.asyncio
    async def test_weekend_restriction_rule(self, rules_engine, test_user_id):
        """测试周末限制规则"""
        # 设置为周六发布
        saturday = datetime.utcnow()
        while saturday.weekday() != 5:  # 5 = Saturday
            saturday += timedelta(days=1)
        
        preferences = SchedulingPreferences(
            founder_id=test_user_id,
            avoid_weekends=True
        )
        
        result = await rules_engine.validate_publishing_rules(
            test_user_id,
            proposed_time=saturday,
            preferences=preferences
        )
        
        # 根据规则设置，可能被阻止或警告
        assert hasattr(result, 'can_publish')

    @pytest.mark.asyncio
    async def test_duplicate_content_rule(self, rules_engine, mock_data_flow_manager, test_user_id):
        """测试重复内容规则"""
        # 模拟最近的帖子
        recent_post = Mock()
        recent_post.content = "This is test content"
        mock_data_flow_manager.get_recent_posts = Mock(return_value=[recent_post])
        
        # 模拟内容草稿
        content_draft = Mock()
        content_draft.current_content = "This is test content"  # 相同内容
        content_draft.generated_text = None
        mock_data_flow_manager.get_content_draft_by_id = Mock(return_value=content_draft)
        
        result = await rules_engine.validate_publishing_rules(
            test_user_id,
            content_id="test_content"
        )
        
        # 应该有重复内容警告
        assert any("Similar content" in violation for violation in result.violations)

    @pytest.mark.asyncio
    async def test_create_custom_rule(self, rules_engine, test_user_id):
        """测试创建自定义规则"""
        custom_rule = SchedulingRule(
            name="Test Custom Rule",
            rule_type=PublishingRule.TIME_WINDOW,
            enabled=True,
            priority=1,
            conditions={"test": "condition"},
            actions={"test": "action"}
        )
        
        result = await rules_engine.create_custom_rule(test_user_id, custom_rule)
        
        # 应该成功创建（在mock中）
        assert result is True

    @pytest.mark.asyncio
    async def test_update_rule(self, rules_engine, test_user_id):
        """测试更新规则"""
        rule_id = "test_rule_123"
        updates = {"enabled": False, "priority": 10}
        
        result = await rules_engine.update_rule(test_user_id, rule_id, updates)
        
        # Mock应该返回成功
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_rule(self, rules_engine, test_user_id):
        """测试删除规则"""
        rule_id = "test_rule_123"
        
        result = await rules_engine.delete_rule(test_user_id, rule_id)
        
        # Mock应该返回成功
        assert result is True

    @pytest.mark.asyncio
    async def test_generate_optimal_times(self, rules_engine, test_user_id):
        """测试生成最佳时间"""
        preferences = SchedulingPreferences(
            founder_id=test_user_id,
            preferred_posting_times=["09:00", "13:00", "17:00"],
            avoid_weekends=False
        )
        
        optimal_times = await rules_engine._generate_optimal_times(test_user_id, preferences)
        
        assert isinstance(optimal_times, list)
        assert len(optimal_times) <= 10  # 最多返回10个建议

    @pytest.mark.asyncio
    async def test_find_next_available_slot(self, rules_engine, test_user_id):
        """测试找到下一个可用时段"""
        preferences = SchedulingPreferences(
            founder_id=test_user_id,
            max_posts_per_day=5,
            min_interval_minutes=60
        )
        
        next_slot = await rules_engine._find_next_available_slot(test_user_id, preferences)
        
        # 应该返回一个未来时间或None
        if next_slot:
            assert next_slot > datetime.utcnow()

    @pytest.mark.asyncio
    async def test_rule_violations_summary(self, rules_engine, test_user_id):
        """测试规则违反摘要"""
        summary = await rules_engine.get_rule_violations_summary(test_user_id, days=7)
        
        assert isinstance(summary, dict)
        assert 'total_violations' in summary
        assert 'violations_by_rule' in summary
        assert 'violations_by_severity' in summary

    def test_calculate_similarity(self, rules_engine):
        """测试文本相似度计算"""
        text1 = "This is a test message"
        text2 = "This is a test message"
        text3 = "Completely different content"
        
        # 完全相同的文本
        similarity1 = rules_engine._calculate_similarity(text1, text2)
        assert similarity1 == 1.0
        
        # 完全不同的文本
        similarity2 = rules_engine._calculate_similarity(text1, text3)
        assert similarity2 < 1.0
        
        # 部分相似的文本
        text4 = "This is another test message"
        similarity3 = rules_engine._calculate_similarity(text1, text4)
        assert 0 < similarity3 < 1.0

    def test_rule_violation_object(self):
        """测试规则违反对象"""
        violation = RuleViolation(
            rule_name="Test Rule",
            severity=RuleSeverity.ERROR,
            message="Test violation",
            blocking=True,
            suggestion="Test suggestion"
        )
        
        assert violation.rule_name == "Test Rule"
        assert violation.severity == RuleSeverity.ERROR
        assert violation.message == "Test violation"
        assert violation.blocking is True
        assert violation.suggestion == "Test suggestion"

    @pytest.mark.asyncio
    async def test_check_daily_limit_rule_no_violation(self, rules_engine, mock_data_flow_manager, test_user_id):
        """测试每日限制规则无违反"""
        # 设置当前发布数为2，限制为5
        mock_data_flow_manager.get_daily_post_count = Mock(return_value=2)
        
        rule = SchedulingRule(
            name="Daily Limit",
            rule_type=PublishingRule.FREQUENCY_LIMIT,
            conditions={"type": "daily_limit", "max_posts_per_day": 5},
            actions={"type": "block"}
        )
        
        preferences = SchedulingPreferences(founder_id=test_user_id, max_posts_per_day=5)
        proposed_time = datetime.utcnow() + timedelta(hours=1)
        
        violation = await rules_engine._check_daily_limit_rule(
            rule, test_user_id, proposed_time, preferences
        )
        
        assert violation is None

    @pytest.mark.asyncio
    async def test_check_min_interval_rule_no_violation(self, rules_engine, mock_data_flow_manager, test_user_id):
        """测试最小间隔规则无违反"""
        # 设置最后发布时间为2小时前
        last_post_time = datetime.utcnow() - timedelta(hours=2)
        mock_data_flow_manager.get_last_post_time = Mock(return_value=last_post_time)
        
        rule = SchedulingRule(
            name="Min Interval",
            rule_type=PublishingRule.CONTENT_SPACING,
            conditions={"type": "min_interval", "min_minutes": 60},
            actions={"type": "block"}
        )
        
        preferences = SchedulingPreferences(founder_id=test_user_id, min_interval_minutes=60)
        proposed_time = datetime.utcnow() + timedelta(minutes=5)
        
        violation = await rules_engine._check_min_interval_rule(
            rule, test_user_id, proposed_time, preferences
        )
        
        assert violation is None

    @pytest.mark.asyncio
    async def test_check_time_window_rule_overnight_quiet_hours(self, rules_engine, test_user_id):
        """测试跨夜安静时间规则"""
        # 设置安静时间为22:00-08:00，测试凌晨2点
        proposed_time = datetime.utcnow().replace(hour=2, minute=0, second=0)
        
        rule = SchedulingRule(
            name="Quiet Hours",
            rule_type=PublishingRule.TIME_WINDOW,
            conditions={"type": "time_window", "start_time": "22:00", "end_time": "08:00"},
            actions={"type": "warn"}
        )
        
        preferences = SchedulingPreferences(
            founder_id=test_user_id,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00"
        )
        
        violation = await rules_engine._check_time_window_rule(
            rule, test_user_id, proposed_time, preferences
        )
        
        # 应该有违反（在安静时间内）
        assert violation is not None
        assert "quiet hours" in violation.message

    @pytest.mark.asyncio
    async def test_check_weekend_rule_weekday(self, rules_engine, test_user_id):
        """测试周末规则在工作日"""
        # 确保是工作日
        weekday = datetime.utcnow()
        while weekday.weekday() >= 5:  # 0-4 是工作日
            weekday += timedelta(days=1)
        
        rule = SchedulingRule(
            name="Weekend Rule",
            rule_type=PublishingRule.TIME_WINDOW,
            conditions={"type": "weekend_restriction", "allow_weekends": False},
            actions={"type": "block"}
        )
        
        preferences = SchedulingPreferences(founder_id=test_user_id, avoid_weekends=True)
        
        violation = await rules_engine._check_weekend_rule(
            rule, test_user_id, weekday, preferences
        )
        
        # 工作日不应该有违反
        assert violation is None

    @pytest.mark.asyncio
    async def test_error_handling_in_rule_validation(self, rules_engine, test_user_id):
        """测试规则验证中的错误处理"""
        # 测试无效的content_id
        result = await rules_engine.validate_publishing_rules(
            test_user_id,
            content_id="invalid_content_id"
        )
        
        # 应该返回结果而不是抛出异常
        assert hasattr(result, 'can_publish')
        assert isinstance(result.violations, list)

    @pytest.mark.asyncio
    async def test_user_specific_rules_fallback_to_defaults(self, rules_engine, mock_data_flow_manager, test_user_id):
        """测试用户特定规则回退到默认规则"""
        # Mock返回空的用户规则
        mock_data_flow_manager.get_user_scheduling_rules = Mock(return_value=[])
        
        user_rules = await rules_engine._get_user_rules(test_user_id)
        
        # 应该返回默认规则
        assert len(user_rules) > 0
        assert all(hasattr(rule, 'name') for rule in user_rules)

    @pytest.mark.asyncio
    async def test_preferences_fallback_to_defaults(self, rules_engine, mock_data_flow_manager, test_user_id):
        """测试偏好设置回退到默认值"""
        # Mock返回空的用户偏好
        mock_data_flow_manager.get_user_scheduling_preferences = Mock(return_value=None)
        
        preferences = await rules_engine._get_user_preferences(test_user_id)
        
        # 应该返回默认偏好设置
        assert preferences.founder_id == test_user_id
        assert hasattr(preferences, 'max_posts_per_day')
        assert hasattr(preferences, 'min_interval_minutes')

    @pytest.mark.asyncio
    async def test_comprehensive_rule_check_with_multiple_violations(self, rules_engine, 
                                                                   mock_data_flow_manager, test_user_id):
        """测试多个规则违反的综合检查"""
        # 设置多个违反条件
        mock_data_flow_manager.get_daily_post_count = Mock(return_value=5)  # 达到每日限制
        mock_data_flow_manager.get_last_post_time = Mock(return_value=datetime.utcnow() - timedelta(minutes=30))  # 间隔太短
        
        preferences = SchedulingPreferences(
            founder_id=test_user_id,
            max_posts_per_day=5,
            min_interval_minutes=60,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00"
        )
        
        # 在安静时间发布
        quiet_time = datetime.utcnow().replace(hour=23, minute=0)
        
        result = await rules_engine.validate_publishing_rules(
            test_user_id,
            proposed_time=quiet_time,
            preferences=preferences
        )
        
        # 应该有多个违反
        assert len(result.violations) > 1
        assert result.can_publish is False 