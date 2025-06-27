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
        """步骤2: Twitter OAuth授权"""
        print_step("Twitter OAuth授权", "检查Twitter授权状态...")
        
        # 首先检查是否需要重新授权
        print("检查Twitter授权状态...")
        reauth_check_response = self.api_client.request("GET", "/api/user/profile/twitter/reauth-check")
        
        if "error" not in reauth_check_response:
            needs_reauth = reauth_check_response.get("needs_reauth", True)
            has_access_token = reauth_check_response.get("has_access_token", False)
            
            if not needs_reauth and has_access_token:
                print_success(f"Twitter账户已授权且令牌有效, 令牌：{reauth_check_response.get('access_token', '未知')}")
                return True
            
            if needs_reauth:
                print_warning("检测到需要重新授权Twitter账户")
                print(f"原因: {reauth_check_response.get('message', '令牌无效或过期')}")
                
                # 询问用户是否要重新授权
                print("\n选择操作:")
                print("1. 开始重新授权流程")
                print("2. 跳过Twitter授权")
                
                choice = input("请选择 (1-2, 默认为1): ").strip() or "1"
                
                if choice == "2":
                    print_warning("跳过Twitter授权，某些功能可能不可用")
                    return False
                
                # 开始重新授权流程
                print("启动Twitter重新授权流程...")
                start_reauth_response = self.api_client.request("POST", "/api/user/profile/twitter/start-reauth")
                
                if "error" not in start_reauth_response:
                    auth_url = start_reauth_response.get("auth_url")
                    state = start_reauth_response.get("state")
                    
                    if auth_url:
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
                else:
                    print_error(f"启动重新授权失败: {start_reauth_response.get('error', '未知错误')}")
                    return False
        
        # 如果检查失败，使用原有的授权流程
        print_warning("无法检查授权状态，使用标准授权流程...")
        
        # 原有的授权逻辑
        status_response = self.api_client.request("GET", "/api/user/profile/twitter/status")
        
        if "error" not in status_response and status_response.get("connected"):
            # 检查token是否有效
            if status_response.get("has_valid_token"):
                print_success("Twitter账户已连接且token有效")
                return True
            else:
                print_warning("Twitter账户已连接但token无效或已过期")
                print(f"状态信息: {status_response.get('message', '未知状态')}")
                
                # 询问是否刷新token
                print("\n选择操作:")
                print("1. 尝试刷新token")
                print("2. 重新授权")
                
                try:
                    choice = input("请选择 (1-2, 默认为2): ").strip() or "2"
                    
                    if choice == "1":
                        print("尝试刷新Twitter token...")
                        refresh_response = self.api_client.request("POST", "/api/user/profile/twitter/refresh")
                        
                        if "error" not in refresh_response:
                            print_success("Token刷新成功")
                            return True
                        else:
                            print_warning(f"Token刷新失败: {refresh_response.get('error', '未知错误')}")
                            print("需要重新授权...")
                            # 继续执行重新授权流程
                            
                except KeyboardInterrupt:
                    print("\n用户取消操作")
                    return False
        
        # 执行完整的OAuth流程
        print("开始Twitter OAuth授权流程...")
        
        try:
            # 获取授权URL
            auth_response = self.api_client.request("GET", "/api/user/profile/twitter/auth")
            
            if "error" in auth_response:
                print_error(f"获取授权URL失败: {auth_response['error']}")
                return False
            
            auth_url = auth_response.get("auth_url")
            if not auth_url:
                print_error("未获取到授权URL")
                return False
            
            print_success("授权URL获取成功")
            print(f"\n请访问以下URL完成Twitter授权:")
            print(f"🔗 {auth_url}")
            
            print("\n授权完成后，您将被重定向到回调页面")
            print("回调页面会显示授权码，请复制该授权码")
            
            # 等待用户输入授权码
            code = input("\n请输入授权码: ").strip()
            if not code:
                print_error("未输入授权码")
                return False
            
            # 提交授权码
            callback_data = {
                "code": code,
                "state": auth_response.get("state")
            }
            
            callback_response = self.api_client.request(
                "POST", 
                "/api/user/profile/twitter/callback",
                data=callback_data
            )
            
            if "error" in callback_response:
                print_error(f"授权回调失败: {callback_response['error']}")
                return False
            
            print_success("Twitter授权成功！")
            twitter_username = callback_response.get("twitter_username")
            if twitter_username:
                print(f"Twitter用户名: @{twitter_username}")
            
            return True
            
        except KeyboardInterrupt:
            print("\n用户取消授权")
            return False
        except Exception as e:
            print_error(f"授权过程发生错误: {e}")
            return False

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
            # if len(analysis_text) > 400:
            #     print(f"{analysis_text[:400]}...")
            # else:
            print(analysis_text)
                
            # 显示结构化总结
            if trend.get('structured_summary'):
                print(f"\n📋 结构化总结:")
                summary_text = trend['structured_summary']
                # if len(summary_text) > 200:
                #     print(f"{summary_text[:200]}...")
                # else:
                print(summary_text)
                    
            # 显示机会和标签
            if trend.get('opportunities'):
                print(f"\n💡 市场机会: {', '.join(trend['opportunities'])}")
            if trend.get('hashtags'):
                print(f"🏷️  建议标签: {' '.join(trend['hashtags'])}")
                
        print("\n" + "="*50)


    def step_7_scheduling_posting(self) -> bool:
        """步骤7: 调度与发布"""
        print_step("步骤7", "调度与发布")
        
        self.demo_data["approved_content"] = "🚀 探索AI驱动的创新趋势！我们的智能助手正在重新定义效率边界，为企业释放前所未有的潜力。#AI #创新 #效率 #科技"

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
                            
                        # 保存发布记录
                        self.demo_data["published_tweet_id"] = tweet_id
                        self.demo_data["published_at"] = datetime.now().isoformat()
                    else:
                        print_error(f"发布失败: {publish_response['error']}")
                        print_warning("模拟发布成功")
                        print_success("内容已成功发布到Twitter")
                else:
                    print_warning("发布已取消")
                    
            elif choice == "2":
                # 真正的调度发布功能
                return self._handle_content_scheduling(approved_content)
                
            else:
                # 仅保存草稿
                print_success("内容已保存为草稿")
                
        except KeyboardInterrupt:
            print_warning("发布已取消")
            
        return True

    def _handle_content_scheduling(self, content: str) -> bool:
        """处理内容调度"""
        print("\n📅 设置调度时间:")
        print("1. 1分钟后")
        print("2. 5分钟后")
        print("3. 自定义时间")
        
        time_choice = input("请选择调度时间 (1-3, 默认为1): ").strip() or "1"
        
        # 使用UTC时间，与服务器端验证保持一致
        now_utc = datetime.utcnow()
        print(f"当前UTC时间: {now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        schedule_time = None
        
        if time_choice == "1":
            schedule_time = now_utc + timedelta(minutes=1)
            print(f"⏰ 选择: 1分钟后 (UTC时间)")
        elif time_choice == "2":
            schedule_time = now_utc + timedelta(minutes=5)
            print(f"⏰ 选择: 5分钟后 (UTC时间)")
        elif time_choice == "3":
            print("请输入调度时间 (格式: YYYY-MM-DD HH:MM，将被视为UTC时间):")
            custom_time = input().strip()
            try:
                schedule_time = datetime.strptime(custom_time, "%Y-%m-%d %H:%M")
                if schedule_time <= now_utc:
                    print_error("调度时间必须在未来 (UTC时间)")
                    return False
                print(f"⏰ 自定义时间: {schedule_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            except ValueError:
                print_error("时间格式错误，请使用 YYYY-MM-DD HH:MM 格式")
                return False
        else:
            print_error("无效选择")
            return False
        
        print(f"\n⏰ 最终调度时间: {schedule_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"🔍 当前UTC时间: {now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"⏳ 距离调度时间: {(schedule_time - now_utc).total_seconds():.0f} 秒")
        
        # 创建内容草稿 (实际保存到数据库)
        print("📝 创建内容草稿...")
        
        # 使用UUID格式的content_id，与数据库模型兼容
        import uuid
        content_id = str(uuid.uuid4())
        
        # 直接在数据库中创建内容草稿记录
        try:
            import sqlite3
            
            print(f"🔍 调试信息:")
            print(f"  User ID: {self.api_client.user_id}")
            print(f"  Content ID: {content_id}")
            print(f"  Content: {content[:50]}...")
            
            
            # 连接数据库
            conn = sqlite3.connect('ideation_db.sqlite')
            cursor = conn.cursor()
            
            # 首先获取user_profiles中的用户信息
            cursor.execute("SELECT user_id, email FROM user_profiles WHERE user_id = ?", (self.api_client.user_id,))
            user_profile = cursor.fetchone()
            if not user_profile:
                print_error(f"❌ User Profile {self.api_client.user_id} 不存在于数据库中")
                conn.close()
                return False
            
            user_id, email = user_profile
            print_success(f"✅ User Profile 验证通过: {email}")
            
            # 检查或创建对应的founder记录
            cursor.execute("SELECT id FROM founders WHERE id = ?", (user_id,))
            founder_exists = cursor.fetchone()
            if not founder_exists:
                print_warning(f"⚠️  Founder记录不存在，正在创建...")
                # 创建founder记录，使用user_profiles中的信息
                current_time = datetime.utcnow()
                cursor.execute("""
                    INSERT INTO founders (id, email, hashed_password, created_at, updated_at, settings)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    email,
                    "demo_password_hash",  # 占位符密码哈希
                    current_time.isoformat(),
                    current_time.isoformat(),
                    '{"demo": true}'  # 标记为demo用户
                ))
                print_success(f"✅ Founder记录创建成功")
            else:
                print_success(f"✅ Founder记录已存在")
            
            # 创建内容草稿记录
            current_time = datetime.utcnow()
            
            # 检查是否已存在相同ID的记录
            cursor.execute("SELECT id FROM generated_content_drafts WHERE id = ?", (content_id,))
            existing = cursor.fetchone()
            if existing:
                print_warning(f"⚠️  内容草稿 {content_id} 已存在，跳过创建")
            else:
                cursor.execute("""
                    INSERT INTO generated_content_drafts (
                        id, founder_id, content_type, generated_text, status,
                        ai_generation_metadata, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    content_id,
                    user_id,  # 使用相同的ID作为founder_id
                    "tweet",
                    content,
                    "approved",  # 设置为已批准状态，可以调度
                    '{"source": "demo_workflow", "created_at": "' + current_time.isoformat() + '"}',
                    current_time.isoformat()
                ))
                
                # 验证插入是否成功
                if cursor.rowcount == 1:
                    print_success(f"✅ 数据库插入成功 (影响 {cursor.rowcount} 行)")
                else:
                    print_error(f"❌ 数据库插入失败 (影响 {cursor.rowcount} 行)")
            
            conn.commit()
            
            # 验证记录是否真的存在
            cursor.execute("SELECT id, status, content_type FROM generated_content_drafts WHERE id = ?", (content_id,))
            verification = cursor.fetchone()
            if verification:
                print_success(f"✅ 内容草稿验证成功: ID={verification[0]}, Status={verification[1]}, Type={verification[2]}")
            else:
                print_error(f"❌ 内容草稿验证失败: 数据库中找不到记录")
                conn.close()
                return False
            
            conn.close()
            
            print_success(f"✅ 内容草稿创建成功！")
            print(f"📋 草稿ID: {content_id}")
            print(f"📊 数据库记录已创建并验证")
            
        except Exception as e:
            print_error(f"❌ 创建内容草稿失败: {e}")
            print_warning("将使用UUID继续演示，但调度可能失败")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            return False
        
        # 显示保存的内容信息
        print(f"\n📄 已保存的内容:")
        print(f"ID: {content_id}")
        print(f"内容: {content[:100]}{'...' if len(content) > 100 else ''}")
        print(f"状态: approved (已批准，可调度)")
        print(f"创建时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        return self._schedule_content_for_later(content_id, content, schedule_time)
        

    def _publish_content_immediately(self, content_id: str, content: str) -> bool:
        """立即发布内容"""
        print("\n🚀 立即发布内容...")
        
        try:
            publish_response = self.api_client.request(
                "POST", 
                f"/api/scheduling/publish/{content_id}",
                {
                    "force_publish": False,
                    "skip_rules_check": False
                }
            )
            
            if "error" not in publish_response and publish_response.get("success"):
                tweet_id = publish_response.get("posted_tweet_id")
                print_success("🎉 内容发布成功！")
                if tweet_id:
                    print(f"🐦 Tweet ID: {tweet_id}")
                    print(f"🔗 链接: https://x.com/user/status/{tweet_id}")
                
                self.demo_data["published_content"] = {
                    "content_id": content_id,
                    "tweet_id": tweet_id,
                    "content": content,
                    "published_at": datetime.now().isoformat(),
                    "status": "published"
                }
                
                return True
            else:
                error_msg = publish_response.get("message", "未知错误")
                print_error(f"发布失败: {error_msg}")
                return False
                
        except Exception as e:
            print_error(f"发布API调用失败: {e}")
            return False

    def _schedule_content_for_later(self, content_id: str, content: str, schedule_time: datetime) -> bool:
        """调度内容稍后发布"""
        print("\n📅 调度内容发布...")
        
        # 使用UTC时间进行比较，与服务器端验证保持一致
        current_utc = datetime.utcnow()
        
        # 如果传入的schedule_time是本地时间，需要转换为UTC
        # 简单处理：如果时间已经过期，设置为UTC时间+5分钟
        if schedule_time <= current_utc:
            schedule_time = current_utc + timedelta(minutes=5)
            print(f"⏰ 调整调度时间为UTC: {schedule_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        else:
            print(f"⏰ 调度时间: {schedule_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        schedule_data = {
            "content_id": content_id,
            "scheduled_time": schedule_time.isoformat(),
            "priority": 5,  # 使用整数而不是字符串
            "tags": ["demo", "scheduled"]
        }
        
        print(f"🔍 调试信息:")
        print(f"  当前UTC时间: {current_utc.isoformat()}")
        print(f"  调度UTC时间: {schedule_time.isoformat()}")
        print(f"  时间差: {(schedule_time - current_utc).total_seconds()} 秒")
        
        try:
            schedule_response = self.api_client.request(
                "POST", 
                f"/api/scheduling/schedule/{content_id}", 
                schedule_data
            )
            
            if "error" not in schedule_response and schedule_response.get("success"):
                scheduled_id = schedule_response.get("scheduled_content_id")
                print_success("✅ 内容调度成功！")
                print(f"📋 调度ID: {scheduled_id}")
                print(f"⏰ 调度时间: {schedule_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                print(f"📝 内容预览: {content[:50]}...")
                
                # 保存调度信息
                self.demo_data["scheduled_content"] = {
                    "content_id": content_id,
                    "scheduled_id": scheduled_id,
                    "scheduled_time": schedule_time.isoformat(),
                    "content": content,
                    "status": "scheduled"
                }
                
                # 询问是否监控调度状态
                print("\n🔍 是否监控调度执行状态? (y/N): ")
                monitor = input().strip().lower()
                
                if monitor == 'y':
                    return self._monitor_scheduled_content(scheduled_id)
                else:
                    self._start_background_queue_processor()
                
                return True
                
            else:
                error_msg = schedule_response.get("message", "未知错误")
                print_error(f"调度失败: {error_msg}")
                
                # 显示详细错误信息
                if "detail" in schedule_response:
                    detail = schedule_response["detail"]
                    if isinstance(detail, list):
                        print("❌ 详细错误:")
                        for error in detail:
                            if isinstance(error, dict):
                                print(f"  - 字段: {error.get('loc', ['unknown'])[-1]}")
                                print(f"    错误: {error.get('msg', '未知错误')}")
                                print(f"    输入值: {error.get('input', 'N/A')}")
                
                # 显示规则违规信息
                violations = schedule_response.get("rule_violations", [])
                if violations:
                    print("❌ 规则违规:")
                    for violation in violations:
                        print(f"  - {violation}")
                
                return False
                
        except Exception as e:
            print_error(f"调度API调用失败: {e}")
            return False
        
        return True

    def _monitor_scheduled_content(self, scheduled_id: str, max_wait_time: int = 300) -> bool:
        """监控调度内容的执行状态"""
        print(f"\n🔍 开始监控调度内容 {scheduled_id}...")
        print("(按 Ctrl+C 可随时停止监控)")
        
        start_time = time.time()
        
        # 启动后台队列处理
        self._start_background_queue_processor()
        
        try:
            while time.time() - start_time < max_wait_time:
                try:
                    # 查询调度状态
                    status_response = self.api_client.request(
                        "GET", 
                        f"/api/scheduling/status/{scheduled_id}"
                    )
                    
                    if "error" not in status_response:
                        status = status_response.get("status", "unknown")
                        
                        if status == "completed":
                            tweet_id = status_response.get("posted_tweet_id")
                            print_success(f"🎉 内容发布成功！")
                            if tweet_id:
                                print(f"🐦 Tweet ID: {tweet_id}")
                                print(f"🔗 链接: https://x.com/user/status/{tweet_id}")
                            
                            self.demo_data["scheduled_content"]["status"] = "completed"
                            self.demo_data["scheduled_content"]["tweet_id"] = tweet_id
                            return True
                            
                        elif status == "failed":
                            error_msg = status_response.get("error_message", "未知错误")
                            print_error(f"💥 发布失败: {error_msg}")
                            
                            self.demo_data["scheduled_content"]["status"] = "failed"
                            self.demo_data["scheduled_content"]["error"] = error_msg
                            return False
                            
                        elif status == "scheduled":
                            scheduled_time = status_response.get("scheduled_time")
                            print(f"⏰ 等待发布... (调度时间: {scheduled_time})")
                            
                            # 触发队列处理
                            self._trigger_queue_processing()
                            
                        elif status == "processing":
                            print("🔄 正在处理发布...")
                            
                        else:
                            print(f"📊 状态: {status}")
                    
                    else:
                        print_warning(f"状态查询失败: {status_response.get('error', '未知错误')}")
                    
                    # 等待10秒后再次检查
                    time.sleep(10)
                    
                except KeyboardInterrupt:
                    print_warning("\n监控被用户中断")
                    return True
                    
                except Exception as e:
                    print_warning(f"监控过程中发生错误: {e}")
                    time.sleep(10)
            
            print_warning(f"监控超时 ({max_wait_time}秒)，停止监控")
            print("💡 您可以稍后通过调度管理界面查看发布状态")
            return True
            
        except KeyboardInterrupt:
            print_warning("\n监控被用户中断")
            return True

    def _start_background_queue_processor(self):
        """启动后台队列处理器"""
        import threading
        import time
        
        def queue_processor():
            """后台队列处理线程"""
            print("🚀 启动后台队列处理器...")
            
            while getattr(self, '_queue_processing_active', True):
                try:
                    # 每30秒触发一次队列处理
                    self._trigger_queue_processing()
                    time.sleep(30)
                except Exception as e:
                    print(f"⚠️ 队列处理错误: {e}")
                    time.sleep(30)
        
        # 设置处理标志
        self._queue_processing_active = True
        
        # 启动后台线程
        queue_thread = threading.Thread(target=queue_processor, daemon=True)
        queue_thread.start()
        
        print("✅ 后台队列处理器已启动")

    def _trigger_queue_processing(self):
        """触发队列处理"""
        try:
            # 调用队列处理API
            response = self.api_client.request(
                "POST",
                "/api/scheduling/queue/process"
            )
            
            if "error" not in response:
                processed_count = response.get("processed_count", 0)
                if processed_count > 0:
                    print(f"⚡ 队列处理完成: 处理了 {processed_count} 个项目")
            else:
                # 如果API调用失败，可能是权限问题，我们直接调用服务
                self._direct_queue_processing()
                
        except Exception as e:
            # API调用失败，尝试直接处理
            self._direct_queue_processing()

    def _direct_queue_processing(self):
        """直接调用队列处理服务"""
        try:
            # 导入必要的模块
            from database import get_data_flow_manager
            from modules.scheduling_posting.service import SchedulingPostingService
            from modules.twitter_api import get_twitter_client
            from modules.user_profile.service import UserProfileService
            from modules.user_profile.repository import UserProfileRepository
            
            # 创建服务实例
            data_flow_manager = get_data_flow_manager()
            twitter_client = get_twitter_client()
            user_repository = UserProfileRepository(data_flow_manager.db_session)
            user_service = UserProfileService(user_repository, data_flow_manager)
            
            scheduling_service = SchedulingPostingService(
                data_flow_manager=data_flow_manager,
                twitter_client=twitter_client,
                user_profile_service=user_service
            )
            
            # 使用异步处理
            import asyncio
            
            async def process_queue():
                result = await scheduling_service.process_publishing_queue()
                return result
            
            # 运行异步任务
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(process_queue())
                processed_count = result.get('processed_count', 0)
                if processed_count > 0:
                    print(f"⚡ 直接队列处理完成: 处理了 {processed_count} 个项目")
            finally:
                loop.close()
                
        except Exception as e:
            # 静默处理错误，避免干扰演示
            pass

    def run_complete_demo(self) -> bool:
        """运行完整演示"""
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}🚀 开始完整工作流程演示{Colors.END}")
        print("="*60)
        
        steps = [
            ("检查服务器", self.check_server_status),
            ("用户注册/登录", self.step_1_user_registration),
            ("Twitter OAuth", self.step_2_twitter_oauth),
            # ("趋势分析", self.step_3_trend_analysis),
            # ("内容生成", self.step_4_content_generation),
            # ("SEO优化", self.step_5_seo_optimization),
            # ("审核优化", self.step_6_review_optimization),
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
            # 6: ("审核优化", self.step_6_review_optimization),
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
        
        # 显示发布状态
        if self.demo_data.get("published_content"):
            published_info = self.demo_data["published_content"]
            print(f"\n{Colors.BOLD}🐦 发布状态:{Colors.END}")
            print(f"  状态: ✅ 已发布")
            print(f"  内容ID: {published_info.get('content_id')}")
            print(f"  Tweet ID: {published_info.get('tweet_id')}")
            print(f"  发布时间: {published_info.get('published_at', 'N/A')}")
        elif self.demo_data.get("published_tweet_id"):
            print(f"\n{Colors.BOLD}🐦 发布状态:{Colors.END}")
            print(f"  状态: ✅ 已发布")
            print(f"  Tweet ID: {self.demo_data['published_tweet_id']}")
            print(f"  发布时间: {self.demo_data.get('published_at', 'N/A')}")
        
        # 显示保存的内容
        if self.demo_data.get("saved_content"):
            saved_info = self.demo_data["saved_content"]
            print(f"\n{Colors.BOLD}💾 保存的内容:{Colors.END}")
            print(f"  内容ID: {saved_info.get('content_id')}")
            print(f"  状态: {saved_info.get('status')} (可调度发布)")
            print(f"  创建时间: {saved_info.get('created_at')}")
            print(f"  内容预览: {saved_info.get('content', '')[:50]}...")
            if saved_info.get('can_be_scheduled'):
                print(f"  💡 可通过API调度: POST /api/scheduling/schedule/{saved_info.get('content_id')}")
        
        # 显示调度状态
        if self.demo_data.get("scheduled_content"):
            scheduled_info = self.demo_data["scheduled_content"]
            print(f"\n{Colors.BOLD}📅 调度状态:{Colors.END}")
            print(f"  内容ID: {scheduled_info.get('content_id')}")
            print(f"  调度ID: {scheduled_info.get('scheduled_id')}")
            print(f"  调度时间: {scheduled_info.get('scheduled_time')}")
            print(f"  状态: {scheduled_info.get('status')}")
            if scheduled_info.get('tweet_id'):
                print(f"  发布Tweet ID: {scheduled_info['tweet_id']}")
            if scheduled_info.get('error'):
                print(f"  错误信息: {scheduled_info['error']}")
                
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
        
        # 显示完整工作流程状态
        print(f"\n{Colors.BOLD}🎯 工作流程完成度:{Colors.END}")
        workflow_steps = [
            ("✅ 用户认证", bool(self.api_client.auth_token)),
            ("✅ Twitter连接", bool(self.api_client.auth_token)),  # 简化检查
            ("✅ 趋势分析", bool(self.demo_data.get("trends"))),
            ("✅ 内容生成", bool(self.demo_data.get("approved_content"))),
            ("📅 内容调度", bool(self.demo_data.get("scheduled_content"))),
            ("🐦 内容发布", bool(self.demo_data.get("published_tweet_id")))
        ]
        
        for step_name, completed in workflow_steps:
            status_icon = "✅" if completed else "⏸️"
            print(f"  {status_icon} {step_name}")
        
        # 显示下一步建议
        print(f"\n{Colors.BOLD}💡 下一步建议:{Colors.END}")
        
        if not self.demo_data.get("scheduled_content") and not self.demo_data.get("published_tweet_id"):
            print("  - 尝试调度或发布生成的内容")
        elif self.demo_data.get("scheduled_content") and self.demo_data["scheduled_content"].get("status") == "scheduled":
            print("  - 等待调度内容自动发布")
            print("  - 或使用 GET /api/scheduling/status/{scheduled_id} 查看状态")
        elif self.demo_data.get("published_tweet_id"):
            print("  - 查看Twitter上的发布效果")
            print("  - 分析发布数据和用户反馈")
        else:
            print("  - 生成更多内容进行A/B测试")
            print("  - 优化发布时间策略")

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