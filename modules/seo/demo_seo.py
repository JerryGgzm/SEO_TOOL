#!/usr/bin/env python3
"""
SEO Demo
SEO 模块演示，支持 Gemini 和 OpenAI LLM 提供商
"""

import asyncio
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load environment variables
load_dotenv()

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

async def main():
    """Main demo function"""
    print("🚀 LLM-Enhanced SEO Module Demo")
    print("=" * 60)
    
    # Show available providers
    available = []
    if os.getenv('GEMINI_API_KEY'):
        available.append('GEMINI')
    if os.getenv('OPENAI_API_KEY'):
        available.append('OPENAI')
    
    print(f"\n📋 Available LLM Providers: {', '.join(available)}")
    
    # Interactive provider selection (only once)
    selected_provider = interactive_select_provider()
    if not selected_provider:
        print("❌ No LLM provider selected. Demo cancelled.")
        return
    
    # Get LLM client
    llm_client = get_llm_client(selected_provider)
    if not llm_client:
        print("❌ LLM client not available")
        return
    
    print("=" * 60)
    
    # Run core demos with the selected provider
    await demo_llm_seo_intelligence(llm_client, selected_provider)
    await demo_enhanced_seo_optimizer(llm_client, selected_provider)
    
    print("\n" + "=" * 60)
    print("🎉 LLM-Enhanced SEO Demo Completed!")
    
    print("\n🔧 Quick Integration Guide:")
    print("1. Replace your existing SEOOptimizer with EnhancedSEOOptimizer")
    print("2. Pass your LLM client when initializing the services")
    print("3. Configure optimization modes in your config")
    
    print("\n💡 Key Benefits:")
    print("✅ Intelligent keyword integration that maintains natural flow")
    print("✅ Context-aware hashtag optimization")
    print("✅ Engagement-focused content enhancement")
    print("✅ Multiple optimization strategies (traditional, hybrid, intelligent)")
    print("✅ Backward compatibility with existing code")
    
    print(f"\n🤖 LLM Provider Used: {selected_provider.upper()}")
    print("✅ Automatic provider detection and parsing")
    print("✅ Single provider selection")

if __name__ == "__main__":
    asyncio.run(main()) 