"""Sentiment analysis""" 
import numpy as np
from typing import List, Dict, Tuple, Optional
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import logging

from .models import SentimentBreakdown, SentimentLabel, EmotionLabel

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Comprehensive sentiment analysis with multiple approaches"""
    
    def __init__(self):
        self.vader_analyzer = SentimentIntensityAnalyzer()
        
        # Emotion detection keywords (simplified approach)
        self.emotion_keywords = {
            EmotionLabel.JOY: ['happy', 'excited', 'amazing', 'awesome', 'love', 'great', 'wonderful', 'fantastic'],
            EmotionLabel.ANGER: ['angry', 'mad', 'furious', 'hate', 'terrible', 'awful', 'disgusting', 'worst'],
            EmotionLabel.SADNESS: ['sad', 'disappointed', 'depressed', 'upset', 'crying', 'heartbroken'],
            EmotionLabel.FEAR: ['scared', 'afraid', 'worried', 'anxious', 'nervous', 'terrified', 'panic'],
            EmotionLabel.SURPRISE: ['surprised', 'shocked', 'amazed', 'unexpected', 'wow', 'omg', 'incredible'],
            EmotionLabel.DISGUST: ['disgusting', 'gross', 'revolting', 'sick', 'nasty', 'horrible'],
            EmotionLabel.ANTICIPATION: ['excited', 'looking forward', 'can\'t wait', 'anticipating', 'hopeful'],
            EmotionLabel.TRUST: ['trust', 'reliable', 'confident', 'believe', 'faith', 'dependable']
        }
    
    def analyze_text_sentiment(self, text: str) -> SentimentBreakdown:
        """
        Analyze sentiment of a single text using multiple methods
        
        Args:
            text: Text to analyze
            
        Returns:
            SentimentBreakdown with detailed sentiment scores
        """
        if not text or not text.strip():
            return SentimentBreakdown(
                positive_score=0.0,
                negative_score=0.0,
                neutral_score=1.0,
                dominant_sentiment=SentimentLabel.NEUTRAL,
                confidence=0.0
            )
        
        # TextBlob sentiment
        blob = TextBlob(text)
        textblob_polarity = blob.sentiment.polarity
        textblob_subjectivity = blob.sentiment.subjectivity
        
        # VADER sentiment
        vader_scores = self.vader_analyzer.polarity_scores(text)
        
        # Combine scores (weighted average)
        textblob_weight = 0.4
        vader_weight = 0.6
        
        # Convert TextBlob polarity (-1 to 1) to positive/negative scores
        if textblob_polarity > 0:
            textblob_pos = textblob_polarity
            textblob_neg = 0
        elif textblob_polarity < 0:
            textblob_pos = 0
            textblob_neg = abs(textblob_polarity)
        else:
            textblob_pos = 0
            textblob_neg = 0
        
        textblob_neu = 1 - abs(textblob_polarity)
        
        # Weighted combination
        positive_score = (textblob_pos * textblob_weight + 
                         vader_scores['pos'] * vader_weight)
        negative_score = (textblob_neg * textblob_weight + 
                         vader_scores['neg'] * vader_weight)
        neutral_score = (textblob_neu * textblob_weight + 
                        vader_scores['neu'] * vader_weight)
        
        # Normalize scores to sum to 1
        total_score = positive_score + negative_score + neutral_score
        if total_score > 0:
            positive_score /= total_score
            negative_score /= total_score
            neutral_score /= total_score
        else:
            positive_score = negative_score = 0.0
            neutral_score = 1.0
        
        # Determine dominant sentiment
        scores = {
            SentimentLabel.POSITIVE: positive_score,
            SentimentLabel.NEGATIVE: negative_score,
            SentimentLabel.NEUTRAL: neutral_score
        }
        dominant_sentiment = max(scores, key=scores.get)
        
        # Calculate confidence based on the margin between top scores
        sorted_scores = sorted(scores.values(), reverse=True)
        confidence = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) > 1 else sorted_scores[0]
        
        # Detect dominant emotion
        dominant_emotion = self._detect_emotion(text)
        
        return SentimentBreakdown(
            positive_score=positive_score,
            negative_score=negative_score,
            neutral_score=neutral_score,
            dominant_sentiment=dominant_sentiment,
            dominant_emotion=dominant_emotion,
            confidence=confidence
        )
    
    def analyze_batch_sentiment(self, texts: List[str]) -> Tuple[SentimentBreakdown, List[SentimentBreakdown]]:
        """
        Analyze sentiment for a batch of texts
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            Tuple of (aggregated_sentiment, individual_sentiments)
        """
        if not texts:
            neutral_sentiment = SentimentBreakdown(
                positive_score=0.0,
                negative_score=0.0,
                neutral_score=1.0,
                dominant_sentiment=SentimentLabel.NEUTRAL,
                confidence=0.0
            )
            return neutral_sentiment, []
        
        individual_sentiments = []
        
        # Analyze each text
        for text in texts:
            sentiment = self.analyze_text_sentiment(text)
            individual_sentiments.append(sentiment)
        
        # Aggregate results
        total_positive = sum(s.positive_score for s in individual_sentiments)
        total_negative = sum(s.negative_score for s in individual_sentiments)
        total_neutral = sum(s.neutral_score for s in individual_sentiments)
        
        num_texts = len(individual_sentiments)
        avg_positive = total_positive / num_texts
        avg_negative = total_negative / num_texts
        avg_neutral = total_neutral / num_texts
        
        # Determine aggregated dominant sentiment
        scores = {
            SentimentLabel.POSITIVE: avg_positive,
            SentimentLabel.NEGATIVE: avg_negative,
            SentimentLabel.NEUTRAL: avg_neutral
        }
        dominant_sentiment = max(scores, key=scores.get)
        
        # Calculate aggregated confidence
        sorted_scores = sorted(scores.values(), reverse=True)
        confidence = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) > 1 else sorted_scores[0]
        
        # Find most common emotion
        emotions = [s.dominant_emotion for s in individual_sentiments if s.dominant_emotion]
        dominant_emotion = max(set(emotions), key=emotions.count) if emotions else None
        
        aggregated_sentiment = SentimentBreakdown(
            positive_score=avg_positive,
            negative_score=avg_negative,
            neutral_score=avg_neutral,
            dominant_sentiment=dominant_sentiment,
            dominant_emotion=dominant_emotion,
            confidence=confidence
        )
        
        return aggregated_sentiment, individual_sentiments
    
    def _detect_emotion(self, text: str) -> Optional[EmotionLabel]:
        """
        Detect dominant emotion in text using keyword matching
        
        Args:
            text: Text to analyze
            
        Returns:
            Dominant emotion label or None
        """
        if not text:
            return None
        
        text_lower = text.lower()
        emotion_scores = {}
        
        # Score each emotion based on keyword presence
        for emotion, keywords in self.emotion_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            
            if score > 0:
                emotion_scores[emotion] = score
        
        # Return emotion with highest score
        if emotion_scores:
            return max(emotion_scores, key=emotion_scores.get)
        
        return None
    
    def get_sentiment_summary(self, sentiments: List[SentimentBreakdown]) -> Dict[str, any]:
        """
        Generate a summary of sentiment analysis results
        
        Args:
            sentiments: List of sentiment breakdowns
            
        Returns:
            Summary statistics
        """
        if not sentiments:
            return {
                'total_analyzed': 0,
                'avg_positive': 0.0,
                'avg_negative': 0.0,
                'avg_neutral': 0.0,
                'dominant_sentiment_distribution': {},
                'emotion_distribution': {},
                'avg_confidence': 0.0
            }
        
        # Calculate averages
        avg_positive = np.mean([s.positive_score for s in sentiments])
        avg_negative = np.mean([s.negative_score for s in sentiments])
        avg_neutral = np.mean([s.neutral_score for s in sentiments])
        avg_confidence = np.mean([s.confidence for s in sentiments])
        
        # Count distributions
        sentiment_counts = {}
        emotion_counts = {}
        
        for sentiment in sentiments:
            # Sentiment distribution
            sentiment_label = sentiment.dominant_sentiment.value
            sentiment_counts[sentiment_label] = sentiment_counts.get(sentiment_label, 0) + 1
            
            # Emotion distribution
            if sentiment.dominant_emotion:
                emotion_label = sentiment.dominant_emotion.value
                emotion_counts[emotion_label] = emotion_counts.get(emotion_label, 0) + 1
        
        return {
            'total_analyzed': len(sentiments),
            'avg_positive': float(avg_positive),
            'avg_negative': float(avg_negative),
            'avg_neutral': float(avg_neutral),
            'dominant_sentiment_distribution': sentiment_counts,
            'emotion_distribution': emotion_counts,
            'avg_confidence': float(avg_confidence)
        }