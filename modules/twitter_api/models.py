"""Twitter API Models"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class TweetRequest(BaseModel):
    """Tweet creation request model"""
    text: str = Field(..., max_length=280)
    reply_to_tweet_id: Optional[str] = None
    media_ids: Optional[List[str]] = None

class RetweetRequest(BaseModel):
    """Retweet request model"""
    tweet_id: str

class LikeRequest(BaseModel):
    """Like tweet request model"""
    tweet_id: str

class TweetResponse(BaseModel):
    """Tweet response model"""
    id: str
    text: str
    author_id: str
    created_at: datetime
    metrics: Dict[str, int]
    entities: Optional[Dict[str, Any]] = None

class UserResponse(BaseModel):
    """Twitter user response model"""
    id: str
    username: str
    name: str
    profile_image_url: Optional[str] = None
    description: Optional[str] = None
    metrics: Dict[str, int]

class RateLimitResponse(BaseModel):
    """Rate limit response model"""
    limit: int
    remaining: int
    reset: datetime
    endpoint: str 