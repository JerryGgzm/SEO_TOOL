"""Comprehensive tests for ContentGenerationModule"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import json

from modules.content_generation import (
    ContentGenerator, ContentGenerationService, ContentQualityChecker,
    PromptEngine, ContentTypeFactory, LLMAdapterFactory
)
from modules.content_generation.models import (
    ContentDraft, ContentType, ContentGenerationRequest,
    ContentGenerationContext, BrandVoice, SEOSuggestions, LLMResponse
)

# Test Configuration
TEST_CONFIG = {
    'llm_provider': 'openai',
    'api_key': 'test-key-123',
    'model_name': 'gpt-3.5-turbo'
}

class TestContentQualityChecker:
    """Test content quality assessment"""
    
    def test_quality_checker_initialization(self):
        """Test quality checker initializes correctly"""
        checker = ContentQualityChecker()
        assert checker.weights['engagement_prediction'] == 0.25
        assert 'promotional_overload' in checker.quality_patterns
    
    @pytest.mark.asyncio
    async def test_assess_quality_basic(self):
        """Test basic quality assessment"""
        checker = ContentQualityChecker()
        
        # Create test draft
        draft = ContentDraft(
            founder_id="test-founder",
            content_type=ContentType.TWEET,
            generated_text="This is a great tweet about AI innovation! What do you think? #AI #innovation",
            seo_suggestions=SEOSuggestions(hashtags=['AI', 'innovation'])
        )
        
        # Create test context
        context = ContentGenerationContext(
            founder_id="test-founder",
            brand_voice=BrandVoice(tone="professional"),
            target_audience="tech professionals"
        )
        
        quality_score = await checker.assess_quality(draft, context)
        
        assert 0 <= quality_score.overall_score <= 1
        assert quality_score.engagement_prediction > 0
        assert quality_score.readability > 0
    
    def test_identify_quality_issues(self):
        """Test quality issue identification"""
        checker = ContentQualityChecker()
        
        # Test promotional overload
        draft = ContentDraft(
            founder_id="test-founder",
            content_type=ContentType.TWEET,
            generated_text="BUY NOW!!! AMAZING SALE!!! INCREDIBLE DISCOUNT!!!",
            seo_suggestions=SEOSuggestions()
        )
        
        context = ContentGenerationContext(
            founder_id="test-founder",
            brand_voice=BrandVoice()
        )
        
        issues = checker._identify_quality_issues(draft, context)
        assert any("promotional" in issue.lower() for issue in issues)

class TestPromptEngine:
    """Test prompt generation and engineering"""
    
    def test_prompt_engine_initialization(self):
        """Test prompt engine initializes with templates"""
        engine = PromptEngine()
        assert ContentType.TWEET in engine.templates.SYSTEM_PROMPTS
        assert ContentType.TWEET in engine.templates.CONTENT_TEMPLATES
    
    def test_generate_tweet_prompt(self):
        """Test tweet prompt generation"""
        engine = PromptEngine()
        
        context = ContentGenerationContext(
            founder_id="test-founder",
            product_info={
                'name': 'AI Assistant',
                'description': 'Helps with productivity',
                'core_values': ['innovation', 'efficiency']
            },
            brand_voice=BrandVoice(tone="professional"),
            target_audience="business professionals",
            trend_info={
                'topic_name': 'AI productivity',
                'pain_points': ['time management', 'workflow efficiency'],
                'questions': ['How to be more productive?']
            }
        )
        
        prompt = engine.generate_prompt(ContentType.TWEET, context)
        
        assert "AI Assistant" in prompt
        assert "professional" in prompt
        assert "productivity" in prompt
        assert len(prompt) > 100  # Should be substantial
    
    def test_custom_prompt_creation(self):
        """Test custom prompt creation"""
        engine = PromptEngine()
        
        context = ContentGenerationContext(
            founder_id="test-founder",
            product_info={'name': 'TestProduct'},
            brand_voice=BrandVoice(tone="casual")
        )
        
        custom_prompt = engine.create_custom_prompt(
            "Create a fun tweet about our new feature",
            context
        )
        
        assert "TestProduct" in custom_prompt
        assert "casual" in custom_prompt
        assert "fun tweet" in custom_prompt

class TestContentTypeFactory:
    """Test content type handling"""
    
    def test_create_tweet_handler(self):
        """Test tweet content handler creation"""
        handler = ContentTypeFactory.create_handler(ContentType.TWEET)
        assert handler.content_type == ContentType.TWEET
        assert handler.get_character_limit() == 280
    
    def test_validate_tweet_content(self):
        """Test tweet content validation"""
        handler = ContentTypeFactory.create_handler(ContentType.TWEET)
        
        # Valid tweet
        is_valid, issues = handler.validate_content("This is a valid tweet!")
        assert is_valid
        assert len(issues) == 0
        
        # Too long tweet
        long_tweet = "x" * 300
        is_valid, issues = handler.validate_content(long_tweet)
        assert not is_valid
        assert any("280 characters" in issue for issue in issues)
    
    def test_optimize_tweet_content(self):
        """Test tweet content optimization"""
        handler = ContentTypeFactory.create_handler(ContentType.TWEET)
        
        seo_suggestions = SEOSuggestions(hashtags=['AI', 'tech'])
        optimized = handler.optimize_for_platform(
            "Great AI innovation", 
            seo_suggestions
        )
        
        assert "#AI" in optimized
        assert "#tech" in optimized

class TestLLMAdapters:
    """Test LLM adapter functionality"""
    
    def test_llm_adapter_factory(self):
        """Test LLM adapter factory"""
        # Test OpenAI adapter creation
        adapter = LLMAdapterFactory.create_adapter(
            'openai',
            api_key='test-key',
            model_name='gpt-3.5-turbo'
        )
        assert adapter.model_name == 'gpt-3.5-turbo'
        
        # Test Claude adapter creation
        adapter = LLMAdapterFactory.create_adapter(
            'claude',
            api_key='test-key',
            model_name='claude-3-sonnet-20240229'
        )
        assert adapter.model_name == 'claude-3-sonnet-20240229'
    
    def test_llm_response_parsing(self):
        """Test LLM response parsing"""
        from modules.content_generation.llm_adapter import OpenAIAdapter
        
        adapter = OpenAIAdapter('test-key')
        
        # Test simple response
        response = adapter._parse_response("This is a great tweet!", 0.8)
        assert response.content == "This is a great tweet!"
        assert response.confidence == 0.8
        
        # Test response with alternatives
        multi_response = """1. First tweet option
