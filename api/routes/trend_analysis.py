"""Trend Analysis API Routes

This module implements the FastAPI routes for trend analysis,
handling Twitter trending topics extraction, LLM matching, and database storage.
"""
import logging
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse

from database import get_data_flow_manager, DataFlowManager, get_db_session
from api.middleware import get_current_user, User
from modules.trend_analysis.repository import TrendAnalysisRepository
from modules.twitter_api import TwitterAPIClient
from modules.user_profile import UserProfileService
from modules.user_profile.repository import UserProfileRepository

# Load environment variables
load_dotenv('.env')
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/trends", tags=["trend-analysis"])

# Dependencies
async def get_trend_repository(
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager)
) -> TrendAnalysisRepository:
    """Get trend repository with dependencies"""
    try:
        return TrendAnalysisRepository(data_flow_manager.db_session)
    except Exception as e:
        logger.error(f"Failed to create trend repository: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize trend repository"
        )

async def get_twitter_credentials(current_user: User):
    """Get Twitter credentials for current user"""
    try:
        db_session = get_db_session()
        user_service = UserProfileService(UserProfileRepository(db_session), None)
        credentials = user_service.repository.get_twitter_credentials(current_user.id)
        
        if not credentials or not credentials.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Twitter credentials not found. Please connect your Twitter account first."
            )
        
        return credentials
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Twitter credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Twitter credentials"
        )

