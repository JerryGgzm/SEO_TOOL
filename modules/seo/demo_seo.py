#!/usr/bin/env python3
"""
SEO Demo
SEO 模块演示，支持 Gemini 和 OpenAI LLM 提供商
"""

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
from modules.seo.optimizer import EnhancedSEOOptimizer, SEOOptimizer

def get_llm_client(provider: str = None):
    """Get LLM client for specified provider"""
    if provider is None:
        # Auto-detect from available API keys
        if os.getenv('GEMINI_API_KEY'):
            provider = 'gemini'
        elif os.getenv('OPENAI_API_KEY'):
            provider = 'openai'
        else:
            print("❌ No LLM API keys found in .env file")
            return None
    
    print(f"🤖 Using LLM Provider: {provider.upper()}")
    
    if provider.lower() == "gemini":
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ Gemini API key not found. Set GEMINI_API_KEY in your .env file")
            return None
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash-lite")
            print("✅ Gemini LLM client initialized successfully")
            return model
        except ImportError:
            print("❌ Google Generative AI package not installed. Install with: pip install google-generativeai")
            return None
        except Exception as e:
            print(f"❌ Failed to initialize Gemini LLM client: {e}")
            return None
    
    elif provider.lower() in ["openai", "gpt"]:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OpenAI API key not found. Set OPENAI_API_KEY in your .env file")
        return None
    
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=api_key)
            print("✅ OpenAI LLM client initialized successfully")
        return client
    except ImportError:
        print("❌ OpenAI package not installed. Install with: pip install openai")
        return None
    except Exception as e:
            print(f"❌ Failed to initialize OpenAI LLM client: {e}")
            return None
    
    else:
        print(f"❌ Unsupported LLM provider: {provider}")
        return None

def interactive_select_provider():
    """Interactive LLM provider selection"""
    print("\n🤖 LLM Provider Selection")
    print("=" * 40)
    
    providers = []
    if os.getenv('GEMINI_API_KEY'):
        providers.append(('GEMINI', 'gemini-2.0-flash-lite'))
    if os.getenv('OPENAI_API_KEY'):
        providers.append(('OPENAI', 'gpt-4-turbo-preview'))
    
    if not providers:
        print("❌ No LLM providers configured")
        return None
    
    print("Available LLM providers:")
    for i, (name, model) in enumerate(providers, 1):
        print(f"  {i}. {name} ({model})")
    print("  3. Auto-detect (recommended)")
    
    while True:
        try:
            choice = input("\nSelect LLM provider (1-3): ").strip()
            if choice == '3':
                print("✅ Selected: Auto-detect")
                return providers[0][0] if providers else None
            elif choice in ['1', '2']:
                idx = int(choice) - 1
                if idx < len(providers):
                    selected = providers[idx][0]
                    print(f"✅ Selected: {selected}")
                    return selected
            print("❌ Invalid choice. Please enter a number between 1 and 3")
        except (ValueError, IndexError):
            print("❌ Invalid choice. Please enter a number between 1 and 3")

async def demo_llm_seo_intelligence(llm_client, provider: str):
    """Demo LLM SEO Intelligence core features"""
    print(f"\n🎯 Demo: LLM SEO Intelligence Core Features ({provider.upper()})")
    
    # Import LLM intelligence
    from modules.seo.llm_intelligence import LLMSEOIntelligence
    from modules.seo.models import SEOOptimizationLevel, SEOContentType
    
    llm_intelligence = LLMSEOIntelligence(
        llm_client=llm_client,
        llm_provider=provider
    )
    
    test_content = "Working on new AI features for our productivity app"
    print(f"📝 Original Content: {test_content}")
    
        # Test different optimization modes
    optimization_modes = [
        ("Comprehensive Optimization Mode", "comprehensive"),
        ("Intelligent Optimization Mode", "intelligent"), 
        ("Adaptive Optimization Mode", "adaptive")
    ]
    
    for mode_name, mode in optimization_modes:
        print(f"\n🔧 Testing {mode_name}...")
        
        try:
            result = await llm_intelligence.optimize_content(
                content=test_content,
                optimization_level=SEOOptimizationLevel.AGGRESSIVE,
                content_type=SEOContentType.TWEET,
                target_audience="startup founders",
                target_keywords=["AI", "productivity", "startup"]
            )
            
            if result:
                print(f"✨ Optimized Content: {result.optimized_content}")
                print(f"📊 Optimization Score: {result.optimization_score:.2f}")
                print(f"🚀 Estimated Reach Improvement: {result.estimated_reach_improvement:.1f}%")
                if result.improvements_made:
                    print(f"🔧 Key Improvements:")
                    for improvement in result.improvements_made[:2]:  # Show only top 2
                        print(f"  • {improvement}")
            else:
                print("❌ Optimization failed")
                
        except Exception as e:
            print(f"❌ {mode_name} failed: {e}")

