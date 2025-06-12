"""Content type specific processing and optimization"""
from typing import Dict, Any, List, Tuple
import re

from .models import ContentType, ContentDraft

class BaseContentProcessor:
    """Base class for content type processors"""
    
    def __init__(self):
        pass
    
    def validate_content(self, text: str, context: Dict[str, Any] = None) -> Tuple[bool, List[str]]:
        """Validate content for the specific platform"""
        issues = []
        
        # Basic validation
        if not text.strip():
            issues.append("Content is empty")
        
        return len(issues) == 0, issues
    
    def optimize_for_platform(self, text: str, context: Dict[str, Any] = None) -> str:
        """Optimize content for the specific platform"""
        # Basic optimization - just clean up whitespace
        optimized = ' '.join(text.split())
        
        # Ensure proper hashtag formatting
        optimized = re.sub(r'\s+#', ' #', optimized)  # Ensure space before hashtags
        optimized = re.sub(r'#\s+', '#', optimized)   # Remove space after hashtag symbol
        
        return optimized

class TweetContent(BaseContentProcessor):
    """Twitter-specific content processing"""
    
    def validate_content(self, text: str, context: Dict[str, Any] = None) -> Tuple[bool, List[str]]:
        """Validate tweet content"""
        issues = []
        
        # Length validation
        if len(text) > 280:
            issues.append(f"Tweet exceeds 280 characters ({len(text)}/280)")
        
        # Hashtag count validation
        hashtags = re.findall(r'#\w+', text)
        if len(hashtags) > 5:
            issues.append("Too many hashtags (max 5 recommended)")
        
        # Mention validation
        mentions = re.findall(r'@\w+', text)
        if len(mentions) > 10:
            issues.append("Too many mentions")
        
        return len(issues) == 0, issues
    
    def optimize_for_platform(self, text: str, context: Dict[str, Any] = None) -> str:
        """Optimize content for Twitter"""
        # Apply base optimization first
        optimized = super().optimize_for_platform(text, context)
        
        # Twitter-specific optimizations
        # Ensure proper length
        if len(optimized) > 280:
            # Intelligent truncation
            sentences = optimized.split('. ')
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence + '. ') <= 275:
                    truncated += sentence + '. '
                else:
                    break
            
            if truncated:
                optimized = truncated.rstrip('. ') + '...'
            else:
                optimized = optimized[:277] + '...'
        
        # Ensure proper spacing around hashtags and mentions
        optimized = re.sub(r'(\w)#', r'\1 #', optimized)
        optimized = re.sub(r'(\w)@', r'\1 @', optimized)
        
        return optimized

class ReplyContent(BaseContentProcessor):
    """Reply-specific content processing"""
    
    def validate_content(self, text: str, context: Dict[str, Any] = None) -> Tuple[bool, List[str]]:
        """Validate reply content"""
        issues = []
        
        # Length validation
        if len(text) > 280:
            issues.append(f"Reply exceeds 280 characters ({len(text)}/280)")
        
        # Conversational elements check
        conversational_words = ['thanks', 'thank you', 'great', 'good', 'interesting', 'agree', 'exactly']
        if not any(word in text.lower() for word in conversational_words):
            issues.append("Reply lacks conversational elements")
        
        return len(issues) == 0, issues
    
    def optimize_for_platform(self, text: str, context: Dict[str, Any] = None) -> str:
        """Optimize content for replies"""
        # Apply base optimization
        optimized = super().optimize_for_platform(text, context)
        
        # Reply-specific optimizations
        # Ensure length compliance
        if len(optimized) > 280:
            optimized = optimized[:277] + '...'
        
        return optimized

class ThreadContent(BaseContentProcessor):
    """Thread-specific content processing"""
    
    def validate_content(self, text: str, context: Dict[str, Any] = None) -> Tuple[bool, List[str]]:
        """Validate thread content"""
        issues = []
        
        # Length validation for individual thread post
        if len(text) > 280:
            issues.append(f"Thread post exceeds 280 characters ({len(text)}/280)")
        
        # Thread structure validation
        if not re.search(r'\d+/', text) and 'thread' not in text.lower():
            issues.append("Thread post should indicate thread structure (e.g., 1/n)")
        
        return len(issues) == 0, issues
    
    def optimize_for_platform(self, text: str, context: Dict[str, Any] = None) -> str:
        """Optimize content for threads"""
        # Apply base optimization
        optimized = super().optimize_for_platform(text, context)
        
        # Thread-specific optimizations
        # Ensure length compliance
        if len(optimized) > 280:
            optimized = optimized[:277] + '...'
        
        return optimized

class ContentTypeFactory:
    """Factory for creating content type processors"""
    
    _processors = {
        ContentType.TWEET: TweetContent,
        ContentType.REPLY: ReplyContent,
        ContentType.THREAD: ThreadContent,
        ContentType.QUOTE_TWEET: TweetContent,  # Use tweet processor for quote tweets
    }
    
    @classmethod
    def get_processor(cls, content_type: ContentType) -> BaseContentProcessor:
        """Get appropriate processor for content type"""
        processor_class = cls._processors.get(content_type, BaseContentProcessor)
        return processor_class()
    
    @classmethod
    def validate_and_optimize(cls, draft: ContentDraft, context: Dict[str, Any] = None) -> Tuple[bool, List[str], str]:
        """Validate and optimize content draft"""
        processor = cls.get_processor(draft.content_type)
        
        # Validate content
        is_valid, issues = processor.validate_content(draft.generated_text, context)
        
        # Optimize content
        optimized_text = processor.optimize_for_platform(draft.generated_text, context)
        
        return is_valid, issues, optimized_text