@router.post("/fetch-and-store")
async def fetch_and_store_trending_topics(
    location_id: str = Query(default="1", description="Twitter location ID (1=Global, 23424977=USA)"),
    keywords: List[str] = Query(default=[], description="Optional keywords to filter trends"),
    max_topics: int = Query(default=20, ge=1, le=50, description="Maximum number of topics to store"),
    current_user: User = Depends(get_current_user),
    repository: TrendAnalysisRepository = Depends(get_trend_repository)
):
    """
    从Twitter抓取trending topics，使用LLM匹配相关话题，并存储到数据库
    """
    try:
        # 1. 获取Twitter凭证
        credentials = await get_twitter_credentials(current_user)
        
        # 2. 初始化Twitter客户端
        twitter_client = TwitterAPIClient(
            client_id=os.getenv('TWITTER_CLIENT_ID'),
            client_secret=os.getenv('TWITTER_CLIENT_SECRET')
        )
        
        # 3. 从Twitter获取trending topics（优先使用个性化趋势）
        logger.info(f"Fetching personalized trending topics (fallback location: {location_id})")
        raw_trends = twitter_client.get_trends(
            user_token=credentials.access_token, 
            location_id=location_id, 
            prefer_personalized=True,
            max_results=max_topics
        )
        
        if not raw_trends:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message": "No trending topics found on Twitter",
                    "stored_topics": []
                }
            )
        
        # 4. 获取数据库中的keywords (如果没有提供的话)
        if not keywords:
            # 从数据库获取用户的keywords或者系统默认keywords
            try:
                # 这里可以从用户配置或其他地方获取keywords
                # 暂时使用一些默认的keywords
                keywords = ["AI", "technology", "innovation", "business", "startup", "digital", "future"]
            except Exception as e:
                logger.warning(f"Failed to get keywords from database: {e}")
                keywords = ["AI", "technology", "innovation"]
        
        # 5. 使用LLM匹配相关topics
        matched_topics = []
        try:
            from modules.trend_analysis.llm_matcher import create_llm_trend_matcher
            import openai
            
            if os.getenv('OPENAI_API_KEY'):
                openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                llm_matcher = create_llm_trend_matcher(openai_client)
                
                # 使用LLM匹配
                trend_matches = llm_matcher.match_trends_with_keywords(
                    trends=raw_trends,
                    keywords=keywords,
                    max_matches=max_topics
                )
                
                # 转换为存储格式
                for match in trend_matches:
                    matched_topics.append({
                        "topic_name": match.trend_name,
                        "tweet_volume": match.trend_data.get('tweet_volume', 0),
                        "url": match.trend_data.get('url', ''),
                        "matching_keywords": match.semantic_keywords,
                        "matching_reasons": match.matching_reasons,
                        "relevance_score": match.relevance_score,
                        "confidence_score": match.relevance_score,
                        "location_id": location_id,
                        "source": "twitter_llm_matched"
                    })
                
                logger.info(f"LLM matching successful: {len(matched_topics)} topics matched")
            else:
                logger.warning("OpenAI API key not found, using traditional matching")
                raise Exception("OpenAI API key not available")
                
        except Exception as e:
            logger.warning(f"LLM matching failed, using traditional matching: {e}")
            
            # 传统关键词匹配作为fallback
            for trend in raw_trends:
                trend_name = trend.get('name', '').lower()
                trend_url = trend.get('url', '').lower()
                
                matching_keywords = []
                matching_reasons = []
                
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    if (keyword_lower in trend_name or 
                        keyword_lower in trend_url or
                        trend_name in keyword_lower):
                        matching_keywords.append(keyword)
                        matching_reasons.append(f"关键词 '{keyword}' 在话题名称中匹配")
                
                if matching_keywords:
                    matched_topics.append({
                        "topic_name": trend.get('name', ''),
                        "tweet_volume": trend.get('tweet_volume', 0),
                        "url": trend.get('url', ''),
                        "matching_keywords": matching_keywords,
                        "matching_reasons": matching_reasons,
                        "relevance_score": 0.6,  # 传统匹配的默认分数
                        "confidence_score": 0.6,
                        "location_id": location_id,
                        "source": "twitter_traditional_matched"
                    })
                
                if len(matched_topics) >= max_topics:
                    break
        
        # 6. 存储匹配的topics到数据库
        stored_topics = []
        for topic_data in matched_topics:
            try:
                # 使用repository存储topic
                stored_topic = await repository.store_trending_topic(
                    user_id=current_user.id,
                    topic_name=topic_data["topic_name"],
                    tweet_volume=topic_data["tweet_volume"],
                    url=topic_data.get("url"),
                    matching_keywords=topic_data["matching_keywords"],
                    relevance_score=topic_data["relevance_score"],
                    confidence_score=topic_data["confidence_score"],
                    location_id=topic_data["location_id"],
                    source=topic_data["source"],
                    metadata={
                        "matching_reasons": topic_data["matching_reasons"],
                        "fetched_at": datetime.now().isoformat()
                    }
                )
                
                if stored_topic:
                    stored_topics.append({
                        "id": stored_topic.id,
                        "topic_name": stored_topic.topic_name,
                        "tweet_volume": topic_data["tweet_volume"],
                        "matching_keywords": topic_data["matching_keywords"],
                        "relevance_score": topic_data["relevance_score"],
                        "stored_at": stored_topic.analyzed_at.isoformat() if stored_topic.analyzed_at else None
                    })
                    
            except Exception as e:
                logger.error(f"Failed to store topic '{topic_data['topic_name']}': {e}")
                continue
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Successfully fetched and stored {len(stored_topics)} trending topics",
                "total_twitter_trends": len(raw_trends),
                "matched_topics": len(matched_topics),
                "stored_topics": len(stored_topics),
                "keywords_used": keywords,
                "location_id": location_id,
                "topics": stored_topics
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch and store trending topics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch and store trending topics: {str(e)}"
        )

