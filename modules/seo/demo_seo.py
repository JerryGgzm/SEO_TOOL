"""LLM-Enhanced SEO Demo and Integration Guide

This demo shows how to integrate and use the LLM-enhanced SEO functionality
with your existing content generation system.

Run python -m modules.seo.demo_seo to test
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the enhanced SEO modules
from modules.seo.service_integration import SEOService, create_enhanced_seo_service
from modules.seo.optimizer import SEOOptimizer, create_enhanced_seo_optimizer
from modules.seo.llm_intelligence import LLMSEOOrchestrator, LLMSEOIntelligence, LLMSEOAnalyzer
from modules.seo.models import SEOOptimizationRequest, SEOAnalysisContext, SEOContentType, SEOOptimizationLevel, HashtagStrategy

# Import content generation for integration demo
from modules.content_generation.service import ContentGenerationService
from modules.content_generation.models import ContentGenerationRequest, ContentType, GenerationMode

# Mock services for demo
from unittest.mock import Mock, MagicMock

# Load environment variables
load_dotenv()

def get_llm_client():
    """Get LLM client (adapt this to your LLM setup)"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OpenAI API key not found. Set OPENAI_API_KEY in your .env file")
        return None
    
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=api_key)
        print("✅ LLM client initialized successfully")
        return client
    except ImportError:
        print("❌ OpenAI package not installed. Install with: pip install openai")
        return None
    except Exception as e:
        print(f"❌ Failed to initialize LLM client: {e}")
        return None

def create_mock_services():
    """Create mock services for demo"""
    
    # Mock Twitter client
    mock_twitter_client = Mock()
    mock_twitter_client.get_trending_hashtags.return_value = ['AI', 'productivity', 'innovation']
    
    # Mock user service with proper dictionary-like behavior
    mock_user_service = Mock()
    
    # Create a real dictionary for user profile (not a Mock)
    mock_user_profile = {
        'target_audience': 'tech entrepreneurs',
        'niche_keywords': ['startup', 'innovation', 'technology'],
        'industry_category': 'technology',
        'core_values': ['innovation', 'efficiency'],
        'product_categories': ['technology'],
        'brand_voice': 'professional',
        'founder_id': 'demo_founder',
        'company_name': 'Demo Company',
        'product_name': 'AI Productivity Suite',
        'business_model': 'SaaS',
        'stage': 'growth',
        'location': 'San Francisco',
        'website': 'https://demo.com',
        'description': 'AI-powered productivity tools for developers'
    }
    
    # Make the mock return the real dictionary
    mock_user_service.get_user_profile.return_value = mock_user_profile
    
    # Also handle get_founder_profile method if it exists
    mock_user_service.get_founder_profile.return_value = mock_user_profile
    
    # Mock data flow manager with proper methods
    mock_data_flow_manager = Mock()
    mock_data_flow_manager.get_seo_performance_history.return_value = []
    mock_data_flow_manager.store_seo_optimization_result = Mock()
    
    # Add content repository mock for content generation demo
    mock_content_repo = Mock()
    mock_content_repo.get_by_id.return_value = None  # Will be handled gracefully
    mock_content_repo.save.return_value = "mock_draft_id_123"
    mock_data_flow_manager.content_repo = mock_content_repo
    
    # Add user repository mock
    mock_user_repo = Mock()
    mock_user_repo.get_by_id.return_value = mock_user_profile
    mock_data_flow_manager.user_repo = mock_user_repo
    
    return mock_twitter_client, mock_user_service, mock_data_flow_manager

