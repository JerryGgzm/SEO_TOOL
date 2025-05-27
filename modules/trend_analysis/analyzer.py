"""Trend analyzer""" 
import asyncio
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import json
import logging
from collections import defaultdict

from modules.twitter_api import TwitterAPIClient, TwitterAPIError
from modules.user_profile import UserProfileService
from .models import (
    AnalyzedTrend, TrendAnalysisRequest, TrendAnalysisConfig,
    TrendMetrics, ExampleTweet, TopicCluster, TrendSource
)
from .data_processor import TweetPreprocessor
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
        
        # Initialize analysis components
        self.preprocessor = TweetPreprocessor()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.micro_trend_detector = MicroTrendDetector(self.config.dict())
        self.llm_extractor = LLMInsightExtractor(llm_client, self.config.llm_model_name)
    
    async def analyze_trends_for_user(self, user_id: str, 
                                    request: TrendAnalysisRequest = None) -> List[AnalyzedTrend]:
        """
        Main entry point for trend analysis
        
        Args:
            user_id: User ID to analyze trends for
            request: Optional analysis request parameters
            
        Returns:
            List of analyzed trends
        """
        try:
            logger.info(f"Starting trend analysis for user {user_id}")
            
            # Get user profile and product info
            user_profile = self.user_service.get_user_profile(user_id)
            if not user_profile or not user_profile.product_info:
                logger.warning(f"No product info found for user {user_id}")
                return []
            
            # Get user's Twitter access token
            access_token = self.user_service.get_twitter_access_token(user_id)
            if not access_token:
                logger.warning(f"No Twitter access token for user {user_id}")
                return []
            
            # Use request parameters or derive from user profile
            if not request:
                request = self._create_default_request(user_id, user_profile.product_info)
            
            # Step 1: Get trending topics
            trending_topics = await self._get_trending_topics(access_token, request.location_id)
            
            # Step 2: Search for niche-specific trends
            niche_trends = await self._search_niche_trends(access_token, request.focus_keywords)
            
            # Step 3: Combine and filter trends
            all_candidate_trends = self._combine_and_filter_trends(
                trending_topics, niche_trends, request.focus_keywords
            )
            
            # Step 4: Analyze each trend
            analyzed_trends = []
            for i, trend_data in enumerate(all_candidate_trends[:request.max_trends_to_analyze]):
                logger.info(f"Analyzing trend {i+1}/{len(all_candidate_trends)}: {trend_data['name']}")
                
                analyzed_trend = await self._analyze_single_trend(
                    access_token, trend_data, user_profile, request
                )
                
                if analyzed_trend:
                    analyzed_trends.append(analyzed_trend)
            
            # Step 5: Identify micro-trends
            micro_trends = self.micro_trend_detector.detect_micro_trends(analyzed_trends)
            
            # Step 6: Sort by relevance and potential
            analyzed_trends.sort(
                key=lambda t: (t.trend_potential_score * 0.6 + t.niche_relevance_score * 0.4),
                reverse=True
            )
            
            logger.info(f"Completed trend analysis for user {user_id}: {len(analyzed_trends)} trends, {len(micro_trends)} micro-trends")
            
            return analyzed_trends
            
        except Exception as e:
            logger.error(f"Trend analysis failed for user {user_id}: {e}")
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
    
    async def _analyze_single_trend(self, access_token: str, trend_data: Dict,
                                  user_profile: Any, request: TrendAnalysisRequest) -> Optional[AnalyzedTrend]:
        """Analyze a single trend comprehensively"""
        try:
            trend_name = trend_data.get('name', '')
            if not trend_name:
                return None
            
            # Get tweet samples for analysis
            tweet_samples = await self._get_tweet_samples(
                access_token, trend_data, request.tweet_sample_size
            )
            
            if not tweet_samples or len(tweet_samples) < 10:
                logger.warning(f"Insufficient tweet samples for trend: {trend_name}")
                return None
            
            # Process tweets
            processed_data = self.preprocessor.batch_process_tweets(tweet_samples)
            
            # Sentiment analysis
            tweet_texts = [tweet.get('text', '') for tweet in tweet_samples]
            overall_sentiment, individual_sentiments = self.sentiment_analyzer.analyze_batch_sentiment(tweet_texts)
            
            # Calculate metrics
            metrics = self._calculate_trend_metrics(tweet_samples)
            
            # Calculate velocity and early adopter ratio
            velocity_score = self.micro_trend_detector.calculate_trend_velocity(
                tweet_samples, self.config.analysis_time_window_hours
            )
            
            early_adopter_ratio = self.micro_trend_detector.analyze_early_adopters(tweet_samples)
            
            # Extract insights using LLM if available
            pain_points = processed_data['pain_points']
            opportunities = []
            
            if self.config.use_llm_for_insights:
                niche_context = {
                    'product_info': user_profile.product_info.dict() if user_profile.product_info else {},
                    'niche_keywords': request.focus_keywords
                }
                
                llm_pain_points, llm_opportunities = self.llm_extractor.extract_pain_points_and_opportunities(
                    tweet_texts[:20], trend_name, niche_context
                )
                
                # Combine with preprocessor results
                pain_points.extend(llm_pain_points)
                opportunities.extend(llm_opportunities)
                
                # Remove duplicates and limit
                pain_points = list(dict.fromkeys(pain_points))[:15]
                opportunities = list(dict.fromkeys(opportunities))[:10]
            
            # Calculate overall scores
            niche_relevance_score = trend_data.get('relevance_score', 0.5)
            
            trend_potential_score = self.micro_trend_detector.calculate_trend_potential_score(
                velocity_score,
                early_adopter_ratio,
                {'avg_engagement_rate': metrics.avg_engagement_rate},
                niche_relevance_score
            )
            
            # Select example tweets
            example_tweets = self._select_example_tweets(tweet_samples, individual_sentiments)
            
            # Create analyzed trend object
            analyzed_trend = AnalyzedTrend(
                id=f"trend_{user_profile.user_id}_{int(datetime.utcnow().timestamp())}_{hash(trend_name) % 10000}",
                user_id=user_profile.user_id,
                trend_source=TrendSource(trend_data.get('source', 'twitter_trending')),
                trend_source_id=trend_data.get('id'),
                topic_name=trend_name,
                topic_keywords=processed_data['all_keywords'][:10],
                niche_relevance_score=niche_relevance_score,
                trend_potential_score=trend_potential_score,
                confidence_score=min(overall_sentiment.confidence, 0.9),
                overall_sentiment=overall_sentiment,
                extracted_pain_points=pain_points,
                common_questions=processed_data['questions'][:10],
                discussion_focus_points=processed_data['all_keywords'][:8],
                key_opportunities=opportunities,
                trend_velocity_score=velocity_score,
                early_adopter_ratio=early_adopter_ratio,
                metrics=metrics,
                sample_tweet_ids_analyzed=[tweet.get('id', '') for tweet in tweet_samples],
                example_tweets=example_tweets
            )
            
            return analyzed_trend
            
        except Exception as e:
            logger.error(f"Failed to analyze trend '{trend_data.get('name')}': {e}")
            return None
    
    async def _get_tweet_samples(self, access_token: str, trend_data: Dict, 
                               sample_size: int) -> List[Dict]:
        """Get representative tweet samples for a trend"""
        try:
            # Check if we already have search results
            if 'search_results' in trend_data:
                return trend_data['search_results'].get('data', [])
            
            # Search for tweets about this trend
            trend_name = trend_data.get('name', '')
            
            # Create search query
            if trend_name.startswith('#'):
                query = f"{trend_name} -is:retweet"
            else:
                query = f'"{trend_name}" -is:retweet'
            
            # Add engagement filter
            query += " min_faves:2"
            
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
            
        except TwitterAPIError as e:
            logger.error(f"Failed to get tweet samples for trend: {e}")
            return []
    
    def _calculate_trend_metrics(self, tweets: List[Dict]) -> TrendMetrics:
        """Calculate quantitative metrics for a trend"""
        if not tweets:
            return TrendMetrics(
                tweet_volume=0,
                engagement_volume=0,
                avg_engagement_rate=0.0,
                unique_users=0,
                time_span_hours=0.0,
                velocity_score=0.0
            )
        
        # Calculate engagement metrics
        total_engagement = 0
        unique_users = set()
        tweet_times = []
        
        for tweet in tweets:
            # Engagement
            public_metrics = tweet.get('public_metrics', {})
            engagement = (
                public_metrics.get('like_count', 0) +
                public_metrics.get('retweet_count', 0) +
                public_metrics.get('reply_count', 0) +
                public_metrics.get('quote_count', 0)
            )
            total_engagement += engagement
            
            # Unique users
            author_id = tweet.get('author_id')
            if author_id:
                unique_users.add(author_id)
            
            # Tweet times
            created_at = tweet.get('created_at')
            if created_at:
                try:
                    tweet_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    tweet_times.append(tweet_time)
                except ValueError:
                    continue
        
        # Calculate time span
        if len(tweet_times) >= 2:
            tweet_times.sort()
            time_span = tweet_times[-1] - tweet_times[0]
            time_span_hours = time_span.total_seconds() / 3600
        else:
            time_span_hours = 1.0  # Default to 1 hour
        
        # Calculate averages
        tweet_volume = len(tweets)
        avg_engagement_rate = total_engagement / tweet_volume if tweet_volume > 0 else 0.0
        velocity_score = tweet_volume / time_span_hours if time_span_hours > 0 else 0.0
        
        return TrendMetrics(
            tweet_volume=tweet_volume,
            engagement_volume=total_engagement,
            avg_engagement_rate=avg_engagement_rate,
            unique_users=len(unique_users),
            time_span_hours=time_span_hours,
            velocity_score=velocity_score
        )
    
    def _select_example_tweets(self, tweets: List[Dict], 
                             sentiments: List[Any]) -> List[ExampleTweet]:
        """Select representative example tweets"""
        if not tweets or not sentiments:
            return []
        
        examples = []
        
        # Create tweet-sentiment pairs
        tweet_sentiment_pairs = list(zip(tweets, sentiments))
        
        # Sort by engagement
        tweet_sentiment_pairs.sort(
            key=lambda x: sum(x[0].get('public_metrics', {}).values()),
            reverse=True
        )
        
        # Select diverse examples
        sentiment_buckets = {'positive': [], 'negative': [], 'neutral': []}
        
        for tweet, sentiment in tweet_sentiment_pairs:
            bucket = sentiment.dominant_sentiment.value
            if len(sentiment_buckets[bucket]) < 2:  # Max 2 per sentiment
                engagement_score = sum(tweet.get('public_metrics', {}).values())
                
                example = ExampleTweet(
                    tweet_id=tweet.get('id', ''),
                    text=tweet.get('text', '')[:200],  # Truncate if too long
                    sentiment=sentiment.dominant_sentiment,
                    engagement_score=float(engagement_score),
                    created_at=datetime.fromisoformat(tweet.get('created_at', '').replace('Z', '+00:00')) 
                             if tweet.get('created_at') else datetime.utcnow(),
                    why_selected=f"High engagement {bucket} sentiment example"
                )
                
                sentiment_buckets[bucket].append(example)
                examples.append(example)
                
                if len(examples) >= 5:  # Max 5 examples total
                    break
        
        return examples[:5]
    
    def _create_default_request(self, user_id: str, product_info: Any) -> TrendAnalysisRequest:
        """Create default analysis request from user profile"""
        focus_keywords = []
        
        if product_info:
            # Extract keywords from product info
            if hasattr(product_info, 'niche_keywords') and product_info.niche_keywords:
                focus_keywords.extend(product_info.niche_keywords.primary)
                if product_info.niche_keywords.secondary:
                    focus_keywords.extend(product_info.niche_keywords.secondary[:3])
            
            # Add product name as keyword
            if hasattr(product_info, 'product_name'):
                focus_keywords.append(product_info.product_name.lower())
        
        # Ensure we have at least some keywords
        if not focus_keywords:
            focus_keywords = ['startup', 'technology', 'innovation']
        
        return TrendAnalysisRequest(
            user_id=user_id,
            focus_keywords=focus_keywords[:10],  # Limit to 10 keywords
            max_trends_to_analyze=self.config.max_clusters,
            tweet_sample_size=self.config.max_tweets_per_trend
        )