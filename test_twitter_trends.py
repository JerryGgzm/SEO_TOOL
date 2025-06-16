#!/usr/bin/env python3
"""
Twitter Trends API 测试脚本
用于诊断Twitter趋势API的权限和调用问题
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('.env')

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

def test_twitter_trends_api():
    """测试Twitter Trends API权限"""
    print("🔍 Twitter Trends API 权限测试")
    print("=" * 50)
    
    # 检查环境变量
    client_id = os.getenv('TWITTER_CLIENT_ID')
    client_secret = os.getenv('TWITTER_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Twitter API凭证未配置")
        return False
    
    print(f"✅ Twitter Client ID: {client_id[:10]}...")
    print(f"✅ Twitter Client Secret: {client_secret[:10]}...")
    
    # 检查用户是否已经通过OAuth授权
    try:
        # 使用demo脚本中的API客户端
        from demo_complete_workflow import APIClient
        
        print("\n🔑 检查用户授权状态...")
        api_client = APIClient()
        
        # 尝试登录
        login_response = api_client.request("POST", "/api/user/login", {
            "email": "demo@example.com",
            "password": "DemoPassword123!"
        })
        
        if "error" in login_response:
            print(f"❌ 登录失败: {login_response['error']}")
            return False
        
        if "token" not in login_response:
            print("❌ 登录响应中没有访问令牌")
            return False
        
        api_client.set_auth_token(login_response["token"])
        print("✅ 用户已登录")
        
        # 检查Twitter连接状态
        print("\n📱 检查Twitter连接状态...")
        status_response = api_client.request("GET", "/api/user/profile/twitter/status")
        
        if "error" in status_response:
            print(f"❌ 无法获取Twitter状态: {status_response['error']}")
            return False
        
        print(f"Twitter连接状态: {status_response}")
        
        if not status_response.get("connected"):
            print("❌ Twitter账户未连接")
            return False
        
        print("✅ Twitter账户已连接")
        
        # 直接测试趋势API
        print("\n🔥 测试Twitter趋势API...")
        
        # 方法1：使用我们的API端点
        print("方法1：通过我们的API端点...")
        trends_response = api_client.request("GET", "/api/trends/live?location_id=1&limit=5")
        
        print(f"趋势API响应: {json.dumps(trends_response, indent=2, ensure_ascii=False)}")
        
        if "error" not in trends_response:
            trends = trends_response.get("trends", [])
            print(f"✅ 成功获取 {len(trends)} 个趋势")
            
            if trends:
                print("\n📊 趋势详情:")
                for i, trend in enumerate(trends[:3], 1):
                    print(f"  {i}. {trend.get('name', 'N/A')} - 热度: {trend.get('tweet_volume', 'N/A')}")
                return True
            else:
                print("⚠️  没有获取到趋势数据")
        else:
            print(f"❌ 趋势API调用失败: {trends_response['error']}")
            
        # 方法2：检查权限问题
        print("\n🔍 检查Twitter API权限...")
        
        # 检查是否有读取趋势的权限
        print("检查Twitter应用权限范围...")
        
        # 获取用户信息以验证token
        user_response = api_client.request("GET", "/api/user/profile")
        
        if "error" not in user_response:
            print("✅ 用户token有效")
        else:
            print(f"❌ 用户token无效: {user_response['error']}")
            
        return False
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

def test_twitter_api_scopes():
    """测试Twitter API权限范围"""
    print("\n🔐 Twitter API权限范围检查")
    print("=" * 30)
    
    # 说明所需权限
    required_scopes = [
        "tweet.read",
        "users.read", 
        "follows.read",
        "follows.write",
        "offline.access"
    ]
    
    print("📋 应用所需权限范围:")
    for scope in required_scopes:
        print(f"  • {scope}")
    
    print("\n⚠️  注意事项:")
    print("1. Twitter API v2 不直接支持trends/place端点")
    print("2. 需要使用Twitter API v1.1的trends/place.json端点")
    print("3. 确保你的Twitter应用有以下权限:")
    print("   - Read permissions")
    print("   - 如果要发布推文，需要Write permissions")
    print("4. 检查你的Twitter开发者账户是否已经升级到v2")
    
    return True

def test_openai_api():
    """测试OpenAI API"""
    print("\n🤖 OpenAI API 测试")
    print("=" * 30)
    
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if not openai_key:
        print("❌ OpenAI API密钥未配置")
        return False
    
    print(f"✅ OpenAI API Key: {openai_key[:10]}...")
    
    try:
        import openai
        
        # 测试API调用
        print("🔍 测试OpenAI API连接...")
        client = openai.OpenAI(api_key=openai_key)
        
        # 简单的测试调用
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            max_tokens=10
        )
        
        if response.choices:
            print("✅ OpenAI API连接成功")
            print(f"测试响应: {response.choices[0].message.content}")
            return True
        else:
            print("❌ OpenAI API响应为空")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI API连接失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 Twitter 和 OpenAI API 诊断脚本")
    print("=" * 60)
    
    # 测试Twitter Trends API
    twitter_success = test_twitter_trends_api()
    
    # 测试Twitter权限范围
    test_twitter_api_scopes()
    
    # 测试OpenAI API
    openai_success = test_openai_api()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 诊断结果总结:")
    print(f"  Twitter API: {'✅ 可用' if twitter_success else '❌ 不可用'}")
    print(f"  OpenAI API: {'✅ 可用' if openai_success else '❌ 不可用'}")
    
    if not twitter_success:
        print("\n⚠️  Twitter API问题解决建议:")
        print("1. 检查Twitter应用是否有正确的权限")
        print("2. 确认Twitter API v2访问权限")
        print("3. 检查OAuth令牌是否有效")
        print("4. 考虑升级Twitter开发者账户")
    
    if not openai_success:
        print("\n⚠️  OpenAI API问题解决建议:")
        print("1. 检查API密钥是否正确")
        print("2. 确认OpenAI账户余额")
        print("3. 检查API使用限制")

if __name__ == "__main__":
    main() 