import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone
from database import DataFlowManager
from modules.user_profile import UserProfileService
from modules.seo.service_integration import SEOService
from .processor import ContentPerformanceAnalyzer, SEOPerformanceAnalyzer
from .collector import AnalyticsCollector

logger = logging.getLogger(__name__)

class TrendAnalysisReporter:
    """Trend analysis reporter"""
    
    def __init__(self, data_flow_manager: DataFlowManager):
        self.data_flow_manager = data_flow_manager
    
    def generate_trend_report(self, founder_id: str, days: int = 30) -> Dict[str, Any]:
        """Generate trend report"""
        try:
            # Get trend data
            trends = self.data_flow_manager.trend_repo.get_trends_by_founder(founder_id, limit=50)
            
            if not trends:
                return self._empty_trend_report()
            
            # Analyze trend data
            report = {
                'total_trends_analyzed': len(trends),
                'micro_trends_identified': sum(1 for t in trends if t.is_micro_trend),
                'avg_relevance_score': self._calculate_avg_relevance(trends),
                'trend_categories': self._categorize_trends(trends),
                'top_performing_trends': self._get_top_performing_trends(trends),
                'trend_success_rate': self._calculate_trend_success_rate(trends),
                'emerging_opportunities': self._identify_emerging_opportunities(trends),
                'trend_utilization_rate': self._calculate_trend_utilization(founder_id, trends)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Trend report generation failed: {e}")
            return self._empty_trend_report()
    
    def _calculate_avg_relevance(self, trends: List) -> float:
        """Calculate average relevance score"""
        relevance_scores = [t.niche_relevance_score for t in trends if t.niche_relevance_score]
        return sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
    
    def _categorize_trends(self, trends: List) -> Dict[str, int]:
        """Categorize trends"""
        categories = {
            'high_relevance': 0,  # relevance > 0.7
            'medium_relevance': 0,  # relevance 0.4-0.7
            'low_relevance': 0,  # relevance < 0.4
            'micro_trends': 0,
            'viral_potential': 0  # trend potential > 0.8
        }
        
        for trend in trends:
            relevance = trend.niche_relevance_score or 0
            
            if relevance > 0.7:
                categories['high_relevance'] += 1
            elif relevance > 0.4:
                categories['medium_relevance'] += 1
            else:
                categories['low_relevance'] += 1
            
            if trend.is_micro_trend:
                categories['micro_trends'] += 1
            
            if trend.trend_potential_score and trend.trend_potential_score > 0.8:
                categories['viral_potential'] += 1
        
        return categories
    
    def _get_top_performing_trends(self, trends: List) -> List[Dict[str, Any]]:
        """Get top performing trends"""
        # Sort by potential score
        sorted_trends = sorted(
            trends,
            key=lambda t: (t.trend_potential_score or 0, t.niche_relevance_score or 0),
            reverse=True
        )
        
        top_trends = []
        for trend in sorted_trends[:5]:
            top_trends.append({
                'topic_name': trend.topic_name,
                'relevance_score': trend.niche_relevance_score,
                'potential_score': trend.trend_potential_score,
                'is_micro_trend': trend.is_micro_trend,
                'analyzed_at': trend.analyzed_at.isoformat() if trend.analyzed_at else None
            })
        
        return top_trends
    
    def _calculate_trend_success_rate(self, trends: List) -> float:
        """Calculate trend success rate"""
        if not trends:
            return 0.0
        
        # Success defined as relevance > 0.6 and potential > 0.6
        successful_trends = sum(1 for t in trends if 
                              (t.niche_relevance_score or 0) > 0.6 and 
                              (t.trend_potential_score or 0) > 0.6)
        
        return successful_trends / len(trends)
    
    def _identify_emerging_opportunities(self, trends: List) -> List[str]:
        """Identify emerging opportunities"""
        opportunities = []
        
        # Find high potential but medium relevance trends
        emerging_trends = [
            t for t in trends if
            (t.trend_potential_score or 0) > 0.7 and
            0.4 <= (t.niche_relevance_score or 0) <= 0.7
        ]
        
        if emerging_trends:
            opportunities.append(f"Found {len(emerging_trends)} trends with high potential but medium relevance - consider expansion opportunities")
        
        # Find micro-trend opportunities
        micro_trends = [t for t in trends if t.is_micro_trend]
        if len(micro_trends) > len(trends) * 0.2:
            opportunities.append("High micro-trend detection rate - good for early adoption strategy")
        
        return opportunities
    
    def _calculate_trend_utilization(self, founder_id: str, trends: List) -> float:
        """Calculate trend utilization rate"""
        try:
            # Get content count based on trends
            trend_ids = [t.id for t in trends]
            
            content_count = self.data_flow_manager.db_session.query(
                self.data_flow_manager.content_repo.model_class
            ).filter(
                self.data_flow_manager.content_repo.model_class.founder_id == founder_id,
                self.data_flow_manager.content_repo.model_class.analyzed_trend_id.in_(trend_ids)
            ).count()
            
            return content_count / len(trends) if trends else 0.0
            
        except Exception as e:
            logger.error(f"Failed to calculate trend utilization rate: {e}")
            return 0.0
    
    def _empty_trend_report(self) -> Dict[str, Any]:
        """Return empty trend report"""
        return {
            'total_trends_analyzed': 0,
            'micro_trends_identified': 0,
            'avg_relevance_score': 0.0,
            'trend_categories': {},
            'top_performing_trends': [],
            'trend_success_rate': 0.0,
            'emerging_opportunities': [],
            'trend_utilization_rate': 0.0
        }

class ComprehensiveAnalyticsService:
    """Comprehensive analytics service"""
    
    def __init__(self, data_flow_manager: DataFlowManager, 
                 user_profile_service: UserProfileService,
                 seo_service: SEOService):
        self.data_flow_manager = data_flow_manager
        self.user_profile_service = user_profile_service
        self.seo_service = seo_service
        
        # Initialize analyzers
        self.content_analyzer = ContentPerformanceAnalyzer(data_flow_manager)
        self.seo_analyzer = SEOPerformanceAnalyzer(data_flow_manager, seo_service)
        self.trend_reporter = TrendAnalysisReporter(data_flow_manager)
    
    async def generate_comprehensive_report(self, founder_id: str, 
                                          days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        try:
            logger.info(f"Generating comprehensive analysis report for founder {founder_id}")
            
            # Execute all analyses in parallel
            content_analysis, seo_analysis, trend_analysis = await asyncio.gather(
                asyncio.to_thread(self.content_analyzer.analyze_content_performance, founder_id, days),
                asyncio.to_thread(self.seo_analyzer.analyze_seo_performance, founder_id, days),
                asyncio.to_thread(self.trend_reporter.generate_trend_report, founder_id, days),
                return_exceptions=True
            )
            
            # Handle possible exceptions
            if isinstance(content_analysis, Exception):
                logger.error(f"Content analysis failed: {content_analysis}")
                content_analysis = {}
            
            if isinstance(seo_analysis, Exception):
                logger.error(f"SEO analysis failed: {seo_analysis}")
                seo_analysis = {}
            
            if isinstance(trend_analysis, Exception):
                logger.error(f"Trend analysis failed: {trend_analysis}")
                trend_analysis = {}
            
            # Generate comprehensive insights
            comprehensive_insights = self._generate_comprehensive_insights(
                content_analysis, seo_analysis, trend_analysis
            )
            
            # Generate action recommendations
            action_recommendations = self._generate_action_recommendations(
                content_analysis, seo_analysis, trend_analysis
            )
            
            # Calculate overall performance score
            overall_score = self._calculate_overall_performance_score(
                content_analysis, seo_analysis, trend_analysis
            )
            
            report = {
                'report_generated_at': datetime.now(timezone.utc).isoformat(),
                'analysis_period_days': days,
                'founder_id': founder_id,
                'overall_performance_score': overall_score,
                'content_performance': content_analysis,
                'seo_performance': seo_analysis,
                'trend_analysis': trend_analysis,
                'comprehensive_insights': comprehensive_insights,
                'action_recommendations': action_recommendations,
                'next_review_date': (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
            }
            
            # Store report to database
            self._store_analytics_report(founder_id, report)
            
            logger.info(f"Comprehensive analysis report generation completed")
            return report
            
        except Exception as e:
            logger.error(f"Comprehensive analysis report generation failed: {e}")
            return self._empty_comprehensive_report(founder_id, days)
    
    def _generate_comprehensive_insights(self, content_analysis: Dict, 
                                       seo_analysis: Dict, 
                                       trend_analysis: Dict) -> List[str]:
        """Generate comprehensive insights"""
        insights = []
        
        # Content performance insights
        content_growth = content_analysis.get('growth_metrics', {})
        if content_growth.get('trend') == 'improving':
            insights.append(f"Content engagement is improving with {content_growth.get('growth_rate', 0):.1f}% growth")
        
        # SEO performance insights
        seo_trends = seo_analysis.get('optimization_trends', {})
        if seo_trends.get('trend_direction') == 'improving':
            insights.append("SEO optimization efforts are showing positive results")
        
        # Trend utilization insights
        trend_utilization = trend_analysis.get('trend_utilization_rate', 0)
        if trend_utilization > 0.5:
            insights.append("High trend utilization rate indicates good market awareness")
        elif trend_utilization < 0.2:
            insights.append("Low trend utilization - opportunity to leverage trending topics more")
        
        # Cross-domain insights
        avg_engagement = content_analysis.get('avg_engagement_rate', 0)
        avg_seo_score = seo_analysis.get('avg_seo_score', 0)
        
        if avg_engagement > 0.05 and avg_seo_score > 0.7:
            insights.append("Strong performance across both engagement and SEO metrics")
        elif avg_engagement > 0.05 and avg_seo_score < 0.6:
            insights.append("High engagement but SEO optimization could be improved")
        elif avg_engagement < 0.03 and avg_seo_score > 0.7:
            insights.append("Good SEO optimization but engagement rates need attention")
        
        return insights[:5]  # Limit to top 5 insights
    
    def _generate_action_recommendations(self, content_analysis: Dict, 
                                       seo_analysis: Dict, 
                                       trend_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate action recommendations"""
        recommendations = []
        
        # Content optimization recommendations
        avg_engagement = content_analysis.get('avg_engagement_rate', 0)
        if avg_engagement < 0.03:
            recommendations.append({
                'category': 'content_optimization',
                'priority': 'high',
                'action': 'Focus on improving content engagement',
                'specific_steps': [
                    'Analyze best performing content patterns',
                    'Increase use of questions and calls-to-action',
                    'Optimize posting times based on audience activity'
                ],
                'expected_impact': 'Increase engagement rate by 50-100%'
            })
        
        # SEO optimization recommendations
        avg_seo_score = seo_analysis.get('avg_seo_score', 0)
        if avg_seo_score < 0.6:
            recommendations.append({
                'category': 'seo_optimization',
                'priority': 'medium',
                'action': 'Improve SEO optimization practices',
                'specific_steps': [
                    'Increase keyword diversity in content',
                    'Use trending hashtags more strategically',
                    'Optimize content length for target platforms'
                ],
                'expected_impact': 'Improve SEO scores by 20-30%'
            })
        
        # Trend utilization recommendations
        trend_utilization = trend_analysis.get('trend_utilization_rate', 0)
        if trend_utilization < 0.3:
            recommendations.append({
                'category': 'trend_utilization',
                'priority': 'medium',
                'action': 'Increase trend-based content creation',
                'specific_steps': [
                    'Set up daily trend monitoring',
                    'Create content calendar based on trending topics',
                    'Focus on micro-trends for early adoption advantage'
                ],
                'expected_impact': 'Increase content reach by 25-40%'
            })
        
        # Hashtag optimization recommendations
        hashtag_perf = content_analysis.get('hashtag_performance', {})
        if hashtag_perf.get('hashtag_usage_stats', {}).get('avg_hashtags_per_post', 0) < 3:
            recommendations.append({
                'category': 'hashtag_optimization',
                'priority': 'low',
                'action': 'Optimize hashtag usage',
                'specific_steps': [
                    'Increase hashtag count to 3-5 per post',
                    'Mix popular and niche hashtags',
                    'Track hashtag performance regularly'
                ],
                'expected_impact': 'Improve content discoverability by 15-25%'
            })
        
        return recommendations
    
    def _calculate_overall_performance_score(self, content_analysis: Dict, 
                                           seo_analysis: Dict, 
                                           trend_analysis: Dict) -> float:
        """Calculate overall performance score"""
        # Weight allocation
        content_weight = 0.4
        seo_weight = 0.3
        trend_weight = 0.3
        
        # Normalize scores
        content_score = min(1.0, content_analysis.get('avg_engagement_rate', 0) * 20)  # 5% engagement rate = 1.0 score
        seo_score = seo_analysis.get('avg_seo_score', 0)
        trend_score = trend_analysis.get('avg_relevance_score', 0)
        
        overall_score = (
            content_score * content_weight +
            seo_score * seo_weight +
            trend_score * trend_weight
        )
        
        return round(overall_score, 3)
    
    def _store_analytics_report(self, founder_id: str, report: Dict[str, Any]) -> None:
        """Store analytics report to database"""
        try:
            # This should store the report to database
            # Currently only logging
            logger.info(f"Storing analytics report for founder {founder_id}")
        except Exception as e:
            logger.error(f"Failed to store analytics report: {e}")
    
    def _empty_comprehensive_report(self, founder_id: str, days: int) -> Dict[str, Any]:
        """Return empty comprehensive report"""
        return {
            'report_generated_at': datetime.now(timezone.utc).isoformat(),
            'analysis_period_days': days,
            'founder_id': founder_id,
            'overall_performance_score': 0.0,
            'content_performance': {},
            'seo_performance': {},
            'trend_analysis': {},
            'comprehensive_insights': ['Insufficient data for analysis'],
            'action_recommendations': [],
            'next_review_date': (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        }