@router.get("/cached")
async def get_cached_trending_topics(
    keywords: List[str] = Query(default=[], description="Keywords to filter cached topics"),
    location_id: str = Query(default="1", description="Twitter location ID to filter"),
    limit: int = Query(default=10, ge=1, le=50, description="Number of topics to return"),
    max_age_hours: int = Query(default=24, ge=1, le=168, description="Maximum age of cached topics in hours"),
    current_user: User = Depends(get_current_user),
    repository: TrendAnalysisRepository = Depends(get_trend_repository)
):
    """
    获取数据库中缓存的trending topics
    """
    try:
        # 计算时间范围
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        # 从数据库获取缓存的topics
        if keywords:
            cached_topics = repository.get_trends_by_keywords(
                user_id=current_user.id,
                keywords=keywords,
                limit=limit,
                after_time=cutoff_time
            )
        else:
            cached_topics = repository.get_latest_trends_for_user(
                user_id=current_user.id,
                limit=limit,
                after_time=cutoff_time
            )
        
        # 转换为API响应格式
        topics_data = []
        for topic in cached_topics:
            topics_data.append({
                "id": topic.id,
                "topic_name": topic.topic_name,
                "tweet_volume": getattr(topic.metrics, 'tweet_volume', 0) if hasattr(topic, 'metrics') and topic.metrics else 0,
                "relevance_score": topic.niche_relevance_score or 0,
                "confidence_score": topic.confidence_score or 0,
                "analyzed_at": topic.analyzed_at.isoformat() if topic.analyzed_at else None,
                "source": "database_cached"
            })
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Retrieved {len(topics_data)} cached trending topics",
                "keywords_filter": keywords,
                "location_id": location_id,
                "max_age_hours": max_age_hours,
                "total_topics": len(topics_data),
                "topics": topics_data
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get cached trending topics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cached trending topics: {str(e)}"
        )

