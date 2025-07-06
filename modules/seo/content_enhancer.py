"""Content enhancement and optimization engine"""
import re
import math
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import Counter
import logging

logger = logging.getLogger(__name__)

class ContentEnhancer:
    """Advanced content enhancement and optimization"""
    
    def __init__(self, config: Dict[str, any] = None):
        self.config = config or {}
        
        # Content enhancement patterns
        self.enhancement_patterns = {
            'engagement': ['question', 'poll', 'thoughts', 'opinion', 'experience'],
            'action': ['learn', 'discover', 'explore', 'try', 'implement'],
            'urgency': ['now', 'today', 'limited', 'exclusive', 'breaking'],
            'social_proof': ['proven', 'trusted', 'recommended', 'popular', 'trending']
        }
        
        # Platform-specific optimizations
        self.platform_optimizations = {
            'twitter': {
                'max_length': 280,
                'preferred_length': 200,
                'hashtag_limit': 5,
                'mention_limit': 3
            },
            'linkedin': {
                'max_length': 3000,
                'preferred_length': 1000,
                'hashtag_limit': 10,
                'mention_limit': 5
            },
            'facebook': {
                'max_length': 63206,
                'preferred_length': 500,
                'hashtag_limit': 8,
                'mention_limit': 4
            }
        }
        
        # Readability improvement patterns
        self.readability_patterns = {
            'long_sentence_threshold': 25,
            'complex_word_threshold': 0.3,
            'transition_words': [
                'however', 'therefore', 'furthermore', 'moreover', 'consequently',
                'in addition', 'on the other hand', 'for example', 'specifically'
            ]
        }
    
    def enhance_with_keywords(self, content: str, keywords: List[str],
                           target_density: float = 0.02) -> str:
        """
        Enhance content with target keywords while maintaining natural flow
        
        Args:
            content: Original content
            keywords: Target keywords to integrate
            target_density: Target keyword density (0.01 = 1%)
            
        Returns:
            Enhanced content with integrated keywords
        """
        try:
            enhanced_content = content
            words = content.split()
            total_words = len(words)
            
            for keyword in keywords:
                if not keyword or len(keyword.strip()) < 2:
                    continue
                
                # Calculate current density
                current_count = content.lower().count(keyword.lower())
                current_density = current_count / total_words if total_words > 0 else 0
                
                # Calculate target count
                target_count = int(total_words * target_density)
                
                if current_density < target_density:
                    # Need to add keyword
                    additions_needed = target_count - current_count
                    
                    # Integrate keyword naturally
                    enhanced_content = self._integrate_keyword_naturally(
                        enhanced_content, keyword, additions_needed
                    )
                    
                    # Recalculate word count
                    words = enhanced_content.split()
                    total_words = len(words)
            
            return enhanced_content.strip()
            
        except Exception as e:
            logger.error(f"Keyword enhancement failed: {e}")
            return content
    
    def _integrate_keyword_naturally(self, content: str, keyword: str, count: int) -> str:
        """Integrate keyword naturally into content"""
        try:
            sentences = content.split('.')
            integrated_content = []
            additions_made = 0
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    integrated_content.append(sentence)
                    continue
                
                # Check if keyword is already in sentence
                if keyword.lower() in sentence.lower():
                    integrated_content.append(sentence)
                    continue
                
                # Find natural integration point
                if additions_made < count:
                    enhanced_sentence = self._find_natural_integration_point(sentence, keyword)
                    if enhanced_sentence != sentence:
                        additions_made += 1
                    integrated_content.append(enhanced_sentence)
                else:
                    integrated_content.append(sentence)
            
            return '. '.join(integrated_content)
            
        except Exception as e:
            logger.error(f"Natural keyword integration failed: {e}")
            return content
    
    def _find_natural_integration_point(self, sentence: str, keyword: str) -> str:
        """Find natural point to integrate keyword in sentence"""
        try:
            # Try to insert at beginning if sentence is short
            if len(sentence.split()) <= 8:
                return f"{keyword} {sentence}"
            
            # Try to insert after common transition words
            transition_words = ['however', 'therefore', 'furthermore', 'moreover']
            for transition in transition_words:
                if transition in sentence.lower():
                    parts = sentence.split(transition, 1)
                    if len(parts) == 2:
                        return f"{parts[0]}{transition} {keyword} {parts[1]}"
            
            # Insert in middle of sentence
            words = sentence.split()
            if len(words) >= 4:
                mid_point = len(words) // 2
                words.insert(mid_point, keyword)
                return ' '.join(words)
            
            # Fallback: add at end
            return f"{sentence} {keyword}"
            
        except Exception as e:
            logger.error(f"Natural integration point finding failed: {e}")
            return sentence
    
    def improve_readability(self, content: str) -> str:
        """
        Improve content readability through various techniques
        
        Args:
            content: Content to improve
            
        Returns:
            Improved content with better readability
        """
        try:
            improved_content = content
            
            # Break long sentences
            improved_content = self._break_long_sentences(improved_content)
            
            # Add transitions
            improved_content = self._add_transitions(improved_content)
            
            # Improve sentence structure
            improved_content = self._improve_sentence_structure(improved_content)
            
            # Fix punctuation
            improved_content = self._fix_punctuation(improved_content)
            
            return improved_content.strip()
            
        except Exception as e:
            logger.error(f"Readability improvement failed: {e}")
            return content
    
    def _break_long_sentences(self, content: str) -> str:
        """Break long sentences into shorter, more readable ones"""
        try:
            sentences = content.split('.')
            improved_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    improved_sentences.append(sentence)
                    continue
                
                words = sentence.split()
                if len(words) <= self.readability_patterns['long_sentence_threshold']:
                    improved_sentences.append(sentence)
                    continue
                
                # Try to break at natural points
                break_points = ['and', 'but', 'or', 'however', 'therefore', 'furthermore']
                broken = False
                
                for break_point in break_points:
                    if break_point in sentence.lower():
                        parts = sentence.split(break_point, 1)
                        if len(parts) == 2 and len(parts[0].split()) >= 5:
                            improved_sentences.append(f"{parts[0].strip()}. {break_point.capitalize()} {parts[1].strip()}")
                            broken = True
                            break
                
                if not broken:
                    improved_sentences.append(sentence)
            
            return '. '.join(improved_sentences)
            
        except Exception as e:
            logger.error(f"Sentence breaking failed: {e}")
            return content
    
    def _add_transitions(self, content: str) -> str:
        """Add transition words to improve flow"""
        try:
            sentences = content.split('.')
            improved_sentences = []
            
            for i, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if not sentence:
                    improved_sentences.append(sentence)
                    continue
                
                # Add transition if sentence starts with common patterns
                if i > 0 and not any(transition in sentence.lower() 
                                   for transition in self.readability_patterns['transition_words']):
                    # Check if sentence could benefit from transition
                    if len(sentence.split()) > 5:
                        # Add simple transition
                        sentence = f"Additionally, {sentence}"
                
                improved_sentences.append(sentence)
            
            return '. '.join(improved_sentences)
            
        except Exception as e:
            logger.error(f"Transition addition failed: {e}")
            return content
    
    def _improve_sentence_structure(self, content: str) -> str:
        """Improve overall sentence structure"""
        try:
            # Simple improvements
            improved = content
            
            # Fix common issues
            improved = re.sub(r'\s+', ' ', improved)  # Remove extra spaces
            improved = re.sub(r'\.+', '.', improved)  # Fix multiple periods
            
            return improved
            
        except Exception as e:
            logger.error(f"Sentence structure improvement failed: {e}")
            return content
    
    def _fix_punctuation(self, content: str) -> str:
        """Fix common punctuation issues"""
        try:
            fixed = content
            
            # Fix spacing around punctuation
            fixed = re.sub(r'\s+([.,!?])', r'\1', fixed)
            fixed = re.sub(r'([.,!?])([A-Za-z])', r'\1 \2', fixed)
            
            # Ensure proper capitalization
            sentences = fixed.split('. ')
            capitalized_sentences = []
            
            for sentence in sentences:
                if sentence and sentence[0].isalpha():
                    sentence = sentence[0].upper() + sentence[1:]
                capitalized_sentences.append(sentence)
            
            return '. '.join(capitalized_sentences)
            
        except Exception as e:
            logger.error(f"Punctuation fixing failed: {e}")
            return content
    
    def add_engagement_elements(self, content: str) -> str:
        """
        Add engagement elements to content
        
        Args:
            content: Content to enhance
            
        Returns:
            Content with engagement elements
        """
        try:
            enhanced_content = content
            
            # Add engaging question if missing
            if '?' not in enhanced_content:
                enhanced_content = self._add_engaging_question(enhanced_content)
            
            # Enhance with action words
            enhanced_content = self._enhance_with_action_words(enhanced_content)
            
            # Add attention-grabbing numbers
            enhanced_content = self._add_attention_grabbing_numbers(enhanced_content)
            
            return enhanced_content.strip()
            
        except Exception as e:
            logger.error(f"Engagement enhancement failed: {e}")
            return content
    
    def _add_engaging_question(self, content: str) -> str:
        """Add an engaging question to content"""
        try:
            # Simple question addition
            if not content.endswith('?'):
                return f"{content} What do you think?"
            
            return content
            
        except Exception as e:
            logger.error(f"Question addition failed: {e}")
            return content
    
    def _enhance_with_action_words(self, content: str) -> str:
        """Enhance content with action words"""
        try:
            action_words = [
                'discover', 'learn', 'explore', 'unlock', 'master',
                'achieve', 'transform', 'optimize', 'leverage', 'implement'
            ]
            
            # Check if content already has action words
            content_lower = content.lower()
            has_action_words = any(word in content_lower for word in action_words)
            
            if not has_action_words:
                # Add action word at beginning
                action_word = action_words[0]  # Use first action word
                return f"{action_word.title()} how {content.lower()}"
            
            return content
            
        except Exception as e:
            logger.error(f"Action word enhancement failed: {e}")
            return content
    
    def _add_attention_grabbing_numbers(self, content: str) -> str:
        """Add attention-grabbing numbers to content"""
        try:
            # Check if content already has numbers
            if re.search(r'\d+', content):
                return content
            
            # Add simple number
            return f"Here are 3 key insights: {content}"
            
        except Exception as e:
            logger.error(f"Number addition failed: {e}")
            return content
    
    def optimize_for_platform(self, content: str, platform: str = 'twitter') -> str:
        """
        Optimize content for specific platform
        
        Args:
            content: Content to optimize
            platform: Target platform (twitter, linkedin, facebook)
            
        Returns:
            Platform-optimized content
        """
        try:
            platform_config = self.platform_optimizations.get(platform, 
                                                            self.platform_optimizations['twitter'])
            
            if platform == 'twitter':
                return self._optimize_for_twitter(content, platform_config)
            elif platform == 'linkedin':
                return self._optimize_for_linkedin(content, platform_config)
            elif platform == 'facebook':
                return self._optimize_for_facebook(content, platform_config)
            else:
                return content
                
        except Exception as e:
            logger.error(f"Platform optimization failed: {e}")
            return content
    
    def _optimize_for_twitter(self, content: str, config: Dict[str, Any]) -> str:
        """Optimize content for Twitter"""
        try:
            optimized = content
            
            # Ensure optimal length
            if len(optimized) > config['preferred_length']:
                optimized = self._shorten_content(optimized, config['preferred_length'])
            
            # Make it scannable
            optimized = self._make_scannable(optimized)
            
            return optimized
            
        except Exception as e:
            logger.error(f"Twitter optimization failed: {e}")
            return content
    
    def _optimize_for_linkedin(self, content: str, config: Dict[str, Any]) -> str:
        """Optimize content for LinkedIn"""
        try:
            optimized = content
            
            # Add professional tone
            optimized = self._add_professional_tone(optimized)
            
            # Add industry context
            optimized = self._add_industry_context(optimized)
            
            return optimized
            
        except Exception as e:
            logger.error(f"LinkedIn optimization failed: {e}")
            return content
    
    def _optimize_for_facebook(self, content: str, config: Dict[str, Any]) -> str:
        """Optimize content for Facebook"""
        try:
            optimized = content
            
            # Add personal touch
            optimized = self._add_personal_touch(optimized)
            
            # Add emotional elements
            optimized = self._add_emotional_elements(optimized)
            
            return optimized
            
        except Exception as e:
            logger.error(f"Facebook optimization failed: {e}")
            return content
    
    def _shorten_content(self, content: str, max_length: int) -> str:
        """Shorten content to fit within character limit"""
        try:
            if len(content) <= max_length:
                return content
            
            # Try to shorten by removing less important parts
            sentences = content.split('.')
            shortened = []
            current_length = 0
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                if current_length + len(sentence) + 1 <= max_length:
                    shortened.append(sentence)
                    current_length += len(sentence) + 1
                else:
                    break
            
            return '. '.join(shortened).strip()
            
        except Exception as e:
            logger.error(f"Content shortening failed: {e}")
            return content[:max_length] if len(content) > max_length else content
    
    def _make_scannable(self, content: str) -> str:
        """Make content more scannable"""
        try:
            # Add line breaks for key points
            sentences = content.split('.')
            scannable = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and len(sentence.split()) > 8:
                    scannable.append(f"• {sentence}")
                else:
                    scannable.append(sentence)
            
            return '\n'.join(scannable)
            
        except Exception as e:
            logger.error(f"Scannable formatting failed: {e}")
            return content
    
    def _add_professional_tone(self, content: str) -> str:
        """Add professional tone to content"""
        try:
            # Simple professional enhancements
            if not content.endswith('.'):
                content += '.'
            
            return content
            
        except Exception as e:
            logger.error(f"Professional tone addition failed: {e}")
            return content
    
    def _add_industry_context(self, content: str) -> str:
        """Add industry context to content"""
        try:
            # Simple industry context addition
            return content
            
        except Exception as e:
            logger.error(f"Industry context addition failed: {e}")
            return content
    
    def _add_personal_touch(self, content: str) -> str:
        """Add personal touch to content"""
        try:
            # Simple personal touch
            return content
            
        except Exception as e:
            logger.error(f"Personal touch addition failed: {e}")
            return content
    
    def _add_emotional_elements(self, content: str) -> str:
        """Add emotional elements to content"""
        try:
            # Simple emotional enhancement
            return content
            
        except Exception as e:
            logger.error(f"Emotional elements addition failed: {e}")
            return content
    
    def enhance_for_seo_score(self, content: str, target_score: float = 0.8) -> str:
        """
        Enhance content for better SEO score
        
        Args:
            content: Content to enhance
            target_score: Target SEO score (0-1)
            
        Returns:
            SEO-enhanced content
        """
        try:
            enhanced_content = content
            
            # Estimate current SEO score
            current_score = self._estimate_seo_score(enhanced_content)
            
            # Enhance if below target
            if current_score < target_score:
                enhanced_content = self._add_structural_improvements(enhanced_content)
            
            return enhanced_content.strip()
            
        except Exception as e:
            logger.error(f"SEO enhancement failed: {e}")
            return content
    
    def _estimate_seo_score(self, content: str) -> float:
        """Estimate SEO score of content"""
        try:
            score = 0.0
            
            # Length score
            if 100 <= len(content) <= 300:
                score += 0.2
            elif 300 < len(content) <= 1000:
                score += 0.3
            else:
                score += 0.1
            
            # Structure score
            sentences = content.split('.')
            if 3 <= len(sentences) <= 10:
                score += 0.2
            else:
                score += 0.1
            
            # Readability score
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
            if avg_sentence_length <= 20:
                score += 0.2
            else:
                score += 0.1
            
            # Engagement score
            if '?' in content or any(word in content.lower() for word in ['you', 'your', 'we']):
                score += 0.2
            else:
                score += 0.1
            
            # Call-to-action score
            if any(cta in content.lower() for cta in ['learn', 'discover', 'try', 'get']):
                score += 0.1
            else:
                score += 0.05
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"SEO score estimation failed: {e}")
            return 0.5
    
    def _add_structural_improvements(self, content: str) -> str:
        """Add structural improvements for SEO"""
        try:
            improved = content
            
            # Ensure proper capitalization
            if improved and improved[0].isalpha():
                improved = improved[0].upper() + improved[1:]
            
            # Add call-to-action if missing
            if not any(cta in improved.lower() for cta in ['learn', 'discover', 'try', 'get']):
                improved += " Learn more about this topic."
            
            return improved
            
        except Exception as e:
            logger.error(f"Structural improvements failed: {e}")
            return content
