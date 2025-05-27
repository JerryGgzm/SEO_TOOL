#!/usr/bin/env python3
"""
Trend Analysis Module Demo

This script demonstrates the functionality of the trend analysis module.
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.trend_analysis.sentiment import SentimentAnalyzer
from modules.trend_analysis.data_processor import TweetPreprocessor
from modules.trend_analysis.micro_trends import MicroTrendDetector
from modules.trend_analysis.models import (
    TweetData, ProcessedTweetData, SentimentBreakdown, 
    TrendMetrics, AnalyzedTrend, SentimentLabel
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def demo_sentiment_analysis():
    """Demonstrate sentiment analysis functionality"""
    logger.info("=== Sentiment Analysis Demo ===")
    
    analyzer = SentimentAnalyzer()
    
    test_texts = [
        "I absolutely love this new AI feature! It's incredible and saves so much time.",
        "This broken system is driving me crazy. Nothing works as expected.",
        "The update is okay, nothing special but not bad either.",
        "Excited to see what innovations come next in this space!",
        "Frustrated with the lack of documentation and support."
    ]
    
    for i, text in enumerate(test_texts, 1):
        aggregated_sentiment, individual_sentiments = analyzer.analyze_batch_sentiment([text])
        logger.info(f"Text {i}: {text[:50]}...")
        logger.info(f"  Sentiment: {aggregated_sentiment.dominant_sentiment.value}")
        logger.info(f"  Scores: Pos={aggregated_sentiment.positive_score:.2f}, "
                   f"Neg={aggregated_sentiment.negative_score:.2f}, "
                   f"Neu={aggregated_sentiment.neutral_score:.2f}")
        logger.info(f"  Emotion: {aggregated_sentiment.dominant_emotion.value if aggregated_sentiment.dominant_emotion else 'None'}")
        logger.info(f"  Confidence: {aggregated_sentiment.confidence:.2f}")
        logger.info("")

def demo_text_processing():
    """Demonstrate text processing functionality"""
    logger.info("=== Text Processing Demo ===")
    
    processor = TweetPreprocessor()
    
    sample_tweets = [
        "Just tried the new #AI chatbot and I'm struggling with a bug. Why doesn't it work? Need help! #productivity #startups",
        "Love how this tool boosts my workflow! How can we integrate it with our existing systems? 🚀",
        "The latest update broke everything. When will this be fixed? So frustrating... #fail"
    ]
    
    # Process tweets
    processed_tweets = []
    for tweet_text in sample_tweets:
        # Create mock tweet data with proper datetime
        tweet_data = {
            "tweet_id": f"tweet_{len(processed_tweets)}",
            "text": tweet_text,
            "created_at": datetime.now() - timedelta(hours=len(processed_tweets)),
            "author_id": f"user_{len(processed_tweets)}",
            "public_metrics": {"like_count": 10, "retweet_count": 5}
        }

        processed = processor.batch_process_tweets([tweet_data])
        processed_tweets.append(processed)
    
    # Extract insights
    # return {
    #         'all_keywords': [kw for kw, count in keyword_counts.most_common(50)],
    #         'pain_points': [pp for pp, count in pain_point_counts.most_common(20) if count >= 2],
    #         'questions': list(set(questions))[:20],  # Remove duplicates, limit to 20
    #         'hashtags': [ht for ht, count in hashtag_counts.most_common(30)],
    #         'processed_texts': processed_texts
    #     }
    
    logger.info(f"Keywords extracted: {[tweet['all_keywords'] for tweet in processed_tweets][:10]}")
    logger.info(f"Pain points found: {[tweet['pain_points'] for tweet in processed_tweets][:10]}")
    logger.info(f"Questions identified: {[tweet['questions'] for tweet in processed_tweets][:10]}")
    logger.info(f"Hashtags: {[tweet['hashtags'] for tweet in processed_tweets][:10]}")

def demo_micro_trend_detection():
    """Demonstrate micro-trend detection"""
    logger.info("=== Micro-Trend Detection Demo ===")
    
    detector = MicroTrendDetector()
    
    # Create sample analyzed trends with proper datetime
    sample_trends = []
    trend_names = ["AI Automation", "Remote Work Tools", "Sustainable Tech", "No-Code Platforms"]
    
    for i, name in enumerate(trend_names):
        # create valid sentiment analysis data
        sentiment = SentimentBreakdown(
            positive_score=0.6 + (i * 0.1),
            negative_score=0.2,
            neutral_score=0.2 - (i * 0.05),
            confidence=0.8,
            dominant_sentiment=SentimentLabel.POSITIVE
        )
        
        trend = AnalyzedTrend(
            trend_name=name,
            trend_type="emerging",
            velocity_score=5.0 + i,
            sentiment_breakdown=sentiment,
            niche_relevance_score=0.7 + (i * 0.05),
            trend_potential_score=0.8 + (i * 0.02),
            early_adopter_ratio=0.3 + (i * 0.1),
            engagement_metrics={"avg_engagement": 100 + (i * 20)},
            keywords=[f"keyword_{i}", f"term_{i}"],
            created_at=datetime.now() - timedelta(hours=i)
        )
        sample_trends.append(trend)
    
    # Detect micro-trends
    micro_trends = detector.detect_micro_trends(sample_trends)
    
    logger.info(f"Detected {len(micro_trends)} micro-trends:")
    for trend in micro_trends:
        logger.info(f"  - {trend.trend_name}: velocity={trend.velocity_score:.1f}, "
                   f"potential={trend.trend_potential_score:.2f}")

async def demo_full_analysis():
    """Demonstrate full trend analysis workflow"""
    logger.info("=== Full Analysis Demo ===")
    
    try:
        logger.info("Creating mock trend analysis...")
        
        steps = [
            "Fetching trending topics",
            "Analyzing sentiment patterns", 
            "Extracting keywords and themes",
            "Calculating trend metrics",
            "Identifying opportunities"
        ]
        
        for step in steps:
            logger.info(f"  {step}...")
            await asyncio.sleep(0.5)
        
        logger.info("✅ Mock analysis completed successfully!")

        mock_results = {
            "trends_analyzed": 5,
            "micro_trends_found": 2,
            "avg_sentiment_score": 0.65,
            "top_keywords": ["AI", "automation", "productivity"],
            "opportunities_identified": 3
        }
        
        logger.info("Analysis Results:")
        for key, value in mock_results.items():
            logger.info(f"  {key}: {value}")
            
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

def run_all_demos():
    """Run all demonstration functions"""
    logger.info("Starting Trend Analysis Module Demo")
    logger.info("=" * 50)
    
    try:
        # Run synchronous demos
        demo_sentiment_analysis()
        demo_text_processing()
        demo_micro_trend_detection()
        
        # Run async demo
        logger.info("Running async analysis demo...")
        asyncio.run(demo_full_analysis())
        
        logger.info("=" * 50)
        logger.info("✅ All demos completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    run_all_demos()