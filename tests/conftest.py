"""pytest配置文件"""
import sys
import os
import pytest
from unittest.mock import Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 现在可以安全导入项目模块
from config.database import Base


@pytest.fixture
def test_db():
    """测试数据库fixture"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def mock_db_session():
    """模拟数据库会话fixture"""
    return Mock()


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """设置测试环境"""
    # 设置测试环境变量
    os.environ.setdefault('TWITTER_CLIENT_ID', 'test_client_id')
    os.environ.setdefault('TWITTER_CLIENT_SECRET', 'test_client_secret')
    os.environ.setdefault('ENCRYPTION_KEY', 'test_encryption_key_32_chars_long')
    os.environ.setdefault('SECRET_KEY', 'test_secret_key')
    os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:') 