"""系统配置设置"""
import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    APP_NAME: str = "Ideation"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-here"
    
    # 数据库配置
    DATABASE_URL: Optional[str] = None
    
    # Twitter API配置
    TWITTER_API_KEY: Optional[str] = None
    TWITTER_API_SECRET: Optional[str] = None
    TWITTER_ACCESS_TOKEN: Optional[str] = None
    TWITTER_ACCESS_TOKEN_SECRET: Optional[str] = None
    
    # OpenAI配置
    OPENAI_API_KEY: Optional[str] = None
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"


settings = Settings() 