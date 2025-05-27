from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any, Optional
import logging
import asyncio

from modules.trend_analysis import (
    TrendAnalysisEngine, TrendAnalysisRequest, TrendAnalysisConfig,
    TrendAnalysisRepository
)
from modules.twitter_api import TwitterAPIClient
from modules.user_profile import UserProfileService
from api.middleware import require_auth, get_user_service

logger = logging.getLogger(__name__)

# Create blueprint for trend analysis routes
trends_bp = Blueprint('trend_analysis', __name__, url_prefix='/api/trends')

def get_trend_analysis_engine() -> TrendAnalysisEngine:
    """Get configured trend analysis engine"""
    # Get dependencies
    twitter_client = get_twitter_client()
    user_service = get_user_service()
    
    # Configure analysis
    config = TrendAnalysisConfig(
        max_tweets_per_trend=150,
        use_llm_for_insights=current_app.config.get('ENABLE_LLM_INSIGHTS', True),
        llm_model_name=current_app.config.get('LLM_MODEL_NAME', 'gpt-3.5-turbo')
    )
    
    # Initialize LLM client if configured
    llm_client = None
    if config.use_llm_for_insights:
        try:
            import openai
            llm_client = openai.OpenAI(
                api_key=current_app.config.get('OPENAI_API_KEY')
            )
        except ImportError:
            logger.warning("OpenAI client not available, LLM insights disabled")
    
    return TrendAnalysisEngine(twitter_client, user_service, config, llm_client)

def get_twitter_client() -> TwitterAPIClient:
    """Get Twitter API client"""
    from modules.twitter_api import TwitterAPIClient
    
    client_id = current_app.config.get('TWITTER_CLIENT_ID')
    client_secret = current_app.config.get('TWITTER_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        raise ValueError("Twitter API credentials not configured")
    
    return TwitterAPIClient(client_id, client_secret)

def get_trend_repository() -> TrendAnalysisRepository:
    """Get trend analysis repository"""
    from database.models import SessionLocal
    db_session = SessionLocal()
    return TrendAnalysisRepository(db_session)

# ==================== Trend Analysis Operations ====================

@trends_bp.route('/analyze', methods=['POST'])
@require_auth
def analyze_trends():
    """Start trend analysis for the current user"""
    try:
        data = request.get_json() or {}
        
        # Create analysis request
        request_data = {
            'user_id': request.current_user_id,
            'focus_keywords': data.get('focus_keywords', []),
            'location_id': data.get('location_id', '1'),
            'max_trends_to_analyze': min(data.get('max_trends_to_analyze', 10), 20),
            'tweet_sample_size': min(data.get('tweet_sample_size', 100), 200),
            'include_micro_trends': data.get('include_micro_trends', True),
            'sentiment_analysis_depth': data.get('sentiment_analysis_depth', 'standard')
        }
        
        try:
            analysis_request = TrendAnalysisRequest(**request_data)
        except Exception as e:
            return jsonify({'error': f'Invalid request parameters: {str(e)}'}), 400
        
        # Run analysis
        engine = get_trend_analysis_engine()
        
        # Use asyncio to run the async analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            analyzed_trends = loop.run_until_complete(
                engine.analyze_trends_for_user(request.current_user_id, analysis_request)
            )
        finally:
            loop.close()
        
        # Store results
        repository = get_trend_repository()
        saved_count = 0
        
        for trend in analyzed_trends:
            if repository.save_analyzed_trend(trend):
                saved_count += 1
        
        # Return summary
        return jsonify({
            'message': f'Analysis completed successfully',
            'trends_analyzed': len(analyzed_trends),
            'trends_saved': saved_count,
            'micro_trends_found': sum(1 for t in analyzed_trends if t.is_micro_trend),
            'analysis_id': f"analysis_{request.current_user_id}_{int(datetime.utcnow().timestamp())}"
        }), 200
        
    except Exception as e:
        logger.error(f"Trend analysis failed: {e}")
        return jsonify({'error': 'Trend analysis failed'}), 500

