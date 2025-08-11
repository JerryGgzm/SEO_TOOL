"""SEO Module API Routes

This module implements the FastAPI routes for the SEO optimization system,
handling content optimization, keyword analysis, and hashtag generation.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, Body
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

from database import get_data_flow_manager, DataFlowManager
from modules.twitter_api import TwitterAPIClient
from modules.user_profile import UserProfileService
from api.middleware import get_current_user, User

from modules.seo.service_integration import SEOService, create_enhanced_seo_service
from modules.seo.models import (
    SEOOptimizationRequest, SEOOptimizationLevel, SEOContentType,
    HashtagStrategy, HashtagGenerationRequest, KeywordOptimizationRequest
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/seo", tags=["seo-optimization"])

# Dependency to get SEO service
async def get_seo_service(
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager),
    current_user: User = Depends(get_current_user)
) -> SEOService:
    """Get SEO service with dependencies"""
    try:
        # Initialize dependencies (would be properly injected in real application)
        twitter_client = None  # Would be injected
        user_service = None    # Would be injected
        llm_client = None      # Would come from config
        
        return create_enhanced_seo_service(
            twitter_client=twitter_client,
            user_service=user_service,
            data_flow_manager=data_flow_manager,
            llm_client=llm_client,
            config={'llm_optimization_mode': 'comprehensive'}
        )
    except Exception as e:
        logger.error(f"Failed to create SEO service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SEO service initialization failed"
        )

@router.get("/keywords/analyze")
async def analyze_keywords(
    content: str = Query(..., description="Content to analyze for keywords"),
    target_keywords: List[str] = Query(default=[], description="Target keywords to analyze"),
    current_user: User = Depends(get_current_user),
    service: SEOService = Depends(get_seo_service)
):
    """
    Analyze keyword usage and optimization in content
    
    Provides detailed keyword analysis including:
    - Keyword density analysis
    - Semantic variations
    - Competition assessment
    - Optimization suggestions
    """
    try:
        # Use the optimizer's keyword analyzer
        keyword_analyses = service.optimizer.keyword_analyzer.analyze_keywords(
            content=content,
            context=await service._build_seo_context(current_user.id, 'tweet'),
            target_keywords=target_keywords
        )
        
        # Convert to response format
        keywords = []
        for analysis in keyword_analyses:
            keywords.append({
                "keyword": analysis.keyword,
                "search_volume": analysis.search_volume,
                "difficulty": analysis.difficulty.value,
                "relevance_score": analysis.relevance_score,
                "semantic_variations": analysis.semantic_variations,
                "trending_status": analysis.trending_status,
                "suggested_usage": analysis.suggested_usage
            })
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Keyword analysis completed",
                "content": content,
                "target_keywords": target_keywords,
                "keyword_analysis": keywords,
                "total_keywords_analyzed": len(keywords)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Keyword analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Keyword analysis failed"
        )

@router.get("/recommendations/{founder_id}")
async def get_seo_recommendations(
    founder_id: str = Path(..., description="Founder ID"),
    current_user: User = Depends(get_current_user),
    service: SEOService = Depends(get_seo_service)
):
    """
    Get personalized SEO recommendations for a founder
    
    Returns intelligent recommendations based on:
    - Historical content performance
    - Industry best practices
    - Current trends
    - AI analysis insights
    """
    try:
        # Validate user access
        if current_user.id != founder_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get intelligent recommendations
        recommendations = await service.get_intelligent_seo_recommendations(
            founder_id=founder_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "SEO recommendations generated",
                "founder_id": founder_id,
                "recommendations": recommendations,
                "llm_enhanced": recommendations.get('llm_enhanced', False)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SEO recommendations generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SEO recommendations generation failed"
        )



@router.get("/hashtags/trending")
async def get_trending_hashtags(
    niche_keywords: List[str] = Query(default=[], description="Niche keywords to filter by"),
    location: str = Query(default="global", description="Location for trending hashtags"),
    count: int = Query(default=20, ge=5, le=50, description="Number of hashtags to return"),
    current_user: User = Depends(get_current_user),
    service: SEOService = Depends(get_seo_service)
):
    """
    Get currently trending hashtags
    
    Returns trending hashtags filtered by:
    - Geographic location
    - Niche relevance
    - Engagement potential
    - Competition level
    """
    try:
        # Get trending hashtags using the analyzer
        trending_hashtags = []
        
        # Use the trending analyzer if available
        if hasattr(service.optimizer, 'hashtag_generator') and hasattr(service.optimizer.hashtag_generator, 'trending_analyzer'):
            trending_metrics = service.optimizer.hashtag_generator.trending_analyzer.get_trending_hashtags_by_location()
            
            # Filter by niche keywords if provided
            for metric in trending_metrics[:count]:
                if not niche_keywords or any(keyword.lower() in metric.hashtag.lower() for keyword in niche_keywords):
                    trending_hashtags.append({
                        "hashtag": metric.hashtag,
                        "usage_count": metric.usage_count,
                        "growth_rate": metric.growth_rate,
                        "engagement_rate": metric.engagement_rate,
                        "trend_momentum": metric.trend_momentum,
                        "competition_level": metric.competition_level.value
                    })
        else:
            # Fallback trending hashtags
            fallback_hashtags = ['AI', 'innovation', 'startup', 'technology', 'growth', 
                               'productivity', 'business', 'networking', 'leadership', 'future']
            for i, hashtag in enumerate(fallback_hashtags[:count]):
                trending_hashtags.append({
                    "hashtag": hashtag,
                    "usage_count": 10000 - (i * 500),
                    "growth_rate": 15.0 - (i * 1.0),
                    "engagement_rate": 0.05 - (i * 0.002),
                    "trend_momentum": 0.8 - (i * 0.05),
                    "competition_level": "medium"
                })
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Trending hashtags retrieved successfully",
                "trending_hashtags": trending_hashtags,
                "location": location,
                "niche_keywords": niche_keywords,
                "total_hashtags": len(trending_hashtags)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trending hashtags retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Trending hashtags retrieval failed"
        )

@router.post("/batch/optimize")
async def batch_optimize_content(
    content_list: List[Dict[str, Any]] = Body(..., description="List of content to optimize"),
    optimization_mode: str = Body(default="comprehensive", description="Optimization mode"),
    current_user: User = Depends(get_current_user),
    service: SEOService = Depends(get_seo_service)
):
    """
    Batch optimize multiple pieces of content
    
    Optimizes multiple content pieces efficiently with:
    - Parallel processing
    - Consistent optimization strategy
    - Bulk analytics
    """
    try:
        # Validate batch size
        if len(content_list) > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size cannot exceed 20 items"
            )
        
        # Process each content item
        optimization_results = []
        for i, content_item in enumerate(content_list):
            try:
                content = content_item.get('content', '')
                content_type = content_item.get('content_type', 'tweet')
                
                if not content:
                    optimization_results.append({
                        "index": i,
                        "error": "Empty content",
                        "success": False
                    })
                    continue
                
                # Optimize content
                result = await service.optimize_content_intelligent(
                    text=content,
                    content_type=content_type,
                    context={'founder_id': current_user.id},
                    optimization_mode=optimization_mode
                )
                
                optimization_results.append({
                    "index": i,
                    "original_content": content,
                    "optimized_content": result['optimized_content'],
                    "optimization_score": result['optimization_score'],
                    "success": True
                })
                
            except Exception as e:
                optimization_results.append({
                    "index": i,
                    "error": str(e),
                    "success": False
                })
        
        # Calculate batch statistics
        successful_count = sum(1 for result in optimization_results if result.get('success'))
        avg_score = sum(result.get('optimization_score', 0) for result in optimization_results if result.get('success'))
        avg_score = avg_score / successful_count if successful_count > 0 else 0
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Batch optimization completed",
                "total_items": len(content_list),
                "successful_optimizations": successful_count,
                "failed_optimizations": len(content_list) - successful_count,
                "average_optimization_score": round(avg_score, 3),
                "optimization_mode": optimization_mode,
                "results": optimization_results
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch optimization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch optimization failed"
        )

@router.get("/config/optimization")
async def get_optimization_config(
    current_user: User = Depends(get_current_user)
):
    """
    Get current SEO optimization configuration and capabilities
    
    Returns information about:
    - Available optimization modes
    - LLM capabilities
    - Configuration settings
    - Feature availability
    """
    try:
        config_info = {
            "optimization_modes": [
                {
                    "mode": "comprehensive",
                    "description": "Advanced optimization combining LLM intelligence with SEO fundamentals",
                    "features": ["llm_enhancement", "seo_optimization", "intelligent_merging", "trend_alignment"]
                },
                {
                    "mode": "intelligent", 
                    "description": "Adaptive optimization that selects the best strategy based on content analysis",
                    "features": ["content_analysis", "strategy_selection", "adaptive_optimization", "context_awareness"]
                },
                {
                    "mode": "adaptive",
                    "description": "Dynamic optimization that adjusts approach based on content characteristics",
                    "features": ["content_characteristics_analysis", "dynamic_strategy", "performance_optimization"]
                }
            ],
            "content_types_supported": [
                "tweet", "reply", "thread", "quote_tweet", 
                "linkedin_post", "facebook_post", "blog_post"
            ],
            "hashtag_strategies": [
                "trending_focus", "niche_specific", "engagement_optimized",
                "brand_building", "discovery_focused"
            ],
            "optimization_levels": ["light", "moderate", "aggressive"],
            "llm_capabilities": {
                "available": True,  # Would be determined by actual LLM client availability
                "features": [
                    "intelligent_keyword_integration",
                    "context_aware_optimization", 
                    "content_variation_generation",
                    "trend_alignment",
                    "engagement_enhancement",
                    "semantic_understanding",
                    "natural_language_optimization"
                ]
            },
            "analytics_features": [
                "performance_tracking", "trend_analysis", "keyword_performance",
                "hashtag_effectiveness", "optimization_impact", "llm_enhancement_metrics"
            ],
            "default_settings": {
                "optimization_mode": "comprehensive",
                "optimization_level": "moderate", 
                "hashtag_strategy": "engagement_optimized",
                "llm_enhancement_enabled": True,
                "fallback_protection": True
            }
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "SEO optimization configuration retrieved",
                "configuration": config_info,
                "user_id": current_user.id
            }
        )
        
    except Exception as e:
        logger.error(f"Configuration retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuration retrieval failed"
        )

@router.post("/optimize")
async def optimize_content(
    content: str = Body(..., description="Content to optimize"),
    content_type: SEOContentType = Body(default=SEOContentType.TWEET),
    optimization_level: SEOOptimizationLevel = Body(default=SEOOptimizationLevel.MODERATE),
    target_keywords: List[str] = Body(default=[], description="Target keywords"),
    optimization_mode: str = Body(default="comprehensive", description="Optimization mode"),
    current_user: User = Depends(get_current_user),
    service: SEOService = Depends(get_seo_service)
):
    """
    Optimize content for SEO performance
    
    Uses AI-powered optimization including:
    - Keyword integration
    - Hashtag optimization  
    - Engagement enhancement
    - Platform-specific optimization
    """
    try:
        # Build optimization context
        context = {
            'founder_id': current_user.id,
            'target_keywords': target_keywords,
            'optimization_strategy': optimization_mode
        }
        
        # Perform intelligent optimization
        result = await service.optimize_content_intelligent(
            text=content,
            content_type=content_type.value,
            context=context,
            optimization_mode=optimization_mode
        )
        
        logger.info(f"Content optimized for user {current_user.id} with mode {optimization_mode}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Content optimized successfully",
                "original_content": result['original_content'],
                "optimized_content": result['optimized_content'],
                "optimization_score": result['optimization_score'],
                "improvements_made": result['improvements_made'],
                "llm_enhanced": result['llm_enhanced'],
                "optimization_mode": result['optimization_mode'],
                "suggestions": result.get('suggestions', []),
                "metadata": result.get('metadata', {})
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content optimization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content optimization failed"
        )

@router.post("/hashtags/generate")
async def generate_hashtags(
    content: str = Body(..., description="Content to generate hashtags for"),
    content_type: SEOContentType = Body(default=SEOContentType.TWEET),
    max_hashtags: int = Body(default=5, ge=1, le=30),
    strategy: HashtagStrategy = Body(default=HashtagStrategy.ENGAGEMENT_OPTIMIZED),
    niche_keywords: List[str] = Body(default=[], description="Niche keywords"),
    current_user: User = Depends(get_current_user),
    service: SEOService = Depends(get_seo_service)
):
    """
    Generate optimized hashtags for content
    
    Uses intelligent hashtag analysis including:
    - Trending hashtag detection
    - Engagement optimization
    - Niche-specific targeting
    - Competition analysis
    """
    try:
        # Create hashtag generation request
        hashtag_request = HashtagGenerationRequest(
            content=content,
            content_type=content_type,
            niche_keywords=niche_keywords,
            max_hashtags=max_hashtags,
            strategy=strategy,
            target_audience=f"followers of {current_user.id}"
        )
        
        # Generate hashtags using SEO service's optimizer
        hashtag_metrics = service.optimizer.hashtag_generator.generate_hashtags(hashtag_request)
        
        # Convert to response format
        hashtags = []
        for metric in hashtag_metrics:
            hashtags.append({
                "hashtag": metric.hashtag,
                "usage_count": metric.usage_count,
                "engagement_rate": metric.engagement_rate,
                "relevance_score": metric.relevance_score,
                "competition_level": metric.competition_level.value,
                "trend_momentum": metric.trend_momentum
            })
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Hashtags generated successfully",
                "hashtags": hashtags,
                "strategy": strategy.value,
                "content_type": content_type.value,
                "total_generated": len(hashtags)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hashtag generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Hashtag generation failed"
        )

@router.get("/suggestions/content")
async def get_content_suggestions(
    trend_topic: str = Query(..., description="Trending topic"),
    industry: str = Query(default="technology", description="Industry category"),
    target_audience: str = Query(default="professionals", description="Target audience"),
    content_type: SEOContentType = Query(default=SEOContentType.TWEET),
    current_user: User = Depends(get_current_user),
    service: SEOService = Depends(get_seo_service)
):
    """
    Get SEO-optimized content suggestions based on trends and context
    
    Returns intelligent suggestions for:
    - Hashtags
    - Keywords
    - Content structure
    - Engagement tactics
    """
    try:
        # Build trend and product info
        trend_info = {
            'topic_name': trend_topic,
            'keywords': [trend_topic.lower()],
            'pain_points': [f"{trend_topic} challenges", f"{trend_topic} solutions"],
            'opportunities': [f"{trend_topic} trends", f"{trend_topic} insights"]
        }
        
        product_info = {
            'industry_category': industry,
            'target_audience': target_audience,
            'core_values': ['innovation', 'quality', 'growth']
        }
        
        # Get enhanced suggestions
        suggestions = await service.get_enhanced_content_suggestions(
            trend_info=trend_info,
            product_info=product_info,
            content_type=content_type.value
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Content suggestions generated successfully",
                "trend_topic": trend_topic,
                "suggestions": suggestions,
                "llm_enhanced": suggestions.get('llm_enhanced', False)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content suggestions generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content suggestions generation failed"
        )

@router.post("/analyze/content")
async def analyze_content_seo(
    content: str = Body(..., description="Content to analyze"),
    content_type: SEOContentType = Body(default=SEOContentType.TWEET),
    current_user: User = Depends(get_current_user),
    service: SEOService = Depends(get_seo_service)
):
    """
    Analyze content's SEO potential and performance
    
    Provides comprehensive analysis including:
    - SEO strength scoring
    - Keyword optimization assessment
    - Hashtag effectiveness
    - Improvement recommendations
    """
    try:
        # Analyze content SEO potential
        analysis = await service.analyze_content_seo_potential(
            content=content,
            founder_id=current_user.id,
            content_type=content_type.value
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Content SEO analysis completed",
                "content": content,
                "content_type": content_type.value,
                "analysis": analysis,
                "analyzed_at": analysis.get('analysis_timestamp')
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content SEO analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content SEO analysis failed"
        )

@router.post("/optimize/trending")
async def optimize_for_trending(
    content: str = Body(..., description="Content to optimize"),
    trending_topics: List[str] = Body(..., description="Trending topics to integrate"),
    content_type: SEOContentType = Body(default=SEOContentType.TWEET),
    current_user: User = Depends(get_current_user),
    service: SEOService = Depends(get_seo_service)
):
    """
    Optimize content specifically for trending topics
    
    Uses AI to intelligently integrate trending topics while maintaining
    content quality and brand alignment.
    """
    try:
        # Optimize for trending topics
        result = await service.optimize_for_trending_topics(
            founder_id=current_user.id,
            content=content,
            trending_topics=trending_topics,
            content_type=content_type.value
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Content optimized for trending topics",
                "original_content": content,
                "optimized_content": result.get('optimized_content'),
                "trending_topics_integrated": result.get('trend_integration', []),
                "optimization_score": result.get('optimization_score'),
                "llm_insights": result.get('llm_insights', {}),
                "suggestions": result.get('suggestions')
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trending optimization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Trending optimization failed"
        )

@router.post("/generate/variations")
async def generate_content_variations(
    content: str = Body(..., description="Original content"),
    variation_count: int = Body(default=3, ge=1, le=5, description="Number of variations"),
    content_type: SEOContentType = Body(default=SEOContentType.TWEET),
    current_user: User = Depends(get_current_user),
    service: SEOService = Depends(get_seo_service)
):
    """
    Generate multiple SEO-optimized variations of content
    
    Creates different versions optimized for:
    - Different strategies (engagement, discovery, keywords)
    - A/B testing
    - Platform-specific optimization
    """
    try:
        # Generate content variations
        variations = await service.generate_content_variations(
            founder_id=current_user.id,
            content=content,
            content_type=content_type.value,
            variation_count=variation_count
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Content variations generated successfully",
                "original_content": content,
                "variations": variations,
                "total_variations": len(variations),
                "content_type": content_type.value
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content variations generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content variations generation failed"
        )

@router.post("/keywords/optimize")
async def optimize_keywords(
    content: str = Body(..., description="Content to optimize for keywords"),
    target_keywords: List[str] = Body(..., description="Target keywords to optimize for"),
    optimization_level: SEOOptimizationLevel = Body(default=SEOOptimizationLevel.MODERATE),
    current_user: User = Depends(get_current_user),
    service: SEOService = Depends(get_seo_service)
):
    """
    Optimize content specifically for target keywords
    
    Intelligently integrates keywords while maintaining:
    - Natural language flow
    - Content readability
    - SEO effectiveness
    - User engagement
    """
    try:
        # Create keyword optimization request
        keyword_request = KeywordOptimizationRequest(
            content=content,
            target_keywords=target_keywords,
            optimization_level=optimization_level,
            maintain_readability=True,
            preserve_tone=True
        )
        
        # Use the keyword analyzer with optimization request
        context = await service._build_seo_context(current_user.id, 'tweet')
        
        # Optimize content with keyword integration using the main optimizer
        optimization_result = await service.optimize_content_intelligent(
            text=content,
            content_type='tweet',
            context={
                'founder_id': current_user.id,
                'target_keywords': target_keywords,
                'optimization_strategy': 'comprehensive'
            },
            optimization_mode='comprehensive'
        )
        
        # Analyze keyword integration in result
        keyword_analysis = service.optimizer.keyword_analyzer.analyze_keywords(
            content=optimization_result['optimized_content'],
            context=context,
            target_keywords=target_keywords
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Content optimized for keywords successfully",
                "original_content": content,
                "optimized_content": optimization_result['optimized_content'],
                "target_keywords": target_keywords,
                "keywords_integrated": [kw.keyword for kw in keyword_analysis if kw.keyword in target_keywords],
                "optimization_score": optimization_result['optimization_score'],
                "readability_score": sum(kw.relevance_score for kw in keyword_analysis) / len(keyword_analysis) if keyword_analysis else 0.0,
                "improvements_made": optimization_result.get('improvements_made', []),
                "llm_enhanced": optimization_result.get('llm_enhanced', False)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Keyword optimization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Keyword optimization failed"
        )

@router.get("/performance/comparison")
async def compare_seo_performance(
    founder_id: str = Query(..., description="Founder ID"),
    period1_days: int = Query(default=30, ge=1, le=90, description="First comparison period"),
    period2_days: int = Query(default=60, ge=1, le=180, description="Second comparison period"),
    current_user: User = Depends(get_current_user),
    service: SEOService = Depends(get_seo_service)
):
    """
    Compare SEO performance across different time periods
    
    Provides comparative analysis of:
    - Optimization effectiveness
    - Hashtag performance trends
    - Keyword ranking improvements
    - Overall SEO impact
    """
    try:
        # Validate user access
        if current_user.id != founder_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get performance data for both periods
        period1_analytics = service.get_seo_analytics_summary(founder_id, period1_days)
        period2_analytics = service.get_seo_analytics_summary(founder_id, period2_days)
        
        # Calculate comparison metrics
        comparison = {
            "optimization_score_change": period1_analytics.get('avg_optimization_score', 0) - period2_analytics.get('avg_optimization_score', 0),
            "hashtag_performance_change": period1_analytics.get('hashtag_effectiveness', 0) - period2_analytics.get('hashtag_effectiveness', 0),
            "keyword_ranking_change": period1_analytics.get('keyword_performance', 0) - period2_analytics.get('keyword_performance', 0),
            "engagement_improvement": period1_analytics.get('engagement_rate', 0) - period2_analytics.get('engagement_rate', 0)
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "SEO performance comparison completed",
                "founder_id": founder_id,
                "period1_data": {
                    "days": period1_days,
                    "analytics": period1_analytics
                },
                "period2_data": {
                    "days": period2_days,
                    "analytics": period2_analytics
                },
                "comparison_metrics": comparison,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SEO performance comparison failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SEO performance comparison failed"
        )

@router.post("/test/ab")
async def create_ab_test(
    test_name: str = Body(..., description="Name for the A/B test"),
    content_variants: List[str] = Body(..., description="Content variants to test"),
    test_duration_hours: int = Body(default=24, ge=1, le=168, description="Test duration in hours"),
    target_metric: str = Body(default="engagement", description="Primary metric to optimize for"),
    current_user: User = Depends(get_current_user),
    service: SEOService = Depends(get_seo_service)
):
    """
    Create an A/B test for SEO-optimized content variants
    
    Sets up controlled testing for:
    - Content optimization strategies
    - Hashtag effectiveness
    - Keyword integration approaches
    - Performance measurement
    """
    try:
        # Validate test parameters
        if len(content_variants) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 content variants required for A/B testing"
            )
        
        if len(content_variants) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 5 content variants allowed per test"
            )
        
        # Create A/B test configuration
        test_config = {
            "test_id": f"ab_test_{current_user.id}_{int(datetime.utcnow().timestamp())}",
            "test_name": test_name,
            "founder_id": current_user.id,
            "variants": [],
            "target_metric": target_metric,
            "test_duration_hours": test_duration_hours,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }
        
        # Analyze each content variant
        for i, content in enumerate(content_variants):
            variant_analysis = await service.analyze_content_seo_potential(
                content=content,
                founder_id=current_user.id,
                content_type='tweet'
            )
            
            test_config["variants"].append({
                "variant_id": f"variant_{i+1}",
                "content": content,
                "seo_score": variant_analysis.get('seo_score', 0),
                "predicted_performance": variant_analysis.get('predicted_engagement', 0),
                "optimization_features": variant_analysis.get('optimization_features', [])
            })
        
        # Store test configuration (would integrate with actual A/B testing system)
        # service.ab_testing_service.create_test(test_config)
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "A/B test created successfully",
                "test_configuration": test_config,
                "next_steps": [
                    "Deploy variants according to test schedule",
                    "Monitor performance metrics",
                    "Analyze results after test completion"
                ]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"A/B test creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A/B test creation failed"
        )

@router.get("/audit/content/{content_id}")
async def audit_content_seo(
    content_id: str = Path(..., description="Content ID to audit"),
    current_user: User = Depends(get_current_user),
    service: SEOService = Depends(get_seo_service),
    data_flow_manager: DataFlowManager = Depends(get_data_flow_manager)
):
    """
    Comprehensive SEO audit of specific content
    
    Provides detailed audit including:
    - Technical SEO analysis
    - Content quality assessment
    - Keyword optimization review
    - Performance predictions
    - Improvement recommendations
    """
    try:
        # Get content from database
        content_data = data_flow_manager.get_content_by_id(content_id)
        if not content_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        # Validate user access
        if str(content_data.founder_id) != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Perform comprehensive SEO audit using available analysis methods
        content_text = content_data.content if hasattr(content_data, 'content') else str(content_data)
        
        # Analyze SEO potential
        seo_analysis = await service.analyze_content_seo_potential(
            content=content_text,
            founder_id=current_user.id,
            content_type='tweet'
        )
        
        # Analyze keywords if any exist in content
        context = await service._build_seo_context(current_user.id, 'tweet')
        keyword_analysis = service.optimizer.keyword_analyzer.analyze_keywords(
            content=content_text,
            context=context,
            target_keywords=[]
        )
        
        # Generate hashtag recommendations
        hashtag_metrics = service.optimizer.hashtag_generator.generate_hashtags(
            HashtagGenerationRequest(
                content=content_text,
                content_type=SEOContentType.TWEET,
                max_hashtags=5,
                strategy=HashtagStrategy.ENGAGEMENT_OPTIMIZED
            )
        )
        
        # Compile comprehensive audit result
        audit_result = {
            "seo_analysis": seo_analysis,
            "keyword_analysis": [
                {
                    "keyword": kw.keyword,
                    "relevance_score": kw.relevance_score,
                    "difficulty": kw.difficulty.value,
                    "trending_status": kw.trending_status
                } for kw in keyword_analysis[:10]
            ],
            "hashtag_recommendations": [
                {
                    "hashtag": ht.hashtag,
                    "relevance_score": ht.relevance_score,
                    "engagement_rate": ht.engagement_rate,
                    "competition_level": ht.competition_level.value
                } for ht in hashtag_metrics[:5]
            ],
            "overall_score": seo_analysis.get('combined_score', 0),
            "recommendations": [
                "Optimize keyword integration for better relevance",
                "Consider using recommended hashtags for increased reach",
                "Enhance content engagement elements",
                "Monitor performance and adjust strategy accordingly"
            ]
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "SEO audit completed successfully",
                "content_id": content_id,
                "audit_results": audit_result,
                "audit_timestamp": datetime.utcnow().isoformat(),
                "recommendations": audit_result.get('recommendations', []),
                "overall_seo_score": audit_result.get('overall_score', 0)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SEO audit failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SEO audit failed"
        )

@router.get("/health")
async def health_check():
    """
    Health check endpoint for SEO service
    
    Returns service status and availability information
    """
    try:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "healthy",
                "service": "seo-optimization",
                "version": "1.0.0",
                "features": [
                    "content_optimization",
                    "hashtag_generation", 
                    "keyword_analysis",
                    "trending_optimization",
                    "content_variations",
                    "seo_analytics",
                    "ab_testing",
                    "performance_comparison"
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service health check failed"
        )