"""TrendAnalysisModule - Comprehensive Trend Analysis Engine

This module provides advanced trend analysis capabilities including:
1. Trending topic identification and filtering
2. Deep sentiment analysis with emotion detection
3. Pain point and opportunity extraction
4. Micro-trend detection based on velocity and early adopters
5. LLM-powered insight generation
6. Comprehensive data storage and retrieval

Main Components:
- analyzer.py: Main trend analysis engine
- sentiment.py: Advanced sentiment analysis
- micro_trends.py: Micro-trend detection algorithms
- data_processor.py: Text processing and feature extraction
- models.py: Data models and structures
- repository.py: Data persistence layer
"""

from .models import (
    AnalyzedTrend,
    TrendAnalysisRequest,
    TrendAnalysisConfig,
    SentimentBreakdown,
    TrendMetrics,
    ExampleTweet,
    TopicCluster,
    TrendSource,
    SentimentLabel,
    EmotionLabel
)

from .analyzer import TrendAnalysisEngine, LLMInsightExtractor
from .sentiment import SentimentAnalyzer
from .micro_trends import MicroTrendDetector
from .data_processor import TweetPreprocessor
from .repository import TrendAnalysisRepository

__all__ = [
    # Models
    'AnalyzedTrend',
    'TrendAnalysisRequest', 
    'TrendAnalysisConfig',
    'SentimentBreakdown',
    'TrendMetrics',
    'ExampleTweet',
    'TopicCluster',
    'TrendSource',
    'SentimentLabel',
    'EmotionLabel',
    
    # Core components
    'TrendAnalysisEngine',
    'LLMInsightExtractor',
    'SentimentAnalyzer',
    'MicroTrendDetector',
    'TweetPreprocessor',
    'TrendAnalysisRepository'
]