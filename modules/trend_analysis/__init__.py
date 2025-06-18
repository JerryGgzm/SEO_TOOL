"""TrendAnalysisModule - Gemini-Powered Internet Trending Topics Engine

This module provides advanced trending topics functionality including:
1. Google Gemini LLM-powered analysis
2. Google Custom Search API integration
3. Two-stage trend analysis (inference + execution)
4. Keyword-based internet search for latest topics
5. Traditional Twitter trending topics (legacy)
6. Data storage and retrieval
7. Caching and management

Main Components:
- gemini_analyzer.py: Gemini LLM integration for trend analysis
- web_search_tool.py: Google Custom Search API integration
- repository.py: Data persistence layer (legacy)
- llm_matcher.py: LLM-powered trend matching (legacy)
- models.py: Data models and structures
"""

from .models import (
    SentimentBreakdown,
    SentimentLabel
)

from .repository import TrendAnalysisRepository
from .llm_matcher import LLMTrendMatcher, create_llm_trend_matcher

# New Gemini-powered components
from .gemini_analyzer import (
    GeminiTrendAnalyzer,
    create_gemini_trend_analyzer,
    quick_analyze_trending_topics
)

from .web_search_tool import (
    get_trending_topics,
    WebSearchTrendAnalyzer
)

__all__ = [
    # Models
    'SentimentBreakdown',
    'SentimentLabel',
    
    # Legacy components
    'TrendAnalysisRepository',
    'LLMTrendMatcher',
    'create_llm_trend_matcher',
    
    # New Gemini-powered components
    'GeminiTrendAnalyzer',
    'create_gemini_trend_analyzer',
    'quick_analyze_trending_topics',
    'get_trending_topics',
    'WebSearchTrendAnalyzer'
]