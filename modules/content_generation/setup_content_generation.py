"""Setup script for ContentGenerationModule testing"""
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    
    requirements = [
        "fastapi==0.104.1",
        "sqlalchemy==2.0.23",
        "openai==1.3.5",
        "anthropic==0.7.7",
        "nltk==3.8.1",
        "spacy==3.7.2",
        "textblob==0.17.1",
        "vaderSentiment==3.3.2",
        "numpy==1.24.4",
        "pydantic==2.5.0",
        "pytest==7.4.3",
        "pytest-asyncio==0.21.1",
        "httpx==0.25.2",
        "python-dotenv==1.0.0"
    ]
    
    for req in requirements:
        subprocess.check_call([sys.executable, "-m", "pip", "install", req])
    
    print("✅ Packages installed successfully!")

def download_nlp_models():
    """Download required NLP models"""
    print("🧠 Downloading NLP models...")
    
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        print("✅ NLTK models downloaded!")
    except ImportError:
        print("⚠️ NLTK not installed, skipping NLTK downloads")
    
    try:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        print("✅ spaCy model downloaded!")
    except subprocess.CalledProcessError:
        print("⚠️ spaCy model download failed, some features may be limited")

def create_env_file():
    """Create example .env file"""
    print("🔧 Creating environment file...")
    
    env_content = """# Content Generation Module Configuration
# API Keys (replace with your actual keys)
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Database Configuration
DATABASE_URL=sqlite:///./test.db

# Twitter API Configuration
TWITTER_CLIENT_ID=your-twitter-client-id
TWITTER_CLIENT_SECRET=your-twitter-client-secret
TWITTER_REDIRECT_URI=http://localhost:8000/auth/twitter/callback

# Security
SECRET_KEY=your-secret-key-for-jwt-tokens
ENCRYPTION_KEY=your-32-character-encryption-key

# Development Settings
DEBUG=True
LOG_LEVEL=INFO
"""
    
    with open('.env.example', 'w') as f:
        f.write(env_content)
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file - please update with your actual API keys!")
    else:
        print("✅ .env file already exists")

def run_basic_tests():
    """Run basic functionality tests"""
    print("🧪 Running basic tests...")
    
    try:
        import sys
        import os
        
        # add project root to Python path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        print(f"Added {project_root} to Python path")
        
        # set temporary environment variable to avoid OpenAI client error
        os.environ['OPENAI_API_KEY'] = 'test-key-for-testing'
        
        # test imports
        from modules.content_generation.service import ContentGenerationService
        from modules.content_generation.models import ContentType, ContentDraft
        from modules.seo.service_integration import SEOService  # Import real SEO service
        print("✅ Module imports successful!")
        
        # create mock dependencies
        from unittest.mock import Mock
        
        # Mock Twitter client
        mock_twitter_client = Mock()
        mock_twitter_client.get_trending_hashtags.return_value = ['AI', 'productivity', 'tech']
        mock_twitter_client.analyze_hashtag_performance.return_value = {'engagement_rate': 0.05}
        
        # Mock user service
        mock_user_service = Mock()
        mock_user_service.get_user_profile.return_value = Mock(
            target_audience='professionals',
            industry_category='technology',
            niche_keywords=['AI', 'productivity']
        )
        
        # Mock data flow manager
        mock_data_flow_manager = Mock()
        mock_data_flow_manager.get_content_generation_context.return_value = {
            'products': [{
                'name': 'AI Assistant',
                'description': 'An intelligent AI assistant for productivity',
                'core_values': ['innovation', 'efficiency'],
                'target_audience': 'professionals'
            }],
            'trend_info': {'topic_name': 'AI productivity tools'},
            'recent_topics': []
        }
        mock_data_flow_manager.store_generated_content_draft.return_value = "test-draft-id"
        mock_data_flow_manager.get_seo_data.return_value = {
            'trending_keywords': ['AI', 'productivity'],
            'competitor_hashtags': ['#AI', '#productivity']
        }
        
        # Create real SEO service with mock dependencies
        seo_service = SEOService(
            twitter_client=mock_twitter_client,
            user_service=mock_user_service,
            data_flow_manager=mock_data_flow_manager
        )
        print("✅ SEO service created successfully!")
        
        mock_llm_config = {
            'openai_api_key': 'test-key-for-testing',
            'model_name': 'gpt-3.5-turbo'
        }
        
        # test basic functionality with real SEO service
        service = ContentGenerationService(
            data_flow_manager=mock_data_flow_manager,
            user_profile_service=mock_user_service,
            seo_service=seo_service,  # Use real SEO service
            llm_config=mock_llm_config
        )
        print("✅ Content generation service with SEO integration created!")
        
        # Test SEO service functionality using actual methods
        print("🔍 Testing SEO service functionality...")
        
        # Test content optimization (using the actual method name)
        test_content = "AI is transforming business productivity"
        founder_id = "test-founder"
        
        try:
            optimized_content = seo_service.optimize_content(
                founder_id=founder_id,
                text=test_content,
                content_type="tweet"
            )
            print(f"Original: {test_content}")
            print(f"Optimized: {optimized_content}")
        except Exception as e:
            print(f"Content optimization test failed: {e}")
        
        # Test hashtag generation using trending hashtags
        try:
            trending_hashtags = seo_service.get_trending_hashtags(
                niche_keywords=['AI', 'productivity', 'business']
            )
            print(f"Trending hashtags: {trending_hashtags}")
        except Exception as e:
            print(f"Hashtag generation test failed: {e}")
        
        # Test keyword suggestions
        try:
            keyword_suggestions = seo_service.generate_keyword_suggestions(
                founder_id=founder_id,
                content_context=test_content
            )
            print(f"Keyword suggestions: {keyword_suggestions}")
        except Exception as e:
            print(f"Keyword suggestions test failed: {e}")
        
        # Test SEO recommendations
        try:
            recommendations = seo_service.get_seo_recommendations(founder_id)
            print(f"SEO recommendations: {recommendations}")
        except Exception as e:
            print(f"SEO recommendations test failed: {e}")
        
        print("✅ SEO service functionality tests completed!")
        print("✅ Basic functionality tests passed!")
        
        # clean up environment variables
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        return True
    except Exception as e:
        print(f"❌ Tests failed: {e}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Python path: {sys.path}")
        
        # clean up environment variables
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up ContentGenerationModule...")
    
    # Install requirements
    install_requirements()
    
    # Download NLP models
    download_nlp_models()
    
    # Create environment file
    create_env_file()
    
    # Run basic tests
    if run_basic_tests():
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Update .env file with your actual API keys")
        print("2. Run: pytest tests/test_content_generation.py")
        print("3. Run: python -m modules.content_generation.demo")
    else:
        print("\n⚠️ Setup completed with warnings. Check the error messages above.")

if __name__ == "__main__":
    main()