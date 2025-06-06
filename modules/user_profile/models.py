"""User profile data models""" 
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, EmailStr, Field, validator
from datetime import datetime
import json

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
    product_name: str = Field(..., min_length=1, max_length=100)
    tagline: Optional[str] = Field(None, max_length=200, description="Product tagline")
    description: str = Field(..., min_length=10, max_length=1000)
    core_features: List[str] = Field(..., min_items=1, description="Core features")
    unique_selling_points: List[str] = Field(..., min_items=1, description="Unique selling points")
    core_values: List[str] = Field(..., min_items=1, description="Core values")
    target_audience_description: str = Field(..., min_length=10, description="Target audience profile")
    brand_story: Optional[str] = Field(None, max_length=2000, description="Brand story")
    key_messages: List[str] = Field(default=[], description="Key messages to convey")
    niche_keywords: ProductKeywords
    competitors: Optional[List[CompetitorInfo]] = Field(default=[])
    reference_influencers: Optional[List[InfluencerReference]] = Field(default=[])
    website_url: Optional[HttpUrl] = None
    pricing_model: Optional[str] = None
    target_markets: Optional[List[str]] = Field(default=[], description="Target markets/regions")
    industry_category: Optional[str] = None
    content_style_preferences: ContentStylePreferences = Field(default_factory=ContentStylePreferences)
    
    @validator('core_features', 'unique_selling_points', 'core_values')
    def validate_lists_not_empty(cls, v):
        if not v or all(not item.strip() for item in v):
            raise ValueError("List cannot be empty and items cannot be empty strings")
        return [item.strip() for item in v if item.strip()]

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

class UserRegistrationRequest(BaseModel):
    """User registration request model"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    terms_accepted: bool = Field(..., description="Must accept terms of service")
    
    @validator('terms_accepted')
    def terms_must_be_accepted(cls, v):
        if not v:
            raise ValueError('Must accept terms of service')
        return v

class UserLoginRequest(BaseModel):
    """User login request model"""
    email: EmailStr
    password: str

class ProductInfoUpdateRequest(BaseModel):
    """Product information update request model"""
    product_info: ProductInfoData