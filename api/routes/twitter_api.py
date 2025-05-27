from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any, Optional
import logging

from modules.twitter_api import TwitterAPIClient, TwitterAPIError
from modules.user_profile import UserProfileService, UserProfileRepository
from api.middleware import require_auth, get_user_service

logger = logging.getLogger(__name__)

# Create blueprint for Twitter API routes
twitter_bp = Blueprint('twitter_api', __name__, url_prefix='/api/twitter')

def get_twitter_client() -> TwitterAPIClient:
    """Get configured Twitter API client"""
    client_id = current_app.config.get('TWITTER_CLIENT_ID')
    client_secret = current_app.config.get('TWITTER_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        raise ValueError("Twitter API credentials not configured")
    
    return TwitterAPIClient(client_id, client_secret)

def get_user_access_token(user_id: str) -> Optional[str]:
    """Get valid access token for user"""
    user_service = get_user_service()
    return user_service.get_twitter_access_token(user_id)

# ==================== Tweet Operations ====================

@twitter_bp.route('/tweets', methods=['POST'])
@require_auth
def create_tweet():
    """Create a new tweet"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Tweet text is required'}), 400
        
        # Get user's access token
        access_token = get_user_access_token(request.current_user_id)
        if not access_token:
            return jsonify({'error': 'Twitter account not connected'}), 401
        
        # Create tweet
        client = get_twitter_client()
        result = client.create_tweet(
            user_token=access_token,
            text=data['text'],
            reply_settings=data.get('reply_settings'),
            in_reply_to_tweet_id=data.get('in_reply_to_tweet_id'),
            quote_tweet_id=data.get('quote_tweet_id'),
            media_ids=data.get('media_ids'),
            poll_options=data.get('poll_options'),
            poll_duration_minutes=data.get('poll_duration_minutes')
        )
        
        logger.info(f"Tweet created successfully for user {request.current_user_id}")
        return jsonify(result), 201
        
    except TwitterAPIError as e:
        logger.error(f"Twitter API error creating tweet: {e}")
        return jsonify({'error': str(e)}), e.status_code or 500
    except Exception as e:
        logger.error(f"Unexpected error creating tweet: {e}")
        return jsonify({'error': 'Failed to create tweet'}), 500

@twitter_bp.route('/tweets/<tweet_id>', methods=['DELETE'])
@require_auth
def delete_tweet(tweet_id: str):
    """Delete a tweet"""
    try:
        access_token = get_user_access_token(request.current_user_id)
        if not access_token:
            return jsonify({'error': 'Twitter account not connected'}), 401
        
        client = get_twitter_client()
        result = client.delete_tweet(access_token, tweet_id)
        
        logger.info(f"Tweet {tweet_id} deleted by user {request.current_user_id}")
        return jsonify(result), 200
        
    except TwitterAPIError as e:
        logger.error(f"Twitter API error deleting tweet: {e}")
        return jsonify({'error': str(e)}), e.status_code or 500
    except Exception as e:
        logger.error(f"Unexpected error deleting tweet: {e}")
        return jsonify({'error': 'Failed to delete tweet'}), 500

@twitter_bp.route('/tweets/<tweet_id>', methods=['GET'])
@require_auth
def get_tweet(tweet_id: str):
    """Get a tweet by ID"""
    try:
        access_token = get_user_access_token(request.current_user_id)
        if not access_token:
            return jsonify({'error': 'Twitter account not connected'}), 401
        
        fields = request.args.get('fields', '').split(',') if request.args.get('fields') else None
        
        client = get_twitter_client()
        result = client.fetch_tweet_by_id(access_token, tweet_id, fields)
        
        return jsonify(result), 200
        
    except TwitterAPIError as e:
        logger.error(f"Twitter API error fetching tweet: {e}")
        return jsonify({'error': str(e)}), e.status_code or 500
    except Exception as e:
        logger.error(f"Unexpected error fetching tweet: {e}")
        return jsonify({'error': 'Failed to fetch tweet'}), 500

@twitter_bp.route('/tweets/search', methods=['GET'])
@require_auth
def search_tweets():
    """Search for tweets"""
    try:
        query = request.args.get('query')
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        access_token = get_user_access_token(request.current_user_id)
        if not access_token:
            return jsonify({'error': 'Twitter account not connected'}), 401
        
        # Parse query parameters
        params = {
            'query': query,
            'max_results': min(int(request.args.get('max_results', 50)), 100),
            'start_time': request.args.get('start_time'),
            'end_time': request.args.get('end_time'),
            'since_id': request.args.get('since_id'),
            'until_id': request.args.get('until_id'),
            'next_token': request.args.get('next_token')
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        client = get_twitter_client()
        result = client.search_tweets(access_token, **params)
        
        return jsonify(result), 200
        
    except TwitterAPIError as e:
        logger.error(f"Twitter API error searching tweets: {e}")
        return jsonify({'error': str(e)}), e.status_code or 500
    except Exception as e:
        logger.error(f"Unexpected error searching tweets: {e}")
        return jsonify({'error': 'Failed to search tweets'}), 500

# ==================== Retweet Operations ====================

@twitter_bp.route('/retweets', methods=['POST'])
@require_auth
def create_retweet():
    """Create a retweet"""
    try:
        data = request.get_json()
        if not data or 'tweet_id' not in data:
            return jsonify({'error': 'Tweet ID is required'}), 400
        
        access_token = get_user_access_token(request.current_user_id)
        if not access_token:
            return jsonify({'error': 'Twitter account not connected'}), 401
        
        # Get user's Twitter ID
        client = get_twitter_client()
        user_info = client.get_me(access_token)
        twitter_user_id = user_info['data']['id']
        
        result = client.create_retweet(
            access_token, 
            twitter_user_id, 
            data['tweet_id']
        )
        
        logger.info(f"Retweet created by user {request.current_user_id}")
        return jsonify(result), 201
        
    except TwitterAPIError as e:
        logger.error(f"Twitter API error creating retweet: {e}")
        return jsonify({'error': str(e)}), e.status_code or 500
    except Exception as e:
        logger.error(f"Unexpected error creating retweet: {e}")
        return jsonify({'error': 'Failed to create retweet'}), 500

@twitter_bp.route('/retweets/<tweet_id>', methods=['DELETE'])
@require_auth
def delete_retweet(tweet_id: str):
    """Delete a retweet"""
    try:
        access_token = get_user_access_token(request.current_user_id)
        if not access_token:
            return jsonify({'error': 'Twitter account not connected'}), 401
        
        # Get user's Twitter ID
        client = get_twitter_client()
        user_info = client.get_me(access_token)
        twitter_user_id = user_info['data']['id']
        
        result = client.delete_retweet(access_token, twitter_user_id, tweet_id)
        
        logger.info(f"Retweet deleted by user {request.current_user_id}")
        return jsonify(result), 200
        
    except TwitterAPIError as e:
        logger.error(f"Twitter API error deleting retweet: {e}")
        return jsonify({'error': str(e)}), e.status_code or 500
    except Exception as e:
        logger.error(f"Unexpected error deleting retweet: {e}")
        return jsonify({'error': 'Failed to delete retweet'}), 500

# ==================== Like Operations ====================

@twitter_bp.route('/likes', methods=['POST'])
@require_auth
def like_tweet():
    """Like a tweet"""
    try:
        data = request.get_json()
        if not data or 'tweet_id' not in data:
            return jsonify({'error': 'Tweet ID is required'}), 400
        
        access_token = get_user_access_token(request.current_user_id)
        if not access_token:
            return jsonify({'error': 'Twitter account not connected'}), 401
        
        # Get user's Twitter ID
        client = get_twitter_client()
        user_info = client.get_me(access_token)
        twitter_user_id = user_info['data']['id']
        
        result = client.like_tweet(access_token, twitter_user_id, data['tweet_id'])
        
        return jsonify(result), 201
        
    except TwitterAPIError as e:
        logger.error(f"Twitter API error liking tweet: {e}")
        return jsonify({'error': str(e)}), e.status_code or 500
    except Exception as e:
        logger.error(f"Unexpected error liking tweet: {e}")
        return jsonify({'error': 'Failed to like tweet'}), 500

@twitter_bp.route('/likes/<tweet_id>', methods=['DELETE'])
@require_auth
def unlike_tweet(tweet_id: str):
    """Unlike a tweet"""
    try:
        access_token = get_user_access_token(request.current_user_id)
        if not access_token:
            return jsonify({'error': 'Twitter account not connected'}), 401
        
        # Get user's Twitter ID
        client = get_twitter_client()
        user_info = client.get_me(access_token)
        twitter_user_id = user_info['data']['id']
        
        result = client.unlike_tweet(access_token, twitter_user_id, tweet_id)
        
        return jsonify(result), 200
        
    except TwitterAPIError as e:
        logger.error(f"Twitter API error unliking tweet: {e}")
        return jsonify({'error': str(e)}), e.status_code or 500
    except Exception as e:
        logger.error(f"Unexpected error unliking tweet: {e}")
        return jsonify({'error': 'Failed to unlike tweet'}), 500

# ==================== User Operations ====================

@twitter_bp.route('/users/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current authenticated user information"""
    try:
        access_token = get_user_access_token(request.current_user_id)
        if not access_token:
            return jsonify({'error': 'Twitter account not connected'}), 401
        
        client = get_twitter_client()
        result = client.get_me(access_token)
        
        return jsonify(result), 200
        
    except TwitterAPIError as e:
        logger.error(f"Twitter API error getting user info: {e}")
        return jsonify({'error': str(e)}), e.status_code or 500
    except Exception as e:
        logger.error(f"Unexpected error getting user info: {e}")
        return jsonify({'error': 'Failed to get user information'}), 500

@twitter_bp.route('/users/<user_id>', methods=['GET'])
@require_auth
def get_user_by_id(user_id: str):
    """Get user information by ID"""
    try:
        access_token = get_user_access_token(request.current_user_id)
        if not access_token:
            return jsonify({'error': 'Twitter account not connected'}), 401
        
        fields = request.args.get('fields', '').split(',') if request.args.get('fields') else None
        
        client = get_twitter_client()
        result = client.get_user_by_id(access_token, user_id, fields)
        
        return jsonify(result), 200
        
    except TwitterAPIError as e:
        logger.error(f"Twitter API error getting user by ID: {e}")
        return jsonify({'error': str(e)}), e.status_code or 500
    except Exception as e:
        logger.error(f"Unexpected error getting user by ID: {e}")
        return jsonify({'error': 'Failed to get user information'}), 500

# ==================== Trends Operations ====================

@twitter_bp.route('/trends', methods=['GET'])
@require_auth
def get_trends():
    """Get trending topics"""
    try:
        access_token = get_user_access_token(request.current_user_id)
        if not access_token:
            return jsonify({'error': 'Twitter account not connected'}), 401
        
        location_id = request.args.get('location_id', '1')  # Default to global
        
        client = get_twitter_client()
        result = client.get_trends_for_location(access_token, location_id)
        
        return jsonify({'trends': result}), 200
        
    except TwitterAPIError as e:
        logger.error(f"Twitter API error getting trends: {e}")
        return jsonify({'error': str(e)}), e.status_code or 500
    except Exception as e:
        logger.error(f"Unexpected error getting trends: {e}")
        return jsonify({'error': 'Failed to get trends'}), 500

# ==================== Utility Operations ====================

@twitter_bp.route('/rate-limits', methods=['GET'])
@require_auth
def get_rate_limits():
    """Get current rate limit status"""
    try:
        client = get_twitter_client()
        status = client.get_rate_limit_status()
        
        return jsonify({
            'rate_limits': status,
            'user_id': request.current_user_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting rate limit status: {e}")
        return jsonify({'error': 'Failed to get rate limit status'}), 500