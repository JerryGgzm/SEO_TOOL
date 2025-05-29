"""Data processing""" 
import re
import string
from typing import List, Dict, Any
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.chunk import ne_chunk
from nltk.tag import pos_tag
import spacy
from textblob import TextBlob
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TweetPreprocessor:
    """Handles text preprocessing for tweet analysis"""
    
    def __init__(self, language: str = "english"):
        self.language = language
        self.lemmatizer = WordNetLemmatizer()
        
        # Download required NLTK data
        self._ensure_nltk_data()
        
        # Load spaCy model for advanced NLP
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Some advanced features will be disabled.")
            self.nlp = None
        
        # Define social media specific patterns
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.mention_pattern = re.compile(r'@[\w_]+')
        self.hashtag_pattern = re.compile(r'#[\w_]+')
        self.emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE
        )
        
        # Load stopwords
        self.stop_words = set(stopwords.words(self.language))
        
        # Add social media specific stopwords
        self.stop_words.update(['rt', 'via', 'amp', 'gt', 'lt'])
    
    def _ensure_nltk_data(self):
        """Download required NLTK data"""
        required_data = [
            'punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger',
            'maxent_ne_chunker', 'words'
        ]
        
        for data in required_data:
            try:
                nltk.data.find(f'tokenizers/{data}')
            except LookupError:
                logger.info(f"Downloading NLTK data: {data}")
                nltk.download(data, quiet=True)
    
    def clean_tweet_text(self, text: str, preserve_hashtags: bool = True, 
                        preserve_mentions: bool = False) -> str:
        """
        Clean tweet text while preserving important elements
        
        Args:
            text: Raw tweet text
            preserve_hashtags: Whether to keep hashtags
            preserve_mentions: Whether to keep @mentions
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = self.url_pattern.sub('', text)
        
        # Handle hashtags
        if preserve_hashtags:
            # Convert hashtags to regular words (remove #)
            text = re.sub(r'#(\w+)', r'\1', text)
        else:
            text = self.hashtag_pattern.sub('', text)
        
        # Handle mentions
        if not preserve_mentions:
            text = self.mention_pattern.sub('', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_keywords(self, text: str, min_length: int = 3, 
                        max_keywords: int = 20) -> List[str]:
        """Extract meaningful keywords from text"""
        if not text:
            return []
        
        # Clean text
        cleaned_text = self.clean_tweet_text(text)
        
        # Tokenize
        tokens = word_tokenize(cleaned_text)
        
        # Remove punctuation and short words
        tokens = [token for token in tokens 
                 if token not in string.punctuation 
                 and len(token) >= min_length
                 and token not in self.stop_words]
        
        # Lemmatize
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
        
        # Use spaCy for better keyword extraction if available
        if self.nlp:
            doc = self.nlp(cleaned_text)
            # Extract noun phrases and named entities
            noun_phrases = [chunk.text.lower() for chunk in doc.noun_chunks 
                           if len(chunk.text.split()) <= 3]
            named_entities = [ent.text.lower() for ent in doc.ents 
                             if ent.label_ in ['PERSON', 'ORG', 'PRODUCT', 'TECH']]
            
            # Combine tokens with noun phrases and entities
            all_keywords = tokens + noun_phrases + named_entities
        else:
            all_keywords = tokens
        
        # Count frequency and return top keywords
        keyword_counts = Counter(all_keywords)
        return [keyword for keyword, count in keyword_counts.most_common(max_keywords)]
    
    def extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        if not text:
            return []
        
        hashtags = self.hashtag_pattern.findall(text.lower())
        return [tag[1:] for tag in hashtags]  # Remove # symbol
    
    def extract_pain_point_indicators(self, text: str) -> List[str]:
        """Extract phrases that indicate pain points or problems"""
        if not text:
            return []
        
        # Pain point indicator patterns
        pain_patterns = [
            r"can't\s+\w+",
            r"unable\s+to\s+\w+",
            r"struggling\s+with\s+\w+",
            r"frustrated\s+by\s+\w+",
            r"hate\s+when\s+\w+",
            r"wish\s+\w+\s+would",
            r"why\s+is\s+\w+\s+so",
            r"problem\s+with\s+\w+",
            r"issue\s+with\s+\w+",
            r"annoying\s+\w+",
            r"terrible\s+\w+",
            r"worst\s+\w+",
            r"broken\s+\w+",
            r"doesn't\s+work",
            r"not\s+working",
            r"fails\s+to\s+\w+"
        ]
        
        pain_points = []
        text_lower = text.lower()
        
        for pattern in pain_patterns:
            matches = re.findall(pattern, text_lower)
            pain_points.extend(matches)
        
        return list(set(pain_points))  # Remove duplicates
    
    def extract_questions(self, text: str) -> List[str]:
        """Extract questions from text"""
        if not text:
            return []
        
        # Split into sentences
        sentences = sent_tokenize(text)
        
        # Find question sentences
        questions = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence.endswith('?'):
                questions.append(sentence)
            elif any(sentence.lower().startswith(qword) 
                    for qword in ['what', 'how', 'why', 'when', 'where', 'who', 'which']):
                questions.append(sentence)
        
        return questions
    
    def batch_process_tweets(self, tweets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a batch of tweets and extract aggregated insights"""
        if not tweets:
            return {
                'all_keywords': [],
                'pain_points': [],
                'questions': [],
                'hashtags': [],
                'processed_texts': []
            }
        
        all_keywords = []
        pain_points = []
        questions = []
        hashtags = []
        processed_texts = []
        
        for tweet in tweets:
            text = tweet.get('text', '')
            if not text:
                continue
            
            # Process tweet
            cleaned_text = self.clean_tweet_text(text)
            processed_texts.append(cleaned_text)
            
            # Extract features
            keywords = self.extract_keywords(text)
            tweet_pain_points = self.extract_pain_point_indicators(text)
            tweet_questions = self.extract_questions(text)
            tweet_hashtags = self.extract_hashtags(text)
            
            all_keywords.extend(keywords)
            pain_points.extend(tweet_pain_points)
            questions.extend(tweet_questions)
            hashtags.extend(tweet_hashtags)
        
        # Aggregate and count
        keyword_counts = Counter(all_keywords)
        pain_point_counts = Counter(pain_points)
        hashtag_counts = Counter(hashtags)
        
        return {
            'all_keywords': [kw for kw, count in keyword_counts.most_common(50)],
            'pain_points': [pp for pp, count in pain_point_counts.most_common(20) if count >= 2],
            'questions': list(set(questions))[:20],  # Remove duplicates, limit to 20
            'hashtags': [ht for ht, count in hashtag_counts.most_common(30)],
            'processed_texts': processed_texts
        }