async def demo_llm_seo_intelligence():
    """Demo core LLM SEO intelligence features"""
    print("\n🎯 Demo: LLM SEO Intelligence Core Features")
    
    # Get LLM client
    llm_client = get_llm_client()
    if not llm_client:
        print("⚠️ Skipping LLM demos - no LLM client available")
        return
    
    # Create enhanced optimizer
    optimizer = create_enhanced_seo_optimizer(
        twitter_client=None,
        config={'llm_optimization_mode': 'hybrid'},
        llm_client=llm_client
    )
    
    # Initialize LLM SEO Intelligence
    llm_intelligence = LLMSEOIntelligence(llm_client)
    llm_analyzer = LLMSEOAnalyzer(llm_client)
    
    # Test content
    test_content = "Working on new AI features for our productivity app"
    
    # Create context
    context = SEOAnalysisContext(
        content_type=SEOContentType.TWEET,
        target_audience="tech entrepreneurs",
        niche_keywords=["AI", "productivity", "startup"],
        product_categories=["technology"],
        industry_vertical="technology"
    )
    
    # Create optimization request
    request = SEOOptimizationRequest(
        content=test_content,
        content_type=SEOContentType.TWEET,
        optimization_level=SEOOptimizationLevel.MODERATE
    )
    
    print(f"📝 Original Content: {test_content}")
    
    try:
        # Test different optimization modes
        optimization_modes = ['traditional', 'hybrid', 'intelligent']
        
        for mode in optimization_modes:
            print(f"\n🔧 Testing {mode.title()} Optimization Mode...")
            
            # Set optimization mode
            optimizer.llm_config['llm_optimization_mode'] = mode
            
            # Perform optimization
            result = await optimizer.optimize_content(request, context)
            
            print(f"✨ Optimized Content: {result.optimized_content}")
            print(f"📊 Optimization Score: {result.optimization_score:.2f}")
            print(f"🚀 Estimated Reach Improvement: {result.estimated_reach_improvement:.1f}%")
            
            if result.improvements_made:
                print(f"🔧 Improvements Made:")
                for improvement in result.improvements_made[:3]:
                    print(f"  • {improvement}")
            
            # Show LLM insights if available
            if result.optimization_metadata and 'llm_insights' in result.optimization_metadata:
                llm_insights = result.optimization_metadata['llm_insights']
                if llm_insights:
                    print(f"🧠 LLM Insights: {len(llm_insights)} optimization strategies applied")
        
    except Exception as e:
        print(f"❌ Enhanced SEO optimizer demo failed: {e}")

async def demo_enhanced_seo_service():
    """Demo enhanced SEO service integration"""
    print("\n🎯 Demo: Enhanced SEO Service Integration")
    
    # Create mock services
    twitter_client, user_service, data_flow_manager = create_mock_services()
    
    # Get LLM client
    llm_client = get_llm_client()
    
    # Create enhanced SEO service
    seo_service = create_enhanced_seo_service(
        twitter_client=twitter_client,
        user_service=user_service,
        data_flow_manager=data_flow_manager,
        llm_client=llm_client,
        config={'default_optimization_mode': 'intelligent'}
    )
    
    print(f"✅ Enhanced SEO Service initialized (LLM enabled: {seo_service.llm_enabled})")
    
    # Test content
    test_content = "Just launched our new dashboard feature for better analytics"
    founder_id = "demo_founder_123"
    
    try:
        # Demo 1: Intelligent Content Optimization
        print("\n🧠 Testing Intelligent Content Optimization...")
        
        optimization_result = await seo_service.optimize_content_intelligent(
            text=test_content,
            content_type='tweet',
            context={'founder_id': founder_id},
            optimization_mode='intelligent'
        )
        
        print(f"📝 Original: {optimization_result.get('original_content', 'N/A')}")
        print(f"✨ Optimized: {optimization_result.get('optimized_content', 'N/A')}")
        print(f"📊 Score: {optimization_result.get('optimization_score', 0):.2f}")
        print(f"🤖 LLM Enhanced: {optimization_result.get('llm_enhanced', False)}")
        
        # Show suggestions
        seo_suggestions = optimization_result.get('seo_suggestions', {})
        if seo_suggestions.get('recommended_hashtags'):
            hashtags = seo_suggestions['recommended_hashtags'][:3]
            print(f"🏷️ Recommended Hashtags: {', '.join(f'#{tag}' for tag in hashtags)}")
        
        # Demo 2: Content Variations
        print("\n🎨 Testing Content Variations...")
        
        variations = await seo_service.generate_content_variations(
            founder_id=founder_id,
            content=test_content,
            content_type='tweet',
            variation_count=2
        )
        
        for i, variation in enumerate(variations, 1):
            print(f"\n  Variation {i}:")
            print(f"    Content: {variation.get('optimized_content', 'N/A')}")
            print(f"    Strategy: {variation.get('strategy', 'N/A')}")
            print(f"    Score: {variation.get('optimization_score', 0):.2f}")
        
        # Demo 3: SEO Potential Analysis
        if llm_client:
            print("\n📊 Testing SEO Potential Analysis...")
            
            analysis = await seo_service.analyze_content_seo_potential(
                content=test_content,
                founder_id=founder_id,
                content_type='tweet'
            )
            
            print(f"🔍 Combined SEO Score: {analysis.get('combined_score', 0):.2f}")
            print(f"🤖 LLM Enhanced: {analysis.get('llm_enhanced', False)}")
            
            if 'recommendations' in analysis:
                recommendations = analysis['recommendations'][:2]
                print(f"💡 Top Recommendations:")
                for rec in recommendations:
                    print(f"  • {rec}")
        
        # Demo 4: Enhanced Content Suggestions
        print("\n💡 Testing Enhanced Content Suggestions...")
        
        trend_info = {
            'topic_name': 'AI productivity tools',
            'keywords': ['ai', 'productivity', 'automation']
        }
        
        product_info = {
            'target_audience': 'software developers',
            'core_values': ['efficiency', 'innovation'],
            'industry_category': 'technology'
        }
        
        # Fix: Properly handle async get_content_suggestions method
        try:
            suggestions = await seo_service.get_content_suggestions(
                trend_info=trend_info,
                product_info=product_info,
                content_type=SEOContentType.TWEET
            )
            
            print(f"🏷️ Hashtag Suggestions: {', '.join(suggestions.recommended_hashtags[:5])}")
            print(f"🔑 Primary Keywords: {', '.join(suggestions.primary_keywords[:3])}")
            print(f"💬 Engagement Tactics: {', '.join(suggestions.engagement_tactics[:2])}")
        except Exception as e:
            print(f"⚠️ Content suggestions failed: {e}")
            print("Skipping content suggestions demo...")
        
    except Exception as e:
        print(f"❌ Enhanced SEO service demo failed: {e}")

