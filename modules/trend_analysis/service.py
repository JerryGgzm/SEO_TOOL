"""TrendAnalysis integration service"""
import asyncio
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timezone
import json

from modules.twitter_api import TwitterAPIClient
from modules.user_profile import UserProfileService
from database import DataFlowManager

from .analyzer import TrendAnalysisEngine
from .models import TrendAnalysisRequest, TrendAnalysisConfig
from .database_adapter import TrendAnalysisDatabaseAdapter

logger = logging.getLogger(__name__)

class TrendAnalysisService:
    """High-level service for trend analysis integration"""
    
    def __init__(self, twitter_client: TwitterAPIClient, 
                 user_service: UserProfileService,
                 data_flow_manager: DataFlowManager,
                 config: TrendAnalysisConfig = None,
                 llm_client=None):
        
        self.twitter_client = twitter_client
        self.user_service = user_service
        self.data_flow_manager = data_flow_manager
        self.config = config or TrendAnalysisConfig()
        
        # Initialize the analysis engine
        self.analysis_engine = TrendAnalysisEngine(
            twitter_client=twitter_client,
            user_service=user_service,
            config=self.config,
            llm_client=llm_client
        )
    
    async def analyze_trends_for_founder(self, founder_id: str, 
                                       custom_request: TrendAnalysisRequest = None) -> List[str]:
        """Analyze trends for a founder"""
        try:
            logger.info(f"Starting trend analysis for founder {founder_id}")
            
            # get user profile and product info
            user_profile = self.user_service.get_user_profile(founder_id)
            if not user_profile:
                logger.warning(f"Founder {founder_id} not found")
                return []
            
            # create analysis request
            if custom_request:
                request = custom_request
            else:
                request = self.analysis_engine._create_default_request(founder_id, user_profile.product_info)
            
            # execute trend analysis
            analyzed_trends = await self.analysis_engine.analyze_trends_for_user(founder_id, request)
            print("analyzed_trends: ", analyzed_trends)
            
            if not analyzed_trends:
                logger.warning(f"No trends analyzed for founder {founder_id}")
                return []
            
            # save analysis results to database
            saved_trend_ids = []
            for trend in analyzed_trends:
                try:
                    # use correct database field names to save trend data
                    saved_trend = self.data_flow_manager.trend_repo.create(
                        founder_id=founder_id,
                        topic_name=trend.trend_name,
                        trend_source_id=getattr(trend, 'trend_source_id', ''),
                        niche_relevance_score=trend.niche_relevance_score,
                        sentiment_scores=trend.sentiment_breakdown.dict() if trend.sentiment_breakdown else {},
                        extracted_pain_points=json.dumps(trend.pain_points) if trend.pain_points else "[]",
                        common_questions=json.dumps(trend.questions) if trend.questions else "[]",
                        discussion_focus_points=json.dumps(trend.keywords[:5]) if trend.keywords else "[]",
                        is_micro_trend=trend.is_micro_trend,
                        trend_velocity_score=trend.velocity_score,
                        trend_potential_score=trend.trend_potential_score,
                        example_tweets_json=json.dumps([]) if not hasattr(trend, 'example_tweets') else json.dumps(trend.example_tweets),
                        expires_at=getattr(trend, 'expires_at', None)
                    )
                    
                    if saved_trend:
                        saved_trend_ids.append(str(saved_trend.id))
                        logger.info(f"Successfully saved trend: {trend.trend_name}")
                    else:
                        logger.warning(f"Failed to save trend: {trend.trend_name}")
                except Exception as e:
                    logger.error(f"Failed to save trend {trend.trend_name}: {e}")
                    continue
            
            logger.info(f"Successfully analyzed and saved {len(saved_trend_ids)} trends")
            return saved_trend_ids
            
        except Exception as e:
            logger.error(f"Founder {founder_id} trend analysis failed: {e}")
            return []
    
    def get_trends_for_content_generation(self, founder_id: str, 
                                        limit: int = 10) -> List[Dict[str, Any]]:
        """Get relevant trends for content generation"""
        return self.data_flow_manager.get_relevant_trends_for_content_generation(
            founder_id, limit
        )
    
    def get_founder_trend_statistics(self, founder_id: str, 
                                   days: int = 30) -> Dict[str, Any]:
        """Get trend analysis statistics for a founder"""
        # This would use your database repositories
        trends = self.data_flow_manager.trend_repo.get_trends_by_founder(
            founder_id, limit=1000, include_expired=True
        )
        
        if not trends:
            return {'total_trends': 0, 'micro_trends': 0}
        
        micro_trend_count = sum(1 for t in trends if t.is_micro_trend)
        avg_relevance = sum(t.niche_relevance_score for t in trends) / len(trends)
        
        # fix time comparison issue
        current_time = datetime.now(timezone.utc)
        
        return {
            'total_trends': len(trends),
            'micro_trends': micro_trend_count,
            'avg_relevance_score': round(avg_relevance, 3),
            'recent_analysis_count': len([t for t in trends if 
                (current_time - t.analyzed_at).days <= days])
        }