@router.get("/live")
async def get_live_trending_topics(
    location_id: str = Query(default="1", description="Twitter location ID"),
    keywords: List[str] = Query(default=[], description="Keywords to filter trends"),
    limit: int = Query(default=10, ge=1, le=50, description="Number of trends to return"),
    use_llm: bool = Query(default=True, description="Whether to use LLM for matching"),
    current_user: User = Depends(get_current_user)
):
    """
    实时从Twitter获取trending topics（不存储到数据库）
    """
    try:
        # 添加调试日志
        logger.info(f"🔍 Live trends request - Keywords: {keywords}, Use LLM: {use_llm}, Location: {location_id}")
        logger.info(f"🔍 Keywords type: {type(keywords)}, Length: {len(keywords)}")
        if keywords:
            logger.info(f"🔍 First keyword: '{keywords[0]}'")
        else:
            logger.info(f"🔍 No keywords provided - will return all trends without matching")
        # 尝试获取Twitter凭证
        credentials = None
        twitter_connected = False
        raw_trends = None
        
        try:
            credentials = await get_twitter_credentials(current_user)
            twitter_connected = True
            
            # 初始化Twitter客户端
            import os
            twitter_client = TwitterAPIClient(
                client_id=os.getenv('TWITTER_CLIENT_ID'),
                client_secret=os.getenv('TWITTER_CLIENT_SECRET')
            )
            
            # 获取trending topics（优先使用个性化趋势）
            raw_trends = twitter_client.get_trends(
                user_token=credentials.access_token, 
                location_id=location_id, 
                prefer_personalized=True,
                max_results=limit*2  # 获取更多数据以便筛选
            )
            
        except HTTPException as twitter_error:
            logger.warning(f"Twitter credentials not available: {twitter_error.detail}")
            logger.info("Attempting to retry Twitter authentication...")
            
            # 尝试重新验证Twitter凭证状态
            try:
                # 检查用户的Twitter连接状态
                from modules.user_profile import UserProfileService
                from modules.user_profile.repository import UserProfileRepository
                
                db_session = get_db_session()
                user_service = UserProfileService(UserProfileRepository(db_session), None)
                twitter_status = user_service.get_twitter_connection_status(current_user.id)
                
                if twitter_status.get('connected') and twitter_status.get('has_valid_token'):
                    logger.info("Twitter credentials found in database, retrying API call...")
                    credentials = user_service.repository.get_twitter_credentials(current_user.id)
                    
                    if credentials and credentials.access_token:
                        # 重新尝试Twitter API调用
                        import os
                        twitter_client = TwitterAPIClient(
                            client_id=os.getenv('TWITTER_CLIENT_ID'),
                            client_secret=os.getenv('TWITTER_CLIENT_SECRET')
                        )
                        raw_trends = twitter_client.get_trends(
                            user_token=credentials.access_token, 
                            location_id=location_id, 
                            prefer_personalized=True,
                            max_results=limit*2
                        )
                        twitter_connected = True
                        logger.info("Successfully retrieved Twitter trends on retry")
                    else:
                        raise Exception("Twitter credentials invalid")
                else:
                    raise Exception("Twitter not properly connected")
                    
            except Exception as retry_error:
                logger.warning(f"Twitter retry failed: {retry_error}")
                # 使用模拟数据作为fallback，匹配个性化趋势格式
                raw_trends = [
                    {"name": "AI Revolution", "tweet_volume": 125000, "url": "https://twitter.com/search?q=AI+Revolution", 
                     "category": "Technology", "trending_since": "2024-01-15T10:30:00Z", "source": "mock_personalized"},
                    {"name": "Tech Innovation", "tweet_volume": 89000, "url": "https://twitter.com/search?q=Tech+Innovation",
                     "category": "Technology", "trending_since": "2024-01-15T09:45:00Z", "source": "mock_personalized"},
                    {"name": "Smart Technology", "tweet_volume": 67000, "url": "https://twitter.com/search?q=Smart+Technology",
                     "category": "Technology", "trending_since": "2024-01-15T11:15:00Z", "source": "mock_personalized"},
                    {"name": "Digital Transformation", "tweet_volume": 54000, "url": "https://twitter.com/search?q=Digital+Transformation",
                     "category": "Business", "trending_since": "2024-01-15T08:20:00Z", "source": "mock_personalized"},
                    {"name": "Machine Learning", "tweet_volume": 43000, "url": "https://twitter.com/search?q=Machine+Learning",
                     "category": "Technology", "trending_since": "2024-01-15T12:00:00Z", "source": "mock_personalized"},
                    {"name": "Artificial Intelligence", "tweet_volume": 78000, "url": "https://twitter.com/search?q=Artificial+Intelligence",
                     "category": "Technology", "trending_since": "2024-01-15T07:30:00Z", "source": "mock_personalized"},
                    {"name": "Innovation Hub", "tweet_volume": 32000, "url": "https://twitter.com/search?q=Innovation+Hub",
                     "category": "Business", "trending_since": "2024-01-15T13:10:00Z", "source": "mock_personalized"},
                    {"name": "Future Tech", "tweet_volume": 28000, "url": "https://twitter.com/search?q=Future+Tech",
                     "category": "Technology", "trending_since": "2024-01-15T14:00:00Z", "source": "mock_personalized"},
                    {"name": "Smart Solutions", "tweet_volume": 25000, "url": "https://twitter.com/search?q=Smart+Solutions",
                     "category": "Business", "trending_since": "2024-01-15T15:30:00Z", "source": "mock_personalized"},
                    {"name": "Tech Startup", "tweet_volume": 21000, "url": "https://twitter.com/search?q=Tech+Startup",
                     "category": "Business", "trending_since": "2024-01-15T16:45:00Z", "source": "mock_personalized"}
                ]
                logger.info("Using mock trending data for demonstration, but will enable LLM matching")
        
        if not raw_trends:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message": "No trending topics found on Twitter",
                    "trends": []
                }
            )
        
        # 如果没有提供keywords，返回所有trends
        if not keywords:
            limited_trends = raw_trends[:limit]
            trends_data = []
            for trend in limited_trends:
                trends_data.append({
                    "name": trend.get('name', ''),
                    "tweet_volume": trend.get('tweet_volume', 0),
                    "url": trend.get('url', ''),
                    "source": "twitter_live_all" if twitter_connected else "mock_demo"
                })
            
            data_source = "twitter_live" if twitter_connected else "mock_demo"
            message = f"Retrieved {len(trends_data)} live trending topics"
            if twitter_connected:
                message += " from Twitter"
            else:
                message += " from demo data (connect Twitter for real data)"
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message": message,
                    "location_id": location_id,
                    "data_source": data_source,
                    "twitter_connected": twitter_status,
                    "total_available": len(raw_trends),
                    "trends": trends_data
                }
            )
        
        # 使用LLM或传统方法匹配keywords
        matched_trends = []
        llm_success = False
        
        logger.info(f"🚀 Starting trend matching - Use LLM: {use_llm}, Keywords: {keywords}")
        
        if use_llm:
            try:
                logger.info("Initializing LLM trend matching...")
                from modules.trend_analysis.llm_matcher import create_llm_trend_matcher
                import openai
                import os
                
                openai_api_key = os.getenv('OPENAI_API_KEY')
                if not openai_api_key:
                    logger.warning("OpenAI API key not found in environment variables")
                    # 检查可能的其他环境变量名
                    alternative_keys = ['OPENAI_KEY', 'OPENAI_SECRET_KEY', 'GPT_API_KEY']
                    for alt_key in alternative_keys:
                        alt_value = os.getenv(alt_key)
                        if alt_value:
                            openai_api_key = alt_value
                            logger.info(f"Found OpenAI API key in {alt_key}")
                            break
                    
                    if not openai_api_key:
                        raise Exception("OpenAI API key not available in any environment variable")
                
                logger.info("Creating OpenAI client and LLM matcher...")
                openai_client = openai.OpenAI(api_key=openai_api_key)
                llm_matcher = create_llm_trend_matcher(openai_client)
                
                logger.info(f"Using LLM to match {len(raw_trends)} trends with keywords: {keywords}")
                logger.info(f"Data source: {'Twitter API' if twitter_connected else 'Mock data (demo)'}")
                
                trend_matches = llm_matcher.match_trends_with_keywords(
                    trends=raw_trends,
                    keywords=keywords,
                    max_matches=limit
                )
                
                logger.info(f"LLM returned {len(trend_matches)} matches")
                
                for match in trend_matches:
                    matched_trends.append({
                        "name": match.trend_name,
                        "tweet_volume": match.trend_data.get('tweet_volume', 0),
                        "url": match.trend_data.get('url', ''),
                        "matching_keywords": match.semantic_keywords,
                        "matching_reasons": match.matching_reasons,
                        "relevance_score": match.relevance_score,
                        "source": "twitter_live_llm" if twitter_connected else "mock_demo_llm"
                    })
                
                llm_success = True
                logger.info(f"LLM matching successful: {len(matched_trends)} relevant trends found")
                    
            except Exception as e:
                logger.error(f"LLM matching failed: {str(e)}", exc_info=True)
                logger.warning("将回退到传统关键词匹配方法")
                logger.warning(f"错误详情: {type(e).__name__}: {str(e)}")
                use_llm = False
        
        # 传统匹配（如果LLM失败或被禁用）
        if not use_llm or not matched_trends:
            for trend in raw_trends:
                trend_name = trend.get('name', '').lower()
                trend_url = trend.get('url', '').lower()
                
                matching_keywords = []
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    if (keyword_lower in trend_name or 
                        keyword_lower in trend_url or
                        trend_name in keyword_lower):
                        matching_keywords.append(keyword)
                
                if matching_keywords:
                    matched_trends.append({
                        "name": trend.get('name', ''),
                        "tweet_volume": trend.get('tweet_volume', 0),
                        "url": trend.get('url', ''),
                        "matching_keywords": matching_keywords,
                        "relevance_score": 0.6,
                        "source": "twitter_live_traditional"
                    })
                
                if len(matched_trends) >= limit:
                    break
        
        data_source = "twitter_live" if twitter_connected else "mock_demo"
        message = f"Found {len(matched_trends)} matching live trends"
        if not twitter_connected:
            message += " (using demo data - connect Twitter for real data)"
        
        # 添加OpenAI配置状态检查
        import os
        openai_configured = bool(os.getenv('OPENAI_API_KEY'))
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": message,
                "keywords": keywords,
                "location_id": location_id,
                "matching_method": "llm" if llm_success else "traditional",
                "llm_attempted": use_llm,
                "llm_success": llm_success,
                "data_source": data_source,
                "twitter_connected": twitter_connected,
                "total_twitter_trends": len(raw_trends),
                "openai_configured": openai_configured,
                "trends": matched_trends[:limit]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get live trending topics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve live trending topics: {str(e)}"
        )

