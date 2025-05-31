"""LLM adapter abstraction layer"""
from typing import List, Dict, Any, Optional, Protocol
from abc import ABC, abstractmethod
import logging
import asyncio
import openai
import anthropic

from .models import LLMResponse

logger = logging.getLogger(__name__)

class LLMAdapter(ABC):
    """Abstract base class for LLM adapters"""
    
    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
        self.api_key = api_key
    
    @abstractmethod
    async def generate_content(self, prompt: str, max_tokens: int = 1000, 
                             temperature: float = 0.7) -> LLMResponse:
        """Generate content using the LLM"""
        pass
    
    @abstractmethod
    async def generate_multiple(self, prompt: str, count: int = 3, 
                              max_tokens: int = 1000, 
                              temperature: float = 0.7) -> List[LLMResponse]:
        """Generate multiple content variations"""
        pass
    
    def _parse_response(self, raw_response: str, confidence: float = 0.8) -> LLMResponse:
        """Parse raw LLM response into structured format"""
        # Extract alternatives if present (looking for numbered lists)
        lines = raw_response.strip().split('\n')
        alternatives = []
        main_content = raw_response
        
        # Simple parsing for numbered alternatives
        if any(line.strip().startswith(('1.', '2.', '3.')) for line in lines):
            alternatives = []
            current_content = []
            
            for line in lines:
                stripped = line.strip()
                if stripped.startswith(('1.', '2.', '3.', '4.', '5.')):
                    if current_content:
                        alternatives.append('\n'.join(current_content).strip())
                    current_content = [stripped[2:].strip()]
                else:
                    current_content.append(line)
            
            if current_content:
                alternatives.append('\n'.join(current_content).strip())
            
            main_content = alternatives[0] if alternatives else raw_response
            alternatives = alternatives[1:] if len(alternatives) > 1 else []
        
        return LLMResponse(
            content=main_content.strip(),
            confidence=confidence,
            alternatives=alternatives,
            metadata={'raw_response': raw_response}
        )

class OpenAIAdapter(LLMAdapter):
    """OpenAI GPT adapter"""
    
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        super().__init__(model_name, api_key)
        self.client = openai.AsyncOpenAI(api_key=api_key)
    
    async def generate_content(self, prompt: str, max_tokens: int = 1000, 
                             temperature: float = 0.7) -> LLMResponse:
        """Generate content using OpenAI GPT"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert social media content creator specializing in engaging, brand-aligned posts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                n=1
            )
            
            content = response.choices[0].message.content
            confidence = 1.0 - (temperature * 0.5)  # Higher temperature = lower confidence
            
            return self._parse_response(content, confidence)
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return LLMResponse(
                content="Error generating content",
                confidence=0.0,
                metadata={'error': str(e)}
            )
    
    async def generate_multiple(self, prompt: str, count: int = 3, 
                              max_tokens: int = 1000, 
                              temperature: float = 0.8) -> List[LLMResponse]:
        """Generate multiple variations using OpenAI"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert social media content creator. Generate multiple engaging variations of the requested content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                n=count
            )
            
            results = []
            for choice in response.choices:
                content = choice.message.content
                confidence = 1.0 - (temperature * 0.5)
                results.append(self._parse_response(content, confidence))
            
            return results
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return [LLMResponse(
                content="Error generating content",
                confidence=0.0,
                metadata={'error': str(e)}
            )]

class ClaudeAdapter(LLMAdapter):
    """Anthropic Claude adapter"""
    
    def __init__(self, api_key: str, model_name: str = "claude-3-sonnet-20240229"):
        super().__init__(model_name, api_key)
        self.client = anthropic.Anthropic(api_key=api_key)
    
    async def generate_content(self, prompt: str, max_tokens: int = 1000, 
                             temperature: float = 0.7) -> LLMResponse:
        """Generate content using Claude"""
        try:
            message = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.client.messages.create(
                    model=self.model_name,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{
                        "role": "user", 
                        "content": f"You are an expert social media content creator. {prompt}"
                    }]
                )
            )
            
            content = message.content[0].text
            confidence = 1.0 - (temperature * 0.4)
            
            return self._parse_response(content, confidence)
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return LLMResponse(
                content="Error generating content",
                confidence=0.0,
                metadata={'error': str(e)}
            )
    
    async def generate_multiple(self, prompt: str, count: int = 3, 
                              max_tokens: int = 1000, 
                              temperature: float = 0.8) -> List[LLMResponse]:
        """Generate multiple variations using Claude"""
        multi_prompt = f"{prompt}\n\nPlease provide {count} different variations, numbered 1., 2., 3., etc."
        
        response = await self.generate_content(multi_prompt, max_tokens, temperature)
        
        # If we got alternatives from parsing, return them as separate responses
        if response.alternatives:
            results = [response]  # First one
            for alt in response.alternatives:
                results.append(LLMResponse(
                    content=alt,
                    confidence=response.confidence * 0.9,  # Slightly lower confidence
                    metadata=response.metadata
                ))
            return results[:count]
        
        # Otherwise generate multiple individual calls
        tasks = [
            self.generate_content(prompt, max_tokens, temperature) 
            for _ in range(count)
        ]
        return await asyncio.gather(*tasks)

class LocalLLMAdapter(LLMAdapter):
    """Adapter for local LLM models (e.g., Ollama)"""
    
    def __init__(self, model_name: str = "llama2", base_url: str = "http://localhost:11434"):
        super().__init__(model_name, "")
        self.base_url = base_url
    
    async def generate_content(self, prompt: str, max_tokens: int = 1000, 
                             temperature: float = 0.7) -> LLMResponse:
        """Generate content using local LLM"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens
                        }
                    }
                ) as response:
                    result = await response.json()
                    content = result.get('response', 'Error generating content')
                    
                    return self._parse_response(content, 0.7)
                    
        except Exception as e:
            logger.error(f"Local LLM error: {e}")
            return LLMResponse(
                content="Error generating content",
                confidence=0.0,
                metadata={'error': str(e)}
            )
    
    async def generate_multiple(self, prompt: str, count: int = 3, 
                              max_tokens: int = 1000, 
                              temperature: float = 0.8) -> List[LLMResponse]:
        """Generate multiple variations using local LLM"""
        tasks = [
            self.generate_content(prompt, max_tokens, temperature) 
            for _ in range(count)
        ]
        return await asyncio.gather(*tasks)

class LLMAdapterFactory:
    """Factory for creating LLM adapters"""
    
    @staticmethod
    def create_adapter(provider: str, **kwargs) -> LLMAdapter:
        """Create LLM adapter based on provider"""
        
        # Ensure provider is not in kwargs to avoid duplication
        clean_kwargs = {k: v for k, v in kwargs.items() if k != 'provider'}
        
        if provider.lower() == "openai":
            return OpenAIAdapter(
                api_key=clean_kwargs.get('api_key'),
                model_name=clean_kwargs.get('model_name', 'gpt-3.5-turbo')
            )
        elif provider.lower() == "anthropic":
            return ClaudeAdapter(
                api_key=clean_kwargs.get('api_key'),
                model_name=clean_kwargs.get('model_name', 'claude-3-sonnet-20240229')
            )
        elif provider.lower() == "local":
            return LocalLLMAdapter(
                model_name=clean_kwargs.get('model_name', 'llama2'),
                base_url=clean_kwargs.get('base_url', 'http://localhost:11434')
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")