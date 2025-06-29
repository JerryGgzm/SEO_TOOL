#!/usr/bin/env python3
"""
测试合并后的内容生成API
"""
import asyncio
import aiohttp
import json
import jwt
import os
from typing import Dict, Any
from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API基础URL
BASE_URL = "http://localhost:8000"

# JWT配置（与middleware.py保持一致）
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"

class ContentGenerationAPITester:
    TEST_FOUNDER_ID = "11111111-1111-1111-1111-111111111111"
    def __init__(self):
        self.session = None
        self.auth_token = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        # 创建测试用户token
        self.auth_token = self.create_test_token(self.TEST_FOUNDER_ID)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def create_test_token(self, user_id: str) -> str:
        """创建测试用户的JWT token - 设置为管理员用户"""
        payload = {
            "sub": user_id,
            "user_id": user_id,
            "username": "demo_user",  # 关键：让middleware识别为管理员
            "email": f"{user_id}@admin.com",  # 关键：让middleware识别为管理员
            "is_active": True,
            "is_admin": True,
            "exp": datetime.now(UTC) + timedelta(hours=1)
        }
        print(f"🔑 创建测试token，使用SECRET_KEY: {SECRET_KEY[:10]}...")
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    def get_auth_headers(self) -> Dict[str, str]:
        """获取认证头"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_token}"
        }
    
    async def test_health_check(self) -> bool:
        """测试健康检查"""
        print("🔍 测试健康检查...")
        try:
            async with self.session.get(f"{BASE_URL}/api/content/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 健康检查通过: {data}")
                    return True
                else:
                    print(f"❌ 健康检查失败: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return False
    
    async def test_standard_content_generation(self) -> bool:
        """测试标准内容生成"""
        print("\n🔍 测试标准内容生成...")
        
        payload = {
            "founder_id": self.TEST_FOUNDER_ID,
            "content_type": "tweet",
            "generation_mode": "standard",
            "quantity": 2,
            "quality_threshold": 0.5
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/api/content/generate",
                json=payload,
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    print(f"✅ 标准内容生成成功:")
                    print(f"   - 生成模式: {data.get('generation_mode')}")
                    print(f"   - 草稿数量: {data.get('count')}")
                    print(f"   - 草稿IDs: {data.get('draft_ids')}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 标准内容生成失败: {response.status}")
                    print(f"   错误信息: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ 标准内容生成异常: {e}")
            return False
    
    async def test_viral_focused_generation(self) -> bool:
        """测试病毒式内容生成"""
        print("\n🔍 测试病毒式内容生成...")
        
        payload = {
            "founder_id": self.TEST_FOUNDER_ID,
            "content_type": "tweet",
            "generation_mode": "viral_focused",
            "quantity": 3,
            "quality_threshold": 0.6
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/api/content/generate",
                json=payload,
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    print(f"✅ 病毒式内容生成成功:")
                    print(f"   - 生成模式: {data.get('generation_mode')}")
                    print(f"   - 草稿数量: {data.get('count')}")
                    print(f"   - 草稿IDs: {data.get('draft_ids')}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 病毒式内容生成失败: {response.status}")
                    print(f"   错误信息: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ 病毒式内容生成异常: {e}")
            return False
    
    async def test_brand_focused_generation(self) -> bool:
        """测试品牌导向内容生成"""
        print("\n🔍 测试品牌导向内容生成...")
        
        payload = {
            "founder_id": self.TEST_FOUNDER_ID,
            "content_type": "tweet",
            "generation_mode": "brand_focused",
            "custom_brand_voice": {
                "tone": "professional",
                "style": "authoritative",
                "personality_traits": ["expert", "reliable"],
                "formality_level": 0.8
            },
            "quantity": 2,
            "quality_threshold": 0.7
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/api/content/generate",
                json=payload,
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    print(f"✅ 品牌导向内容生成成功:")
                    print(f"   - 生成模式: {data.get('generation_mode')}")
                    print(f"   - 草稿数量: {data.get('count')}")
                    print(f"   - 草稿IDs: {data.get('draft_ids')}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 品牌导向内容生成失败: {response.status}")
                    print(f"   错误信息: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ 品牌导向内容生成异常: {e}")
            return False
    
    async def test_engagement_optimized_generation(self) -> bool:
        """测试互动优化内容生成"""
        print("\n🔍 测试互动优化内容生成...")
        
        payload = {
            "founder_id": self.TEST_FOUNDER_ID,
            "content_type": "tweet",
            "generation_mode": "engagement_optimized",
            "quantity": 2,
            "quality_threshold": 0.6
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/api/content/generate",
                json=payload,
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    print(f"✅ 互动优化内容生成成功:")
                    print(f"   - 生成模式: {data.get('generation_mode')}")
                    print(f"   - 草稿数量: {data.get('count')}")
                    print(f"   - 草稿IDs: {data.get('draft_ids')}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 互动优化内容生成失败: {response.status}")
                    print(f"   错误信息: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ 互动优化内容生成异常: {e}")
            return False
    
    async def test_different_content_types(self) -> bool:
        """测试不同内容类型"""
        print("\n🔍 测试不同内容类型...")
        
        content_types = ["tweet", "reply", "thread"]
        results = []
        
        for content_type in content_types:
            print(f"   测试 {content_type} 类型...")
            payload = {
                "founder_id": self.TEST_FOUNDER_ID,
                "content_type": content_type,
                "generation_mode": "standard",
                "quantity": 1,
                "quality_threshold": 0.5
            }
            
            try:
                async with self.session.post(
                    f"{BASE_URL}/api/content/generate",
                    json=payload,
                    headers=self.get_auth_headers()
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        print(f"   ✅ {content_type} 生成成功")
                        results.append(True)
                    else:
                        print(f"   ❌ {content_type} 生成失败: {response.status}")
                        results.append(False)
            except Exception as e:
                print(f"   ❌ {content_type} 生成异常: {e}")
                results.append(False)
        
        success_count = sum(results)
        print(f"   内容类型测试结果: {success_count}/{len(content_types)} 成功")
        return success_count == len(content_types)
    
    async def test_draft_management(self) -> bool:
        """测试草稿管理功能"""
        print("\n🔍 测试草稿管理功能...")
        
        # 首先生成一些草稿用于测试
        print("   生成测试草稿...")
        generate_payload = {
            "founder_id": self.TEST_FOUNDER_ID,
            "content_type": "tweet",
            "generation_mode": "standard",
            "quantity": 2,
            "quality_threshold": 0.5
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/api/content/generate",
                json=generate_payload,
                headers=self.get_auth_headers()
            ) as response:
                if response.status != 201:
                    print(f"   ❌ 生成草稿失败: {response.status}")
                    return False
                
                data = await response.json()
                draft_ids = data.get('draft_ids', [])
                if not draft_ids:
                    print("   ❌ 没有生成草稿")
                    return False
                
                test_draft_id = draft_ids[0]
                print(f"   ✅ 生成测试草稿: {test_draft_id}")
        
        except Exception as e:
            print(f"   ❌ 生成草稿异常: {e}")
            return False
        
        # 测试获取草稿详情
        print("   测试获取草稿详情...")
        try:
            async with self.session.get(
                f"{BASE_URL}/api/content/drafts/{test_draft_id}",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ 获取草稿详情成功: {data.get('draft_id')}")
                else:
                    print(f"   ❌ 获取草稿详情失败: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ 获取草稿详情异常: {e}")
            return False
        
        # 测试更新草稿质量评分
        print("   测试更新草稿质量评分...")
        try:
            update_payload = {
                "update_type": "quality_score",
                "quality_score": 0.85
            }
            
            async with self.session.put(
                f"{BASE_URL}/api/content/drafts/{test_draft_id}",
                json=update_payload,
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ 更新草稿成功: {data.get('message')}")
                else:
                    print(f"   ❌ 更新草稿失败: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ 更新草稿异常: {e}")
            return False
        
        # 测试获取创始人草稿列表
        print("   测试获取创始人草稿列表...")
        try:
            async with self.session.get(
                f"{BASE_URL}/api/content/drafts/founder/{self.TEST_FOUNDER_ID}?limit=10",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    draft_count = data.get('count', 0)
                    print(f"   ✅ 获取草稿列表成功: {draft_count} 个草稿")
                else:
                    print(f"   ❌ 获取草稿列表失败: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ 获取草稿列表异常: {e}")
            return False
        
        # 测试复制草稿
        print("   测试复制草稿...")
        try:
            async with self.session.post(
                f"{BASE_URL}/api/content/drafts/{test_draft_id}/duplicate",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ 复制草稿成功: {data.get('new_draft_id')}")
                else:
                    print(f"   ❌ 复制草稿失败: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ 复制草稿异常: {e}")
            return False
        
        # 测试兼容性API - 质量评分更新
        print("   测试兼容性质量评分更新API...")
        try:
            async with self.session.put(
                f"{BASE_URL}/api/content/drafts/{test_draft_id}/quality-score?quality_score=0.95",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ 兼容性API更新成功: {data.get('message')}")
                else:
                    print(f"   ❌ 兼容性API更新失败: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ 兼容性API更新异常: {e}")
            return False
        
        print("   ✅ 草稿管理功能测试完成")
        return True
    
    async def test_draft_filtering(self) -> bool:
        """测试草稿过滤功能"""
        print("\n🔍 测试草稿过滤功能...")
        
        # 测试按内容类型过滤
        print("   测试按内容类型过滤...")
        try:
            async with self.session.get(
                f"{BASE_URL}/api/content/drafts/founder/{self.TEST_FOUNDER_ID}?content_type=tweet&limit=5",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    filters = data.get('filters', {})
                    print(f"   ✅ 内容类型过滤成功: {filters.get('content_type')}")
                else:
                    print(f"   ❌ 内容类型过滤失败: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ 内容类型过滤异常: {e}")
            return False
        
        # 测试按质量阈值过滤
        print("   测试按质量阈值过滤...")
        try:
            async with self.session.get(
                f"{BASE_URL}/api/content/drafts/founder/{self.TEST_FOUNDER_ID}?quality_threshold=0.7&limit=5",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    filters = data.get('filters', {})
                    print(f"   ✅ 质量阈值过滤成功: {filters.get('quality_threshold')}")
                else:
                    print(f"   ❌ 质量阈值过滤失败: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ 质量阈值过滤异常: {e}")
            return False
        
        print("   ✅ 草稿过滤功能测试完成")
        return True
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始测试合并后的内容生成API")
        print("=" * 50)
        
        tests = [
            ("健康检查", self.test_health_check),
            ("标准内容生成", self.test_standard_content_generation),
            ("病毒式内容生成", self.test_viral_focused_generation),
            ("品牌导向内容生成", self.test_brand_focused_generation),
            ("互动优化内容生成", self.test_engagement_optimized_generation),
            ("不同内容类型", self.test_different_content_types),
            ("草稿管理", self.test_draft_management),
            ("草稿过滤", self.test_draft_filtering),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} 测试异常: {e}")
                results.append((test_name, False))
        
        # 输出测试总结
        print("\n" + "=" * 50)
        print("📊 测试总结:")
        success_count = 0
        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   {test_name}: {status}")
            if result:
                success_count += 1
        
        print(f"\n🎯 总体结果: {success_count}/{len(results)} 测试通过")
        
        if success_count == len(results):
            print("🎉 所有测试通过！API合并成功！")
        else:
            print("⚠️ 部分测试失败，需要检查API实现")

async def main():
    """主函数"""
    async with ContentGenerationAPITester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 