async def demo_content_generation_with_seo():
    """Demo content generation with LLM-enhanced SEO"""
    print("\n📝 Testing Content Generation with LLM-Enhanced SEO...")
    
    try:
        # Create content generation service
        from modules.content_generation.service import ContentGenerationService
        
        # Mock services with better structure
        twitter_client, user_service, data_flow_manager = create_mock_services()
        llm_client = get_llm_client()
        
        # Create SEO service
        seo_service = create_enhanced_seo_service(
            twitter_client=twitter_client,
            user_service=user_service,
            data_flow_manager=data_flow_manager,
            llm_client=llm_client
        )
        
        # Create content generation service with better error handling
        try:
            content_service = ContentGenerationService(
                seo_service=seo_service,
                data_flow_manager=data_flow_manager,
                llm_config={
                    'default_content_type': 'tweet',
                    'max_content_length': 280,
                    'enable_seo_optimization': True,
                    'optimization_mode': 'intelligent'
                }
            )
        except Exception as e:
            print(f"⚠️ Failed to create ContentGenerationService: {e}")
            print("This might be due to missing dependencies or configuration issues")
            
            # Fallback to direct SEO optimization demo
            print("\n🔄 Demonstrating SEO optimization directly...")
            
            test_content = "Boost your development workflow with AI-powered tools"
            try:
                optimization_result = await seo_service.optimize_content_intelligent(
                    text=test_content,
                    content_type='tweet',
                    context={'founder_id': 'demo_founder'},
                    optimization_mode='intelligent'
                )
                
                print(f"📝 Original: {test_content}")
                print(f"✨ Optimized: {optimization_result.get('optimized_content', 'N/A')}")
                print(f"📊 Score: {optimization_result.get('optimization_score', 0):.2f}")
                print(f"🤖 LLM Enhanced: {optimization_result.get('llm_enhanced', False)}")
            except Exception as opt_e:
                print(f"⚠️ SEO optimization also failed: {opt_e}")
            return
        
        # Test content generation request
        from modules.content_generation.models import ContentGenerationRequest
        
        request = ContentGenerationRequest(
            founder_id="demo_founder",
            product_name="AI Productivity Suite",
            content_type="tweet",
            target_audience="software developers",
            key_message="Boost your development workflow with AI-powered tools",
            tone="professional",
            include_hashtags=True,
            max_length=280
        )
        
        print("🔧 Generating content with LLM-enhanced SEO optimization...")
        
        # Generate content with comprehensive error handling
        try:
            draft_ids = await content_service.generate_content_for_founder(
                founder_id=request.founder_id, 
                request=request
            )
            
            if not draft_ids:
                print("❌ No content generated")
                # Fallback to direct optimization
                print("\n🔄 Demonstrating SEO optimization directly...")
                
                test_content = "Boost your development workflow with AI-powered tools"
                optimization_result = await seo_service.optimize_content_intelligent(
                    text=test_content,
                    content_type='tweet',
                    context={'founder_id': request.founder_id},
                    optimization_mode='intelligent'
                )
                
                print(f"📝 Original: {test_content}")
                print(f"✨ Optimized: {optimization_result.get('optimized_content', 'N/A')}")
                print(f"📊 Score: {optimization_result.get('optimization_score', 0):.2f}")
                print(f"🤖 LLM Enhanced: {optimization_result.get('llm_enhanced', False)}")
                return
            
            print(f"✅ Generated {len(draft_ids)} content drafts")
            
            # Get the first draft for demonstration
            first_draft_id = draft_ids[0]
            
            # Retrieve the draft data from database
            try:
                draft_data = content_service.data_flow_manager.content_repo.get_by_id(first_draft_id)
                
                if draft_data:
                    # Convert database model to service model for easier access
                    draft = content_service.db_adapter.from_database_format(draft_data)
                    
                    print(f"📄 Generated Content: {draft.generated_text}")
                    print(f"📊 Quality Score: {draft.quality_score.overall_score if draft.quality_score else 'N/A'}")
                    
                    # Check for SEO suggestions in metadata
                    seo_metadata = draft.generation_metadata.get('seo_suggestions', {})
                    if seo_metadata:
                        hashtags = seo_metadata.get('recommended_hashtags', [])
                        keywords = seo_metadata.get('primary_keywords', [])
                        print(f"🏷️ Recommended Hashtags: {', '.join(hashtags[:5])}")
                        print(f"🔑 Primary Keywords: {', '.join(keywords[:3])}")
                    
                    # Check trend alignment
                    trend_alignment = draft.generation_metadata.get('trend_alignment', [])
                    if trend_alignment:
                        print(f"📈 Trend Alignment: {', '.join(trend_alignment[:3])}")
                    
                    # Check if SEO optimized
                    if draft.generation_metadata.get('seo_optimized'):
                        print("✅ Content successfully optimized with SEO")
                    else:
                        print("⚠️ Basic content generated (SEO optimization limited)")
                else:
                    print("❌ Could not retrieve generated draft")
            except Exception as e:
                print(f"⚠️ Could not retrieve draft data: {e}")
            
        except Exception as e:
            print(f"⚠️ Content generation failed: {e}")
            print("This might be due to missing user profile or configuration issues")
            
            # Try to demonstrate SEO optimization directly instead
            print("\n🔄 Demonstrating SEO optimization directly...")
            
            test_content = "Boost your development workflow with AI-powered tools"
            try:
                optimization_result = await seo_service.optimize_content_intelligent(
                    text=test_content,
                    content_type='tweet',
                    context={'founder_id': request.founder_id},
                    optimization_mode='intelligent'
                )
                
                print(f"📝 Original: {test_content}")
                print(f"✨ Optimized: {optimization_result.get('optimized_content', 'N/A')}")
                print(f"📊 Score: {optimization_result.get('optimization_score', 0):.2f}")
                print(f"🤖 LLM Enhanced: {optimization_result.get('llm_enhanced', False)}")
            except Exception as opt_e:
                print(f"⚠️ SEO optimization also failed: {opt_e}")
        
        print("\n✅ Content generation with SEO demo completed!")
        
    except Exception as e:
        print(f"❌ Content generation demo failed: {e}")
        import traceback
        traceback.print_exc()

