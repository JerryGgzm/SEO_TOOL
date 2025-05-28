import pytest
from datetime import datetime, timedelta
from sqlalchemy import func

from database import init_database, get_db_context, DataFlowManager

class TestDatabaseIntegration:
    @pytest.fixture(scope='class')
    def setup_test_db(self):
        """Setup test database using SQLite for integration tests"""
        # Use SQLite in-memory database for integration tests
        test_db_url = 'sqlite:///:memory:'
        init_database(test_db_url, create_tables=True)
        yield
        # Cleanup after tests (SQLite memory DB is automatically cleaned up)
    
    def test_complete_user_journey(self, setup_test_db):
        """Test complete user journey from registration to analytics"""
        
        with get_db_context() as session:
            data_flow = DataFlowManager(session)
            
            # Step 1: Founder registration
            founder_id = data_flow.process_founder_registration({
                'email': 'integration@test.com',
                'hashed_password': 'hash123',
                'settings': {'test_mode': True}
            })
            assert founder_id is not None
            
            # Step 2: Product information
            product_id = data_flow.process_product_information_entry(founder_id, {
                'product_name': 'Test Product',
                'description': 'A product for integration testing',
                'target_audience_description': 'Test users',
                'niche_definition': {'keywords': ['test', 'integration']},
                'core_values': ['testing', 'reliability']  # 改为列表格式
            })
            assert product_id is not None
            
            # Step 3: Store analyzed trends
            trend_ids = data_flow.store_analyzed_trends(founder_id, [{
                'topic_name': '#TestTrend',
                'niche_relevance_score': 0.8,
                'sentiment_scores': {
                    'positive': 0.6,
                    'negative': 0.2,
                    'neutral': 0.2,
                    'dominant_sentiment': 'positive'
                },
                'extracted_pain_points': ['testing complexity', 'setup difficulties'],
                'is_micro_trend': True,
                'trend_potential_score': 0.75
            }])
            assert len(trend_ids) == 1
            
            # Step 4: Generate content
            draft_id = data_flow.store_generated_content_draft({
                'founder_id': founder_id,
                'analyzed_trend_id': trend_ids[0],
                'content_type': 'tweet',
                'generated_text': 'Testing is crucial for reliable software! #TestTrend',
                'seo_suggestions': {'hashtags': ['#TestTrend', '#Testing']}
            })
            assert draft_id is not None
            
            # Step 5: Approve content
            approval_success = data_flow.process_content_review_decision(
                draft_id, founder_id, 'approved'
            )
            assert approval_success is True
            
            # Step 6: Simulate publication
            pub_success = data_flow.record_successful_publication(
                draft_id, 'test_tweet_123456'
            )
            assert pub_success is True
            
            # Step 7: Store analytics
            analytics_success = data_flow.store_post_analytics({
                'posted_tweet_id': 'test_tweet_123456',
                'founder_id': founder_id,
                'impressions': 1500,
                'likes': 50,
                'retweets': 15,
                'replies': 8,
                'posted_at': datetime.now()  # ensure data is committed
            })
            assert analytics_success is True
            
            # ensure data is committed
            session.commit()
            
            # Step 8: Get dashboard data
            dashboard = data_flow.get_analytics_dashboard_data(founder_id)

            # print(f"Dashboard summary: {dashboard.get('summary', {})}")
            
            
            assert dashboard['summary']['total_posts'] >= 1
            assert dashboard['summary']['total_impressions'] >= 1500