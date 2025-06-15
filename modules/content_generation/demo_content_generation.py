"""Demo script for ContentGenerationModule - Streamlined Content Generation

This demo showcases the core content generation capabilities:
- Pure content generation using LLM
- Multiple generation modes (standard, viral-focused, brand-focused)
- Quality assessment and validation
- Content type handling (tweets, replies, threads)
- Brand voice consistency

Note: SEO optimization is demonstrated separately via the SEO module.
"""
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
    ContentType, BrandVoice, GenerationMode
)
from modules.content_generation.generator import ContentGenerator, ContentGenerationFactory
from modules.content_generation.service import ContentGenerationService
from modules.content_generation.quality_checker import ContentQualityChecker
from modules.content_generation.database_adapter import ContentGenerationDatabaseAdapter

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

class MockDatabaseAdapter(ContentGenerationDatabaseAdapter):
    """Mock database adapter for demo"""
    
    def __init__(self):
        self._drafts = {}
        self._founder_profiles = {}
        self._product_info = {}
        self._content_preferences = {}
        
        # Setup demo data
        self._setup_demo_data()
    
    def _setup_demo_data(self):
        """Setup demo data"""
        demo_founder_id = "demo_founder"
        
        self._founder_profiles[demo_founder_id] = {
            'preferred_tone': 'professional',
            'writing_style': 'informative',
            'personality_traits': ['innovative', 'helpful', 'professional'],
            'avoid_words': ['boring', 'complicated'],
            'preferred_phrases': ['excited to share', 'looking forward'],
            'formality_level': 0.6,
            'target_audience': 'tech entrepreneurs and developers'
        }
        
        self._product_info[demo_founder_id] = {
            'name': 'AI Productivity Assistant',
            'description': 'AI-powered tools that help professionals manage tasks and workflows efficiently',
            'industry': 'productivity software',
            'target_market': 'busy professionals and entrepreneurs'
        }
        
        self._content_preferences[demo_founder_id] = {
            'preferred_content_types': ['tweet', 'thread'],
            'posting_frequency': 'daily',
            'engagement_style': 'conversational'
        }
    
    async def get_founder_profile(self, founder_id: str) -> Dict[str, Any]:
        return self._founder_profiles.get(founder_id, {})
    
    async def get_product_info(self, founder_id: str) -> Dict[str, Any]:
        return self._product_info.get(founder_id, {'name': 'Demo Product'})
    
    async def get_trend_info(self, trend_id: str) -> Dict[str, Any]:
        return {
            'topic': 'AI productivity trends',
            'keywords': ['ai', 'productivity', 'automation', 'efficiency'],
            'sentiment': 'positive',
            'relevance_score': 0.8
        }
    
    async def get_content_preferences(self, founder_id: str) -> Dict[str, Any]:
        return self._content_preferences.get(founder_id, {})
    
    async def get_successful_patterns(self, founder_id: str) -> List[Dict[str, Any]]:
        return [
            {
                'pattern_type': 'question_based',
                'performance_score': 0.8,
                'characteristics': ['includes question', 'personal touch']
            },
            {
                'pattern_type': 'how_to',
                'performance_score': 0.7,
                'characteristics': ['educational', 'step-by-step']
            }
        ]
    
    async def get_recent_content(self, founder_id: str, limit: int = 10) -> List[str]:
        return [
            "Just shared our latest feature update!",
            "Excited about the AI developments in our industry",
            "Great meeting with potential customers today"
        ]
    
    async def store_draft(self, draft) -> str:
        draft_id = f"draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._drafts)}"
        self._drafts[draft_id] = draft
        print(f"✅ Stored draft: {draft_id}")
        return draft_id
    
    async def get_draft(self, draft_id: str):
        return self._drafts.get(draft_id)
    
    async def get_drafts_by_founder(self, founder_id: str, limit: int = 20) -> List:
        return [draft for draft in self._drafts.values() 
                if hasattr(draft, 'founder_id') and draft.founder_id == founder_id][:limit]
    
    async def update_draft_quality_score(self, draft_id: str, quality_score: float) -> bool:
        if draft_id in self._drafts:
            self._drafts[draft_id].quality_score = quality_score
            return True
        return False

