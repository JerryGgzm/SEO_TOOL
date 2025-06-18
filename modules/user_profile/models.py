"""User Profile Models

This module defines the data models for user profile management,
including registration, authentication, and profile information.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, EmailStr, Field, validator
from datetime import datetime
import json
from enum import Enum

class ProductKeywords(BaseModel):
    """Product keywords structure"""
    primary: List[str] = Field(..., min_items=1, description="Primary keywords")
    secondary: Optional[List[str]] = Field(default=None, description="Secondary keywords")
    seo_keywords: Optional[List[str]] = Field(default=None, description="SEO-specific keywords")

class CompetitorInfo(BaseModel):
    """Competitor information"""
    name: str
    description: Optional[str] = None
    website: Optional[HttpUrl] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None

class InfluencerReference(BaseModel):
    """Reference influencer information"""
    name: str
    twitter_handle: Optional[str] = None
    platform: str = "Twitter"
    why_reference: Optional[str] = None  # Why reference this influencer

class ContentStylePreferences(BaseModel):
    """Content style preferences"""
    tone: str = Field(default="professional", description="Tone: professional, casual, humorous, formal")
    voice: str = Field(default="friendly", description="Voice style: authoritative, friendly, educational")
    max_tweet_length: int = Field(default=280, ge=1, le=280)
    use_emojis: bool = Field(default=True)
    use_hashtags: bool = Field(default=True)
    preferred_languages: List[str] = Field(default=["en"])

class ProductInfoData(BaseModel):
    """Product information data model"""
    company_name: Optional[str] = Field(None, max_length=100, description="Company name")
    product_name: str = Field(..., min_length=1, max_length=100, description="Product name")
    product_description: Optional[str] = Field(None, max_length=1000, description="Product description")
    industry: Optional[str] = Field(None, max_length=50, description="Industry category")
    brand_voice: Optional[str] = Field(None, max_length=50, description="Brand voice style")

class UserProfileData(BaseModel):
    """User profile data model"""
    user_id: str
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = Field(None, max_length=50)
    timezone: str = Field(default="UTC")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    product_info: Optional[ProductInfoData] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class TwitterCredentials(BaseModel):
    """Twitter authentication credentials model (for internal processing, sensitive information encrypted)"""
    user_id: str
    access_token: str  # Will be encrypted for storage
    refresh_token: Optional[str] = None  # Will be encrypted for storage
    token_type: str = "Bearer"
    expires_at: Optional[datetime] = None
    scope: Optional[str] = None
    twitter_user_id: Optional[str] = None
    twitter_username: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def is_expired(self) -> bool:
        """Check if access token is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at

class UserRegistration(BaseModel):
    """User registration request model"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    terms_accepted: bool = Field(..., description="Must accept terms of service")
    industry: Optional[str] = None
    website: Optional[str] = None
    twitter_handle: Optional[str] = None
    
    @validator('terms_accepted')
    def terms_must_be_accepted(cls, v):
        if not v:
            raise ValueError('Must accept terms of service')
        return v

class UserLogin(BaseModel):
    """User login request model"""
    email: EmailStr
    password: str

class ProductInfoUpdate(BaseModel):
    """Product information update request model"""
    product_info: ProductInfoData


class TwitterAuthResponse(BaseModel):
    """Twitter OAuth response model"""
    user_id: str
    twitter_username: str
    access_token: str
    access_token_secret: str
    created_at: datetime

class TwitterStatus(BaseModel):
    """Twitter connection status model"""
    connected: bool
    twitter_username: Optional[str] = None
    last_sync: Optional[datetime] = None
    error_message: Optional[str] = None


class UserPreferences(BaseModel):
    """User preferences model"""
    content_frequency: str = "daily"
    preferred_posting_times: List[str] = []
    content_types: List[str] = ["tweet", "thread"]
    auto_schedule: bool = True
    notification_settings: Dict[str, bool] = Field(default_factory=dict)
    theme: str = "light"
    language: str = "en"