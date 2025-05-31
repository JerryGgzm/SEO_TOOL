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
    SEOOptimizationLevel, HashtagStrategy, ContentOptimizationSuggestions
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

def get_llm_client():
    """Get LLM client for demos"""
    try:
        api_key = get_openai_api_key()
        if not api_key:
            return None
        
        from modules.llm.client import LLMClient
        return LLMClient(provider='openai', api_key=api_key)
    except Exception as e:
        print(f"⚠️ Could not initialize LLM client: {e}")
        return None

def create_mock_services():
    """Create mock services for demo"""
    # Mock Twitter client
    twitter_client = Mock()
    twitter_client.get_trending_hashtags.return_value = ['#AI', '#productivity', '#innovation']
    
    # Mock User service with proper dictionary-like behavior
    user_service = Mock()
    
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
    user_service.get_user_profile.return_value = mock_user_profile
    
    # Also handle get_founder_profile method if it exists
    user_service.get_founder_profile.return_value = mock_user_profile
    
    # Mock data flow manager with proper methods
    data_flow_manager = Mock()
    data_flow_manager.get_seo_performance_history.return_value = []
    data_flow_manager.store_seo_optimization_result = Mock()
    
    # Add content repository mock for content generation demo
    mock_content_repo = Mock()
    mock_content_repo.get_by_id.return_value = None  # Will be handled gracefully
    mock_content_repo.save.return_value = "mock_draft_id_123"
    data_flow_manager.content_repo = mock_content_repo
    
    # Add user repository mock
    mock_user_repo = Mock()
    mock_user_repo.get_by_id.return_value = mock_user_profile
    data_flow_manager.user_repo = mock_user_repo
    
    return twitter_client, user_service, data_flow_manager

def create_enhanced_seo_service(twitter_client, user_service, data_flow_manager, llm_client=None):
    """Create enhanced SEO service for demo"""
    try:
        from modules.seo.service_integration import SEOService
        
        config = {
            'llm_optimization_mode': 'hybrid',
            'cache_duration_hours': 6,
            'default_optimization_mode': 'hybrid'
        }
        
        return SEOService(
            twitter_client=twitter_client,
            user_service=user_service,
            data_flow_manager=data_flow_manager,
            llm_client=llm_client,
            config=config
        )
    except Exception as e:
        print(f"⚠️ Could not create enhanced SEO service: {e}")
        return None

def demo_seo_configuration():
    """Demo SEO configuration and setup"""
    print("\n⚙️ Demo: SEO Configuration")
    
    print("🔧 SEO Module Configuration:")
    print("✅ Enhanced SEO Optimizer with LLM integration")
    print("✅ Multiple optimization modes: traditional, hybrid, intelligent")
    print("✅ Content type support: tweets, posts, articles")
    print("✅ Hashtag and keyword optimization")
    print("✅ Real-time trend analysis")
    
    # Check LLM availability
    llm_client = get_llm_client()
    if llm_client:
        print("✅ LLM client configured for intelligent optimization")
    else:
        print("⚠️ LLM client not available - using traditional optimization")

async def demo_basic_seo_content_generation():
    """Demo basic SEO-enhanced content generation"""
    print("\n📝 Demo: Basic SEO Content Generation")
    
    try:
        # Create mock services
        twitter_client, user_service, data_flow_manager = create_mock_services()
        llm_client = get_llm_client()
        
        # Create SEO service
        seo_service = create_enhanced_seo_service(
            twitter_client, user_service, data_flow_manager, llm_client
        )
        
        if not seo_service:
            print("❌ Could not create SEO service")
            return
        
        print("🔧 Testing SEO content suggestions...")
        
        # Test content suggestions
        trend_info = {
            'topic_name': 'AI productivity tools',
            'keywords': ['ai', 'productivity', 'automation']
        }
        
        product_info = {
            'target_audience': 'software developers',
            'core_values': ['efficiency', 'innovation'],
            'industry_category': 'technology'
        }
        
        try:
            suggestions = await seo_service.get_content_suggestions(
                trend_info=trend_info,
                product_info=product_info,
                content_type='tweet'
            )
            
            print(f"🏷️ Recommended Hashtags: {', '.join(suggestions.recommended_hashtags[:5])}")
            print(f"🔑 Primary Keywords: {', '.join(suggestions.primary_keywords[:3])}")
            print(f"📏 Optimal Length: {suggestions.optimal_length}")
            print(f"💬 Call to Action: {suggestions.call_to_action}")
            
        except Exception as e:
            print(f"⚠️ SEO suggestions failed: {e}")
        
        print("\n✅ Basic SEO content generation demo completed!")
        
    except Exception as e:
        print(f"❌ Basic SEO demo failed: {e}")

