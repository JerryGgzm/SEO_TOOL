import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv('.env')

class Settings:
    """Application configuration"""
    
    # Database configuration
    DATABASE_URL: str = os.getenv(
        'DATABASE_URL', 
        'postgresql://ideation_user:password@localhost:5432/ideation_db'
    )
    
    # Twitter API configuration
    TWITTER_CLIENT_ID: Optional[str] = os.getenv('TWITTER_CLIENT_ID')
    TWITTER_CLIENT_SECRET: Optional[str] = os.getenv('TWITTER_CLIENT_SECRET')
    TWITTER_REDIRECT_URI: str = os.getenv(
        'TWITTER_REDIRECT_URI', 
        'http://localhost:8000/auth/twitter/callback'
    )
    
    # Google APIs configuration
    GEMINI_API_KEY: Optional[str] = os.getenv('GEMINI_API_KEY')
    GOOGLE_SEARCH_API_KEY: Optional[str] = os.getenv('GOOGLE_SEARCH_API_KEY')
    GOOGLE_SEARCH_ENGINE_ID: Optional[str] = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    # Security configuration
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'change-this-in-production')
    ENCRYPTION_KEY: Optional[str] = os.getenv('ENCRYPTION_KEY')
    
    # JWT configuration
    JWT_EXPIRY_HOURS: int = int(os.getenv('JWT_EXPIRY_HOURS', '24'))
    
    # Application configuration
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    PORT: int = int(os.getenv('PORT', '8000'))
    HOST: str = os.getenv('HOST', '0.0.0.0')
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration items"""
        required_vars = [
            'TWITTER_CLIENT_ID',
            'TWITTER_CLIENT_SECRET'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        return True
    
    @classmethod
    def validate_google_apis(cls) -> bool:
        """验证Google API配置"""
        google_vars = [
            'GEMINI_API_KEY',
            'GOOGLE_SEARCH_API_KEY', 
            'GOOGLE_SEARCH_ENGINE_ID'
        ]
        
        missing_vars = []
        for var in google_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"缺少Google API环境变量: {', '.join(missing_vars)}")
            print("注意：这些是新的基于Gemini的趋势分析功能所必需的")
            return False
        
        return True

settings = Settings()