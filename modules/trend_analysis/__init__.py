"""TrendAnalysisModule - Simplified Trending Topics Engine

This module provides simplified trending topics functionality including:
1. Twitter trending topics fetching
2. LLM-powered keyword matching  
3. Simple data storage and retrieval
4. Caching and management

Main Components:
- repository.py: Data persistence layer
- llm_matcher.py: LLM-powered trend matching
- models.py: Data models and structures (simplified)
"""

from .models import (
    SentimentBreakdown,
    SentimentLabel
)

from .repository import TrendAnalysisRepository
from .llm_matcher import LLMTrendMatcher, create_llm_trend_matcher

__all__ = [
    # Models (only what we actually use)
    'SentimentBreakdown',
    'SentimentLabel',
    
    # Core components (simplified)
    'TrendAnalysisRepository',
    'LLMTrendMatcher',
    'create_llm_trend_matcher'
]