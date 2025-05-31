import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from collections import defaultdict, Counter
from database import DataFlowManager
from modules.seo.service_integration import SEOService

logger = logging.getLogger(__name__)

class ContentPerformanceAnalyzer:
    """Content performance analyzer"""
    
    def __init__(self, data_flow_manager: DataFlowManager):
        self.data_flow_manager = data_flow_manager
    
    def analyze_content_performance(self, founder_id: str, days: int = 30) -> Dict[str, Any]:
        """Analyze content performance"""
        try:
            # Get content data
            content_data = self._get_content_data(founder_id, days)
            
            if not content_data:
                return self._empty_performance_result()
            
            # Calculate key metrics
            metrics = {
                'total_posts': len(content_data),
                'avg_engagement_rate': self._calculate_avg_engagement(content_data),
                'best_performing_content': self._get_best_performing_content(content_data),
                'content_type_performance': self._analyze_content_type_performance(content_data),
                'posting_time_analysis': self._analyze_posting_times(content_data),
                'hashtag_performance': self._analyze_hashtag_performance(content_data),
                'trend_correlation': self._analyze_trend_correlation(content_data),
                'growth_metrics': self._calculate_growth_metrics(content_data, days)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Content performance analysis failed: {e}")
            return self._empty_performance_result()
    
    def _get_content_data(self, founder_id: str, days: int) -> List[Dict[str, Any]]:
        """Get content data"""
        try:
            since_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Get published content
            published_content = self.data_flow_manager.db_session.query(
                self.data_flow_manager.content_repo.model_class
            ).filter(
                self.data_flow_manager.content_repo.model_class.founder_id == founder_id,
                self.data_flow_manager.content_repo.model_class.status == 'posted',
                self.data_flow_manager.content_repo.model_class.posted_at >= since_date
            ).all()
            
            content_data = []
            for content in published_content:
                # Get analysis data
                analytics = self._get_content_analytics(content.posted_tweet_id) if content.posted_tweet_id else {}
                
                content_data.append({
                    'content_id': content.id,
                    'content_type': content.content_type,
                    'posted_at': content.posted_at,
                    'content_text': content.final_text,
                    'tweet_id': content.posted_tweet_id,
                    'analytics': analytics,
                    'trend_id': content.analyzed_trend_id,
                    'seo_data': content.seo_suggestions or {}
                })
            
            return content_data
            
        except Exception as e:
            logger.error(f"Failed to get content data: {e}")
            return []
    
    def _get_content_analytics(self, tweet_id: str) -> Dict[str, Any]:
        """Get tweet analysis data"""
        try:
            # This should call the Twitter API to get real data
            # Currently returns simulated data
            import random
            return {
                'impressions': random.randint(100, 10000),
                'engagements': random.randint(10, 500),
                'likes': random.randint(5, 200),
                'retweets': random.randint(0, 50),
                'replies': random.randint(0, 30),
                'engagement_rate': random.uniform(0.01, 0.15)
            }
        except Exception as e:
            logger.error(f"Failed to get tweet analysis data: {e}")
            return {}
    
    def _calculate_avg_engagement(self, content_data: List[Dict[str, Any]]) -> float:
        """Calculate average engagement rate"""
        if not content_data:
            return 0.0
        
        engagement_rates = []
        for content in content_data:
            analytics = content.get('analytics', {})
            engagement_rate = analytics.get('engagement_rate', 0)
            if engagement_rate > 0:
                engagement_rates.append(engagement_rate)
        
        return sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0.0
    
    def _get_best_performing_content(self, content_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get best performing content"""
        # Sort by engagement rate
        sorted_content = sorted(
            content_data,
            key=lambda x: x.get('analytics', {}).get('engagement_rate', 0),
            reverse=True
        )
        
        return sorted_content[:5]  # Return top 5
    
    def _analyze_content_type_performance(self, content_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze content type performance"""
        type_performance = defaultdict(list)
        
        for content in content_data:
            content_type = content.get('content_type', 'unknown')
            engagement_rate = content.get('analytics', {}).get('engagement_rate', 0)
            type_performance[content_type].append(engagement_rate)
        
        # Calculate average performance for each content type
        result = {}
        for content_type, rates in type_performance.items():
            if rates:
                result[content_type] = {
                    'avg_engagement_rate': sum(rates) / len(rates),
                    'post_count': len(rates),
                    'max_engagement': max(rates),
                    'min_engagement': min(rates)
                }
        
        return result
    
    def _analyze_posting_times(self, content_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze posting time performance"""
        hour_performance = defaultdict(list)
        day_performance = defaultdict(list)
        
        for content in content_data:
            posted_at = content.get('posted_at')
            if not posted_at:
                continue
            
            engagement_rate = content.get('analytics', {}).get('engagement_rate', 0)
            
            # Analyze by hour
            hour = posted_at.hour
            hour_performance[hour].append(engagement_rate)
            
            # Analyze by day of the week
            day = posted_at.strftime('%A')
            day_performance[day].append(engagement_rate)
        
        # Calculate best time
        best_hours = {}
        for hour, rates in hour_performance.items():
            if rates:
                best_hours[hour] = sum(rates) / len(rates)
        
        best_days = {}
        for day, rates in day_performance.items():
            if rates:
                best_days[day] = sum(rates) / len(rates)
        
        return {
            'best_hours': dict(sorted(best_hours.items(), key=lambda x: x[1], reverse=True)[:3]),
            'best_days': dict(sorted(best_days.items(), key=lambda x: x[1], reverse=True)[:3]),
            'hour_performance': dict(best_hours),
            'day_performance': dict(best_days)
        }
    
    def _analyze_hashtag_performance(self, content_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze hashtag performance"""
        hashtag_performance = defaultdict(list)
        
        for content in content_data:
            content_text = content.get('content_text', '')
            engagement_rate = content.get('analytics', {}).get('engagement_rate', 0)
            
            # Extract hashtags
            import re
            hashtags = re.findall(r'#(\w+)', content_text.lower())
            
            for hashtag in hashtags:
                hashtag_performance[hashtag].append(engagement_rate)
        
        # Calculate average performance for each hashtag
        result = {}
        for hashtag, rates in hashtag_performance.items():
            if rates and len(rates) >= 2:  # Used at least 2 times
                result[hashtag] = {
                    'avg_engagement_rate': sum(rates) / len(rates),
                    'usage_count': len(rates),
                    'max_engagement': max(rates)
                }
        
        # Sort by performance
        sorted_hashtags = dict(sorted(result.items(), key=lambda x: x[1]['avg_engagement_rate'], reverse=True))
        
        return {
            'top_performing_hashtags': dict(list(sorted_hashtags.items())[:10]),
            'hashtag_usage_stats': {
                'total_unique_hashtags': len(result),
                'avg_hashtags_per_post': sum(len(re.findall(r'#\w+', content.get('content_text', ''))) for content in content_data) / len(content_data) if content_data else 0
            }
        }
    
    def _analyze_trend_correlation(self, content_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trend correlation"""
        trend_performance = defaultdict(list)
        
        for content in content_data:
            trend_id = content.get('trend_id')
            if trend_id:
                engagement_rate = content.get('analytics', {}).get('engagement_rate', 0)
                trend_performance[trend_id].append(engagement_rate)
        
        # Calculate trend content performance
        trend_based_count = len([c for c in content_data if c.get('trend_id')])
        non_trend_engagement = [
            c.get('analytics', {}).get('engagement_rate', 0)
            for c in content_data if not c.get('trend_id')
        ]
        trend_engagement = [
            c.get('analytics', {}).get('engagement_rate', 0)
            for c in content_data if c.get('trend_id')
        ]
        
        avg_trend_engagement = sum(trend_engagement) / len(trend_engagement) if trend_engagement else 0
        avg_non_trend_engagement = sum(non_trend_engagement) / len(non_trend_engagement) if non_trend_engagement else 0
        
        return {
            'trend_based_content_count': trend_based_count,
            'avg_trend_engagement': avg_trend_engagement,
            'avg_non_trend_engagement': avg_non_trend_engagement,
            'trend_performance_boost': avg_trend_engagement - avg_non_trend_engagement,
            'trend_effectiveness': avg_trend_engagement / avg_non_trend_engagement if avg_non_trend_engagement > 0 else 0
        }
    
    def _calculate_growth_metrics(self, content_data: List[Dict[str, Any]], days: int) -> Dict[str, Any]:
        """Calculate growth metrics"""
        if len(content_data) < 2:
            return {'growth_rate': 0, 'trend': 'insufficient_data'}
        
        # Sort by time
        sorted_content = sorted(content_data, key=lambda x: x.get('posted_at', datetime.min))
        
        # Calculate early and later period performance
        mid_point = len(sorted_content) // 2
        early_period = sorted_content[:mid_point]
        later_period = sorted_content[mid_point:]
        
        early_avg = sum(c.get('analytics', {}).get('engagement_rate', 0) for c in early_period) / len(early_period)
        later_avg = sum(c.get('analytics', {}).get('engagement_rate', 0) for c in later_period) / len(later_period)
        
        growth_rate = ((later_avg - early_avg) / early_avg * 100) if early_avg > 0 else 0
        
        trend = 'stable'
        if growth_rate > 10:
            trend = 'improving'
        elif growth_rate < -10:
            trend = 'declining'
        
        return {
            'growth_rate': round(growth_rate, 2),
            'trend': trend,
            'early_period_avg': round(early_avg, 4),
            'later_period_avg': round(later_avg, 4),
            'analysis_period_days': days
        }
    
    def _empty_performance_result(self) -> Dict[str, Any]:
        """Return empty performance result"""
        return {
            'total_posts': 0,
            'avg_engagement_rate': 0.0,
            'best_performing_content': [],
            'content_type_performance': {},
            'posting_time_analysis': {},
            'hashtag_performance': {},
            'trend_correlation': {},
            'growth_metrics': {'growth_rate': 0, 'trend': 'no_data'}
        }

class SEOPerformanceAnalyzer:
    """SEO performance analyzer"""
    
    def __init__(self, data_flow_manager: DataFlowManager, seo_service: SEOService):
        self.data_flow_manager = data_flow_manager
        self.seo_service = seo_service
    
    def analyze_seo_performance(self, founder_id: str, days: int = 30) -> Dict[str, Any]:
        """Analyze SEO performance"""
        try:
            # Get SEO optimization history
            seo_history = self.data_flow_manager.get_seo_performance_history(founder_id, days)
            
            if not seo_history:
                return self._empty_seo_result()
            
            # Analyze SEO metrics
            metrics = {
                'total_optimizations': len(seo_history),
                'avg_seo_score': self._calculate_avg_seo_score(seo_history),
                'keyword_performance': self._analyze_keyword_performance(seo_history),
                'hashtag_effectiveness': self._analyze_hashtag_effectiveness(seo_history),
                'optimization_trends': self._analyze_optimization_trends(seo_history),
                'content_type_seo_performance': self._analyze_content_type_seo(seo_history),
                'improvement_opportunities': self._identify_improvement_opportunities(seo_history),
                'seo_roi_analysis': self._calculate_seo_roi(seo_history)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"SEO performance analysis failed: {e}")
            return self._empty_seo_result()
    
    def _calculate_avg_seo_score(self, seo_history: List[Dict[str, Any]]) -> float:
        """Calculate average SEO score"""
        scores = [entry.get('seo_quality_score', 0) for entry in seo_history]
        return sum(scores) / len(scores) if scores else 0.0
    
    def _analyze_keyword_performance(self, seo_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze keyword performance"""
        keyword_usage = Counter()
        keyword_scores = defaultdict(list)
        
        for entry in seo_history:
            keywords = entry.get('keywords_used', [])
            seo_score = entry.get('seo_quality_score', 0)
            
            for keyword in keywords:
                keyword_usage[keyword] += 1
                keyword_scores[keyword].append(seo_score)
        
        # Calculate keyword performance
        keyword_performance = {}
        for keyword, scores in keyword_scores.items():
            if len(scores) >= 2:  # Used at least 2 times
                keyword_performance[keyword] = {
                    'usage_count': keyword_usage[keyword],
                    'avg_seo_score': sum(scores) / len(scores),
                    'max_score': max(scores),
                    'consistency': 1.0 - (max(scores) - min(scores)) / max(scores) if max(scores) > 0 else 0
                }
        
        # Sort by performance
        top_keywords = dict(sorted(
            keyword_performance.items(),
            key=lambda x: x[1]['avg_seo_score'],
            reverse=True
        )[:10])
        
        return {
            'top_performing_keywords': top_keywords,
            'total_unique_keywords': len(keyword_performance),
            'most_used_keywords': dict(keyword_usage.most_common(10))
        }
    
    def _analyze_hashtag_effectiveness(self, seo_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze hashtag effectiveness"""
        hashtag_usage = Counter()
        hashtag_scores = defaultdict(list)
        
        for entry in seo_history:
            hashtags = entry.get('hashtags_suggested', [])
            seo_score = entry.get('seo_quality_score', 0)
            
            for hashtag in hashtags:
                hashtag_usage[hashtag] += 1
                hashtag_scores[hashtag].append(seo_score)
        
        # Calculate hashtag performance
        hashtag_performance = {}
        for hashtag, scores in hashtag_scores.items():
            if len(scores) >= 2:
                hashtag_performance[hashtag] = {
                    'usage_count': hashtag_usage[hashtag],
                    'avg_seo_score': sum(scores) / len(scores),
                    'effectiveness_rating': self._calculate_hashtag_effectiveness(scores)
                }
        
        # Sort by effectiveness
        top_hashtags = dict(sorted(
            hashtag_performance.items(),
            key=lambda x: x[1]['avg_seo_score'],
            reverse=True
        )[:10])
        
        return {
            'top_effective_hashtags': top_hashtags,
            'hashtag_diversity': len(hashtag_performance),
            'recommended_hashtags': self._get_recommended_hashtags(hashtag_performance)
        }
    
    def _calculate_hashtag_effectiveness(self, scores: List[float]) -> str:
        """Calculate hashtag effectiveness rating"""
        avg_score = sum(scores) / len(scores)
        
        if avg_score >= 0.8:
            return 'excellent'
        elif avg_score >= 0.7:
            return 'good'
        elif avg_score >= 0.6:
            return 'average'
        else:
            return 'poor'
    
    def _get_recommended_hashtags(self, hashtag_performance: Dict[str, Any]) -> List[str]:
        """Get recommended hashtags"""
        # Select hashtags with good performance and moderate usage frequency
        recommended = []
        
        for hashtag, perf in hashtag_performance.items():
            if (perf['avg_seo_score'] >= 0.7 and 
                2 <= perf['usage_count'] <= 10):  # Don't overuse
                recommended.append(hashtag)
        
        return recommended[:5]
    
    def _analyze_optimization_trends(self, seo_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze optimization trends"""
        # Sort by time
        sorted_history = sorted(
            seo_history,
            key=lambda x: x.get('optimization_timestamp', '')
        )
        
        if len(sorted_history) < 3:
            return {'trend': 'insufficient_data'}
        
        # Calculate moving average
        window_size = 5
        moving_averages = []
        
        for i in range(len(sorted_history) - window_size + 1):
            window = sorted_history[i:i + window_size]
            avg_score = sum(entry.get('seo_quality_score', 0) for entry in window) / window_size
            moving_averages.append(avg_score)
        
        # Analyze trend
        if len(moving_averages) >= 2:
            trend_direction = 'improving' if moving_averages[-1] > moving_averages[0] else 'declining'
            if abs(moving_averages[-1] - moving_averages[0]) < 0.05:
                trend_direction = 'stable'
        else:
            trend_direction = 'stable'
        
        return {
            'trend_direction': trend_direction,
            'recent_avg_score': moving_averages[-1] if moving_averages else 0,
            'score_improvement': moving_averages[-1] - moving_averages[0] if len(moving_averages) >= 2 else 0,
            'optimization_consistency': self._calculate_consistency(sorted_history)
        }
    
    def _calculate_consistency(self, seo_history: List[Dict[str, Any]]) -> float:
        """Calculate optimization consistency"""
        scores = [entry.get('seo_quality_score', 0) for entry in seo_history]
        
        if not scores or len(scores) < 2:
            return 0.0
        
        # Calculate coefficient of variation
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        std_deviation = variance ** 0.5
        
        consistency = 1.0 - (std_deviation / mean_score) if mean_score > 0 else 0.0
        return max(0.0, min(1.0, consistency))
    
    def _analyze_content_type_seo(self, seo_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze content type SEO performance"""
        content_type_performance = defaultdict(list)
        
        for entry in seo_history:
            content_type = entry.get('content_type', 'unknown')
            seo_score = entry.get('seo_quality_score', 0)
            content_type_performance[content_type].append(seo_score)
        
        # Calculate SEO performance for each content type
        result = {}
        for content_type, scores in content_type_performance.items():
            if scores:
                result[content_type] = {
                    'avg_seo_score': sum(scores) / len(scores),
                    'optimization_count': len(scores),
                    'best_score': max(scores),
                    'score_range': max(scores) - min(scores)
                }
        
        return result
    
    def _identify_improvement_opportunities(self, seo_history: List[Dict[str, Any]]) -> List[str]:
        """Identify improvement opportunities"""
        opportunities = []
        
        # Analyze score distribution
        scores = [entry.get('seo_quality_score', 0) for entry in seo_history]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        if avg_score < 0.6:
            opportunities.append("Overall SEO scores are below target (0.6). Focus on keyword optimization.")
        
        if avg_score < 0.7:
            opportunities.append("Consider diversifying hashtag strategy for better reach.")
        
        # Analyze keyword diversity
        all_keywords = []
        for entry in seo_history:
            all_keywords.extend(entry.get('keywords_used', []))
        
        unique_keywords = len(set(all_keywords))
        total_keyword_uses = len(all_keywords)
        
        if total_keyword_uses > 0 and unique_keywords / total_keyword_uses < 0.3:
            opportunities.append("Increase keyword diversity to avoid over-optimization.")
        
        # Analyze consistency
        consistency = self._calculate_consistency(seo_history)
        if consistency < 0.7:
            opportunities.append("Improve optimization consistency across content.")
        
        return opportunities
    
    def _calculate_seo_roi(self, seo_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate SEO return on investment"""
        # Simplified ROI calculation based on SEO score improvement
        if len(seo_history) < 5:
            return {'roi': 0, 'analysis': 'insufficient_data'}
        
        # Sort by time
        sorted_history = sorted(
            seo_history,
            key=lambda x: x.get('optimization_timestamp', '')
        )
        
        # Calculate early and later period performance
        early_period = sorted_history[:len(sorted_history)//3]
        later_period = sorted_history[-len(sorted_history)//3:]
        
        early_avg = sum(entry.get('seo_quality_score', 0) for entry in early_period) / len(early_period)
        later_avg = sum(entry.get('seo_quality_score', 0) for entry in later_period) / len(later_period)
        
        improvement = later_avg - early_avg
        roi_percentage = (improvement / early_avg * 100) if early_avg > 0 else 0
        
        return {
            'roi_percentage': round(roi_percentage, 2),
            'score_improvement': round(improvement, 3),
            'optimization_efficiency': 'high' if roi_percentage > 20 else 'moderate' if roi_percentage > 0 else 'low'
        }
    
    def _empty_seo_result(self) -> Dict[str, Any]:
        """Return empty SEO result"""
        return {
            'total_optimizations': 0,
            'avg_seo_score': 0.0,
            'keyword_performance': {},
            'hashtag_effectiveness': {},
            'optimization_trends': {'trend': 'no_data'},
            'content_type_seo_performance': {},
            'improvement_opportunities': [],
            'seo_roi_analysis': {'roi': 0}
        }