async def demo_trending_topics_optimization():
    """Demo trending topics optimization with LLM"""
    print("\n🎯 Demo: Trending Topics Optimization with LLM")
    
    try:
        # Create enhanced SEO service
        twitter_client, user_service, data_flow_manager = create_mock_services()
        llm_client = get_llm_client()
        
        seo_service = create_enhanced_seo_service(
            twitter_client=twitter_client,
            user_service=user_service,
            data_flow_manager=data_flow_manager,
            llm_client=llm_client
        )
        
        # Test content and trending topics
        base_content = "Our platform helps businesses improve their operations"
        trending_topics = ['AI automation', 'digital transformation', 'productivity hacks']
        founder_id = "demo_founder_123"
        
        print(f"📝 Base Content: {base_content}")
        print(f"🔥 Trending Topics: {', '.join(trending_topics)}")
        
        # Optimize for trending topics
        result = await seo_service.optimize_for_trending_topics(
            founder_id=founder_id,
            content=base_content,
            trending_topics=trending_topics,
            content_type='tweet'
        )
        
        print(f"\n✨ Trend-Optimized Content: {result.get('optimized_content', 'N/A')}")
        print(f"📊 Optimization Score: {result.get('optimization_score', 0):.2f}")
        print(f"🔥 Trends Integrated: {', '.join(result.get('trend_integration', []))}")
        
        # Show LLM insights if available
        llm_insights = result.get('llm_insights', {})
        if llm_insights:
            print(f"🧠 LLM Insights Available: {len(llm_insights)} optimization aspects")
        
    except Exception as e:
        print(f"❌ Trending topics optimization demo failed: {e}")

