"""Unit tests for SchedulingPostingService"""
import pytest
from datetime import datetime, timedelta
import asyncio
from unittest.mock import AsyncMock, patch

from modules.scheduling_posting import (
    SchedulingPostingService, ScheduleRequest, PublishRequest,
    BatchScheduleRequest, BatchPublishRequest, StatusUpdateRequest,
    PublishStatus, ScheduleResponse, PublishResponse, BatchOperationResponse
)
from modules.twitter_api import TwitterAPIError

from .conftest import create_content_drafts, create_scheduled_content


class TestSchedulingService:
    """Test cases for SchedulingPostingService"""

    @pytest.mark.asyncio
    async def test_get_pending_content_success(self, scheduling_service, setup_test_data, test_user_id):
        """测试获取待发布内容成功"""
        # 创建多个内容草稿
        drafts = create_content_drafts(setup_test_data, test_user_id, 3)
        
        # 获取待发布内容
        pending_content = await scheduling_service.get_pending_content(test_user_id)
        
        assert len(pending_content) == 3
        assert all(item['status'] == 'approved' for item in pending_content)
        assert all(item['content_text'] is not None for item in pending_content)

    @pytest.mark.asyncio
    async def test_get_pending_content_with_filters(self, scheduling_service, setup_test_data, test_user_id):
        """测试带过滤器获取待发布内容"""
        # 创建不同状态的内容
        drafts = create_content_drafts(setup_test_data, test_user_id, 2)
        drafts[0].status = 'scheduled'
        
        # 仅获取已调度的内容
        pending_content = await scheduling_service.get_pending_content(
            test_user_id, status='scheduled', limit=10
        )
        
        assert len(pending_content) == 1
        assert pending_content[0]['status'] == 'scheduled'

    @pytest.mark.asyncio
    async def test_schedule_content_success(self, scheduling_service, setup_test_data, 
                                          test_user_id, valid_schedule_request):
        """测试成功调度内容"""
        result = await scheduling_service.schedule_content(test_user_id, valid_schedule_request)
        
        assert result.success is True
        assert result.scheduled_content_id is not None
        assert result.scheduled_time == valid_schedule_request.scheduled_time
        assert "successfully" in result.message

    @pytest.mark.asyncio
    async def test_schedule_content_invalid_content(self, scheduling_service, test_user_id):
        """测试调度不存在的内容"""
        invalid_request = ScheduleRequest(
            content_id="nonexistent_content",
            scheduled_time=datetime.utcnow() + timedelta(hours=1)
        )
        
        result = await scheduling_service.schedule_content(test_user_id, invalid_request)
        
        assert result.success is False
        assert "not found" in result.message

    @pytest.mark.asyncio
    async def test_schedule_content_wrong_status(self, scheduling_service, setup_test_data,
                                               test_user_id, test_content_draft):
        """测试调度错误状态的内容"""
        # 设置内容状态为非approved
        test_content_draft.status = 'draft'
        
        schedule_request = ScheduleRequest(
            content_id=test_content_draft.id,
            scheduled_time=datetime.utcnow() + timedelta(hours=1)
        )
        
        result = await scheduling_service.schedule_content(test_user_id, schedule_request)
        
        assert result.success is False
        assert "not valid for scheduling" in result.message

    @pytest.mark.asyncio
    async def test_schedule_content_past_time(self, scheduling_service, test_user_id, test_content_id):
        """测试调度过去的时间"""
        past_request = ScheduleRequest(
            content_id=test_content_id,
            scheduled_time=datetime.utcnow() - timedelta(hours=1)  # 过去时间
        )
        
        with pytest.raises(ValueError, match="must be in the future"):
            await scheduling_service.schedule_content(test_user_id, past_request)

    @pytest.mark.asyncio
    async def test_cancel_scheduled_content_success(self, scheduling_service, setup_test_data,
                                                  test_user_id, test_content_id):
        """测试成功取消已调度内容"""
        # 创建调度内容
        create_scheduled_content(setup_test_data, test_user_id, test_content_id)
        
        result = await scheduling_service.cancel_scheduled_content(test_user_id, test_content_id)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_cancel_scheduled_content_not_found(self, scheduling_service, test_user_id):
        """测试取消不存在的调度内容"""
        result = await scheduling_service.cancel_scheduled_content(test_user_id, "nonexistent")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_batch_schedule_content_success(self, scheduling_service, setup_test_data, test_user_id):
        """测试批量调度内容成功"""
        # 创建多个内容草稿
        drafts = create_content_drafts(setup_test_data, test_user_id, 3)
        content_ids = [draft.id for draft in drafts]
        
        batch_request = BatchScheduleRequest(
            content_ids=content_ids,
            schedule_time=datetime.utcnow() + timedelta(hours=1),
            stagger_minutes=5
        )
        
        result = await scheduling_service.batch_schedule_content(test_user_id, batch_request)
        
        assert result.total_items == 3
        assert result.successful_items == 3
        assert result.failed_items == 0
        assert len(result.results) == 3

    @pytest.mark.asyncio
    async def test_batch_schedule_content_partial_failure(self, scheduling_service, 
                                                        setup_test_data, test_user_id):
        """测试批量调度部分失败"""
        # 创建内容草稿，其中一个不存在
        drafts = create_content_drafts(setup_test_data, test_user_id, 2)
        content_ids = [draft.id for draft in drafts] + ["nonexistent_content"]
        
        batch_request = BatchScheduleRequest(
            content_ids=content_ids,
            schedule_time=datetime.utcnow() + timedelta(hours=1)
        )
        
        result = await scheduling_service.batch_schedule_content(test_user_id, batch_request)
        
        assert result.total_items == 3
        assert result.successful_items == 2
        assert result.failed_items == 1

    @pytest.mark.asyncio
    async def test_publish_content_immediately_success(self, scheduling_service, setup_test_data,
                                                     test_user_id, valid_publish_request):
        """测试立即发布内容成功"""
        result = await scheduling_service.publish_content_immediately(test_user_id, valid_publish_request)
        
        assert result.success is True
        assert result.posted_tweet_id is not None
        assert result.posted_at is not None
        assert "successfully" in result.message

    @pytest.mark.asyncio
    async def test_publish_content_immediately_no_token(self, scheduling_service, setup_test_data,
                                                      test_user_id, valid_publish_request,
                                                      mock_user_profile_service):
        """测试发布时没有Twitter令牌"""
        # 设置用户没有Twitter令牌
        mock_user_profile_service.set_access_token(test_user_id, None)
        
        result = await scheduling_service.publish_content_immediately(test_user_id, valid_publish_request)
        
        assert result.success is False
        assert result.error_code == "NO_ACCESS_TOKEN"
        assert "not connected" in result.message

    @pytest.mark.asyncio
    async def test_publish_content_immediately_twitter_api_error(self, scheduling_service, setup_test_data,
                                                               test_user_id, valid_publish_request,
                                                               mock_twitter_client):
        """测试Twitter API错误"""
        # 设置Twitter客户端失败
        mock_twitter_client.set_should_succeed(False)
        
        result = await scheduling_service.publish_content_immediately(test_user_id, valid_publish_request)
        
        assert result.success is False
        assert result.error_code == "TWITTER_API_ERROR"

    @pytest.mark.asyncio
    async def test_publish_content_tweet_too_long(self, scheduling_service, setup_test_data,
                                                 test_user_id, test_content_draft):
        """测试推文过长"""
        # 设置内容过长
        test_content_draft.current_content = "a" * 300  # 超过280字符限制
        
        publish_request = PublishRequest(content_id=test_content_draft.id)
        result = await scheduling_service.publish_content_immediately(test_user_id, publish_request)
        
        assert result.success is False
        assert result.error_code == "TWEET_TOO_LONG"

    @pytest.mark.asyncio
    async def test_batch_publish_content_success(self, scheduling_service, setup_test_data, test_user_id):
        """测试批量发布成功"""
        # 创建多个内容草稿
        drafts = create_content_drafts(setup_test_data, test_user_id, 2)
        content_ids = [draft.id for draft in drafts]
        
        batch_request = BatchPublishRequest(
            content_ids=content_ids,
            stagger_minutes=1
        )
        
        result = await scheduling_service.batch_publish_content(test_user_id, batch_request)
        
        assert result.total_items == 2
        assert result.successful_items == 2
        assert result.failed_items == 0

    @pytest.mark.asyncio
    async def test_update_publishing_status_success(self, scheduling_service, setup_test_data,
                                                  test_user_id, test_content_id):
        """测试更新发布状态成功"""
        # 创建调度内容
        create_scheduled_content(setup_test_data, test_user_id, test_content_id)
        
        status_request = StatusUpdateRequest(
            status=PublishStatus.POSTED,
            posted_tweet_id="123456789"
        )
        
        result = await scheduling_service.update_publishing_status(
            test_user_id, test_content_id, status_request
        )
        
        assert result is True

    @pytest.mark.asyncio
    async def test_update_publishing_status_failed_with_retry(self, scheduling_service, setup_test_data,
                                                            test_user_id, test_content_id):
        """测试更新失败状态并重试"""
        # 创建调度内容
        create_scheduled_content(setup_test_data, test_user_id, test_content_id)
        
        status_request = StatusUpdateRequest(
            status=PublishStatus.FAILED,
            error_message="Test error",
            error_code="TEST_ERROR",
            retry_scheduled=True
        )
        
        result = await scheduling_service.update_publishing_status(
            test_user_id, test_content_id, status_request
        )
        
        assert result is True

    @pytest.mark.asyncio
    async def test_get_publishing_history(self, scheduling_service, setup_test_data, test_user_id):
        """测试获取发布历史"""
        history = await scheduling_service.get_publishing_history(test_user_id, limit=10)
        
        assert isinstance(history, list)
        # 由于mock数据为空，应该返回空列表
        assert len(history) == 0

    @pytest.mark.asyncio
    async def test_get_publishing_analytics(self, scheduling_service, test_user_id):
        """测试获取发布分析"""
        analytics = await scheduling_service.get_publishing_analytics(test_user_id, days=30)
        
        assert analytics.total_scheduled == 0
        assert analytics.total_published == 0
        assert analytics.total_failed == 0
        assert analytics.success_rate == 0.0

    @pytest.mark.asyncio
    async def test_check_publishing_rules(self, scheduling_service, test_user_id, test_content_id):
        """测试检查发布规则"""
        proposed_time = datetime.utcnow() + timedelta(hours=1)
        
        result = await scheduling_service.check_publishing_rules(
            test_user_id, test_content_id, proposed_time
        )
        
        assert hasattr(result, 'can_publish')
        assert hasattr(result, 'violations')
        assert hasattr(result, 'recommendations')

    @pytest.mark.asyncio
    async def test_get_queue_info(self, scheduling_service, test_user_id):
        """测试获取队列信息"""
        queue_info = await scheduling_service.get_queue_info(test_user_id)
        
        assert queue_info.total_pending == 0
        assert queue_info.total_scheduled == 0
        assert hasattr(queue_info, 'queue_by_status')

    @pytest.mark.asyncio
    async def test_process_publishing_queue_empty(self, scheduling_service):
        """测试处理空队列"""
        result = await scheduling_service.process_publishing_queue()
        
        assert result['status'] == 'completed'
        assert result['processed_count'] == 0

    @pytest.mark.asyncio
    async def test_process_publishing_queue_already_processing(self, scheduling_service):
        """测试队列已在处理中"""
        # 设置正在处理状态
        scheduling_service._queue_processing = True
        
        result = await scheduling_service.process_publishing_queue()
        
        assert result['status'] == 'already_processing'
        
        # 重置状态
        scheduling_service._queue_processing = False

    @pytest.mark.asyncio
    async def test_custom_message_publishing(self, scheduling_service, setup_test_data,
                                           test_user_id, test_content_id):
        """测试使用自定义消息发布"""
        custom_message = "This is a custom tweet message"
        
        publish_request = PublishRequest(
            content_id=test_content_id,
            custom_message=custom_message
        )
        
        result = await scheduling_service.publish_content_immediately(test_user_id, publish_request)
        
        assert result.success is True
        # 验证Twitter客户端收到了自定义消息
        twitter_calls = scheduling_service.twitter_client.call_log
        assert any(call[2] == custom_message for call in twitter_calls if call[0] == 'create_tweet')

    @pytest.mark.asyncio
    async def test_force_publish_bypasses_rules(self, scheduling_service, setup_test_data,
                                              test_user_id, test_content_id):
        """测试强制发布绕过规则"""
        publish_request = PublishRequest(
            content_id=test_content_id,
            force_publish=True
        )
        
        result = await scheduling_service.publish_content_immediately(test_user_id, publish_request)
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_analytics_recording(self, scheduling_service, setup_test_data,
                                     test_user_id, valid_schedule_request, mock_analytics_collector):
        """测试分析记录"""
        await scheduling_service.schedule_content(test_user_id, valid_schedule_request)
        
        # 验证分析事件被记录
        assert len(mock_analytics_collector.events) > 0
        assert any(event.get('event_type') == 'content_scheduled' for event in mock_analytics_collector.events)

    @pytest.mark.asyncio
    async def test_error_handling_in_service_methods(self, scheduling_service, test_user_id):
        """测试服务方法中的错误处理"""
        # 测试获取不存在用户的待发布内容
        pending_content = await scheduling_service.get_pending_content("nonexistent_user")
        assert len(pending_content) == 0
        
        # 测试获取不存在用户的分析数据
        analytics = await scheduling_service.get_publishing_analytics("nonexistent_user")
        assert analytics.total_scheduled == 0

    @pytest.mark.asyncio
    async def test_timezone_handling(self, scheduling_service, setup_test_data, 
                                   test_user_id, test_content_id):
        """测试时区处理"""
        schedule_request = ScheduleRequest(
            content_id=test_content_id,
            scheduled_time=datetime.utcnow() + timedelta(hours=1),
            timezone="America/New_York"
        )
        
        result = await scheduling_service.schedule_content(test_user_id, schedule_request)
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_priority_handling(self, scheduling_service, setup_test_data,
                                   test_user_id, test_content_id):
        """测试优先级处理"""
        high_priority_request = ScheduleRequest(
            content_id=test_content_id,
            scheduled_time=datetime.utcnow() + timedelta(hours=1),
            priority=1  # 高优先级
        )
        
        result = await scheduling_service.schedule_content(test_user_id, high_priority_request)
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_tags_handling(self, scheduling_service, setup_test_data,
                               test_user_id, test_content_id):
        """测试标签处理"""
        tags = ["urgent", "marketing", "promotion"]
        
        schedule_request = ScheduleRequest(
            content_id=test_content_id,
            scheduled_time=datetime.utcnow() + timedelta(hours=1),
            tags=tags
        )
        
        result = await scheduling_service.schedule_content(test_user_id, schedule_request)
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, scheduling_service, setup_test_data, test_user_id):
        """测试并发操作"""
        # 创建多个内容草稿
        drafts = create_content_drafts(setup_test_data, test_user_id, 5)
        
        # 并发调度多个内容
        tasks = []
        for draft in drafts:
            schedule_request = ScheduleRequest(
                content_id=draft.id,
                scheduled_time=datetime.utcnow() + timedelta(hours=1, minutes=len(tasks)*5)
            )
            task = scheduling_service.schedule_content(test_user_id, schedule_request)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # 验证所有操作都成功
        assert all(result.success for result in results)
        assert len(results) == 5 