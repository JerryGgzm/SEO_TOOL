"""Setup script for ContentGenerationModule testing"""
import subprocess
import sys
import os
from pathlib import Path

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
        os.environ['OPENAI_API_KEY'] = 'API key here'
        
        # test imports
        from modules.content_generation.service import ContentGenerationService
        from modules.content_generation.models import ContentType, ContentDraft
        print("✅ Module imports successful!")
        
        # create mock objects
        from unittest.mock import Mock
        
        mock_data_flow_manager = Mock()
        mock_user_profile_service = Mock()
        mock_llm_config = {
            'openai_api_key': 'test-key-for-testing',
            'model_name': 'gpt-3.5-turbo'
        }
        
        # test basic functionality
        service = ContentGenerationService(
            data_flow_manager=mock_data_flow_manager,
            user_profile_service=mock_user_profile_service,
            llm_config=mock_llm_config
        )
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