#!/usr/bin/env python3
"""
Database Tables Viewer

This script connects to the database and shows all tables in the database.
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_url():
    """Get database URL from environment variables"""
    database_url = os.getenv('DATABASE_URL', 'sqlite:///./seo_tool.db')
    
    # If DATABASE_URL is not set, construct it from individual components
    if database_url == 'sqlite:///./seo_tool.db' and not os.path.exists('./seo_tool.db'):
        # Try to construct from PostgreSQL components
        host = os.getenv('DATABASE_HOST', 'localhost')
        port = os.getenv('DATABASE_PORT', '5432')
        name = os.getenv('DATABASE_NAME', 'ideation_db')
        user = os.getenv('DATABASE_USER', 'postgres')
        password = os.getenv('DATABASE_PASSWORD', 'Tianjin@0430')
        
        if all([host, name, user, password]):
            database_url = f"postgresql://{user}:{password}@{host}:{port}/{name}"
    
    return database_url

def show_tables():
    """Show all tables in the database"""
    try:
        # Get database URL
        database_url = get_database_url()
        print(f"🔗 连接到数据库: {database_url.split('@')[1] if '@' in database_url else database_url}")
        
        # Create engine
        engine = create_engine(database_url, echo=False)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ 数据库连接成功")
        
        # Get inspector
        inspector = inspect(engine)
        
        # Get all table names
        tables = inspector.get_table_names()
        
        if not tables:
            print("❌ 数据库中没有找到任何表")
            return
        
        print(f"\n📊 数据库中共有 {len(tables)} 个表:\n")
        
        # Show tables with details
        for i, table_name in enumerate(sorted(tables), 1):
            print(f"{i:2d}. {table_name}")
            
            # Get column information
            columns = inspector.get_columns(table_name)
            print(f"    列数: {len(columns)}")
            
            # Show primary keys
            pk_constraint = inspector.get_pk_constraint(table_name)
            if pk_constraint['constrained_columns']:
                print(f"    主键: {', '.join(pk_constraint['constrained_columns'])}")
            
            # Show foreign keys
            fk_constraints = inspector.get_foreign_keys(table_name)
            if fk_constraints:
                fk_info = []
                for fk in fk_constraints:
                    fk_info.append(f"{', '.join(fk['constrained_columns'])} -> {fk['referred_table']}.{', '.join(fk['referred_columns'])}")
                print(f"    外键: {'; '.join(fk_info)}")
            
            # Show indexes
            indexes = inspector.get_indexes(table_name)
            if indexes:
                index_names = [idx['name'] for idx in indexes if not idx.get('unique', False)]
                if index_names:
                    print(f"    索引: {', '.join(index_names)}")
            
            print()
        
        # Show table relationships
        print("🔗 表关系图:")
        for table_name in sorted(tables):
            fk_constraints = inspector.get_foreign_keys(table_name)
            if fk_constraints:
                for fk in fk_constraints:
                    print(f"    {table_name} -> {fk['referred_table']}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        print("\n请检查:")
        print("1. 数据库连接配置是否正确")
        print("2. 数据库服务是否正在运行")
        print("3. 环境变量是否正确设置")
        
        # Show current environment variables
        print(f"\n当前环境变量:")
        print(f"DATABASE_URL: {os.getenv('DATABASE_URL', '未设置')}")
        print(f"DATABASE_HOST: {os.getenv('DATABASE_HOST', '未设置')}")
        print(f"DATABASE_NAME: {os.getenv('DATABASE_NAME', '未设置')}")
        print(f"DATABASE_USER: {os.getenv('DATABASE_USER', '未设置')}")

if __name__ == "__main__":
    show_tables() 