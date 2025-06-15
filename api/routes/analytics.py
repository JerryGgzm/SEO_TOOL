"""
Analytics API Module

This module provides RESTful API endpoints for Twitter analytics functionality.
It includes endpoints for dashboard data, post analytics, data collection, and overview statistics.

Key Features:
- User dashboard analytics with customizable date ranges
- Detailed analytics for individual tweets
- Batch analytics for multiple tweets
- Analytics overview with different time periods
- Authentication required for all endpoints

Dependencies:
- Flask: Web framework
- SQLAlchemy: Database ORM
- datetime: Date handling
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import PostAnalytic, Founder
from database import get_db_context
from functools import wraps

# Create blueprint for analytics routes
analytics_bp = Blueprint('analytics', __name__)

def require_auth(f):
    """
    Authentication decorator for protecting analytics endpoints.
    
    This decorator:
    1. Checks for the presence of an Authorization header
    2. Extracts the Bearer token
    3. Validates the token (TODO: implement actual validation)
    
    Args:
        f: The function to be decorated
        
    Returns:
        Decorated function that checks authentication before execution
        
    Raises:
        401 Unauthorized if token is missing or invalid
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Missing authentication token'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        # TODO: Implement token validation logic
        # payload = verify_jwt_token(token)
        # if 'error' in payload:
        #     return jsonify({'error': payload['error']}), 401
        
        # request.current_user_id = payload['user_id']
        return f(*args, **kwargs)
    
    return decorated_function

@analytics_bp.route('/dashboard/<user_id>', methods=['GET'])
@require_auth
def get_dashboard(user_id: str):
    """
    Get user's analytics dashboard data with customizable date range.
    
    This endpoint provides aggregated analytics data for a user's tweets within a specified time period.
    It calculates key metrics like total impressions, engagements, and average engagement rate.
    
    Args:
        user_id (str): The ID of the user whose analytics are being requested
        
    Query Parameters:
        date_range (str): Time range for analytics ('7d', '30d', '90d', or 'custom')
        start_date (str): Start date for custom range (format: YYYY-MM-DD)
        end_date (str): End date for custom range (format: YYYY-MM-DD)
        
    Returns:
        JSON response containing:
        - Total impressions
        - Total engagements
        - Average engagement rate
        - Number of posts analyzed
        - Date range information
        
    Raises:
        400 Bad Request if date parameters are invalid
        401 Unauthorized if authentication fails
    """
    date_range = request.args.get('date_range')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Validate date range
    if date_range == "custom" and (not start_date or not end_date):
        return jsonify({'error': 'Custom date range requires both start_date and end_date'}), 400
    
    # Calculate date range
    end = datetime.now()
    if date_range == "7d":
        start = end - timedelta(days=7)
    elif date_range == "30d":
        start = end - timedelta(days=30)
    elif date_range == "90d":
        start = end - timedelta(days=90)
    else:  # custom
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    # Get analytics data
    with get_db_context() as db:
        analytics = db.query(PostAnalytic).filter(
            PostAnalytic.founder_id == user_id,
            PostAnalytic.posted_at.between(start, end)
        ).all()
        
        # Calculate metrics
        total_impressions = sum(a.impressions for a in analytics)
        total_engagements = sum(a.total_engagements for a in analytics)
        avg_engagement_rate = sum(a.engagement_rate or 0 for a in analytics) / len(analytics) if analytics else 0
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_impressions': total_impressions,
                'total_engagements': total_engagements,
                'average_engagement_rate': avg_engagement_rate,
                'posts_analyzed': len(analytics),
                'date_range': {
                    'start': start.isoformat(),
                    'end': end.isoformat()
                }
            }
        })

