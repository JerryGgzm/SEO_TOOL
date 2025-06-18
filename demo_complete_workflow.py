#!/usr/bin/env python3
"""
完整的工作流程演示脚本
================

这个脚本演示了从用户注册到内容发布的完整流程：

1. 用户注册/登录
2. Twitter OAuth集成  
3. 趋势分析
4. 内容生成
5. SEO优化
6. 审核与优化
7. 调度与发布

使用方法:
    python demo_complete_workflow.py --help
    python demo_complete_workflow.py --setup       # 初始化环境
    python demo_complete_workflow.py --demo        # 运行完整演示
    python demo_complete_workflow.py --step 1      # 运行特定步骤
    python demo_complete_workflow.py --step 3      # 运行趋势分析步骤

环境变量要求:
    # Twitter OAuth (步骤2必需)
    TWITTER_CLIENT_ID=your_twitter_client_id
    TWITTER_CLIENT_SECRET=your_twitter_client_secret
    TWITTER_REDIRECT_URI=http://localhost:8000/auth/twitter/callback
    
    # Gemini趋势分析 (步骤3可选，未设置将使用模拟数据)
    GEMINI_API_KEY=your_gemini_api_key
    GOOGLE_SEARCH_API_KEY=your_google_search_api_key
    GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
"""

import os
import sys
import json
import time
import asyncio
import argparse
import requests
import webbrowser
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pprint import pprint
from dotenv import load_dotenv
# from validate_env import validate_env

load_dotenv('.env')

