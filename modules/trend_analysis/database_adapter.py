"""Adapter to bridge TrendAnalysis models with database models"""
from typing import Dict, Any, List
from datetime import datetime
import json

from .models import AnalyzedTrend as TrendAnalysisResult
from database.models import AnalyzedTrend as DatabaseTrend

class TrendAnalysisDatabaseAdapter:
    """Converts between TrendAnalysis models and Database models"""
    
    @staticmethod
    def to_database_format(trend_analysis: TrendAnalysisResult) -> Dict[str, Any]:
        """Convert TrendAnalysis model to database format"""
        return {
            'founder_id': trend_analysis.user_id,
            'topic_name': trend_analysis.trend_name,
            'trend_source_id': trend_analysis.trend_source_id,
            'niche_relevance_score': trend_analysis.niche_relevance_score,
            'sentiment_scores': trend_analysis.sentiment_breakdown.dict(),
            'extracted_pain_points': json.dumps(trend_analysis.pain_points),
            'common_questions': json.dumps(trend_analysis.questions),
            'discussion_focus_points': json.dumps(trend_analysis.keywords),
            'is_micro_trend': trend_analysis.is_micro_trend,
            'trend_velocity_score': trend_analysis.velocity_score,
            'trend_potential_score': trend_analysis.trend_potential_score,
            'example_tweets_json': [tweet.dict() for tweet in trend_analysis.example_tweets],
            'expires_at': datetime.utcnow() + timedelta(days=30)  # Default expiration
        }
    
    @staticmethod
    def batch_to_database_format(trends: List[TrendAnalysisResult]) -> List[Dict[str, Any]]:
        """Convert multiple trends to database format"""
        return [
            TrendAnalysisDatabaseAdapter.to_database_format(trend) 
            for trend in trends
        ]