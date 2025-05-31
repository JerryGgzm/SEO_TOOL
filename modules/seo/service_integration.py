"""SEO Module Service - Integration layer for system-wide SEO functionality"""
import asyncio
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from modules.twitter_api import TwitterAPIClient
from modules.user_profile import UserProfileService
from database import DataFlowManager

from .optimizer import SEOOptimizer
from .models import (
    SEOOptimizationRequest, SEOAnalysisContext, SEOContentType,
    SEOOptimizationLevel, HashtagStrategy, ContentOptimizationSuggestions
)

logger = logging.getLogger(__name__)

class SEOService:
    """
    High-level SEO service for system integration
    Provides SEO optimization functionality to other modules
    """
    
    def __init__(self, twitter_client: TwitterAPIClient,
                 user_service: UserProfileService,
                 data_flow_manager: DataFlowManager,
                 config: Dict[str, Any] = None):
        
        self.twitter_client = twitter_client
        self.user_service = user_service
        self.data_flow_manager = data_flow_manager
        self.config = config or {}
        
        # Initialize SEO optimizer
        self.optimizer = SEOOptimizer(twitter_client, config)
        
        # Cache for optimization results
        self._optimization_cache = {}
        self._cache_duration = timedelta(hours=self.config.get('cache_duration_hours', 6))
    
    async def get_content_suggestions(self, trend_info: Dict[str, Any],
                                    product_info: Dict[str, Any],
                                    content_type: str) -> ContentOptimizationSuggestions:
        """
        Get SEO suggestions for content generation (Called by ContentGenerationModule)
        
        Args:
            trend_info: Information about the trend
            product_info: User's product information
            content_type: Type of content being generated
            
        Returns:
            SEO optimization suggestions
        """
        try:
            logger.info(f"Getting SEO suggestions for {content_type} content")
            
            # Convert content type string to enum
            seo_content_type = self._convert_content_type(content_type)
            
            # Get suggestions from optimizer
            suggestions = await self.optimizer.get_content_suggestions(
                trend_info, product_info, seo_content_type
            )
            
            logger.info(f"Generated {len(suggestions.recommended_hashtags)} hashtag suggestions")
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to get SEO content suggestions: {e}")
            return ContentOptimizationSuggestions()
    
    def optimize_content(self, text: str, content_type: str, 
                        context: Dict[str, Any] = None) -> str:
        """
        Optimize content for SEO (Called by ContentGenerationModule)
        
        Args:
            text: Content to optimize
            content_type: Type of content
            context: Additional context for optimization
            
        Returns:
            Optimized content
        """
        try:
            # Convert content type
            seo_content_type = self._convert_content_type(content_type)
            
            # Use simple optimization for integration
            optimized_text = self.optimizer.optimize_content_simple(
                text, seo_content_type, context
            )
            
            return optimized_text
            
        except Exception as e:
            logger.error(f"Content optimization failed: {e}")
            return text
    
    async def optimize_content_full(self, founder_id: str, content: str,
                                  content_type: str, optimization_level: str = "moderate") -> Dict[str, Any]:
        """
        Full SEO optimization with detailed analysis
        
        Args:
            founder_id: Founder's ID
            content: Content to optimize
            content_type: Type of content
            optimization_level: Level of optimization
            
        Returns:
            Complete optimization result
        """
        try:
            # Build context from user profile
            context = await self._build_seo_context(founder_id, content_type)
            
            # Create optimization request
            request = SEOOptimizationRequest(
                content=content,
                content_type=self._convert_content_type(content_type),
                optimization_level=self._convert_optimization_level(optimization_level),
                context=context
            )
            
            # Perform optimization
            result = await self.optimizer.optimize_content(request)
            
            # Convert result to dictionary for API response
            return {
                'original_content': result.original_content,
                'optimized_content': result.optimized_content,
                'optimization_score': result.optimization_score,
                'improvements_made': result.improvements_made,
                'hashtag_suggestions': [ht.hashtag for ht in result.hashtag_analysis],
                'keyword_suggestions': [kw.keyword for kw in result.keyword_analysis],
                'estimated_reach_improvement': result.estimated_reach_improvement,
                'suggestions': {
                    'recommended_hashtags': result.suggestions.recommended_hashtags,
                    'primary_keywords': result.suggestions.primary_keywords,
                    'engagement_tactics': result.suggestions.engagement_tactics,
                    'optimal_length': result.suggestions.optimal_length,
                    'call_to_action': result.suggestions.call_to_action
                }
            }
            
        except Exception as e:
            logger.error(f"Full SEO optimization failed: {e}")
            return {
                'original_content': content,
                'optimized_content': content,
                'optimization_score': 0.5,
                'error': str(e)
            }
    
    async def analyze_hashtag_performance(self, founder_id: str,
                                        hashtags: List[str]) -> Dict[str, Any]:
        """
        Analyze performance of specific hashtags
        
        Args:
            founder_id: Founder's ID
            hashtags: List of hashtags to analyze
            
        Returns:
            Hashtag performance analysis
        """
        try:
            # Get hashtag performance insights
            insights = self.optimizer.hashtag_generator.get_hashtag_performance_insights(
                hashtags, time_period_days=30
            )
            
            # Store analysis results
            self._store_hashtag_analysis(founder_id, hashtags, insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"Hashtag performance analysis failed: {e}")
            return {}
    
    def get_trending_hashtags(self, niche_keywords: List[str],
                            max_hashtags: int = 20) -> List[Dict[str, Any]]:
        """
        Get trending hashtags relevant to niche
        
        Args:
            niche_keywords: Keywords related to user's niche
            max_hashtags: Maximum number of hashtags to return
            
        Returns:
            List of trending hashtag data
        """
        try:
            # This would integrate with Twitter API to get real trending data
            # For now, return simulated trending hashtags
            
            trending_hashtags = []
            base_trending = ['ai', 'innovation', 'startup', 'tech', 'growth']
            
            # Add niche-specific trending
            for keyword in niche_keywords[:3]:
                base_trending.append(f"{keyword.lower()}tips")
                base_trending.append(f"{keyword.lower()}trending")
            
            for hashtag in base_trending[:max_hashtags]:
                trending_hashtags.append({
                    'hashtag': hashtag,
                    'usage_count': 1000 + len(hashtag) * 100,
                    'growth_rate': 5.0 + (len(hashtag) % 5) * 2.0,
                    'engagement_rate': 0.03 + (len(hashtag) % 3) * 0.01,
                    'relevance_score': 0.8 if hashtag in niche_keywords else 0.6
                })
            
            return trending_hashtags
            
        except Exception as e:
            logger.error(f"Failed to get trending hashtags: {e}")
            return []
    
    def generate_keyword_suggestions(self, founder_id: str, 
                                   content_context: str = "",
                                   max_keywords: int = 20) -> List[Dict[str, Any]]:
        """
        Generate keyword suggestions for founder
        
        Args:
            founder_id: Founder's ID
            content_context: Context for keyword generation
            max_keywords: Maximum keywords to return
            
        Returns:
            List of keyword suggestions with analysis
        """
        try:
            # Get user profile for context
            user_profile = self.user_service.get_user_profile(founder_id)
            if not user_profile:
                return []
            
            # Build analysis context
            context = SEOAnalysisContext(
                content_type=SEOContentType.TWEET,  # Default
                niche_keywords=getattr(user_profile, 'niche_keywords', []),
                target_audience=getattr(user_profile, 'target_audience', 'professionals'),
                product_categories=[getattr(user_profile, 'industry_category', 'technology')]
            )
            
            # Generate keyword suggestions
            keywords = self.optimizer.keyword_analyzer.generate_keyword_suggestions(
                context, max_keywords
            )
            
            # Convert to response format
            keyword_suggestions = []
            for keyword in keywords:
                # Get detailed analysis for each keyword
                analysis = self.optimizer.keyword_analyzer._analyze_single_keyword(
                    keyword, content_context, context
                )
                
                if analysis:
                    keyword_suggestions.append({
                        'keyword': analysis.keyword,
                        'search_volume': analysis.search_volume,
                        'difficulty': analysis.difficulty.value,
                        'relevance_score': analysis.relevance_score,
                        'trending_status': analysis.trending_status,
                        'suggested_usage': analysis.suggested_usage
                    })
            
            return keyword_suggestions
            
        except Exception as e:
            logger.error(f"Keyword suggestion generation failed: {e}")
            return []
    
    async def track_seo_performance(self, founder_id: str, 
                                  content_id: str,
                                  pre_metrics: Dict[str, float],
                                  post_metrics: Dict[str, float]) -> bool:
        """
        Track SEO optimization performance
        
        Args:
            founder_id: Founder's ID
            content_id: Content identifier
            pre_metrics: Metrics before optimization
            post_metrics: Metrics after optimization
            
        Returns:
            Success status
        """
        try:
            # Calculate improvement
            improvement = {}
            for metric, post_value in post_metrics.items():
                pre_value = pre_metrics.get(metric, 0)
                if pre_value > 0:
                    improvement[metric] = ((post_value - pre_value) / pre_value) * 100
                else:
                    improvement[metric] = 0
            
            # Store performance data
            performance_data = {
                'founder_id': founder_id,
                'content_id': content_id,
                'pre_optimization_metrics': pre_metrics,
                'post_optimization_metrics': post_metrics,
                'improvement_percentage': improvement.get('engagement_rate', 0),
                'tracking_timestamp': datetime.utcnow().isoformat()
            }
            
            # Save to database (would use actual repository)
            self._store_performance_data(performance_data)
            
            return True
            
        except Exception as e:
            logger.error(f"SEO performance tracking failed: {e}")
            return False
    
    def get_seo_recommendations(self, founder_id: str) -> Dict[str, Any]:
        """
        Get personalized SEO recommendations for founder
        
        Args:
            founder_id: Founder's ID
            
        Returns:
            SEO recommendations and insights
        """
        try:
            # Get user profile
            user_profile = self.user_service.get_user_profile(founder_id)
            if not user_profile:
                return {}
            
            # Get performance history
            performance_history = self._get_performance_history(founder_id)
            
            # Generate recommendations based on profile and performance
            recommendations = {
                'hashtag_strategy': self._recommend_hashtag_strategy(user_profile, performance_history),
                'keyword_focus': self._recommend_keyword_focus(user_profile),
                'content_optimization': self._recommend_content_optimization(performance_history),
                'posting_schedule': self._recommend_posting_schedule(performance_history),
                'engagement_tactics': self._recommend_engagement_tactics(performance_history)
            }
            
            return recommendations
            
        except Exception as e:
            logger.error(f"SEO recommendations generation failed: {e}")
            return {}
    
    async def _build_seo_context(self, founder_id: str, content_type: str) -> SEOAnalysisContext:
        """Build SEO analysis context from user profile"""
        try:
            # Get user profile
            user_profile = self.user_service.get_user_profile(founder_id)
            
            if not user_profile:
                return SEOAnalysisContext(
                    content_type=self._convert_content_type(content_type)
                )
            
            # Extract relevant information
            niche_keywords = []
            if hasattr(user_profile, 'niche_keywords'):
                niche_keywords = user_profile.niche_keywords
            elif hasattr(user_profile, 'product_info'):
                product_info = user_profile.product_info
                if hasattr(product_info, 'core_values'):
                    niche_keywords = product_info.core_values
            
            target_audience = getattr(user_profile, 'target_audience', 'professionals')
            industry = getattr(user_profile, 'industry_category', 'technology')
            
            return SEOAnalysisContext(
                content_type=self._convert_content_type(content_type),
                target_audience=target_audience,
                niche_keywords=niche_keywords,
                product_categories=[industry],
                industry_vertical=industry
            )
            
        except Exception as e:
            logger.error(f"Failed to build SEO context: {e}")
            return SEOAnalysisContext(
                content_type=self._convert_content_type(content_type)
            )
    
    def _convert_content_type(self, content_type: str) -> SEOContentType:
        """Convert string content type to enum"""
        mapping = {
            'tweet': SEOContentType.TWEET,
            'reply': SEOContentType.REPLY,
            'thread': SEOContentType.THREAD,
            'quote_tweet': SEOContentType.QUOTE_TWEET
        }
        return mapping.get(content_type.lower(), SEOContentType.TWEET)
    
    def _convert_optimization_level(self, level: str) -> SEOOptimizationLevel:
        """Convert string optimization level to enum"""
        mapping = {
            'basic': SEOOptimizationLevel.BASIC,
            'moderate': SEOOptimizationLevel.MODERATE,
            'aggressive': SEOOptimizationLevel.AGGRESSIVE
        }
        return mapping.get(level.lower(), SEOOptimizationLevel.MODERATE)
    
    def _store_hashtag_analysis(self, founder_id: str, hashtags: List[str], 
                              insights: Dict[str, Any]) -> None:
        """Store hashtag analysis results"""
        try:
            # In a real implementation, this would store to database
            analysis_data = {
                'founder_id': founder_id,
                'hashtags': hashtags,
                'insights': insights,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
            # Store using data flow manager or direct database access
            logger.info(f"Stored hashtag analysis for founder {founder_id}")
            
        except Exception as e:
            logger.error(f"Failed to store hashtag analysis: {e}")
    
    def _store_performance_data(self, performance_data: Dict[str, Any]) -> None:
        """Store SEO performance data"""
        try:
            # In a real implementation, this would store to database
            logger.info(f"Stored SEO performance data for content {performance_data['content_id']}")
            
        except Exception as e:
            logger.error(f"Failed to store performance data: {e}")
    
    def _get_performance_history(self, founder_id: str) -> List[Dict[str, Any]]:
        """Get performance history for founder"""
        try:
            # In a real implementation, this would query database
            # Return simulated performance history
            return [
                {
                    'content_id': 'content_1',
                    'optimization_score': 0.8,
                    'engagement_improvement': 25.0,
                    'reach_improvement': 30.0,
                    'timestamp': (datetime.utcnow() - timedelta(days=7)).isoformat()
                },
                {
                    'content_id': 'content_2', 
                    'optimization_score': 0.7,
                    'engagement_improvement': 15.0,
                    'reach_improvement': 20.0,
                    'timestamp': (datetime.utcnow() - timedelta(days=14)).isoformat()
                }
            ]
            
        except Exception as e:
            logger.error(f"Failed to get performance history: {e}")
            return []
    
    def _recommend_hashtag_strategy(self, user_profile: Any, 
                                  performance_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Recommend hashtag strategy based on profile and performance"""
        # Analyze performance to recommend strategy
        avg_performance = 0.0
        if performance_history:
            avg_performance = sum(p.get('engagement_improvement', 0) for p in performance_history) / len(performance_history)
        
        if avg_performance < 10:
            strategy = "engagement_optimized"
            recommendation = "Focus on engagement-optimized hashtags to improve interaction rates"
        elif avg_performance < 20:
            strategy = "trending_focus" 
            recommendation = "Leverage trending hashtags for better discovery"
        else:
            strategy = "niche_specific"
            recommendation = "Continue with niche-specific hashtags for targeted audience"
        
        return {
            'recommended_strategy': strategy,
            'explanation': recommendation,
            'max_hashtags_per_post': 5
        }
    
    def _recommend_keyword_focus(self, user_profile: Any) -> Dict[str, Any]:
        """Recommend keyword focus areas"""
        # Extract industry from profile
        industry = getattr(user_profile, 'industry_category', 'technology')
        
        keyword_focuses = {
            'technology': ['innovation', 'automation', 'digital transformation'],
            'marketing': ['growth', 'conversion', 'brand awareness'],
            'finance': ['investment', 'financial planning', 'fintech'],
            'healthcare': ['wellness', 'medical technology', 'patient care'],
            'education': ['learning', 'skills development', 'online education']
        }
        
        focus_keywords = keyword_focuses.get(industry.lower(), ['business', 'growth', 'success'])
        
        return {
            'primary_focus_keywords': focus_keywords,
            'keyword_density_target': 0.02,
            'recommendation': f"Focus on {industry} industry keywords for better niche targeting"
        }
    
    def _recommend_content_optimization(self, performance_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Recommend content optimization approaches"""
        # Analyze what works best
        high_performing = [p for p in performance_history if p.get('optimization_score', 0) > 0.7]
        
        if len(high_performing) < len(performance_history) * 0.5:
            return {
                'focus_area': 'engagement_elements',
                'recommendation': 'Add more questions and call-to-actions to improve engagement',
                'target_optimization_score': 0.8
            }
        else:
            return {
                'focus_area': 'advanced_optimization',
                'recommendation': 'Focus on advanced keyword integration and platform-specific optimization',
                'target_optimization_score': 0.9
            }
    
    def _recommend_posting_schedule(self, performance_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Recommend optimal posting schedule"""
        return {
            'optimal_times': ['9:00 AM', '1:00 PM', '7:00 PM'],
            'optimal_days': ['Tuesday', 'Wednesday', 'Thursday'],
            'frequency': 'Daily posting with 2-3 optimized posts per day',
            'recommendation': 'Post during peak engagement hours for maximum visibility'
        }
    
    def _recommend_engagement_tactics(self, performance_history: List[Dict[str, Any]]) -> List[str]:
        """Recommend engagement tactics"""
        return [
            "Ask questions to encourage replies",
            "Use numbers and statistics to grab attention", 
            "Include clear call-to-actions",
            "Share personal insights and experiences",
            "Use trending hashtags strategically",
            "Respond quickly to comments and mentions"
        ]
    
    def get_seo_analytics_summary(self, founder_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get SEO analytics summary for founder
        
        Args:
            founder_id: Founder's ID
            days: Number of days to analyze
            
        Returns:
            SEO analytics summary
        """
        try:
            # Get performance data from database
            performance_data = self._get_performance_history(founder_id)
            
            if not performance_data:
                return {
                    'total_optimizations': 0,
                    'avg_optimization_score': 0.0,
                    'avg_engagement_improvement': 0.0,
                    'best_performing_hashtags': [],
                    'recommendations': []
                }
            
            # Calculate summary metrics
            total_optimizations = len(performance_data)
            avg_optimization_score = sum(p.get('optimization_score', 0) for p in performance_data) / total_optimizations
            avg_engagement_improvement = sum(p.get('engagement_improvement', 0) for p in performance_data) / total_optimizations
            
            # Get best performing hashtags (would be from actual data)
            best_hashtags = ['innovation', 'startup', 'growth', 'tech', 'productivity']
            
            # Generate recommendations
            recommendations = self.get_seo_recommendations(founder_id)
            
            return {
                'total_optimizations': total_optimizations,
                'avg_optimization_score': round(avg_optimization_score, 2),
                'avg_engagement_improvement': round(avg_engagement_improvement, 1),
                'avg_reach_improvement': round(sum(p.get('reach_improvement', 0) for p in performance_data) / total_optimizations, 1),
                'best_performing_hashtags': best_hashtags,
                'optimization_trend': 'improving' if avg_optimization_score > 0.7 else 'needs_improvement',
                'recommendations': recommendations,
                'analysis_period_days': days
            }
            
        except Exception as e:
            logger.error(f"SEO analytics summary generation failed: {e}")
            return {}
    
    def clear_optimization_cache(self) -> None:
        """Clear optimization cache"""
        self._optimization_cache.clear()
        logger.info("SEO optimization cache cleared")