def demo_configuration_and_setup():
    """Demo configuration and setup for LLM-enhanced SEO"""
    print("\n⚙️ Demo: Configuration and Setup")
    
    print("🔧 LLM-Enhanced SEO Configuration Options:")
    
    # Configuration examples
    configurations = {
        'basic_llm_config': {
            'use_llm_for_keywords': True,
            'use_llm_for_hashtags': True,
            'use_llm_for_engagement': True,
            'llm_optimization_mode': 'hybrid',
            'fallback_to_traditional': True
        },
        'aggressive_llm_config': {
            'use_llm_for_keywords': True,
            'use_llm_for_hashtags': True,
            'use_llm_for_engagement': True,
            'llm_optimization_mode': 'llm_enhanced',
            'fallback_to_traditional': False
        },
        'intelligent_config': {
            'use_llm_for_keywords': True,
            'use_llm_for_hashtags': True,
            'use_llm_for_engagement': True,
            'llm_optimization_mode': 'intelligent',
            'fallback_to_traditional': True,
            'default_optimization_mode': 'intelligent'
        }
    }
    
    for config_name, config in configurations.items():
        print(f"\n📋 {config_name.replace('_', ' ').title()}:")
        for key, value in config.items():
            print(f"  • {key}: {value}")
    
    print("\n🔌 Integration Steps:")
    integration_steps = [
        "1. Install required packages: pip install openai anthropic",
        "2. Set up LLM API keys in environment variables",
        "3. Replace SEOOptimizer with EnhancedSEOOptimizer in your services",
        "4. Replace SEOService with EnhancedSEOService",
        "5. Configure LLM optimization modes in your config",
        "6. Test the integration with sample content",
        "7. Monitor optimization results and adjust settings"
    ]
    
    for step in integration_steps:
        print(f"  {step}")
    
    print("\n📋 Environment Variables Required:")
    env_vars = [
        "OPENAI_API_KEY=your_openai_api_key_here",
        "# Optional: For Claude integration",
        "ANTHROPIC_API_KEY=your_anthropic_api_key_here"
    ]
    
    for var in env_vars:
        print(f"  {var}")

