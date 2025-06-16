"""Trend Analysis API Routes

This module implements the FastAPI routes for trend analysis,
handling trend detection, analysis and reporting.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse
import logging

from database import get_data_flow_manager, DataFlowManager
from api.middleware import get_current_user, User

from modules.trend_analysis.engine import TrendAnalysisEngine
from modules.trend_analysis.repository import TrendAnalysisRepository
from modules.twitter_api import TwitterAPIClient

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/trends", tags=["trend-analysis"])

# Dependencies
async def get_trend_analysis_engine(
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager)
) -> TrendAnalysisEngine:
    """Get trend analysis engine with dependencies"""
    try:
        return TrendAnalysisEngine(data_flow_manager)
    except Exception as e:
        logger.error(f"Failed to create trend analysis engine: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize trend analysis engine"
        )

async def get_twitter_client(
    current_user: User = Depends(get_current_user)
) -> TwitterAPIClient:
    """Get Twitter client for current user"""
    try:
        return TwitterAPIClient(current_user.twitter_access_token)
    except Exception as e:
        logger.error(f"Failed to create Twitter client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize Twitter client"
        )

async def get_trend_repository(
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager)
) -> TrendAnalysisRepository:
    """Get trend repository with dependencies"""
    try:
        # DataFlowManager already has db_session, use it directly
        return TrendAnalysisRepository(data_flow_manager.db_session)
    except Exception as e:
        logger.error(f"Failed to create trend repository: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize trend repository"
        )

@router.post("/analyze")
async def analyze_trends(
    keywords: List[str] = Query(..., description="Keywords to analyze"),
    timeframe: str = Query(default="24h", description="Analysis timeframe"),
    current_user: User = Depends(get_current_user),
    engine: TrendAnalysisEngine = Depends(get_trend_analysis_engine),
    twitter_client: TwitterAPIClient = Depends(get_twitter_client)
):
    """Analyze trends based on keywords and timeframe"""
    try:
        results = await engine.analyze_trends(keywords, timeframe, twitter_client)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Trend analysis completed successfully",
                "results": results
            }
        )
    except Exception as e:
        logger.error(f"Trend analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze trends"
        )

@router.get("/latest")
async def get_latest_trends(
    limit: int = Query(default=10, ge=1, le=50, description="Number of trends to return"),
    current_user: User = Depends(get_current_user),
    repository: TrendAnalysisRepository = Depends(get_trend_repository)
):
    """Get latest trending topics"""
    try:
        trends = repository.get_latest_trends_for_user(current_user.id, limit)
        # Convert AnalyzedTrend objects to dict format
        trends_data = []
        for trend in trends:
            trends_data.append({
                "id": trend.id,
                "name": trend.topic_name,
                "tweet_volume": getattr(trend.metrics, 'tweet_volume', 0) if hasattr(trend, 'metrics') and trend.metrics else 0,
                "sentiment_score": trend.confidence_score,
                "description": f"分析的趋势话题: {trend.topic_name}",
                "relevance_score": trend.niche_relevance_score,
                "potential_score": trend.trend_potential_score,
                "analyzed_at": trend.analyzed_at.isoformat() if trend.analyzed_at else None
            })
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Latest trends retrieved successfully",
                "trends": trends_data
            }
        )
    except Exception as e:
        logger.error(f"Failed to get latest trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve latest trends"
        )

@router.get("/micro-trends")
async def get_micro_trends(
    industry: str = Query(..., description="Industry to analyze"),
    current_user: User = Depends(get_current_user),
    engine: TrendAnalysisEngine = Depends(get_trend_analysis_engine)
):
    """Get micro-trends for specific industry"""
    try:
        trends = await engine.get_micro_trends(industry)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Micro-trends retrieved successfully",
                "industry": industry,
                "trends": trends
            }
        )
    except Exception as e:
        logger.error(f"Failed to get micro-trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve micro-trends"
        )

@router.get("/search")
async def search_trends(
    query: str = Query(..., description="Search query"),
    current_user: User = Depends(get_current_user),
    repository: TrendAnalysisRepository = Depends(get_trend_repository)
):
    """Search for trends"""
    try:
        results = await repository.search_trends(query)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Trend search completed successfully",
                "query": query,
                "results": results
            }
        )
    except Exception as e:
        logger.error(f"Trend search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search trends"
        )

@router.get("/statistics")
async def get_trend_statistics(
    current_user: User = Depends(get_current_user),
    engine: TrendAnalysisEngine = Depends(get_trend_analysis_engine)
):
    """Get trend analysis statistics"""
    try:
        stats = await engine.get_statistics()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Trend statistics retrieved successfully",
                "statistics": stats
            }
        )
    except Exception as e:
        logger.error(f"Failed to get trend statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trend statistics"
        )

@router.get("/{trend_id}")
async def get_trend_details(
    trend_id: str = Path(..., description="Trend ID"),
    current_user: User = Depends(get_current_user),
    repository: TrendAnalysisRepository = Depends(get_trend_repository)
):
    """Get detailed information about a specific trend"""
    try:
        trend = await repository.get_trend_details(trend_id)
        if not trend:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trend not found"
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Trend details retrieved successfully",
                "trend": trend
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get trend details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trend details"
        )

@router.get("/config")
async def get_analysis_config(
    current_user: User = Depends(get_current_user),
    engine: TrendAnalysisEngine = Depends(get_trend_analysis_engine)
):
    """Get trend analysis configuration"""
    try:
        config = await engine.get_config()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Analysis config retrieved successfully",
                "config": config
            }
        )
    except Exception as e:
        logger.error(f"Failed to get analysis config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analysis config"
        )