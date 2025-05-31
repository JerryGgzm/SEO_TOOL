"""Simple LLM client for content generation and SEO optimization"""
import openai
from typing import Dict, Any, Optional, List
import logging
import asyncio

logger = logging.getLogger(__name__)

class LLMClient:
    """Simple LLM client wrapper"""
    
    def __init__(self, provider: str = 'openai', api_key: str = None, model_name: str = 'gpt-3.5-turbo'):
        self.provider = provider
        self.api_key = api_key
        self.model_name = model_name
        
        if provider == 'openai' and api_key:
            openai.api_key = api_key
    
    async def generate_response(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate response from LLM"""
        try:
            if self.provider == 'openai' and self.api_key:
                response = await openai.ChatCompletion.acreate(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            else:
                return "Mock LLM response for demo"
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return "Fallback response"
    
    async def chat(self, messages: List[Dict[str, str]], max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Chat completion method for compatibility"""
        try:
            if self.provider == 'openai' and self.api_key:
                response = await openai.ChatCompletion.acreate(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content
            else:
                # Mock response based on last message
                last_message = messages[-1].get('content', '') if messages else ''
                return f"Mock response to: {last_message[:50]}..."
        except Exception as e:
            logger.error(f"LLM chat failed: {e}")
            return "Fallback chat response"
    
    def is_available(self) -> bool:
        """Check if LLM client is properly configured"""
        return self.api_key is not None
    
    # Additional compatibility methods
    async def complete(self, prompt: str, **kwargs) -> str:
        """Text completion method for compatibility"""
        return await self.generate_response(prompt, kwargs.get('max_tokens', 500))
    
    async def analyze(self, content: str, analysis_type: str = 'general') -> Dict[str, Any]:
        """Content analysis method for SEO integration"""
        try:
            prompt = f"Analyze this content for {analysis_type}: {content}"
            response = await self.generate_response(prompt, 300)
            
            # Return structured analysis
            return {
                'analysis': response,
                'score': 0.7,  # Mock score
                'recommendations': ['Improve engagement', 'Add hashtags', 'Use keywords'],
                'analysis_type': analysis_type
            }
        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            return {
                'analysis': 'Analysis failed',
                'score': 0.5,
                'recommendations': [],
                'error': str(e)
            } 