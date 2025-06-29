#!/usr/bin/env python3
"""
插入测试用的founder用户到数据库
"""
import sqlite3
import os

# 数据库文件路径
db_path = "test.db"

# 测试用 UUID
founder_id = "11111111-1111-1111-1111-111111111111"
username = "test_founder"
email = "test_founder@example.com"

def insert_test_founder():
    """插入测试founder到数据库"""
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查是否已存在
        cursor.execute("SELECT id FROM founders WHERE id = ?", (founder_id,))
        if cursor.fetchone():
            print("✅ Founder 已存在，无需重复插入。")
            return True
        
        # 插入 founder
        cursor.execute(
            "INSERT INTO founders (id, username, email, created_at) VALUES (?, ?, ?, datetime('now'))",
            (founder_id, username, email)
        )
        conn.commit()
        print("✅ 成功插入测试founder:")
        print(f"   - ID: {founder_id}")
        print(f"   - Username: {username}")
        print(f"   - Email: {email}")
        
        # 验证插入
        cursor.execute("SELECT id, username, email FROM founders WHERE id = ?", (founder_id,))
        result = cursor.fetchone()
        if result:
            print("✅ 验证成功，founder已正确插入数据库")
            return True
        else:
            print("❌ 验证失败，founder未找到")
            return False
            
    except Exception as e:
        print(f"❌ 插入founder失败: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🔧 开始插入测试founder...")
    success = insert_test_founder()
    if success:
        print("🎉 测试founder准备完成！现在可以运行测试了。")
    else:
        print("💥 测试founder准备失败，请检查数据库连接。")