async def demo_performance_comparison():
    """Demo performance comparison between traditional and LLM-enhanced SEO"""
    print("\n📊 Demo: Performance Comparison")
    
    try:
        # Create both traditional and enhanced optimizers
        twitter_client, user_service, data_flow_manager = create_mock_services()
        llm_client = get_llm_client()
        
        # Traditional optimizer
        from modules.seo.optimizer import SEOOptimizer
        traditional_optimizer = SEOOptimizer(twitter_client)
        
        # Enhanced optimizer
        enhanced_optimizer = create_enhanced_seo_optimizer(
            twitter_client=twitter_client,
            llm_client=llm_client
        )
        
        # Test content
        test_contents = [
            "Working on new features for our app",
            "Just shipped a major update to our platform",
            "Helping businesses automate their workflows"
        ]
        
        print("🔍 Comparing Traditional vs LLM-Enhanced SEO Optimization:")
        
        for i, content in enumerate(test_contents, 1):
            print(f"\n--- Test {i}: {content} ---")
            
            # Create context
            context = SEOAnalysisContext(
                content_type=SEOContentType.TWEET,
                target_audience="business professionals",
                niche_keywords=["business", "automation", "productivity"],
                industry_vertical="technology"
            )
            
            request = SEOOptimizationRequest(
                content=content,
                content_type=SEOContentType.TWEET,
                optimization_level=SEOOptimizationLevel.MODERATE
            )
            
            # Traditional optimization (synchronous)
            try:
                traditional_result = traditional_optimizer.optimize_content(request, context)
                traditional_score = traditional_result.optimization_score
                traditional_content = traditional_result.optimized_content
            except Exception as e:
                print(f"⚠️ Traditional optimization failed: {e}")
                traditional_score = 0.5
                traditional_content = content
            
            # Enhanced optimization (synchronous for base method, async for intelligent)
            if llm_client:
                try:
                    # Use the async intelligent optimization method
                    enhanced_result_dict = await enhanced_optimizer.optimize_content_intelligent(
                        text=content,
                        content_type='tweet',
                        context={'founder_id': 'demo_founder'},
                        optimization_mode='intelligent'
                    )
                    enhanced_score = enhanced_result_dict.get('optimization_score', 0.5)
                    enhanced_content = enhanced_result_dict.get('optimized_content', content)
                    llm_enhanced = enhanced_result_dict.get('llm_enhanced', False)
                except Exception as e:
                    print(f"⚠️ Enhanced optimization failed: {e}")
                    # Fallback to synchronous method
                    try:
                        enhanced_result = enhanced_optimizer.optimize_content(request, context)
                        enhanced_score = enhanced_result.optimization_score
                        enhanced_content = enhanced_result.optimized_content
                        llm_enhanced = enhanced_result.optimization_metadata.get('llm_enhanced', False) if hasattr(enhanced_result, 'optimization_metadata') and enhanced_result.optimization_metadata else False
                    except Exception as e2:
                        print(f"⚠️ Fallback optimization also failed: {e2}")
                        enhanced_score = traditional_score
                        enhanced_content = traditional_content
                        llm_enhanced = False
            else:
                # No LLM client, use traditional method
                try:
                    enhanced_result = enhanced_optimizer.optimize_content(request, context)
                    enhanced_score = enhanced_result.optimization_score
                    enhanced_content = enhanced_result.optimized_content
                    llm_enhanced = False
                except Exception as e:
                    print("Got an exception HERE", e)
                    enhanced_score = traditional_score
                    enhanced_content = traditional_content
                    llm_enhanced = False
            
            # Display comparison
            print(f"📊 Traditional SEO:")
            print(f"  Content: {traditional_content}")
            print(f"  Score: {traditional_score:.2f}")
            
            print(f"🤖 LLM-Enhanced SEO:")
            print(f"  Content: {enhanced_content}")
            print(f"  Score: {enhanced_score:.2f}")
            print(f"  LLM Enhanced: {llm_enhanced}")
            
            if enhanced_score > traditional_score:
                improvement = ((enhanced_score - traditional_score) / traditional_score) * 100
                print(f"📈 Improvement: +{improvement:.1f}%")
            elif enhanced_score < traditional_score:
                decline = ((traditional_score - enhanced_score) / traditional_score) * 100
                print(f"📉 Decline: -{decline:.1f}%")
            else:
                print("➡️ Similar performance")
        
    except Exception as e:
        print(f"❌ Performance comparison demo failed: {e}")