class TrendDataProcessor:
    """process trend data"""
    
    def __init__(self):
        self.preprocessor = TweetPreprocessor()
    
    def process_tweets(self, tweets_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """process tweets data"""
        try:
            if not tweets_data:
                return self._empty_result()
            
            # use existing batch processing method
            batch_results = self.preprocessor.batch_process_tweets(tweets_data)
            
            # calculate engagement metrics
            total_engagement = 0
            total_impressions = 0
            
            for tweet in tweets_data:
                public_metrics = tweet.get('public_metrics', {})
                engagement = (public_metrics.get('like_count', 0) + 
                            public_metrics.get('retweet_count', 0) + 
                            public_metrics.get('reply_count', 0) + 
                            public_metrics.get('quote_count', 0))
                total_engagement += engagement
                
                # estimate impressions (if no direct data)
                estimated_impressions = engagement * 10  # simplified estimation
                total_impressions += estimated_impressions
            
            # calculate average engagement
            avg_engagement_rate = 0.0
            if total_impressions > 0:
                avg_engagement_rate = total_engagement / total_impressions
            elif len(tweets_data) > 0:
                avg_engagement_rate = total_engagement / len(tweets_data) / 100
            
            # calculate sentiment score (simplified version)
            sentiment_score = self._calculate_sentiment_score(batch_results['processed_texts'])
            
            return {
                'processed_tweets': tweets_data,
                'total_tweets': len(tweets_data),
                'total_engagement': total_engagement,
                'total_impressions': total_impressions,
                'avg_engagement_rate': avg_engagement_rate,
                'sentiment_score': sentiment_score,
                'all_keywords': batch_results['all_keywords'],
                'pain_points': batch_results['pain_points'],
                'questions': batch_results['questions'],
                'hashtags': batch_results['hashtags'],
                'processing_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"process tweets data failed: {e}")
            return self._empty_result()
    
    def _calculate_sentiment_score(self, processed_texts: List[str]) -> float:
        """calculate sentiment score (simplified version)"""
        try:
            if not processed_texts:
                return 0.5  # neutral
            
            positive_indicators = [
                'good', 'great', 'awesome', 'amazing', 'love', 'like', 'best', 
                'excellent', 'fantastic', 'wonderful', 'perfect', 'happy'
            ]
            
            negative_indicators = [
                'bad', 'terrible', 'awful', 'hate', 'worst', 'horrible', 
                'disgusting', 'annoying', 'frustrated', 'angry', 'sad'
            ]
            
            positive_count = 0
            negative_count = 0
            
            for text in processed_texts:
                text_lower = text.lower()
                
                for indicator in positive_indicators:
                    if indicator in text_lower:
                        positive_count += 1
                        break
                
                for indicator in negative_indicators:
                    if indicator in text_lower:
                        negative_count += 1
                        break
            
            total_sentiment_tweets = positive_count + negative_count
            if total_sentiment_tweets == 0:
                return 0.5  # neutral
            
            # return a score between 0-1, 0.5 is neutral
            return positive_count / total_sentiment_tweets
            
        except Exception as e:
            logger.error(f"calculate sentiment score failed: {e}")
            return 0.5
    
    def _empty_result(self) -> Dict[str, Any]:
        """return empty result"""
        return {
            'processed_tweets': [],
            'total_tweets': 0,
            'total_engagement': 0,
            'total_impressions': 0,
            'avg_engagement_rate': 0.0,
            'sentiment_score': 0.5,
            'all_keywords': [],
            'pain_points': [],
            'questions': [],
            'hashtags': [],
            'processing_timestamp': datetime.now().isoformat()
        }
    
    def analyze_trend_momentum(self, tweets_data: List[Dict[str, Any]], 
                             time_window_hours: int = 24) -> Dict[str, Any]:
        """analyze trend momentum"""
        try:
            if not tweets_data:
                return {'momentum_score': 0.0, 'trend_direction': 'stable'}
            
            # sort tweets by time
            sorted_tweets = sorted(tweets_data, 
                                 key=lambda x: x.get('created_at', ''))
            
            if len(sorted_tweets) < 2:
                return {'momentum_score': 0.0, 'trend_direction': 'stable'}
            
            # calculate tweet distribution within time window
            time_buckets = self._create_time_buckets(sorted_tweets, time_window_hours)
            
            # analyze trend direction
            trend_direction = self._analyze_trend_direction(time_buckets)
            momentum_score = self._calculate_momentum_score(time_buckets)
            
            return {
                'momentum_score': momentum_score,
                'trend_direction': trend_direction,
                'time_buckets': time_buckets,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"分析趋势动量失败: {e}")
            return {'momentum_score': 0.0, 'trend_direction': 'stable'}
    
    def _create_time_buckets(self, tweets: List[Dict[str, Any]], 
                           hours: int) -> List[Dict[str, Any]]:
        """create time buckets for analysis"""
        bucket_size = max(1, len(tweets) // 4)  # 分成4个时间段
        buckets = []
        
        for i in range(0, len(tweets), bucket_size):
            bucket_tweets = tweets[i:i + bucket_size]
            total_engagement = sum(
                tweet.get('public_metrics', {}).get('like_count', 0) +
                tweet.get('public_metrics', {}).get('retweet_count', 0)
                for tweet in bucket_tweets
            )
            
            buckets.append({
                'tweet_count': len(bucket_tweets),
                'total_engagement': total_engagement,
                'bucket_index': len(buckets)
            })
        
        return buckets
    
    def _analyze_trend_direction(self, time_buckets: List[Dict[str, Any]]) -> str:
        """analyze trend direction"""
        if len(time_buckets) < 2:
            return 'stable'
        
        first_bucket = time_buckets[0]
        last_bucket = time_buckets[-1]
        
        first_activity = first_bucket['tweet_count'] + first_bucket['total_engagement']
        last_activity = last_bucket['tweet_count'] + last_bucket['total_engagement']
        
        if last_activity > first_activity * 1.2:
            return 'rising'
        elif last_activity < first_activity * 0.8:
            return 'declining'
        else:
            return 'stable'
    
    def _calculate_momentum_score(self, time_buckets: List[Dict[str, Any]]) -> float:
        """calculate momentum score"""
        if len(time_buckets) < 2:
            return 0.0
        
        activities = [
            bucket['tweet_count'] + bucket['total_engagement']
            for bucket in time_buckets
        ]
        
        if not activities or max(activities) == 0:
            return 0.0
        
        # simplified momentum calculation
        momentum = (activities[-1] - activities[0]) / max(activities)
        return max(0.0, min(1.0, momentum + 0.5))