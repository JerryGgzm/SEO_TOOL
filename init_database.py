#!/usr/bin/env python3
"""
数据库初始化脚本

此脚本将创建所有必要的数据库表，包括：
- user_profiles 表（用于用户注册和认证）
- founders 表（主要用户表）
- products 表（产品信息）
- twitter_credentials 表（Twitter OAuth）
- 其他应用表
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, inspect
from database import init_database, get_db_manager
from database.models import Base
from modules.user_profile.repository import UserProfileTable

def reset_database(database_url: str = None):
    """重置数据库（删除现有数据库文件）"""
    if database_url is None:
        database_url = os.getenv('DATABASE_URL', 'sqlite:///./seo_tool.db')
    
    print("🗑️  重置数据库...")
    
    # 只对SQLite数据库删除文件
    if database_url.startswith('sqlite:///'):
        db_file = database_url.replace('sqlite:///', '')
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"✅ 删除现有数据库文件: {db_file}")
        else:
            print(f"ℹ️  数据库文件不存在: {db_file}")

def create_all_tables(reset: bool = False):
    """创建所有数据库表"""
    print("🚀 开始初始化数据库...")
    
    # 获取数据库URL
    database_url = os.getenv('DATABASE_URL', 'sqlite:///./seo_tool.db')
    print(f"📍 数据库URL: {database_url}")
    
    # 如果需要重置，先删除现有数据库
    if reset:
        reset_database(database_url)
    
    # 初始化数据库连接
    init_database(database_url, create_tables=False)
    
    # 获取数据库管理器
    db_manager = get_db_manager()
    
    # 创建引擎
    engine = create_engine(database_url, echo=True)
    
    try:
        print("📋 创建表结构...")
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        # 验证表是否创建成功
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print("✅ 成功创建的表:")
        for table in sorted(tables):
            print(f"  - {table}")
            
        # 检查关键表
        required_tables = [
            'user_profiles',
            'founders', 
            'products',
            'twitter_credentials',
            'analyzed_trends',
            'generated_content_drafts'
        ]
        
        missing_tables = []
        for table in required_tables:
            if table in tables:
                print(f"✅ {table} - 已创建")
            else:
                missing_tables.append(table)
                print(f"❌ {table} - 缺失")
        
        if missing_tables:
            print(f"\n⚠️  警告：以下表未创建: {missing_tables}")
            return False
        else:
            print("\n🎉 所有必要的表都已成功创建！")
            return True
            
    except Exception as e:
        print(f"❌ 创建表时发生错误: {e}")
        return False

def verify_database():
    """验证数据库连接和表结构"""
    try:
        from database import health_check
        if health_check():
            print("✅ 数据库连接正常")
            return True
        else:
            print("❌ 数据库连接失败")
            return False
    except Exception as e:
        print(f"❌ 数据库验证失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🔧 SEO工具数据库管理")
    print("=" * 50)
    
    # 设置环境变量（如果没有设置）
    if not os.getenv('SECRET_KEY'):
        os.environ['SECRET_KEY'] = 'your-secret-key-here'
        print("🔑 设置默认SECRET_KEY")
        
    if not os.getenv('ENCRYPTION_KEY'):
        os.environ['ENCRYPTION_KEY'] = 'your-encryption-key-change-in-production'
        print("🔐 设置默认ENCRYPTION_KEY")
    
    # 检查命令行参数
    reset_mode = '--reset' in sys.argv or '-r' in sys.argv
    
    if reset_mode:
        print("⚠️  重置模式：将删除现有数据库并重新创建")
        confirm = input("继续? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ 操作已取消")
            sys.exit(0)
    
    try:
        # 创建表
        success = create_all_tables(reset=reset_mode)
        
        if success:
            # 验证数据库
            verify_success = verify_database()
            
            if verify_success:
                if reset_mode:
                    print("\n🎊 数据库重置完成！")
                else:
                    print("\n🎊 数据库初始化完成！")
                    
                print("\n📝 下一步：")
                print("1. 运行应用: python -m uvicorn main:app --reload")
                print("2. 或运行演示: python demo_complete_workflow.py")
                print("\n💡 提示：")
                print("- 普通初始化：python init_database.py")
                print("- 重置数据库：python init_database.py --reset")
                
                # 显示创建的数据库文件位置
                db_url = os.getenv('DATABASE_URL', 'sqlite:///./seo_tool.db')
                if db_url.startswith('sqlite'):
                    db_file = db_url.replace('sqlite:///', '')
                    db_path = Path(db_file).absolute()
                    print(f"\n📁 数据库文件位置: {db_path}")
                    
            else:
                print("\n❌ 数据库验证失败")
                sys.exit(1)
        else:
            print("\n❌ 数据库初始化失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断了操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 初始化过程中发生错误: {e}")
        sys.exit(1) 