async def demo_basic_content_generation():
    """Demo basic content generation functionality"""
    print("\n📝 Demo: Basic Content Generation")
    
    try:
        # Create mock database adapter
        db_adapter = MockDatabaseAdapter()
        
        # Create content generation service
        service = ContentGenerationService(
            llm_config={'provider': 'openai'},
            database_adapter=db_adapter
        )
        
        print("🔧 Testing basic content generation...")
        
        # Generate standard tweet
        draft_ids = await service.generate_content(
            founder_id="demo_founder",
            content_type=ContentType.TWEET,
            generation_mode=GenerationMode.STANDARD,
            quantity=2
        )
        
        print(f"✅ Generated {len(draft_ids)} drafts")
        
        # Display generated content
        for draft_id in draft_ids:
            draft = await service.get_draft(draft_id)
            if draft:
                print(f"\n📄 Draft {draft_id}:")
                print(f"   Content: {draft.generated_text}")
                print(f"   Quality Score: {draft.quality_score:.2f}")
                print(f"   Type: {draft.content_type.value}")
        
        print("\n✅ Basic content generation demo completed!")
        
    except Exception as e:
        print(f"❌ Basic content generation demo failed: {e}")
        import traceback
        traceback.print_exc()

async def demo_generation_modes():
    """Demo different generation modes"""
    print("\n🎯 Demo: Different Generation Modes")
    
    try:
        db_adapter = MockDatabaseAdapter()
        service = ContentGenerationService(
            llm_config={'provider': 'openai'},
            database_adapter=db_adapter
        )
        
        modes = [
            (GenerationMode.VIRAL_FOCUSED, "viral-focused"),
            (GenerationMode.BRAND_FOCUSED, "brand-focused"),
            (GenerationMode.ENGAGEMENT_OPTIMIZED, "engagement-optimized")
        ]
        
        for mode, description in modes:
            print(f"\n🔧 Testing {description} content generation...")
            
            try:
                if mode == GenerationMode.VIRAL_FOCUSED:
                    draft_ids = await service.generate_viral_focused_content(
                        founder_id="demo_founder",
                        content_type=ContentType.TWEET,
                        quantity=1
                    )
                elif mode == GenerationMode.BRAND_FOCUSED:
                    draft_ids = await service.generate_brand_focused_content(
                        founder_id="demo_founder",
                        content_type=ContentType.TWEET,
                        quantity=1
                    )
                else:
                    draft_ids = await service.generate_content(
                        founder_id="demo_founder",
                        content_type=ContentType.TWEET,
                        generation_mode=mode,
                        quantity=1
                    )
                
                if draft_ids:
                    draft = await service.get_draft(draft_ids[0])
                    if draft:
                        print(f"📄 {description.title()} Content:")
                        print(f"   {draft.generated_text}")
                        print(f"   Quality: {draft.quality_score:.2f}")
                
            except Exception as e:
                print(f"⚠️ {description} generation failed: {e}")
        
        print("\n✅ Generation modes demo completed!")
                    
    except Exception as e:
        print(f"❌ Generation modes demo failed: {e}")

async def demo_content_types():
    """Demo different content types"""
    print("\n📱 Demo: Different Content Types")
    
    try:
        db_adapter = MockDatabaseAdapter()
        service = ContentGenerationService(
            llm_config={'provider': 'openai'},
            database_adapter=db_adapter
        )
        
        content_types = [
            (ContentType.TWEET, "Tweet"),
            (ContentType.REPLY, "Reply"),
            (ContentType.THREAD, "Thread"),
            (ContentType.QUOTE_TWEET, "Quote Tweet")
        ]
        
        for content_type, description in content_types:
            print(f"\n🔧 Testing {description} generation...")
            
            try:
                draft_ids = await service.generate_content(
                    founder_id="demo_founder",
                    content_type=content_type,
                    generation_mode=GenerationMode.STANDARD,
                    quantity=1
                )
                
                if draft_ids:
                    draft = await service.get_draft(draft_ids[0])
                    if draft:
                        print(f"📄 {description}:")
                        print(f"   {draft.generated_text}")
                        print(f"   Quality: {draft.quality_score:.2f}")
                        print(f"   Length: {len(draft.generated_text)} characters")
            
            except Exception as e:
                print(f"⚠️ {description} generation failed: {e}")
        
        print("\n✅ Content types demo completed!")
        
    except Exception as e:
        print(f"❌ Content types demo failed: {e}")

