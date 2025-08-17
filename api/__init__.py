"""API模块初始化"""
from flask import Flask
from flask_cors import CORS


def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    CORS(app)
    
    # ...existing code...
    
    return app 