@analytics_bp.route('/posts/<tweet_id>', methods=['GET'])
@require_auth
def get_post_analytics(tweet_id: str):
    """
    Get detailed analytics for a specific tweet.
    
    This endpoint provides comprehensive analytics data for a single tweet,
    including impressions, various engagement metrics, and conversion data.
    
    Args:
        tweet_id (str): The ID of the tweet to analyze
        
    Returns:
        JSON response containing:
        - Tweet ID
        - Impressions
        - Engagement metrics (likes, retweets, replies, quote tweets)
        - Engagement rate
        - Link clicks
        - Profile visits
        - Posting and last update timestamps
        
    Raises:
        404 Not Found if tweet analytics don't exist
        401 Unauthorized if authentication fails
    """
    with get_db_context() as db:
        analytics = db.query(PostAnalytic).filter(
            PostAnalytic.posted_tweet_id == tweet_id
        ).first()
        
        if not analytics:
            return jsonify({'error': 'Tweet analytics not found'}), 404
        
        return jsonify({
            'status': 'success',
            'data': {
                'tweet_id': analytics.posted_tweet_id,
                'impressions': analytics.impressions,
                'engagements': {
                    'likes': analytics.likes,
                    'retweets': analytics.retweets,
                    'replies': analytics.replies,
                    'quote_tweets': analytics.quote_tweets
                },
                'engagement_rate': analytics.engagement_rate,
                'link_clicks': analytics.link_clicks,
                'profile_visits': analytics.profile_visits_from_tweet,
                'posted_at': analytics.posted_at.isoformat(),
                'last_updated': analytics.last_updated_at.isoformat()
            }
        })

@analytics_bp.route('/posts', methods=['GET'])
@require_auth
def get_user_posts_analytics():
    """
    Get analytics for all user's posts with pagination and sorting options.
    
    This endpoint provides analytics data for all tweets by a specific user,
    with support for pagination and different sorting criteria.
    
    Query Parameters:
        user_id (str): Required. The ID of the user whose posts to analyze
        limit (int): Optional. Number of posts per page (default: 20)
        offset (int): Optional. Number of posts to skip (default: 0)
        sort_by (str): Optional. Sort criteria ('engagement', 'likes', 'retweets', 'replies', 'date')
        
    Returns:
        JSON response containing:
        - Total number of posts
        - Pagination information
        - List of posts with their analytics data
        
    Raises:
        400 Bad Request if required parameters are missing or invalid
        401 Unauthorized if authentication fails
    """
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
        
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    sort_by = request.args.get('sort_by', 'date')
    
    if sort_by not in ['engagement', 'likes', 'retweets', 'replies', 'date']:
        return jsonify({'error': 'Invalid sort_by parameter'}), 400
    
    with get_db_context() as db:
        query = db.query(PostAnalytic).filter(PostAnalytic.founder_id == user_id)
        total = query.count()
        # Apply sorting
        if sort_by == "engagement":
            query = query.order_by(PostAnalytic.engagement_rate.desc())
        elif sort_by == "likes":
            query = query.order_by(PostAnalytic.likes.desc())
        elif sort_by == "retweets":
            query = query.order_by(PostAnalytic.retweets.desc())
        elif sort_by == "replies":
            query = query.order_by(PostAnalytic.replies.desc())
        else:  # date
            query = query.order_by(PostAnalytic.posted_at.desc())
        # Apply pagination
        posts = query.offset(offset).limit(limit).all()
        return jsonify({
            'status': 'success',
            'data': {
                'total': total,
                'offset': offset,
                'limit': limit,
                'posts': [{
                    'tweet_id': post.posted_tweet_id,
                    'impressions': post.impressions,
                    'engagements': {
                        'likes': post.likes,
                        'retweets': post.retweets,
                        'replies': post.replies,
                        'quote_tweets': post.quote_tweets
                    },
                    'engagement_rate': post.engagement_rate,
                    'posted_at': post.posted_at.isoformat()
                } for post in posts]
            }
        })

