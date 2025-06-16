"""Main FastAPI Application"""
import logging

import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import user_profile, twitter_api, trend_analysis, seo, content_generation, scheduling_posting, review_optimization
from dotenv import load_dotenv
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # 确保输出到控制台
    ]
)

# 设置各模块的日志级别
logging.getLogger('api.routes.user_profile').setLevel(logging.INFO)
logging.getLogger('modules.user_profile').setLevel(logging.INFO)
logging.getLogger('uvicorn.access').setLevel(logging.INFO)
logging.getLogger('uvicorn').setLevel(logging.INFO)

logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 打印环境变量（仅用于调试）
logger.info("环境变量检查:")
logger.info(f"TWITTER_CLIENT_ID: {'已设置' if os.getenv('TWITTER_CLIENT_ID') else '未设置'}")
logger.info(f"TWITTER_CLIENT_SECRET: {'已设置' if os.getenv('TWITTER_CLIENT_SECRET') else '未设置'}")
logger.info(f"TWITTER_REDIRECT_URI: {os.getenv('TWITTER_REDIRECT_URI', '未设置')}")
logger.info(f"SECRET_KEY: {'已设置' if os.getenv('SECRET_KEY') else '未设置'}")

# 初始化数据库
from database import init_database, health_check
try:
    logger.info("🔨 正在初始化数据库...")
    database_url = os.getenv('DATABASE_URL', 'sqlite:///./seo_tool.db')
    init_database(database_url, create_tables=True)
    
    # 检查数据库健康状态
    if health_check():
        logger.info("✅ 数据库初始化成功")
    else:
        logger.warning("⚠️ 数据库健康检查失败")
        
except Exception as e:
    logger.error(f"❌ 数据库初始化失败: {e}")
    # 不要停止应用，但记录错误
    import traceback
    traceback.print_exc()

app = FastAPI(title="SEO Tool API")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(user_profile.router)
app.include_router(twitter_api.router)
app.include_router(trend_analysis.router)
app.include_router(seo.router)
app.include_router(content_generation.router)
app.include_router(scheduling_posting.router)
app.include_router(review_optimization.router)

@app.get("/health")
async def health_check():
    """健康检查端点"""
    # 检查数据库状态
    from database import health_check as db_health_check
    db_status = db_health_check()
    
    return {
        "status": "healthy" if db_status else "degraded",
        "version": "1.0.0",
        "timestamp": "2024-01-15T10:00:00Z",
        "database": "connected" if db_status else "disconnected"
    }