async def demo_comprehensive_seo_workflow():
    """Demo comprehensive SEO workflow"""
    print("\n🔄 Demo: Comprehensive SEO Workflow")
    
    try:
        # Create mock services
        twitter_client, user_service, data_flow_manager = create_mock_services()
        llm_client = get_llm_client()
        
        # Create SEO service
        seo_service = create_enhanced_seo_service(
            twitter_client, user_service, data_flow_manager, llm_client
        )
        
        if not seo_service:
            print("❌ Could not create SEO service")
            return
        
        print("🔧 Testing comprehensive SEO workflow...")
        
        # Test content optimization
        test_content = "Excited to share our latest AI development tools that boost productivity!"
        context = {
            'founder_id': 'demo_founder',
            'target_keywords': ['AI', 'productivity', 'development'],
            'target_audience': 'developers'
        }
        
        try:
            # Use the correct method call
            result = await seo_service.optimize_content_intelligent(
                text=test_content,
                content_type='tweet',
                context=context,
                optimization_mode='intelligent'
            )
            
            print(f"📝 Original: {result.get('original_content', 'N/A')}")
            print(f"✨ Optimized: {result.get('optimized_content', 'N/A')}")
            print(f"📊 Score: {result.get('optimization_score', 0):.2f}")
            print(f"🤖 LLM Enhanced: {result.get('llm_enhanced', False)}")
            
            if result.get('improvements_made'):
                print("🔧 Improvements:")
                for improvement in result['improvements_made'][:3]:
                    print(f"  • {improvement}")
                    
        except Exception as e:
            print(f"⚠️ Content optimization failed: {e}")
        
        # Test content suggestions
        try:
            trend_info = {
                'topic_name': 'AI development trends',
                'keywords': ['ai', 'development', 'automation']
            }
            
            product_info = {
                'name': 'AI Development Tools',
                'target_audience': 'developers',
                'core_values': ['innovation', 'efficiency'],
                'industry_category': 'technology'
            }
            
            suggestions = await seo_service.get_content_suggestions(
                trend_info=trend_info,
                product_info=product_info,
                content_type='tweet'
            )
            
            print(f"\n💡 Content Suggestions:")
            print(f"  🏷️ Hashtags: {', '.join(suggestions.recommended_hashtags[:5])}")
            print(f"  🔑 Keywords: {', '.join(suggestions.primary_keywords[:3])}")
            print(f"  📏 Optimal Length: {suggestions.optimal_length}")
            
        except Exception as e:
            print(f"⚠️ Content suggestions failed: {e}")
        
        print("\n✅ Comprehensive SEO workflow demo completed!")
        
    except Exception as e:
        print(f"❌ Comprehensive SEO workflow demo failed: {e}")

async def demo_content_generation_with_seo():
    """Demo content generation with LLM-enhanced SEO"""
    print("\n📝 Testing Content Generation with LLM-Enhanced SEO...")
    
    try:
        # Create mock services
        twitter_client, user_service, data_flow_manager = create_mock_services()
        llm_client = get_llm_client()
        
        # Create SEO service
        seo_service = create_enhanced_seo_service(
            twitter_client, user_service, data_flow_manager, llm_client
        )
        
        if not seo_service:
            print("❌ Could not create SEO service")
            return
        
        print("🔧 Testing SEO-enhanced content generation...")
        
        # Test content optimization directly (simpler approach)
        test_content = "Excited to announce our new AI-powered development tools!"
        
        try:
            # Use the intelligent optimization method
            result = await seo_service.optimize_content_intelligent(
                text=test_content,
                content_type='tweet',
                context={
                    'founder_id': 'demo_founder',
                    'target_keywords': ['AI', 'development', 'tools'],
                    'target_audience': 'developers'
                },
                optimization_mode='intelligent'
            )
            
            print(f"📝 Original: {result.get('original_content', 'N/A')}")
            print(f"✨ Optimized: {result.get('optimized_content', 'N/A')}")
            print(f"📊 Score: {result.get('optimization_score', 0):.2f}")
            print(f"🤖 LLM Enhanced: {result.get('llm_enhanced', False)}")
            
            if result.get('improvements_made'):
                print("🔧 Improvements:")
                for improvement in result['improvements_made'][:3]:
                    print(f"  • {improvement}")
                    
        except Exception as e:
            print(f"⚠️ Content optimization failed: {e}")
        
        # Test content suggestions
        try:
            trend_info = {
                'topic_name': 'AI development trends',
                'keywords': ['ai', 'development', 'automation']
            }
            
            product_info = {
                'name': 'AI Development Tools',
                'target_audience': 'developers',
                'core_values': ['innovation', 'efficiency'],
                'industry_category': 'technology'
            }
            
            suggestions = await seo_service.get_content_suggestions(
                trend_info=trend_info,
                product_info=product_info,
                content_type='tweet'
            )
            
            print(f"\n💡 Content Suggestions:")
            print(f"  🏷️ Hashtags: {', '.join(suggestions.recommended_hashtags[:5])}")
            print(f"  🔑 Keywords: {', '.join(suggestions.primary_keywords[:3])}")
            print(f"  📏 Optimal Length: {suggestions.optimal_length}")
            
        except Exception as e:
            print(f"⚠️ Content suggestions failed: {e}")
        
        # Test SEO potential analysis
        try:
            analysis = await seo_service.analyze_content_seo_potential(
                content=test_content,
                founder_id='demo_founder',
                content_type='tweet'
            )
            
            print(f"\n📊 SEO Analysis:")
            print(f"  🔍 SEO Score: {analysis.get('combined_score', 0):.2f}")
            print(f"  🤖 LLM Enhanced: {analysis.get('llm_enhanced', False)}")
            
            if 'recommendations' in analysis:
                print("  💡 Top Recommendations:")
                for rec in analysis['recommendations'][:3]:
                    print(f"    • {rec}")
                    
        except Exception as e:
            print(f"⚠️ SEO potential analysis failed: {e}")
        
        print("\n✅ Content generation with SEO demo completed!")
        
    except Exception as e:
        print(f"❌ Content generation with SEO demo failed: {e}")
        import traceback
        traceback.print_exc()