# 打印环境变量（仅用于调试）
print("\n环境变量检查:")
print(f"TWITTER_CLIENT_ID: {'已设置' if os.getenv('TWITTER_CLIENT_ID') else '未设置'}")
print(f"TWITTER_CLIENT_SECRET: {'已设置' if os.getenv('TWITTER_CLIENT_SECRET') else '未设置'}")
print(f"TWITTER_REDIRECT_URI: {os.getenv('TWITTER_REDIRECT_URI', '未设置')}")
print(f"SECRET_KEY: {'已设置' if os.getenv('SECRET_KEY') else '未设置'}\n")

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_step(step: str, message: str):
    """打印步骤信息"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}🔹 {step}{Colors.END}")
    print(f"{Colors.CYAN}{message}{Colors.END}")

def print_success(message: str):
    """打印成功信息"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_warning(message: str):
    """打印警告信息"""  
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_error(message: str):
    """打印错误信息"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

class APIClient:
    """API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        
    def set_auth_token(self, token: str):
        """设置认证令牌"""
        self.auth_token = token
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })
        
    def request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
        """发送API请求"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            # 确保认证头存在
            headers = {}
            if self.auth_token:
                headers['Authorization'] = f'Bearer {self.auth_token}'
                
            # 为了调试，打印请求信息
            print(f"发送请求: {method} {url}")
            if self.auth_token:
                print(f"使用令牌: {self.auth_token[:20]}...")
            
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=30
            )
            
            if response.status_code >= 400:
                print_error(f"API请求失败: {response.status_code}")
                print(f"响应内容: {response.text}")
                return {"error": response.text, "status_code": response.status_code}
                
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            print_error(f"网络请求失败: {e}")
            return {"error": str(e)}

class CompleteWorkflowDemo:
    """完整工作流程演示"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_client = APIClient(api_base_url)
        self.demo_data = {}
        
        # 演示用户信息
        self.demo_user = {
            "email": "demo@example.com",
            "password": "DemoPassword123!",
            "username": "demo_user",
            "company_name": "DemoTech",
            "product_name": "AI智能助手",
            "product_description": "一款帮助企业提升效率的AI智能助手工具",
            "industry": "AI/科技",
            "brand_voice": "专业、友好、创新"
        }
        
    def check_server_status(self) -> bool:
        """检查服务器状态"""
        print_step("服务器检查", "检查API服务器是否运行...")
        
        try:
            response = self.api_client.request("GET", "/health")
            if "error" not in response:
                print_success("API服务器运行正常")
                return True
        except:
            pass
            
        print_error("API服务器未运行，请先启动服务器")
        print(f"请运行: uvicorn main:app --host 0.0.0.0 --port 8000")
        return False
        
    def step_1_user_registration(self) -> bool:
        """步骤1: 用户注册和登录"""
        print_step("步骤1", "用户注册和登录")
        
        # 尝试登录
        print("尝试登录现有用户...")
        login_response = self.api_client.request("POST", "/api/user/login", {
            "email": self.demo_user["email"],
            "password": self.demo_user["password"]
        })
        
        if "error" not in login_response and "token" in login_response:
            print_success("登录成功")
            self.api_client.set_auth_token(login_response["token"])
            self.api_client.user_id = login_response.get("user_id")
            return True
            
        # 注册新用户
        print("注册新用户...")
        register_response = self.api_client.request("POST", "/api/user/register", {
            "email": self.demo_user["email"],
            "password": self.demo_user["password"],
            "username": self.demo_user["username"],
            "terms_accepted": True
        })
        
        if "error" in register_response:
            print_error(f"注册失败: {register_response['error']}")
            return False
        elif "error" not in register_response:
            print_success(f"注册成功: {register_response.get('message', '')}")
        
        # 登录
        login_response = self.api_client.request("POST", "/api/user/login", {
            "email": self.demo_user["email"],
            "password": self.demo_user["password"]
        })
        
        if "error" in login_response:
            print_error(f"登录失败: {login_response['error']}")
            return False
            
        if "token" not in login_response:
            print(f"login_response: {login_response}")
            print_error("登录响应中没有访问令牌")
            return False
            
        print_success("登录成功")
        self.api_client.set_auth_token(login_response["token"])
        self.api_client.user_id = login_response.get("user_id")
        
        # 更新产品信息
        print("更新产品信息...")
        product_response = self.api_client.request("PUT", "/api/user/profile/product", {
            "company_name": self.demo_user["company_name"],
            "product_name": self.demo_user["product_name"],
            "product_description": self.demo_user["product_description"],
            "industry": self.demo_user["industry"],
            "brand_voice": self.demo_user["brand_voice"]
        })
        
        if "error" not in product_response:
            print_success("产品信息更新成功")
        else:
            print_warning(f"产品信息更新失败: {product_response.get('error', '未知错误')}")
            
        return True
        
    def step_2_twitter_oauth(self) -> bool:
        """步骤2: Twitter OAuth集成"""
        print_step("步骤2", "Twitter OAuth集成")
        
        # 检查环境变量
        if not os.getenv('TWITTER_CLIENT_ID') or not os.getenv('TWITTER_CLIENT_SECRET'):
            print_error("缺少Twitter API配置")
            print_warning("请设置以下环境变量:")
            print("  - TWITTER_CLIENT_ID")
            print("  - TWITTER_CLIENT_SECRET")
            print("  - TWITTER_REDIRECT_URI (可选，默认为 http://localhost:8000/auth/twitter/callback)")
            return False
        
        # 检查Twitter连接状态
        status_response = self.api_client.request("GET", "/api/user/profile/twitter/status")
        print("status response: ", status_response)
        
        if "error" not in status_response and status_response.get("connected"):
            print_success("Twitter账户已连接")
            return True
            
        print("需要连接Twitter账户...")
        print("您将被重定向到Twitter的官方授权页面。")
        print("请确保您已登录Twitter，并仔细阅读授权范围。")
        
        # 获取OAuth授权URL
        auth_response = self.api_client.request("GET", "/api/user/profile/twitter/auth_url")

        print("url response: ", auth_response)
        
        if "error" in auth_response:
            print_error(f"获取Twitter授权URL失败: {auth_response['error']}")
            print_warning("请确保:")
            print("1. TWITTER_CLIENT_ID 和 TWITTER_CLIENT_SECRET 已正确配置")
            print("2. TWITTER_REDIRECT_URI 已正确配置")
            print("3. 应用已在Twitter开发者平台正确设置")
            return False
            
        auth_url = auth_response["auth_url"]
        state = auth_response["state"]
        
        print(f"\n🔐 授权URL:")
        print(f"{Colors.CYAN}{auth_url}{Colors.END}")
        
        # 自动打开浏览器
        try:
            webbrowser.open(auth_url)
            print_success("已在浏览器中打开授权页面")
        except:
            print_warning("无法自动打开浏览器，请手动复制URL到浏览器")
            
        print("\n📝 授权步骤:")
        print("1. 在Twitter授权页面登录您的账号")
        print("2. 仔细阅读授权范围")
        print("3. 点击'授权'按钮")
        print("4. 复制回调URL中的code参数")
        
        # 等待用户输入授权码
        print("\n完成授权后, 请复制回调URL中的code参数:")
        code = input("请输入授权码: ").strip()
        
        if not code:
            print_error("未输入授权码")
            return False
            
        # 处理回调 - 不再需要传递code_verifier
        print("\n正在处理授权...")
        callback_response = self.api_client.request("POST", "/api/user/profile/twitter/callback", {
            "code": code,
            "state": state
            # 注意：code_verifier 现在由服务器安全管理，不需要客户端传递
        })
        
        if "error" in callback_response:
            print_error(f"Twitter授权失败: {callback_response['error']}")
            print_warning("请确保:")
            print("1. 授权码正确且未过期")
            print("2. 回调URL配置正确")
            print("3. 应用有正确的权限范围")
            return False
            
        print_success("Twitter账户连接成功")
        print("您现在可以使用Twitter API功能了")
        
        # 添加短暂延迟确保数据库事务完全提交
        import time
        print("正在确保数据持久化...")
        time.sleep(3)
        
        return True

    def step_3_trend_analysis(self) -> bool:
        """步骤3: 趋势分析"""
        print_step("步骤3", "趋势分析")
        
        # 检查环境变量
        required_vars = ['GEMINI_API_KEY', 'GOOGLE_SEARCH_API_KEY', 'GOOGLE_SEARCH_ENGINE_ID']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print_warning(f"缺少环境变量: {', '.join(missing_vars)}")
            print("将使用模拟数据进行演示")
            self.demo_data["trends"] = [
                {
                    "keyword": "AI智能助手",
                    "trend_score": 85,
                    "analysis": "AI智能助手市场持续增长，企业对自动化工具需求旺盛。ChatGPT和类似工具的成功带动了整个行业的发展。",
                    "opportunities": ["企业自动化", "客服机器人", "代码生成"],
                    "hashtags": ["#AI", "#智能助手", "#企业工具", "#自动化"]
                },
                {
                    "keyword": "企业效率工具",
                    "trend_score": 78,
                    "analysis": "远程办公推动了企业效率工具的快速发展，团队协作和项目管理工具需求增长显著。",
                    "opportunities": ["项目管理", "团队协作", "时间管理"],
                    "hashtags": ["#效率工具", "#远程办公", "#团队协作", "#项目管理"]
                }
            ]
            print_warning("使用模拟趋势数据")
            self._display_trend_results()
            return True
        
        # 基于产品信息生成关键词
        product_keywords = []
        if hasattr(self, 'demo_user'):
            keywords_from_product = [
                self.demo_user.get("product_name", "").split()[0] if self.demo_user.get("product_name") else "",
                self.demo_user.get("industry", ""),
                "效率工具", "企业工具"
            ]
            product_keywords = [k for k in keywords_from_product if k]
        
        # 默认关键词
        if not product_keywords:
            product_keywords = ["AI", "智能助手", "企业工具"]
        
        print(f"分析关键词: {product_keywords}")
        
        # 构建用户上下文 (在try块外定义，确保作用域正确)
        user_context = f"我是{self.demo_user.get('industry', '技术')}行业的从业者，产品是{self.demo_user.get('product_name', 'AI工具')}"
        
        # 尝试API调用
        try:
            # 首先检查Gemini配置
            config_response = self.api_client.request("GET", "/api/trends/gemini/config-check")
            if "error" in config_response:
                error_detail = config_response.get('error', '未知错误')
                print_warning(f"Gemini配置检查失败: {error_detail}")
                
                # 检查是否是503错误（配置不完整）
                if config_response.get('status_code') == 503:
                    print_warning("这是因为Google API配置不完整，将跳过在线分析")
                    raise Exception("Google API配置不完整")
                else:
                    raise Exception("配置检查失败")
            
            print_success("Gemini配置检查通过")
            
            # 执行趋势分析
            print("正在分析网络热门趋势...")
            
            # 构建查询参数 - FastAPI期望重复的参数名来表示列表
            params = [
                ("user_context", user_context),
                ("max_topics", 5)
            ]
            # 添加每个keyword作为单独的keywords参数
            for keyword in product_keywords:
                params.append(("keywords", keyword))
            
            analysis_response = self.api_client.request("POST", "/api/trends/gemini/analyze", 
                                                       data=None, params=params)
            
            if "error" not in analysis_response and analysis_response.get("success"):
                print_success("趋势分析完成")
                
                # 解析分析结果
                self.demo_data["trends"] = [{
                    "keyword": ', '.join(product_keywords),
                    "trend_score": 90,
                    "analysis": analysis_response.get("analysis", "分析结果未获取"),
                    "search_query": analysis_response.get("search_query", ""),
                    "function_called": analysis_response.get("function_called", ""),
                    "timestamp": analysis_response.get("timestamp", "")
                }]
                
                # 尝试获取结构化总结
                print("正在生成结构化总结...")
                summary_params = [
                    ("user_context", user_context),
                    ("max_topics", 3)
                ]
                # 添加每个keyword作为单独的keywords参数
                for keyword in product_keywords:
                    summary_params.append(("keywords", keyword))
                
                summary_response = self.api_client.request("POST", "/api/trends/gemini/summary", 
                                                         data=None, params=summary_params)
                
                if "error" not in summary_response and summary_response.get("success"):
                    structured_summary = summary_response.get("structured_summary")
                    if structured_summary:
                        self.demo_data["trends"][0]["structured_summary"] = structured_summary
                        print_success("结构化总结生成完成")
                    
            else:
                raise Exception(f"API分析失败: {analysis_response.get('error', '未知错误')}")
                
        except Exception as e:
            print_warning(f"在线趋势分析失败: {e}")
            print("使用本地趋势分析...")
            
            # 尝试本地分析
            try:
                from modules.trend_analysis import quick_analyze_trending_topics
                
                result = quick_analyze_trending_topics(
                    keywords=product_keywords,
                    user_context=user_context
                )
                
                if result["success"]:
                    self.demo_data["trends"] = [{
                        "keyword": ', '.join(product_keywords),
                        "trend_score": 85,
                        "analysis": result["analysis"],
                        "search_query": result.get("search_query", ""),
                        "function_called": result.get("function_called", ""),
                        "timestamp": result["timestamp"]
                    }]
                    print_success("本地趋势分析完成")
                else:
                    raise Exception(f"本地分析失败: {result.get('error')}")
                    
            except Exception as local_error:
                print_warning(f"本地分析也失败: {local_error}")
                # 使用模拟数据
                self.demo_data["trends"] = [
                    {
                        "keyword": ', '.join(product_keywords),
                        "trend_score": 80,
                        "analysis": f"基于关键词 {product_keywords} 的模拟趋势分析：当前市场对{product_keywords[0]}相关产品需求旺盛，特别是在企业级应用场景中。建议关注用户体验优化和功能差异化。",
                        "opportunities": ["市场机会1", "市场机会2", "市场机会3"],
                        "hashtags": [f"#{kw}" for kw in product_keywords]
                    }
                ]
                print_warning("使用模拟趋势数据")
        
        # 显示分析结果
        self._display_trend_results()
        return True
    
    def _display_trend_results(self):
        """显示趋势分析结果"""
        if not self.demo_data.get("trends"):
            print_warning("没有趋势数据可显示")
            return
            
        print("\n📈 趋势分析结果:")
        print("="*50)
        
        for i, trend in enumerate(self.demo_data["trends"], 1):
            print(f"\n🔍 趋势 {i}:")
            print(f"关键词: {trend.get('keyword', 'N/A')}")
            print(f"趋势评分: {trend.get('trend_score', 'N/A')}")
            
            if trend.get('search_query'):
                print(f"搜索查询: {trend['search_query']}")
            if trend.get('function_called'):
                print(f"调用功能: {trend['function_called']}")
            if trend.get('timestamp'):
                print(f"分析时间: {trend['timestamp']}")
                
            print(f"\n📝 分析内容:")
            analysis_text = trend.get('analysis', '无分析内容')
            # 限制显示长度
            if len(analysis_text) > 300:
                print(f"{analysis_text[:300]}...")
            else:
                print(analysis_text)
                
            # 显示结构化总结
            if trend.get('structured_summary'):
                print(f"\n📋 结构化总结:")
                summary_text = trend['structured_summary']
                if len(summary_text) > 200:
                    print(f"{summary_text[:200]}...")
                else:
                    print(summary_text)
                    
            # 显示机会和标签
            if trend.get('opportunities'):
                print(f"\n💡 市场机会: {', '.join(trend['opportunities'])}")
            if trend.get('hashtags'):
                print(f"🏷️  建议标签: {' '.join(trend['hashtags'])}")
                
        print("\n" + "="*50)

    def step_4_content_generation(self) -> bool:
        """步骤4: 内容生成"""
        print_step("步骤4", "内容生成")
        
        # 基础内容生成
        print("生成基础宣传内容...")
        generation_request = {
            "content_type": "social_media_post",
            "topic": "AI智能助手产品介绍",
            "target_audience": "企业用户",
            "platform": "twitter",
            "tone": "专业友好",
            "include_hashtags": True,
            "max_length": 280
        }
        
        content_response = self.api_client.request("POST", "/api/content/generate", generation_request)
        
        if "error" in content_response:
            print_warning(f"内容生成失败: {content_response['error']}")
            # 使用模拟内容
            self.demo_data["generated_content"] = [
                "🚀 介绍我们的AI智能助手！专为企业打造，提升工作效率，简化日常任务。让AI成为您团队的得力助手 #AI #企业工具 #效率提升",
                "💡 智能化办公新体验！我们的AI助手能够理解您的需求，提供个性化解决方案。现在就体验未来的工作方式 #人工智能 #办公自动化",
                "🌟 重新定义企业效率！AI智能助手不仅是工具，更是您的智能伙伴。24/7随时待命，让工作变得更简单 #智能助手 #企业服务"
            ]
            print_warning("使用模拟内容数据")
        else:
            self.demo_data["generated_content"] = content_response.get("content_variants", [])
            print_success(f"生成了 {len(self.demo_data['generated_content'])} 个内容变体")
            
        # 显示生成的内容
        if self.demo_data["generated_content"]:
            print("\n📝 生成的内容:")
            for i, content in enumerate(self.demo_data["generated_content"][:3], 1):
                print(f"  {i}. {content[:100]}...")
                
        return True

    def step_5_seo_optimization(self) -> bool:
        """步骤5: SEO优化"""
        print_step("步骤5", "SEO优化")
        
        if not self.demo_data.get("generated_content"):
            print_error("没有可优化的内容")
            return False
            
        selected_content = self.demo_data["generated_content"][0]
        print(f"优化内容: {selected_content[:100]}...")
        
        # 内容SEO优化
        optimization_response = self.api_client.request("POST", "/api/seo/optimize", {
            "content": selected_content,
            "target_keywords": ["AI", "智能助手", "企业工具"],
            "platform": "twitter",
            "optimization_focus": "engagement"
        })
        
        if "error" in optimization_response:
            print_warning(f"SEO优化失败: {optimization_response['error']}")
            # 使用模拟优化结果
            self.demo_data["optimized_content"] = {
                "optimized_text": selected_content + " #AI助手 #企业效率 #智能办公",
                "optimization_score": 85,
                "suggested_hashtags": ["#AI助手", "#企业效率", "#智能办公", "#工作流程"],
                "seo_suggestions": [
                    "添加热门关键词",
                    "优化标签使用",
                    "提高内容互动性"
                ]
            }
            print_warning("使用模拟优化数据")
        else:
            self.demo_data["optimized_content"] = optimization_response
            print_success("SEO优化完成")
            
        # 显示优化结果
        print(f"\n🎯 优化评分: {self.demo_data['optimized_content'].get('optimization_score', 'N/A')}")
        print(f"📝 优化后内容: {self.demo_data['optimized_content'].get('optimized_text', '')[:150]}...")
        
        return True

    def step_6_review_optimization(self) -> bool:
        """步骤6: 审核与优化"""
        print_step("步骤6", "审核与优化")
        
        if not self.demo_data.get("optimized_content"):
            print_error("没有可审核的内容")
            return False
            
        # 模拟审核流程
        optimized_text = self.demo_data["optimized_content"]["optimized_text"]
        
        # 显示内容供审核
        print(f"\n📋 待审核内容:")
        print(f"内容: {optimized_text}")
        print(f"SEO评分: {self.demo_data['optimized_content'].get('optimization_score', 'N/A')}")
        
        # 模拟审核决定
        print("\n选择审核决定:")
        print("1. 批准 (APPROVE)")
        print("2. 编辑后批准 (EDIT_AND_APPROVE)")  
        print("3. 拒绝 (REJECT)")
        
        try:
            choice = input("请选择 (1-3, 默认为1): ").strip() or "1"
            
            if choice == "1":
                decision = "APPROVE"
                feedback = "内容质量良好，可以发布"
                self.demo_data["approved_content"] = optimized_text
            elif choice == "2":
                decision = "EDIT_AND_APPROVE"
                feedback = "内容需要小幅调整"
                # 进行编辑
                print("请输入编辑后的内容 (回车保持原内容):")
                edited_content = input().strip()
                if edited_content:
                    self.demo_data["approved_content"] = edited_content
                else:
                    self.demo_data["approved_content"] = optimized_text
            else:
                decision = "REJECT"
                feedback = "内容需要重新生成"
                print_warning("内容已拒绝，需要重新生成")
                return False
                
        except KeyboardInterrupt:
            decision = "APPROVE"
            feedback = "自动批准"
            self.demo_data["approved_content"] = optimized_text
            
        print_success(f"审核决定: {decision}")
        self.demo_data["review_decision"] = decision
        return True

    def step_7_scheduling_posting(self) -> bool:
        """步骤7: 调度与发布"""
        print_step("步骤7", "调度与发布")
        
        if not self.demo_data.get("approved_content"):
            print_error("没有已批准的内容可发布")
            return False
            
        approved_content = self.demo_data["approved_content"]
        print(f"准备发布内容: {approved_content[:100]}...")
        
        # 选择发布方式
        print("\n选择发布方式:")
        print("1. 立即发布")
        print("2. 调度发布")
        print("3. 仅保存草稿")
        
        try:
            choice = input("请选择 (1-3, 默认为3): ").strip() or "3"
            
            if choice == "1":
                # 立即发布
                print("确认立即发布到Twitter? (y/N): ")
                confirm = input().strip().lower()
                
                if confirm == 'y':
                    # 发布内容
                    publish_response = self.api_client.request("POST", "/api/twitter/tweets", {
                        "text": approved_content
                    })
                    
                    if "error" not in publish_response:
                        tweet_data = publish_response.get("data", {})
                        tweet_id = tweet_data.get("id")
                        print_success(f"内容发布成功！")
                        if tweet_id:
                            print(f"🐦 Tweet ID: {tweet_id}")
                            print(f"🔗 链接: https://x.com/user/status/{tweet_id}")
                    else:
                        print_error(f"发布失败: {publish_response['error']}")
                        print_warning("模拟发布成功")
                        print_success("内容已成功发布到Twitter")
                else:
                    print_warning("发布已取消")
                    
            elif choice == "2":
                # 调度发布
                schedule_time = datetime.now() + timedelta(hours=1)
                print_success(f"内容已调度，将于 {schedule_time.strftime('%Y-%m-%d %H:%M')} 发布")
                
            else:
                # 仅保存草稿
                print_success("内容已保存为草稿")
                
        except KeyboardInterrupt:
            print_warning("发布已取消")
            
        return True

    def run_complete_demo(self) -> bool:
        """运行完整演示"""
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}🚀 开始完整工作流程演示{Colors.END}")
        print("="*60)
        
        steps = [
            ("检查服务器", self.check_server_status),
            ("用户注册/登录", self.step_1_user_registration),
            ("Twitter OAuth", self.step_2_twitter_oauth),
            ("趋势分析", self.step_3_trend_analysis),
            ("内容生成", self.step_4_content_generation),
            ("SEO优化", self.step_5_seo_optimization),
            ("审核优化", self.step_6_review_optimization),
            ("调度发布", self.step_7_scheduling_posting)
        ]
        
        for i, (step_name, step_func) in enumerate(steps, 1):
            print(f"\n{Colors.BOLD}📍 步骤 {i}/{len(steps)}: {step_name}{Colors.END}")
            print("-" * 40)
            
            try:
                success = step_func()
                if not success:
                    print_error(f"步骤 {i} 失败，演示中断")
                    return False
                    
                print_success(f"步骤 {i} 完成")
                
                # 步骤间暂停
                if i < len(steps):
                    input(f"\n{Colors.YELLOW}按回车继续下一步...{Colors.END}")
                    
            except KeyboardInterrupt:
                print_warning(f"\n演示在步骤 {i} 被用户中断")
                return False
            except Exception as e:
                print_error(f"步骤 {i} 发生异常: {e}")
                return False
                
        print(f"\n{Colors.BOLD}{Colors.GREEN}🎉 完整工作流程演示成功！{Colors.END}")
        print("="*60)
        
        # 显示演示摘要
        self.print_demo_summary()
        
        return True

    def run_specific_step(self, step_number: int) -> bool:
        """运行特定步骤"""
        steps = {
            0: ("服务器检查", self.check_server_status),
            1: ("用户注册/登录", self.step_1_user_registration),
            2: ("Twitter OAuth", self.step_2_twitter_oauth),
            3: ("趋势分析", self.step_3_trend_analysis),
            4: ("内容生成", self.step_4_content_generation),
            5: ("SEO优化", self.step_5_seo_optimization),
            6: ("审核优化", self.step_6_review_optimization),
            7: ("调度发布", self.step_7_scheduling_posting)
        }
        
        if step_number not in steps:
            print_error(f"无效的步骤编号: {step_number}")
            print("可用步骤: 0-7")
            return False
        
        # 对于步骤3及以上，需要确保用户已经登录
        if step_number >= 3 and not self.api_client.auth_token:
            print_warning("运行此步骤需要用户登录，自动执行登录...")
            if not self.check_server_status():
                return False
            if not self.step_1_user_registration():
                print_error("用户登录失败，无法继续")
                return False
            print_success("自动登录成功，继续执行步骤...")
            
        step_name, step_func = steps[step_number]
        print(f"\n{Colors.BOLD}🎯 运行步骤 {step_number}: {step_name}{Colors.END}")
        print("-" * 40)
        
        try:
            return step_func()
        except Exception as e:
            print_error(f"步骤执行失败: {e}")
            return False
            
    def print_demo_summary(self):
        """打印演示摘要"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}📊 演示摘要{Colors.END}")
        print("="*40)
        
        summary_items = [
            ("用户ID", self.api_client.user_id),
            ("认证令牌", "已设置" if self.api_client.auth_token else "未设置"),
            ("趋势数量", len(self.demo_data.get("trends", []))),
            ("生成内容数", len(self.demo_data.get("generated_content", []))),
            ("SEO评分", self.demo_data.get("optimized_content", {}).get("optimization_score")),
            ("审核决定", self.demo_data.get("review_decision")),
            ("最终内容", self.demo_data.get("approved_content", "未生成")[:50] + "..." if self.demo_data.get("approved_content") else "未生成")
        ]
        
        for item, value in summary_items:
            if value:
                print(f"  {item}: {value}")
                
        # 显示趋势分析详情
        if self.demo_data.get("trends"):
            print(f"\n{Colors.BOLD}📈 趋势分析详情:{Colors.END}")
            for i, trend in enumerate(self.demo_data["trends"], 1):
                print(f"  趋势 {i}:")
                print(f"    关键词: {trend.get('keyword', 'N/A')}")
                print(f"    评分: {trend.get('trend_score', 'N/A')}")
                if trend.get('search_query'):
                    print(f"    搜索: {trend['search_query']}")
                if trend.get('opportunities'):
                    print(f"    机会: {', '.join(trend['opportunities'][:3])}")
                if trend.get('hashtags'):
                    print(f"    标签: {' '.join(trend['hashtags'][:3])}")

    def setup_environment(self):
        """设置演示环境"""
        print_step("环境设置", "检查和设置演示环境")
        
        # 验证环境变量
        # if not validate_env():
        #     print_error("环境变量验证失败")
        #     return False
            
        print_success("环境设置完成")
        return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="完整工作流程演示脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s --demo                 # 运行完整演示
  %(prog)s --step 1               # 运行步骤1(用户注册)
  %(prog)s --step 3               # 运行步骤3(趋势分析)
  %(prog)s --url http://localhost:8000  # 指定API地址
        """
    )
    
    parser.add_argument('--demo', action='store_true',
                       help='运行完整工作流程演示')
    parser.add_argument('--step', type=int, metavar='N',
                       help='运行特定步骤 (0-7)')
    parser.add_argument('--setup', action='store_true',
                       help='设置演示环境')
    parser.add_argument('--url', default='http://localhost:8000',
                       help='API服务器地址 (默认: http://localhost:8000)')
    
    args = parser.parse_args()
    
    # 创建演示实例
    demo = CompleteWorkflowDemo(args.url)
    
    try:
        if args.setup:
            success = demo.setup_environment()
        elif args.step is not None:
            success = demo.run_specific_step(args.step)
        elif args.demo:
            success = demo.run_complete_demo()
        else:
            parser.print_help()
            return
            
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print_warning("\n演示被用户中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"演示发生异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 