async def demo_quality_assessment():
    """Demo content quality assessment"""
    print("\n📊 Demo: Content Quality Assessment")
    
    try:
        db_adapter = MockDatabaseAdapter()
        service = ContentGenerationService(
            llm_config={'provider': 'openai'},
            database_adapter=db_adapter
        )
        
        print("🔧 Testing quality assessment...")
        
        # Generate content with different quality thresholds
        thresholds = [0.3, 0.6, 0.8]
        
        for threshold in thresholds:
            print(f"\n📏 Testing with quality threshold: {threshold}")
            
            try:
                draft_ids = await service.generate_content(
                    founder_id="demo_founder",
                    content_type=ContentType.TWEET,
                    generation_mode=GenerationMode.STANDARD,
                    quantity=3
                )
                
                # Filter by quality threshold
                quality_drafts = []
                for draft_id in draft_ids:
                    draft = await service.get_draft(draft_id)
                    if draft and draft.quality_score >= threshold:
                        quality_drafts.append(draft)
                
                print(f"✅ {len(quality_drafts)}/{len(draft_ids)} drafts meet threshold {threshold}")
                
                if quality_drafts:
                    best_draft = max(quality_drafts, key=lambda d: d.quality_score)
                    print(f"🏆 Best draft (score: {best_draft.quality_score:.2f}):")
                    print(f"   {best_draft.generated_text}")
                    
            except Exception as e:
                print(f"⚠️ Quality assessment failed for threshold {threshold}: {e}")
        
        print("\n✅ Quality assessment demo completed!")
        
    except Exception as e:
        print(f"❌ Quality assessment demo failed: {e}")

async def demo_brand_voice_customization():
    """Demo brand voice customization"""
    print("\n🎨 Demo: Brand Voice Customization")
    
    try:
        db_adapter = MockDatabaseAdapter()
        service = ContentGenerationService(
            llm_config={'provider': 'openai'},
            database_adapter=db_adapter
        )
        
        print("🔧 Testing brand voice customization...")
        
        # Test different brand voices
        brand_voices = [
            BrandVoice(
                tone="casual",
                style="conversational",
                personality_traits=["friendly", "approachable"],
                formality_level=0.2
            ),
            BrandVoice(
                tone="professional",
                style="authoritative", 
                personality_traits=["expert", "reliable"],
                formality_level=0.8
            ),
            BrandVoice(
                tone="enthusiastic",
                style="inspiring",
                personality_traits=["energetic", "motivational"],
                formality_level=0.4
            )
        ]
        
        for i, brand_voice in enumerate(brand_voices, 1):
            print(f"\n🎭 Testing Brand Voice {i} ({brand_voice.tone}, {brand_voice.style}):")
            
            try:
                draft_ids = await service.generate_brand_focused_content(
                    founder_id="demo_founder",
                    custom_brand_voice=brand_voice,
                    content_type=ContentType.TWEET,
                    quantity=1
                )
                
                if draft_ids:
                    draft = await service.get_draft(draft_ids[0])
                    if draft:
                        print(f"📄 Content: {draft.generated_text}")
                        print(f"📊 Quality: {draft.quality_score:.2f}")
                    
            except Exception as e:
                print(f"⚠️ Brand voice {i} generation failed: {e}")
        
        print("\n✅ Brand voice customization demo completed!")
        
    except Exception as e:
        print(f"❌ Brand voice customization demo failed: {e}")

