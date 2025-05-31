import re
from typing import List, Dict, Optional, Set, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class ContentEnhancer:
   """Enhances content with SEO optimizations while maintaining readability"""
   
   def __init__(self, config: Dict[str, any] = None):
       self.config = config or {}
       
       # Enhancement patterns and strategies
       self.enhancement_strategies = {
           'keyword_integration': {
               'natural_positions': ['beginning', 'middle', 'end'],
               'max_density': 0.03,
               'min_distance': 5  # words between keyword repetitions
           },
           'readability': {
               'max_sentence_length': 20,
               'prefer_active_voice': True,
               'use_transitions': True
           },
           'engagement': {
               'add_questions': True,
               'use_action_words': True,
               'include_numbers': True
           }
       }
       
       # Transition words for better flow
       self.transition_words = [
           'however', 'moreover', 'furthermore', 'additionally',
           'meanwhile', 'therefore', 'consequently', 'subsequently'
       ]
       
       # Action words for engagement
       self.action_words = [
           'discover', 'explore', 'learn', 'master', 'unlock',
           'boost', 'improve', 'optimize', 'transform', 'achieve'
       ]
       
       # Question starters
       self.question_starters = [
           'What if', 'How can', 'Why do', 'When should',
           'Where will', 'Which approach', 'Who benefits'
       ]
   
   def enhance_with_keywords(self, content: str, keywords: List[str],
                           target_density: float = 0.02) -> str:
       """
       Enhance content by naturally integrating keywords
       
       Args:
           content: Original content
           keywords: Keywords to integrate
           target_density: Target keyword density
           
       Returns:
           Enhanced content with integrated keywords
       """
       try:
           if not keywords:
               return content
           
           words = content.split()
           total_words = len(words)
           enhanced_content = content
           
           for keyword in keywords[:3]:  # Limit to top 3 keywords
               current_count = enhanced_content.lower().count(keyword.lower())
               current_density = current_count / total_words if total_words > 0 else 0
               
               if current_density < target_density:
                   target_count = max(1, int(total_words * target_density))
                   additions_needed = target_count - current_count
                   
                   enhanced_content = self._integrate_keyword_naturally(
                       enhanced_content, keyword, additions_needed
                   )
           
           return enhanced_content
           
       except Exception as e:
           logger.error(f"Keyword enhancement failed: {e}")
           return content
   
   def _integrate_keyword_naturally(self, content: str, keyword: str, count: int) -> str:
       """Integrate keyword naturally into content"""
       if count <= 0:
           return content
       
       sentences = content.split('.')
       enhanced_sentences = []
       integrations_made = 0
       
       for i, sentence in enumerate(sentences):
           sentence = sentence.strip()
           if not sentence:
               enhanced_sentences.append(sentence)
               continue
           
           # Check if we need more integrations
           if integrations_made < count and keyword.lower() not in sentence.lower():
               
               # Strategy 1: Beginning of sentence
               if i == 0 or integrations_made == 0:
                   if not sentence.lower().startswith(keyword.lower()):
                       sentence = f"{keyword} " + sentence.lower()
                       integrations_made += 1
               
               # Strategy 2: Natural context integration
               elif integrations_made < count:
                   integrated_sentence = self._find_natural_integration_point(sentence, keyword)
                   if integrated_sentence != sentence:
                       sentence = integrated_sentence
                       integrations_made += 1
           
           enhanced_sentences.append(sentence)
       
       return '. '.join([s for s in enhanced_sentences if s.strip()])
   
   def _find_natural_integration_point(self, sentence: str, keyword: str) -> str:
       """Find natural points to integrate keyword in sentence"""
       # Strategy: Add keyword as a subject or object modifier
       
       # Look for common patterns where keyword can be naturally added
       patterns = [
           (r'\b(using|with|through|via)\s+', f'\\1 {keyword} '),
           (r'\b(about|regarding|concerning)\s+', f'\\1 {keyword} '),
           (r'\b(for|in|on)\s+(\w+)', f'\\1 {keyword} \\2'),
       ]
       
       for pattern, replacement in patterns:
           if re.search(pattern, sentence, re.IGNORECASE):
               new_sentence = re.sub(pattern, replacement, sentence, count=1, flags=re.IGNORECASE)
               if new_sentence != sentence:
                   return new_sentence
       
       return sentence
   
   def improve_readability(self, content: str) -> str:
       """Improve content readability"""
       try:
           # Break up long sentences
           content = self._break_long_sentences(content)
           
           # Add transition words for better flow
           content = self._add_transitions(content)
           
           # Improve sentence structure
           content = self._improve_sentence_structure(content)
           
           # Ensure proper punctuation
           content = self._fix_punctuation(content)
           
           return content
           
       except Exception as e:
           logger.error(f"Readability improvement failed: {e}")
           return content
   
   def _break_long_sentences(self, content: str) -> str:
       """Break up sentences that are too long"""
       sentences = content.split('.')
       improved_sentences = []
       
       for sentence in sentences:
           sentence = sentence.strip()
           if not sentence:
               continue
           
           words = sentence.split()
           if len(words) > 20:  # Long sentence
               # Try to break at conjunctions
               break_points = ['and', 'but', 'or', 'so', 'yet']
               
               for break_word in break_points:
                   if f' {break_word} ' in sentence:
                       parts = sentence.split(f' {break_word} ', 1)
                       if len(parts) == 2 and len(parts[0].split()) > 5:
                           improved_sentences.append(parts[0].strip())
                           improved_sentences.append(f"{break_word.capitalize()} {parts[1].strip()}")
                           break
               else:
                   # No good break point found, keep original
                   improved_sentences.append(sentence)
           else:
               improved_sentences.append(sentence)
       
       return '. '.join(improved_sentences)
   
   def _add_transitions(self, content: str) -> str:
       """Add transition words for better flow"""
       sentences = content.split('.')
       
       if len(sentences) < 3:
           return content
       
       # Add transitions to middle sentences
       for i in range(1, len(sentences) - 1):
           sentence = sentences[i].strip()
           if sentence and not any(trans in sentence.lower() for trans in self.transition_words):
               # Add appropriate transition
               if i == 1:
                   sentences[i] = f" Moreover, {sentence.lower()}"
               elif i == len(sentences) - 2:
                   sentences[i] = f" Finally, {sentence.lower()}"
               else:
                   sentences[i] = f" Additionally, {sentence.lower()}"
       
       return '. '.join([s for s in sentences if s.strip()])
   
   def _improve_sentence_structure(self, content: str) -> str:
       """Improve sentence structure for better readability"""
       # Convert passive voice to active where possible
       passive_patterns = [
           (r'(\w+) was (\w+ed) by', r'\\2 \\1'),
           (r'(\w+) is (\w+ed) by', r'\\2 \\1'),
       ]
       
       for pattern, replacement in passive_patterns:
           content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
       
       return content
   
   def _fix_punctuation(self, content: str) -> str:
       """Fix punctuation issues"""
       # Fix double spaces
       content = re.sub(r'\s+', ' ', content)
       
       # Fix punctuation spacing
       content = re.sub(r'\s+([.,!?])', r'\1', content)
       content = re.sub(r'([.,!?])(\w)', r'\1 \2', content)
       
       # Ensure content ends with proper punctuation
       content = content.strip()
       if content and content[-1] not in '.!?':
           content += '.'
       
       return content
   
   def add_engagement_elements(self, content: str) -> str:
       """Add elements to improve engagement"""
       try:
           # Add question if none exists
           if '?' not in content:
               content = self._add_engaging_question(content)
           
           # Add action words
           content = self._enhance_with_action_words(content)
           
           # Add numbers for attention
           content = self._add_attention_grabbing_numbers(content)
           
           return content
           
       except Exception as e:
           logger.error(f"Engagement enhancement failed: {e}")
           return content
   
   def _add_engaging_question(self, content: str) -> str:
       """Add an engaging question to the content"""
       # Analyze content to generate relevant question
       words = content.lower().split()
       
       if any(word in words for word in ['tip', 'tips', 'advice', 'guide']):
           return content + " What tips have worked best for you?"
       elif any(word in words for word in ['experience', 'try', 'test']):
           return content + " Have you tried this approach?"
       elif any(word in words for word in ['strategy', 'approach', 'method']):
           return content + " What strategy do you prefer?"
       else:
           return content + " What are your thoughts?"
   
   def _enhance_with_action_words(self, content: str) -> str:
       """Enhance content with action words"""
       # Replace weak verbs with stronger action words
       weak_to_strong = {
           'use': 'leverage',
           'make': 'create',
           'get': 'achieve',
           'do': 'execute',
           'see': 'discover',
           'find': 'uncover'
       }
       
       words = content.split()
       enhanced_words = []
       
       for word in words:
           clean_word = word.lower().strip('.,!?')
           if clean_word in weak_to_strong:
               replacement = weak_to_strong[clean_word]
               enhanced_words.append(word.replace(clean_word, replacement))
           else:
               enhanced_words.append(word)
       
       return ' '.join(enhanced_words)
   
   def _add_attention_grabbing_numbers(self, content: str) -> str:
       """Add numbers to make content more attention-grabbing"""
       # If content has no numbers, try to add some context
       if not any(char.isdigit() for char in content):
           # Add percentage or statistic if appropriate
           enhancement_numbers = {
               'productivity': '30% more productive',
               'efficiency': '50% more efficient', 
               'growth': '2x faster growth',
               'performance': '25% better performance',
               'results': '3x better results'
           }
           
           content_lower = content.lower()
           for keyword, number_phrase in enhancement_numbers.items():
               if keyword in content_lower and number_phrase not in content_lower:
                   content = content.replace(keyword, f"{number_phrase} {keyword}", 1)
                   break
       
       return content
   
   def optimize_for_platform(self, content: str, platform: str = 'twitter') -> str:
       """Optimize content for specific social media platform"""
       try:
           if platform.lower() == 'twitter':
               return self._optimize_for_twitter(content)
           elif platform.lower() == 'linkedin':
               return self._optimize_for_linkedin(content)
           elif platform.lower() == 'facebook':
               return self._optimize_for_facebook(content)
           else:
               return content
               
       except Exception as e:
           logger.error(f"Platform optimization failed: {e}")
           return content
   
   def _optimize_for_twitter(self, content: str) -> str:
       """Optimize content specifically for Twitter"""
       # Ensure content is concise
       if len(content) > 250:  # Leave room for hashtags
           content = self._shorten_content(content, 250)
       
       # Add engagement elements
       if not any(char in content for char in '?!'):
           content = content.rstrip('.') + '!'
       
       # Ensure it's scannable
       content = self._make_scannable(content)
       
       return content
   
   def _optimize_for_linkedin(self, content: str) -> str:
       """Optimize content for LinkedIn"""
       # LinkedIn allows longer content, so we can be more detailed
       # Add professional tone
       content = self._add_professional_tone(content)
       
       # Add industry insights
       content = self._add_industry_context(content)
       
       return content
   
   def _optimize_for_facebook(self, content: str) -> str:
       """Optimize content for Facebook"""
       # Facebook favors personal, story-driven content
       content = self._add_personal_touch(content)
       
       # Add emotional elements
       content = self._add_emotional_elements(content)
       
       return content
   
   def _shorten_content(self, content: str, max_length: int) -> str:
       """Shorten content while preserving meaning"""
       if len(content) <= max_length:
           return content
       
       # Try to shorten by removing filler words
       filler_words = ['very', 'really', 'quite', 'rather', 'somewhat', 'absolutely']
       words = content.split()
       
       shortened_words = [word for word in words if word.lower() not in filler_words]
       shortened_content = ' '.join(shortened_words)
       
       if len(shortened_content) <= max_length:
           return shortened_content
       
       # If still too long, truncate at sentence boundary
       sentences = content.split('.')
       truncated = ""
       
       for sentence in sentences:
           if len(truncated + sentence + '.') <= max_length - 3:  # Leave room for "..."
               truncated += sentence + '.'
           else:
               break
       
       return truncated.strip() + "..." if truncated else content[:max_length-3] + "..."
   
   def _make_scannable(self, content: str) -> str:
       """Make content more scannable"""
       # Add emphasis to key phrases
       key_phrases = ['important', 'key', 'essential', 'crucial', 'critical']
       
       for phrase in key_phrases:
           content = content.replace(phrase, phrase.upper())
       
       return content
   
   def _add_professional_tone(self, content: str) -> str:
       """Add professional tone for LinkedIn"""
       # Replace casual words with professional equivalents
       casual_to_professional = {
           'cool': 'innovative',
           'awesome': 'excellent',
           'great': 'outstanding',
           'nice': 'valuable'
       }
       
       for casual, professional in casual_to_professional.items():
           content = re.sub(r'\b' + casual + r'\b', professional, content, flags=re.IGNORECASE)
       
       return content
   
   def _add_industry_context(self, content: str) -> str:
       """Add industry context for professional platforms"""
       # Add industry-relevant insights
       if 'technology' in content.lower():
           content += " This aligns with current digital transformation trends."
       elif 'business' in content.lower():
           content += " Essential for modern business strategy."
       
       return content
   
   def _add_personal_touch(self, content: str) -> str:
       """Add personal elements for Facebook"""
       # Add personal pronouns if missing
       if not any(pronoun in content.lower() for pronoun in ['i', 'my', 'we', 'our']):
           content = "I've found that " + content.lower()
       
       return content
   
   def _add_emotional_elements(self, content: str) -> str:
       """Add emotional elements to content"""
       # Add emotional words
       if not any(word in content.lower() for word in ['love', 'excited', 'amazing', 'incredible']):
           content = content + " Excited to see what comes next!"
       
       return content
   
   def enhance_for_seo_score(self, content: str, target_score: float = 0.8) -> str:
       """Enhance content to achieve target SEO score"""
       try:
           enhanced_content = content
           
           # Progressive enhancement based on current score
           current_score = self._estimate_seo_score(enhanced_content)
           
           while current_score < target_score:
               # Apply enhancements in order of impact
               if current_score < 0.3:
                   enhanced_content = self.improve_readability(enhanced_content)
               elif current_score < 0.5:
                   enhanced_content = self.add_engagement_elements(enhanced_content)
               elif current_score < 0.7:
                   enhanced_content = self._add_structural_improvements(enhanced_content)
               else:
                   break  # Good enough
               
               new_score = self._estimate_seo_score(enhanced_content)
               if new_score <= current_score:
                   break  # No improvement, stop
               current_score = new_score
           
           return enhanced_content
           
       except Exception as e:
           logger.error(f"SEO score enhancement failed: {e}")
           return content
   
   def _estimate_seo_score(self, content: str) -> float:
       """Estimate SEO score of content"""
       score = 0.0
       
       # Length score
       word_count = len(content.split())
       if 15 <= word_count <= 30:
           score += 0.2
       
       # Engagement elements
       if '?' in content:
           score += 0.2
       if any(word in content.lower() for word in self.action_words):
           score += 0.2
       
       # Structure score
       if content.count('.') >= 1:  # Multiple sentences
           score += 0.2
       
       # Readability
       avg_sentence_length = word_count / max(1, content.count('.'))
       if avg_sentence_length <= 15:
           score += 0.2
       
       return min(1.0, score)
   
   def _add_structural_improvements(self, content: str) -> str:
       """Add structural improvements for better SEO"""
       # Add bullet points for lists (simplified)
       if ' and ' in content and content.count(' and ') >= 2:
           # Convert lists to more structured format
           content = content.replace(' and ', ', ')
           content = content.replace(', ', ' • ')
       
       # Add emphasis to important points
       important_indicators = ['important', 'key', 'essential', 'crucial']
       for indicator in important_indicators:
           content = re.sub(
               f'({indicator}\\s+\\w+)', 
               r'**\1**', 
               content, 
               flags=re.IGNORECASE
           )
       
       return content
   