@router.delete("/cached/clear")
async def clear_cached_topics(
    older_than_hours: int = Query(default=48, ge=1, description="Clear topics older than specified hours"),
    current_user: User = Depends(get_current_user),
    repository: TrendAnalysisRepository = Depends(get_trend_repository)
):
    """
    清理缓存的trending topics
    """
    try:
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        
        # 删除旧的topics
        deleted_count = await repository.delete_old_trends(
            user_id=current_user.id,
            before_time=cutoff_time
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Successfully cleared {deleted_count} cached topics",
                "older_than_hours": older_than_hours,
                "cutoff_time": cutoff_time.isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to clear cached topics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cached topics: {str(e)}"
        )

@router.get("/status")
async def get_trending_status(
    current_user: User = Depends(get_current_user),
    repository: TrendAnalysisRepository = Depends(get_trend_repository)
):
    """
    获取trending analysis系统状态
    """
    try:
        # 获取数据库统计信息
        total_topics = await repository.get_topics_count()
        recent_topics = await repository.get_recent_topics_count(hours=24)
        
        # 获取最近的topics示例
        sample_topics = await repository.get_recent_topics(
            limit=3,
            user_id=current_user.id
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "active",
                "total_topics_stored": total_topics,
                "topics_last_24h": recent_topics,
                "sample_recent_topics": [
                    {
                        "topic_name": topic.topic_name,
                        "relevance_score": topic.relevance_score,
                        "created_at": topic.created_at.isoformat() if topic.created_at else None
                    }
                    for topic in sample_topics
                ],
                "last_updated": datetime.now().isoformat()
            }
        )
    
    except Exception as e:
        logger.error(f"Failed to get trending status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get trending status"
        )


