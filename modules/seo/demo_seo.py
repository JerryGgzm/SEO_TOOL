"""Demo script for SEO Module functionality"""
import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from modules.seo.models import (
    SEOOptimizationRequest, SEOAnalysisContext, SEOContentType,
    SEOOptimizationLevel, HashtagStrategy, HashtagGenerationRequest
)
from modules.seo.optimizer import SEOOptimizer
from modules.seo.hashtag_generator import HashtagGenerator
from modules.seo.keyword_analyzer import KeywordAnalyzer
from modules.seo.content_enhancer import ContentEnhancer

async def demo_seo_optimization():
    """Demo comprehensive SEO optimization"""
    print("🎯 Demo: SEO Content Optimization")
    
    # Initialize SEO optimizer
    optimizer = SEOOptimizer()
    
    # Create test content
    test_content = "Building a startup is challenging but rewarding. Here are some tips for entrepreneurs."
    
    # Create analysis context
    context = SEOAnalysisContext(
        content_type=SEOContentType.TWEET,
        target_audience="entrepreneurs and startup founders",
        niche_keywords=["startup", "entrepreneur", "business"],
        product_categories=["business tools"],
        industry_vertical="technology"
    )
    
    # Create optimization request
    request = SEOOptimizationRequest(
        content=test_content,
        content_type=SEOContentType.TWEET,
        optimization_level=SEOOptimizationLevel.MODERATE,
        hashtag_strategy=HashtagStrategy.ENGAGEMENT_OPTIMIZED,
        context=context
    )
    
    print(f"📝 Original Content: {test_content}")
    print(f"🎯 Target Audience: {context.target_audience}")
    print(f"🏷️ Niche Keywords: {', '.join(context.niche_keywords)}")
    
    try:
        # Perform optimization
        result = await optimizer.optimize_content(request)
        
        print("\n✅ Optimization Results:")
        print(f"📈 Optimization Score: {result.optimization_score:.2f}")
        print(f"🔄 Optimized Content: {result.optimized_content}")
        print(f"📊 Estimated Reach Improvement: {result.estimated_reach_improvement:.1f}%")
        
        if result.improvements_made:
            print(f"\n🔧 Improvements Made:")
            for improvement in result.improvements_made:
                print(f"  • {improvement}")
        
        # Show hashtag suggestions
        if result.hashtag_analysis:
            print(f"\n🏷️ Hashtag Suggestions:")
            for hashtag in result.hashtag_analysis[:5]:
                print(f"  • #{hashtag.hashtag} (relevance: {hashtag.relevance_score:.2f}, engagement: {hashtag.engagement_rate:.1%})")
        
        # Show keyword insights
        if result.keyword_analysis:
            print(f"\n🔍 Keyword Analysis:")
            for keyword in result.keyword_analysis[:3]:
                print(f"  • '{keyword.keyword}' - Volume: {keyword.search_volume}, Difficulty: {keyword.difficulty.value}")
        
    except Exception as e:
        print(f"❌ Optimization failed: {e}")

def demo_hashtag_generation():
    """Demo hashtag generation"""
    print("\n🎯 Demo: Hashtag Generation")
    
    generator = HashtagGenerator()
    
    # Create hashtag request
    request = HashtagGenerationRequest(
        content="AI is transforming the future of work and productivity",
        content_type=SEOContentType.TWEET,
        niche_keywords=["AI", "productivity", "automation"],
        max_hashtags=8,
        strategy=HashtagStrategy.ENGAGEMENT_OPTIMIZED,
        target_audience="tech professionals"
    )
    
    print(f"📝 Content: {request.content}")
    print(f"🎯 Strategy: {request.strategy.value}")
    print(f"🏷️ Niche Keywords: {', '.join(request.niche_keywords)}")
    
    try:
        hashtags = generator.generate_hashtags(request)
        
        print(f"\n✅ Generated {len(hashtags)} hashtags:")
        for i, hashtag in enumerate(hashtags, 1):
            print(f"  {i}. #{hashtag.hashtag}")
            print(f"     • Relevance: {hashtag.relevance_score:.2f}")
            print(f"     • Engagement Rate: {hashtag.engagement_rate:.1%}")
            print(f"     • Competition: {hashtag.competition_level.value}")
            print(f"     • Growth Rate: {hashtag.growth_rate:.1f}%")
        
    except Exception as e:
        print(f"❌ Hashtag generation failed: {e}")