@trends_bp.route('/latest', methods=['GET'])
@require_auth
def get_latest_trends():
    """Get latest analyzed trends for the current user"""
    try:
        limit = min(int(request.args.get('limit', 10)), 50)
        include_expired = request.args.get('include_expired', 'false').lower() == 'true'
        
        repository = get_trend_repository()
        trends = repository.get_latest_trends_for_user(
            request.current_user_id, 
            limit, 
            include_expired
        )
        
        # Convert to dict for JSON response
        trends_data = []
        for trend in trends:
            trend_dict = trend.dict()
            # Convert datetime objects to ISO strings
            trend_dict['analyzed_at'] = trend.analyzed_at.isoformat()
            if trend.expires_at:
                trend_dict['expires_at'] = trend.expires_at.isoformat()
            
            trends_data.append(trend_dict)
        
        return jsonify({
            'trends': trends_data,
            'total_count': len(trends_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get latest trends: {e}")
        return jsonify({'error': 'Failed to retrieve trends'}), 500

@trends_bp.route('/micro-trends', methods=['GET'])
@require_auth
def get_micro_trends():
    """Get micro-trends for the current user"""
    try:
        limit = min(int(request.args.get('limit', 5)), 20)
        
        repository = get_trend_repository()
        micro_trends = repository.get_micro_trends_for_user(
            request.current_user_id, 
            limit
        )
        
        # Convert to dict for JSON response
        trends_data = []
        for trend in micro_trends:
            trend_dict = trend.dict()
            trend_dict['analyzed_at'] = trend.analyzed_at.isoformat()
            if trend.expires_at:
                trend_dict['expires_at'] = trend.expires_at.isoformat()
            
            trends_data.append(trend_dict)
        
        return jsonify({
            'micro_trends': trends_data,
            'total_count': len(trends_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get micro-trends: {e}")
        return jsonify({'error': 'Failed to retrieve micro-trends'}), 500

@trends_bp.route('/search', methods=['GET'])
@require_auth
def search_trends():
    """Search trends by keywords"""
    try:
        keywords = request.args.get('keywords', '').split(',')
        keywords = [kw.strip() for kw in keywords if kw.strip()]
        
        if not keywords:
            return jsonify({'error': 'Keywords parameter is required'}), 400
        
        limit = min(int(request.args.get('limit', 10)), 30)
        
        repository = get_trend_repository()
        trends = repository.get_trends_by_keywords(
            request.current_user_id,
            keywords,
            limit
        )
        
        # Convert to dict for JSON response
        trends_data = []
        for trend in trends:
            trend_dict = trend.dict()
            trend_dict['analyzed_at'] = trend.analyzed_at.isoformat()
            if trend.expires_at:
                trend_dict['expires_at'] = trend.expires_at.isoformat()
            
            trends_data.append(trend_dict)
        
        return jsonify({
            'trends': trends_data,
            'search_keywords': keywords,
            'total_count': len(trends_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to search trends: {e}")
        return jsonify({'error': 'Failed to search trends'}), 500

@trends_bp.route('/statistics', methods=['GET'])
@require_auth
def get_trend_statistics():
    """Get trend analysis statistics for the current user"""
    try:
        days = min(int(request.args.get('days', 30)), 90)
        
        repository = get_trend_repository()
        stats = repository.get_trend_statistics(request.current_user_id, days)
        
        return jsonify({
            'statistics': stats,
            'period_days': days,
            'user_id': request.current_user_id
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get trend statistics: {e}")
        return jsonify({'error': 'Failed to retrieve statistics'}), 500

@trends_bp.route('/<trend_id>', methods=['GET'])
@require_auth
def get_trend_details(trend_id: str):
    """Get detailed information about a specific trend"""
    try:
        repository = get_trend_repository()
        
        # Get all trends for user and find the specific one
        all_trends = repository.get_latest_trends_for_user(
            request.current_user_id, 
            limit=1000,  # Get all trends
            include_expired=True
        )
        
        trend = None
        for t in all_trends:
            if t.id == trend_id:
                trend = t
                break
        
        if not trend:
            return jsonify({'error': 'Trend not found'}), 404
        
        # Convert to dict for JSON response
        trend_dict = trend.dict()
        trend_dict['analyzed_at'] = trend.analyzed_at.isoformat()
        if trend.expires_at:
            trend_dict['expires_at'] = trend.expires_at.isoformat()
        
        return jsonify({'trend': trend_dict}), 200
        
    except Exception as e:
        logger.error(f"Failed to get trend details: {e}")
        return jsonify({'error': 'Failed to retrieve trend details'}), 500

# ==================== Configuration Operations ====================

@trends_bp.route('/config', methods=['GET'])
@require_auth
def get_analysis_config():
    """Get current trend analysis configuration"""
    try:
        config = TrendAnalysisConfig()
        
        return jsonify({
            'config': config.dict(),
            'llm_available': current_app.config.get('ENABLE_LLM_INSIGHTS', False)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get analysis config: {e}")
        return jsonify({'error': 'Failed to retrieve configuration'}), 500