# ===== 新的Gemini-powered API端点 =====

@router.post("/gemini/analyze")
async def analyze_trending_topics_with_gemini(
    keywords: List[str] = Query(..., description="用户关键词列表 (例如: ['AI', '效率', '创业'])"),
    user_context: Optional[str] = Query(None, description="可选的用户背景信息"),
    max_topics: int = Query(default=5, ge=1, le=10, description="返回的最大话题数量"),
    current_user: User = Depends(get_current_user)
):
    """
    使用Google Gemini分析基于关键词的互联网热门话题
    
    这是新的主要功能：
    1. 接收用户的关键词（如 "AI", "效率" 等）
    2. 使用Gemini LLM和Google Custom Search API
    3. 返回当前互联网上最热门的相关话题
    """
    try:
        # 验证Google API配置
        from config.settings import settings
        if not settings.validate_google_apis():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google API配置不完整。请联系管理员配置GEMINI_API_KEY、SEARCH_API_KEY和SEARCH_ENGINE_ID"
            )
        
        # 输入验证
        if not keywords or len(keywords) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供至少一个关键词"
            )
        
        if len(keywords) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="关键词数量不能超过10个"
            )
        
        logger.info(f"用户 {current_user.id} 请求分析关键词: {keywords}")
        
        # 创建Gemini分析器
        from modules.trend_analysis import create_gemini_trend_analyzer
        analyzer = create_gemini_trend_analyzer()
        
        # 执行分析
        analysis_result = analyzer.analyze_trending_topics(
            keywords=keywords,
            user_context=user_context
        )
        
        if not analysis_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"分析失败: {analysis_result.get('error', '未知错误')}"
            )
        
        # 返回结果
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "keywords": keywords,
                "user_context": user_context,
                "analysis": analysis_result["analysis"],
                "search_query_used": analysis_result.get("search_query", ""),
                "function_called": analysis_result.get("function_called"),
                "has_search_results": analysis_result.get("search_results") is not None,
                "timestamp": analysis_result["timestamp"],
                "user_id": current_user.id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gemini分析过程中发生错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析过程中发生内部错误: {str(e)}"
        )


