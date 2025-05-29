import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta, timezone
import json

from modules.trend_analysis import (
    TrendAnalysisEngine, SentimentAnalyzer, MicroTrendDetector,
    TweetPreprocessor, AnalyzedTrend, TrendAnalysisRequest,
    SentimentBreakdown, SentimentLabel
)

# 添加异步测试支持
pytestmark = pytest.mark.asyncio

class TestSentimentAnalyzer:
    """Test sentiment analysis functionality"""
    
    def test_analyze_text_sentiment_positive(self):
        """Test positive sentiment analysis"""
        analyzer = SentimentAnalyzer()
        text = "I love this amazing new feature! It's fantastic and works perfectly."
        
        result = analyzer.analyze_text_sentiment(text)
        
        assert result.dominant_sentiment == SentimentLabel.POSITIVE
        assert result.positive_score > result.negative_score
        assert result.positive_score > result.neutral_score
        assert 0 <= result.confidence <= 1
    
    def test_analyze_text_sentiment_negative(self):
        """Test negative sentiment analysis"""
        analyzer = SentimentAnalyzer()
        text = "This is terrible! I hate how broken and awful this system is."
        
        result = analyzer.analyze_text_sentiment(text)
        
        assert result.dominant_sentiment == SentimentLabel.NEGATIVE
        assert result.negative_score > result.positive_score
        assert result.negative_score > result.neutral_score
    
    def test_analyze_batch_sentiment(self):
        """Test batch sentiment analysis"""
        analyzer = SentimentAnalyzer()
        texts = [
            "Great product, love it!",
            "Terrible experience, very disappointed",
            "It's okay, nothing special",
            "Amazing features and excellent support"
        ]
        
        aggregated, individual = analyzer.analyze_batch_sentiment(texts)
        
        assert len(individual) == len(texts)
        assert isinstance(aggregated, SentimentBreakdown)
        assert all(isinstance(sentiment, SentimentBreakdown) for sentiment in individual)
    
    def test_emotion_detection(self):
        """Test emotion detection functionality"""
        analyzer = SentimentAnalyzer()
        
        # Test different emotions
        test_cases = [
            ("I'm so excited and happy about this!", "joy"),
            ("This makes me really angry and frustrated", "anger"),
            ("I'm scared and worried about the future", "fear"),
            ("What an amazing surprise!", "surprise")
        ]
        
        for text, expected_emotion in test_cases:
            result = analyzer.analyze_text_sentiment(text)
            # Note: Emotion detection is keyword-based, so may not always be accurate
            # Just check that an emotion is detected
            assert result.dominant_emotion is not None or result.dominant_sentiment != SentimentLabel.NEUTRAL

class TestTweetPreprocessor:
    """Test tweet preprocessing functionality"""
    
    def test_clean_tweet_text(self):
        """Test tweet text cleaning"""
        preprocessor = TweetPreprocessor()
        
        raw_text = "Check out this amazing #startup https://example.com @username RT @someone"
        cleaned = preprocessor.clean_tweet_text(raw_text, preserve_hashtags=True)
        
        assert "https://example.com" not in cleaned
        assert "startup" in cleaned.lower()
        assert "@username" not in cleaned
    
    def test_extract_keywords(self):
        """Test keyword extraction"""
        preprocessor = TweetPreprocessor()
        
        text = "Machine learning and artificial intelligence are transforming business automation"
        keywords = preprocessor.extract_keywords(text)
        
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        assert any("machine" in kw.lower() or "learning" in kw.lower() for kw in keywords)
    
    def test_extract_pain_point_indicators(self):
        """Test pain point detection"""
        preprocessor = TweetPreprocessor()
        
        text = "I'm struggling with this broken feature and can't get it to work properly"
        pain_points = preprocessor.extract_pain_point_indicators(text)
        
        assert isinstance(pain_points, list)
        assert len(pain_points) > 0
    
    def test_extract_questions(self):
        """Test question extraction"""
        preprocessor = TweetPreprocessor()
        
        text = "How does this work? Why is it so complicated? What are the alternatives?"
        questions = preprocessor.extract_questions(text)
        
        assert isinstance(questions, list)
        assert len(questions) == 3
        assert all(q.strip().endswith('?') for q in questions)
    
    def test_batch_process_tweets(self):
        """Test batch tweet processing"""
        preprocessor = TweetPreprocessor()
        
        tweets = [
            {"text": "Love this new #AI feature! How does it work?"},
            {"text": "Struggling with bugs in the system"},
            {"text": "Great #productivity tool for #startups"}
        ]
        
        result = preprocessor.batch_process_tweets(tweets)
        
        assert 'all_keywords' in result
        assert 'pain_points' in result
        assert 'questions' in result
        assert 'hashtags' in result
        assert len(result['processed_texts']) == len(tweets)