def demo_keyword_analysis():
    """Demo keyword analysis"""
    print("\n🎯 Demo: Keyword Analysis")
    
    analyzer = KeywordAnalyzer()
    
    # Create analysis context
    context = SEOAnalysisContext(
        content_type=SEOContentType.TWEET,
        niche_keywords=["productivity", "automation", "efficiency"],
        target_audience="business professionals",
        industry_vertical="technology"
    )
    
    test_content = "Boost your productivity with automation tools that save time and increase efficiency"
    
    print(f"📝 Content: {test_content}")
    print(f"🎯 Niche: {', '.join(context.niche_keywords)}")
    
    try:
        keywords = analyzer.analyze_keywords(test_content, context)
        
        print(f"\n✅ Analyzed {len(keywords)} keywords:")
        for keyword in keywords[:5]:
            print(f"\n  🔍 '{keyword.keyword}'")
            print(f"     • Search Volume: {keyword.search_volume:,}")
            print(f"     • Difficulty: {keyword.difficulty.value}")
            print(f"     • Relevance: {keyword.relevance_score:.2f}")
            print(f"     • Trending: {'Yes' if keyword.trending_status else 'No'}")
            if keyword.semantic_variations:
                print(f"     • Variations: {', '.join(keyword.semantic_variations[:3])}")
        
        # Generate keyword suggestions
        suggestions = analyzer.generate_keyword_suggestions(context, 10)
        print(f"\n💡 Keyword Suggestions:")
        for suggestion in suggestions[:5]:
            print(f"  • {suggestion}")
        
    except Exception as e:
        print(f"❌ Keyword analysis failed: {e}")

def demo_content_enhancement():
    """Demo content enhancement"""
    print("\n🎯 Demo: Content Enhancement")
    
    enhancer = ContentEnhancer()
    
    # Test different enhancement features
    test_contents = [
        {
            'content': "This is a basic post about business growth",
            'description': "Basic content enhancement"
        },
        {
            'content': "AI and machine learning are revolutionizing business operations and customer experience",
            'description': "Keyword integration"
        },
        {
            'content': "Very long sentence that goes on and on about productivity and efficiency and automation and all the ways that technology can help businesses improve their operations and reduce costs while increasing revenue and customer satisfaction",
            'description': "Readability improvement"
        }
    ]
    
    for test in test_contents:
        print(f"\n--- {test['description']} ---")
        print(f"📝 Original: {test['content']}")
        
        try:
            # Test different enhancements
            enhanced = enhancer.improve_readability(test['content'])
            print(f"📖 Readability: {enhanced}")
            
            enhanced_engagement = enhancer.add_engagement_elements(enhanced)
            print(f"💬 Engagement: {enhanced_engagement}")
            
            # Test keyword enhancement
            if 'keyword' in test['description'].lower():
                keywords = ['productivity', 'automation']
                keyword_enhanced = enhancer.enhance_with_keywords(test['content'], keywords)
                print(f"🔍 With Keywords: {keyword_enhanced}")
            
        except Exception as e:
            print(f"❌ Enhancement failed: {e}")

def demo_platform_optimization():
    """Demo platform-specific optimization"""
    print("\n🎯 Demo: Platform Optimization")
    
    enhancer = ContentEnhancer()
    
    base_content = "Sharing insights about AI and innovation in the tech industry"
    
    platforms = ['twitter', 'linkedin', 'facebook']
    
    print(f"📝 Base Content: {base_content}")
    
    for platform in platforms:
        try:
            optimized = enhancer.optimize_for_platform(base_content, platform)
            print(f"\n📱 {platform.title()}: {optimized}")
            
        except Exception as e:
            print(f"❌ {platform} optimization failed: {e}")