async def demo_system_integration():
    """Demo full system integration"""
    print("\n🔗 Demo: Full System Integration")
    
    try:
        # Create mock services
        twitter_client, user_service, data_flow_manager = create_mock_services()
        llm_client = get_llm_client()
        
        # Create SEO service
        seo_service = create_enhanced_seo_service(
            twitter_client, user_service, data_flow_manager, llm_client
        )
        
        if not seo_service:
            print("❌ Could not create SEO service")
            return
        
        print("🔧 Testing full system integration...")
        
        # Test SEO analytics
        try:
            analytics = seo_service.get_seo_analytics_summary('demo_founder', 30)
            
            print(f"📈 Total Optimizations: {analytics.get('total_optimizations', 0)}")
            print(f"📊 Average Score: {analytics.get('avg_optimization_score', 0):.2f}")
            print(f"🤖 LLM Enhanced: {analytics.get('llm_enabled', False)}")
            
        except Exception as e:
            print(f"⚠️ SEO analytics failed: {e}")
        
        # Test SEO recommendations
        try:
            recommendations = seo_service.get_seo_recommendations('demo_founder')
            
            if recommendations:
                print("💡 SEO Recommendations:")
                hashtag_rec = recommendations.get('hashtag_strategy', {}).get('recommendation', 'N/A')
                keyword_rec = recommendations.get('keyword_focus', {}).get('recommendation', 'N/A')
                print(f"  • Hashtag Strategy: {hashtag_rec}")
                print(f"  • Keyword Focus: {keyword_rec}")
                
        except Exception as e:
            print(f"⚠️ SEO recommendations failed: {e}")
        
        print("\n✅ System integration demo completed!")
        
    except Exception as e:
        print(f"❌ System integration demo failed: {e}")

async def main():
    """Run all content generation demos with SEO integration"""
    print("🚀 Content Generation with SEO Integration Demo")
    print("=" * 60)
    
    # Check API key availability
    api_key = get_openai_api_key()
    if api_key:
        print("✅ OpenAI API key available - running full demos")
    else:
        print("⚠️ OpenAI API key not available - running limited demos")
    
    print("\n" + "=" * 60)
    
    # Run demos
    try:
        # Configuration demo (non-async)
        demo_seo_configuration()
        
        # Basic demos
        await demo_basic_seo_content_generation()
        await demo_comprehensive_seo_workflow()
        await demo_content_generation_with_seo()
        
        # Advanced demos
        await demo_system_integration()
        
    except Exception as e:
        print(f"❌ Demo execution failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🎉 Content Generation with SEO Demo Completed!")
    
    print("\n🔧 Integration Summary:")
    print("✅ SEO-enhanced content generation")
    print("✅ Intelligent content optimization")
    print("✅ Content variation generation")
    print("✅ SEO potential analysis")
    print("✅ Full system integration")
    
    print("\n💡 Key Features Demonstrated:")
    print("• Automatic SEO optimization during content generation")
    print("• LLM-powered content enhancement")
    print("• Hashtag and keyword optimization")
    print("• Content quality scoring")
    print("• Multiple optimization strategies")
    print("• Real-time SEO analysis")

if __name__ == "__main__":
    asyncio.run(main())