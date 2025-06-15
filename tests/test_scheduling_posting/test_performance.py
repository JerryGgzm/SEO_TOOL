"""Performance tests for scheduling_posting module"""
import pytest
import time
import asyncio
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from modules.scheduling_posting import (
    SchedulingPostingService, ScheduleRequest, PublishRequest,
    BatchScheduleRequest, BatchPublishRequest
)

from .conftest import create_content_drafts


class TestPerformance:
    """Performance test cases for scheduling_posting module"""

    @pytest.mark.asyncio
    async def test_batch_scheduling_performance(self, scheduling_service, setup_test_data, test_user_id):
        """测试批量调度性能 - 来自用户示例"""
        content_ids = []
        
        # 创建50个内容草稿（批量限制）
        drafts = create_content_drafts(setup_test_data, test_user_id, 50)
        content_ids = [draft.id for draft in drafts]
        
        start_time = time.time()
        
        batch_request = BatchScheduleRequest(
            content_ids=content_ids,
            schedule_time=datetime.utcnow() + timedelta(hours=1),
            stagger_minutes=1
        )
        
        result = await scheduling_service.batch_schedule_content(test_user_id, batch_request)
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert result.successful_items == 50
        assert duration < 30  # 应该在30秒内完成

    @pytest.mark.asyncio
    async def test_batch_publishing_performance(self, scheduling_service, setup_test_data, test_user_id):
        """测试批量发布性能"""
        # 创建50个内容草稿
        drafts = create_content_drafts(setup_test_data, test_user_id, 50)
        content_ids = [draft.id for draft in drafts]
        
        start_time = time.time()
        
        batch_request = BatchPublishRequest(
            content_ids=content_ids,
            force_publish=True,  # 跳过规则检查以测试纯发布性能
            stagger_minutes=0  # 最小延迟
        )
        
        result = await scheduling_service.batch_publish_content(test_user_id, batch_request)
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert result.successful_items == 50
        assert duration < 60  # 应该在60秒内完成
        
        # 计算吞吐量
        throughput = result.successful_items / duration
        assert throughput > 1  # 每秒至少处理1个

    @pytest.mark.asyncio
    async def test_concurrent_scheduling_performance(self, scheduling_service, setup_test_data, test_user_id):
        """测试并发调度性能"""
        # 创建20个内容草稿
        drafts = create_content_drafts(setup_test_data, test_user_id, 20)
        
        start_time = time.time()
        
        # 并发执行20个调度请求
        tasks = []
        for i, draft in enumerate(drafts):
            schedule_request = ScheduleRequest(
                content_id=draft.id,
                scheduled_time=datetime.utcnow() + timedelta(hours=1, minutes=i)
            )
            task = scheduling_service.schedule_content(test_user_id, schedule_request)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 验证所有调度都成功
        successful_count = sum(1 for result in results if result.success)
        assert successful_count == 20
        
        # 并发操作应该比串行快很多
        assert duration < 10  # 应该在10秒内完成

    @pytest.mark.asyncio
    async def test_concurrent_publishing_performance(self, scheduling_service, setup_test_data, test_user_id):
        """测试并发发布性能"""
        # 创建15个内容草稿
        drafts = create_content_drafts(setup_test_data, test_user_id, 15)
        
        start_time = time.time()
        
        # 并发执行15个发布请求
        tasks = []
        for draft in drafts:
            publish_request = PublishRequest(content_id=draft.id, force_publish=True)
            task = scheduling_service.publish_content_immediately(test_user_id, publish_request)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 验证所有发布都成功
        successful_count = sum(1 for result in results if result.success)
        assert successful_count == 15
        
        # 并发操作应该高效
        assert duration < 15  # 应该在15秒内完成

    @pytest.mark.asyncio
    async def test_rule_checking_performance(self, scheduling_service, test_user_id):
        """测试规则检查性能"""
        start_time = time.time()
        
        # 并发执行100次规则检查
        tasks = []
        for i in range(100):
            proposed_time = datetime.utcnow() + timedelta(hours=1, minutes=i)
            task = scheduling_service.check_publishing_rules(
                test_user_id, f"content_{i}", proposed_time
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 验证所有规则检查都完成
        assert len(results) == 100
        assert all(hasattr(result, 'can_publish') for result in results)
        
        # 规则检查应该很快
        assert duration < 5  # 应该在5秒内完成

    @pytest.mark.asyncio
    async def test_queue_processing_performance(self, scheduling_service, setup_test_data, test_user_id):
        """测试队列处理性能"""
        # 创建多个调度内容来模拟队列
        drafts = create_content_drafts(setup_test_data, test_user_id, 25)
        
        # 调度所有内容，确保时间在未来
        for i, draft in enumerate(drafts):
            schedule_request = ScheduleRequest(
                content_id=draft.id,
                scheduled_time=datetime.utcnow() + timedelta(minutes=i+1)  # 确保至少1分钟后
            )
            await scheduling_service.schedule_content(test_user_id, schedule_request)
        
        start_time = time.time()
        
        # 处理队列
        result = await scheduling_service.process_publishing_queue()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 队列处理应该高效
        assert duration < 30  # 应该在30秒内完成
        assert result['status'] in ['completed', 'already_processing']

    @pytest.mark.asyncio
    async def test_analytics_retrieval_performance(self, scheduling_service, test_user_id):
        """测试分析数据检索性能"""
        start_time = time.time()
        
        # 并发获取多种分析数据
        tasks = [
            scheduling_service.get_publishing_analytics(test_user_id, 7),
            scheduling_service.get_publishing_analytics(test_user_id, 30),
            scheduling_service.get_publishing_history(test_user_id, limit=50),
            scheduling_service.get_queue_info(test_user_id),
            scheduling_service.get_pending_content(test_user_id, limit=100)
        ]
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 验证所有分析数据都获取到
        assert len(results) == 5
        
        # 分析数据检索应该很快
        assert duration < 3  # 应该在3秒内完成

    @pytest.mark.asyncio
    async def test_mixed_workload_performance(self, scheduling_service, setup_test_data, test_user_id):
        """测试混合工作负载性能"""
        # 创建内容草稿
        drafts = create_content_drafts(setup_test_data, test_user_id, 30)
        
        start_time = time.time()
        
        # 混合操作：调度、发布、规则检查、分析
        tasks = []
        
        # 调度10个内容
        for i in range(10):
            schedule_request = ScheduleRequest(
                content_id=drafts[i].id,
                scheduled_time=datetime.utcnow() + timedelta(hours=1, minutes=i*5)
            )
            task = scheduling_service.schedule_content(test_user_id, schedule_request)
            tasks.append(task)
        
        # 立即发布10个内容
        for i in range(10, 20):
            publish_request = PublishRequest(content_id=drafts[i].id, force_publish=True)
            task = scheduling_service.publish_content_immediately(test_user_id, publish_request)
            tasks.append(task)
        
        # 检查10个内容的规则
        for i in range(20, 30):
            task = scheduling_service.check_publishing_rules(
                test_user_id, drafts[i].id, datetime.utcnow() + timedelta(hours=1)
            )
            tasks.append(task)
        
        # 添加分析任务
        tasks.append(scheduling_service.get_publishing_analytics(test_user_id))
        tasks.append(scheduling_service.get_queue_info(test_user_id))
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 验证所有操作都完成
        assert len(results) == 32
        
        # 混合工作负载应该在合理时间内完成
        assert duration < 45  # 应该在45秒内完成

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, scheduling_service, setup_test_data, test_user_id):
        """测试高负载下的内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建大量内容并执行操作
        drafts = create_content_drafts(setup_test_data, test_user_id, 100)
        
        # 批量调度（分批处理以遵循限制）
        batch_request = BatchScheduleRequest(
            content_ids=[draft.id for draft in drafts[:50]],
            schedule_time=datetime.utcnow() + timedelta(hours=1),
            stagger_minutes=1
        )
        await scheduling_service.batch_schedule_content(test_user_id, batch_request)
        
        # 批量发布
        batch_publish_request = BatchPublishRequest(
            content_ids=[draft.id for draft in drafts[50:100]],
            force_publish=True,
            stagger_minutes=0
        )
        await scheduling_service.batch_publish_content(test_user_id, batch_publish_request)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # 内存增长应该在合理范围内
        assert memory_increase < 100  # 不应该增长超过100MB

    @pytest.mark.asyncio
    async def test_error_handling_performance_impact(self, scheduling_service, setup_test_data,
                                                   test_user_id, mock_twitter_client):
        """测试错误处理对性能的影响"""
        # 创建内容草稿
        drafts = create_content_drafts(setup_test_data, test_user_id, 20)
        
        start_time = time.time()
        
        # 执行发布操作，交替设置成功/失败状态
        results = []
        for i, draft in enumerate(drafts):
            # 设置每个操作的成功/失败状态
            should_succeed = i % 2 == 0  # 偶数索引成功，奇数索引失败
            mock_twitter_client.set_should_succeed(should_succeed)
            
            publish_request = PublishRequest(content_id=draft.id, force_publish=True)
            result = await scheduling_service.publish_content_immediately(test_user_id, publish_request)
            results.append(result)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 验证有成功和失败的操作
        successful = sum(1 for result in results if result.success)
        failed = sum(1 for result in results if not result.success)
        
        assert successful > 0, f"Expected some successful operations, got {successful}"
        assert failed > 0, f"Expected some failed operations, got {failed}"
        
        # 错误处理不应该显著影响性能
        assert duration < 25  # 应该在25秒内完成

    @pytest.mark.asyncio
    async def test_scalability_simulation(self, scheduling_service, setup_test_data, test_user_id):
        """测试可扩展性模拟"""
        # 模拟多个用户的操作
        user_ids = [f"user_{i}" for i in range(5)]
        
        start_time = time.time()
        
        # 为每个用户创建内容并执行操作
        all_tasks = []
        
        for user_id in user_ids:
            # 为每个用户创建内容
            user_drafts = create_content_drafts(setup_test_data, user_id, 10)
            
            # 每个用户执行一些操作
            for i, draft in enumerate(user_drafts[:5]):
                # 调度一些内容
                schedule_request = ScheduleRequest(
                    content_id=draft.id,
                    scheduled_time=datetime.utcnow() + timedelta(hours=1, minutes=i*10)
                )
                task = scheduling_service.schedule_content(user_id, schedule_request)
                all_tasks.append(task)
            
            for draft in user_drafts[5:]:
                # 发布一些内容
                publish_request = PublishRequest(content_id=draft.id, force_publish=True)
                task = scheduling_service.publish_content_immediately(user_id, publish_request)
                all_tasks.append(task)
        
        results = await asyncio.gather(*all_tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 验证所有操作都完成
        assert len(results) == 50  # 5个用户 × 10个操作
        
        # 多用户操作应该在合理时间内完成
        assert duration < 60  # 应该在60秒内完成

    @pytest.mark.asyncio
    async def test_database_operation_performance(self, scheduling_service, setup_test_data, test_user_id):
        """测试数据库操作性能"""
        # 创建内容草稿
        drafts = create_content_drafts(setup_test_data, test_user_id, 50)
        
        start_time = time.time()
        
        # 执行大量数据库密集型操作
        tasks = []
        
        # 调度操作（涉及写入）
        for i, draft in enumerate(drafts[:25]):
            schedule_request = ScheduleRequest(
                content_id=draft.id,
                scheduled_time=datetime.utcnow() + timedelta(hours=1, minutes=i)
            )
            task = scheduling_service.schedule_content(test_user_id, schedule_request)
            tasks.append(task)
        
        # 查询操作
        for _ in range(25):
            tasks.append(scheduling_service.get_pending_content(test_user_id, limit=20))
            tasks.append(scheduling_service.get_queue_info(test_user_id))
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 验证所有数据库操作都完成
        assert len(results) == 75
        
        # 数据库操作应该高效
        assert duration < 20  # 应该在20秒内完成

    def test_synchronous_operations_performance(self, scheduling_service, setup_test_data, test_user_id):
        """测试同步操作性能"""
        # 测试一些同步方法的性能
        from modules.scheduling_posting.rules_engine import InternalRulesEngine
        
        rules_engine = InternalRulesEngine(setup_test_data)
        
        start_time = time.time()
        
        # 执行大量文本相似度计算
        text1 = "This is a test message for similarity calculation"
        text2 = "This is another test message for similarity"
        
        similarities = []
        for i in range(1000):
            similarity = rules_engine._calculate_similarity(text1, text2)
            similarities.append(similarity)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 验证计算完成
        assert len(similarities) == 1000
        assert all(0 <= sim <= 1 for sim in similarities)
        
        # 同步计算应该很快
        assert duration < 1  # 应该在1秒内完成

    @pytest.mark.asyncio
    async def test_stress_test_with_failures(self, scheduling_service, setup_test_data,
                                           test_user_id, mock_twitter_client):
        """压力测试包含失败场景"""
        # 创建大量内容
        drafts = create_content_drafts(setup_test_data, test_user_id, 100)
        
        # 随机设置失败
        import random
        
        start_time = time.time()
        
        tasks = []
        for i, draft in enumerate(drafts):
            # 随机决定是否让操作失败
            should_fail = random.random() < 0.3  # 30% 失败率
            mock_twitter_client.set_should_succeed(not should_fail)
            
            if i % 2 == 0:
                # 调度操作
                schedule_request = ScheduleRequest(
                    content_id=draft.id,
                    scheduled_time=datetime.utcnow() + timedelta(hours=1, minutes=i)
                )
                task = scheduling_service.schedule_content(test_user_id, schedule_request)
            else:
                # 发布操作
                publish_request = PublishRequest(content_id=draft.id, force_publish=True)
                task = scheduling_service.publish_content_immediately(test_user_id, publish_request)
            
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 验证操作完成（包括失败的）
        assert len(results) == 100
        
        # 即使有失败，系统也应该保持响应
        assert duration < 120  # 应该在120秒内完成
        
        # 确保没有异常抛出到顶层
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0  # 所有异常都应该被妥善处理 