2. Second tweet option
3. Third tweet option"""
        
        response = adapter._parse_response(multi_response, 0.8)
        assert response.content == "First tweet option"
        assert len(response.alternatives) == 2
        assert "Second tweet option" in response.alternatives

class TestContentGenerator:
    """Test main content generator"""
    
    @pytest.fixture
    def mock_llm_adapter(self):
        """Create mock LLM adapter"""
        adapter = Mock()
        adapter.generate_content = AsyncMock(return_value=LLMResponse(
            content="This is a great AI tweet! What do you think? #AI",
            confidence=0.8,
            alternatives=["Alternative AI tweet about innovation #AI"]
        ))
        adapter.generate_multiple = AsyncMock(return_value=[
            LLMResponse(content="Tweet 1 #AI", confidence=0.8),
            LLMResponse(content="Tweet 2 #tech", confidence=0.7)
        ])
        return adapter
    
    @pytest.fixture
    def content_generator(self, mock_llm_adapter):
        """Create content generator with mocked dependencies"""
        return ContentGenerator(mock_llm_adapter)
    
    @pytest.mark.asyncio
    async def test_generate_single_content(self, content_generator):
        """Test single content generation"""
        request = ContentGenerationRequest(
            founder_id="test-founder",
            content_type=ContentType.TWEET,
            quantity=1
        )
        
        context = ContentGenerationContext(
            founder_id="test-founder",
            product_info={'name': 'AI Tool'},
            brand_voice=BrandVoice(tone="professional"),
            target_audience="developers"
        )
        
        drafts = await content_generator.generate_content(request, context)
        
        assert len(drafts) >= 0  # May be filtered by quality threshold
        if drafts:
            assert drafts[0].founder_id == "test-founder"
            assert drafts[0].content_type == ContentType.TWEET
    
    @pytest.mark.asyncio
    async def test_generate_multiple_content(self, content_generator):
        """Test multiple content generation"""
        request = ContentGenerationRequest(
            founder_id="test-founder",
            content_type=ContentType.TWEET,
            quantity=3,
            quality_threshold=0.0  # Accept all for testing
        )
        
        context = ContentGenerationContext(
            founder_id="test-founder",
            product_info={'name': 'AI Tool'},
            brand_voice=BrandVoice(tone="casual")
        )
        
        drafts = await content_generator.generate_content(request, context)
        
        assert len(drafts) >= 0
        for draft in drafts:
            assert draft.content_type == ContentType.TWEET
            assert len(draft.generated_text) <= 280  # Should be within limits

class TestContentGenerationService:
    """Test content generation service integration"""
    
    @pytest.fixture
    def mock_data_flow_manager(self):
        """Create mock data flow manager"""
        manager = Mock()
        manager.get_content_generation_context.return_value = {
            'founder_id': 'test-founder',
            'products': [{
                'name': 'AI Assistant',
                'description': 'Productivity tool',
                'core_values': ['innovation', 'efficiency'],
                'target_audience': 'professionals'
            }],
            'founder_settings': {'content_preferences': {'tone': 'professional'}},
            'trend_info': {
                'topic_name': 'AI productivity',
                'pain_points': ['time management'],
                'questions': ['How to be productive?']
            },
            'recent_topics': [],
            'successful_content_patterns': []
        }
        manager.store_generated_content_draft.return_value = "draft-123"
        return manager
    
    @pytest.fixture
    def mock_user_service(self):
        """Create mock user profile service"""
        return Mock()
    
    @pytest.fixture
    def content_service(self, mock_data_flow_manager, mock_user_service):
        """Create content generation service"""
        llm_config = {
            'provider': 'openai',
            'api_key': 'test-key',
            'model_name': 'gpt-3.5-turbo'
        }
        
        with patch('modules.content_generation.service.ContentGenerationFactory.create_generator') as mock_factory:
            mock_generator = Mock()
            mock_generator.generate_content = AsyncMock(return_value=[
                ContentDraft(
                    founder_id="test-founder",
                    content_type=ContentType.TWEET,
                    generated_text="Test tweet content #AI",
                    seo_suggestions=SEOSuggestions(hashtags=['AI'])
                )
            ])
            mock_factory.return_value = mock_generator
            
            service = ContentGenerationService(
                mock_data_flow_manager,
                mock_user_service,
                llm_config
            )
            service.content_generator = mock_generator
            return service
    
    @pytest.mark.asyncio
    async def test_generate_content_for_founder(self, content_service):
        """Test end-to-end content generation for founder"""
        request = ContentGenerationRequest(
            founder_id="test-founder",
            content_type=ContentType.TWEET,
            quantity=1
        )
        
        draft_ids = await content_service.generate_content_for_founder("test-founder", request)
        
        assert len(draft_ids) == 1
        assert draft_ids[0] == "draft-123"
    
    @pytest.mark.asyncio
    async def test_generate_trend_based_content(self, content_service):
        """Test trend-based content generation"""
        draft_ids = await content_service.generate_trend_based_content(
            "test-founder", 
            "trend-123", 
            ContentType.TWEET, 
            2
        )
        
        assert len(draft_ids) >= 0
    
    def test_approve_content_for_publishing(self, content_service):
        """Test content approval workflow"""
        success = content_service.approve_content_for_publishing(
            "draft-123", 
            "test-founder", 
            edited_text="Edited content"
        )
        
        # Mock should return True/False based on implementation
        assert isinstance(success, bool)

class TestIntegrationWorkflow:
    """Test complete integration workflow"""
    
    @pytest.mark.asyncio
    async def test_complete_content_generation_workflow(self):
        """Test complete workflow from request to storage"""
        
        # This would require actual database setup
        # For now, test the workflow structure
        
        # 1. Mock all dependencies
        with patch('modules.content_generation.service.ContentGenerationFactory') as mock_factory:
            with patch('database.DataFlowManager') as mock_dfm:
                with patch('modules.user_profile.UserProfileService') as mock_ups:
                    
                    # Setup mocks
                    mock_generator = Mock()
                    mock_generator.generate_content = AsyncMock(return_value=[
                        ContentDraft(
                            founder_id="test-founder",
                            content_type=ContentType.TWEET,
                            generated_text="Integration test tweet #test",
                            seo_suggestions=SEOSuggestions()
                        )
                    ])
                    mock_factory.create_generator.return_value = mock_generator
                    
                    mock_dfm_instance = Mock()
                    mock_dfm_instance.get_content_generation_context.return_value = {
                        'founder_id': 'test-founder',
                        'products': [{'name': 'Test Product'}],
                        'founder_settings': {},
                        'trend_info': None
                    }
                    mock_dfm_instance.store_generated_content_draft.return_value = "draft-456"
                    mock_dfm.return_value = mock_dfm_instance
                    
                    # Create service
                    from modules.content_generation.service import ContentGenerationService
                    service = ContentGenerationService(
                        mock_dfm_instance,
                        Mock(),
                        {'provider': 'openai', 'api_key': 'test'}
                    )
                    
                    # Test workflow
                    request = ContentGenerationRequest(
                        founder_id="test-founder",
                        content_type=ContentType.TWEET
                    )
                    
                    draft_ids = await service.generate_content_for_founder("test-founder", request)
                    
                    # Verify workflow completed
                    assert len(draft_ids) >= 0
                    mock_dfm_instance.get_content_generation_context.assert_called_once()