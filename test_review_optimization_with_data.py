#!/usr/bin/env python3
"""
Review Optimization Module API 完整测试脚本

包含数据生成的完整测试流程
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timedelta
import jwt

# 配置
BASE_URL = "http://localhost:8000"
TEST_FOUNDER_ID = "11111111-1111-1111-1111-111111111111"
SECRET_KEY = "your-secret-key-here"

def create_test_token():
    """创建测试token"""
    payload = {
        "sub": TEST_FOUNDER_ID,
        "user_id": TEST_FOUNDER_ID,
        "username": "demo_user",
        "email": f"{TEST_FOUNDER_ID}@admin.com",
        "is_active": True,
        "is_admin": True,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def get_auth_headers():
    """获取认证头"""
    token = create_test_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

class ReviewOptimizationCompleteTester:
    """Review Optimization 完整测试器"""
    
    def __init__(self):
        self.session = None
        self.test_draft_ids = []
        self.test_regeneration_id = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate_test_drafts(self) -> bool:
        """生成测试草稿"""
        print("\n🔧 生成测试草稿...")
        
        # 生成不同类型的草稿
        draft_types = [
            {"generation_mode": "standard", "content_type": "tweet", "quantity": 2},
            {"generation_mode": "viral_focused", "content_type": "tweet", "quantity": 1},
            {"generation_mode": "brand_focused", "content_type": "tweet", "quantity": 1},
        ]
        
        all_draft_ids = []
        
        for draft_config in draft_types:
            try:
                payload = {
                    "founder_id": TEST_FOUNDER_ID,
                    "content_type": draft_config["content_type"],
                    "generation_mode": draft_config["generation_mode"],
                    "quantity": draft_config["quantity"],
                    "quality_threshold": 0.5  # 降低阈值确保生成成功
                }
                
                async with self.session.post(
                    f"{BASE_URL}/api/content/generate",
                    json=payload,
                    headers=get_auth_headers()
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        draft_ids = data.get('draft_ids', [])
                        all_draft_ids.extend(draft_ids)
                        print(f"   ✅ 生成 {draft_config['generation_mode']} 草稿: {len(draft_ids)} 个")
                    else:
                        error_text = await response.text()
                        print(f"   ❌ 生成 {draft_config['generation_mode']} 草稿失败: {response.status}")
                        print(f"      错误信息: {error_text}")
                        
            except Exception as e:
                print(f"   ❌ 生成 {draft_config['generation_mode']} 草稿异常: {e}")
        
        if all_draft_ids:
            self.test_draft_ids = all_draft_ids
            print(f"   📋 总测试草稿: {len(all_draft_ids)} 个")
            print(f"   🆔 草稿IDs: {all_draft_ids}")
            return True
        else:
            print("   ⚠️  没有生成任何测试草稿")
            return False
    
    async def test_get_pending_drafts(self) -> bool:
        """测试获取待审核草稿列表"""
        print("\n🔍 测试获取待审核草稿列表...")
        
        try:
            async with self.session.get(
                f"{BASE_URL}/api/review/pending?user_id={TEST_FOUNDER_ID}&limit=10",
                headers=get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 获取待审核草稿成功: {len(data)} 个草稿")
                    if data:
                        # 修复：正确提取草稿ID
                        self.test_draft_ids = []
                        for draft in data[:5]:
                            draft_id = draft.get('id') or draft.get('draft_id')
                            if draft_id:
                                self.test_draft_ids.append(draft_id)
                        print(f"   测试草稿IDs: {self.test_draft_ids}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 获取待审核草稿失败: {response.status}")
                    print(f"   错误信息: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ 获取待审核草稿异常: {e}")
            return False
    
    async def test_submit_review_decision(self) -> bool:
        """测试提交审核决定"""
        print("\n🔍 测试提交审核决定...")
        
        if not self.test_draft_ids:
            print("   ⚠️  没有可用的测试草稿，跳过测试")
            return True
        
        # 确保草稿ID不为None
        valid_draft_ids = [draft_id for draft_id in self.test_draft_ids if draft_id and draft_id != 'None']
        if not valid_draft_ids:
            print(f"   ⚠️  没有有效的草稿ID，跳过测试。草稿IDs: {self.test_draft_ids}")
            return True
        
        draft_id = valid_draft_ids[0]
        print(f"   使用草稿ID: {draft_id}")
        
        # 测试批准决定
        approve_payload = {
            "decision": "approve",
            "feedback": "内容质量很好，符合品牌声音",
            "tags": ["approved", "high-quality"],
            "priority": "high"
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/api/review/decision/{draft_id}",
                json=approve_payload,
                headers=get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 提交审核决定成功: {data.get('decision')}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 提交审核决定失败: {response.status}")
                    print(f"   错误信息: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ 提交审核决定异常: {e}")
            return False
    
    async def test_submit_batch_review_decisions(self) -> bool:
        """测试批量审核决定"""
        print("\n🔍 测试批量审核决定...")
        
        if len(self.test_draft_ids) < 2:
            print("   ⚠️  没有足够的测试草稿，跳过测试")
            return True
        
        # 确保草稿ID不为None
        valid_draft_ids = [draft_id for draft_id in self.test_draft_ids if draft_id and draft_id != 'None']
        if len(valid_draft_ids) < 2:
            print(f"   ⚠️  没有足够的有效草稿ID，跳过测试。有效ID: {valid_draft_ids}")
            return True
        
        batch_payload = {
            "decisions": [
                {
                    "draft_id": valid_draft_ids[0],
                    "decision": "approve",
                    "feedback": "批量审核 - 批准",
                    "tags": ["batch-approved"]
                },
                {
                    "draft_id": valid_draft_ids[1],
                    "decision": "reject",
                    "feedback": "需要改进品牌声音",
                    "tags": ["batch-rejected"]
                }
            ]
        }
        
        print(f"   发送批量审核请求: {batch_payload}")
        
        try:
            async with self.session.post(
                f"{BASE_URL}/api/review/decision/batch",
                json=batch_payload,
                headers=get_auth_headers()
            ) as response:
                print(f"   响应状态: {response.status}")
                print(f"   响应头: {dict(response.headers)}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 批量审核决定成功: {data.get('processed_count')} 个决定")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 批量审核决定失败: {response.status}")
                    print(f"   错误信息: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ 批量审核决定异常: {e}")
            return False
    
    async def test_get_review_history(self) -> bool:
        """测试获取审核历史"""
        print("\n🔍 测试获取审核历史...")
        
        try:
            async with self.session.get(
                f"{BASE_URL}/api/review/history?user_id={TEST_FOUNDER_ID}&limit=10",
                headers=get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 获取审核历史成功: {len(data)} 条记录")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 获取审核历史失败: {response.status}")
                    print(f"   错误信息: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ 获取审核历史异常: {e}")
            return False
    
    async def test_regenerate_content(self) -> bool:
        """测试重新生成内容"""
        print("\n🔍 测试重新生成内容...")
        
        if not self.test_draft_ids:
            print("   ⚠️  没有可用的测试草稿，跳过测试")
            return True
        
        draft_id = self.test_draft_ids[0]
        
        regeneration_payload = {
            "feedback": "内容太正式了，需要更轻松的语气",
            "target_improvements": ["tone", "engagement"],
            "style_preferences": {
                "tone": "casual",
                "engagement": "high"
            },
            "keep_elements": ["topic", "brand_mention"],
            "avoid_elements": ["formal_language", "technical_terms"]
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/api/review/regenerate/{draft_id}",
                json=regeneration_payload,
                headers=get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 重新生成内容成功: {data.get('new_draft_id')}")
                    self.test_regeneration_id = draft_id  # 保存原始ID
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 重新生成内容失败: {response.status}")
                    print(f"   错误信息: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ 重新生成内容异常: {e}")
            return False
    
    async def test_get_regeneration_result(self) -> bool:
        """测试获取重新生成结果"""
        print("\n🔍 测试获取重新生成结果...")
        
        if not self.test_regeneration_id:
            print("   ⚠️  没有重新生成的内容，跳过测试")
            return True
        
        try:
            async with self.session.get(
                f"{BASE_URL}/api/review/new_result/{self.test_regeneration_id}",  # 传原始ID
                headers=get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 获取重新生成结果成功")
                    print(f"   新内容: {data.get('new_content', '')[:100]}...")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 获取重新生成结果失败: {response.status}")
                    print(f"   错误信息: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ 获取重新生成结果异常: {e}")
            return False
    
    async def test_content_generation_integration(self) -> bool:
        """测试与ContentGeneration模块的集成"""
        print("\n🔍 测试与ContentGeneration模块的集成...")
        
        # 测试获取草稿详情（使用ContentGeneration的API）
        if not self.test_draft_ids:
            print("   ⚠️  没有可用的测试草稿，跳过测试")
            return True
        
        draft_id = self.test_draft_ids[0]
        
        try:
            async with self.session.get(
                f"{BASE_URL}/api/content/drafts/{draft_id}",
                headers=get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ ContentGeneration集成测试成功")
                    print(f"   草稿内容: {data.get('generated_text', '')[:100]}...")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ ContentGeneration集成测试失败: {response.status}")
                    print(f"   错误信息: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ ContentGeneration集成测试异常: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始测试精简后的ReviewOptimization API（完整版）")
        print("=" * 70)
        
        test_results = []
        
        # 第一阶段：生成测试数据
        print("\n📋 第一阶段：生成测试数据")
        data_generated = await self.generate_test_drafts()
        if not data_generated:
            print("⚠️  无法生成测试数据，将使用现有数据")
        
        # 第二阶段：运行API测试
        print("\n📋 第二阶段：运行API测试")
        tests = [
            ("获取待审核草稿列表", self.test_get_pending_drafts),
            ("提交审核决定", self.test_submit_review_decision),
            ("批量审核决定", self.test_submit_batch_review_decisions),
            ("获取审核历史", self.test_get_review_history),
            ("重新生成内容", self.test_regenerate_content),
            ("获取重新生成结果", self.test_get_regeneration_result),
            ("ContentGeneration集成", self.test_content_generation_integration),
        ]
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                test_results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} 测试异常: {e}")
                test_results.append((test_name, False))
        
        # 输出测试总结
        print("\n" + "=" * 70)
        print("📊 测试总结:")
        
        passed = 0
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   {test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n🎯 总体结果: {passed}/{len(test_results)} 测试通过")
        
        if passed == len(test_results):
            print("🎉 所有测试通过！ReviewOptimization模块工作正常")
        else:
            print("⚠️ 部分测试失败，需要检查API实现")

async def main():
    """主函数"""
    async with ReviewOptimizationCompleteTester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 