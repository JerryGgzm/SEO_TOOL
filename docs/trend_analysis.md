# Trend Analysis Module Usage Guide

## Overview

The TrendAnalysisModule provides comprehensive trend analysis capabilities including sentiment analysis, micro-trend detection, pain point extraction, and LLM-powered insights.

## Quick Start

### 1. Basic Setup

```python
from modules.trend_analysis import TrendAnalysisEngine, TrendAnalysisConfig
from modules.twitter_api import TwitterAPIClient
from modules.user_profile import UserProfileService

# Initialize dependencies
twitter_client = TwitterAPIClient(client_id, client_secret)
user_service = UserProfileService(repository)

# Configure analysis
config = TrendAnalysisConfig(
    max_tweets_per_trend=150,
    use_llm_for_insights=True,
    velocity_threshold=2.0,
    enable_topic_clustering=True
)

# Create analysis engine
engine = TrendAnalysisEngine(
    twitter_client=twitter_client,
    user_service=user_service,
    config=config,
    llm_client=openai_client  # Optional
)
```

### 2. Run Trend Analysis

```python
import asyncio

# Create analysis request
request = TrendAnalysisRequest(
    user_id="user_123",
    focus_keywords=["AI", "automation", "productivity"],
    location_id="1",  # Global trends
    max_trends_to_analyze=10,
    tweet_sample_size=100,
    include_micro_trends=True
)

# Run analysis
analyzed_trends = await engine.analyze_trends_for_user("user_123", request)

# Process results
for trend in analyzed_trends:
    print(f"Trend: {trend.topic_name}")
    print(f"Relevance: {trend.niche_relevance_score:.2f}")
    print(f"Potential: {trend.trend_potential_score:.2f}")
    print(f"Micro-trend: {trend.is_micro_trend}")
    print(f"Sentiment: {trend.overall_sentiment.dominant_sentiment}")
    print(f"Pain points: {trend.extracted_pain_points}")
    print("---")
```

## Core Components

### Sentiment Analysis

```python
from modules.trend_analysis import SentimentAnalyzer

analyzer = SentimentAnalyzer()

# Analyze single text
sentiment = analyzer.analyze_text_sentiment("I love this new feature!")
print(f"Sentiment: {sentiment.dominant_sentiment}")
print(f"Confidence: {sentiment.confidence}")
print(f"Emotion: {sentiment.dominant_emotion}")

# Analyze batch of texts
texts = ["Great product!", "Terrible experience", "It's okay"]
aggregated, individual = analyzer.analyze_batch_sentiment(texts)
```

### Text Processing

```python
from modules.trend_analysis import TweetPreprocessor

processor = TweetPreprocessor()

# Process single tweet
text = "Check out this amazing #AI tool! https://example.com @user"
cleaned = processor.clean_tweet_text(text)
keywords = processor.extract_keywords(text)
pain_points = processor.extract_pain_point_indicators(text)
questions = processor.extract_questions(text)

# Batch processing
tweets = [{"text": "tweet 1"}, {"text": "tweet 2"}]
results = processor.batch_process_tweets(tweets)
```

### Micro-Trend Detection

```python
from modules.trend_analysis import MicroTrendDetector

detector = MicroTrendDetector()

# Calculate trend velocity
velocity = detector.calculate_trend_velocity(tweets, 24.0)

# Analyze early adopters
early_adopter_ratio = detector.analyze_early_adopters(tweets)

# Calculate overall potential
potential = detector.calculate_trend_potential_score(
    velocity_score=velocity,
    early_adopter_ratio=early_adopter_ratio,
    engagement_metrics={'avg_engagement_rate': 0.05},
    relevance_score=0.8
)
```

## Configuration Options

### Analysis Configuration

```python
config = TrendAnalysisConfig(
    # Sampling parameters
    max_tweets_per_trend=200,
    min_engagement_threshold=1,
    analysis_time_window_hours=24.0,
    
    # Relevance scoring weights
    keyword_match_weight=0.4,
    engagement_weight=0.3,
    recency_weight=0.3,
    
    # Micro-trend detection
    velocity_threshold=2.0,
    min_tweet_volume=50,
    early_adopter_threshold=0.2,
    
    # LLM integration
    use_llm_for_insights=True,
    llm_model_name="gpt-3.5-turbo",
    max_tokens_per_llm_call=1000
)
```

