import os
from typing import Optional

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

settings = Settings()