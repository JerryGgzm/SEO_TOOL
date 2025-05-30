"""Content quality assessment and validation"""
import re
import math
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

from .models import ContentDraft, ContentQualityScore, ContentGenerationContext, ContentType

logger = logging.getLogger(__name__)

class ContentQualityChecker:
    """Comprehensive content quality assessment"""
    
    def __init__(self):
        # Quality assessment weights
        self.weights = {
            'engagement_prediction': 0.25,
            'brand_alignment': 0.20,
            'trend_relevance': 0.20,
            'seo_optimization': 0.15,
            'readability': 0.20
        }
        
        # Common quality issues patterns
        self.quality_patterns = {
            'promotional_overload': [
                r'\b(buy now|purchase|sale|discount|offer)\b',
                r'[!]{3,}',  # Multiple exclamation marks
                r'\b(best|amazing|incredible|fantastic){2,}'  # Repetitive superlatives
            ],
            'poor_readability': [
                r'^[A-Z\s!]{20,}',  # All caps
                r'[.]{3,}',  # Multiple dots
                r'\w{15,}',  # Very long words
            ],
            'spam_indicators': [
                r'\b(click here|follow me|dm me)\b',
                r'[🔥💰💵]{3,}',  # Excessive money/fire emojis
                r'#\w+(?:\s+#\w+){5,}',  # Too many consecutive hashtags
            ],
            'engagement_killers': [
                r'^(?:(?!\?).)*$',  # No questions or calls to action
                r'^\w+\s+\w+\s+\w+$',  # Too short/minimal content
                r'^[^.!?]*[.!?]\s*$'  # Single sentence only
            ]
        }
    
    async def assess_quality(self, draft: ContentDraft, 
                           context: ContentGenerationContext) -> ContentQualityScore:
        """Comprehensive quality assessment of content draft"""
        
        try:
            # Individual quality assessments
            engagement_score = self._assess_engagement_potential(draft, context)
            brand_alignment_score = self._assess_brand_alignment(draft, context)
            trend_relevance_score = self._assess_trend_relevance(draft, context)
            seo_score = self._assess_seo_optimization(draft)
            readability_score = self._assess_readability(draft)
            
            # Calculate overall score
            overall_score = (
                engagement_score * self.weights['engagement_prediction'] +
                brand_alignment_score * self.weights['brand_alignment'] +
                trend_relevance_score * self.weights['trend_relevance'] +
                seo_score * self.weights['seo_optimization'] +
                readability_score * self.weights['readability']
            )
            
            # Identify issues and suggestions
            issues = self._identify_quality_issues(draft, context)
            suggestions = self._generate_improvement_suggestions(draft, context, issues)
            
            return ContentQualityScore(
                overall_score=round(overall_score, 3),
                engagement_prediction=round(engagement_score, 3),
                brand_alignment=round(brand_alignment_score, 3),
                trend_relevance=round(trend_relevance_score, 3),
                seo_optimization=round(seo_score, 3),
                readability=round(readability_score, 3),
                issues=issues,
                suggestions=suggestions
            )
            
        except Exception as e:
            logger.error(f"Quality assessment failed: {e}")
            return ContentQualityScore(
                overall_score=0.5,
                engagement_prediction=0.5,
                brand_alignment=0.5,
                trend_relevance=0.5,
                seo_optimization=0.5,
                readability=0.5,
                issues=["Quality assessment failed"],
                suggestions=["Manual review recommended"]
            )
    
    def _assess_engagement_potential(self, draft: ContentDraft, 
                                   context: ContentGenerationContext) -> float:
        """Assess potential for engagement based on content characteristics"""
        
        score = 0.5  # Base score
        text = draft.generated_text.lower()
        
        # Positive engagement factors
        engagement_boosters = {
            'has_question': r'\?',
            'has_call_to_action': r'\b(what do you think|share your|tell me|comment|thoughts)\b',
            'has_personal_touch': r'\b(i|we|my|our|you|your)\b',
            'has_numbers': r'\b\d+\b',
            'has_emojis': r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]',
            'has_contrast': r'\b(but|however|yet|although|while)\b',
            'has_urgency': r'\b(now|today|urgent|limited|soon)\b'
        }
        
        for factor, pattern in engagement_boosters.items():
            if re.search(pattern, text):
                if factor == 'has_question':
                    score += 0.15
                elif factor == 'has_call_to_action':
                    score += 0.12
                elif factor == 'has_personal_touch':
                    score += 0.08
                else:
                    score += 0.05
        
        # Content type specific adjustments
        if draft.content_type == ContentType.REPLY:
            # Replies should be conversational
            if any(word in text for word in ['thanks', 'agree', 'exactly', 'interesting']):
                score += 0.1
        
        elif draft.content_type == ContentType.THREAD:
            # Threads should have good flow
            if '1/' in draft.generated_text or 'thread' in text:
                score += 0.05
        
        # Length optimization
        text_length = len(draft.generated_text)
        if draft.content_type == ContentType.TWEET:
            # Optimal tweet length is 71-100 characters
            if 71 <= text_length <= 100:
                score += 0.05
            elif text_length < 50:
                score -= 0.1
        
        # Check against successful patterns
        if context.successful_patterns:
            pattern_match_score = self._match_successful_patterns(draft, context.successful_patterns)
            score += pattern_match_score * 0.1
        
        return min(1.0, max(0.0, score))
    
    def _assess_brand_alignment(self, draft: ContentDraft, 
                              context: ContentGenerationContext) -> float:
        """Assess alignment with brand voice and values"""
        
        score = 0.5  # Base score
        text = draft.generated_text.lower()
        brand_voice = context.brand_voice
        
        # Tone alignment
        tone_keywords = {
            'professional': ['expertise', 'solution', 'analysis', 'recommend', 'optimize'],
            'casual': ['hey', 'awesome', 'cool', 'love', 'fun'],
            'friendly': ['help', 'support', 'together', 'community', 'share'],
            'authoritative': ['proven', 'research', 'data', 'evidence', 'expert'],
            'inspirational': ['achieve', 'success', 'growth', 'potential', 'transform']
        }
        
        target_tone = brand_voice.tone.lower()
        if target_tone in tone_keywords:
            tone_matches = sum(1 for keyword in tone_keywords[target_tone] if keyword in text)
            score += min(0.2, tone_matches * 0.05)
        
        # Avoid words check
        avoided_words_found = sum(1 for word in brand_voice.avoid_words if word.lower() in text)
        if avoided_words_found > 0:
            score -= avoided_words_found * 0.1
        
        # Preferred phrases check
        preferred_found = sum(1 for phrase in brand_voice.preferred_phrases if phrase.lower() in text)
        score += min(0.15, preferred_found * 0.05)
        
        # Formality level check
        formality_indicators = {
            'formal': ['please', 'would', 'could', 'regarding', 'furthermore'],
            'casual': ['gonna', 'wanna', 'hey', 'cool', 'awesome']
        }
        
        if brand_voice.formality_level > 0.7:  # Formal
            formal_matches = sum(1 for word in formality_indicators['formal'] if word in text)
            casual_matches = sum(1 for word in formality_indicators['casual'] if word in text)
            score += (formal_matches - casual_matches) * 0.02
        
        elif brand_voice.formality_level < 0.3:  # Casual
            formal_matches = sum(1 for word in formality_indicators['formal'] if word in text)
            casual_matches = sum(1 for word in formality_indicators['casual'] if word in text)
            score += (casual_matches - formal_matches) * 0.02
        
        return min(1.0, max(0.0, score))
    
    def _assess_trend_relevance(self, draft: ContentDraft, 
                              context: ContentGenerationContext) -> float:
        """Assess relevance to trending topic"""
        
        if not context.trend_info:
            return 0.5  # No trend context to evaluate against
        
        score = 0.0
        text = draft.generated_text.lower()
        trend_info = context.trend_info
        
        # Topic name mention
        topic_name = trend_info.get('topic_name', '').lower()
        if topic_name and topic_name in text:
            score += 0.3
        
        # Pain points addressed
        pain_points = trend_info.get('pain_points', [])
        pain_points_addressed = 0
        for pain_point in pain_points:
            if any(word in text for word in pain_point.lower().split() if len(word) > 3):
                pain_points_addressed += 1
        
        if pain_points:
            score += (pain_points_addressed / len(pain_points)) * 0.25
        
        # Questions answered
        questions = trend_info.get('questions', [])
        questions_addressed = 0
        for question in questions:
            # Check if content seems to answer the question
            question_words = [w for w in question.lower().split() if len(w) > 3]
            if any(word in text for word in question_words):
                questions_addressed += 1
        
        if questions:
            score += (questions_addressed / len(questions)) * 0.2
        
        # Focus points covered
        focus_points = trend_info.get('focus_points', [])
        focus_coverage = 0
        for point in focus_points:
            if point.lower() in text:
                focus_coverage += 1
        
        if focus_points:
            score += (focus_coverage / len(focus_points)) * 0.15
        
        # Sentiment alignment
        if 'sentiment_scores' in trend_info:
            trend_sentiment = trend_info['sentiment_scores'].get('dominant_sentiment', 'neutral')
            content_sentiment = self._detect_content_sentiment(text)
            if trend_sentiment == content_sentiment:
                score += 0.1
        
        return min(1.0, score)
    
    def _assess_seo_optimization(self, draft: ContentDraft) -> float:
        """Assess SEO optimization level"""
        
        score = 0.5  # Base score
        text = draft.generated_text
        seo_suggestions = draft.seo_suggestions
        
        # Hashtag optimization
        hashtags_in_content = len(re.findall(r'#\w+', text))
        suggested_hashtags = len(seo_suggestions.hashtags)
        
        if suggested_hashtags > 0:
            hashtag_usage_ratio = hashtags_in_content / suggested_hashtags
            if 0.3 <= hashtag_usage_ratio <= 1.0:  # Good hashtag usage
                score += 0.2
            elif hashtag_usage_ratio > 1.0:  # Too many hashtags
                score -= 0.1
        
        # Keyword inclusion
        keywords_used = 0
        text_lower = text.lower()
        for keyword in seo_suggestions.keywords:
            if keyword.lower() in text_lower:
                keywords_used += 1
        
        if seo_suggestions.keywords:
            keyword_ratio = keywords_used / len(seo_suggestions.keywords)
            score += keyword_ratio * 0.2
        
        # Mentions usage
        mentions_in_content = len(re.findall(r'@\w+', text))
        if mentions_in_content > 0 and seo_suggestions.mentions:
            score += 0.1
        
        # Length optimization for platform
        if draft.content_type == ContentType.TWEET:
            # Twitter optimal length considerations
            if 100 <= len(text) <= 250:  # Good length for engagement
                score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _assess_readability(self, draft: ContentDraft) -> float:
        """Assess content readability and clarity"""
        
        score = 0.7  # Base score assuming decent readability
        text = draft.generated_text
        
        # Sentence structure analysis
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            
            # Optimal sentence length for social media (10-20 words)
            if 8 <= avg_sentence_length <= 20:
                score += 0.1
            elif avg_sentence_length > 25:
                score -= 0.15
        
        # Word complexity
        words = text.split()
        complex_words = [w for w in words if len(w) > 12]
        if len(words) > 0:
            complexity_ratio = len(complex_words) / len(words)
            if complexity_ratio > 0.2:  # Too many complex words
                score -= 0.1
        
        # Readability issues
        readability_issues = 0
        
        # All caps check
        if re.search(r'^[A-Z\s!]{10,}', text):
            readability_issues += 1
        
        # Excessive punctuation
        if re.search(r'[!]{3,}|[?]{2,}|[.]{4,}', text):
            readability_issues += 1
        
        # No punctuation
        if not re.search(r'[.!?]', text) and len(text) > 50:
            readability_issues += 1
        
        score -= readability_issues * 0.05
        
        # Positive readability factors
        # Has proper capitalization
        if re.search(r'^[A-Z]', text):
            score += 0.05
        
        # Has good flow connectors
        connectors = ['and', 'but', 'so', 'because', 'while', 'when', 'if']
        if any(connector in text.lower() for connector in connectors):
            score += 0.05
        
        return min(1.0, max(0.0, score))
    
    def _identify_quality_issues(self, draft: ContentDraft, 
                               context: ContentGenerationContext) -> List[str]:
        """Identify specific quality issues in content"""
        
        issues = []
        text = draft.generated_text
        
        # Check against quality patterns
        for issue_type, patterns in self.quality_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    issue_descriptions = {
                        'promotional_overload': 'Content appears overly promotional',
                        'poor_readability': 'Content has readability issues',
                        'spam_indicators': 'Content contains spam-like elements',
                        'engagement_killers': 'Content lacks engagement elements'
                    }
                    issues.append(issue_descriptions.get(issue_type, f'{issue_type} detected'))
                    break
        
        # Length issues
        if draft.content_type == ContentType.TWEET and len(text) > 280:
            issues.append(f'Content exceeds Twitter character limit ({len(text)}/280)')
        
        # Missing elements for content type
        if draft.content_type == ContentType.REPLY:
            if not re.search(r'\b(thanks|agree|interesting|good point)\b', text, re.IGNORECASE):
                issues.append('Reply lacks conversational elements')
        
        # Trend relevance issues
        if context.trend_info and not any(
            word in text.lower() 
            for word in context.trend_info.get('topic_name', '').lower().split()
        ):
            issues.append('Content does not clearly relate to the trending topic')
        
        # Brand alignment issues
        brand_voice = context.brand_voice
        for avoid_word in brand_voice.avoid_words:
            if avoid_word.lower() in text.lower():
                issues.append(f'Contains word to avoid: "{avoid_word}"')
        
        return issues
    
    def _generate_improvement_suggestions(self, draft: ContentDraft, 
                                        context: ContentGenerationContext,
                                        issues: List[str]) -> List[str]:
        """Generate specific improvement suggestions"""
        
        suggestions = []
        text = draft.generated_text
        
        # Length-based suggestions
        if len(text) > 280 and draft.content_type == ContentType.TWEET:
            suggestions.append('Shorten content to fit Twitter character limit')
        elif len(text) < 50:
            suggestions.append('Expand content with more detail or context')
        
        # Engagement suggestions
        if not re.search(r'\?', text):
            suggestions.append('Add a question to encourage engagement')
        
        if not re.search(r'\b(you|your)\b', text, re.IGNORECASE):
            suggestions.append('Use "you/your" to make content more personal')
        
        # SEO suggestions
        seo_suggestions = draft.seo_suggestions
        hashtags_in_content = len(re.findall(r'#\w+', text))
        
        if len(seo_suggestions.hashtags) > hashtags_in_content:
            missing_hashtags = len(seo_suggestions.hashtags) - hashtags_in_content
            suggestions.append(f'Consider adding {missing_hashtags} more relevant hashtags')
        
        # Brand voice suggestions
        brand_voice = context.brand_voice
        if brand_voice.tone == 'professional' and any(word in text.lower() for word in ['awesome', 'cool', 'hey']):
            suggestions.append('Use more professional language to match brand tone')
        
        # Trend relevance suggestions
        if context.trend_info:
            topic_name = context.trend_info.get('topic_name', '')
            if topic_name and topic_name.lower() not in text.lower():
                suggestions.append(f'Include reference to trending topic: {topic_name}')
        
        # Content type specific suggestions
        if draft.content_type == ContentType.THREAD:
            if '1/' not in text and 'thread' not in text.lower():
                suggestions.append('Add thread numbering (1/n format) for clarity')
        
        elif draft.content_type == ContentType.REPLY:
            if not any(word in text.lower() for word in ['thanks', 'great', 'interesting', 'agree']):
                suggestions.append('Add conversational elements appropriate for replies')
        
        return suggestions
    
    def _match_successful_patterns(self, draft: ContentDraft, 
                                 successful_patterns: List[Dict[str, Any]]) -> float:
        """Compare draft against successful content patterns"""
        
        if not successful_patterns:
            return 0.0
        
        text = draft.generated_text.lower()
        pattern_scores = []
        
        for pattern in successful_patterns:
            score = 0.0
            
            # Content type match
            if pattern.get('content_type') == draft.content_type.value:
                score += 0.3
            
            # Topic similarity (basic keyword matching)
            pattern_topic = pattern.get('topic', '').lower()
            if pattern_topic:
                common_words = set(text.split()) & set(pattern_topic.split())
                if common_words:
                    score += len(common_words) * 0.1
            
            # Length similarity
            pattern_length = pattern.get('content_length', 0)
            if pattern_length > 0:
                length_diff = abs(len(draft.generated_text) - pattern_length) / pattern_length
                if length_diff < 0.2:  # Within 20% of successful length
                    score += 0.2
            
            pattern_scores.append(score)
        
        return max(pattern_scores) if pattern_scores else 0.0
    
    def _detect_content_sentiment(self, text: str) -> str:
        """Simple sentiment detection for content"""
        
        positive_words = ['great', 'awesome', 'amazing', 'excellent', 'love', 'fantastic', 'wonderful']
        negative_words = ['terrible', 'awful', 'hate', 'worst', 'disappointing', 'frustrated']
        
        positive_count = sum(1 for word in positive_words if word in text.lower())
        negative_count = sum(1 for word in negative_words if word in text.lower())
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def bulk_assess_quality(self, drafts: List[ContentDraft], 
                          context: ContentGenerationContext) -> List[ContentQualityScore]:
        """Assess quality for multiple drafts efficiently"""
        
        import asyncio
        
        async def assess_all():
            tasks = [self.assess_quality(draft, context) for draft in drafts]
            return await asyncio.gather(*tasks)
        
        return asyncio.run(assess_all())