class AdvancedContentAnalyzer:
    """Advanced content analysis for optimization insights"""
    
    def __init__(self):
        self.readability_metrics = {}
        self.engagement_patterns = {}
        self.sentiment_indicators = {}
        
        # Initialize analysis patterns
        self._initialize_analysis_patterns()
    
    def _initialize_analysis_patterns(self):
        """Initialize content analysis patterns"""
        self.readability_metrics = {
            'sentence_length_optimal': (10, 20),
            'word_length_optimal': (4, 8),
            'syllable_count_optimal': (1, 3),
            'passive_voice_threshold': 0.1,
            'transition_word_ratio': 0.05
        }
        
        self.engagement_patterns = {
            'question_indicators': ['?', 'what', 'how', 'why', 'when', 'where', 'which', 'who'],
            'action_verbs': ['discover', 'learn', 'master', 'achieve', 'unlock', 'boost', 'transform'],
            'emotional_triggers': ['amazing', 'incredible', 'shocking', 'surprising', 'powerful'],
            'urgency_words': ['now', 'today', 'limited', 'urgent', 'immediate', 'quickly'],
            'social_proof': ['proven', 'tested', 'trusted', 'recommended', 'popular']
        }
        
        self.sentiment_indicators = {
            'positive': ['excellent', 'outstanding', 'fantastic', 'brilliant', 'amazing', 'perfect'],
            'negative': ['terrible', 'awful', 'horrible', 'disappointing', 'frustrating', 'worst'],
            'neutral': ['adequate', 'acceptable', 'standard', 'typical', 'normal', 'average']
        }
    
    def analyze_content_structure(self, content: str) -> Dict[str, Any]:
        """Analyze content structure and provide detailed metrics"""
        try:
            sentences = self._split_sentences(content)
            words = content.split()
            
            analysis = {
                'basic_metrics': {
                    'character_count': len(content),
                    'word_count': len(words),
                    'sentence_count': len(sentences),
                    'paragraph_count': content.count('\n\n') + 1,
                    'avg_words_per_sentence': len(words) / max(len(sentences), 1),
                    'avg_chars_per_word': sum(len(word) for word in words) / max(len(words), 1)
                },
                'readability': self._analyze_readability(content, sentences, words),
                'engagement': self._analyze_engagement_potential(content),
                'structure': self._analyze_structure_quality(content, sentences),
                'sentiment': self._analyze_sentiment_distribution(content),
                'seo_factors': self._analyze_seo_factors(content)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Content structure analysis failed: {e}")
            return {}
    
    def _split_sentences(self, content: str) -> List[str]:
        """Split content into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', content)
        return [s.strip() for s in sentences if s.strip()]
    
    def _analyze_readability(self, content: str, sentences: List[str], words: List[str]) -> Dict[str, Any]:
        """Analyze content readability"""
        if not sentences or not words:
            return {'score': 0.0, 'issues': ['No readable content']}
        
        issues = []
        score = 1.0
        
        # Sentence length analysis
        long_sentences = [s for s in sentences if len(s.split()) > 25]
        if long_sentences:
            score -= 0.2
            issues.append(f"{len(long_sentences)} sentences are too long")
        
        # Word complexity analysis
        complex_words = [w for w in words if len(w) > 12]
        complexity_ratio = len(complex_words) / len(words)
        if complexity_ratio > 0.15:
            score -= 0.15
            issues.append("Too many complex words")
        
        # Passive voice detection (simplified)
        passive_indicators = ['was', 'were', 'been', 'being']
        passive_count = sum(1 for word in words if word.lower() in passive_indicators)
        passive_ratio = passive_count / len(words)
        if passive_ratio > 0.1:
            score -= 0.1
            issues.append("Consider reducing passive voice")
        
        # Transition words
        transition_words = ['however', 'therefore', 'moreover', 'furthermore', 'additionally']
        transition_count = sum(1 for word in words if word.lower() in transition_words)
        if len(sentences) > 3 and transition_count == 0:
            score -= 0.1
            issues.append("Add transition words for better flow")
        
        return {
            'score': max(0.0, score),
            'avg_sentence_length': sum(len(s.split()) for s in sentences) / len(sentences),
            'complex_word_ratio': complexity_ratio,
            'passive_voice_ratio': passive_ratio,
            'issues': issues,
            'suggestions': self._generate_readability_suggestions(issues)
        }
    
    def _analyze_engagement_potential(self, content: str) -> Dict[str, Any]:
        """Analyze content engagement potential"""
        content_lower = content.lower()
        score = 0.0
        elements = []
        
        # Check for questions
        if '?' in content:
            score += 0.3
            elements.append('contains_question')
        
        # Check for action verbs
        action_count = sum(1 for verb in self.engagement_patterns['action_verbs'] 
                          if verb in content_lower)
        if action_count > 0:
            score += min(0.2, action_count * 0.05)
            elements.append(f'{action_count}_action_verbs')
        
        # Check for emotional triggers
        emotion_count = sum(1 for trigger in self.engagement_patterns['emotional_triggers']
                           if trigger in content_lower)
        if emotion_count > 0:
            score += min(0.2, emotion_count * 0.1)
            elements.append(f'{emotion_count}_emotional_triggers')
        
        # Check for personal pronouns
        personal_pronouns = ['you', 'your', 'we', 'our', 'us', 'i', 'my']
        pronoun_count = sum(1 for pronoun in personal_pronouns if pronoun in content_lower)
        if pronoun_count > 0:
            score += min(0.15, pronoun_count * 0.03)
            elements.append('uses_personal_pronouns')
        
        # Check for numbers
        if any(char.isdigit() for char in content):
            score += 0.1
            elements.append('contains_numbers')
        
        # Check for urgency
        urgency_count = sum(1 for word in self.engagement_patterns['urgency_words']
                           if word in content_lower)
        if urgency_count > 0:
            score += min(0.1, urgency_count * 0.05)
            elements.append('has_urgency')
        
        return {
            'score': min(1.0, score),
            'elements': elements,
            'suggestions': self._generate_engagement_suggestions(score, elements)
        }
    
    def _analyze_structure_quality(self, content: str, sentences: List[str]) -> Dict[str, Any]:
        """Analyze content structure quality"""
        issues = []
        score = 1.0
        
        # Check for proper capitalization
        if not content[0].isupper():
            score -= 0.1
            issues.append("Content should start with capital letter")
        
        # Check for proper punctuation
        if not content.rstrip().endswith(('.', '!', '?')):
            score -= 0.1
            issues.append("Content should end with proper punctuation")
        
        # Check for paragraph structure
        if len(content) > 200 and '\n' not in content:
            score -= 0.1
            issues.append("Consider breaking into paragraphs for longer content")
        
        # Check for repetitive sentence starts
        if len(sentences) > 2:
            first_words = [s.split()[0].lower() for s in sentences if s.split()]
            if len(set(first_words)) < len(first_words) * 0.7:
                score -= 0.1
                issues.append("Vary sentence beginnings")
        
        return {
            'score': max(0.0, score),
            'issues': issues,
            'suggestions': self._generate_structure_suggestions(issues)
        }
    
    def _analyze_sentiment_distribution(self, content: str) -> Dict[str, Any]:
        """Analyze sentiment distribution in content"""
        content_lower = content.lower()
        
        sentiment_counts = {
            'positive': 0,
            'negative': 0,
            'neutral': 0
        }
        
        for sentiment, words in self.sentiment_indicators.items():
            count = sum(1 for word in words if word in content_lower)
            sentiment_counts[sentiment] = count
        
        total_sentiment_words = sum(sentiment_counts.values())
        
        if total_sentiment_words > 0:
            sentiment_ratios = {
                k: v / total_sentiment_words for k, v in sentiment_counts.items()
            }
            dominant_sentiment = max(sentiment_ratios, key=sentiment_ratios.get)
        else:
            sentiment_ratios = {'positive': 0.33, 'negative': 0.33, 'neutral': 0.34}
            dominant_sentiment = 'neutral'
        
        return {
            'dominant': dominant_sentiment,
            'ratios': sentiment_ratios,
            'word_counts': sentiment_counts,
            'total_sentiment_words': total_sentiment_words
        }
    
    def _analyze_seo_factors(self, content: str) -> Dict[str, Any]:
        """Analyze SEO-related factors"""
        factors = {
            'keyword_density': {},
            'hashtag_count': len(re.findall(r'#\w+', content)),
            'mention_count': len(re.findall(r'@\w+', content)),
            'url_count': len(re.findall(r'https?://\S+', content)),
            'has_call_to_action': self._has_call_to_action(content),
            'content_length_optimal': self._is_optimal_length(content)
        }
        
        return factors
    
    def _has_call_to_action(self, content: str) -> bool:
        """Check if content has call-to-action"""
        cta_patterns = [
            r'\bshare\b', r'\bcomment\b', r'\blike\b', r'\bfollow\b',
            r'\bclick\b', r'\btry\b', r'\bget\b', r'\bjoin\b',
            r'\blearn more\b', r'\bfind out\b', r'\bdiscover\b'
        ]
        
        content_lower = content.lower()
        return any(re.search(pattern, content_lower) for pattern in cta_patterns)
    
    def _is_optimal_length(self, content: str) -> bool:
        """Check if content length is optimal for engagement"""
        char_count = len(content)
        # Optimal length varies by platform - using Twitter as default
        return 100 <= char_count <= 250
    
    def _generate_readability_suggestions(self, issues: List[str]) -> List[str]:
        """Generate suggestions to improve readability"""
        suggestions = []
        
        for issue in issues:
            if "too long" in issue:
                suggestions.append("Break long sentences into shorter ones")
            elif "complex words" in issue:
                suggestions.append("Replace complex words with simpler alternatives")
            elif "passive voice" in issue:
                suggestions.append("Use active voice for stronger impact")
            elif "transition words" in issue:
                suggestions.append("Add transition words to improve flow")
        
        return suggestions
    
    def _generate_engagement_suggestions(self, score: float, elements: List[str]) -> List[str]:
        """Generate suggestions to improve engagement"""
        suggestions = []
        
        if score < 0.3:
            suggestions.append("Add questions to encourage interaction")
            suggestions.append("Use action verbs to motivate readers")
            suggestions.append("Include emotional triggers for impact")
        
        if 'contains_question' not in elements:
            suggestions.append("Ask a question to boost engagement")
        
        if 'uses_personal_pronouns' not in elements:
            suggestions.append("Use 'you' or 'your' to make it personal")
        
        if 'contains_numbers' not in elements:
            suggestions.append("Add statistics or numbers for credibility")
        
        return suggestions
    
    def _generate_structure_suggestions(self, issues: List[str]) -> List[str]:
        """Generate suggestions to improve structure"""
        suggestions = []
        
        for issue in issues:
            if "capital letter" in issue:
                suggestions.append("Start content with proper capitalization")
            elif "punctuation" in issue:
                suggestions.append("End content with appropriate punctuation")
            elif "paragraphs" in issue:
                suggestions.append("Break long content into paragraphs")
            elif "sentence beginnings" in issue:
                suggestions.append("Vary how you start sentences")
        
        return suggestions

class ContentOptimizationEngine:
    """Advanced content optimization engine"""
    
    def __init__(self, content_enhancer: ContentEnhancer):
        self.content_enhancer = content_enhancer
        self.content_analyzer = AdvancedContentAnalyzer()
        
        # Optimization strategies
        self.optimization_strategies = {
            'engagement_focused': self._optimize_for_engagement,
            'readability_focused': self._optimize_for_readability,
            'seo_focused': self._optimize_for_seo,
            'viral_potential': self._optimize_for_virality,
            'professional_tone': self._optimize_for_professional_tone
        }
    
    def optimize_content_comprehensive(self, content: str, 
                                     strategy: str = 'engagement_focused',
                                     target_metrics: Dict[str, float] = None) -> Dict[str, Any]:
        """Comprehensive content optimization"""
        try:
            # Analyze current content
            initial_analysis = self.content_analyzer.analyze_content_structure(content)
            
            # Apply optimization strategy
            if strategy in self.optimization_strategies:
                optimized_content = self.optimization_strategies[strategy](content, initial_analysis)
            else:
                optimized_content = content
            
            # Re-analyze optimized content
            final_analysis = self.content_analyzer.analyze_content_structure(optimized_content)
            
            # Calculate improvement metrics
            improvements = self._calculate_improvements(initial_analysis, final_analysis)
            
            return {
                'original_content': content,
                'optimized_content': optimized_content,
                'initial_analysis': initial_analysis,
                'final_analysis': final_analysis,
                'improvements': improvements,
                'optimization_strategy': strategy,
                'recommendations': self._generate_next_step_recommendations(final_analysis)
            }
            
        except Exception as e:
            logger.error(f"Comprehensive optimization failed: {e}")
            return {'error': str(e)}
    
    def _optimize_for_engagement(self, content: str, analysis: Dict[str, Any]) -> str:
        """Optimize content specifically for engagement"""
        optimized = content
        
        # Add question if missing
        engagement_score = analysis.get('engagement', {}).get('score', 0)
        if engagement_score < 0.5 and '?' not in optimized:
            optimized = self.content_enhancer.add_engagement_elements(optimized)
        
        # Enhance with action words
        optimized = self.content_enhancer._enhance_with_action_words(optimized)
        
        # Add personal touch
        if not any(pronoun in optimized.lower() for pronoun in ['you', 'your', 'we']):
            optimized = f"You'll love this: {optimized}"
        
        # Add numbers for attention
        optimized = self.content_enhancer._add_attention_grabbing_numbers(optimized)
        
        return optimized
    
    def _optimize_for_readability(self, content: str, analysis: Dict[str, Any]) -> str:
        """Optimize content for better readability"""
        optimized = content
        
        # Improve readability
        optimized = self.content_enhancer.improve_readability(optimized)
        
        # Break long sentences
        optimized = self.content_enhancer._break_long_sentences(optimized)
        
        # Add transitions
        optimized = self.content_enhancer._add_transitions(optimized)
        
        # Fix punctuation
        optimized = self.content_enhancer._fix_punctuation(optimized)
        
        return optimized
    
    def _optimize_for_seo(self, content: str, analysis: Dict[str, Any]) -> str:
        """Optimize content for SEO"""
        optimized = content
        
        # Ensure optimal length
        readability = analysis.get('readability', {})
        if readability.get('avg_sentence_length', 0) > 20:
            optimized = self.content_enhancer._break_long_sentences(optimized)
        
        # Add structure
        optimized = self.content_enhancer._add_structural_improvements(optimized)
        
        # Enhance for SEO score
        optimized = self.content_enhancer.enhance_for_seo_score(optimized)
        
        return optimized
    
    def _optimize_for_virality(self, content: str, analysis: Dict[str, Any]) -> str:
        """Optimize content for viral potential"""
        optimized = content
        
        # Add emotional elements
        optimized = self.content_enhancer._add_emotional_elements(optimized)
        
        # Add urgency
        if 'urgent' not in optimized.lower() and 'now' not in optimized.lower():
            optimized = f"This is happening now: {optimized}"
        
        # Add social proof elements
        if not any(word in optimized.lower() for word in ['proven', 'trusted', 'recommended']):
            optimized = optimized.replace('.', ' - proven approach.')
        
        # Make it scannable
        optimized = self.content_enhancer._make_scannable(optimized)
        
        return optimized
    
    def _optimize_for_professional_tone(self, content: str, analysis: Dict[str, Any]) -> str:
        """Optimize content for professional tone"""
        optimized = content
        
        # Add professional tone
        optimized = self.content_enhancer._add_professional_tone(optimized)
        
        # Add industry context
        optimized = self.content_enhancer._add_industry_context(optimized)
        
        # Ensure formal structure
        if not optimized.endswith('.'):
            optimized += '.'
        
        return optimized
    
    def _calculate_improvements(self, initial: Dict[str, Any], final: Dict[str, Any]) -> Dict[str, float]:
        """Calculate improvement metrics"""
        improvements = {}
        
        try:
            # Readability improvement
            initial_readability = initial.get('readability', {}).get('score', 0)
            final_readability = final.get('readability', {}).get('score', 0)
            improvements['readability'] = final_readability - initial_readability
            
            # Engagement improvement
            initial_engagement = initial.get('engagement', {}).get('score', 0)
            final_engagement = final.get('engagement', {}).get('score', 0)
            improvements['engagement'] = final_engagement - initial_engagement
            
            # Structure improvement
            initial_structure = initial.get('structure', {}).get('score', 0)
            final_structure = final.get('structure', {}).get('score', 0)
            improvements['structure'] = final_structure - initial_structure
            
            # Overall improvement
            improvements['overall'] = (
                improvements.get('readability', 0) * 0.4 +
                improvements.get('engagement', 0) * 0.4 +
                improvements.get('structure', 0) * 0.2
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate improvements: {e}")
        
        return improvements
    
    def _generate_next_step_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate next step recommendations"""
        recommendations = []
        
        try:
            # Check readability
            readability_score = analysis.get('readability', {}).get('score', 0)
            if readability_score < 0.7:
                recommendations.append("Further improve readability by simplifying language")
            
            # Check engagement
            engagement_score = analysis.get('engagement', {}).get('score', 0)
            if engagement_score < 0.6:
                recommendations.append("Add more interactive elements like questions or polls")
            
            # Check structure
            structure_score = analysis.get('structure', {}).get('score', 0)
            if structure_score < 0.8:
                recommendations.append("Improve content structure and formatting")
            
            # Check sentiment
            sentiment = analysis.get('sentiment', {})
            if sentiment.get('dominant') == 'neutral':
                recommendations.append("Add more emotional impact to connect with audience")
            
            # Check SEO factors
            seo_factors = analysis.get('seo_factors', {})
            if not seo_factors.get('has_call_to_action'):
                recommendations.append("Include a clear call-to-action")
            
            if not seo_factors.get('content_length_optimal'):
                recommendations.append("Adjust content length for optimal engagement")
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
        
        return recommendations[:5]  # Limit to top 5 recommendations

class ContentPersonalizer:
    """Personalizes content based on audience and context"""
    
    def __init__(self):
        self.audience_profiles = self._initialize_audience_profiles()
        self.personalization_strategies = self._initialize_personalization_strategies()
    
    def _initialize_audience_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Initialize audience profiles"""
        return {
            'entrepreneurs': {
                'interests': ['growth', 'funding', 'innovation', 'leadership'],
                'tone_preference': 'motivational',
                'content_style': 'actionable',
                'keywords': ['startup', 'scale', 'disrupt', 'validate']
            },
            'developers': {
                'interests': ['technology', 'coding', 'tools', 'efficiency'],
                'tone_preference': 'technical',
                'content_style': 'detailed',
                'keywords': ['code', 'development', 'framework', 'api']
            },
            'marketers': {
                'interests': ['campaigns', 'analytics', 'growth', 'conversion'],
                'tone_preference': 'results-focused',
                'content_style': 'data-driven',
                'keywords': ['roi', 'conversion', 'funnel', 'optimization']
            },
            'general_business': {
                'interests': ['productivity', 'strategy', 'leadership', 'growth'],
                'tone_preference': 'professional',
                'content_style': 'insights',
                'keywords': ['business', 'strategy', 'efficiency', 'success']
            }
        }
    
    def _initialize_personalization_strategies(self) -> Dict[str, callable]:
        """Initialize personalization strategies"""
        return {
            'audience_specific': self._personalize_for_audience,
            'tone_matching': self._match_tone_to_audience,
            'keyword_optimization': self._optimize_keywords_for_audience,
            'content_format': self._format_for_audience
        }
    
    def personalize_content(self, content: str, audience: str, 
                          personalization_level: str = 'moderate') -> str:
        """Personalize content for specific audience"""
        try:
            if audience not in self.audience_profiles:
                audience = 'general_business'  # Default fallback
            
            profile = self.audience_profiles[audience]
            personalized = content
            
            # Apply personalization strategies based on level
            if personalization_level in ['moderate', 'aggressive']:
                personalized = self._personalize_for_audience(personalized, profile)
                personalized = self._match_tone_to_audience(personalized, profile)
            
            if personalization_level == 'aggressive':
                personalized = self._optimize_keywords_for_audience(personalized, profile)
                personalized = self._format_for_audience(personalized, profile)
            
            return personalized
            
        except Exception as e:
            logger.error(f"Content personalization failed: {e}")
            return content
    
    def _personalize_for_audience(self, content: str, profile: Dict[str, Any]) -> str:
        """Personalize content based on audience profile"""
        interests = profile.get('interests', [])
        
        # Add audience-relevant context
        if 'growth' in interests and 'growth' not in content.lower():
            content = content + " Perfect for scaling your growth."
        
        if 'innovation' in interests and 'innovation' not in content.lower():
            content = content.replace('.', ' through innovation.')
        
        return content
    
    def _match_tone_to_audience(self, content: str, profile: Dict[str, Any]) -> str:
        """Match tone to audience preference"""
        tone_preference = profile.get('tone_preference', 'professional')
        
        if tone_preference == 'motivational':
            if not any(word in content.lower() for word in ['achieve', 'success', 'win', 'excel']):
                content = f"Ready to achieve more? {content}"
        
        elif tone_preference == 'technical':
            # Add technical precision
            content = content.replace('better', 'more efficient')
            content = content.replace('good', 'optimized')
        
        elif tone_preference == 'results-focused':
            if not any(word in content.lower() for word in ['results', 'roi', 'impact', 'metrics']):
                content = content + " Track your results."
        
        return content
    
    def _optimize_keywords_for_audience(self, content: str, profile: Dict[str, Any]) -> str:
        """Optimize keywords for specific audience"""
        keywords = profile.get('keywords', [])
        
        # Naturally integrate audience-specific keywords
        for keyword in keywords[:2]:  # Limit to avoid over-optimization
            if keyword.lower() not in content.lower():
                content = content.replace('.', f' {keyword}.', 1)
        
        return content
    
    def _format_for_audience(self, content: str, profile: Dict[str, Any]) -> str:
        """Format content for audience preference"""
        content_style = profile.get('content_style', 'insights')
        
        if content_style == 'actionable':
            if not content.startswith(('Here', 'Try', 'Start', 'Use')):
                content = f"Here's how: {content}"
        
        elif content_style == 'detailed':
            if len(content.split()) < 20:
                content = content + " Let me explain the technical details."
        
        elif content_style == 'data-driven':
            if not any(char.isdigit() for char in content):
                content = content + " Studies show 73% improvement."
        
        return content

# Enhanced ContentEnhancer with new components
class EnhancedContentEnhancer(ContentEnhancer):
    """Enhanced content enhancer with advanced analysis and optimization"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
        # Initialize enhanced components
        self.content_analyzer = AdvancedContentAnalyzer()
        self.optimization_engine = ContentOptimizationEngine(self)
        self.personalizer = ContentPersonalizer()
    
    def enhance_content_advanced(self, content: str, 
                               target_audience: str = 'general_business',
                               optimization_strategy: str = 'engagement_focused',
                               personalization_level: str = 'moderate') -> Dict[str, Any]:
        """Advanced content enhancement with comprehensive analysis"""
        try:
            # Step 1: Analyze current content
            initial_analysis = self.content_analyzer.analyze_content_structure(content)
            
            # Step 2: Apply optimization strategy
            optimized_content = self.optimization_engine.optimize_content_comprehensive(
                content, optimization_strategy
            )
            
            # Step 3: Personalize for target audience
            personalized_content = self.personalizer.personalize_content(
                optimized_content.get('optimized_content', content),
                target_audience,
                personalization_level
            )
            
            # Step 4: Final analysis
            final_analysis = self.content_analyzer.analyze_content_structure(personalized_content)
            
            # Step 5: Generate comprehensive report
            enhancement_report = {
                'original_content': content,
                'enhanced_content': personalized_content,
                'initial_analysis': initial_analysis,
                'final_analysis': final_analysis,
                'optimization_details': optimized_content,
                'personalization_applied': {
                    'target_audience': target_audience,
                    'strategy': optimization_strategy,
                    'level': personalization_level
                },
                'improvement_metrics': self._calculate_improvement_metrics(
                    initial_analysis, final_analysis
                ),
                'recommendations': self._generate_final_recommendations(final_analysis)
            }
            
            return enhancement_report
            
        except Exception as e:
            logger.error(f"Advanced content enhancement failed: {e}")
            return {
                'error': str(e),
                'original_content': content,
                'enhanced_content': content  # Fallback to original
            }
    
    def _calculate_improvement_metrics(self, initial: Dict[str, Any], 
                                     final: Dict[str, Any]) -> Dict[str, float]:
        """Calculate improvement metrics between initial and final analysis"""
        try:
            metrics = {}
            
            # Readability improvement
            initial_readability = initial.get('readability', {}).get('score', 0)
            final_readability = final.get('readability', {}).get('score', 0)
            metrics['readability_improvement'] = final_readability - initial_readability
            
            # Engagement improvement
            initial_engagement = initial.get('engagement', {}).get('score', 0)
            final_engagement = final.get('engagement', {}).get('score', 0)
            metrics['engagement_improvement'] = final_engagement - initial_engagement
            
            # Structure improvement
            initial_structure = initial.get('structure', {}).get('score', 0)
            final_structure = final.get('structure', {}).get('score', 0)
            metrics['structure_improvement'] = final_structure - initial_structure
            
            # Overall improvement
            metrics['overall_improvement'] = (
                metrics['readability_improvement'] * 0.3 +
                metrics['engagement_improvement'] * 0.5 +
                metrics['structure_improvement'] * 0.2
            )
            
            # Improvement percentage
            if initial_readability + initial_engagement + initial_structure > 0:
                total_initial = initial_readability + initial_engagement + initial_structure
                total_final = final_readability + final_engagement + final_structure
                metrics['improvement_percentage'] = ((total_final - total_initial) / total_initial) * 100
            else:
                metrics['improvement_percentage'] = 0
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate improvement metrics: {e}")
            return {}
    
    def _generate_final_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate final recommendations based on analysis"""
        recommendations = []
        
        try:
            # Check readability
            readability = analysis.get('readability', {})
            if readability.get('score', 0) < 0.8:
                recommendations.append("Consider simplifying language for better readability")
            
            # Check engagement
            engagement = analysis.get('engagement', {})
            if engagement.get('score', 0) < 0.7:
                recommendations.append("Add more engaging elements like questions or calls-to-action")
            
            # Check structure
            structure = analysis.get('structure', {})
            if structure.get('score', 0) < 0.8:
                recommendations.append("Improve content structure and formatting")
            
            # Check sentiment
            sentiment = analysis.get('sentiment', {})
            if sentiment.get('dominant') == 'neutral':
                recommendations.append("Add more emotional appeal to connect with audience")
            
            # Check length
            basic_metrics = analysis.get('basic_metrics', {})
            word_count = basic_metrics.get('word_count', 0)
            if word_count < 10:
                recommendations.append("Consider expanding content for more impact")
            elif word_count > 100:
                recommendations.append("Consider condensing content for better engagement")
            
            # Limit recommendations
            return recommendations[:5]
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return ["Continue monitoring content performance"]
