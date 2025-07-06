"""Hashtag generation and optimization engine"""
import re
import math
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import logging

from .models import (
    HashtagMetrics, HashtagStrategy, SEOContentType, KeywordDifficulty,
    HashtagGenerationRequest
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