@analytics_bp.route('/collect/<tweet_id>', methods=['POST'])
@require_auth
def collect_tweet_analytics(tweet_id: str):
    """
    Trigger analytics collection for a specific tweet.
    
    This endpoint initiates the collection of analytics data for a single tweet.
    It's designed to be called asynchronously, as data collection may take time.
    
    Args:
        tweet_id (str): The ID of the tweet to collect analytics for
        
    Returns:
        JSON response indicating collection has started
        
    Note:
        This is a placeholder endpoint. Actual Twitter API integration needs to be implemented.
        
    Raises:
        401 Unauthorized if authentication fails
    """
    # TODO: Implement actual Twitter API call to collect analytics
    # This is a placeholder that would need to be implemented with actual Twitter API integration
    return jsonify({
        'status': 'success',
        'data': {
            'status': 'collection_started',
            'tweet_id': tweet_id
        }
    })

@analytics_bp.route('/collect/batch', methods=['POST'])
@require_auth
def collect_batch_analytics():
    """
    Trigger analytics collection for multiple tweets in batch.
    
    This endpoint initiates the collection of analytics data for multiple tweets simultaneously.
    It's designed to be called asynchronously, as batch collection may take significant time.
    
    Request Body:
        JSON object containing:
        - tweet_ids (list): List of tweet IDs to collect analytics for
        
    Returns:
        JSON response indicating batch collection has started
        
    Note:
        This is a placeholder endpoint. Actual Twitter API integration needs to be implemented.
        
    Raises:
        400 Bad Request if tweet_ids are missing
        401 Unauthorized if authentication fails
    """
    data = request.get_json()
    if not data or 'tweet_ids' not in data:
        return jsonify({'error': 'tweet_ids is required in request body'}), 400
    
    # TODO: Implement actual Twitter API call to collect analytics for multiple tweets
    # This is a placeholder that would need to be implemented with actual Twitter API integration
    return jsonify({
        'status': 'success',
        'data': {
            'status': 'batch_collection_started',
            'tweet_ids': data['tweet_ids']
        }
    })

@analytics_bp.route('/overview/<user_id>', methods=['GET'])
@require_auth
def get_analytics_overview(user_id: str):
    """
    Get analytics overview statistics for a user.
    
    This endpoint provides aggregated analytics data for a user's tweets
    over different time periods (daily, weekly, monthly).
    
    Args:
        user_id (str): The ID of the user whose analytics are being requested
        
    Query Parameters:
        period (str): Time period for overview ('daily', 'weekly', 'monthly')
        
    Returns:
        JSON response containing:
        - Period information
        - Total posts
        - Total impressions
        - Total engagements
        - Average engagement rate
        - Date range information
        
    Raises:
        400 Bad Request if period parameter is invalid
        401 Unauthorized if authentication fails
    """
    period = request.args.get('period')
    if not period or period not in ['daily', 'weekly', 'monthly']:
        return jsonify({'error': 'Invalid period parameter'}), 400
    
    # Calculate time range based on period
    end = datetime.now()
    if period == "daily":
        start = end - timedelta(days=1)
    elif period == "weekly":
        start = end - timedelta(weeks=1)
    else:  # monthly
        start = end - timedelta(days=30)
    
    with get_db_context() as db:
        analytics = db.query(PostAnalytic).filter(
            PostAnalytic.founder_id == user_id,
            PostAnalytic.posted_at.between(start, end)
        ).all()
        
        # Calculate statistics
        total_posts = len(analytics)
        total_impressions = sum(a.impressions for a in analytics)
        total_engagements = sum(a.total_engagements for a in analytics)
        avg_engagement_rate = sum(a.engagement_rate or 0 for a in analytics) / total_posts if total_posts > 0 else 0
        
        return jsonify({
            'status': 'success',
            'data': {
                'period': period,
                'total_posts': total_posts,
                'total_impressions': total_impressions,
                'total_engagements': total_engagements,
                'average_engagement_rate': avg_engagement_rate,
                'date_range': {
                    'start': start.isoformat(),
                    'end': end.isoformat()
                }
            }
        }) 