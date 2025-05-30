"""Content type definitions and factories"""
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import re

from .models import ContentType, ContentDraft, SEOSuggestions

class BaseContent(ABC):
    """Base class for content types"""
    
    def __init__(self, content_type: ContentType):
        self.content_type = content_type
        self.seo_optimizer = None  # Will be injected during initialization
    
    def set_seo_optimizer(self, seo_optimizer):
        """Inject SEO optimizer"""
        self.seo_optimizer = seo_optimizer
    
    @abstractmethod
    def validate_content(self, text: str) -> tuple[bool, List[str]]:
        """Validate content format and constraints"""
        pass
    
    @abstractmethod
    def optimize_for_platform(self, text: str, seo_suggestions: SEOSuggestions) -> str:
        """Optimize content for the platform"""
        pass
    
    @abstractmethod
    def get_character_limit(self) -> int:
        """Get character limit for this content type"""
        pass
    
    def _apply_seo_optimization(self, text: str, context: Dict[str, Any] = None) -> tuple[str, SEOSuggestions]:
        """Apply SEO optimization if available"""
        if self.seo_optimizer:
            try:
                # Use SEO module for optimization
                optimized_text = self.seo_optimizer.optimize_content(
                    text, 
                    content_type=self.content_type,
                    context=context or {}
                )
                
                # Get SEO suggestions
                seo_suggestions = self.seo_optimizer.generate_suggestions(
                    text,
                    content_type=self.content_type,
                    context=context or {}
                )
                
                return optimized_text, seo_suggestions
            except Exception as e:
                # If SEO optimization fails, return original text and empty suggestions
                return text, SEOSuggestions()
        
        # If no SEO optimizer available, return original text and empty suggestions
        return text, SEOSuggestions()

class TweetContent(BaseContent):
    """Single tweet content handler"""
    
    def __init__(self):
        super().__init__(ContentType.TWEET)
    
    def validate_content(self, text: str) -> tuple[bool, List[str]]:
        """Validate tweet content"""
        issues = []
        
        if len(text) > 280:
            issues.append(f"Tweet exceeds 280 characters ({len(text)} chars)")
        
        if len(text.strip()) == 0:
            issues.append("Tweet cannot be empty")
        
        # Check for potential issues
        if text.count('#') > 5:
            issues.append("Too many hashtags (max 5 recommended)")
        
        if text.count('@') > 3:
            issues.append("Too many mentions (max 3 recommended)")
        
        # Check for URLs (count as 23 chars on Twitter)
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        if urls:
            # Recalculate length with URL shortening
            actual_length = len(text)
            for url in urls:
                actual_length = actual_length - len(url) + 23
            if actual_length > 280:
                issues.append(f"Tweet with shortened URLs exceeds 280 characters ({actual_length} chars)")
        
        return len(issues) == 0, issues
    
    def optimize_for_platform(self, text: str, seo_suggestions: SEOSuggestions = None, 
                            context: Dict[str, Any] = None) -> str:
        """Optimize tweet for Twitter platform"""
        # First apply SEO optimization
        if context:
            optimized_text, enhanced_seo = self._apply_seo_optimization(text, context)
            # If SEO module provides better suggestions, use them
            if enhanced_seo.hashtags or enhanced_seo.keywords:
                seo_suggestions = enhanced_seo
        else:
            optimized_text = text
        
        optimized = optimized_text.strip()
        
        # Add hashtags if space allows and SEO suggestions are provided
        if seo_suggestions and seo_suggestions.hashtags:
            # Use hashtags suggested by SEO module
            hashtag_text = " " + " ".join(f"#{tag}" for tag in seo_suggestions.hashtags[:3])
            if len(optimized + hashtag_text) <= 280:
                optimized += hashtag_text
        
        # Apply keyword optimization if SEO module provides it
        if seo_suggestions and seo_suggestions.keywords:
            optimized = self._integrate_keywords(optimized, seo_suggestions.keywords)
        
        # Ensure proper spacing around hashtags and mentions
        optimized = re.sub(r'(\w)#', r'\1 #', optimized)
        optimized = re.sub(r'(\w)@', r'\1 @', optimized)
        
        return optimized
    
    def _integrate_keywords(self, text: str, keywords: List[str]) -> str:
        """Intelligently integrate keywords into text"""
        # This can implement more intelligent keyword integration logic
        # Currently just checks if keywords already exist
        for keyword in keywords[:2]:  # Limit number of keywords
            if keyword.lower() not in text.lower() and len(text + f" {keyword}") <= 260:
                # Leave space for hashtags
                text = f"{text} {keyword}"
        return text
    
    def get_character_limit(self) -> int:
        return 280

