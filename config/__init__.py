"""配置模块初始化"""

# LLM Provider Configuration
DEFAULT_LLM_PROVIDER = "gemini"  # 默认使用 Gemini

# 支持的 LLM 提供商
SUPPORTED_LLM_PROVIDERS = ["gemini", "openai", "gpt"]

LLM_CONFIG = {
    "openai": {
        "api_key": "",  # 需要从环境变量或配置文件中获取
        "model": "gpt-4-turbo-preview",
        "temperature": 0.7,
        "max_tokens": 2000
    },
    "anthropic": {
        "api_key": "",  # 需要从环境变量或配置文件中获取
        "model": "claude-3-opus-20240229",
        "temperature": 0.7,
        "max_tokens": 2000
    },
    "gemini": {
        "api_key": "",  # 需要从环境变量或配置文件中获取
        "model": "gemini-pro",
        "temperature": 0.7,
        "max_tokens": 2000
    }
}

# LLM 提供商特定配置
LLM_PROVIDER_CONFIG = {
    "gemini": {
        "response_format": "markdown_json",  # Gemini 经常返回 markdown 格式的 JSON
        "prompt_style": "strict_json",       # 严格的 JSON 提示
        "fallback_strategy": "regex_extraction"
    },
    "openai": {
        "response_format": "clean_json",     # OpenAI 通常返回干净的 JSON
        "prompt_style": "natural_json",      # 自然的 JSON 提示
        "fallback_strategy": "direct_parse"
    },
    "gpt": {
        "response_format": "clean_json",     # GPT 是 OpenAI 的别名
        "prompt_style": "natural_json",
        "fallback_strategy": "direct_parse"
    }
} 