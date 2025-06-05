"""
Performance and load tests for review optimization module
"""
import pytest
import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from unittest.mock import Mock

from modules.review_optimization.models import (
    ReviewItem, ReviewStatus, ReviewFilterRequest
)
from modules.review_optimization.repository import ReviewOptimizationRepository
from modules.review_optimization.service import ReviewOptimizationService


class TestPerformance:
    """Performance tests for review optimization"""
    
    def test_bulk_item_creation_performance(self, repository):
        """Test performance of creating many review items"""
        start_time = time.time()
        
        # Create 1000 review items
        founder_id = "performance_founder"
        items_created = 0
        
        for i in range(1000):
            item = ReviewItem(
                id=str(uuid.uuid4()),
                content_draft_id=f"draft_{i}",
                founder_id=founder_id,
                content_type="tweet",
                original_content=f"Performance test content {i}",
                current_content=f"Performance test content {i}",
                generation_reason="performance_test",
                ai_confidence_score=0.5 + (i % 50) / 100,  # Vary confidence
                review_priority=1 + (i % 10)  # Vary priority
            )
            
            if repository.create_review_item(item):
                items_created += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\nCreated {items_created} items in {duration:.2f} seconds")
        print(f"Rate: {items_created/duration:.2f} items/second")
        
        # Performance assertion - should be able to create at least 100 items/second
        assert items_created/duration > 100, f"Creation rate too slow: {items_created/duration:.2f} items/second"
        assert items_created == 1000, f"Not all items were created: {items_created}/1000"
    
    def test_query_performance_with_large_dataset(self, repository):
        """Test query performance with large dataset"""
        # First create a large dataset
        founder_id = "query_perf_founder"
        
        # Create 5000 items with various statuses
        for i in range(5000):
            status = [ReviewStatus.PENDING, ReviewStatus.APPROVED, ReviewStatus.REJECTED][i % 3]
            item = ReviewItem(
                id=str(uuid.uuid4()),
                content_draft_id=f"query_draft_{i}",
                founder_id=founder_id,
                content_type="tweet",
                original_content=f"Query test content {i}",
                current_content=f"Query test content {i}",
                generation_reason="query_test",
                ai_confidence_score=0.3 + (i % 70) / 100,
                review_priority=1 + (i % 10),
                status=status
            )
            repository.create_review_item(item)
        
        # Test various queries
        queries = [
            # Basic query
            ReviewFilterRequest(limit=50),
            
            # Status filter
            ReviewFilterRequest(status=ReviewStatus.PENDING, limit=100),
            
            # Priority filter
            ReviewFilterRequest(priority_min=7, priority_max=10, limit=100),
            
            # Confidence filter
            ReviewFilterRequest(ai_confidence_min=0.8, limit=100),
            
            # Complex filter
            ReviewFilterRequest(
                status=ReviewStatus.PENDING,
                priority_min=5,
                ai_confidence_min=0.6,
                limit=50
            )
        ]
        
        for i, filter_req in enumerate(queries):
            start_time = time.time()
            
            items = repository.get_review_items(founder_id, filter_req)
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"\nQuery {i+1}: Retrieved {len(items)} items in {duration:.3f} seconds")
            
            # Each query should complete in under 1 second
            assert duration < 1.0, f"Query {i+1} too slow: {duration:.3f} seconds"
    
    def test_concurrent_operations_performance(self, service, repository):
        """Test performance under concurrent operations"""
        founder_id = "concurrent_founder"
        
        # Create some initial items
        item_ids = []
        for i in range(100):
            item = ReviewItem(
                id=str(uuid.uuid4()),
                content_draft_id=f"concurrent_draft_{i}",
                founder_id=founder_id,
                content_type="tweet",
                original_content=f"Concurrent test content {i}",
                current_content=f"Concurrent test content {i}",
                generation_reason="concurrent_test",
                ai_confidence_score=0.7,
                review_priority=5
            )
            if repository.create_review_item(item):
                item_ids.append(item.id)
        
        def concurrent_operations():
            """Perform concurrent operations"""
            results = {
                'queries': 0,
                'updates': 0,
                'errors': 0
            }
            
            try:
                # Query operations
                for _ in range(10):
                    items = service.get_review_queue(founder_id)
                    if items:
                        results['queries'] += 1
                
                # Update operations
                for item_id in item_ids[:10]:
                    success = service.update_content(
                        item_id, founder_id, 
                        f"Updated at {time.time()}", 
                        "concurrent_user"
                    )
                    if success:
                        results['updates'] += 1
                        
            except Exception as e:
                results['errors'] += 1
                print(f"Concurrent operation error: {e}")
            
            return results
        
        # Run concurrent operations
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(concurrent_operations) for _ in range(10)]
            
            all_results = {
                'queries': 0,
                'updates': 0,
                'errors': 0
            }
            
            for future in as_completed(futures):
                result = future.result()
                all_results['queries'] += result['queries']
                all_results['updates'] += result['updates']
                all_results['errors'] += result['errors']
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\nConcurrent operations completed in {duration:.2f} seconds")
        print(f"Total queries: {all_results['queries']}")
        print(f"Total updates: {all_results['updates']}")
        print(f"Total errors: {all_results['errors']}")
        
        # Performance assertions
        assert duration < 10.0, f"Concurrent operations too slow: {duration:.2f} seconds"
        assert all_results['errors'] == 0, f"Concurrent operations had errors: {all_results['errors']}"
        assert all_results['queries'] > 50, f"Not enough queries completed: {all_results['queries']}"
    
    def test_statistics_calculation_performance(self, repository):
        """Test performance of statistics calculation"""
        founder_id = "stats_founder"
        
        # Create a large dataset for statistics
        statuses = [ReviewStatus.PENDING, ReviewStatus.APPROVED, ReviewStatus.REJECTED, ReviewStatus.EDITED]
        
        for i in range(2000):
            item = ReviewItem(
                id=str(uuid.uuid4()),
                content_draft_id=f"stats_draft_{i}",
                founder_id=founder_id,
                content_type="tweet",
                original_content=f"Stats test content {i}",
                current_content=f"Stats test content {i}",
                generation_reason="stats_test",
                ai_confidence_score=0.3 + (i % 70) / 100,
                review_priority=1 + (i % 10),
                status=statuses[i % len(statuses)]
            )
            repository.create_review_item(item)
        
        # Test statistics calculation
        start_time = time.time()
        
        stats = repository.get_review_statistics(founder_id, days=30)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\nStatistics calculation completed in {duration:.3f} seconds")
        print(f"Total items: {stats.total_items}")
        print(f"Approval rate: {stats.approval_rate}")
        
        # Performance assertions
        assert duration < 2.0, f"Statistics calculation too slow: {duration:.3f} seconds"
        assert stats.total_items == 2000, f"Incorrect item count: {stats.total_items}"
    
    def test_memory_usage_during_bulk_operations(self, repository):
        """Test memory usage during bulk operations"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        founder_id = "memory_test_founder"
        
        # Perform bulk operations
        for batch in range(10):  # 10 batches of 500 items each
            batch_items = []
            
            for i in range(500):
                item = ReviewItem(
                    id=str(uuid.uuid4()),
                    content_draft_id=f"memory_draft_{batch}_{i}",
                    founder_id=founder_id,
                    content_type="tweet",
                    original_content=f"Memory test content {batch}_{i}",
                    current_content=f"Memory test content {batch}_{i}",
                    generation_reason="memory_test",
                    ai_confidence_score=0.7,
                    review_priority=5
                )
                repository.create_review_item(item)
            
            # Check memory after each batch
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            
            print(f"Batch {batch + 1}: Memory usage: {current_memory:.1f} MB (increase: {memory_increase:.1f} MB)")
            
            # Memory shouldn't grow excessively (less than 500MB increase)
            assert memory_increase < 500, f"Memory usage too high: {memory_increase:.1f} MB"
    
    def test_database_connection_pooling(self, repository):
        """Test database connection efficiency"""
        founder_id = "db_pool_founder"
        
        # Create initial items
        for i in range(50):
            item = ReviewItem(
                id=str(uuid.uuid4()),
                content_draft_id=f"db_pool_draft_{i}",
                founder_id=founder_id,
                content_type="tweet",
                original_content=f"DB pool test content {i}",
                current_content=f"DB pool test content {i}",
                generation_reason="db_pool_test",
                ai_confidence_score=0.7,
                review_priority=5
            )
            repository.create_review_item(item)
        
        # Perform many rapid database operations
        start_time = time.time()
        
        def rapid_db_operations():
            for _ in range(100):
                # Query operation
                items = repository.get_review_items(founder_id, ReviewFilterRequest(limit=10))
                
                if items:
                    # Update operation
                    repository.update_review_item(items[0].id, {"review_priority": 6})
        
        # Run multiple threads doing rapid DB operations
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=rapid_db_operations)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\nRapid DB operations completed in {duration:.2f} seconds")
        
        # Should complete in reasonable time even with many concurrent operations
        assert duration < 30.0, f"DB operations too slow: {duration:.2f} seconds"


class TestScalability:
    """Test scalability aspects"""
    
    def test_large_filter_result_sets(self, repository):
        """Test handling large filter result sets"""
        founder_id = "large_result_founder"
        
        # Create many items that will match a broad filter
        for i in range(3000):
            item = ReviewItem(
                id=str(uuid.uuid4()),
                content_draft_id=f"large_result_draft_{i}",
                founder_id=founder_id,
                content_type="tweet",
                original_content=f"Large result test content {i}",
                current_content=f"Large result test content {i}",
                generation_reason="large_result_test",
                ai_confidence_score=0.8,  # All high confidence
                review_priority=8,  # All high priority
                status=ReviewStatus.PENDING  # All pending
            )
            repository.create_review_item(item)
        
        # Test various limit sizes
        limits = [10, 50, 100, 500, 1000]
        
        for limit in limits:
            start_time = time.time()
            
            filter_req = ReviewFilterRequest(
                status=ReviewStatus.PENDING,
                ai_confidence_min=0.7,
                limit=limit
            )
            
            items = repository.get_review_items(founder_id, filter_req)
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"Limit {limit}: Retrieved {len(items)} items in {duration:.3f} seconds")
            
            # Verify correct limit is applied
            assert len(items) <= limit, f"Returned more items than limit: {len(items)} > {limit}"
            
            # Performance should scale reasonably
            expected_max_time = 0.1 + (limit / 10000)  # Allow more time for larger limits
            assert duration < expected_max_time, f"Query with limit {limit} too slow: {duration:.3f} seconds"
    
    def test_pagination_performance(self, repository):
        """Test pagination performance"""
        founder_id = "pagination_founder"
        
        # Create items for pagination testing
        for i in range(1000):
            item = ReviewItem(
                id=str(uuid.uuid4()),
                content_draft_id=f"pagination_draft_{i}",
                founder_id=founder_id,
                content_type="tweet",
                original_content=f"Pagination test content {i}",
                current_content=f"Pagination test content {i}",
                generation_reason="pagination_test",
                ai_confidence_score=0.7,
                review_priority=5,
                status=ReviewStatus.PENDING
            )
            repository.create_review_item(item)
        
        # Test pagination through all items
        page_size = 50
        total_retrieved = 0
        page_times = []
        
        for offset in range(0, 1000, page_size):
            start_time = time.time()
            
            filter_req = ReviewFilterRequest(
                status=ReviewStatus.PENDING,
                limit=page_size,
                offset=offset
            )
            
            items = repository.get_review_items(founder_id, filter_req)
            
            end_time = time.time()
            duration = end_time - start_time
            page_times.append(duration)
            
            total_retrieved += len(items)
            
            print(f"Page {offset//page_size + 1}: {len(items)} items in {duration:.3f} seconds")
            
            # Each page should load reasonably quickly
            assert duration < 1.0, f"Page load too slow: {duration:.3f} seconds"
        
        print(f"Total items retrieved: {total_retrieved}")
        print(f"Average page load time: {sum(page_times)/len(page_times):.3f} seconds")
        
        # Verify all items were retrieved
        assert total_retrieved == 1000, f"Not all items retrieved: {total_retrieved}/1000"
        
        # Page load times should be consistent (no significant degradation)
        first_page_time = page_times[0]
        last_page_time = page_times[-1]
        time_degradation = last_page_time / first_page_time
        
        assert time_degradation < 3.0, f"Pagination performance degraded too much: {time_degradation:.2f}x"
    
    def test_concurrent_user_simulation(self, service, repository):
        """Simulate concurrent users performing various operations"""
        # Create initial data for multiple users
        user_ids = [f"concurrent_user_{i}" for i in range(10)]
        
        # Create items for each user
        for user_id in user_ids:
            for i in range(50):
                item = ReviewItem(
                    id=str(uuid.uuid4()),
                    content_draft_id=f"concurrent_draft_{user_id}_{i}",
                    founder_id=user_id,
                    content_type="tweet",
                    original_content=f"Concurrent user test content {i}",
                    current_content=f"Concurrent user test content {i}",
                    generation_reason="concurrent_user_test",
                    ai_confidence_score=0.7,
                    review_priority=5
                )
                repository.create_review_item(item)
        
        def simulate_user_activity(user_id):
            """Simulate a user's activity"""
            operations_completed = 0
            
            try:
                # User performs various operations
                for _ in range(20):
                    # Get review queue
                    items = service.get_review_queue(user_id)
                    
                    if items:
                        item = items[0]
                        
                        # Update content
                        success = service.update_content(
                            item.id, user_id,
                            f"Updated by {user_id} at {time.time()}",
                            user_id
                        )
                        
                        if success:
                            operations_completed += 1
                    
                    # Small delay to simulate realistic usage
                    time.sleep(0.01)
                    
            except Exception as e:
                print(f"Error in user {user_id} simulation: {e}")
            
            return operations_completed
        
        # Run simulation
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=len(user_ids)) as executor:
            futures = [executor.submit(simulate_user_activity, user_id) for user_id in user_ids]
            
            total_operations = 0
            for future in as_completed(futures):
                operations = future.result()
                total_operations += operations
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\nConcurrent user simulation completed in {duration:.2f} seconds")
        print(f"Total operations: {total_operations}")
        print(f"Operations per second: {total_operations/duration:.2f}")
        
        # Performance assertions
        assert duration < 60.0, f"Simulation took too long: {duration:.2f} seconds"
        assert total_operations > 100, f"Not enough operations completed: {total_operations}"
        assert total_operations/duration > 10, f"Operations per second too low: {total_operations/duration:.2f}"


