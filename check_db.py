#!/usr/bin/env python3
import sqlite3

# 连接数据库
conn = sqlite3.connect('test.db')
cursor = conn.cursor()

# 检查founders表结构
print("=== Founders表结构 ===")
cursor.execute('PRAGMA table_info(founders)')
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# 检查是否有测试用户
print("\n=== 检查测试用户 ===")
test_id = '11111111-1111-1111-1111-111111111111'

# 尝试不同的字段名
try:
    cursor.execute('SELECT * FROM founders WHERE id = ?', (test_id,))
    result = cursor.fetchone()
    if result:
        print(f"✅ 找到用户 (id字段): {result}")
    else:
        print(f"❌ 未找到用户 (id字段): {test_id}")
except Exception as e:
    print(f"❌ 查询id字段失败: {e}")

try:
    cursor.execute('SELECT * FROM founders WHERE user_id = ?', (test_id,))
    result = cursor.fetchone()
    if result:
        print(f"✅ 找到用户 (user_id字段): {result}")
    else:
        print(f"❌ 未找到用户 (user_id字段): {test_id}")
except Exception as e:
    print(f"❌ 查询user_id字段失败: {e}")

# 显示所有founders
print("\n=== 所有Founders ===")
try:
    cursor.execute('SELECT * FROM founders LIMIT 5')
    results = cursor.fetchall()
    for i, result in enumerate(results):
        print(f"  {i+1}: {result}")
except Exception as e:
    print(f"❌ 查询所有founders失败: {e}")

conn.close() 