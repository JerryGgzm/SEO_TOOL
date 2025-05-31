import logging
from typing import Dict, Any
from datetime import datetime, timezone
from .reporter import ComprehensiveAnalyticsService
from .collector import AnalyticsCollector

logger = logging.getLogger(__name__)

class AnalyticsDashboard:
    """Analytics dashboard"""
    
    def __init__(self, analytics_service: ComprehensiveAnalyticsService):
        self.analytics_service = analytics_service
        self.collector = AnalyticsCollector(analytics_service.data_flow_manager)
    
    async def get_dashboard_data(self, founder_id: str) -> Dict[str, Any]:
        """Get dashboard data"""
        try:
            # Collect real-time metrics
            real_time_metrics = self.collector.collect_real_time_metrics(founder_id)
            
            # Get quick analysis (last 7 days)
            quick_analysis = await self.analytics_service.generate_comprehensive_report(founder_id, 7)
            
            # Get key metrics trends (last 30 days)
            monthly_trends = await self._get_monthly_trends(founder_id)
            
            return {
                'real_time_metrics': real_time_metrics,
                'quick_analysis': {
                    'overall_score': quick_analysis.get('overall_performance_score', 0),
                    'key_insights': quick_analysis.get('comprehensive_insights', [])[:3],
                    'urgent_actions': [r for r in quick_analysis.get('action_recommendations', []) if r.get('priority') == 'high']
                },
                'monthly_trends': monthly_trends,
                'dashboard_updated_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {}
    
    async def _get_monthly_trends(self, founder_id: str) -> Dict[str, Any]:
        """Get monthly trends"""
        try:
            # Get detailed analysis for the last 30 days
            monthly_report = await self.analytics_service.generate_comprehensive_report(founder_id, 30)
            
            return {
                'content_trend': monthly_report.get('content_performance', {}).get('growth_metrics', {}),
                'seo_trend': monthly_report.get('seo_performance', {}).get('optimization_trends', {}),
                'engagement_trend': monthly_report.get('content_performance', {}).get('avg_engagement_rate', 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get monthly trends: {e}")
            return {}