async def demo_integration_with_content_generation():
    """Demo integration with content generation module"""
    print("\n🎯 Demo: Integration with Content Generation")
    
    optimizer = SEOOptimizer()
    
    # Simulate trend info and product info from other modules
    trend_info = {
        'topic_name': 'AI productivity tools',
        'keywords': ['ai', 'productivity', 'automation', 'efficiency'],
        'pain_points': ['time management', 'workflow optimization']
    }
    
    product_info = {
        'name': 'ProductivityAI',
        'target_audience': 'busy professionals',
        'core_values': ['efficiency', 'innovation', 'simplicity'],
        'industry_category': 'productivity software'
    }
    
    print("🔗 Simulating ContentGenerationModule integration...")
    print(f"📈 Trend: {trend_info['topic_name']}")
    print(f"🎯 Product: {product_info['name']}")
    
    try:
        # Get SEO suggestions for content generation
        suggestions = await optimizer.get_content_suggestions(
            trend_info, product_info, SEOContentType.TWEET
        )
        
        print("\n✅ SEO Suggestions for Content Generation:")
        print(f"🏷️ Recommended Hashtags: {', '.join(f'#{h}' for h in suggestions.recommended_hashtags)}")
        print(f"🔍 Primary Keywords: {', '.join(suggestions.primary_keywords)}")
        print(f"📏 Optimal Length: {suggestions.optimal_length} characters")
        print(f"📢 Suggested CTA: {suggestions.call_to_action}")
        
        # Test simple content optimization
        test_content = "AI tools are changing how we work and boosting productivity for teams everywhere"
        context = {
            'seo_keywords': suggestions.primary_keywords,
            'target_audience': product_info['target_audience']
        }
        
        optimized = optimizer.optimize_content_simple(test_content, SEOContentType.TWEET, context)
        print(f"\n🔄 Quick Optimization:")
        print(f"   Original: {test_content}")
        print(f"   Optimized: {optimized}")
        
    except Exception as e:
        print(f"❌ Integration demo failed: {e}")

def demo_competitor_analysis():
    """Demo competitor hashtag analysis"""
    print("\n🎯 Demo: Competitor Analysis")
    
    generator = HashtagGenerator()
    
    competitor_handles = ['@competitor1', '@competitor2', '@competitor3']
    
    print(f"🔍 Analyzing competitors: {', '.join(competitor_handles)}")
    
    try:
        analysis = generator.analyze_competitor_hashtags(competitor_handles)
        
        print(f"\n✅ Competitor Analysis Results:")
        print(f"🔝 Top Hashtags: {', '.join(f'#{h}' for h in analysis.top_hashtags)}")
        print(f"📊 Most Frequent:")
        for hashtag, count in list(analysis.hashtag_frequency.items())[:3]:
            print(f"   • #{hashtag}: {count} uses")
        
        print(f"📈 Best Engagement:")
        for hashtag, score in list(analysis.engagement_correlation.items())[:3]:
            print(f"   • #{hashtag}: {score:.1%} correlation")
        
        if analysis.gap_opportunities:
            print(f"💡 Gap Opportunities: {', '.join(f'#{h}' for h in analysis.gap_opportunities)}")
        
    except Exception as e:
        print(f"❌ Competitor analysis failed: {e}")

