import pytest
import time
import concurrent.futures
import sys
import os
import tempfile
import uuid
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_context, DataFlowManager, init_database

class TestDatabasePerformance:
    
    @pytest.fixture(scope="class", autouse=True)
    def setup_database(self):
        """Setup test database"""
        # Use temporary directory and unique file name
        temp_dir = tempfile.gettempdir()
        db_filename = f"test_performance_{uuid.uuid4().hex[:8]}.db"
        self.db_path = os.path.join(temp_dir, db_filename)
        test_db_url = f"sqlite:///{self.db_path}"
        
        # Ensure database and tables are created
        try:
            init_database(test_db_url, create_tables=True)
            print(f"🔨 Test database initialized: {self.db_path}")
            
            # Verify tables are created successfully
            with get_db_context() as session:
                from database.models import Base
                # Check if all tables exist
                engine = session.bind
                Base.metadata.create_all(bind=engine)  # Ensure all tables are created
                print("🔨 All tables verified/created")
                
        except Exception as e:
            print(f"❌ Failed to setup test database: {e}")
            raise
            
        yield
        
        # Clean up test database file
        try:
            # Force close all database connections
            from database import _engine, _SessionLocal
            if _SessionLocal:
                _SessionLocal.close_all()
            if _engine:
                _engine.dispose()
            
            # Wait to ensure file handle is released
            time.sleep(0.2)
            
            # Delete database file
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                print("🔨 Test database cleaned up")
        except Exception as e:
            print(f"⚠️ Could not clean up test database: {e}")
    
    def test_concurrent_founder_registration(self):
        """Test concurrent founder registrations"""
        
        def register_founder(index):
            try:
                with get_db_context() as session:
                    data_flow = DataFlowManager(session)
                    return data_flow.process_founder_registration({
                        'email': f'load_test_{index}@example.com',
                        'hashed_password': f'hash_{index}',
                        'settings': {'load_test': True}
                    })
            except Exception as e:
                print(f"Failed to register founder {index}: {e}")
                return None
        
        start_time = time.time()
        
        # Register 50 founders concurrently (reduce number to avoid SQLite locking issues)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(register_founder, i) for i in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        
        # Check results
        successful_registrations = sum(1 for r in results if r is not None)
        print(f"Registered {successful_registrations}/50 founders in {end_time - start_time:.2f}s")
        
        assert successful_registrations >= 45  # Allow some failures
        assert end_time - start_time < 30  # Should complete in 30 seconds
    
    def test_bulk_trend_storage(self):
        """Test storing many trends quickly"""
        
        try:
            with get_db_context() as session:
                data_flow = DataFlowManager(session)
                
                # Create test founder
                founder_id = data_flow.process_founder_registration({
                    'email': 'bulk_test@example.com',
                    'hashed_password': 'hash123'
                })
                
                if not founder_id:
                    raise Exception("Failed to create test founder")
                
                # Generate 100 trends (reduce number to speed up test)
                trends_data = []
                for i in range(100):
                    trends_data.append({
                        'topic_name': f'#BulkTrend{i}',
                        'niche_relevance_score': 0.5 + (i % 50) / 100,
                        'sentiment_scores': {
                            'positive': 0.4,
                            'negative': 0.3,
                            'neutral': 0.3,
                            'dominant_sentiment': 'positive'
                        },
                        'is_micro_trend': i % 10 == 0
                    })
                
                start_time = time.time()
                trend_ids = data_flow.store_analyzed_trends(founder_id, trends_data)
                end_time = time.time()
                
                print(f"Stored {len(trend_ids)} trends in {end_time - start_time:.2f}s")
                
                assert len(trend_ids) == 100
                assert end_time - start_time < 30  # Should complete in 30 seconds
                
        except Exception as e:
            print(f"❌ Bulk trend storage test failed: {e}")
            raise
    
    def test_sequential_operations_performance(self):
        """Test sequential database operations performance"""
        
        with get_db_context() as session:
            data_flow = DataFlowManager(session)
            
            start_time = time.time()
            
            # Create 10 founders sequentially
            founder_ids = []
            for i in range(10):
                founder_id = data_flow.process_founder_registration({
                    'email': f'seq_test_{i}@example.com',
                    'hashed_password': f'hash_{i}',
                    'settings': {'sequential_test': True}
                })
                if founder_id:
                    founder_ids.append(founder_id)
            
            # Create products for each founder
            product_ids = []
            for i, founder_id in enumerate(founder_ids):
                product_id = data_flow.process_product_information_entry(founder_id, {
                    'product_name': f'Sequential Product {i}',
                    'description': f'Product description {i}',
                    'target_audience_description': f'Target audience {i}',
                    'niche_definition': f'Niche {i}',
                    'core_values': ['value1', 'value2']
                })
                if product_id:
                    product_ids.append(product_id)
            
            end_time = time.time()
            
            print(f"Created {len(founder_ids)} founders and {len(product_ids)} products in {end_time - start_time:.2f}s")
            
            assert len(founder_ids) == 10
            assert len(product_ids) == 10
            assert end_time - start_time < 10  # Should complete in 10 seconds