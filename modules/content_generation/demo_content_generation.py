"""Enhanced demo script for ContentGenerationModule with SEO integration"""
import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv
import json

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import content generation models and services
from modules.content_generation.models import (
    ContentGenerationRequest, ContentGenerationContext, 
    ContentType, BrandVoice, SEOSuggestions
)
from modules.content_generation.generator import ContentGenerator, ContentGenerationFactory
from modules.content_generation.service import ContentGenerationService
from modules.content_generation.quality_checker import ContentQualityChecker

# Import SEO components
from modules.seo.optimizer import SEOOptimizer
from modules.seo.service_integration import SEOService
from modules.seo.models import (
    SEOOptimizationRequest, SEOAnalysisContext, SEOContentType,
    SEOOptimizationLevel, HashtagStrategy
)

# Import analytics components  
from modules.analytics.collector import AnalyticsCollector
from modules.analytics.processor import ContentPerformanceAnalyzer, SEOPerformanceAnalyzer

# Mock services for demo
from unittest.mock import Mock, MagicMock

# Load environment variables
load_dotenv()

def get_openai_api_key() -> str:
    """Get OpenAI API key from environment variables"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        # Try alternative environment variable names
        api_key = os.getenv('OPENAI_KEY') or os.getenv('OPENAI_SECRET_KEY')
    
    if not api_key:
        print("❌ OpenAI API key not found in environment variables.")
        print("💡 Please add OPENAI_API_KEY to your .env file:")
        print("   OPENAI_API_KEY=your_api_key_here")
        return None
    
    return api_key

def get_twitter_credentials() -> Dict[str, str]:
    """Get Twitter API credentials from environment variables"""
    credentials = {
        'client_id': os.getenv('TWITTER_CLIENT_ID'),
        'client_secret': os.getenv('TWITTER_CLIENT_SECRET'),
        'bearer_token': os.getenv('TWITTER_BEARER_TOKEN')
    }
    
    missing = [key for key, value in credentials.items() if not value]
    if missing:
        print(f"⚠️ Missing Twitter credentials: {', '.join(missing)}")
        print("💡 Please add to your .env file:")
        for key in missing:
            print(f"   {key.upper()}=your_{key}_here")
    
    return credentials

class MockTwitterClient:
    """Mock Twitter client for demo"""
    def get_trends_for_location(self, access_token, location_id=1):
        return [
            {'name': '#AI', 'tweet_volume': 50000},
            {'name': '#Innovation', 'tweet_volume': 30000},
            {'name': '#Startup', 'tweet_volume': 25000},
            {'name': '#Tech', 'tweet_volume': 40000},
            {'name': '#Productivity', 'tweet_volume': 15000}
        ]

class MockUserProfileService:
    """Mock user profile service for demo"""
    def get_user_profile(self, user_id):
        return MagicMock(
            product_info={
                'name': 'AI Productivity Assistant',
                'description': 'Helps professionals manage tasks and workflows',
                'core_values': ['efficiency', 'innovation', 'simplicity'],
                'industry_category': 'productivity software',
                'target_audience': 'busy professionals and entrepreneurs'
            }
        )
    
    def get_twitter_access_token(self, user_id):
        return "mock_access_token"

class MockDataFlowManager:
    """Mock data flow manager with SEO integration"""
    def __init__(self):
        self.db_session = Mock()
        self.content_repo = Mock()
        self._seo_optimization_cache = []
        
    def get_content_generation_context(self, founder_id, trend_id=None):
        return {
            'products': [{
                'name': 'AI Productivity Assistant',
                'description': 'Helps professionals manage tasks and workflows',
                'core_values': ['efficiency', 'innovation', 'simplicity'],
                'target_audience': 'busy professionals and entrepreneurs',
                'niche_definition': {'category': 'productivity software'}
            }],
            'founder_settings': {
                'content_preferences': {
                    'tone': 'professional',
                    'style': 'helpful',
                    'formality_level': 0.6
                }
            },
            'trend_info': {
                'topic_name': 'AI productivity tools',
                'pain_points': ['information overload', 'task management', 'workflow efficiency'],
                'questions': ['How to be more productive?', 'Best AI tools for work?'],
                'keywords': ['ai', 'productivity', 'automation', 'efficiency']
            },
            'recent_topics': [],
            'successful_content_patterns': []
        }
    
    def store_generated_content_draft(self, draft_data):
        # Simulate storing and return mock ID
        return f"draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def store_seo_optimization_result(self, founder_id: str, optimization_data: dict) -> bool:
        """Store SEO optimization results (mock implementation)"""
        try:
            record = {
                'founder_id': founder_id,
                'timestamp': datetime.now().isoformat(),
                **optimization_data
            }
            self._seo_optimization_cache.append(record)
            print(f"✅ Stored SEO optimization result: Score {optimization_data.get('seo_quality_score', 0):.2f}")
            return True
        except Exception as e:
            print(f"❌ Failed to store SEO result: {e}")
            return False
    
    def get_seo_performance_history(self, founder_id: str, days: int = 30) -> list:
        """Get SEO performance history (mock implementation)"""
        # Return cached results for demo
        return [record for record in self._seo_optimization_cache 
                if record.get('founder_id') == founder_id]

async def demo_basic_seo_content_generation():
    """Demo basic SEO-enhanced content generation"""
    print("\n🎯 Demo: Basic SEO-Enhanced Content Generation")
    
    try:
        # Get API key from environment
        api_key = get_openai_api_key()
        if not api_key:
            return
        
        print("✅ OpenAI API key loaded from environment")
        
        # Import required modules
        from modules.content_generation.generator import ContentGenerator, ContentGenerationFactory
        from modules.content_generation.models import (
            ContentGenerationRequest, ContentGenerationContext, 
            ContentType, GenerationMode
        )
        
        # Configure LLM (remove 'provider' from config to avoid duplication)
        llm_config = {
            'api_key': api_key,
            'model_name': 'gpt-3.5-turbo'
        }
        
        # Create enhanced generator with SEO
        try:
            from modules.seo.optimizer import SEOOptimizer
            seo_optimizer = SEOOptimizer()
            print("✅ SEO optimizer initialized")
        except Exception as e:
            print(f"⚠️ SEO optimizer initialization failed: {e}")
            seo_optimizer = None
        
        enhanced_generator = ContentGenerationFactory.create_enhanced_generator(
            llm_provider='openai',  # Pass provider separately
            llm_config=llm_config,  # Config without provider
            seo_optimizer=seo_optimizer
        )
        
        print("✅ Enhanced content generator created with SEO integration")
        
        # Create sample request with lower quality threshold for demo
        request = ContentGenerationRequest(
            founder_id="demo_founder_123",
            content_type=ContentType.TWEET,
            trend_id="trend_456",
            generation_mode=GenerationMode.SEO_OPTIMIZED,
            quality_threshold=0.3  # Lower threshold for demo
        )
        
        # Create sample context
        context = ContentGenerationContext(
            trend_info={
                "topic_name": "AI productivity tools",
                "keywords": ["ai", "productivity", "automation"],
                "pain_points": ["time management", "workflow optimization"]
            },
            product_info={
                "name": "ProductivityAI",
                "description": "AI-powered productivity assistant",
                "target_audience": "busy professionals",
                "core_values": ["efficiency", "innovation"],
                "industry_category": "productivity software"
            },
            target_audience="tech-savvy professionals",
            content_preferences={
                "tone": "professional",
                "include_hashtags": True,
                "max_length": 250  # Reduced to leave room for processing
            }
        )
        
        print("\n📝 Generating SEO-optimized content...")
        
        # Generate content
        drafts = await enhanced_generator.generate_content(request, context)
        
        if drafts:
            print(f"\n✅ Generated {len(drafts)} content draft(s):")
            
            for i, draft in enumerate(drafts, 1):
                print(f"\n--- Draft {i} ---")
                print(f"Content: {draft.generated_text}")
                print(f"Length: {len(draft.generated_text)} characters")
                print(f"Quality Score: {draft.quality_score:.2f}")
                
                # Show SEO metrics if available
                if 'seo_quality_score' in draft.generation_metadata:
                    seo_score = draft.generation_metadata['seo_quality_score']
                    print(f"SEO Score: {seo_score:.2f}")
                
                if 'seo_keywords_used' in draft.generation_metadata:
                    keywords = draft.generation_metadata['seo_keywords_used']
                    print(f"Keywords Used: {', '.join(keywords[:3])}")
                
                if 'seo_hashtags_suggested' in draft.generation_metadata:
                    hashtags = draft.generation_metadata['seo_hashtags_suggested']
                    print(f"Hashtags: {', '.join(f'#{tag}' for tag in hashtags[:3])}")
        else:
            print("❌ No content generated")
        
        print("\n✅ Basic SEO content generation demo completed!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

async def demo_seo_performance_analysis():
    """Demo SEO performance analysis"""
    print("\n🎯 Demo: SEO Performance Analysis")
    
    try:
        # Initialize mock services
        data_flow_manager = MockDataFlowManager()
        
        # Add some mock SEO data
        mock_seo_data = [
            {
                'founder_id': 'demo-founder',
                'content_draft_id': 'draft_1',
                'seo_quality_score': 0.84,
                'overall_quality_score': 0.82,
                'keywords_used': ['ai', 'productivity', 'automation'],
                'hashtags_suggested': ['AI', 'ProductivityHack', 'Innovation'],
                'content_type': 'tweet',
                'optimization_method': 'integrated_generation',
                'content_length': 245,
                'optimization_timestamp': datetime.now().isoformat()
            },
            {
                'founder_id': 'demo-founder',
                'content_draft_id': 'draft_2',
                'seo_quality_score': 0.79,
                'overall_quality_score': 0.78,
                'keywords_used': ['workflow', 'automation', 'ai assistant'],
                'hashtags_suggested': ['Efficiency', 'AITools', 'WorkSmarter'],
                'content_type': 'tweet',
                'optimization_method': 'integrated_generation',
                'content_length': 238,
                'optimization_timestamp': datetime.now().isoformat()
            }
        ]
        
        # Store mock data
        for data in mock_seo_data:
            data_flow_manager.store_seo_optimization_result('demo-founder', data)
        
        # Analyze SEO performance
        seo_analyzer = SEOPerformanceAnalyzer(data_flow_manager, None)
        seo_performance = seo_analyzer.analyze_seo_performance('demo-founder', 30)
        
        print("📊 SEO Performance Analysis Results:")
        print(f"  • Total Optimizations: {seo_performance.get('total_optimizations', 0)}")
        print(f"  • Average SEO Score: {seo_performance.get('avg_seo_score', 0):.2f}")
        
        keyword_perf = seo_performance.get('keyword_performance', {})
        if keyword_perf.get('top_performing_keywords'):
            print(f"  • Top Keywords: {', '.join(list(keyword_perf['top_performing_keywords'].keys())[:3])}")
        
        hashtag_eff = seo_performance.get('hashtag_effectiveness', {})
        if hashtag_eff.get('top_effective_hashtags'):
            print(f"  • Top Hashtags: {', '.join(list(hashtag_eff['top_effective_hashtags'].keys())[:3])}")
        
        optimization_trends = seo_performance.get('optimization_trends', {})
        print(f"  • Optimization Trend: {optimization_trends.get('trend_direction', 'unknown')}")
        
        improvements = seo_performance.get('improvement_opportunities', [])
        if improvements:
            print(f"  • Improvement Opportunities:")
            for improvement in improvements[:2]:
                print(f"    - {improvement}")
        
    except Exception as e:
        print(f"❌ SEO analysis demo failed: {e}")

async def demo_comprehensive_seo_workflow():
    """Demo comprehensive SEO workflow"""
    print("\n🎯 Demo: Comprehensive SEO Workflow")
    
    try:
        # Initialize services
        twitter_client = MockTwitterClient()
        user_service = MockUserProfileService()
        data_flow_manager = MockDataFlowManager()
        
        # Initialize SEO service
        seo_service = SEOService(
            twitter_client=twitter_client,
            user_service=user_service,
            data_flow_manager=data_flow_manager
        )
        
        # Step 1: Get SEO suggestions for content generation
        print("1️⃣ Getting SEO suggestions for content generation...")
        
        trend_info = {
            'topic_name': 'AI productivity tools',
            'keywords': ['ai', 'productivity', 'automation'],
            'pain_points': ['information overload', 'task management']
        }
        
        product_info = {
            'name': 'AI Productivity Assistant',
            'target_audience': 'busy professionals',
            'core_values': ['efficiency', 'innovation'],
            'industry_category': 'productivity software'
        }
        
        seo_suggestions = await seo_service.get_content_suggestions(
            trend_info=trend_info,
            product_info=product_info,
            content_type='tweet'
        )
        
        print(f"  ✅ SEO Suggestions Generated:")
        print(f"    • Hashtags: {', '.join(seo_suggestions.recommended_hashtags)}")
        print(f"    • Keywords: {', '.join(seo_suggestions.primary_keywords)}")
        print(f"    • Optimal Length: {seo_suggestions.optimal_length}")
        
        # Step 2: Generate content with SEO optimization
        print("\n2️⃣ Generating content with SEO optimization...")
        
        test_content = "AI tools are transforming productivity for modern professionals"
        optimized_content = seo_service.optimize_content(
            text=test_content,
            content_type='tweet',
            context={
                'seo_keywords': seo_suggestions.primary_keywords,
                'target_audience': 'professionals'
            }
        )
        
        print(f"  📝 Original: {test_content}")
        print(f"  🔧 Optimized: {optimized_content}")
        
        # Step 3: Full SEO optimization analysis
        print("\n3️⃣ Running full SEO optimization analysis...")
        
        full_optimization = await seo_service.optimize_content_full(
            founder_id="demo-founder",
            content=test_content,
            content_type='tweet',
            optimization_level='moderate'
        )
        
        print(f"  📊 Full Optimization Results:")
        print(f"    • Optimization Score: {full_optimization.get('optimization_score', 0):.2f}")
        print(f"    • Estimated Reach Improvement: {full_optimization.get('estimated_reach_improvement', 0):.1f}%")
        
        improvements = full_optimization.get('improvements_made', [])
        if improvements:
            print(f"    • Improvements Made:")
            for improvement in improvements:
                print(f"      - {improvement}")
        
        # Step 4: Generate SEO recommendations
        print("\n4️⃣ Generating personalized SEO recommendations...")
        
        recommendations = seo_service.get_seo_recommendations("demo-founder")
        
        if recommendations:
            print(f"  💡 SEO Recommendations:")
            for category, rec in recommendations.items():
                if isinstance(rec, dict) and 'recommendation' in rec:
                    print(f"    • {category.title()}: {rec['recommendation']}")
        
        # Step 5: Analytics summary
        print("\n5️⃣ Getting SEO analytics summary...")
        
        analytics_summary = seo_service.get_seo_analytics_summary("demo-founder")
        
        if analytics_summary:
            print(f"  📈 Analytics Summary:")
            print(f"    • Total Optimizations: {analytics_summary.get('total_optimizations', 0)}")
            print(f"    • Average Score: {analytics_summary.get('avg_optimization_score', 0):.2f}")
            print(f"    • Optimization Trend: {analytics_summary.get('optimization_trend', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Comprehensive SEO workflow demo failed: {e}")

def demo_seo_configuration():
    """Demo SEO configuration and setup"""
    print("\n🎯 Demo: SEO Configuration & Setup")
    
    try:
        from modules.seo.models import SEOConfiguration, SEOOptimizationLevel, HashtagStrategy
        
        # Create SEO configuration
        seo_config = SEOConfiguration(
            default_optimization_level=SEOOptimizationLevel.MODERATE,
            default_hashtag_strategy=HashtagStrategy.ENGAGEMENT_OPTIMIZED,
            max_hashtags_per_tweet=5,
            max_hashtags_per_thread=3,
            max_hashtags_per_reply=2,
            keyword_analysis_enabled=True,
            competitor_analysis_enabled=True,
            trending_analysis_enabled=True,
            auto_optimization_threshold=0.7,
            performance_tracking_enabled=True
        )
        
        print(f"⚙️ SEO Configuration:")
        print(f"  • Default Optimization Level: {seo_config.default_optimization_level.value}")
        print(f"  • Default Hashtag Strategy: {seo_config.default_hashtag_strategy.value}")
        print(f"  • Max Hashtags per Tweet: {seo_config.max_hashtags_per_tweet}")
        print(f"  • Auto Optimization Threshold: {seo_config.auto_optimization_threshold}")
        print(f"  • Performance Tracking: {'Enabled' if seo_config.performance_tracking_enabled else 'Disabled'}")
        
        # Demo different optimization levels
        print(f"\n🎚️ Optimization Levels:")
        for level in SEOOptimizationLevel:
            print(f"  • {level.value.title()}: {level.value}")
        
        # Demo hashtag strategies  
        print(f"\n🏷️ Hashtag Strategies:")
        for strategy in HashtagStrategy:
            print(f"  • {strategy.value.replace('_', ' ').title()}: {strategy.value}")
        
    except Exception as e:
        print(f"❌ SEO configuration demo failed: {e}")

async def demo_system_integration():
    """Demo full system integration"""
    print("\n🔗 Demo: Full System Integration")
    
    try:
        # Check environment configuration
        api_key = get_openai_api_key()
        twitter_creds = get_twitter_credentials()
        
        if not api_key:
            print("⚠️ Skipping system integration demo due to missing OpenAI API key")
            return
        
        print("✅ Environment configuration checked")
        
        # Import system components
        try:
            from modules.content_generation.service import ContentGenerationService
            
            print("✅ System modules imported successfully")
        except ImportError as e:
            print(f"⚠️ System module import failed: {e}")
            print("💡 Running standalone demo instead")
            await demo_basic_seo_content_generation()
            return
        
        # Initialize system components
        try:
            # Mock data flow manager for demo
            class MockDataFlowManager:
                def __init__(self):
                    pass
                
                def store_content_draft(self, draft_data):
                    print(f"📝 Mock: Stored content draft for {draft_data.get('founder_id')}")
                
                def store_seo_optimization_result(self, seo_data):
                    print(f"📊 Mock: Stored SEO result for {seo_data.get('founder_id')}")
            
            data_flow_manager = MockDataFlowManager()
            
            # Initialize SEO service (optional)
            seo_service = None
            try:
                from modules.seo.service_integration import SEOService
                seo_service = SEOService(data_flow_manager, None, None)
                print("✅ SEO service initialized")
            except Exception as e:
                print(f"⚠️ SEO service initialization failed: {e}")
            
            # LLM configuration
            llm_config = {
                'provider': 'openai',
                'api_key': api_key,
                'model_name': 'gpt-3.5-turbo'
            }
            
            # Initialize content service
            content_service = ContentGenerationService(
                data_flow_manager=data_flow_manager,
                seo_service=seo_service,
                llm_config=llm_config
            )
            
            print("✅ System services initialized")
            
        except Exception as e:
            print(f"⚠️ Service initialization failed: {e}")
            return
        
        # Demo content generation with full system
        founder_id = "demo_founder_123"
        
        print(f"\n👤 Generating content for founder: {founder_id}")
        
        # Sample trend and product data
        trend_info = {
            'topic_name': 'AI productivity tools',
            'keywords': ['ai', 'productivity', 'automation', 'efficiency'],
            'pain_points': ['time management', 'workflow optimization'],
            'trend_potential_score': 0.85
        }
        
        product_info = {
            'name': 'ProductivityAI',
            'target_audience': 'busy professionals',
            'core_values': ['efficiency', 'innovation', 'simplicity'],
            'industry_category': 'productivity software'
        }
        
        # Generate content through service
        try:
            generated_content = await content_service.generate_content_with_seo(
                founder_id=founder_id,
                trend_info=trend_info,
                product_info=product_info,
                content_type='tweet'
            )
            
            if generated_content:
                print(f"\n✅ Generated content:")
                print(f"📝 Content: {generated_content.get('content', 'N/A')}")
                print(f"📊 SEO Score: {generated_content.get('seo_score', 0):.2f}")
                print(f"🏷️ Hashtags: {', '.join(generated_content.get('hashtags', []))}")
                print(f"🔑 Keywords: {', '.join(generated_content.get('keywords_used', []))}")
            else:
                print("❌ No content generated")
                
        except Exception as e:
            print(f"⚠️ Content generation failed: {e}")
        
        print("\n✅ System integration demo completed!")
        
    except Exception as e:
        print(f"❌ System integration demo failed: {e}")
        import traceback
        traceback.print_exc()

async def demo_configuration_check():
    """Demo configuration validation"""
    print("\n⚙️ Demo: Configuration Check")
    
    print("🔍 Checking environment configuration...")
    
    # Check .env file existence
    env_file = project_root / '.env'
    if env_file.exists():
        print("✅ .env file found")
    else:
        print("❌ .env file not found")
        print("💡 Create a .env file in the project root with:")
        print("   OPENAI_API_KEY=your_openai_api_key")
        print("   TWITTER_CLIENT_ID=your_twitter_client_id")
        print("   TWITTER_CLIENT_SECRET=your_twitter_client_secret")
    
    # Check OpenAI configuration
    openai_key = get_openai_api_key()
    if openai_key:
        print(f"✅ OpenAI API key configured (length: {len(openai_key)})")
    else:
        print("❌ OpenAI API key not configured")
    
    # Check Twitter configuration
    twitter_creds = get_twitter_credentials()
    configured_creds = [k for k, v in twitter_creds.items() if v]
    if configured_creds:
        print(f"✅ Twitter credentials configured: {', '.join(configured_creds)}")
    else:
        print("❌ No Twitter credentials configured")
    
    # Check required packages
    required_packages = ['openai', 'python-dotenv', 'pydantic']
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} package available")
        except ImportError:
            print(f"❌ {package} package not installed")
            print(f"   Install with: pip install {package}")

async def main():
    """Run all content generation demos"""
    print("🚀 Content Generation Module Demo with SEO Integration")
    print("=" * 60)
    
    # Check configuration first
    await demo_configuration_check()
    
    print("\n" + "=" * 60)
    
    # Run demos
    await demo_basic_seo_content_generation()
    await demo_comprehensive_seo_workflow()
    await demo_system_integration()
    
    print("\n" + "=" * 60)
    print("🎉 Content Generation Demo Completed!")
    
    print("\n📋 Configuration Checklist:")
    print("1. ✅ Create .env file in project root")
    print("2. ✅ Add OPENAI_API_KEY to .env file")
    print("3. ⚠️ Add Twitter API credentials (optional)")
    print("4. ✅ Install required packages: pip install openai python-dotenv pydantic")
    
    print("\n💡 Sample .env file:")
    print("```")
    print("OPENAI_API_KEY=sk-your-openai-api-key-here")
    print("TWITTER_CLIENT_ID=your-twitter-client-id")
    print("TWITTER_CLIENT_SECRET=your-twitter-client-secret")
    print("TWITTER_BEARER_TOKEN=your-twitter-bearer-token")
    print("```")

if __name__ == "__main__":
    asyncio.run(main())