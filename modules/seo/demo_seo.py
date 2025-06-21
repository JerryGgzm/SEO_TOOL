import sys
import os
import asyncio
import logging
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables from .env file at the very beginning
load_dotenv()

# Add project root to Python path
# This allows the script to be run directly, despite being a sub-module.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.llm_config import LLM_CONFIG
from config.llm_selector import llm_selector
from modules.llm.client import LLMClient
from modules.seo.models import SEOContentType, SEOOptimizationRequest, SEOAnalysisContext
from modules.seo.llm_intelligence import LLMSEOIntelligence


# --- Helper Functions ---

def select_llm_provider():
    """Interactively selects the LLM provider and returns the provider, config, and client."""
    selected_provider_name = llm_selector.interactive_select_provider()
    if not selected_provider_name:
        return None, None, None

    try:
        provider_key = selected_provider_name.lower()
        llm_config = LLM_CONFIG.get(provider_key)
        if not llm_config:
            print(f"❌ Configuration for '{provider_key}' not found.")
            return None, None, None

        # Add the provider name to the config dict for consistent access
        llm_config['provider'] = provider_key
        
        # Create an instance of the LLMClient class
        llm_client = LLMClient(
            provider=provider_key,
            api_key=llm_config.get('api_key'),
            model_name=llm_config.get('model_name')
        )

        print(f"🤖 Using LLM Provider: {provider_key.upper()}")
        if provider_key == 'gemini':
            if llm_client.is_available():
                print("✅ Gemini LLM client initialized.")
            else:
                print("⚠️ Gemini LLM client initialized but API key is missing.")
        elif provider_key == 'openai' or provider_key == 'gpt':
            if llm_client.is_available():
                print("✅ OpenAI LLM client initialized successfully")
            else:
                print("⚠️ OpenAI LLM client initialized but API key is missing.")
        
        return provider_key, llm_config, llm_client
        
    except Exception as e:
        print(f"❌ Error initializing LLM client: {e}")
        return None, None, None


class SEODemo:
    def __init__(self, llm_provider: str, llm_client, config):
        self.llm_provider = llm_provider
        self.llm_client = llm_client
        self.config = config
        self.llm_intelligence = LLMSEOIntelligence(
            llm_client=self.llm_client,
            llm_provider=self.llm_provider
        )

        # Demo tests
        self.demo_tests = [
            {
                "name": "General Productivity Tweet",
                "content": "Working on new AI features for our productivity app",
                "context": {
                    "content_type": SEOContentType.TWEET,
                    "target_audience": "startups and entrepreneurs",
                    "niche_keywords": ["AI", "productivity", "startup"],
                    "product_categories": ["software", "AI tools"],
                    "brand_voice": {"tone": "enthusiastic"},
                }
            },
            {
                "name": "Developer Tool Announcement",
                "content": "Our new feature helps developers save time and boost productivity",
                "context": {
                    "content_type": SEOContentType.TWEET,
                    "target_audience": "software developers",
                    "niche_keywords": ["development", "productivity", "tools"],
                    "product_categories": ["developer tools", "software"],
                    "brand_voice": {"tone": "informative"},
                }
            }
        ]

    def print_header(self, title: str):
        """Prints a formatted header"""
        print(f"\n{title}")
        print("=" * (len(title) + 2))

    async def run_demo(self):
        """Run the simplified SEO optimization demo"""
        self.print_header(f"🎯 SEO Content & Hashtag Generation ({self.llm_provider.upper()})")

        for test in self.demo_tests:
            print(f"\n📝 Original Content: {test['content']}")

            # Prepare context and request
            context = SEOAnalysisContext(**test['context'])
            request = SEOOptimizationRequest(
                content=test['content'],
                content_type=context.content_type,
                target_keywords=context.niche_keywords
            )

            # Use the core LLM intelligence for optimization
            try:
                result = await self.llm_intelligence.enhance_content_with_llm(request, context)

                if result and result.get('enhanced_content'):
                    print(f"✨ Optimized Content: {result['enhanced_content']}")

                    # Display hashtags from suggestions
                    suggestions = result.get('seo_suggestions')
                    if suggestions and suggestions.recommended_hashtags:
                        print(f"🏷️  Generated Hashtags: {' '.join(['#' + tag for tag in suggestions.recommended_hashtags])}")

                else:
                    print("❌ Optimization failed to produce a result.")

            except Exception as e:
                print(f"❌ An error occurred during optimization: {e}")


async def main():
    """Main function to run the SEO demo"""
    print("🚀 LLM-Enhanced SEO Module Demo")
    print("=" * 60)

    # Provider selection
    llm_provider, llm_config, llm_client = select_llm_provider()

    if not llm_client:
        print("❌ Demo cancelled.")
        return

    print("=" * 60)

    # Initialize and run the demo
    demo = SEODemo(
        llm_provider=llm_provider,
        llm_client=llm_client,
        config=llm_config
    )
    await demo.run_demo()

    print("\n" + "=" * 60)
    print("🎉 SEO Demo Completed!")


if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    # Silence the verbose http client logs from the openai library
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    asyncio.run(main())