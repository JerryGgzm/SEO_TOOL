"""Hashtag generation and optimization engine"""
import re
import math
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import logging

from .models import (
    HashtagMetrics, HashtagStrategy, SEOContentType, KeywordDifficulty,
    HashtagGenerationRequest, TrendingHashtagsData, CompetitorHashtagAnalysis
)

logger = logging.getLogger(__name__)

class HashtagGenerator:
    """Advanced hashtag generation and optimization"""
    
    def __init__(self, twitter_client=None, config: Dict[str, Any] = None):
        self.twitter_client = twitter_client
        self.config = config or {}
        
        # Hashtag categories and their engagement multipliers
        self.hashtag_categories = {
            'trending': 1.5,
            'niche': 1.3,
            'community': 1.2,
            'brand': 1.1,
            'generic': 1.0,
            'overused': 0.7
        }
        
        # Common high-engagement hashtag patterns
        self.engagement_patterns = {
            'question_based': ['ask', 'question', 'help', 'advice', 'tips'],
            'community_building': ['community', 'together', 'share', 'connect', 'join'],
            'trending_topics': ['trending', 'viral', 'popular', 'hot', 'new'],
            'industry_specific': ['tech', 'startup', 'business', 'innovation', 'growth'],
            'actionable': ['learn', 'discover', 'master', 'improve', 'optimize']
        }
        
        # Hashtag blacklist (overused or spam-associated)
        self.blacklisted_hashtags = {
            'follow4follow', 'like4like', 'followme', 'spam', 'bot',
            'followback', 'teamfollowback', 'pleasefollow', 'follows',
            'followtrick', 'followall', 'alwaysfollowback'
        }
    
    def generate_hashtags(self, request: HashtagGenerationRequest) -> List[HashtagMetrics]:
        """
        Generate optimized hashtags based on content and strategy
        
        Args:
            request: Hashtag generation request
            
        Returns:
            List of hashtag metrics with recommendations
        """
        try:
            logger.info(f"Generating hashtags for {request.content_type} content")
            
            # Extract base hashtags from content and context
            base_hashtags = self._extract_content_hashtags(request.content)
            niche_hashtags = self._generate_niche_hashtags(request.niche_keywords)
            trending_hashtags = self._get_trending_hashtags(request) if request.include_trending else []
            strategic_hashtags = self._generate_strategic_hashtags(request)
            
            # Combine and deduplicate
            all_hashtags = set()
            all_hashtags.update(base_hashtags)
            if request.include_niche:
                all_hashtags.update(niche_hashtags)
            all_hashtags.update(trending_hashtags)
            all_hashtags.update(strategic_hashtags)
            
            # Remove excluded hashtags
            all_hashtags -= set(tag.lower() for tag in request.exclude_hashtags)
            all_hashtags -= self.blacklisted_hashtags
            
            # Score and rank hashtags
            scored_hashtags = []
            for hashtag in all_hashtags:
                metrics = self._analyze_hashtag(hashtag, request)
                if metrics and metrics.relevance_score > 0.3:  # Minimum relevance threshold
                    scored_hashtags.append(metrics)
            
            # Sort by optimization strategy
            scored_hashtags = self._rank_hashtags_by_strategy(scored_hashtags, request.strategy)
            
            # Return top hashtags based on request limit
            return scored_hashtags[:request.max_hashtags]
            
        except Exception as e:
            logger.error(f"Hashtag generation failed: {e}")
            return []
    
    def _extract_content_hashtags(self, content: str) -> List[str]:
        """Extract hashtags already present in content"""
        existing_hashtags = re.findall(r'#(\w+)', content.lower())
        return list(set(existing_hashtags))
    
    def _generate_niche_hashtags(self, niche_keywords: List[str]) -> List[str]:
        """Generate hashtags based on niche keywords"""
        niche_hashtags = []
        
        for keyword in niche_keywords:
            # Direct keyword
            clean_keyword = re.sub(r'[^a-zA-Z0-9]', '', keyword.lower())
            if len(clean_keyword) > 2:
                niche_hashtags.append(clean_keyword)
            
            # Keyword variations
            variations = self._generate_keyword_variations(keyword)
            niche_hashtags.extend(variations)
        
        return list(set(niche_hashtags))
    
    def _generate_keyword_variations(self, keyword: str) -> List[str]:
        """Generate variations of a keyword for hashtags"""
        variations = []
        keyword = keyword.lower().strip()
        
        # Remove common stop words
        stop_words = {'and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        words = [w for w in keyword.split() if w not in stop_words]
        
        if len(words) == 1:
            word = words[0]
            # Add common suffixes
            variations.extend([
                f"{word}tips",
                f"{word}hack", 
                f"{word}guide",
                f"{word}101",
                f"learn{word}",
                f"{word}expert"
            ])
        elif len(words) == 2:
            # Combine words
            combined = ''.join(words)
            if len(combined) <= 20:  # Twitter hashtag length limit
                variations.append(combined)
            
            # Individual words with modifiers
            for word in words:
                if len(word) > 3:
                    variations.extend([f"{word}tips", f"{word}hack"])
        
        # Filter out variations that are too long or too short
        variations = [v for v in variations if 3 <= len(v) <= 20]
        
        return variations
    
    def _get_trending_hashtags(self, request: HashtagGenerationRequest) -> List[str]:
        """Get currently trending hashtags relevant to the content"""
        if not self.twitter_client:
            return self._get_fallback_trending_hashtags(request)
        
        try:
            # This would integrate with Twitter API to get trending topics
            # For now, return simulated trending hashtags
            trending_data = self._fetch_trending_data()
            
            # Filter trending hashtags by relevance to content
            relevant_trending = []
            content_words = set(request.content.lower().split())
            niche_words = set(' '.join(request.niche_keywords).lower().split())
            
            for hashtag in trending_data:
                hashtag_words = set(hashtag.lower().split())
                
                # Check relevance to content or niche
                if (hashtag_words & content_words) or (hashtag_words & niche_words):
                    relevant_trending.append(hashtag)
            
            return relevant_trending[:5]  # Limit trending hashtags
            
        except Exception as e:
            logger.warning(f"Failed to get trending hashtags: {e}")
            return self._get_fallback_trending_hashtags(request)
    
    def _get_fallback_trending_hashtags(self, request: HashtagGenerationRequest) -> List[str]:
        """Fallback trending hashtags when API is unavailable"""
        fallback_trending = {
            SEOContentType.TWEET: ['innovation', 'trending', 'viral', 'discover'],
            SEOContentType.THREAD: ['thread', 'story', 'insights', 'learn'],
            SEOContentType.REPLY: ['discussion', 'thoughts', 'community'],
        }
        
        base_trending = fallback_trending.get(request.content_type, ['trending', 'discover'])
        
        # Add some niche-specific trending
        if request.niche_keywords:
            for keyword in request.niche_keywords[:2]:
                clean_keyword = re.sub(r'[^a-zA-Z0-9]', '', keyword.lower())
                if len(clean_keyword) > 3:
                    base_trending.append(f"{clean_keyword}trending")
        
        return base_trending
    
    def _generate_strategic_hashtags(self, request: HashtagGenerationRequest) -> List[str]:
        """Generate hashtags based on optimization strategy"""
        strategic_hashtags = []
        
        if request.strategy == HashtagStrategy.ENGAGEMENT_OPTIMIZED:
            strategic_hashtags.extend([
                'engage', 'discuss', 'share', 'thoughts', 'community',
                'connect', 'network', 'learn', 'grow', 'discover'
            ])
        
        elif request.strategy == HashtagStrategy.DISCOVERY_FOCUSED:
            strategic_hashtags.extend([
                'discover', 'explore', 'new', 'trending', 'viral',
                'popular', 'hot', 'fresh', 'latest', 'breakthrough'
            ])
        
        elif request.strategy == HashtagStrategy.BRAND_BUILDING:
            strategic_hashtags.extend([
                'brand', 'startup', 'entrepreneur', 'founder', 'business',
                'innovation', 'success', 'growth', 'leadership', 'vision'
            ])
        
        elif request.strategy == HashtagStrategy.NICHE_SPECIFIC:
            # Focus on niche-related hashtags
            strategic_hashtags.extend(request.niche_keywords)
        
        elif request.strategy == HashtagStrategy.TRENDING_FOCUS:
            # This would be handled by _get_trending_hashtags
            pass
        
        # Content type specific hashtags
        content_specific = {
            SEOContentType.THREAD: ['thread', 'story', 'insights', 'breakdown'],
            SEOContentType.REPLY: ['discussion', 'thoughts', 'opinion'],
            SEOContentType.QUOTE_TWEET: ['quote', 'perspective', 'take']
        }
        
        if request.content_type in content_specific:
            strategic_hashtags.extend(content_specific[request.content_type])
        
        return list(set(strategic_hashtags))
    
    def _analyze_hashtag(self, hashtag: str, request: HashtagGenerationRequest) -> Optional[HashtagMetrics]:
        """Analyze a hashtag and return metrics"""
        try:
            # Calculate relevance score
            relevance_score = self._calculate_relevance_score(hashtag, request)
            
            # Estimate usage and competition (would be real data from Twitter API)
            usage_count = self._estimate_usage_count(hashtag)
            competition_level = self._estimate_competition_level(hashtag)
            
            # Calculate engagement rate (would be based on historical data)
            engagement_rate = self._estimate_engagement_rate(hashtag, request.strategy)
            
            # Calculate growth rate
            growth_rate = self._estimate_growth_rate(hashtag)
            
            # Calculate trend momentum
            trend_momentum = self._calculate_trend_momentum(hashtag)
            
            return HashtagMetrics(
                hashtag=hashtag,
                usage_count=usage_count,
                growth_rate=growth_rate,
                engagement_rate=engagement_rate,
                competition_level=competition_level,
                relevance_score=relevance_score,
                trend_momentum=trend_momentum
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze hashtag {hashtag}: {e}")
            return None
    
    def _calculate_relevance_score(self, hashtag: str, request: HashtagGenerationRequest) -> float:
        """Calculate relevance score of hashtag to content and niche"""
        score = 0.0
        
        # Check presence in content
        if hashtag.lower() in request.content.lower():
            score += 0.3
        
        # Check relevance to niche keywords
        niche_text = ' '.join(request.niche_keywords).lower()
        if hashtag.lower() in niche_text:
            score += 0.4
        
        # Check word overlap
        hashtag_words = set(hashtag.lower().split())
        content_words = set(request.content.lower().split())
        niche_words = set(niche_text.split())
        
        content_overlap = len(hashtag_words & content_words) / max(len(hashtag_words), 1)
        niche_overlap = len(hashtag_words & niche_words) / max(len(hashtag_words), 1)
        
        score += content_overlap * 0.2
        score += niche_overlap * 0.3
        
        # Check semantic similarity (simplified)
        semantic_score = self._calculate_semantic_similarity(hashtag, request)
        score += semantic_score * 0.2
        
        return min(1.0, score)
    
    def _calculate_semantic_similarity(self, hashtag: str, request: HashtagGenerationRequest) -> float:
        """Calculate semantic similarity (simplified version)"""
        # This is a simplified semantic similarity calculation
        # In production, you might use word embeddings or semantic models
        
        similarity_keywords = {
            'tech': ['technology', 'innovation', 'digital', 'software', 'ai', 'ml'],
            'business': ['startup', 'entrepreneur', 'growth', 'strategy', 'success'],
            'social': ['community', 'network', 'connect', 'share', 'engage'],
            'learning': ['learn', 'education', 'tips', 'guide', 'tutorial']
        }
        
        max_similarity = 0.0
        hashtag_lower = hashtag.lower()
        content_lower = request.content.lower()
        
        for category, keywords in similarity_keywords.items():
            if any(keyword in hashtag_lower for keyword in keywords):
                if any(keyword in content_lower for keyword in keywords):
                    max_similarity = max(max_similarity, 0.8)
                elif category in content_lower:
                    max_similarity = max(max_similarity, 0.6)
        
        return max_similarity
    
    def _estimate_usage_count(self, hashtag: str) -> int:
        """Estimate hashtag usage count (would be from Twitter API)"""
        # Simplified estimation based on hashtag characteristics
        base_count = 1000
        
        # Popular patterns get higher usage
        if any(pattern in hashtag.lower() for pattern in ['tips', 'hack', '101', 'guide']):
            base_count *= 5
        
        # Shorter hashtags tend to be used more
        if len(hashtag) <= 8:
            base_count *= 2
        elif len(hashtag) >= 15:
            base_count //= 2
        
        # Add some randomness to simulate real data
        import random
        return int(base_count * (0.5 + random.random()))
    
    def _estimate_competition_level(self, hashtag: str) -> KeywordDifficulty:
        """Estimate competition level for hashtag"""
        # Simplified competition estimation
        if len(hashtag) <= 5 or hashtag.lower() in ['love', 'life', 'happy', 'good']:
            return KeywordDifficulty.VERY_HIGH
        elif len(hashtag) <= 8:
            return KeywordDifficulty.HIGH
        elif len(hashtag) <= 12:
            return KeywordDifficulty.MEDIUM
        else:
            return KeywordDifficulty.LOW
    
    def _estimate_engagement_rate(self, hashtag: str, strategy: HashtagStrategy) -> float:
        """Estimate engagement rate for hashtag"""
        base_rate = 0.03  # 3% base engagement rate
        
        # Strategy-based adjustments
        if strategy == HashtagStrategy.ENGAGEMENT_OPTIMIZED:
            if any(word in hashtag.lower() for word in ['question', 'ask', 'help', 'tips']):
                base_rate *= 1.5
        
        elif strategy == HashtagStrategy.NICHE_SPECIFIC:
            # Niche hashtags typically have higher engagement in smaller communities
            base_rate *= 1.3
        
        # Length-based adjustment
        if 6 <= len(hashtag) <= 12:
            base_rate *= 1.2  # Sweet spot for engagement
        
        return min(0.15, base_rate)  # Cap at 15%
    
    def _estimate_growth_rate(self, hashtag: str) -> float:
        """Estimate hashtag growth rate"""
        # Simplified growth estimation
        if any(word in hashtag.lower() for word in ['new', 'trending', 'viral', '2024', '2025']):
            return 25.0  # 25% growth
        elif any(word in hashtag.lower() for word in ['ai', 'ml', 'blockchain', 'crypto']):
            return 15.0  # 15% growth for tech trends
        else:
            return 5.0  # 5% baseline growth
    
    def _calculate_trend_momentum(self, hashtag: str) -> float:
        """Calculate trend momentum score"""
        # This would analyze recent usage patterns
        # For now, return a simplified momentum score
        
        momentum_indicators = ['trending', 'viral', 'hot', 'new', 'breaking', 'latest']
        if any(indicator in hashtag.lower() for indicator in momentum_indicators):
            return 0.8
        
        # Time-sensitive hashtags
        current_year = str(datetime.now().year)
        if current_year in hashtag:
            return 0.7
        
        return 0.4  # Default momentum
    
    def _rank_hashtags_by_strategy(self, hashtags: List[HashtagMetrics], 
                                  strategy: HashtagStrategy) -> List[HashtagMetrics]:
        """Rank hashtags based on optimization strategy"""
        
        def score_function(hashtag: HashtagMetrics) -> float:
            if strategy == HashtagStrategy.ENGAGEMENT_OPTIMIZED:
                return (hashtag.engagement_rate * 0.4 + 
                       hashtag.relevance_score * 0.3 + 
                       (1 - hashtag.competition_level.value.__hash__() / 10) * 0.3)
            
            elif strategy == HashtagStrategy.DISCOVERY_FOCUSED:
                return (hashtag.usage_count / 10000 * 0.4 + 
                       hashtag.trend_momentum * 0.3 + 
                       hashtag.relevance_score * 0.3)
            
            elif strategy == HashtagStrategy.BRAND_BUILDING:
                return (hashtag.relevance_score * 0.5 + 
                       hashtag.engagement_rate * 0.3 + 
                       hashtag.trend_momentum * 0.2)
            
            else:  # Default scoring
                return (hashtag.relevance_score * 0.4 + 
                       hashtag.engagement_rate * 0.3 + 
                       hashtag.trend_momentum * 0.3)
        
        return sorted(hashtags, key=score_function, reverse=True)
    
    def _fetch_trending_data(self) -> List[str]:
        """Fetch trending hashtags data (would integrate with Twitter API)"""
        # Simulated trending hashtags - in production this would call Twitter API
        return [
            'ai', 'innovation', 'startup', 'tech', 'growth',
            'productivity', 'leadership', 'entrepreneur', 'digital',
            'future', 'trends', 'business', 'success', 'networking'
        ]
    
    def analyze_competitor_hashtags(self, competitor_handles: List[str]) -> CompetitorHashtagAnalysis:
        """Analyze competitor hashtag usage patterns"""
        try:
            # This would analyze competitor tweets to find hashtag patterns
            # For now, return simulated analysis
            
            competitor_analysis = CompetitorHashtagAnalysis(
                competitor_name="Combined Analysis",
                top_hashtags=['startup', 'innovation', 'tech', 'business', 'growth'],
                hashtag_frequency={
                    'startup': 45,
                    'innovation': 38,
                    'tech': 35,
                    'business': 32,
                    'growth': 28
                },
                engagement_correlation={
                    'startup': 0.85,
                    'innovation': 0.78,
                    'tech': 0.72,
                    'business': 0.68,
                    'growth': 0.75
                },
                unique_hashtags=['disrupt', 'scale', 'pivot', 'mvp', 'unicorn'],
                gap_opportunities=['emerging', 'breakthrough', 'gamechange', 'nextgen']
            )
            
            return competitor_analysis
            
        except Exception as e:
            logger.error(f"Competitor hashtag analysis failed: {e}")
            return CompetitorHashtagAnalysis(
                competitor_name="Analysis Failed",
                top_hashtags=[],
                hashtag_frequency={},
                engagement_correlation={},
                unique_hashtags=[],
                gap_opportunities=[]
            )
    
    def get_hashtag_performance_insights(self, hashtags: List[str], 
                                       time_period_days: int = 30) -> Dict[str, Any]:
        """Get performance insights for specific hashtags"""
        try:
            insights = {
                'hashtag_performance': {},
                'best_performing': [],
                'worst_performing': [],
                'trending_up': [],
                'trending_down': [],
                'recommendations': []
            }
            
            for hashtag in hashtags:
                # Simulate performance data
                performance = {
                    'reach': 1000 + len(hashtag) * 100,
                    'engagement_rate': 0.03 + (len(hashtag) % 3) * 0.01,
                    'growth_rate': 5.0 + (len(hashtag) % 5) * 2.0,
                    'competition_score': 0.5 + (len(hashtag) % 4) * 0.1
                }
                insights['hashtag_performance'][hashtag] = performance
                
                # Categorize hashtags
                if performance['engagement_rate'] > 0.04:
                    insights['best_performing'].append(hashtag)
                elif performance['engagement_rate'] < 0.025:
                    insights['worst_performing'].append(hashtag)
                
                if performance['growth_rate'] > 8.0:
                    insights['trending_up'].append(hashtag)
                elif performance['growth_rate'] < 3.0:
                    insights['trending_down'].append(hashtag)
            
            # Generate recommendations
            insights['recommendations'] = [
                "Focus more on hashtags with engagement rates above 4%",
                "Consider replacing underperforming hashtags",
                "Leverage trending hashtags for increased visibility",
                "Balance popular and niche hashtags for optimal reach"
            ]
            
            return insights
            
        except Exception as e:
            logger.error(f"Hashtag performance analysis failed: {e}")
            return {}
    
    def optimize_hashtags_for_content_type(self, hashtags: List[str], 
                                         content_type: SEOContentType) -> List[str]:
        """Optimize hashtags specifically for content type"""
        
        # Content type specific optimization rules
        optimization_rules = {
            SEOContentType.TWEET: {
                'max_hashtags': 5,
                'preferred_length': (3, 12),
                'avoid_patterns': ['thread', 'story']
            },
            SEOContentType.THREAD: {
                'max_hashtags': 3,
                'preferred_length': (4, 15),
                'preferred_patterns': ['thread', 'story', 'insights']
            },
            SEOContentType.REPLY: {
                'max_hashtags': 2,
                'preferred_length': (3, 10),
                'preferred_patterns': ['discussion', 'thoughts']
            },
            SEOContentType.QUOTE_TWEET: {
                'max_hashtags': 3,
                'preferred_length': (3, 12),
                'preferred_patterns': ['quote', 'perspective']
            }
        }
        
        rules = optimization_rules.get(content_type, optimization_rules[SEOContentType.TWEET])
        
        # Filter and optimize hashtags
        optimized = []
        for hashtag in hashtags:
            # Check length constraints
            if rules['preferred_length'][0] <= len(hashtag) <= rules['preferred_length'][1]:
                # Check avoid patterns
                if 'avoid_patterns' in rules:
                    if any(pattern in hashtag.lower() for pattern in rules['avoid_patterns']):
                        continue
                
                optimized.append(hashtag)
                
                if len(optimized) >= rules['max_hashtags']:
                    break
        
        return optimized

class TrendingHashtagAnalyzer:
    """Analyzes trending hashtags and their performance"""
    
    def __init__(self, twitter_client=None):
        self.twitter_client = twitter_client
        self.trending_cache = {}
        self.cache_duration = timedelta(hours=1)
    
    def get_trending_hashtags_by_location(self, woeid: int = 1) -> List[HashtagMetrics]:
        """Get trending hashtags for specific location"""
        try:
            cache_key = f"trending_{woeid}"
            now = datetime.now()
            
            # Check cache
            if cache_key in self.trending_cache:
                cached_data, timestamp = self.trending_cache[cache_key]
                if now - timestamp < self.cache_duration:
                    return cached_data
            
            # Fetch trending data (would use Twitter API)
            trending_data = self._fetch_trending_data(woeid)
            hashtag_metrics = []
            
            for trend in trending_data:
                metrics = HashtagMetrics(
                    hashtag=trend['name'].replace('#', ''),
                    usage_count=trend.get('tweet_volume', 1000),
                    growth_rate=self._estimate_growth_rate(trend),
                    engagement_rate=self._estimate_engagement_rate(trend),
                    competition_level=self._assess_competition(trend),
                    relevance_score=0.8,  # High for trending
                    trend_momentum=0.9
                )
                hashtag_metrics.append(metrics)
            
            # Cache results
            self.trending_cache[cache_key] = (hashtag_metrics, now)
            return hashtag_metrics
            
        except Exception as e:
            logger.error(f"Failed to get trending hashtags: {e}")
            return []
    
    def _fetch_trending_data(self, woeid: int) -> List[Dict[str, Any]]:
        """Fetch trending data from Twitter API"""
        if self.twitter_client:
            try:
                # Would integrate with actual Twitter API
                return self.twitter_client.get_trends_for_location(woeid)
            except Exception as e:
                logger.warning(f"Twitter API failed: {e}")
        
        # Fallback simulated trending data
        return [
            {'name': '#AI', 'tweet_volume': 50000},
            {'name': '#Innovation', 'tweet_volume': 30000},
            {'name': '#Startup', 'tweet_volume': 25000},
            {'name': '#Tech', 'tweet_volume': 40000},
            {'name': '#Productivity', 'tweet_volume': 15000}
        ]
    
    def _estimate_growth_rate(self, trend: Dict[str, Any]) -> float:
        """Estimate hashtag growth rate"""
        volume = trend.get('tweet_volume', 1000)
        
        # Simple heuristic based on volume
        if volume > 100000:
            return 50.0  # High growth
        elif volume > 50000:
            return 30.0
        elif volume > 10000:
            return 15.0
        else:
            return 5.0
    
    def _estimate_engagement_rate(self, trend: Dict[str, Any]) -> float:
        """Estimate engagement rate for trending hashtag"""
        # Trending hashtags typically have higher engagement
        base_rate = 0.05  # 5% base rate for trending
        
        # Adjust based on characteristics
        name = trend.get('name', '').lower()
        if any(word in name for word in ['question', 'challenge', 'vote']):
            base_rate *= 1.5
        
        return min(0.15, base_rate)
    
    def _assess_competition(self, trend: Dict[str, Any]) -> KeywordDifficulty:
        """Assess competition level for trending hashtag"""
        volume = trend.get('tweet_volume', 1000)
        
        if volume > 100000:
            return KeywordDifficulty.VERY_HIGH
        elif volume > 50000:
            return KeywordDifficulty.HIGH
        elif volume > 10000:
            return KeywordDifficulty.MEDIUM
        else:
            return KeywordDifficulty.LOW

class HashtagPerformanceTracker:
    """Tracks hashtag performance over time"""
    
    def __init__(self, data_storage=None):
        self.data_storage = data_storage
        self.performance_history = defaultdict(list)
    
    def track_hashtag_performance(self, hashtag: str, metrics: Dict[str, float]) -> None:
        """Track performance metrics for a hashtag"""
        try:
            performance_entry = {
                'hashtag': hashtag,
                'timestamp': datetime.utcnow(),
                'reach': metrics.get('reach', 0),
                'impressions': metrics.get('impressions', 0),
                'engagement_rate': metrics.get('engagement_rate', 0),
                'click_rate': metrics.get('click_rate', 0),
                'conversion_rate': metrics.get('conversion_rate', 0)
            }
            
            self.performance_history[hashtag].append(performance_entry)
            
            # Store in database if available
            if self.data_storage:
                self.data_storage.store_hashtag_performance(performance_entry)
            
            logger.info(f"Tracked performance for #{hashtag}")
            
        except Exception as e:
            logger.error(f"Failed to track hashtag performance: {e}")
    
    def get_hashtag_performance_trend(self, hashtag: str, days: int = 30) -> Dict[str, Any]:
        """Get performance trend for a hashtag"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            recent_entries = [
                entry for entry in self.performance_history[hashtag]
                if entry['timestamp'] > cutoff_date
            ]
            
            if not recent_entries:
                return {'trend': 'no_data'}
            
            # Calculate trend
            engagement_rates = [entry['engagement_rate'] for entry in recent_entries]
            reach_values = [entry['reach'] for entry in recent_entries]
            
            avg_engagement = sum(engagement_rates) / len(engagement_rates)
            avg_reach = sum(reach_values) / len(reach_values)
            
            # Determine trend direction
            if len(engagement_rates) >= 2:
                recent_avg = sum(engagement_rates[-3:]) / min(3, len(engagement_rates))
                early_avg = sum(engagement_rates[:3]) / min(3, len(engagement_rates))
                
                if recent_avg > early_avg * 1.1:
                    trend = 'improving'
                elif recent_avg < early_avg * 0.9:
                    trend = 'declining'
                else:
                    trend = 'stable'
            else:
                trend = 'insufficient_data'
            
            return {
                'hashtag': hashtag,
                'trend': trend,
                'avg_engagement_rate': avg_engagement,
                'avg_reach': avg_reach,
                'total_entries': len(recent_entries),
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance trend: {e}")
            return {'trend': 'error'}
    
    def get_top_performing_hashtags(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing hashtags based on recent data"""
        try:
            hashtag_scores = {}
            
            for hashtag, entries in self.performance_history.items():
                if not entries:
                    continue
                
                # Calculate composite score
                recent_entries = entries[-5:]  # Last 5 entries
                avg_engagement = sum(e['engagement_rate'] for e in recent_entries) / len(recent_entries)
                avg_reach = sum(e['reach'] for e in recent_entries) / len(recent_entries)
                
                # Composite score (weighted)
                score = (avg_engagement * 0.6) + (avg_reach / 10000 * 0.4)
                hashtag_scores[hashtag] = {
                    'hashtag': hashtag,
                    'score': score,
                    'avg_engagement_rate': avg_engagement,
                    'avg_reach': avg_reach,
                    'entry_count': len(recent_entries)
                }
            
            # Sort by score and return top performers
            top_hashtags = sorted(
                hashtag_scores.values(), 
                key=lambda x: x['score'], 
                reverse=True
            )
            
            return top_hashtags[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get top performing hashtags: {e}")
            return []

class HashtagRecommendationEngine:
    """Advanced hashtag recommendation system"""
    
    def __init__(self, hashtag_generator: HashtagGenerator,
                 trending_analyzer: TrendingHashtagAnalyzer,
                 performance_tracker: HashtagPerformanceTracker):
        self.hashtag_generator = hashtag_generator
        self.trending_analyzer = trending_analyzer
        self.performance_tracker = performance_tracker
    
    def get_comprehensive_recommendations(self, request: HashtagGenerationRequest,
                                        user_history: List[str] = None) -> Dict[str, List[HashtagMetrics]]:
        """Get comprehensive hashtag recommendations"""
        try:
            recommendations = {
                'primary': [],      # Best overall recommendations
                'trending': [],     # Currently trending
                'niche': [],       # Niche-specific
                'engagement': [],   # High engagement potential
                'discovery': []     # Good for discovery
            }
            
            # Get base recommendations
            base_hashtags = self.hashtag_generator.generate_hashtags(request)
            
            # Get trending hashtags
            trending_hashtags = self.trending_analyzer.get_trending_hashtags_by_location()
            
            # Get user's historical performance
            top_performing = []
            if user_history:
                for hashtag in user_history:
                    trend = self.performance_tracker.get_hashtag_performance_trend(hashtag)
                    if trend.get('trend') == 'improving':
                        # Convert to HashtagMetrics format
                        metrics = HashtagMetrics(
                            hashtag=hashtag,
                            usage_count=1000,
                            growth_rate=20.0,
                            engagement_rate=trend.get('avg_engagement_rate', 0.03),
                            competition_level=KeywordDifficulty.MEDIUM,
                            relevance_score=0.8,
                            trend_momentum=0.8
                        )
                        top_performing.append(metrics)
            
            # Categorize recommendations
            for hashtag in base_hashtags:
                # Primary recommendations (high relevance + good engagement)
                if hashtag.relevance_score > 0.7 and hashtag.engagement_rate > 0.03:
                    recommendations['primary'].append(hashtag)
                
                # Niche recommendations (high relevance, lower competition)
                if (hashtag.relevance_score > 0.8 and 
                    hashtag.competition_level in [KeywordDifficulty.LOW, KeywordDifficulty.MEDIUM]):
                    recommendations['niche'].append(hashtag)
                
                # Engagement recommendations (high engagement potential)
                if hashtag.engagement_rate > 0.04:
                    recommendations['engagement'].append(hashtag)
                
                # Discovery recommendations (good balance)
                if (hashtag.trend_momentum > 0.6 and 
                    hashtag.competition_level != KeywordDifficulty.VERY_HIGH):
                    recommendations['discovery'].append(hashtag)
            
            # Add trending hashtags that are relevant
            for trending in trending_hashtags:
                if any(keyword.lower() in trending.hashtag.lower() 
                       for keyword in request.niche_keywords):
                    recommendations['trending'].append(trending)
            
            # Add historical top performers
            recommendations['primary'].extend(top_performing)
            
            # Limit each category and remove duplicates
            for category in recommendations:
                # Remove duplicates based on hashtag name
                seen = set()
                unique_hashtags = []
                for ht in recommendations[category]:
                    if ht.hashtag.lower() not in seen:
                        seen.add(ht.hashtag.lower())
                        unique_hashtags.append(ht)
                
                recommendations[category] = unique_hashtags[:8]  # Limit per category
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to get comprehensive recommendations: {e}")
            return {key: [] for key in ['primary', 'trending', 'niche', 'engagement', 'discovery']}
    
    def optimize_hashtag_mix(self, hashtags: List[HashtagMetrics], 
                           strategy: HashtagStrategy) -> List[HashtagMetrics]:
        """Optimize hashtag mix based on strategy"""
        try:
            if not hashtags:
                return []
            
            if strategy == HashtagStrategy.ENGAGEMENT_OPTIMIZED:
                # Prioritize engagement rate and relevance
                return sorted(hashtags, 
                            key=lambda h: h.engagement_rate * h.relevance_score, 
                            reverse=True)
            
            elif strategy == HashtagStrategy.TRENDING_FOCUS:
                # Prioritize trend momentum and growth
                return sorted(hashtags,
                            key=lambda h: h.trend_momentum * (h.growth_rate / 100),
                            reverse=True)
            
            elif strategy == HashtagStrategy.DISCOVERY_FOCUSED:
                # Balance reach potential with competition
                def discovery_score(h):
                    competition_penalty = {
                        KeywordDifficulty.LOW: 1.0,
                        KeywordDifficulty.MEDIUM: 0.8,
                        KeywordDifficulty.HIGH: 0.6,
                        KeywordDifficulty.VERY_HIGH: 0.3
                    }.get(h.competition_level, 0.5)
                    
                    return (h.usage_count / 10000) * competition_penalty * h.relevance_score
                
                return sorted(hashtags, key=discovery_score, reverse=True)
            
            elif strategy == HashtagStrategy.NICHE_SPECIFIC:
                # Prioritize relevance and niche targeting
                return sorted(hashtags,
                            key=lambda h: h.relevance_score * (2 - h.competition_level.value.__hash__() / 10),
                            reverse=True)
            
            else:  # BRAND_BUILDING
                # Balance relevance, engagement, and sustainable growth
                def brand_score(h):
                    return (h.relevance_score * 0.4 + 
                           h.engagement_rate * 10 * 0.3 +
                           h.trend_momentum * 0.3)
                
                return sorted(hashtags, key=brand_score, reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to optimize hashtag mix: {e}")
            return hashtags
    
    def generate_hashtag_calendar(self, hashtags: List[HashtagMetrics],
                                days: int = 7) -> Dict[str, List[str]]:
        """Generate a hashtag calendar for optimal posting schedule"""
        try:
            calendar = {}
            hashtag_pool = [h.hashtag for h in hashtags]
            
            # Rotate hashtags across days to avoid repetition
            for day in range(days):
                day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                           'Friday', 'Saturday', 'Sunday'][day % 7]
                
                # Select hashtags for this day (avoid immediate repetition)
                day_hashtags = []
                start_idx = (day * 3) % len(hashtag_pool)
                
                for i in range(5):  # 5 hashtags per day
                    idx = (start_idx + i) % len(hashtag_pool)
                    day_hashtags.append(hashtag_pool[idx])
                
                calendar[day_name] = day_hashtags
            
            return calendar
            
        except Exception as e:
            logger.error(f"Failed to generate hashtag calendar: {e}")
            return {}

# Enhanced HashtagGenerator with new components
class EnhancedHashtagGenerator(HashtagGenerator):
    """Enhanced hashtag generator with advanced features"""
    
    def __init__(self, twitter_client=None, config: Dict[str, Any] = None):
        super().__init__(twitter_client, config)
        
        # Initialize enhanced components
        self.trending_analyzer = TrendingHashtagAnalyzer(twitter_client)
        self.performance_tracker = HashtagPerformanceTracker()
        self.recommendation_engine = HashtagRecommendationEngine(
            self, self.trending_analyzer, self.performance_tracker
        )
    
    def get_smart_recommendations(self, request: HashtagGenerationRequest,
                                user_history: List[str] = None) -> Dict[str, Any]:
        """Get smart hashtag recommendations with multiple strategies"""
        try:
            # Get comprehensive recommendations
            recommendations = self.recommendation_engine.get_comprehensive_recommendations(
                request, user_history
            )
            
            # Optimize primary recommendations
            if recommendations['primary']:
                recommendations['optimized_primary'] = self.recommendation_engine.optimize_hashtag_mix(
                    recommendations['primary'], request.strategy
                )
            
            # Generate calendar
            all_hashtags = []
            for category_hashtags in recommendations.values():
                all_hashtags.extend(category_hashtags)
            
            if all_hashtags:
                recommendations['weekly_calendar'] = self.recommendation_engine.generate_hashtag_calendar(
                    all_hashtags[:20]  # Top 20 for calendar
                )
            
            # Add usage tips
            recommendations['usage_tips'] = self._generate_usage_tips(request.content_type)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Smart recommendations failed: {e}")
            return {}
    
    def _generate_usage_tips(self, content_type: SEOContentType) -> List[str]:
        """Generate usage tips for hashtag optimization"""
        base_tips = [
            "Use a mix of popular and niche hashtags",
            "Monitor hashtag performance and adjust strategy",
            "Avoid banned or overused hashtags",
            "Keep hashtags relevant to your content"
        ]
        
        type_specific_tips = {
            SEOContentType.TWEET: [
                "Use 3-5 hashtags maximum for tweets",
                "Place hashtags at the end of your tweet",
                "Research hashtag trends before posting"
            ],
            SEOContentType.THREAD: [
                "Use hashtags mainly in the first tweet",
                "Add 2-3 relevant hashtags per thread",
                "Include one trending hashtag if relevant"
            ],
            SEOContentType.REPLY: [
                "Use 1-2 hashtags maximum in replies",
                "Focus on conversational hashtags",
                "Avoid excessive hashtag use in replies"
            ]
        }
        
        return base_tips + type_specific_tips.get(content_type, [])