async def demo_enhanced_seo_optimizer(llm_client, provider: str):
    """Demo enhanced SEO optimizer"""
    print(f"\n🎯 Demo: Enhanced SEO Optimizer ({provider.upper()})")
    
    try:
        from modules.seo.optimizer import EnhancedSEOOptimizer
        from modules.seo.models import SEOOptimizationRequest, SEOContentType, SEOOptimizationLevel
        
        # Create enhanced optimizer
        optimizer = EnhancedSEOOptimizer(
            twitter_client=None,
            config={'llm_optimization_mode': 'comprehensive'},
            llm_client=llm_client
        )
        
        test_content = "Our new feature helps developers save time and boost productivity"
        print(f"📝 Original Content: {test_content}")
        
        # Create optimization request
        request = SEOOptimizationRequest(
            content=test_content,
            content_type=SEOContentType.TWEET,
            optimization_level=SEOOptimizationLevel.AGGRESSIVE,
            target_keywords=["development", "productivity"]
        )
        
        # Create analysis context
        from modules.seo.models import SEOAnalysisContext
        context = SEOAnalysisContext(
            content_type=SEOContentType.TWEET,
            target_audience="software developers",
            niche_keywords=["development", "productivity", "tools"]
        )
        
        print("🎯 Target Audience: software developers")
        print("🔑 Target Keywords: development, productivity")
        print("🏷️ Niche Keywords: development, productivity, tools")
        
        print("\n🤖 Testing LLM-Enhanced Optimization Modes...")
        
        # Test different optimization modes
        modes = ['comprehensive', 'intelligent', 'adaptive']
        
        for mode in modes:
            print(f"\n🔧 Testing {mode.title()} Mode...")
            
            try:
                # Set optimization mode
                optimizer.llm_config['llm_optimization_mode'] = mode
                
                # Perform optimization
                result = await optimizer.optimize_content_async(request, context)
                
                if result:
                    print(f"✨ Optimized Content: {result.optimized_content}")
                    print(f"📊 Optimization Score: {result.optimization_score:.2f}")
                    print(f"🚀 Estimated Reach Improvement: {result.estimated_reach_improvement:.1f}%")
                    
                    if result.improvements_made:
                        print(f"🔧 Key Improvements:")
                        for improvement in result.improvements_made[:2]:  # Show only top 2
                            print(f"  • {improvement}")
                else:
                    print("❌ Optimization failed")

        except Exception as e:
                print(f"❌ {mode.title()} mode failed: {e}")
        
    except Exception as e:
        print(f"❌ Enhanced SEO optimizer demo failed: {e}")

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
    print("\n📋 Available LLM Providers: GEMINI, OPENAI")
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

# --- Helper Functions ---

def select_llm_provider():
    """Interactively selects the LLM provider and returns the provider, config, and client."""
    selected_provider_name = llm_selector.interactive_select_provider()
    if not selected_provider_name:
        return None, None, None

    # Get config and client
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
            # Note: The current LLMClient only has logic for 'openai'.
            # This will effectively run in a mock mode for Gemini unless client.py is updated.
            print("✅ Gemini LLM client initialized (Note: currently uses mock responses).")
        elif provider_key == 'openai' or provider_key == 'gpt':
            print("✅ OpenAI LLM client initialized successfully")
        return provider_key, llm_config, llm_client
    except Exception as e:
        print(f"❌ Error initializing LLM client: {e}")
        return None, None, None

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    # Silence the verbose http client logs from the openai library
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    asyncio.run(main())