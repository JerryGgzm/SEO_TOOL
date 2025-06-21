"""
LLM Provider Selection Configuration
支持多种 LLM 提供商的选择和配置
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class LLMSelector:
    """LLM 提供商选择器"""
    
    def __init__(self):
        self.supported_providers = ["gemini", "openai"]
        self.default_provider = "gemini"
    
    def get_preferred_provider(self) -> str:
        """获取首选的 LLM 提供商"""
        # 从环境变量获取
        env_provider = os.getenv('LLM_PROVIDER', '').lower()
        if env_provider in self.supported_providers:
            return env_provider
        
        # 检查可用的 API 密钥
        if os.getenv('GEMINI_API_KEY'):
            return 'gemini'
        elif os.getenv('OPENAI_API_KEY'):
            return 'openai'
        
        # 默认返回 Gemini
        return self.default_provider
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """获取指定提供商的配置"""
        configs = {
            'gemini': {
                'api_key_env': 'GEMINI_API_KEY',
                'model': 'gemini-2.0-flash-lite',
                'temperature': 0.7,
                'max_tokens': 2000,
                'response_format': 'markdown_json',
                'prompt_style': 'strict_json'
            },
            'openai': {
                'api_key_env': 'OPENAI_API_KEY',
                'model': 'gpt-4-turbo-preview',
                'temperature': 0.7,
                'max_tokens': 2000,
                'response_format': 'clean_json',
                'prompt_style': 'natural_json'
            }
        }
        
        return configs.get(provider.lower(), configs['gemini'])
    
    def is_provider_available(self, provider: str) -> bool:
        """检查指定提供商是否可用"""
        config = self.get_provider_config(provider)
        api_key = os.getenv(config['api_key_env'])
        return bool(api_key)
    
    def get_available_providers(self) -> list:
        """获取所有可用的提供商"""
        available = []
        for provider in self.supported_providers:
            if self.is_provider_available(provider):
                available.append(provider)
        return available
    
    def validate_provider_setup(self, provider: str) -> tuple[bool, str]:
        """验证提供商设置"""
        if provider not in self.supported_providers:
            return False, f"Unsupported provider: {provider}"
        
        config = self.get_provider_config(provider)
        api_key = os.getenv(config['api_key_env'])
        
        if not api_key:
            return False, f"API key not found for {provider}. Set {config['api_key_env']} in your .env file"
        
        return True, f"{provider} is properly configured"
    
    def interactive_select_provider(self) -> str:
        """交互式选择 LLM 提供商"""
        print("\n🤖 LLM Provider Selection")
        print("=" * 40)
        
        # 检查可用的提供商
        available = self.get_available_providers()
        
        if not available:
            print("❌ No LLM providers are available!")
            print("Please set up at least one of the following API keys in your .env file:")
            print("  - GEMINI_API_KEY for Gemini")
            print("  - OPENAI_API_KEY for OpenAI/GPT")
            return None
        
        print("Available LLM providers:")
        for i, provider in enumerate(available, 1):
            config = self.get_provider_config(provider)
            model = config['model']
            print(f"  {i}. {provider.upper()} ({model})")
        
        print(f"  {len(available) + 1}. Auto-detect (recommended)")
        
        while True:
            try:
                choice = input(f"\nSelect LLM provider (1-{len(available) + 1}): ").strip()
                
                if choice.isdigit():
                    choice_num = int(choice)
                    
                    if 1 <= choice_num <= len(available):
                        selected = available[choice_num - 1]
                        print(f"✅ Selected: {selected.upper()}")
                        return selected
                    elif choice_num == len(available) + 1:
                        # Auto-detect
                        auto_selected = self.get_preferred_provider()
                        print(f"✅ Auto-detected: {auto_selected.upper()}")
                        return auto_selected
                    else:
                        print(f"❌ Invalid choice. Please enter a number between 1 and {len(available) + 1}")
                else:
                    print("❌ Please enter a valid number")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Demo cancelled by user")
                return None
            except Exception as e:
                print(f"❌ Error: {e}")
                print("Please try again")

# 全局实例
llm_selector = LLMSelector()

def get_llm_provider() -> str:
    """获取当前 LLM 提供商"""
    return llm_selector.get_preferred_provider()

def get_llm_config(provider: str = None) -> Dict[str, Any]:
    """获取 LLM 配置"""
    if provider is None:
        provider = get_llm_provider()
    return llm_selector.get_provider_config(provider)

def is_llm_available(provider: str = None) -> bool:
    """检查 LLM 是否可用"""
    if provider is None:
        provider = get_llm_provider()
    return llm_selector.is_provider_available(provider)

def interactive_select_llm_provider() -> str:
    """交互式选择 LLM 提供商"""
    return llm_selector.interactive_select_provider() 