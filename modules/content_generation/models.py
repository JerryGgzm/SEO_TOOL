"""Content generation data models"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum
import uuid

class ContentType(str, Enum):
    """Content types supported"""
    TWEET = "tweet"
    REPLY = "reply" 
    QUOTE_TWEET = "quote_tweet"
    THREAD = "thread"

class GenerationMode(str, Enum):
    """Content generation modes"""
    STANDARD = "standard"
    VIRAL_FOCUSED = "viral_focused"
    BRAND_FOCUSED = "brand_focused"
    TREND_BASED = "trend_based"
    ENGAGEMENT_OPTIMIZED = "engagement_optimized"

class BrandVoice(BaseModel):
    """Brand voice configuration"""
    tone: str = Field(default="professional", description="Content tone")
    style: str = Field(default="informative", description="Writing style")
    personality_traits: List[str] = Field(default=[], description="Brand personality")
    avoid_words: List[str] = Field(default=[], description="Words to avoid")
    preferred_phrases: List[str] = Field(default=[], description="Preferred expressions")
    formality_level: float = Field(default=0.5, ge=0, le=1, description="0=casual, 1=formal")

class ContentGenerationContext(BaseModel):
    """Context for content generation"""
    trend_info: Optional[Dict[str, Any]] = Field(None, description="Related trend data")
    product_info: Dict[str, Any] = Field(default={}, description="Product information")
    brand_voice: BrandVoice = Field(default_factory=BrandVoice)
    recent_content: List[str] = Field(default=[], description="Recent posts to avoid repetition")
    successful_patterns: List[Dict[str, Any]] = Field(default=[], description="High-performing content patterns")
    target_audience: Optional[str] = Field(None, description="Target audience description")
    content_preferences: Dict[str, Any] = Field(default={}, description="Content generation preferences")

class ContentQualityScore(BaseModel):
    """Content quality assessment"""
    overall_score: float = Field(..., ge=0, le=1, description="Overall quality score")
    engagement_prediction: float = Field(..., ge=0, le=1, description="Predicted engagement")
    brand_alignment: float = Field(..., ge=0, le=1, description="Brand voice alignment")
    trend_relevance: float = Field(..., ge=0, le=1, description="Relevance to trend")
    readability: float = Field(..., ge=0, le=1, description="Content readability")
    issues: List[str] = Field(default=[], description="Identified issues")
    suggestions: List[str] = Field(default=[], description="Improvement suggestions")

class ContentDraft(BaseModel):
    """Generated content draft"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    founder_id: str = Field(..., description="Founder ID")
    content_type: ContentType = Field(..., description="Type of content")
    generated_text: str = Field(..., description="Generated content text")
    quality_score: float = Field(default=0.0, ge=0, le=1, description="Quality assessment score")
    generation_metadata: Dict[str, Any] = Field(default={}, description="Generation metadata")
    created_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('generated_text')
    @classmethod
    def validate_content_length(cls, v: str, info) -> str:
        """Validate content length based on content type"""
        # Clean the content first - remove quotes and extra whitespace
        cleaned_content = v.strip().strip('"').strip("'").strip()
        
        # Get content type from the model instance
        content_type = info.data.get('content_type') if info.data else None
        
        if content_type == ContentType.TWEET:
            if len(cleaned_content) > 280:
                # Truncate to 280 characters, preserving hashtags if possible
                if '#' in cleaned_content:
                    # Try to preserve hashtags
                    parts = cleaned_content.split('#')
                    main_content = parts[0].strip()
                    hashtags = ['#' + part.split()[0] for part in parts[1:] if part.strip()]
                    
                    # Calculate space needed for hashtags
                    hashtag_text = ' ' + ' '.join(hashtags) if hashtags else ''
                    available_space = 280 - len(hashtag_text)
                    
                    if available_space > 50:  # Ensure minimum content length
                        truncated_main = main_content[:available_space].strip()
                        # Remove incomplete words at the end
                        if not truncated_main.endswith('.') and ' ' in truncated_main:
                            truncated_main = truncated_main.rsplit(' ', 1)[0]
                        cleaned_content = truncated_main + hashtag_text
                    else:
                        # If hashtags take too much space, just truncate everything
                        cleaned_content = cleaned_content[:277] + '...'
                else:
                    # No hashtags, simple truncation
                    cleaned_content = cleaned_content[:277] + '...'
        
        elif content_type == ContentType.REPLY:
            if len(cleaned_content) > 280:
                cleaned_content = cleaned_content[:277] + '...'
        
        return cleaned_content

class ContentGenerationRequest(BaseModel):
    """Request for content generation"""
    founder_id: str = Field(..., description="Founder ID")
    content_type: ContentType = Field(..., description="Type of content to generate")
    generation_mode: GenerationMode = Field(default=GenerationMode.STANDARD, description="Generation mode")
    trend_id: Optional[str] = Field(None, description="Specific trend to base content on")
    source_tweet_id: Optional[str] = Field(None, description="Tweet to reply to")
    custom_prompt: Optional[str] = Field(None, description="Custom generation prompt")
    quantity: int = Field(default=1, ge=1, le=10, description="Number of variations to generate")
    quality_threshold: float = Field(default=0.6, ge=0, le=1, description="Minimum quality score")

class LLMResponse(BaseModel):
    """Response from LLM"""
    content: str = Field(..., description="Generated content")
    confidence: float = Field(..., ge=0, le=1, description="Generation confidence")
    reasoning: Optional[str] = Field(None, description="Generation reasoning")
    alternatives: List[str] = Field(default=[], description="Alternative versions")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")

class PromptTemplate(BaseModel):
    """Prompt template for content generation"""
    name: str = Field(..., description="Template name")
    template: str = Field(..., description="Prompt template with placeholders")
    variables: List[str] = Field(..., description="Required template variables")
    content_type: ContentType = Field(..., description="Content type this template is for")
    description: Optional[str] = Field(None, description="Template description")