async def demo_system_integration():
    """Demo real system integration"""
    print("\n🔗 Demo: Real System Integration")
    
    try:
        # Use absolute imports
        from database import DataFlowManager
        from modules.user_profile import UserProfileService
        from modules.twitter_api.client import TwitterAPIClient
        from modules.content_generation.service import ContentGenerationService
        from modules.analytics.collector import AnalyticsCollector
        from modules.seo.service_integration import SEOService
        from modules.seo.models import SEOContentType, SEOOptimizationLevel
        
        print("🚀 Initializing system components...")
        
        # Check if configuration is available
        try:
            from config.settings import settings
            settings.TWITTER.validate()
            print("✅ Twitter API credentials found")
            
            # Initialize Twitter client with real credentials
            twitter_client = TwitterAPIClient(
                client_id=settings.TWITTER.CLIENT_ID,
                client_secret=settings.TWITTER.CLIENT_SECRET
            )
        except (ImportError, ValueError) as e:
            print(f"⚠️ Configuration issue: {e}")
            print("💡 Using mock Twitter client for demo")
            
            # Create mock Twitter client for demo
            class MockTwitterClient:
                def __init__(self, client_id, client_secret):
                    self.client_id = client_id
                    self.client_secret = client_secret
                
                def get_tweet_by_id(self, *args, **kwargs):
                    return {
                        'data': {
                            'public_metrics': {
                                'like_count': 10,
                                'retweet_count': 2,
                                'reply_count': 1,
                                'quote_count': 0
                            },
                            'created_at': '2024-01-01T12:00:00Z'
                        }
                    }
            
            twitter_client = MockTwitterClient("demo_client_id", "demo_client_secret")
        
        # Initialize database and services
        try:
            data_flow_manager = DataFlowManager()
            print("✅ Database manager initialized")
        except Exception as e:
            print(f"⚠️ Database initialization issue: {e}")
            print("💡 Using mock data flow manager for demo")
            
            # Create mock data flow manager
            class MockDataFlowManager:
                def store_seo_optimization_result(self, data):
                    print(f"📝 Mock: Stored SEO result for {data.get('founder_id')}")
                
                def get_seo_performance_history(self, founder_id, days):
                    return []
            
            data_flow_manager = MockDataFlowManager()
        
        # Initialize services with error handling
        try:
            user_profile_service = UserProfileService(data_flow_manager)
            print("✅ User profile service initialized")
        except Exception as e:
            print(f"⚠️ User service issue: {e}")
            user_profile_service = None
        
        try:
            analytics_collector = AnalyticsCollector(data_flow_manager, twitter_client)
            print("✅ Analytics collector initialized")
        except Exception as e:
            print(f"⚠️ Analytics collector issue: {e}")
            analytics_collector = None
        
        try:
            seo_service = SEOService(data_flow_manager, user_profile_service, twitter_client)
            print("✅ SEO service initialized")
        except Exception as e:
            print(f"⚠️ SEO service issue: {e}")
            # Create minimal SEO service for demo
            from modules.seo.optimizer import SEOOptimizer
            
            class MockSEOService:
                def __init__(self):
                    self.optimizer = SEOOptimizer()
                
                async def optimize_content_for_founder(self, founder_id, content, content_type='tweet'):
                    result = self.optimizer.optimize_content(content)
                    return {
                        'original_content': result.original_content,
                        'optimized_content': result.optimized_content,
                        'seo_score': result.optimization_score,
                        'keywords_used': result.keywords_used,
                        'hashtags_suggested': result.hashtags_suggested
                    }
                
                async def get_optimization_recommendations(self, founder_id, days=30):
                    return {
                        'recommendations': [
                            'Add more relevant hashtags',
                            'Include trending keywords',
                            'Optimize content length'
                        ]
                    }
                
                async def get_seo_analytics(self, founder_id, days=30):
                    return {
                        'avg_seo_score': 0.75,
                        'total_optimizations': 15,
                        'top_keywords': ['productivity', 'ai', 'automation']
                    }
            
            seo_service = MockSEOService()
        
        try:
            content_service = ContentGenerationService(data_flow_manager, seo_service)
            print("✅ Content generation service initialized")
        except Exception as e:
            print(f"⚠️ Content service issue: {e}")
            content_service = None
        
        print("✅ System components initialized (with fallbacks where needed)")
        
        # Demo with a test founder
        founder_id = "demo_founder_123"
        print(f"\n👤 Working with founder: {founder_id}")
        
        # 1. Generate content with SEO optimization
        print("\n📝 Step 1: Generate SEO-optimized content")
        
        sample_content = "Working on new features for our productivity app"
        
        if seo_service:
            optimized_result = await seo_service.optimize_content_for_founder(
                founder_id=founder_id,
                content=sample_content,
                content_type='tweet'
            )
            
            print(f"✅ Original: {optimized_result.get('original_content', 'N/A')}")
            print(f"✨ Optimized: {optimized_result.get('optimized_content', 'N/A')}")
            print(f"🏷️ Hashtags: {', '.join(optimized_result.get('hashtags_suggested', []))}")
            print(f"📊 SEO score: {optimized_result.get('seo_score', 0):.2f}")
        
        # 2. Analyze existing content performance
        print("\n📈 Step 2: Analyze content performance")
        
        if analytics_collector:
            try:
                performance_data = await analytics_collector.collect_real_time_metrics(founder_id)
                print(f"📊 Real-time metrics: {performance_data}")
            except Exception as e:
                print(f"⚠️ Analytics collection failed: {e}")
                print("📊 Mock metrics: {'today_posts': 2, 'week_posts': 8, 'engagement_trend': 'improving'}")
        
        # 3. Get SEO recommendations
        print("\n💡 Step 3: Get SEO recommendations")
        
        if seo_service:
            seo_recommendations = await seo_service.get_optimization_recommendations(
                founder_id=founder_id,
                days=30
            )
            
            print("🎯 SEO Recommendations:")
            for rec in seo_recommendations.get('recommendations', [])[:3]:
                print(f"  • {rec}")
        
        # 4. Track SEO performance over time
        print("\n📈 Step 4: Track SEO performance")
        
        if seo_service:
            seo_analytics = await seo_service.get_seo_analytics(founder_id, days=30)
            
            print(f"📊 SEO Analytics Summary:")
            print(f"  • Average SEO Score: {seo_analytics.get('avg_seo_score', 0):.2f}")
            print(f"  • Total Optimizations: {seo_analytics.get('total_optimizations', 0)}")
            print(f"  • Top Keywords: {', '.join(seo_analytics.get('top_keywords', [])[:3])}")
        
        print("\n✅ System integration demo completed successfully!")
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Make sure all modules are properly installed and configured")
        print("💡 Try running from project root: python -m modules.seo.demo_seo")
    except Exception as e:
        print(f"❌ Integration demo failed: {e}")
        print("💡 Check your configuration and database setup")