### Request Parameters

```python
request = TrendAnalysisRequest(
    user_id="user_123",
    focus_keywords=["keyword1", "keyword2"],
    location_id="23424977",  # US trends
    max_trends_to_analyze=15,
    tweet_sample_size=150,
    include_micro_trends=True,
    sentiment_analysis_depth="advanced"
)
```

## Data Models

### AnalyzedTrend Structure

```python
{
    "id": "trend_user123_1234567890_hash",
    "user_id": "user_123",
    "topic_name": "#AI",
    "topic_keywords": ["artificial", "intelligence", "machine", "learning"],
    "niche_relevance_score": 0.85,
    "trend_potential_score": 0.72,
    "is_micro_trend": true,
    
    "overall_sentiment": {
        "positive_score": 0.6,
        "negative_score": 0.2,
        "neutral_score": 0.2,
        "dominant_sentiment": "positive",
        "dominant_emotion": "joy",
        "confidence": 0.8
    },
    
    "extracted_pain_points": [
        "difficulty integrating AI tools",
        "lack of clear documentation",
        "high implementation costs"
    ],
    
    "key_opportunities": [
        "simplified AI integration platform",
        "better developer documentation",
        "cost-effective AI solutions for SMBs"
    ],
    
    "metrics": {
        "tweet_volume": 150,
        "engagement_volume": 2500,
        "avg_engagement_rate": 16.67,
        "unique_users": 120,
        "velocity_score": 25.5
    }
}
```

## API Usage

### Analyze Trends

```bash
POST /api/trends/analyze
{
    "focus_keywords": ["AI", "automation"],
    "location_id": "1",
    "max_trends_to_analyze": 10,
    "include_micro_trends": true
}
```

### Get Latest Trends

```bash
GET /api/trends/latest?limit=10&include_expired=false
```

### Get Micro-Trends

```bash
GET /api/trends/micro-trends?limit=5
```

### Search Trends

```bash
GET /api/trends/search?keywords=AI,machine%20learning&limit=10
```

## Best Practices

### 1. Keyword Selection

```python
# Good: Specific, relevant keywords
focus_keywords = ["machine learning", "AI automation", "productivity tools"]

# Avoid: Too broad or unrelated
focus_keywords = ["technology", "business", "social media"]
```

### 2. Analysis Frequency

```python
# Recommended: Run analysis 2-3 times per day
# Too frequent: Every hour (rate limiting issues)
# Too infrequent: Once per week (miss fast-moving trends)
```

### 3. LLM Integration

```python
# Configure LLM for better insights
config = TrendAnalysisConfig(
    use_llm_for_insights=True,
    llm_model_name="gpt-4",  # Better quality
    max_tokens_per_llm_call=1500  # More detailed analysis
)
```

### 4. Result Filtering

```python
# Filter high-quality trends
quality_trends = [
    trend for trend in analyzed_trends
    if trend.confidence_score > 0.7
    and trend.niche_relevance_score > 0.5
    and trend.metrics.tweet_volume > 20
]
```

## Troubleshooting

### Common Issues

1. **Low Relevance Scores**
   - Solution: Refine focus keywords to be more specific
   - Check: Ensure keywords match your niche accurately

2. **No Micro-Trends Detected**
   - Solution: Lower velocity_threshold in config
   - Check: Ensure sufficient tweet sample size

3. **Poor Sentiment Analysis**
   - Solution: Enable emotion detection and use advanced depth
   - Check: Verify tweet quality and language

4. **LLM Insights Not Generated**
   - Solution: Check API key configuration and rate limits
   - Check: Verify model availability and permissions

### Performance Optimization

```python
# Optimize for speed
config = TrendAnalysisConfig(
    max_tweets_per_trend=100,  # Reduce sample size
    enable_topic_clustering=False,  # Disable heavy processing
    use_llm_for_insights=False  # Skip LLM calls
)

# Optimize for quality
config = TrendAnalysisConfig(
    max_tweets_per_trend=300,  # Larger sample
    sentiment_analysis_depth="advanced",
    use_llm_for_insights=True,
    enable_topic_clustering=True
)
```

This module provides the foundation for intelligent trend analysis that powers content generation and marketing automation in the Ideation system.

