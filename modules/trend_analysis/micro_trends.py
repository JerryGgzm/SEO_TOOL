import math
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import numpy as np
import logging

from .models import TrendMetrics, AnalyzedTrend

logger = logging.getLogger(__name__)

class MicroTrendDetector:
    """Detects emerging micro-trends based on velocity and growth patterns"""
    
    def __init__(self, config: Dict[str, any] = None):
        self.config = config or {}
        
        # Default thresholds
        self.velocity_threshold = self.config.get('velocity_threshold', 2.0)
        self.min_tweet_volume = self.config.get('min_tweet_volume', 50)
        self.early_adopter_threshold = self.config.get('early_adopter_threshold', 0.2)
        self.acceleration_threshold = self.config.get('acceleration_threshold', 1.5)
    
    def calculate_trend_velocity(self, tweets: List[Dict[str, any]], 
                                time_window_hours: float = 24.0) -> float:
        """
        Calculate trend velocity based on tweet frequency over time
        
        Args:
            tweets: List of tweet data with 'created_at' timestamps
            time_window_hours: Time window for velocity calculation
            
        Returns:
            Velocity score (tweets per hour)
        """
        if not tweets:
            return 0.0
        
        # Convert all timestamps to timezone-aware datetime objects
        timestamps = []
        for tweet in tweets:
            created_at = tweet.get('created_at')
            if isinstance(created_at, str):
                # Parse string timestamp and make it timezone-aware
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            elif isinstance(created_at, datetime):
                # Make timezone-aware if it's naive
                if created_at.tzinfo is None:
                    dt = created_at.replace(tzinfo=timezone.utc)
                else:
                    dt = created_at
            else:
                continue
            timestamps.append(dt)
        
        if len(timestamps) < 2:
            return 0.0
        
        # Sort timestamps
        timestamps.sort()
        
        # Calculate time span
        time_span = timestamps[-1] - timestamps[0]
        time_span_hours = time_span.total_seconds() / 3600
        
        if time_span_hours == 0:
            return 0.0
        
        # Calculate velocity (tweets per hour)
        velocity = len(timestamps) / time_span_hours
        
        return velocity
    
    def analyze_early_adopters(self, tweets: List[Dict[str, any]]) -> float:
        """
        Analyze the ratio of early adopters in the trend
        
        Args:
            tweets: List of tweet data with user information
            
        Returns:
            Early adopter ratio (0.0 to 1.0)
        """
        if not tweets:
            return 0.0
        
        early_adopter_indicators = 0
        total_users = 0
        user_scores = {}
        
        for tweet in tweets:
            author_id = tweet.get('author_id')
            if not author_id:
                continue
            
            # Skip if we've already analyzed this user
            if author_id in user_scores:
                continue
            
            total_users += 1
            
            # Get user metrics from expanded data
            user_data = tweet.get('includes', {}).get('users', [])
            user_info = None
            
            for user in user_data:
                if user.get('id') == author_id:
                    user_info = user
                    break
            
            if not user_info:
                continue
            
            # Analyze early adopter signals
            public_metrics = user_info.get('public_metrics', {})
            followers_count = public_metrics.get('followers_count', 0)
            following_count = public_metrics.get('following_count', 0)
            tweet_count = public_metrics.get('tweet_count', 0)
            
            # Early adopter scoring criteria
            score = 0
            
            # Moderate follower count (not mainstream, not too small)
            if 1000 <= followers_count <= 50000:
                score += 1
            
            # High following to follower ratio (actively discovering new content)
            if followers_count > 0 and following_count / followers_count > 0.5:
                score += 1
            
            # Active tweeter
            if tweet_count > 500:
                score += 1
            
            # Verified but not celebrity level
            if user_info.get('verified') and followers_count < 100000:
                score += 1
            
            # Bio contains innovation/tech keywords
            description = user_info.get('description', '').lower()
            innovation_keywords = [
                'entrepreneur', 'startup', 'founder', 'innovation', 'tech',
                'developer', 'designer', 'product', 'early adopter', 'beta'
            ]
            if any(keyword in description for keyword in innovation_keywords):
                score += 1
            
            user_scores[author_id] = score
            
            # Consider early adopter if score >= 2
            if score >= 2:
                early_adopter_indicators += 1
        
        if total_users == 0:
            return 0.0
        
        return early_adopter_indicators / total_users
    
    def calculate_trend_potential_score(self, velocity_score: float, 
                                      early_adopter_ratio: float,
                                      engagement_metrics: Dict[str, any],
                                      relevance_score: float) -> float:
        """
        Calculate overall trend potential score
        
        Args:
            velocity_score: Growth velocity
            early_adopter_ratio: Ratio of early adopters
            engagement_metrics: Engagement statistics
            relevance_score: Relevance to user's niche
            
        Returns:
            Overall potential score (0.0 to 1.0)
        """
        # Normalize velocity score (log scale to handle wide range)
        normalized_velocity = min(1.0, math.log(velocity_score + 1) / math.log(10))
        
        # Weight factors
        velocity_weight = 0.3
        adopter_weight = 0.25
        engagement_weight = 0.25
        relevance_weight = 0.2
        
        # Calculate engagement score
        avg_engagement = engagement_metrics.get('avg_engagement_rate', 0)
        normalized_engagement = min(1.0, avg_engagement / 0.1)  # Normalize to 10% max
        
        # Combine scores
        potential_score = (
            normalized_velocity * velocity_weight +
            early_adopter_ratio * adopter_weight +
            normalized_engagement * engagement_weight +
            relevance_score * relevance_weight
        )
        
        return min(1.0, potential_score)
    
    def detect_micro_trends(self, analyzed_trends: List[AnalyzedTrend]) -> List[AnalyzedTrend]:
        """
        Identify which analyzed trends qualify as micro-trends
        
        Args:
            analyzed_trends: List of analyzed trends
            
        Returns:
            List of trends identified as micro-trends
        """
        micro_trends = []
        
        for trend in analyzed_trends:
            # Check minimum volume requirement
            if trend.tweet_volume and trend.tweet_volume < self.min_tweet_volume:
                continue
            
            # Check velocity threshold
            if not trend.velocity_score or trend.velocity_score < self.velocity_threshold:
                continue
            
            # Check early adopter ratio
            if not trend.early_adopter_ratio or trend.early_adopter_ratio < self.early_adopter_threshold:
                continue
            
            # Check overall potential
            if trend.trend_potential_score < 0.5:  # Minimum potential threshold
                continue
            
            # Mark as micro-trend
            trend.is_micro_trend = True
            micro_trends.append(trend)
        
        # Sort by potential score
        micro_trends.sort(key=lambda t: t.trend_potential_score, reverse=True)
        
        return micro_trends