class TestResourceUsage:
    """Test resource usage patterns"""
    
    def test_cpu_usage_during_intensive_operations(self, repository):
        """Monitor CPU usage during intensive operations"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        founder_id = "cpu_test_founder"
        
        # Start CPU monitoring
        cpu_percentages = []
        
        def monitor_cpu():
            for _ in range(50):  # Monitor for 5 seconds
                cpu_percent = process.cpu_percent(interval=0.1)
                cpu_percentages.append(cpu_percent)
        
        # Start monitoring in background
        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.start()
        
        # Perform CPU-intensive operations
        start_time = time.time()
        
        for i in range(1000):
            item = ReviewItem(
                id=str(uuid.uuid4()),
                content_draft_id=f"cpu_test_draft_{i}",
                founder_id=founder_id,
                content_type="tweet",
                original_content=f"CPU test content {i}",
                current_content=f"CPU test content {i}",
                generation_reason="cpu_test",
                ai_confidence_score=0.7,
                review_priority=5
            )
            repository.create_review_item(item)
            
            # Perform some updates
            if i % 10 == 0:
                repository.update_review_item(item.id, {"review_priority": 6})
        
        end_time = time.time()
        monitor_thread.join()
        
        duration = end_time - start_time
        avg_cpu = sum(cpu_percentages) / len(cpu_percentages) if cpu_percentages else 0
        max_cpu = max(cpu_percentages) if cpu_percentages else 0
        
        print(f"\nCPU-intensive operations completed in {duration:.2f} seconds")
        print(f"Average CPU usage: {avg_cpu:.1f}%")
        print(f"Maximum CPU usage: {max_cpu:.1f}%")
        
        # CPU usage should be reasonable (not constantly at 100%)
        assert avg_cpu < 80.0, f"Average CPU usage too high: {avg_cpu:.1f}%"
    
    def test_error_recovery_performance(self, service, repository, mock_content_service):
        """Test performance during error conditions"""
        founder_id = "error_recovery_founder"
        
        # Create some items
        item_ids = []
        for i in range(50):
            item = ReviewItem(
                id=str(uuid.uuid4()),
                content_draft_id=f"error_recovery_draft_{i}",
                founder_id=founder_id,
                content_type="tweet",
                original_content=f"Error recovery test content {i}",
                current_content=f"Error recovery test content {i}",
                generation_reason="error_recovery_test",
                ai_confidence_score=0.7,
                review_priority=5
            )
            if repository.create_review_item(item):
                item_ids.append(item.id)
        
        # Test operations with intermittent failures
        start_time = time.time()
        
        successful_operations = 0
        failed_operations = 0
        
        for i, item_id in enumerate(item_ids):
            try:
                # Simulate intermittent failures
                if i % 5 == 0:
                    # Force a failure by using invalid data
                    success = service.update_content(
                        "nonexistent_id", founder_id, "content", "user"
                    )
                    if not success:
                        failed_operations += 1
                else:
                    # Normal operation
                    success = service.update_content(
                        item_id, founder_id, f"Updated content {i}", "user"
                    )
                    if success:
                        successful_operations += 1
                    else:
                        failed_operations += 1
                        
            except Exception as e:
                failed_operations += 1
                print(f"Operation {i} failed: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\nError recovery test completed in {duration:.2f} seconds")
        print(f"Successful operations: {successful_operations}")
        print(f"Failed operations: {failed_operations}")
        print(f"Success rate: {successful_operations/(successful_operations + failed_operations)*100:.1f}%")
        
        # System should handle errors gracefully without major performance impact
        assert duration < 10.0, f"Error recovery took too long: {duration:.2f} seconds"
        assert successful_operations > 0, "No operations succeeded"


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])  # -s to see print statements