class ReplyContent(BaseContent):
    """Reply tweet content handler"""
    
    def __init__(self):
        super().__init__(ContentType.REPLY)
        self.mentions_required = True
    
    def validate_content(self, text: str) -> tuple[bool, List[str]]:
        """Validate reply content"""
        issues = []
        
        if len(text) > 280:
            issues.append(f"Reply exceeds 280 characters ({len(text)} chars)")
        
        if len(text.strip()) == 0:
            issues.append("Reply cannot be empty")
        
        # Check if it looks like a reply (should be conversational)
        conversational_words = ['thanks', 'agree', 'interesting', 'great', 'exactly', 'however', 'but', 'yes', 'no']
        if not any(word in text.lower() for word in conversational_words):
            issues.append("Reply should be more conversational")
        
        return len(issues) == 0, issues
    
    def optimize_for_platform(self, text: str, seo_suggestions: SEOSuggestions = None,
                            context: Dict[str, Any] = None) -> str:
        """Optimize reply for engagement"""
        # Apply SEO optimization
        if context:
            optimized_text, enhanced_seo = self._apply_seo_optimization(text, context)
            if enhanced_seo.hashtags:
                seo_suggestions = enhanced_seo
        else:
            optimized_text = text
        
        optimized = optimized_text.strip()
        
        # Add relevant hashtags sparingly for replies (replies usually don't need many hashtags)
        if seo_suggestions and seo_suggestions.hashtags:
            # Only add the most relevant hashtag
            hashtag_text = f" #{seo_suggestions.hashtags[0]}"
            if len(optimized + hashtag_text) <= 280:
                optimized += hashtag_text
        
        return optimized
    
    def get_character_limit(self) -> int:
        return 280

class ThreadContent(BaseContent):
    """Thread content handler"""
    
    def __init__(self):
        super().__init__(ContentType.THREAD)
        self.max_thread_length = 10
    
    def validate_content(self, text: str) -> tuple[bool, List[str]]:
        """Validate thread content"""
        issues = []
        
        # Split into thread parts
        parts = self._split_into_thread_parts(text)
        
        if len(parts) > self.max_thread_length:
            issues.append(f"Thread too long ({len(parts)} tweets, max {self.max_thread_length})")
        
        # Validate each part
        for i, part in enumerate(parts):
            if len(part) > 280:
                issues.append(f"Thread part {i+1} exceeds 280 characters ({len(part)} chars)")
        
        return len(issues) == 0, issues
    
    def optimize_for_platform(self, text: str, seo_suggestions: SEOSuggestions = None,
                            context: Dict[str, Any] = None) -> str:
        """Optimize thread for readability"""
        # Apply SEO optimization
        if context:
            optimized_text, enhanced_seo = self._apply_seo_optimization(text, context)
            if enhanced_seo.hashtags or enhanced_seo.keywords:
                seo_suggestions = enhanced_seo
        else:
            optimized_text = text
        
        parts = self._split_into_thread_parts(optimized_text)
        optimized_parts = []
        
        for i, part in enumerate(parts):
            # Add thread numbering
            if len(parts) > 1:
                thread_num = f"{i+1}/{len(parts)} "
                part = thread_num + part
            
            # Add hashtags to first tweet only (SEO best practice)
            if i == 0 and seo_suggestions and seo_suggestions.hashtags:
                hashtag_text = " " + " ".join(f"#{tag}" for tag in seo_suggestions.hashtags[:2])
                if len(part + hashtag_text) <= 280:
                    part += hashtag_text
            
            # Add CTA to last tweet if SEO module suggests it
            if i == len(parts) - 1 and seo_suggestions and hasattr(seo_suggestions, 'call_to_action'):
                if seo_suggestions.call_to_action and len(part + f" {seo_suggestions.call_to_action}") <= 280:
                    part += f" {seo_suggestions.call_to_action}"
            
            optimized_parts.append(part)
        
        return "\n\n".join(optimized_parts)
    
    def get_character_limit(self) -> int:
        return 280 * self.max_thread_length
    
    def _split_into_thread_parts(self, text: str) -> List[str]:
        """Split long text into thread parts"""
        # Simple splitting by sentences or paragraphs
        paragraphs = text.split('\n\n')
        parts = []
        current_part = ""
        
        for paragraph in paragraphs:
            if len(current_part + paragraph) <= 250:  # Leave room for thread numbering
                current_part += paragraph + "\n\n"
            else:
                if current_part:
                    parts.append(current_part.strip())
                current_part = paragraph + "\n\n"
        
        if current_part:
            parts.append(current_part.strip())
        
        return parts

class ContentTypeFactory:
    """Factory for creating content type handlers"""
    
    _handlers = {
        ContentType.TWEET: TweetContent,
        ContentType.REPLY: ReplyContent,
        ContentType.THREAD: ThreadContent,
        ContentType.QUOTE_TWEET: TweetContent,  # Same as regular tweet for now
    }
    
    @classmethod
    def create_handler(cls, content_type: ContentType, seo_optimizer=None) -> BaseContent:
        """Create content handler for specified type"""
        handler_class = cls._handlers.get(content_type)
        if not handler_class:
            raise ValueError(f"Unsupported content type: {content_type}")
        
        handler = handler_class()
        
        # Inject SEO optimizer
        if seo_optimizer:
            handler.set_seo_optimizer(seo_optimizer)
        
        return handler
    
    @classmethod
    def validate_and_optimize(cls, draft: ContentDraft, context: Dict[str, Any] = None,
                            seo_optimizer=None) -> tuple[bool, List[str], str]:
        """Validate and optimize content draft"""
        handler = cls.create_handler(draft.content_type, seo_optimizer)
        
        # Validate
        is_valid, issues = handler.validate_content(draft.generated_text)
        
        # Optimize if valid
        optimized_text = draft.generated_text
        if is_valid:
            optimized_text = handler.optimize_for_platform(
                draft.generated_text, 
                draft.seo_suggestions,
                context
            )
        
        return is_valid, issues, optimized_text