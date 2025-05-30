"""Demo script for ContentGenerationModule"""
import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from modules.content_generation.models import (
    ContentGenerationRequest, ContentGenerationContext, 
    ContentType, BrandVoice, SEOSuggestions
)
from modules.content_generation.generator import ContentGenerationFactory
from modules.content_generation.quality_checker import ContentQualityChecker
from modules.content_generation.prompts import PromptEngine

# Load environment variables
load_dotenv()

async def demo_basic_content_generation():
    """Demo basic content generation"""
    print("🎯 Demo: Basic Content Generation")
    
    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'your-openai-api-key-here':
        print("⚠️ Please set OPENAI_API_KEY in .env file")
        return
    
    try:
        # Create content generator
        generator = ContentGenerationFactory.create_generator(
            'openai',
            {'api_key': api_key, 'model_name': 'gpt-3.5-turbo'}
        )
        
        # Create test request
        request = ContentGenerationRequest(
            founder_id="demo-founder",
            content_type=ContentType.TWEET,
            quantity=2,
            quality_threshold=0.3  # Lower threshold for demo
        )
        
        # Create test context
        context = ContentGenerationContext(
            founder_id="demo-founder",
            product_info={
                'name': 'AI Productivity Assistant',
                'description': 'Helps professionals manage tasks and workflows',
                'core_values': ['efficiency', 'innovation', 'simplicity'],
                'industry_category': 'productivity software'
            },
            brand_voice=BrandVoice(
                tone="professional",
                style="helpful",
                personality_traits=["innovative", "reliable"]
            ),
            target_audience="busy professionals and entrepreneurs",
            trend_info={
                'topic_name': 'AI productivity tools',
                'pain_points': ['information overload', 'task management', 'workflow efficiency'],
                'questions': ['How to be more productive?', 'Best AI tools for work?']
            }
        )
        
        print("🤖 Generating content...")
        drafts = await generator.generate_content(request, context)
        
        print(f"\n✅ Generated {len(drafts)} content drafts:")
        for i, draft in enumerate(drafts, 1):
            print(f"\n--- Draft {i} ---")
            print(f"Content: {draft.generated_text}")
            print(f"Type: {draft.content_type.value}")
            if draft.quality_score:
                print(f"Quality Score: {draft.quality_score.overall_score:.2f}")
                print(f"Engagement Prediction: {draft.quality_score.engagement_prediction:.2f}")
            if draft.seo_suggestions.hashtags:
                print(f"Suggested Hashtags: {', '.join(draft.seo_suggestions.hashtags)}")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

def demo_prompt_engineering():
    """Demo prompt engineering"""
    print("\n🎯 Demo: Prompt Engineering")
    
    engine = PromptEngine()
    
    # Create test context
    context = ContentGenerationContext(
        founder_id="demo-founder",
        product_info={
            'name': 'EcoTracker',
            'description': 'Sustainability tracking app',
            'core_values': ['environmental responsibility', 'transparency']
        },
        brand_voice=BrandVoice(tone="inspiring", style="educational"),
        target_audience="environmentally conscious consumers",
        trend_info={
            'topic_name': 'sustainable living',
            'pain_points': ['tracking carbon footprint', 'sustainable choices'],
            'questions': ['How to live more sustainably?']
        }
    )
    
    # Generate different types of prompts
    tweet_prompt = engine.generate_prompt(ContentType.TWEET, context)
    reply_prompt = engine.generate_prompt(ContentType.REPLY, context)
    
    print("📝 Generated Tweet Prompt:")
    print(tweet_prompt[:3000] + "..." if len(tweet_prompt) > 3000 else tweet_prompt)
    
    print("\n📝 Generated Reply Prompt:")
    print(reply_prompt[:3000] + "..." if len(reply_prompt) > 3000 else reply_prompt)

async def demo_quality_assessment():
    """Demo content quality assessment"""
    print("\n🎯 Demo: Quality Assessment")
    
    checker = ContentQualityChecker()
    
    # Test different content samples
    test_contents = [
        {
            'text': "Excited to share our new AI feature! It helps you save 2 hours daily. What's your biggest productivity challenge? #AI #ProductivityHack",
            'description': "High-quality tweet"
        },
        {
            'text': "BUY NOW!!! AMAZING DEAL!!! LIMITED TIME ONLY!!! 🔥🔥🔥",
            'description': "Low-quality promotional tweet"
        },
        {
            'text': "AI is good",
            'description': "Too short tweet"
        }
    ]
    
    context = ContentGenerationContext(
        founder_id="demo-founder",
        brand_voice=BrandVoice(tone="professional", avoid_words=["buy now"]),
        trend_info={'topic_name': 'AI productivity'}
    )
    
    for content in test_contents:
        from modules.content_generation.models import ContentDraft
        draft = ContentDraft(
            founder_id="demo-founder",
            content_type=ContentType.TWEET,
            generated_text=content['text'],
            seo_suggestions=SEOSuggestions()
        )
        
        quality_score = await checker.assess_quality(draft, context)
        
        print(f"\n--- {content['description']} ---")
        print(f"Content: {content['text']}")
        print(f"Overall Score: {quality_score.overall_score:.2f}")
        print(f"Engagement: {quality_score.engagement_prediction:.2f}")
        print(f"Brand Alignment: {quality_score.brand_alignment:.2f}")
        if quality_score.issues:
            print(f"Issues: {', '.join(quality_score.issues)}")

def demo_content_types():
    """Demo different content types"""
    print("\n🎯 Demo: Content Type Handling")
    
    from modules.content_generation.content_types import ContentTypeFactory
    
    # Test different content types
    content_samples = [
        (ContentType.TWEET, "Great insights on AI innovation! What's your take on the future of automation? #AI #Future"),
        (ContentType.REPLY, "Thanks for sharing this! I completely agree that AI will transform how we work. Have you tried any AI tools recently?"),
        (ContentType.THREAD, """The future of AI in business is incredibly exciting. Here's what I see happening:

First, AI will automate routine tasks, freeing up humans for creative work.

Second, personalized customer experiences will become the norm.

Third, decision-making will be enhanced with real-time data insights.

What trends are you seeing in your industry?""")
    ]
    
    for content_type, text in content_samples:
        print(f"\n--- {content_type.value.title()} Content ---")
        print(f"Original: {text[:1000]}{'...' if len(text) > 1000 else ''}")
        
        handler = ContentTypeFactory.create_handler(content_type)
        is_valid, issues = handler.validate_content(text)
        
        print(f"Valid: {is_valid}")
        if issues:
            print(f"Issues: {', '.join(issues)}")
        
        # Test optimization
        seo_suggestions = SEOSuggestions(hashtags=['AI', 'innovation'])
        optimized = handler.optimize_for_platform(text, seo_suggestions)
        
        if optimized != text:
            print(f"Optimized: {optimized[:1000]}{'...' if len(optimized) > 1000 else ''}")

async def main():
    """Run all demos"""
    print("🚀 ContentGenerationModule Demo\n")
    
    # Run demos
    await demo_basic_content_generation()
    demo_prompt_engineering()
    await demo_quality_assessment()
    demo_content_types()
    
    print("\n🎉 Demo completed!")
    print("\nTo run with your own API keys:")
    print("1. Set OPENAI_API_KEY in .env file")
    print("2. Run: python -m modules.content_generation.demo")

if __name__ == "__main__":
    asyncio.run(main())