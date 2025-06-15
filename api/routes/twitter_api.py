"""Twitter API Routes

This module implements the FastAPI routes for Twitter API integration,
handling tweet operations, user interactions and rate limits.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse
import logging
import os

from database import get_data_flow_manager, DataFlowManager
from api.middleware import get_current_user, User

from modules.twitter_api import TwitterAPIClient
from modules.twitter_api.models import (
    TweetRequest, RetweetRequest, LikeRequest,
    TweetResponse, UserResponse, RateLimitResponse
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/twitter", tags=["twitter-api"])

# Dependencies
async def get_twitter_client(
    current_user: User = Depends(get_current_user)
) -> TwitterAPIClient:
    """Get Twitter client for current user"""
    try:
        client_id = os.getenv('TWITTER_CLIENT_ID')
        client_secret = os.getenv('TWITTER_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Twitter API credentials not configured"
            )
        
        # 检查用户是否有Twitter访问令牌
        if not hasattr(current_user, 'twitter_access_token') or not current_user.twitter_access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User has not authorized Twitter access. Please complete Twitter OAuth flow first."
            )
            
        return TwitterAPIClient(
            client_id=client_id,
            client_secret=client_secret
        )
    except Exception as e:
        logger.error(f"Failed to create Twitter client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize Twitter client"
        )

@router.post("/tweets")
async def create_tweet(
    tweet_request: TweetRequest,
    current_user: User = Depends(get_current_user),
    twitter_client: TwitterAPIClient = Depends(get_twitter_client)
):
    """Create a new tweet"""
    try:
        result = twitter_client.create_tweet(
            user_token=current_user.twitter_access_token,
            text=tweet_request.text,
            in_reply_to_tweet_id=tweet_request.reply_to_tweet_id,
            media_ids=tweet_request.media_ids
        )
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Tweet created successfully",
                "tweet": result
            }
        )
    except Exception as e:
        logger.error(f"Failed to create tweet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tweet"
        )

@router.delete("/tweets/{tweet_id}")
async def delete_tweet(
    tweet_id: str = Path(..., description="Tweet ID to delete"),
    current_user: User = Depends(get_current_user),
    twitter_client: TwitterAPIClient = Depends(get_twitter_client)
):
    """Delete a tweet"""
    try:
        success = await twitter_client.delete_tweet(tweet_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tweet not found or could not be deleted"
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Tweet deleted successfully",
                "tweet_id": tweet_id
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete tweet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete tweet"
        )

@router.get("/tweets/{tweet_id}")
async def get_tweet(
    tweet_id: str = Path(..., description="Tweet ID to retrieve"),
    current_user: User = Depends(get_current_user),
    twitter_client: TwitterAPIClient = Depends(get_twitter_client)
):
    """Get tweet details"""
    try:
        tweet = await twitter_client.get_tweet(tweet_id)
        if not tweet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tweet not found"
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Tweet retrieved successfully",
                "tweet": tweet
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tweet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tweet"
        )

@router.get("/tweets/search")
async def search_tweets(
    query: str = Query(..., description="Search query"),
    max_results: int = Query(default=10, ge=1, le=100, description="Maximum number of results"),
    current_user: User = Depends(get_current_user),
    twitter_client: TwitterAPIClient = Depends(get_twitter_client)
):
    """Search tweets"""
    try:
        results = await twitter_client.search_tweets(query, max_results)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Tweets search completed successfully",
                "query": query,
                "results": results
            }
        )
    except Exception as e:
        logger.error(f"Failed to search tweets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search tweets"
        )

@router.post("/retweets")
async def create_retweet(
    retweet_request: RetweetRequest,
    current_user: User = Depends(get_current_user),
    twitter_client: TwitterAPIClient = Depends(get_twitter_client)
):
    """Create a retweet"""
    try:
        result = await twitter_client.create_retweet(retweet_request.tweet_id)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Retweet created successfully",
                "retweet": result
            }
        )
    except Exception as e:
        logger.error(f"Failed to create retweet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create retweet"
        )

@router.delete("/retweets/{tweet_id}")
async def delete_retweet(
    tweet_id: str = Path(..., description="Tweet ID to unretweet"),
    current_user: User = Depends(get_current_user),
    twitter_client: TwitterAPIClient = Depends(get_twitter_client)
):
    """Delete a retweet"""
    try:
        success = await twitter_client.delete_retweet(tweet_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Retweet not found or could not be deleted"
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Retweet deleted successfully",
                "tweet_id": tweet_id
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete retweet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete retweet"
        )

@router.post("/likes")
async def like_tweet(
    like_request: LikeRequest,
    current_user: User = Depends(get_current_user),
    twitter_client: TwitterAPIClient = Depends(get_twitter_client)
):
    """Like a tweet"""
    try:
        result = await twitter_client.like_tweet(like_request.tweet_id)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Tweet liked successfully",
                "like": result
            }
        )
    except Exception as e:
        logger.error(f"Failed to like tweet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to like tweet"
        )

@router.delete("/likes/{tweet_id}")
async def unlike_tweet(
    tweet_id: str = Path(..., description="Tweet ID to unlike"),
    current_user: User = Depends(get_current_user),
    twitter_client: TwitterAPIClient = Depends(get_twitter_client)
):
    """Unlike a tweet"""
    try:
        success = await twitter_client.unlike_tweet(tweet_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Like not found or could not be removed"
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Tweet unliked successfully",
                "tweet_id": tweet_id
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unlike tweet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unlike tweet"
        )

@router.get("/users/me")
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    twitter_client: TwitterAPIClient = Depends(get_twitter_client)
):
    """Get current user's Twitter profile"""
    try:
        profile = await twitter_client.get_current_user()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "User profile retrieved successfully",
                "profile": profile
            }
        )
    except Exception as e:
        logger.error(f"Failed to get user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )

@router.get("/users/{user_id}")
async def get_user_by_id(
    user_id: str = Path(..., description="Twitter user ID"),
    current_user: User = Depends(get_current_user),
    twitter_client: TwitterAPIClient = Depends(get_twitter_client)
):
    """Get Twitter user profile by ID"""
    try:
        profile = await twitter_client.get_user_by_id(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "User profile retrieved successfully",
                "profile": profile
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )

@router.get("/trends")
async def get_trends(
    location_id: str = Query(default="1", description="Twitter location ID"),
    current_user: User = Depends(get_current_user),
    twitter_client: TwitterAPIClient = Depends(get_twitter_client)
):
    """Get trending topics"""
    try:
        trends = await twitter_client.get_trends(location_id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Trends retrieved successfully",
                "location_id": location_id,
                "trends": trends
            }
        )
    except Exception as e:
        logger.error(f"Failed to get trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trends"
        )

@router.get("/rate-limits")
async def get_rate_limits(
    current_user: User = Depends(get_current_user),
    twitter_client: TwitterAPIClient = Depends(get_twitter_client)
):
    """Get Twitter API rate limits"""
    try:
        limits = await twitter_client.get_rate_limits()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Rate limits retrieved successfully",
                "limits": limits
            }
        )
    except Exception as e:
        logger.error(f"Failed to get rate limits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rate limits"
        )