async def demo_content_generation_integration():
    """Demo integration with content generation module"""
    print("\n🎯 Demo: Content Generation Integration")
    
    try:
        from modules.seo.optimizer import SEOOptimizer
        from modules.seo.models import SEOContentType, SEOOptimizationLevel
        
        print("📝 Content Generation Integration Features:")
        print("1. Automatic SEO optimization during content creation")
        print("2. Keyword integration based on trends and niche")
        print("3. Hashtag suggestions for maximum reach")
        print("4. Content length optimization for platform")
        
        # Demo SEO optimization
        optimizer = SEOOptimizer()
        
        sample_contents = [
            "Excited to share our new AI tool",
            "Building the future of productivity software",
            "Just launched our latest feature update"
        ]
        
        print("\n📊 SEO Optimization Examples:")
        
        for i, content in enumerate(sample_contents, 1):
            result = optimizer.optimize_content(
                content=content,
                content_type=SEOContentType.TWEET,
                target_keywords=['ai', 'productivity', 'software']
            )
            
            print(f"\n{i}. Original: {result.original_content}")
            print(f"   Optimized: {result.optimized_content}")
            print(f"   SEO Score: {result.optimization_score:.2f}")
            print(f"   Keywords: {', '.join(result.keywords_used[:3])}")
            print(f"   Hashtags: {', '.join(result.hashtags_suggested[:3])}")
        
        print("\n✅ Content generation integration demo completed!")
        
    except Exception as e:
        print(f"❌ Content generation integration demo failed: {e}")

async def demo_analytics_integration():
    """Demo integration with analytics module"""
    print("\n🎯 Demo: Analytics Integration")
    
    try:
        print("📊 Analytics Integration Features:")
        print("1. Real-time SEO performance monitoring")
        print("2. Keyword and hashtag effectiveness tracking")
        print("3. Content optimization ROI analysis")
        print("4. Trend correlation with SEO performance")
        
        analytics_features = [
            "📈 Track SEO score improvements over time",
            "🏷️ Monitor hashtag performance and reach",
            "🔍 Analyze keyword effectiveness and ranking",
            "💰 Calculate ROI of SEO optimization efforts",
            "🎯 Identify high-performing content patterns"
        ]
        
        for feature in analytics_features:
            print(f"   • {feature}")
        
        print("\n📋 Analytics Workflow:")
        print("1. AnalyticsCollector gathers real-time engagement data")
        print("2. SEOPerformanceAnalyzer processes SEO-specific metrics")
        print("3. System generates actionable insights and recommendations")
        print("4. Feedback loop improves future content optimization")
        
        print("\n✅ Analytics integration demo completed!")
        
    except Exception as e:
        print(f"❌ Analytics integration demo failed: {e}")

