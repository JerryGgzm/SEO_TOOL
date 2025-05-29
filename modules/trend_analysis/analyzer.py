"""Trend analyzer""" 
import asyncio
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta, timezone
import json
import logging
from collections import defaultdict

from modules.twitter_api import TwitterAPIClient, TwitterAPIError
from modules.user_profile import UserProfileService
from .models import (
    AnalyzedTrend, TrendAnalysisRequest, TrendAnalysisConfig,
    TrendMetrics, ExampleTweet, TopicCluster, TrendSource,
    SentimentBreakdown, SentimentLabel
)
from .data_processor import TweetPreprocessor, TrendDataProcessor
from .sentiment import SentimentAnalyzer
from .micro_trends import MicroTrendDetector

logger = logging.getLogger(__name__)

class LLMInsightExtractor:
    """Extracts insights using LLM for pain points and opportunities"""
    
    def __init__(self, llm_client=None, model_name: str = "gpt-3.5-turbo"):
        self.llm_client = llm_client
        self.model_name = model_name
    
    def extract_pain_points_and_opportunities(self, tweets: List[str], 
                                            topic_name: str, 
                                            niche_context: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """
        Extract pain points and business opportunities using LLM
        
        Args:
            tweets: Sample tweets about the trend
            topic_name: Name of the trend topic
            niche_context: User's niche and product information
            
        Returns:
            Tuple of (pain_points, opportunities)
        """
        if not self.llm_client or not tweets:
            return [], []
        
        try:
            # Prepare context
            product_info = niche_context.get('product_info', {})
            niche_keywords = niche_context.get('niche_keywords', [])
            
            # Create prompt for pain point extraction
            pain_point_prompt = self._create_pain_point_prompt(
                tweets[:20],  # Limit to first 20 tweets
                topic_name,
                product_info,
                niche_keywords
            )
            
            # Call LLM for pain points
            pain_points_response = self._call_llm(pain_point_prompt)
            pain_points = self._parse_list_response(pain_points_response)
            
            # Create prompt for opportunity extraction
            opportunity_prompt = self._create_opportunity_prompt(
                tweets[:20],
                topic_name,
                product_info,
                niche_keywords,
                pain_points
            )
            
            # Call LLM for opportunities
            opportunities_response = self._call_llm(opportunity_prompt)
            opportunities = self._parse_list_response(opportunities_response)
            
            return pain_points[:10], opportunities[:10]  # Limit results
            
        except Exception as e:
            logger.error(f"LLM insight extraction failed: {e}")
            return [], []
    
    def _create_pain_point_prompt(self, tweets: List[str], topic_name: str, 
                                product_info: Dict, niche_keywords: List[str]) -> str:
        """Create prompt for pain point extraction"""
        tweets_text = "\n".join([f"- {tweet}" for tweet in tweets])
        keywords_text = ", ".join(niche_keywords[:10])
        
        prompt = f"""
Analyze the following tweets about "{topic_name}" and identify the main pain points, problems, or frustrations that users are expressing.

Context: This is for a {product_info.get('product_name', 'product')} in the {keywords_text} space.

Tweets:
{tweets_text}

Please extract 5-10 specific pain points or problems that users are discussing. Format your response as a simple list:
1. [Pain point 1]
2. [Pain point 2]
...

Focus on actionable problems that could potentially be solved by products or services.
"""
        return prompt
    
    def _create_opportunity_prompt(self, tweets: List[str], topic_name: str,
                                 product_info: Dict, niche_keywords: List[str],
                                 pain_points: List[str]) -> str:
        """Create prompt for opportunity extraction"""
        tweets_text = "\n".join([f"- {tweet}" for tweet in tweets])
        keywords_text = ", ".join(niche_keywords[:10])
        pain_points_text = "\n".join([f"- {pp}" for pp in pain_points])
        
        prompt = f"""
Based on the following tweets about "{topic_name}" and the identified pain points, suggest business opportunities or solutions.

Context: This is for a {product_info.get('product_name', 'product')} in the {keywords_text} space.

Pain Points Identified:
{pain_points_text}

Sample Tweets:
{tweets_text}

Please identify 5-10 specific business opportunities or solutions that could address these pain points. Format your response as a simple list:
1. [Opportunity 1]
2. [Opportunity 2]
...

Focus on actionable opportunities that align with the product/service context.
"""
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM with the given prompt"""
        if not self.llm_client:
            return ""
        
        try:
            # This would be implemented based on your LLM client
            # Example for OpenAI client:
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert business analyst specializing in identifying market opportunities from social media trends."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return ""
    
    def _parse_list_response(self, response: str) -> List[str]:
        """Parse LLM response into a list of items"""
        if not response:
            return []
        
        lines = response.strip().split('\n')
        items = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove list numbering and bullet points
            if line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.')):
                line = line[2:].strip()
            elif line.startswith('-'):
                line = line[1:].strip()
            elif line.startswith('•'):
                line = line[1:].strip()
            
            if line and len(line) > 5:  # Filter out very short items
                items.append(line)
        
        return items

class TrendAnalysisEngine:
    """Main trend analysis engine that orchestrates all analysis components"""
    
    def __init__(self, twitter_client: TwitterAPIClient, 
                 user_service: UserProfileService,
                 config: TrendAnalysisConfig = None,
                 llm_client=None):
        self.twitter_client = twitter_client
        self.user_service = user_service
        self.config = config or TrendAnalysisConfig()
        self.data_processor = TrendDataProcessor()
        self.llm_client = llm_client
        
        # Initialize analysis components
        self.preprocessor = TweetPreprocessor()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.micro_trend_detector = MicroTrendDetector(self.config.dict())
        self.llm_extractor = LLMInsightExtractor(llm_client, self.config.llm_model_name)
    
    async def analyze_trends_for_user(self, user_id: str, 
                                    request: TrendAnalysisRequest) -> List[AnalyzedTrend]:
        """Analyze trends for a user"""
        try:
            logger.info(f"Start analyzing trends for user {user_id}")
            
            # get user profile
            user_profile = self.user_service.get_user_profile(user_id)
            if not user_profile:
                logger.warning(f"No user profile found for {user_id}")
                return []
            
            # get Twitter access token
            access_token = self.user_service.get_twitter_access_token(user_id)
            if not access_token:
                logger.warning(f"User {user_id} has no valid Twitter access token")
                return []
            
            # get trends data
            trends_data = await self._fetch_trends_data(request, access_token)
            if not trends_data:
                logger.warning(f"No trends data found")
                return []
            
            # analyze each trend - fix async processing here
            analyzed_trends = []
            for trend_data in trends_data[:request.max_trends_to_analyze]:
                try:
                    analyzed_trend = await self._analyze_single_trend(
                        trend_data, user_profile, request, access_token
                    )
                    if analyzed_trend:
                        analyzed_trends.append(analyzed_trend)
                except Exception as e:
                    logger.error(f"Failed to analyze a single trend: {e}")
                    continue
            
            logger.info(f"Successfully analyzed {len(analyzed_trends)} trends")
            return analyzed_trends
            
        except Exception as e:
            logger.error(f"Failed to analyze trends for user {user_id}: {e}")
            return []
    
    async def _get_trending_topics(self, access_token: str, location_id: int) -> List[Dict]:
        """Get trending topics from Twitter"""
        try:
            trends = await self.twitter_client.get_trends_for_location(access_token, location_id)
            return trends or []
        except TwitterAPIError as e:
            logger.error(f"Failed to get trending topics: {e}")
            return []
    
    async def _search_niche_trends(self, access_token: str, focus_keywords: List[str]) -> List[Dict]:
        """Search for trends in specific niche"""
        niche_trends = []
        
        for keyword in focus_keywords[:5]:  # Limit to prevent rate limiting
            try:
                query = f"{keyword} -is:retweet min_faves:10"
                
                search_results = self.twitter_client.search_tweets(
                    user_token=access_token,
                    query=query,
                    max_results=50,
                    tweet_fields=['created_at', 'public_metrics', 'context_annotations']
                )
                
                if search_results.get('data'):
                    # Create synthetic trend from search results
                    trend_data = {
                        'name': keyword,
                        'tweet_volume': len(search_results['data']),
                        'url': f"search?q={keyword}",
                        'source': 'keyword_search',
                        'search_results': search_results
                    }
                    niche_trends.append(trend_data)
                    
            except TwitterAPIError as e:
                logger.warning(f"Failed to search for keyword '{keyword}': {e}")
                continue
        
        return niche_trends
    
    def _combine_and_filter_trends(self, trending_topics: List[Dict], 
                                 niche_trends: List[Dict], 
                                 focus_keywords: List[str]) -> List[Dict]:
        """Combine and filter trend sources"""
        all_trends = []
        seen_names = set()
        
        # Add trending topics with relevance scoring
        for trend in trending_topics:
            trend_name = trend.get('name', '').lower()
            if trend_name in seen_names:
                continue
            
            relevance = self._calculate_keyword_relevance(trend_name, focus_keywords)
            if relevance > 0.1:  # Only include somewhat relevant trends
                trend['relevance_score'] = relevance
                trend['source'] = 'twitter_trending'
                all_trends.append(trend)
                seen_names.add(trend_name)
        
        # Add niche trends
        for trend in niche_trends:
            trend_name = trend.get('name', '').lower()
            if trend_name not in seen_names:
                trend['relevance_score'] = 0.8  # High relevance for niche searches
                all_trends.append(trend)
                seen_names.add(trend_name)
        
        # Sort by relevance
        all_trends.sort(key=lambda t: t.get('relevance_score', 0), reverse=True)
        
        return all_trends
    
    def _calculate_keyword_relevance(self, trend_name: str, focus_keywords: List[str]) -> float:
        """Calculate relevance of trend to focus keywords"""
        if not trend_name or not focus_keywords:
            return 0.0
        
        trend_words = set(trend_name.lower().split())
        keyword_words = set(' '.join(focus_keywords).lower().split())
        
        # Calculate Jaccard similarity
        intersection = trend_words.intersection(keyword_words)
        union = trend_words.union(keyword_words)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    async def _analyze_single_trend(self, trend_data: Dict[str, Any],
                                  user_profile: Any,
                                  request: TrendAnalysisRequest,
                                  access_token: str) -> Optional[AnalyzedTrend]:
        """Analyze a single trend"""
        try:
            trend_name = trend_data.get('name', '')
            
            # get tweet samples for the trend
            sample_tweets = await self._fetch_trend_tweets(
                trend_name, 
                request.tweet_sample_size,
                access_token
            )
            
            if not sample_tweets:
                logger.warning(f"Did not get tweet samples for {trend_name}")
                return None

            processed_data = self.data_processor.process_tweets(sample_tweets)

            relevance_score = self._calculate_niche_relevance(
                trend_data, user_profile, processed_data
            )

            print("processed_data: ", processed_data)

            is_micro_trend = self._detect_micro_trend(trend_data, processed_data)

            content_suggestions = await self._generate_content_suggestions(
                trend_data, user_profile, processed_data
            )

            from .models import AnalyzedTrend, TrendSource, SentimentBreakdown, TrendMetrics

            # create basic sentiment analysis results
            sentiment_score = processed_data.get('sentiment_score', 0.5)
            positive_score = max(0.0, sentiment_score)
            negative_score = max(0.0, 1.0 - sentiment_score)
            neutral_score = 0.5
            
            # normalize scores, ensure total sum is 1
            total_score = positive_score + negative_score + neutral_score
            if total_score > 0:
                positive_score /= total_score
                negative_score /= total_score
                neutral_score /= total_score
            
            print("positive_score: ", positive_score)
            print("negative_score: ", negative_score)
            print("neutral_score: ", neutral_score)
            # determine dominant sentiment
            if positive_score > negative_score and positive_score > neutral_score:
                dominant_sentiment = SentimentLabel.POSITIVE
            elif negative_score > positive_score and negative_score > neutral_score:
                dominant_sentiment = SentimentLabel.NEGATIVE
            else:
                dominant_sentiment = SentimentLabel.NEUTRAL
            
            # calculate confidence (difference between highest and second highest score)
            scores = [positive_score, negative_score, neutral_score]
            scores.sort(reverse=True)
            confidence = scores[0] - scores[1] if len(scores) > 1 else scores[0]

            print("confidence: ", confidence)
            
            sentiment = SentimentBreakdown(
                positive_score=positive_score,
                negative_score=negative_score,
                neutral_score=neutral_score,
                dominant_sentiment=dominant_sentiment,
                confidence=confidence
            )

            print("sentiment: ", sentiment)
            
            metrics = TrendMetrics(
                tweet_volume=processed_data.get('total_tweets', 0),
                engagement_volume=processed_data.get('total_engagement', 0),
                avg_engagement_rate=processed_data.get('avg_engagement_rate', 0.0),
                unique_users=len(set(tweet.get('author_id', '') for tweet in sample_tweets if tweet.get('author_id'))),
                time_span_hours=24.0,
                velocity_score=processed_data.get('momentum_score', 0.0)
            )

            print("metrics: ", metrics)
            
            # determine correct enum value based on trend source
            source = trend_data.get('source', 'twitter_trending')
            if source == 'keyword_search':
                trend_source = TrendSource.KEYWORD_SEARCH
            elif source == 'micro_trend_detection':
                trend_source = TrendSource.MICRO_TREND_DETECTION
            elif source == 'manual':
                trend_source = TrendSource.MANUAL
            else:
                trend_source = TrendSource.TWITTER_TRENDING
            
            return AnalyzedTrend(
                trend_name=trend_name,
                trend_type="trending",
                tweet_volume=processed_data.get('total_tweets', 0),
                velocity_score=processed_data.get('momentum_score', 0.0),
                sentiment_breakdown=sentiment,
                niche_relevance_score=relevance_score,
                trend_potential_score=min(1.0, relevance_score + 0.2),
                early_adopter_ratio=0.1,
                engagement_metrics={
                    'avg_engagement_rate': processed_data.get('avg_engagement_rate', 0.0),
                    'total_engagement': processed_data.get('total_engagement', 0)
                },
                sample_tweets=[],
                keywords=processed_data.get('all_keywords', [])[:10],
                pain_points=processed_data.get('pain_points', []),
                questions=processed_data.get('questions', []),
                is_micro_trend=is_micro_trend,
                created_at=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            print("trend_data: ", trend_data)
            logger.error(f"Failed to analyze trend {trend_data.get('name', 'unknown')}: {e}")
            return None
    
    async def _fetch_trend_tweets(self, trend_name: str, sample_size: int, access_token: str) -> List[Dict]:
        """Get representative tweet samples for a trend"""
        try:
            # Build search query
            if trend_name.startswith('#'):
                query = f"{trend_name} -is:retweet"
            else:
                query = f'"{trend_name}" -is:retweet'
            
            # Add engagement filter
            query += " min_faves:2"
            
            # Search tweets - should not use await here
            search_results = self.twitter_client.search_tweets(
                user_token=access_token,
                query=query,
                max_results=min(sample_size, 100),
                tweet_fields=[
                    'created_at', 'public_metrics', 'context_annotations',
                    'conversation_id', 'in_reply_to_user_id', 'author_id'
                ],
                user_fields=['public_metrics', 'verified', 'description'],
                expansions=['author_id']
            )
            
            return search_results.get('data', []) if search_results else []
            
        except Exception as e:
            logger.error(f"Get tweets for {trend_name} failed: {e}")
            return []
    
    def _calculate_niche_relevance(self, trend_data: Dict, user_profile: Any, processed_data: Dict) -> float:
        """Calculate relevance of trend to user's niche"""
        if not trend_data or not user_profile or not processed_data:
            return 0.0
        
        # Implement your logic to calculate relevance based on trend data and user profile
        # This is a placeholder and should be replaced with actual implementation
        return 0.5
    
    def _detect_micro_trend(self, trend_data: Dict, processed_data: Dict) -> bool:
        """Detect if a trend is a micro-trend"""
        if not trend_data or not processed_data:
            return False
        
        # Implement your logic to detect micro-trend based on trend data and processed data
        # This is a placeholder and should be replaced with actual implementation
        return False
    
    async def _generate_content_suggestions(self, trend_data: Dict[str, Any],
                                          user_profile: Any,
                                          processed_data: Dict[str, Any]) -> List[str]:
        """generate content suggestions"""
        try:
            suggestions = []
            
            # basic suggestions
            trend_name = trend_data.get('name', '')
            suggestions.append(f"Share insights about {trend_name}")
            suggestions.append(f"Create tutorial content related to {trend_name}")
            
            # based on pain points
            pain_points = processed_data.get('pain_points', [])
            if pain_points:
                suggestions.append(f"Create content to solve {pain_points[0]}")
            
            # based on questions
            questions = processed_data.get('questions', [])
            if questions:
                suggestions.append(f"Answer common questions about {trend_name}")
            
            # if LLM client exists, generate more intelligent suggestions
            print("suggestions: ", suggestions)
            if self.llm_client:
                try:
                    # here should call LLM to generate more personalized suggestions
                    # temporarily return basic suggestions
                    pass
                except Exception as e:
                    logger.warning(f"LLM content suggestions generation failed: {e}")
            
            return suggestions[:5]  # limit suggestion count
            
        except Exception as e:
            logger.error(f"generate content suggestions failed: {e}")
            return []
    
    def _create_default_request(self, user_id: str, product_info: Any) -> TrendAnalysisRequest:
        """Create default analysis request from user profile"""
        focus_keywords = []
        
        if product_info:
            # Extract keywords from product info
            try:
                if hasattr(product_info, 'niche_keywords') and product_info.niche_keywords:
                    if hasattr(product_info.niche_keywords, 'primary'):
                        focus_keywords.extend(product_info.niche_keywords.primary)
                    if hasattr(product_info.niche_keywords, 'secondary'):
                        focus_keywords.extend(product_info.niche_keywords.secondary[:3])
                
                # Add product name as keyword
                if hasattr(product_info, 'product_name') and product_info.product_name:
                    focus_keywords.append(product_info.product_name.lower())
            except Exception as e:
                logger.warning(f"Failed to extract product keywords: {e}")
        
        # Ensure we have at least some keywords
        if not focus_keywords:
            focus_keywords = ['startup', 'technology', 'innovation']
        
        return TrendAnalysisRequest(
            user_id=user_id,
            focus_keywords=focus_keywords[:10],  # Limit to 10 keywords
            max_trends_to_analyze=self.config.max_clusters,
            tweet_sample_size=self.config.max_tweets_per_trend
        )

    async def _fetch_trends_data(self, request: TrendAnalysisRequest, 
                               access_token: str) -> List[Dict[str, Any]]:
        """Get trends data"""
        try:
            # Get current trends - should not use await here because get_trends_for_location is not an async method
            trends = self.twitter_client.get_trends_for_location(
                access_token, location_id=1  # global trends
            )
            
            if not trends:
                return []
            
            # Filter relevant trends
            relevant_trends = []
            for trend in trends:
                trend_name = trend.get('name', '').lower()
                
                # Check if it's relevant to user keywords
                is_relevant = False
                for keyword in request.focus_keywords:
                    if keyword.lower() in trend_name:
                        is_relevant = True
                        break
                
                if is_relevant or len(relevant_trends) < 5:  # At least 5 trends
                    relevant_trends.append(trend)
            
            return relevant_trends
            
        except Exception as e:
            logger.error(f"failed to fetch trends data: {e}")
            return []