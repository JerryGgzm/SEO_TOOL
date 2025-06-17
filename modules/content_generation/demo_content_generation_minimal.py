"""Minimal demo script for ContentGenerationModule - Focused on token efficiency

This demo showcases basic content generation with minimal token usage.
"""
import asyncio
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import content generation models and services
from modules.content_generation.models import (
    ContentGenerationRequest, ContentGenerationContext, 
    ContentType, BrandVoice, GenerationMode
)
from modules.content_generation.generator import ContentGenerator
from modules.content_generation.service import ContentGenerationService
from modules.content_generation.quality_checker import ContentQualityChecker
from modules.content_generation.database_adapter import ContentGenerationDatabaseAdapter
from modules.content_generation.llm_adapter import LLMAdapterFactory
from config.llm_config import LLM_CONFIG, DEFAULT_LLM_PROVIDER

# Load environment variables
load_dotenv()

def print_section(title: str):
    """Print a section header"""
    print(f"\n{'=' * 50}")
    print(f"📌 {title}")
    print(f"{'=' * 50}")

def print_json(data: Dict[str, Any], title: str = None):
    """Print JSON data in a formatted way"""
    if title:
        print(f"\n📋 {title}:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

class MinimalMockDatabaseAdapter(ContentGenerationDatabaseAdapter):
    """Minimal mock database adapter for token-efficient demo"""
    
    def __init__(self):
        self._drafts = {}
        self._founder_profiles = {}
        self._product_info = {}
        self._content_preferences = {}
        
        # Setup minimal demo data
        self._setup_demo_data()
    
    def _setup_demo_data(self):
        """Setup minimal demo data"""
        demo_founder_id = "demo_founder"
        
        # Simplified founder profile
        self._founder_profiles[demo_founder_id] = {
            'preferred_tone': 'professional',
            'target_audience': 'developers'
        }
        
        # Minimal product info
        self._product_info[demo_founder_id] = {
            'name': 'AI Tool',
            'description': 'Developer productivity tool'
        }
        
        # Basic content preferences
        self._content_preferences[demo_founder_id] = {
            'preferred_content_types': ['tweet']
        }
        
        print_section("Demo Data Setup")
        print_json(self._founder_profiles[demo_founder_id], "Founder Profile")
        print_json(self._product_info[demo_founder_id], "Product Info")
        print_json(self._content_preferences[demo_founder_id], "Content Preferences")
    
    async def get_founder_profile(self, founder_id: str) -> Dict[str, Any]:
        profile = self._founder_profiles.get(founder_id, {})
        print(f"\n🔍 Retrieved founder profile for {founder_id}")
        return profile
    
    async def get_product_info(self, founder_id: str) -> Dict[str, Any]:
        info = self._product_info.get(founder_id, {'name': 'Demo Product'})
        print(f"\n🔍 Retrieved product info for {founder_id}")
        return info
    
    async def get_trend_info(self, trend_id: str) -> Dict[str, Any]:
        info = {
            'topic': 'AI tools',
            'keywords': ['ai', 'productivity']
        }
        print(f"\n🔍 Retrieved trend info")
        return info
    
    async def get_content_preferences(self, founder_id: str) -> Dict[str, Any]:
        prefs = self._content_preferences.get(founder_id, {})
        print(f"\n🔍 Retrieved content preferences for {founder_id}")
        return prefs
    
    async def get_successful_patterns(self, founder_id: str) -> List[Dict[str, Any]]:
        patterns = [{
            'pattern_type': 'question_based',
            'performance_score': 0.8
        }]
        print(f"\n🔍 Retrieved successful patterns for {founder_id}")
        return patterns
    
    async def get_recent_content(self, founder_id: str, limit: int = 10) -> List[str]:
        content = ["Just shared our latest feature!"]
        print(f"\n🔍 Retrieved recent content for {founder_id}")
        return content
    
    async def store_draft(self, draft) -> str:
        draft_id = f"draft_{len(self._drafts)}"
        self._drafts[draft_id] = draft
        print(f"\n💾 Stored draft {draft_id}:")
        print(f"   Content: {draft.generated_text}")
        print(f"   Quality Score: {draft.quality_score:.2f}")
        if hasattr(draft, 'generation_metadata'):
            print_json(draft.generation_metadata, "Generation Metadata")
        return draft_id
    
    async def get_draft(self, draft_id: str):
        draft = self._drafts.get(draft_id)
        if draft:
            print(f"\n📄 Retrieved draft {draft_id}")
        return draft
    
    async def get_drafts_by_founder(self, founder_id: str, limit: int = 20) -> List:
        drafts = [draft for draft in self._drafts.values() 
                 if hasattr(draft, 'founder_id') and draft.founder_id == founder_id][:limit]
        print(f"\n📚 Retrieved {len(drafts)} drafts for founder {founder_id}")
        return drafts

async def demo_minimal_content_generation():
    """Demo minimal content generation functionality"""
    print_section("Minimal Content Generation Demo")
    
    try:
        # Create mock database adapter
        db_adapter = MinimalMockDatabaseAdapter()
        
        # Create content generation service
        service = ContentGenerationService(
            data_flow_manager=None,
            user_service=None,
            llm_provider='gemini'
        )
        
        print("\n⚙️ Service Configuration:")
        print(f"   LLM Provider: Gemini")
        print(f"   Model: {LLM_CONFIG['gemini']['model_name']}")
        
        print("\n🔧 Starting content generation...")
        
        # Generate single tweet with minimal context
        draft_ids = await service.generate_content(
            founder_id="demo_founder",
            content_type=ContentType.TWEET,
            generation_mode=GenerationMode.STANDARD,
            quantity=1  # Generate only one tweet
        )
        
        print(f"\n✅ Generated {len(draft_ids)} drafts")
        
        # Display generated content
        for draft_id in draft_ids:
            draft = await service.get_draft(draft_id)
            if draft:
                print_section(f"Draft {draft_id}")
                print(f"📝 Content: {draft.generated_text}")
                print(f"📊 Quality Score: {draft.quality_score:.2f}")
                if hasattr(draft, 'generation_metadata'):
                    print_json(draft.generation_metadata, "Generation Metadata")
        
        print("\n✅ Minimal content generation demo completed!")
        
    except Exception as e:
        print(f"\n❌ Minimal content generation demo failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run minimal demo"""
    print_section("Starting Minimal Content Generation Demo")
    
    # Run minimal demo
    await demo_minimal_content_generation()
    
    print("\n✨ Demo completed!")

if __name__ == "__main__":
    asyncio.run(main()) 