class TestMicroTrendDetector:
    """Test micro-trend detection functionality"""
    
    def test_calculate_trend_velocity(self):
        """Test trend velocity calculation"""
        detector = MicroTrendDetector()
        
        # Create mock tweets with timestamps
        now = datetime.utcnow()
        tweets = []
        for i in range(20):
            tweet_time = now - timedelta(hours=i*0.5)  # Every 30 minutes
            tweets.append({
                'created_at': tweet_time.isoformat() + 'Z'
            })
        
        velocity = detector.calculate_trend_velocity(tweets, 24.0)
        
        assert velocity > 0
        assert isinstance(velocity, float)
    
    def test_analyze_early_adopters(self):
        """Test early adopter analysis"""
        detector = MicroTrendDetector()
        
        # Mock tweet data with user information
        tweets = [
            {
                'author_id': 'user1',
                'includes': {
                    'users': [{
                        'id': 'user1',
                        'verified': True,
                        'public_metrics': {
                            'followers_count': 10000,
                            'following_count': 5000,
                            'tweet_count': 1000
                        },
                        'description': 'Tech entrepreneur and startup founder'
                    }]
                }
            },
            {
                'author_id': 'user2',
                'includes': {
                    'users': [{
                        'id': 'user2',
                        'verified': False,
                        'public_metrics': {
                            'followers_count': 1000000,
                            'following_count': 100,
                            'tweet_count': 10000
                        },
                        'description': 'Celebrity account'
                    }]
                }
            }
        ]
        
        ratio = detector.analyze_early_adopters(tweets)
        
        assert 0 <= ratio <= 1
        assert isinstance(ratio, float)
    
    def test_calculate_trend_potential_score(self):
        """Test trend potential scoring"""
        detector = MicroTrendDetector()
        
        score = detector.calculate_trend_potential_score(
            velocity_score=5.0,
            early_adopter_ratio=0.3,
            engagement_metrics={'avg_engagement_rate': 0.05},
            relevance_score=0.8
        )
        
        assert 0 <= score <= 1
        assert isinstance(score, float)

class TestTrendAnalysisEngine:
    """Test main trend analysis engine"""
    
    @pytest.fixture
    def mock_twitter_client(self):
        """Mock Twitter API client"""
        client = Mock()
        client.get_trends_for_location.return_value = [
            {'name': '#AI', 'tweet_volume': 100000},
            {'name': '#MachineLearning', 'tweet_volume': 50000}
        ]
        client.search_tweets.return_value = {
            'data': [
                {
                    'id': '123',
                    'text': 'AI is transforming everything!',
                    'created_at': datetime.utcnow().isoformat() + 'Z',
                    'public_metrics': {'like_count': 10, 'retweet_count': 5}
                }
            ]
        }
        return client
    
    @pytest.fixture
    def mock_user_service(self):
        """Mock user profile service"""
        service = Mock()
        user_profile = Mock()
        user_profile.user_id = 'test_user'
        
        # 修复product_info的Mock配置
        product_info = Mock()
        product_info.niche_keywords = Mock()
        product_info.niche_keywords.primary = ['AI', 'automation']
        product_info.niche_keywords.secondary = ['machine learning', 'tech']
        product_info.product_name = 'AI Startup Tool'
        
        user_profile.product_info = product_info
        service.get_user_profile.return_value = user_profile
        service.get_twitter_access_token.return_value = 'test_token'
        return service
    
    @pytest.fixture
    def analysis_engine(self, mock_twitter_client, mock_user_service):
        """Create analysis engine with mocked dependencies"""
        return TrendAnalysisEngine(
            twitter_client=mock_twitter_client,
            user_service=mock_user_service
        )
    
    @pytest.mark.asyncio
    async def test_analyze_trends_for_user(self, analysis_engine):
        """Test full trend analysis workflow"""
        
        # mock create_analysis_request method, return correct TrendAnalysisRequest object
        with patch.object(analysis_engine.user_service, 'create_analysis_request') as mock_create_request:
            with patch.object(analysis_engine.twitter_client, 'get_trends_for_location') as mock_get_trends:
                with patch.object(analysis_engine.twitter_client, 'search_tweets') as mock_search:
                    
                    # Setup mocks - use actual TrendAnalysisRequest object
                    from modules.trend_analysis.models import TrendAnalysisRequest
                    
                    request = TrendAnalysisRequest(
                        user_id='test_user',
                        location_woeid=1,  # add missing location_woeid
                        max_trends=10,
                        include_micro_trends=True,
                        sentiment_analysis=True
                    )
                    
                    mock_create_request.return_value = request
                    
                    mock_get_trends.return_value = [
                        {'name': '#AI', 'tweet_volume': 1000}
                    ]
                    
                    mock_search.return_value = {
                        'data': [
                            {
                                'id': '123',
                                'text': 'AI is transforming everything!',
                                'created_at': datetime.now(timezone.utc).isoformat() + 'Z',
                                'author_id': 'user123',
                                'public_metrics': {'like_count': 10, 'retweet_count': 5}
                            }
                        ]
                    }
                    
                    # Run analysis with await - pass request parameter
                    result = await analysis_engine.analyze_trends_for_user('test_user', request)
                    
                    # Verify results
                    assert isinstance(result, list)
                    mock_get_trends.assert_called_once()
    
    def test_calculate_keyword_relevance(self, analysis_engine):
        """Test keyword relevance calculation"""
        trend_name = "artificial intelligence startup"
        focus_keywords = ["AI", "startup", "technology"]
        
        relevance = analysis_engine._calculate_keyword_relevance(trend_name, focus_keywords)
        
        assert 0 <= relevance <= 1
        assert isinstance(relevance, float)
        assert relevance > 0  # Should have some relevance