@router.post("/gemini/summary")
async def get_trending_topics_summary_with_gemini(
    keywords: List[str] = Query(..., description="用户关键词列表"),
    user_context: Optional[str] = Query(None, description="用户背景信息"),
    max_topics: int = Query(default=5, ge=1, le=10, description="最大话题数量"),
    current_user: User = Depends(get_current_user)
):
    """
    获取结构化的热门话题总结（包含标题、描述、相关性评分等）
    """
    try:
        # 验证配置
        from config.settings import settings
        if not settings.validate_google_apis():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google API配置不完整"
            )
        
        # 输入验证
        if not keywords:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供关键词"
            )
        
        logger.info(f"用户 {current_user.id} 请求结构化总结，关键词: {keywords}")
        
        # 创建分析器并获取总结
        from modules.trend_analysis import create_gemini_trend_analyzer
        analyzer = create_gemini_trend_analyzer()
        
        summary_result = analyzer.get_trending_summary(
            keywords=keywords,
            max_topics=max_topics,
            user_context=user_context
        )
        
        if not summary_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取总结失败: {summary_result.get('error', '未知错误')}"
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "keywords": keywords,
                "max_topics": max_topics,
                "raw_analysis": summary_result["raw_analysis"],
                "structured_summary": summary_result.get("structured_summary"),
                "summary_error": summary_result.get("summary_error"),
                "has_search_results": summary_result.get("search_results") is not None,
                "timestamp": summary_result["timestamp"],
                "user_id": current_user.id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取总结时发生错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取总结时发生内部错误: {str(e)}"
        )


@router.get("/gemini/quick-demo")
async def quick_demo_trending_analysis(
    current_user: User = Depends(get_current_user)
):
    """
    快速演示Gemini热门话题分析功能
    使用预设的关键词进行演示
    """
    try:
        # 预设的演示关键词
        demo_keywords = ["AI", "创业", "效率工具"]
        demo_context = "科技创业者，关注最新的技术趋势和商业机会"
        
        logger.info(f"用户 {current_user.id} 请求快速演示")
        
        # 快速分析
        from modules.trend_analysis import quick_analyze_trending_topics
        
        result = quick_analyze_trending_topics(
            keywords=demo_keywords,
            user_context=demo_context
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "demo": True,
                "message": "这是一个演示，展示基于关键词的热门话题分析",
                "demo_keywords": demo_keywords,
                "demo_context": demo_context,
                "result": result,
                "note": "要使用自定义关键词，请调用 /api/trends/gemini/analyze 端点",
                "user_id": current_user.id
            }
        )
        
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "demo": True,
                "success": False,
                "error": str(e),
                "message": "演示失败，可能是因为缺少Google API配置",
                "note": "请确保设置了GEMINI_API_KEY、GOOGLE_SEARCH_API_KEY和GOOGLE_SEARCH_ENGINE_ID环境变量"
            }
        )


@router.get("/gemini/config-check")
async def check_gemini_configuration(
    current_user: User = Depends(get_current_user)
):
    """
    检查Gemini配置状态
    """
    try:
        from config.settings import settings
        
        config_status = {
            "gemini_api_key": bool(settings.GEMINI_API_KEY),
            "google_search_api_key": bool(settings.GOOGLE_SEARCH_API_KEY),
            "google_search_engine_id": bool(settings.GOOGLE_SEARCH_ENGINE_ID),
        }
        
        all_configured = all(config_status.values())
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "configured": all_configured,
                "config_status": config_status,
                "message": "所有配置完整" if all_configured else "部分配置缺失",
                "required_env_vars": [
                    "GEMINI_API_KEY",
                    "GOOGLE_SEARCH_API_KEY", 
                    "GOOGLE_SEARCH_ENGINE_ID"
                ],
                "instructions": {
                    "gemini_api_key": "从 Google AI Studio 获取",
                    "google_search_api_key": "从 Google Cloud Console 创建",
                    "google_search_engine_id": "从 Programmable Search Engine 获取"
                }
            }
        )
        
    except Exception as e:
        logger.error(f"检查配置时发生错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="无法检查配置状态"
        )