async def demo_enhanced_seo_optimizer():
    """Demo enhanced SEO optimizer with LLM integration"""
    print("\n🎯 Demo: Enhanced SEO Optimizer")
    
    # Get LLM client
    llm_client = get_llm_client()
    
    # Create enhanced optimizer
    optimizer = create_enhanced_seo_optimizer(
        twitter_client=None,
        config={'llm_optimization_mode': 'hybrid'},
        llm_client=llm_client
    )
    
    # Test content
    test_content = "Our new feature helps developers save time and boost productivity"
    
    # Create context
    context = SEOAnalysisContext(
        content_type=SEOContentType.TWEET,
        target_audience="software developers",
        niche_keywords=["development", "productivity", "tools"],
        product_categories=["technology"],
        industry_vertical="technology"
    )
    
    # Create optimization request
    request = SEOOptimizationRequest(
        content=test_content,
        content_type=SEOContentType.TWEET,
        optimization_level=SEOOptimizationLevel.MODERATE,
        target_keywords=["development", "productivity"],
        include_hashtags=True,
        include_trending_tags=True,
        hashtag_strategy=HashtagStrategy.ENGAGEMENT_OPTIMIZED
    )
    
    print(f"📝 Original Content: {test_content}")
    print(f"🎯 Target Audience: {context.target_audience}")
    print(f"🔑 Target Keywords: {', '.join(request.target_keywords)}")
    print(f"🏷️ Niche Keywords: {', '.join(context.niche_keywords)}")
    
    try:
        # Test different optimization modes if LLM is available
        if llm_client:
            print("\n🤖 Testing LLM-Enhanced Optimization Modes...")
            
            modes = ['traditional', 'hybrid', 'llm_enhanced']
            
            for mode in modes:
                print(f"\n--- {mode.upper()} MODE ---")
                
                # Update optimizer config
                optimizer.llm_config['llm_optimization_mode'] = mode
                
                # Use async method for LLM-enhanced optimization
                if mode in ['hybrid', 'llm_enhanced'] and hasattr(optimizer, 'optimize_content_async'):
                    try:
                        mode_result = await optimizer.optimize_content_async(request, context)
                    except Exception as e:
                        print(f"⚠️ Async optimization failed: {e}")
                        # Fallback to sync method
                        mode_result = optimizer.optimize_content(request, context)
                else:
                    mode_result = optimizer.optimize_content(request, context)
                
                print(f"Content: {mode_result.optimized_content}")
                print(f"Score: {mode_result.optimization_score:.2f}")
                
                # Check if LLM was actually used
                llm_used = mode_result.optimization_metadata.get('llm_enhanced', False) if hasattr(mode_result, 'optimization_metadata') and mode_result.optimization_metadata else False
                print(f"LLM Enhanced: {llm_used}")
        
        # Test intelligent optimization (this one is async)
        print("\n🧠 Testing Intelligent Optimization...")
        
        intelligent_result = await optimizer.optimize_content_intelligent(
            text=test_content,
            content_type='tweet',
            context={'founder_id': 'demo_founder'},
            optimization_mode='intelligent'
        )
        
        print(f"🧠 Intelligent Result: {intelligent_result.get('optimized_content', 'N/A')}")
        print(f"📊 Intelligence Score: {intelligent_result.get('optimization_score', 0):.2f}")
        
        if 'llm_insights' in intelligent_result:
            insights = intelligent_result['llm_insights']
            print(f"💡 LLM Insights: {len(insights)} optimization aspects analyzed")
        
        print("\n✅ Enhanced SEO Optimizer demo completed!")
        
    except Exception as e:
        print(f"❌ Enhanced SEO optimizer demo failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all LLM-enhanced SEO demos"""
    print("🚀 LLM-Enhanced SEO Module Demo")
    print("=" * 60)
    
    # Check LLM availability
    llm_client = get_llm_client()
    if llm_client:
        print("✅ LLM client available - running full demos")
    else:
        print("⚠️ LLM client not available - running limited demos")
    
    print("\n" + "=" * 60)
    
    # Run demos
    try:
        await demo_llm_seo_intelligence()
        await demo_enhanced_seo_optimizer()
        await demo_enhanced_seo_service()
        await demo_content_generation_with_seo()
        await demo_trending_topics_optimization()
        await demo_performance_comparison()
        
        # Configuration demo (non-async)
        demo_configuration_and_setup()
        
    except Exception as e:
        print(f"❌ Demo execution failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 LLM-Enhanced SEO Demo Completed!")
    
    print("\n🔧 Quick Integration Guide:")
    print("1. Replace your existing SEOOptimizer with EnhancedSEOOptimizer")
    print("2. Replace your SEOService with EnhancedSEOService")
    print("3. Pass your LLM client when initializing the services")
    print("4. Configure optimization modes in your config")
    print("5. Your ContentGenerationModule will automatically use LLM-enhanced SEO")
    
    print("\n💡 Key Benefits:")
    print("✅ Intelligent keyword integration that maintains natural flow")
    print("✅ Context-aware hashtag optimization")
    print("✅ Engagement-focused content enhancement")
    print("✅ Trend-aligned content optimization")
    print("✅ Multiple optimization strategies (traditional, hybrid, intelligent)")
    print("✅ Backward compatibility with existing code")
    print("✅ Comprehensive analytics and insights")

if __name__ == "__main__":
    asyncio.run(main())