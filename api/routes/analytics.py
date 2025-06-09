from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import PostAnalytic, Founder
from database import get_db_context
from functools import wraps

# 创建蓝图
analytics_bp = Blueprint('analytics', __name__)

def require_auth(f):
    """Authentication decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Missing authentication token'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        # TODO: 实现token验证逻辑
        # payload = verify_jwt_token(token)
        # if 'error' in payload:
        #     return jsonify({'error': payload['error']}), 401
        
        # request.current_user_id = payload['user_id']
        return f(*args, **kwargs)
    
    return decorated_function

@analytics_bp.route('/dashboard/<user_id>', methods=['GET'])
@require_auth
def get_dashboard(user_id: str):
    """Get user's analytics dashboard data"""
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
    """Get detailed analytics for a specific tweet"""
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
    """Get analytics for all user's posts"""
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
    """Trigger analytics collection for a specific tweet"""
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
    """Trigger analytics collection for multiple tweets"""
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
    """Get analytics overview statistics"""
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