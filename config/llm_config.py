"""Configuration settings"""

import os
from typing import Dict, Any

# LLM Configuration
LLM_CONFIG = {
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model_name": "gpt-3.5-turbo"
    },
    "claude": {
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
        "model_name": "claude-3-sonnet-20240229"
    },
    "gemini": {
        "api_key": os.getenv("GEMINI_API_KEY"),
        # "model_name": "gemini-2.0-flash"
        # "model_name": "gemini-2.0-flash-lite"
        # "model_name": "gemini-2.5-flash"
        # "model_name": "gemini-2.5-flash-preview-04-17"
        # "model_name": "gemini-2.5-flash-lite-preview-06-17"
        "model_name": "gemma-3n-e2b-it"
    }
}

# Default LLM provider
DEFAULT_LLM_PROVIDER = "gemini" 