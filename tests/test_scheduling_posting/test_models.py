"""Unit tests for scheduling_posting models"""
import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from modules.scheduling_posting.models import (
    PublishStatus, ScheduleFrequency, PublishingRule,
    TimeZoneInfo, SchedulingPreferences, PublishingError,
    ScheduledContent, ScheduleRequest, BatchScheduleRequest,
    PublishRequest, BatchPublishRequest, StatusUpdateRequest,
    PublishingHistoryItem, PublishingAnalytics, RuleCheckRequest,
    RuleCheckResult, SchedulingQueueInfo, AutoScheduleSettings,
    PublishingConfiguration, PublishingMetrics, SchedulingRule,
    ContentQueueItem, ScheduleResponse, PublishResponse, BatchOperationResponse
)


class TestModels:
    """Test cases for data models"""

    def test_publish_status_enum(self):
        """测试发布状态枚举"""
        assert PublishStatus.PENDING == "pending"
        assert PublishStatus.SCHEDULED == "scheduled"
        assert PublishStatus.POSTED == "posted"
        assert PublishStatus.FAILED == "failed"
        assert PublishStatus.CANCELLED == "cancelled"

    def test_schedule_frequency_enum(self):
        """测试调度频率枚举"""
        assert ScheduleFrequency.IMMEDIATE == "immediate"
        assert ScheduleFrequency.DAILY == "daily"
        assert ScheduleFrequency.WEEKLY == "weekly"

    def test_publishing_rule_enum(self):
        """测试发布规则枚举"""
        assert PublishingRule.TIME_WINDOW == "time_window"
        assert PublishingRule.FREQUENCY_LIMIT == "frequency_limit"
        assert PublishingRule.CONTENT_SPACING == "content_spacing"

    def test_timezone_info_model(self):
        """测试时区信息模型"""
        tz_info = TimeZoneInfo(
            timezone="America/New_York",
            offset_hours=-5,
            dst_active=True
        )
        
        assert tz_info.timezone == "America/New_York"
        assert tz_info.offset_hours == -5
        assert tz_info.dst_active is True

    def test_timezone_info_defaults(self):
        """测试时区信息默认值"""
        tz_info = TimeZoneInfo()
        
        assert tz_info.timezone == "UTC"
        assert tz_info.offset_hours == 0
        assert tz_info.dst_active is False

    def test_scheduling_preferences_model(self):
        """测试调度偏好模型"""
        preferences = SchedulingPreferences(
            founder_id="test_user_123",
            default_timezone="America/New_York",
            auto_schedule_enabled=True,
            preferred_posting_times=["09:00", "13:00", "17:00"],
            max_posts_per_day=10,
            min_interval_minutes=30,
            avoid_weekends=True,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00"
        )
        
        assert preferences.founder_id == "test_user_123"
        assert preferences.auto_schedule_enabled is True
        assert len(preferences.preferred_posting_times) == 3
        assert preferences.max_posts_per_day == 10

    def test_scheduling_preferences_defaults(self):
        """测试调度偏好默认值"""
        preferences = SchedulingPreferences(founder_id="test_user")
        
        assert preferences.default_timezone == "UTC"
        assert preferences.auto_schedule_enabled is False
        assert preferences.max_posts_per_day == 5
        assert preferences.min_interval_minutes == 60

    def test_publishing_error_model(self):
        """测试发布错误模型"""
        error = PublishingError(
            error_code="TWITTER_API_ERROR",
            error_message="Rate limit exceeded",
            retry_count=2,
            last_retry_at=datetime.utcnow(),
            is_retryable=True,
            technical_details={"status_code": 429}
        )
        
        assert error.error_code == "TWITTER_API_ERROR"
        assert error.retry_count == 2
        assert error.is_retryable is True
        assert "status_code" in error.technical_details

    def test_scheduled_content_model(self):
        """测试预定内容模型"""
        scheduled_time = datetime.utcnow() + timedelta(hours=1)
        
        content = ScheduledContent(
            content_draft_id="draft_123",
            founder_id="user_456",
            scheduled_time=scheduled_time,
            created_by="user_456",
            priority=3,
            tags=["urgent", "marketing"]
        )
        
        assert content.content_draft_id == "draft_123"
        assert content.founder_id == "user_456"
        assert content.scheduled_time == scheduled_time
        assert content.status == PublishStatus.SCHEDULED
        assert content.priority == 3
        assert len(content.tags) == 2

    def test_scheduled_content_defaults(self):
        """测试预定内容默认值"""
        scheduled_time = datetime.utcnow() + timedelta(hours=1)
        
        content = ScheduledContent(
            content_draft_id="draft_123",
            founder_id="user_456",
            scheduled_time=scheduled_time,
            created_by="user_456"
        )
        
        assert content.status == PublishStatus.SCHEDULED
        assert content.platform == "twitter"
        assert content.retry_count == 0
        assert content.max_retries == 3
        assert content.priority == 5

    def test_schedule_request_validation(self):
        """测试调度请求验证"""
        future_time = datetime.utcnow() + timedelta(hours=1)
        
        request = ScheduleRequest(
            content_id="content_123",
            scheduled_time=future_time,
            timezone="UTC",
            priority=7
        )
        
        assert request.content_id == "content_123"
        assert request.priority == 7

    def test_schedule_request_past_time_validation(self):
        """测试调度请求过去时间验证"""
        past_time = datetime.utcnow() - timedelta(hours=1)
        
        with pytest.raises(ValidationError, match="must be in the future"):
            ScheduleRequest(
                content_id="content_123",
                scheduled_time=past_time
            )

    def test_schedule_request_priority_validation(self):
        """测试调度请求优先级验证"""
        future_time = datetime.utcnow() + timedelta(hours=1)
        
        # 测试无效优先级
        with pytest.raises(ValidationError):
            ScheduleRequest(
                content_id="content_123",
                scheduled_time=future_time,
                priority=15  # 超出范围 1-10
            )

    def test_batch_schedule_request_validation(self):
        """测试批量调度请求验证"""
        content_ids = [f"content_{i}" for i in range(10)]
        
        request = BatchScheduleRequest(
            content_ids=content_ids,
            schedule_time=datetime.utcnow() + timedelta(hours=1),
            stagger_minutes=5
        )
        
        assert len(request.content_ids) == 10
        assert request.stagger_minutes == 5

    def test_batch_schedule_request_size_validation(self):
        """测试批量调度请求大小验证"""
        # 创建超过限制的内容ID列表
        content_ids = [f"content_{i}" for i in range(60)]
        
        with pytest.raises(ValidationError, match="cannot exceed 50"):
            BatchScheduleRequest(content_ids=content_ids)

    def test_publish_request_model(self):
        """测试发布请求模型"""
        request = PublishRequest(
            content_id="content_123",
            force_publish=True,
            skip_rules_check=True,
            custom_message="Custom tweet message"
        )
        
        assert request.content_id == "content_123"
        assert request.force_publish is True
        assert request.skip_rules_check is True
        assert request.custom_message == "Custom tweet message"

    def test_batch_publish_request_model(self):
        """测试批量发布请求模型"""
        content_ids = ["content_1", "content_2", "content_3"]
        
        request = BatchPublishRequest(
            content_ids=content_ids,
            schedule_time=datetime.utcnow() + timedelta(hours=1),
            force_publish=True,
            stagger_minutes=2
        )
        
        assert len(request.content_ids) == 3
        assert request.force_publish is True
        assert request.stagger_minutes == 2

    def test_status_update_request_model(self):
        """测试状态更新请求模型"""
        request = StatusUpdateRequest(
            status=PublishStatus.POSTED,
            posted_tweet_id="1234567890",
            error_message=None,
            error_code=None,
            technical_details={"duration": 1.5},
            retry_scheduled=False
        )
        
        assert request.status == PublishStatus.POSTED
        assert request.posted_tweet_id == "1234567890"
        assert request.retry_scheduled is False

    def test_publishing_history_item_model(self):
        """测试发布历史项模型"""
        scheduled_time = datetime.utcnow() - timedelta(hours=2)
        posted_time = datetime.utcnow() - timedelta(hours=1)
        
        history_item = PublishingHistoryItem(
            content_id="content_123",
            scheduled_content_id="scheduled_456",
            content_preview="This is a test tweet...",
            scheduled_time=scheduled_time,
            posted_at=posted_time,
            status=PublishStatus.POSTED,
            posted_tweet_id="1234567890",
            platform="twitter",
            retry_count=1,
            tags=["test", "automation"]
        )
        
        assert history_item.content_id == "content_123"
        assert history_item.status == PublishStatus.POSTED
        assert history_item.retry_count == 1
        assert len(history_item.tags) == 2

    def test_publishing_analytics_model(self):
        """测试发布分析模型"""
        analytics = PublishingAnalytics(
            total_scheduled=100,
            total_published=85,
            total_failed=15,
            success_rate=85.0,
            avg_publish_delay_minutes=2.5,
            most_common_errors=["RATE_LIMIT", "NETWORK_ERROR"],
            publishing_times_distribution={"09": 20, "13": 25, "17": 30},
            platform_breakdown={"twitter": 85}
        )
        
        assert analytics.total_scheduled == 100
        assert analytics.success_rate == 85.0
        assert len(analytics.most_common_errors) == 2

    def test_rule_check_request_model(self):
        """测试规则检查请求模型"""
        request = RuleCheckRequest(
            user_id="user_123",
            content_type="twitter_post",
            proposed_time=datetime.utcnow() + timedelta(hours=1),
            content_id="content_456"
        )
        
        assert request.user_id == "user_123"
        assert request.content_type == "twitter_post"
        assert request.content_id == "content_456"

    def test_rule_check_result_model(self):
        """测试规则检查结果模型"""
        result = RuleCheckResult(
            can_publish=False,
            violations=["Daily limit exceeded", "Too soon after last post"],
            recommendations=["Wait 30 minutes", "Schedule for tomorrow"],
            suggested_times=[datetime.utcnow() + timedelta(hours=1)],
            next_available_slot=datetime.utcnow() + timedelta(minutes=30),
            current_daily_count=5,
            daily_limit=5
        )
        
        assert result.can_publish is False
        assert len(result.violations) == 2
        assert len(result.recommendations) == 2
        assert result.current_daily_count == 5

    def test_scheduling_queue_info_model(self):
        """测试调度队列信息模型"""
        queue_info = SchedulingQueueInfo(
            total_pending=25,
            total_scheduled=50,
            next_publish_time=datetime.utcnow() + timedelta(minutes=30),
            queue_by_status={
                "pending": 25,
                "scheduled": 50,
                "retry_pending": 5
            },
            upcoming_24h=30,
            overdue_count=2,
            retry_queue_size=5
        )
        
        assert queue_info.total_pending == 25
        assert queue_info.total_scheduled == 50
        assert queue_info.upcoming_24h == 30
        assert queue_info.overdue_count == 2

    def test_auto_schedule_settings_model(self):
        """测试自动调度设置模型"""
        settings = AutoScheduleSettings(
            enabled=True,
            frequency=ScheduleFrequency.DAILY,
            preferred_times=["09:00", "13:00", "17:00"],
            content_types=["twitter_post", "linkedin_post"],
            min_quality_score=0.8,
            max_daily_posts=5,
            respect_quiet_hours=True,
            stagger_minutes=60
        )
        
        assert settings.enabled is True
        assert settings.frequency == ScheduleFrequency.DAILY
        assert len(settings.preferred_times) == 3
        assert settings.min_quality_score == 0.8

    def test_publishing_configuration_model(self):
        """测试发布配置模型"""
        config = PublishingConfiguration(
            max_concurrent_publishes=10,
            retry_delays_minutes=[5, 15, 60, 240],
            default_max_retries=4,
            publish_timeout_seconds=45,
            queue_check_interval_seconds=30,
            enable_rule_validation=True,
            enable_analytics_tracking=True,
            platform_configs={
                "twitter": {"rate_limit": 300},
                "linkedin": {"rate_limit": 100}
            }
        )
        
        assert config.max_concurrent_publishes == 10
        assert len(config.retry_delays_minutes) == 4
        assert config.enable_rule_validation is True
        assert "twitter" in config.platform_configs

    def test_publishing_metrics_model(self):
        """测试发布指标模型"""
        metrics = PublishingMetrics(
            queue_size=15,
            publishing_rate_per_hour=12.5,
            success_rate_24h=95.2,
            avg_processing_time_seconds=2.8,
            active_publishers=3,
            last_successful_publish=datetime.utcnow() - timedelta(minutes=10),
            last_failed_publish=datetime.utcnow() - timedelta(hours=2),
            error_rate_24h=4.8
        )
        
        assert metrics.queue_size == 15
        assert metrics.success_rate_24h == 95.2
        assert metrics.active_publishers == 3

    def test_scheduling_rule_model(self):
        """测试调度规则模型"""
        rule = SchedulingRule(
            name="Daily Posting Limit",
            rule_type=PublishingRule.FREQUENCY_LIMIT,
            enabled=True,
            priority=1,
            conditions={
                "max_posts_per_day": 5,
                "reset_time": "00:00"
            },
            actions={
                "type": "block",
                "message": "Daily limit exceeded"
            }
        )
        
        assert rule.name == "Daily Posting Limit"
        assert rule.rule_type == PublishingRule.FREQUENCY_LIMIT
        assert rule.enabled is True
        assert rule.priority == 1
        assert "max_posts_per_day" in rule.conditions

    def test_content_queue_item_model(self):
        """测试内容队列项模型"""
        scheduled_time = datetime.utcnow() + timedelta(minutes=30)
        
        queue_item = ContentQueueItem(
            content_draft_id="draft_123",
            founder_id="user_456",
            scheduled_time=scheduled_time,
            priority=3,
            status=PublishStatus.PENDING,
            platform="twitter",
            retry_count=1
        )
        
        assert queue_item.content_draft_id == "draft_123"
        assert queue_item.priority == 3
        assert queue_item.retry_count == 1

    def test_content_queue_item_properties(self):
        """测试内容队列项属性"""
        # 测试过期的项目
        past_time = datetime.utcnow() - timedelta(minutes=10)
        overdue_item = ContentQueueItem(
            content_draft_id="draft_123",
            founder_id="user_456",
            scheduled_time=past_time
        )
        
        assert overdue_item.is_due is True
        assert overdue_item.is_overdue is True
        
        # 测试未来的项目
        future_time = datetime.utcnow() + timedelta(hours=1)
        future_item = ContentQueueItem(
            content_draft_id="draft_456",
            founder_id="user_789",
            scheduled_time=future_time
        )
        
        assert future_item.is_due is False
        assert future_item.is_overdue is False

    def test_content_queue_item_should_retry(self):
        """测试内容队列项重试判断"""
        failed_item = ContentQueueItem(
            content_draft_id="draft_123",
            founder_id="user_456",
            scheduled_time=datetime.utcnow(),
            status=PublishStatus.FAILED,
            retry_count=2,
            last_attempt_at=datetime.utcnow() - timedelta(minutes=10)
        )
        
        assert failed_item.should_retry is True
        
        # 测试超过重试次数的项目
        max_retry_item = ContentQueueItem(
            content_draft_id="draft_456",
            founder_id="user_789",
            scheduled_time=datetime.utcnow(),
            status=PublishStatus.FAILED,
            retry_count=5  # 超过默认最大重试次数
        )
        
        assert max_retry_item.should_retry is False

    def test_schedule_response_model(self):
        """测试调度响应模型"""
        response = ScheduleResponse(
            success=True,
            scheduled_content_id="scheduled_123",
            scheduled_time=datetime.utcnow() + timedelta(hours=1),
            message="Content scheduled successfully",
            rule_violations=[]
        )
        
        assert response.success is True
        assert response.scheduled_content_id == "scheduled_123"
        assert len(response.rule_violations) == 0

    def test_publish_response_model(self):
        """测试发布响应模型"""
        response = PublishResponse(
            success=True,
            posted_tweet_id="1234567890",
            posted_at=datetime.utcnow(),
            message="Content published successfully",
            error_code=None
        )
        
        assert response.success is True
        assert response.posted_tweet_id == "1234567890"
        assert response.error_code is None

    def test_batch_operation_response_model(self):
        """测试批量操作响应模型"""
        results = {
            "content_1": ScheduleResponse(success=True, message="Success"),
            "content_2": ScheduleResponse(success=False, message="Failed")
        }
        
        batch_response = BatchOperationResponse(
            total_items=2,
            successful_items=1,
            failed_items=1,
            results=results,
            message="Batch operation completed"
        )
        
        assert batch_response.total_items == 2
        assert batch_response.successful_items == 1
        assert batch_response.failed_items == 1
        assert len(batch_response.results) == 2

    def test_model_serialization(self):
        """测试模型序列化"""
        preferences = SchedulingPreferences(
            founder_id="test_user",
            preferred_posting_times=["09:00", "13:00"]
        )
        
        # 测试转换为字典
        prefs_dict = preferences.dict()
        assert isinstance(prefs_dict, dict)
        assert prefs_dict["founder_id"] == "test_user"
        assert isinstance(prefs_dict["preferred_posting_times"], list)
        
        # 测试JSON序列化
        prefs_json = preferences.json()
        assert isinstance(prefs_json, str)
        assert "test_user" in prefs_json

    def test_model_validation_edge_cases(self):
        """测试模型验证边界情况"""
        # 测试空字符串 - SchedulingPreferences的founder_id不能为空
        with pytest.raises(ValidationError):
            SchedulingPreferences(founder_id="")  # 空字符串应该被拒绝
        
        # 测试负数优先级 - 应该被拒绝，因为有ge=1的约束
        with pytest.raises(ValidationError):
            ScheduleRequest(
                content_id="test",
                scheduled_time=datetime.utcnow() + timedelta(hours=1),
                priority=-1  # 负数应该被拒绝
            )

    def test_datetime_handling(self):
        """测试日期时间处理"""
        now = datetime.utcnow()
        future_time = now + timedelta(hours=1)
        
        content = ScheduledContent(
            content_draft_id="draft_123",
            founder_id="user_456",
            scheduled_time=future_time,
            created_by="user_456"
        )
        
        # 验证时间字段正确设置
        assert content.scheduled_time == future_time
        assert content.created_at is not None
        assert content.updated_at is not None
        assert content.created_at <= now + timedelta(seconds=1)  # 允许小量时间差

    def test_optional_fields_handling(self):
        """测试可选字段处理"""
        # 测试最小必需字段
        minimal_content = ScheduledContent(
            content_draft_id="draft_123",
            founder_id="user_456",
            scheduled_time=datetime.utcnow() + timedelta(hours=1),
            created_by="user_456"
        )
        
        # 验证可选字段的默认值
        assert minimal_content.posted_at is None
        assert minimal_content.posted_tweet_id is None
        assert minimal_content.error_info is None
        assert len(minimal_content.tags) == 0 