"""Integration test for TrendAnalysisModule"""
import pytest
import asyncio
from unittest.mock import Mock, patch

from database import init_database, get_db_context, DataFlowManager
from modules.trend_analysis.service import TrendAnalysisService
from modules.trend_analysis.models import TrendAnalysisConfig

class TestTrendAnalysisIntegration:
    
    @pytest.fixture(scope='class')
    def setup_test_db(self):
        """Setup test database"""
        test_db_url = 'sqlite:///:memory:'
        init_database(test_db_url, create_tables=True)
        yield
    
    @pytest.fixture
    def mock_twitter_client(self):
        """Mock Twitter client"""
        client = Mock()
        client.get_trends_for_location = Mock(return_value=[
            {'name': '#AI', 'tweet_volume': 1000, 'id': '1'}
        ])
        client.search_tweets = Mock(return_value={
            'data': [
                {
                    'id': '123',
                    'text': 'AI is transforming everything!',
                    'created_at': '2024-01-01T00:00:00.000Z',
                    'author_id': 'user123',
                    'public_metrics': {'like_count': 10, 'retweet_count': 5}
                }
            ]
        })
        return client
    
    @pytest.fixture 
    def mock_user_service(self):
        """Mock user service"""
        service = Mock()
        service.get_twitter_access_token = Mock(return_value='test_token')
        
        # Create user profile Mock
        user_profile = Mock()
        user_profile.user_id = 'test_user'
        
        # Create product info Mock
        product_info = Mock()
        product_info.niche_keywords = Mock()
        product_info.niche_keywords.primary = ['AI', 'automation']
        product_info.niche_keywords.secondary = ['machine learning', 'tech']
        product_info.product_name = 'AI Startup Tool'
        
        user_profile.product_info = product_info
        service.get_user_profile = Mock(return_value=user_profile)
        
        return service
    
    @pytest.mark.asyncio
    async def test_complete_trend_analysis_flow(self, setup_test_db, 
                                               mock_twitter_client, 
                                               mock_user_service):
        """Test complete trend analysis integration"""
        
        with get_db_context() as session:
            data_flow = DataFlowManager(session)
            
            # Create test founder
            founder_id = data_flow.process_founder_registration({
                'email': 'test@example.com',
                'hashed_password': 'hash123'
            })
            
            # Add product info
            data_flow.process_product_information_entry(founder_id, {
                'product_name': 'AI Tool',
                'description': 'An AI productivity tool',
                'target_audience_description': 'Developers',
                'niche_definition': {'keywords': ['AI', 'productivity']},
                'core_values': ['innovation', 'efficiency']
            })
            
            # Add other mocked methods as needed
            user_profile = mock_user_service.get_user_profile.return_value
            user_profile.user_id = founder_id
            
            # Create trend analysis service
            config = TrendAnalysisConfig(max_trends_to_analyze=2)
            service = TrendAnalysisService(
                twitter_client=mock_twitter_client,
                user_service=mock_user_service,
                data_flow_manager=data_flow,
                config=config
            )
            
            # Run trend analysis
            trend_ids = await service.analyze_trends_for_founder(founder_id)
            print(f"Trend IDs: {trend_ids}")
            
            # Verify results
            assert len(trend_ids) > 0
            
            # Verify trends are stored in database
            trends = data_flow.get_relevant_trends_for_content_generation(founder_id)
            assert len(trends) > 0
            assert trends[0]['topic_name'] == '#AI'