async def demo_twitter_api_integration():
    """Demo integration with Twitter API"""
    print("\n🎯 Demo: Twitter API Integration")
    
    try:
        print("🐦 Twitter API Integration Features:")
        print("1. Real-time engagement metrics collection")
        print("2. Hashtag performance tracking")
        print("3. Trend analysis and keyword research")
        print("4. Content reach and impression analytics")
        
        api_features = [
            "📊 Fetch real tweet engagement metrics",
            "🔥 Monitor trending hashtags and topics",
            "👥 Analyze audience engagement patterns",
            "📈 Track content performance over time",
            "🎯 Optimize posting times based on engagement data"
        ]
        
        for feature in api_features:
            print(f"   • {feature}")
        
        print("\n⚙️ Configuration Required:")
        print("1. Set up Twitter Developer Account")
        print("2. Create Twitter App and get API credentials")
        print("3. Configure OAuth 2.0 for user authentication")
        print("4. Store user access tokens securely")
        
        print("\n💡 Usage in SEO Module:")
        print("  • Real engagement data improves SEO score accuracy")
        print("  • Trending topics inform keyword strategy")
        print("  • Performance metrics guide optimization decisions")
        
        print("\n✅ Twitter API integration demo completed!")
        
    except Exception as e:
        print(f"❌ Twitter API integration demo failed: {e}")

# Import existing demo functions
from modules.seo.demo_seo_basic import (
    demo_seo_optimization,
    demo_hashtag_generation,
    demo_keyword_analysis,
    demo_content_enhancement,
    demo_platform_optimization,
    demo_integration_with_content_generation,
    demo_competitor_analysis
)

async def main():
    """Run all SEO module demos including system integration"""
    print("🚀 SEO Module Comprehensive Demo with System Integration")
    print("=" * 60)
    
    # Run basic demos first
    try:
        await demo_seo_optimization()
        demo_hashtag_generation()
        demo_keyword_analysis()
        demo_content_enhancement()
        demo_platform_optimization()
        await demo_integration_with_content_generation()
        demo_competitor_analysis()
    except Exception as e:
        print(f"⚠️ Some basic demos failed: {e}")
    
    # Run integration demos
    await demo_system_integration()
    await demo_content_generation_integration()
    await demo_analytics_integration()
    await demo_twitter_api_integration()
    
    print("\n" + "=" * 60)
    print("🎉 Complete SEO Module Demo with System Integration!")
    
    print("\n🔧 Integration Checklist:")
    print("✅ SEO optimization during content generation")
    print("✅ Real-time analytics and performance tracking")
    print("✅ Twitter API integration for live data")
    print("✅ Automated keyword and hashtag optimization")
    print("✅ Performance-based recommendation system")
    
    print("\n📋 Next Steps for Production:")
    print("1. Configure real Twitter API credentials")
    print("2. Set up database with proper founder and content data")
    print("3. Implement user authentication and token management")
    print("4. Add error handling and monitoring")
    print("5. Set up automated SEO performance reporting")
    
    print("\n💡 Quick Start Guide:")
    print("```python")
    print("# Initialize SEO service")
    print("seo_service = SEOService(data_flow_manager, user_service, twitter_client)")
    print("")
    print("# Generate SEO-optimized content")
    print("content = await seo_service.optimize_content_for_founder(")
    print("    founder_id, content, content_type")
    print(")")
    print("")
    print("# Track performance")
    print("analytics = await seo_service.get_seo_analytics(founder_id)")
    print("```")

if __name__ == "__main__":
    asyncio.run(main())