"""API模块初始化"""
from flask import Flask
from flask_cors import CORS
from .routes.analytics import analytics_bp

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    CORS(app)
    
    # 注册蓝图
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    
    return app 