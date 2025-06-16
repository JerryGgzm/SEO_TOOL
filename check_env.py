#!/usr/bin/env python3
"""
环境变量检查脚本
用于诊断Twitter OAuth和OpenAI API配置问题
"""

import os
from dotenv import load_dotenv

def check_environment():
    """检查关键环境变量配置"""
    print("🔍 环境变量配置检查")
    print("=" * 50)
    
    # 加载.env文件
    load_dotenv('.env')
    
    # 检查Twitter配置
    print("\n📱 Twitter API 配置:")
    twitter_vars = {
        'TWITTER_CLIENT_ID': os.getenv('TWITTER_CLIENT_ID'),
        'TWITTER_CLIENT_SECRET': os.getenv('TWITTER_CLIENT_SECRET'), 
        'TWITTER_REDIRECT_URI': os.getenv('TWITTER_REDIRECT_URI'),
    }
    
    for var_name, var_value in twitter_vars.items():
        if var_value:
            # 只显示前几个字符，保护敏感信息
            display_value = var_value[:10] + "..." if len(var_value) > 10 else var_value
            print(f"  ✅ {var_name}: {display_value}")
        else:
            print(f"  ❌ {var_name}: 未设置")
    
    # 检查OpenAI配置
    print("\n🤖 OpenAI API 配置:")
    openai_vars = [
        'OPENAI_API_KEY',
        'OPENAI_KEY', 
        'OPENAI_SECRET_KEY',
        'GPT_API_KEY'
    ]
    
    openai_found = False
    for var_name in openai_vars:
        var_value = os.getenv(var_name)
        if var_value:
            display_value = var_value[:10] + "..." if len(var_value) > 10 else var_value
            print(f"  ✅ {var_name}: {display_value}")
            openai_found = True
        else:
            print(f"  ❌ {var_name}: 未设置")
    
    # 检查其他重要配置
    print("\n🔐 其他配置:")
    other_vars = {
        'SECRET_KEY': os.getenv('SECRET_KEY'),
        'DATABASE_URL': os.getenv('DATABASE_URL'),
    }
    
    for var_name, var_value in other_vars.items():
        if var_value:
            display_value = var_value[:20] + "..." if len(var_value) > 20 else var_value
            print(f"  ✅ {var_name}: {display_value}")
        else:
            print(f"  ❌ {var_name}: 未设置")
    
    # 总结
    print("\n📊 配置状态总结:")
    twitter_complete = all(twitter_vars.values())
    print(f"  Twitter API: {'✅ 完整配置' if twitter_complete else '❌ 配置不完整'}")
    print(f"  OpenAI API: {'✅ 已配置' if openai_found else '❌ 未配置'}")
    
    if not twitter_complete:
        print("\n⚠️  Twitter API配置不完整，将使用模拟数据")
        print("   请确保在.env文件中设置:")
        print("   - TWITTER_CLIENT_ID")
        print("   - TWITTER_CLIENT_SECRET") 
        print("   - TWITTER_REDIRECT_URI (可选)")
    
    if not openai_found:
        print("\n⚠️  OpenAI API未配置，将使用传统关键词匹配")
        print("   请在.env文件中设置 OPENAI_API_KEY")
    
    print("\n" + "=" * 50)
    return twitter_complete, openai_found

if __name__ == "__main__":
    check_environment() 