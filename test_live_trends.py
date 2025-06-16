#!/usr/bin/env python3
"""
测试实时趋势API功能
"""

import requests
import json
from typing import List, Dict, Any

class TrendTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        
    def login(self, email: str, password: str) -> bool:
        """登录获取认证令牌"""
        try:
            response = self.session.post(f"{self.base_url}/api/user/login", json={
                "email": email,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                if self.auth_token:
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.auth_token}'
                    })
                    return True
            return False
        except Exception as e:
            print(f"登录失败: {e}")
            return False
    
    def test_live_trends(self, keywords: List[str]) -> Dict[str, Any]:
        """测试实时趋势API"""
        if not self.auth_token:
            return {"error": "未登录"}
            
        try:
            # 构建查询参数
            params = {
                "keywords": keywords,
                "location_id": "1",
                "limit": 10
            }
            
            response = self.session.get(f"{self.base_url}/api/trends/live", params=params)
            
            print(f"请求URL: {response.url}")
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API错误: {response.status_code}", "detail": response.text}
                
        except Exception as e:
            return {"error": str(e)}
    
    def test_fallback_trends(self, keywords: List[str]) -> Dict[str, Any]:
        """测试数据库趋势API"""
        if not self.auth_token:
            return {"error": "未登录"}
            
        try:
            # 构建查询参数
            params = {
                "keywords": keywords,
                "limit": 10,
                "max_age_hours": 24
            }
            
            response = self.session.get(f"{self.base_url}/api/trends/cached", params=params)
            print(f"数据库趋势响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API错误: {response.status_code}", "detail": response.text}
                
        except Exception as e:
            return {"error": str(e)}

def main():
    tester = TrendTester()
    
    # 测试登录
    print("🔐 测试登录...")
    login_success = tester.login("demo@example.com", "DemoPassword123!")
    
    if not login_success:
        print("❌ 登录失败，请确保用户已注册")
        return
    
    print("✅ 登录成功")
    
    # 测试实时趋势API
    print("\n🔥 测试实时趋势API...")
    keywords = ["AI", "Technology", "Innovation", "Smart"]
    
    result = tester.test_live_trends(keywords)
    
    if "error" in result:
        print("result: ", result)
        print(f"❌ 实时趋势API失败: {result['error']}")
        
        # 测试数据库趋势作为后备
        print("\n📚 测试数据库趋势API...")
        fallback_result = tester.test_fallback_trends(keywords)
        
        if "error" in fallback_result:
            print(f"❌ 数据库趋势也失败: {fallback_result['error']}")
        else:
            print("✅ 数据库趋势成功")
            topics = fallback_result.get("topics", [])
            print(f"获取到 {len(topics)} 个数据库趋势")
            
            for i, topic in enumerate(topics[:3], 1):
                print(f"  {i}. {topic.get('topic_name', 'N/A')} (来源: {topic.get('source', 'database')})")
    else:
        print("✅ 实时趋势API成功")
        trends = result.get("trends", [])
        print(f"关键词: {result.get('keywords', [])}")
        print(f"总Twitter趋势: {result.get('total_twitter_trends', 'N/A')}")
        print(f"过滤后趋势: {len(trends)}")
        
        if trends:
            print("\n📈 匹配的趋势:")
            for i, trend in enumerate(trends, 1):
                matching = trend.get('matching_keywords', [])
                print(f"  {i}. {trend.get('name', 'N/A')} (热度: {trend.get('tweet_volume', 'N/A')}) [匹配: {', '.join(matching)}]")
        else:
            print("没有找到匹配的趋势")

if __name__ == "__main__":
    main() 