"""Demo script for SEO Module functionality"""
import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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

async def main():
    """Run all SEO module demos"""
    print("🚀 SEO Module Comprehensive Demo")
    print("=" * 50)
    
    # Run all demos
    await demo_seo_optimization()
    demo_hashtag_generation()
    demo_keyword_analysis()
    demo_content_enhancement()
    demo_platform_optimization()
    await demo_integration_with_content_generation()
    demo_competitor_analysis()
    
    print("\n" + "=" * 50)
    print("🎉 SEO Module Demo Completed!")
    print("\nKey Features Demonstrated:")
    print("✅ Comprehensive content optimization")
    print("✅ Intelligent hashtag generation")
    print("✅ Advanced keyword analysis")
    print("✅ Content enhancement for engagement")
    print("✅ Platform-specific optimization")
    print("✅ Integration with content generation")
    print("✅ Competitor analysis capabilities")
    
    print("\nTo integrate with your system:")
    print("1. Import the SEOService class")
    print("2. Initialize with Twitter client and user service")
    print("3. Call get_content_suggestions() from ContentGenerationModule")
    print("4. Use optimize_content() for post-generation optimization")

if __name__ == "__main__":
    asyncio.run(main())