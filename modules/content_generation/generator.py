"""Main content generation orchestrator"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime

from .models import (
    ContentDraft, ContentType, ContentGenerationRequest, 
    ContentGenerationContext, ContentQualityScore
)
from .llm_adapter import LLMAdapter, LLMAdapterFactory
from .prompts import PromptEngine
from .content_types import ContentTypeFactory
from .quality_checker import ContentQualityChecker

logger = logging.getLogger(__name__)

class ContentGenerator:
    """Streamlined content generator focused on content creation"""
    
    def __init__(self, llm_adapter: LLMAdapter, quality_checker=None, prompt_engine=None):
        """
        Initialize content generator
        
        Args:
            llm_adapter: LLM adapter for content generation
            quality_checker: Optional quality checker
            prompt_engine: Optional prompt engine
        """
        self.llm_adapter = llm_adapter
        self.quality_checker = quality_checker or ContentQualityChecker()
        self.prompt_engine = prompt_engine or PromptEngine()
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
    
    async def generate_content(self, request: ContentGenerationRequest, 
                             context: ContentGenerationContext) -> List[ContentDraft]:
        """Generate content based on request and context"""
        
        try:
            drafts = []
            
            for i in range(request.quantity):
                # Build prompt
                prompt = self._build_prompt(request, context)
                
                # Generate content using LLM
                raw_content = await self.llm_adapter.generate_content(prompt)
                
                # Clean the generated content
                cleaned_content = self._clean_generated_content(raw_content, request.content_type)
                
                # Assess quality
                if self.quality_checker:
                    # Create a temporary draft for quality assessment
                    temp_draft = ContentDraft(
                        founder_id=request.founder_id,
                        content_type=request.content_type,
                        generated_text=cleaned_content,
                        quality_score=0.0  # Will be updated
                    )
                    
                    # Use the async assess_quality method
                    quality_assessment = await self.quality_checker.assess_quality(temp_draft, context)
                    quality_score = quality_assessment.overall_score
                    
                    # Store detailed quality metrics for later use
                    quality_metadata = {
                        "overall_score": quality_assessment.overall_score,
                        "engagement_prediction": quality_assessment.engagement_prediction,
                        "brand_alignment": quality_assessment.brand_alignment,
                        "trend_relevance": quality_assessment.trend_relevance,
                        "readability": quality_assessment.readability,
                        "issues": quality_assessment.issues,
                        "suggestions": quality_assessment.suggestions
                    }
                else:
                    # Fallback to basic quality assessment
                    quality_score = self._basic_quality_assessment(cleaned_content, request.content_type)
                    quality_metadata = {"fallback_assessment": True}
                
                # Skip if below quality threshold
                if quality_score < request.quality_threshold:
                    self.logger.info(f"Draft {i+1} below quality threshold ({quality_score:.2f})")
                    continue
                
                # Create final draft with all metadata
                draft = ContentDraft(
                    founder_id=request.founder_id,
                    content_type=request.content_type,
                    generated_text=cleaned_content,
                    quality_score=quality_score,
                    generation_metadata={
                        'prompt_used': prompt[:200] + '...' if len(prompt) > 200 else prompt,
                        'generation_attempt': i + 1,
                        'llm_provider': self.llm_adapter.__class__.__name__,
                        'quality_assessment': quality_metadata
                    }
                )
                
                drafts.append(draft)
            
            return drafts
            
        except Exception as e:
            self.logger.error(f"Content generation failed: {e}")
            raise
    
    def _clean_generated_content(self, raw_content: str, content_type: ContentType) -> str:
        """Clean and format generated content"""
        if not raw_content:
            return ""
        
        # Remove common LLM artifacts
        cleaned = raw_content.content.strip()
        
        # Remove quotes that LLMs often add
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
        elif cleaned.startswith("'") and cleaned.endswith("'"):
            cleaned = cleaned[1:-1]
        
        # Remove "Tweet:" or similar prefixes
        prefixes_to_remove = [
            "Tweet:", "Reply:", "Thread:", "Quote Tweet:",
            "Here's a tweet:", "Here's a reply:", "Tweet content:",
            "Content:", "Post:"
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
        
        # Clean up extra whitespace
        cleaned = ' '.join(cleaned.split())
        
        # Ensure proper hashtag formatting
        import re
        cleaned = re.sub(r'\s+#', ' #', cleaned)  # Ensure space before hashtags
        cleaned = re.sub(r'#\s+', '#', cleaned)   # Remove space after hashtag symbol
        
        return cleaned
    
    def _build_prompt(self, request: ContentGenerationRequest, 
                     context: ContentGenerationContext) -> str:
        """Build generation prompt based on request and context"""
        
        # Use prompt engine if available
        if self.prompt_engine:
            return self.prompt_engine.generate_prompt(request, context)
        
        # Fallback to basic prompt building
        prompt_parts = []
        
        # Base instruction
        prompt_parts.append(f"Generate a {request.content_type} for a founder.")
        
        # Add product context
        if context.product_info:
            product_name = context.product_info.get('name', 'the product')
            prompt_parts.append(f"The product is {product_name}.")
            
            if 'description' in context.product_info:
                prompt_parts.append(f"Product description: {context.product_info['description']}")
        
        # Add trend context
        if context.trend_info:
            trend_topic = context.trend_info.get('topic', 'current trends')
            prompt_parts.append(f"This should relate to the trending topic: {trend_topic}")
        
        # Add brand voice
        if context.brand_voice:
            prompt_parts.append(f"Use a {context.brand_voice.tone} tone with {context.brand_voice.style} style.")
        
        # Add generation mode specific instructions
        if request.generation_mode:
            mode_instructions = {
                'viral_focused': "Make it engaging and shareable, likely to go viral.",
                'brand_focused': "Focus on brand messaging and values.",
                'trend_based': "Capitalize on current trends and topics.",
                'engagement_optimized': "Optimize for maximum engagement and interaction."
            }
            
            if request.generation_mode in mode_instructions:
                prompt_parts.append(mode_instructions[request.generation_mode])
        
        # Add custom prompt if provided
        if request.custom_prompt:
            prompt_parts.append(f"Additional requirements: {request.custom_prompt}")
        
        # Content type specific instructions
        if request.content_type == ContentType.TWEET:
            prompt_parts.append("Keep it under 280 characters.")
        elif request.content_type == ContentType.REPLY:
            prompt_parts.append("Make it conversational and engaging as a reply.")
        elif request.content_type == ContentType.THREAD:
            prompt_parts.append("This is part of a thread, make it coherent and flowing.")
        
        return " ".join(prompt_parts)
    
    def _basic_quality_assessment(self, content: str, content_type: ContentType) -> float:
        """Basic quality assessment when quality checker is not available"""
        score = 0.5  # Base score
        
        # Length assessment
        if content_type == ContentType.TWEET:
            if 50 <= len(content) <= 280:
                score += 0.2
            elif len(content) > 280:
                score -= 0.3
        
        # Check for basic engagement elements
        if '?' in content:  # Questions
            score += 0.1
        if any(word in content.lower() for word in ['you', 'your', 'we', 'us']):  # Personal touch
            score += 0.1
        if '#' in content:  # Hashtags
            score += 0.1
        
        return min(1.0, max(0.0, score))

class ContentGenerationFactory:
    """Factory for creating content generators"""
    
    @staticmethod
    def create_generator(llm_provider: str, llm_config: Dict[str, Any],
                        quality_checker=None, prompt_engine=None) -> ContentGenerator:
        """Create a content generator with specified LLM provider"""
        
        # Create LLM adapter
        llm_adapter = LLMAdapterFactory.create_adapter(llm_provider=llm_provider, **llm_config)
        
        # Create and return generator
        return ContentGenerator(
            llm_adapter=llm_adapter,
            quality_checker=quality_checker,
            prompt_engine=prompt_engine
        )
    
    @staticmethod
    def create_basic_generator(llm_provider: str, llm_config: Dict[str, Any]) -> ContentGenerator:
        """Create a basic content generator with default components"""
        return ContentGenerationFactory.create_generator(
            llm_provider=llm_provider,
            llm_config=llm_config
        )