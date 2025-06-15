"""Main FastAPI Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import auth, user_profile, twitter_api, trend_analysis, seo, content_generation, scheduling_posting, review_optimization
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 打印环境变量（仅用于调试）
print("环境变量检查:")
print(f"TWITTER_CLIENT_ID: {'已设置' if os.getenv('TWITTER_CLIENT_ID') else '未设置'}")
print(f"TWITTER_CLIENT_SECRET: {'已设置' if os.getenv('TWITTER_CLIENT_SECRET') else '未设置'}")
print(f"TWITTER_REDIRECT_URI: {os.getenv('TWITTER_REDIRECT_URI', '未设置')}")
print(f"SECRET_KEY: {'已设置' if os.getenv('SECRET_KEY') else '未设置'}")

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
app.include_router(auth.router)
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
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": "2024-01-15T10:00:00Z"
    }