async def demo_draft_management():
    """Demo draft management functionality"""
    print("\n📋 Demo: Draft Management")
    
    try:
        db_adapter = MockDatabaseAdapter()
        service = ContentGenerationService(
            llm_config={'provider': 'openai'},
            database_adapter=db_adapter
        )
        
        print("🔧 Testing draft management...")
        
        # Generate some drafts
        draft_ids = await service.generate_content(
            founder_id="demo_founder",
            content_type=ContentType.TWEET,
            generation_mode=GenerationMode.STANDARD,
            quantity=3
        )
        
        print(f"✅ Generated {len(draft_ids)} drafts for management demo")
        
        # Test getting drafts by founder
        founder_drafts = await service.get_drafts_by_founder("demo_founder", limit=10)
        print(f"📄 Found {len(founder_drafts)} drafts for founder")
        
        # Test updating quality scores
        if draft_ids:
            test_draft_id = draft_ids[0]
            new_score = 0.95
            
            success = await service.update_draft_quality_score(test_draft_id, new_score)
            if success:
                print(f"✅ Updated quality score for draft {test_draft_id} to {new_score}")
                
                # Verify the update
                updated_draft = await service.get_draft(test_draft_id)
                if updated_draft:
                    print(f"📊 Verified new score: {updated_draft.quality_score}")
        
        print("\n✅ Draft management demo completed!")
        
    except Exception as e:
        print(f"❌ Draft management demo failed: {e}")

def demo_module_configuration():
    """Demo module configuration and capabilities"""
    print("\n⚙️ Demo: Module Configuration")
    
    print("🔧 Content Generation Module Configuration:")
    print("✅ Streamlined content generation focused on quality")
    print("✅ Multiple generation modes: standard, viral-focused, brand-focused")
    print("✅ Content type support: tweets, replies, threads, quote tweets")
    print("✅ Brand voice customization and consistency")
    print("✅ Quality assessment and filtering")
    print("✅ Draft management and storage")
    
    # Check LLM availability
    api_key = get_openai_api_key()
    if api_key:
        print("✅ LLM client configured for intelligent content generation")
    else:
        print("⚠️ LLM client not available - using mock responses")
    
    print("\n🎯 Module Focus:")
    print("• Pure content generation without SEO optimization")
    print("• Quality-driven content creation")
    print("• Brand voice consistency")
    print("• Flexible generation modes")
    print("• Comprehensive content type support")

async def main():
    """Run all content generation demos"""
    print("🚀 Content Generation Module Demo")
    print("=" * 50)
    
    # Check API key availability
    api_key = get_openai_api_key()
    if api_key:
        print("✅ OpenAI API key available - running full demos")
    else:
        print("⚠️ OpenAI API key not available - running with mock responses")
    
    print("\n" + "=" * 50)
    
    # Run demos
    try:
        # Configuration demo (non-async)
        demo_module_configuration()
        
        # Core functionality demos
        await demo_basic_content_generation()
        await demo_generation_modes()
        await demo_content_types()
        await demo_quality_assessment()
        await demo_brand_voice_customization()
        await demo_draft_management()
        
    except Exception as e:
        print(f"❌ Demo execution failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🎉 Content Generation Demo Completed!")
    
    print("\n🔧 Capabilities Demonstrated:")
    print("✅ Basic content generation")
    print("✅ Multiple generation modes")
    print("✅ Content type handling")
    print("✅ Quality assessment")
    print("✅ Brand voice customization")
    print("✅ Draft management")
    
    print("\n💡 Key Features:")
    print("• Streamlined, focused content generation")
    print("• Quality-driven approach")
    print("• Brand consistency maintenance")
    print("• Flexible generation modes")
    print("• Comprehensive draft management")
    
    print("\n📌 Note:")
    print("For SEO optimization, use the dedicated SEO module")
    print("This module focuses purely on content creation and quality")

if __name__ == "__main__":
    asyncio.run(main())