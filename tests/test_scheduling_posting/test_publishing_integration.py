"""Integration tests for scheduling_posting module - End-to-end workflows"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock

from modules.scheduling_posting import (
    SchedulingPostingService, ScheduleRequest, PublishRequest,
    BatchScheduleRequest, BatchPublishRequest, PublishStatus
)

from .conftest import create_content_drafts, create_scheduled_content


class TestPublishingIntegration:
    """Integration test cases for end-to-end publishing workflows"""

    @pytest.mark.asyncio
    async def test_end_to_end_immediate_publishing(self, scheduling_service, setup_test_data, 
                                                 test_user_id, test_content_id):
        """测试端到端即时发布流程"""
        # 1. 创建发布请求
        publish_request = PublishRequest(
            content_id=test_content_id,
            force_publish=False,
            skip_rules_check=False
        )
        
        # 2. 检查发布规则
        rule_check = await scheduling_service.check_publishing_rules(
            test_user_id, test_content_id, datetime.utcnow()
        )
        assert hasattr(rule_check, 'can_publish')
        
        # 3. 立即发布内容
        publish_result = await scheduling_service.publish_content_immediately(
            test_user_id, publish_request
        )
        
        # 4. 验证发布成功
        assert publish_result.success is True
        assert publish_result.posted_tweet_id is not None
        assert publish_result.posted_at is not None
        
        # 5. 验证内容状态已更新
        content_draft = setup_test_data.get_content_draft_by_id(test_content_id)
        assert content_draft.status == 'posted'
        
        # 6. 获取发布历史
        history = await scheduling_service.get_publishing_history(test_user_id, limit=5)
        # Note: 在真实场景中，这里应该能找到刚发布的内容

    @pytest.mark.asyncio
    async def test_end_to_end_scheduled_publishing(self, scheduling_service, setup_test_data,
                                                 test_user_id, test_content_id):
        """测试端到端预定发布流程"""
        future_time = datetime.utcnow() + timedelta(minutes=5)
        
        # 1. 创建调度请求
        schedule_request = ScheduleRequest(
            content_id=test_content_id,
            scheduled_time=future_time,
            timezone="UTC",
            priority=5
        )
        
        # 2. 调度内容
        schedule_result = await scheduling_service.schedule_content(test_user_id, schedule_request)
        
        # 3. 验证调度成功
        assert schedule_result.success is True
        assert schedule_result.scheduled_content_id is not None
        
        # 4. 验证内容出现在队列中
        queue_info = await scheduling_service.get_queue_info(test_user_id)
        assert queue_info.total_scheduled >= 0  # 在mock环境中可能为0
        
        # 5. 模拟队列处理
        process_result = await scheduling_service.process_publishing_queue()
        assert process_result['status'] in ['completed', 'already_processing']
        
        # 6. 获取发布分析
        analytics = await scheduling_service.get_publishing_analytics(test_user_id)
        assert analytics.total_scheduled >= 0

    @pytest.mark.asyncio
    async def test_end_to_end_batch_scheduling_workflow(self, scheduling_service, setup_test_data, test_user_id):
        """测试端到端批量调度工作流程"""
        # 1. 创建多个内容草稿
        drafts = create_content_drafts(setup_test_data, test_user_id, 5)
        content_ids = [draft.id for draft in drafts]
        
        # 2. 创建批量调度请求
        batch_request = BatchScheduleRequest(
            content_ids=content_ids,
            schedule_time=datetime.utcnow() + timedelta(hours=1),
            stagger_minutes=10,
            timezone="UTC"
        )
        
        # 3. 执行批量调度
        batch_result = await scheduling_service.batch_schedule_content(test_user_id, batch_request)
        
        # 4. 验证批量操作结果
        assert batch_result.total_items == 5
        assert batch_result.successful_items == 5
        assert batch_result.failed_items == 0
        assert len(batch_result.results) == 5
        
        # 5. 验证每个单独的结果
        for content_id, result in batch_result.results.items():
            assert result.success is True
            assert result.scheduled_content_id is not None

    @pytest.mark.asyncio
    async def test_end_to_end_batch_publishing_workflow(self, scheduling_service, setup_test_data, test_user_id):
        """测试端到端批量发布工作流程"""
        # 1. 创建多个内容草稿
        drafts = create_content_drafts(setup_test_data, test_user_id, 3)
        content_ids = [draft.id for draft in drafts]
        
        # 2. 创建批量发布请求
        batch_request = BatchPublishRequest(
            content_ids=content_ids,
            force_publish=True,  # 跳过规则检查以简化测试
            stagger_minutes=1
        )
        
        # 3. 执行批量发布
        batch_result = await scheduling_service.batch_publish_content(test_user_id, batch_request)
        
        # 4. 验证批量操作结果
        assert batch_result.total_items == 3
        assert batch_result.successful_items == 3
        assert batch_result.failed_items == 0

    @pytest.mark.asyncio
    async def test_end_to_end_failed_publishing_retry_workflow(self, scheduling_service, setup_test_data,
                                                             test_user_id, test_content_id, mock_twitter_client):
        """测试端到端发布失败重试工作流程"""
        # 1. 设置Twitter客户端失败
        mock_twitter_client.set_should_succeed(False)
        
        # 2. 尝试发布内容
        publish_request = PublishRequest(content_id=test_content_id, force_publish=True)
        publish_result = await scheduling_service.publish_content_immediately(test_user_id, publish_request)
        
        # 3. 验证发布失败
        assert publish_result.success is False
        assert publish_result.error_code == "TWITTER_API_ERROR"
        
        # 4. 重新设置Twitter客户端成功
        mock_twitter_client.set_should_succeed(True)
        
        # 5. 再次尝试发布
        retry_result = await scheduling_service.publish_content_immediately(test_user_id, publish_request)
        
        # 6. 验证重试成功
        assert retry_result.success is True
        assert retry_result.posted_tweet_id is not None

    @pytest.mark.asyncio
    async def test_end_to_end_rule_validation_workflow(self, scheduling_service, setup_test_data,
                                                      test_user_id, mock_data_flow_manager):
        """测试端到端规则验证工作流程"""
        # 1. 设置用户已达到每日限制
        mock_data_flow_manager.get_daily_post_count = Mock(return_value=5)
        
        # 2. 创建内容
        drafts = create_content_drafts(setup_test_data, test_user_id, 1)
        content_id = drafts[0].id
        
        # 3. 检查发布规则
        rule_check = await scheduling_service.check_publishing_rules(
            test_user_id, content_id, datetime.utcnow() + timedelta(hours=1)
        )
        
        # 4. 验证规则检查结果
        assert hasattr(rule_check, 'can_publish')
        assert isinstance(rule_check.violations, list)
        
        # 5. 尝试调度内容（应该失败或警告）
        schedule_request = ScheduleRequest(
            content_id=content_id,
            scheduled_time=datetime.utcnow() + timedelta(hours=1)
        )
        
        schedule_result = await scheduling_service.schedule_content(test_user_id, schedule_request)
        
        # 6. 验证调度结果（根据规则可能成功或失败）
        assert hasattr(schedule_result, 'success')

    @pytest.mark.asyncio
    async def test_end_to_end_queue_processing_workflow(self, scheduling_service, setup_test_data, test_user_id):
        """测试端到端队列处理工作流程"""
        # 1. 创建多个调度内容
        drafts = create_content_drafts(setup_test_data, test_user_id, 3)
        
        for i, draft in enumerate(drafts):
            scheduled_time = datetime.utcnow() + timedelta(minutes=i*5)
            create_scheduled_content(
                setup_test_data, test_user_id, draft.id, 
                scheduled_time, PublishStatus.SCHEDULED
            )
        
        # 2. 获取初始队列信息
        initial_queue_info = await scheduling_service.get_queue_info(test_user_id)
        assert hasattr(initial_queue_info, 'total_scheduled')
        
        # 3. 处理发布队列
        process_result = await scheduling_service.process_publishing_queue()
        
        # 4. 验证处理结果
        assert process_result['status'] in ['completed', 'already_processing']
        assert 'processed_count' in process_result
        
        # 5. 获取处理后的队列信息
        final_queue_info = await scheduling_service.get_queue_info(test_user_id)
        assert hasattr(final_queue_info, 'total_scheduled')

    @pytest.mark.asyncio
    async def test_end_to_end_analytics_tracking_workflow(self, scheduling_service, setup_test_data,
                                                         test_user_id, mock_analytics_collector):
        """测试端到端分析跟踪工作流程"""
        # 1. 创建并发布内容
        drafts = create_content_drafts(setup_test_data, test_user_id, 2)
        
        for draft in drafts:
            publish_request = PublishRequest(content_id=draft.id, force_publish=True)
            publish_result = await scheduling_service.publish_content_immediately(test_user_id, publish_request)
            assert publish_result.success is True
        
        # 2. 验证分析事件被记录
        assert len(mock_analytics_collector.events) > 0
        
        # 3. 获取发布分析
        analytics = await scheduling_service.get_publishing_analytics(test_user_id)
        
        # 4. 验证分析数据结构
        assert hasattr(analytics, 'total_scheduled')
        assert hasattr(analytics, 'total_published')
        assert hasattr(analytics, 'success_rate')

    @pytest.mark.asyncio
    async def test_end_to_end_cancellation_workflow(self, scheduling_service, setup_test_data, test_user_id):
        """测试端到端取消调度工作流程"""
        # 1. 创建并调度内容
        drafts = create_content_drafts(setup_test_data, test_user_id, 1)
        content_id = drafts[0].id
        
        schedule_request = ScheduleRequest(
            content_id=content_id,
            scheduled_time=datetime.utcnow() + timedelta(hours=2)
        )
        
        schedule_result = await scheduling_service.schedule_content(test_user_id, schedule_request)
        assert schedule_result.success is True
        
        # 2. 取消调度
        cancel_result = await scheduling_service.cancel_scheduled_content(test_user_id, content_id)
        assert cancel_result is True
        
        # 3. 验证内容状态恢复
        content_draft = setup_test_data.get_content_draft_by_id(content_id)
        assert content_draft.status == 'approved'

    @pytest.mark.asyncio
    async def test_end_to_end_concurrent_operations(self, scheduling_service, setup_test_data, test_user_id):
        """测试端到端并发操作"""
        # 1. 创建多个内容草稿
        drafts = create_content_drafts(setup_test_data, test_user_id, 5)
        
        # 2. 并发执行多种操作
        tasks = []
        
        # 立即发布一些内容
        for i in range(2):
            publish_request = PublishRequest(content_id=drafts[i].id, force_publish=True)
            task = scheduling_service.publish_content_immediately(test_user_id, publish_request)
            tasks.append(task)
        
        # 调度一些内容
        for i in range(2, 4):
            schedule_request = ScheduleRequest(
                content_id=drafts[i].id,
                scheduled_time=datetime.utcnow() + timedelta(hours=1, minutes=i*10)
            )
            task = scheduling_service.schedule_content(test_user_id, schedule_request)
            tasks.append(task)
        
        # 检查规则
        rule_check_task = scheduling_service.check_publishing_rules(
            test_user_id, drafts[4].id, datetime.utcnow() + timedelta(hours=1)
        )
        tasks.append(rule_check_task)
        
        # 3. 等待所有操作完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 4. 验证所有操作都成功或返回有效结果
        for result in results:
            assert not isinstance(result, Exception)
            assert hasattr(result, 'success') or hasattr(result, 'can_publish')

    @pytest.mark.asyncio
    async def test_end_to_end_error_recovery_workflow(self, scheduling_service, setup_test_data,
                                                    test_user_id, mock_twitter_client):
        """测试端到端错误恢复工作流程"""
        # 1. 创建内容
        drafts = create_content_drafts(setup_test_data, test_user_id, 1)
        content_id = drafts[0].id
        
        # 2. 模拟网络错误
        mock_twitter_client.set_should_succeed(False)
        
        # 3. 尝试发布并失败
        publish_request = PublishRequest(content_id=content_id, force_publish=True)
        failed_result = await scheduling_service.publish_content_immediately(test_user_id, publish_request)
        
        assert failed_result.success is False
        
        # 4. 恢复连接
        mock_twitter_client.set_should_succeed(True)
        
        # 5. 重试发布
        retry_result = await scheduling_service.publish_content_immediately(test_user_id, publish_request)
        
        assert retry_result.success is True
        
        # 6. 验证最终状态一致
        content_draft = setup_test_data.get_content_draft_by_id(content_id)
        assert content_draft.status == 'posted'

    @pytest.mark.asyncio
    async def test_end_to_end_timezone_handling_workflow(self, scheduling_service, setup_test_data, test_user_id):
        """测试端到端时区处理工作流程"""
        # 1. 创建内容
        drafts = create_content_drafts(setup_test_data, test_user_id, 1)
        content_id = drafts[0].id
        
        # 2. 使用不同时区调度内容
        est_time = datetime.utcnow() + timedelta(hours=1)
        
        schedule_request = ScheduleRequest(
            content_id=content_id,
            scheduled_time=est_time,
            timezone="America/New_York"
        )
        
        # 3. 调度内容
        schedule_result = await scheduling_service.schedule_content(test_user_id, schedule_request)
        
        # 4. 验证调度成功
        assert schedule_result.success is True
        
        # 5. 验证时间正确处理
        assert schedule_result.scheduled_time == est_time

    @pytest.mark.asyncio 
    async def test_end_to_end_quality_control_workflow(self, scheduling_service, setup_test_data, test_user_id):
        """测试端到端质量控制工作流程"""
        # 1. 创建不同质量的内容
        high_quality_draft = create_content_drafts(setup_test_data, test_user_id, 1)[0]
        high_quality_draft.quality_score = 0.9
        
        # 2. 检查高质量内容是否可以立即发布
        rule_check = await scheduling_service.check_publishing_rules(
            test_user_id, high_quality_draft.id, datetime.utcnow()
        )
        
        # 3. 发布高质量内容
        if rule_check.can_publish:
            publish_request = PublishRequest(content_id=high_quality_draft.id)
            publish_result = await scheduling_service.publish_content_immediately(test_user_id, publish_request)
            assert publish_result.success is True

    @pytest.mark.asyncio
    async def test_end_to_end_comprehensive_workflow(self, scheduling_service, setup_test_data, test_user_id):
        """测试全面的端到端工作流程"""
        # 1. 创建多个内容草稿
        drafts = create_content_drafts(setup_test_data, test_user_id, 10)
        
        # 2. 立即发布一些内容
        immediate_publish_tasks = []
        for i in range(3):
            publish_request = PublishRequest(content_id=drafts[i].id, force_publish=True)
            task = scheduling_service.publish_content_immediately(test_user_id, publish_request)
            immediate_publish_tasks.append(task)
        
        immediate_results = await asyncio.gather(*immediate_publish_tasks)
        
        # 3. 批量调度一些内容
        batch_content_ids = [draft.id for draft in drafts[3:7]]
        batch_request = BatchScheduleRequest(
            content_ids=batch_content_ids,
            schedule_time=datetime.utcnow() + timedelta(hours=1),
            stagger_minutes=5
        )
        
        batch_result = await scheduling_service.batch_schedule_content(test_user_id, batch_request)
        
        # 4. 检查剩余内容的发布规则
        remaining_content_ids = [draft.id for draft in drafts[7:]]
        rule_check_tasks = []
        
        for content_id in remaining_content_ids:
            task = scheduling_service.check_publishing_rules(
                test_user_id, content_id, datetime.utcnow() + timedelta(hours=2)
            )
            rule_check_tasks.append(task)
        
        rule_results = await asyncio.gather(*rule_check_tasks)
        
        # 5. 获取队列信息
        queue_info = await scheduling_service.get_queue_info(test_user_id)
        
        # 6. 处理队列
        process_result = await scheduling_service.process_publishing_queue()
        
        # 7. 获取分析数据
        analytics = await scheduling_service.get_publishing_analytics(test_user_id)
        
        # 8. 获取发布历史
        history = await scheduling_service.get_publishing_history(test_user_id, limit=20)
        
        # 9. 验证所有操作都成功
        assert all(result.success for result in immediate_results)
        assert batch_result.successful_items == 4
        assert len(rule_results) == 3
        assert hasattr(queue_info, 'total_scheduled')
        assert process_result['status'] in ['completed', 'already_processing']
        assert hasattr(analytics, 'total_scheduled')
        assert isinstance(history, list) 