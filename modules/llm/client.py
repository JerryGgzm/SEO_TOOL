"""Simple LLM client for content generation and SEO optimization"""
import openai
import google.generativeai as genai
from typing import Dict, Any, Optional, List
import logging
import asyncio

logger = logging.getLogger(__name__)

class LLMClient:
    """Simple LLM client wrapper"""
    
    def __init__(self, provider: str = 'openai', api_key: str = None, model_name: str = 'gpt-3.5-turbo'):
        self.provider = provider.lower()
        self.api_key = api_key
        self.model_name = model_name
        
        self.openai_client = None
        self.gemini_model = None

        if self.provider == 'openai' and self.api_key:
            self.openai_client = openai.AsyncOpenAI(api_key=self.api_key)
        elif self.provider == 'gemini' and self.api_key:
            genai.configure(api_key=self.api_key)
            self.gemini_model = genai.GenerativeModel(self.model_name)
    
    async def generate_response(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate response from LLM"""
        # This method can be deprecated in favor of the more flexible `chat` method.
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages=messages, max_tokens=max_tokens)
    
    async def chat(self, messages: List[Dict[str, str]], max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Chat completion method for compatibility"""
        try:
            if self.provider == 'openai' and self.openai_client:
                # New openai v1.0.0+ syntax
                response = await self.openai_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content
            elif self.provider == 'gemini' and self.api_key:
                # Gemini uses a different message format, but for simple user prompts, this is fine.
                # The `generate_content_async` can handle a simple string from the last message.
                last_message = messages[-1].get('content', '') if messages else ''
                response = await self.gemini_model.generate_content_async(last_message)
                return response.text
            else:
                last_message = messages[-1].get('content', '') if messages else ''
                logger.warning(f"Provider '{self.provider}' not fully configured or supported. Returning mock response.")
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