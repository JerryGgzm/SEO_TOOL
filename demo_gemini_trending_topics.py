#!/usr/bin/env python3
"""
Gemini热门话题分析演示脚本

此脚本演示了新的基于Google Gemini的热门话题分析功能：
1. 基于用户关键词搜索网络热门话题
2. 使用Gemini LLM进行智能分析
3. 两阶段处理：推理+执行

使用方法：
python demo_gemini_trending_topics.py

前提条件：
- 设置GEMINI_API_KEY环境变量
- 设置GOOGLE_SEARCH_API_KEY环境变量  
- 设置GOOGLE_SEARCH_ENGINE_ID环境变量
"""

import os
import sys
import asyncio
from typing import List
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('.env')

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_environment():
    """检查必需的环境变量"""
    required_vars = [
        'GEMINI_API_KEY',
        'GOOGLE_SEARCH_API_KEY',
        'GOOGLE_SEARCH_ENGINE_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ 缺少必需的环境变量:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n请设置这些环境变量后再运行演示。")
        print("\n获取API密钥的方法:")
        print("- GEMINI_API_KEY: 访问 https://makersuite.google.com/app/apikey")
        print("- GOOGLE_SEARCH_API_KEY: 在Google Cloud Console中创建")
        print("- GOOGLE_SEARCH_ENGINE_ID: 在Programmable Search Engine中创建")
        return False
    
    print("✅ 所有必需的环境变量都已设置")
    return True


def demo_basic_analysis():
    """演示基本的关键词分析功能"""
    print("\n" + "="*60)
    print("🚀 演示1: 基本关键词分析")
    print("="*60)
    
    try:
        from modules.trend_analysis import quick_analyze_trending_topics
        
        # 演示关键词
        demo_keywords = ["人工智能", "创业"]
        demo_context = "我是一名技术创业者，想了解AI领域的最新趋势"
        
        print(f"关键词: {demo_keywords}")
        print(f"用户背景: {demo_context}")
        print("\n🔍 正在分析中...")
        
        # 执行分析
        result = quick_analyze_trending_topics(
            keywords=demo_keywords,
            user_context=demo_context
        )
        
        if result["success"]:
            print("\n✅ 分析完成!")
            print(f"搜索查询: {result.get('search_query', 'N/A')}")
            print(f"调用的函数: {result.get('function_called', 'N/A')}")
            print(f"时间戳: {result['timestamp']}")
            print("\n📝 分析结果:")
            print(result["analysis"])
            
            if result.get("search_results"):
                print("\n🔍 原始搜索结果 (前100字符):")
                print(result["search_results"][:100] + "...")
        else:
            print(f"❌ 分析失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")


def demo_advanced_analysis():
    """演示高级分析功能"""
    print("\n" + "="*60)
    print("🔬 演示2: 高级分析功能")
    print("="*60)
    
    try:
        from modules.trend_analysis import create_gemini_trend_analyzer
        
        # 创建分析器
        analyzer = create_gemini_trend_analyzer()
        
        # 更复杂的关键词组合
        demo_keywords = ["效率工具", "远程办公", "SaaS"]
        demo_context = "产品经理，想要发现新的效率工具市场机会"
        
        print(f"关键词: {demo_keywords}")
        print(f"用户背景: {demo_context}")
        print("\n🔍 正在进行高级分析...")
        
        # 执行详细分析
        analysis_result = analyzer.analyze_trending_topics(
            keywords=demo_keywords,
            user_context=demo_context
        )
        
        if analysis_result["success"]:
            print("\n✅ 高级分析完成!")
            print("\n📊 详细分析结果:")
            print(analysis_result["analysis"])
            
            # 获取结构化总结
            print("\n🎯 正在生成结构化总结...")
            summary_result = analyzer.get_trending_summary(
                keywords=demo_keywords,
                max_topics=3,
                user_context=demo_context
            )
            
            if summary_result["success"]:
                print("\n📋 结构化总结:")
                if summary_result.get("structured_summary"):
                    print(summary_result["structured_summary"])
                else:
                    print("结构化总结生成失败，显示原始分析:")
                    print(summary_result["raw_analysis"][:300] + "...")
                    
        else:
            print(f"❌ 高级分析失败: {analysis_result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 高级演示过程中发生错误: {e}")


def demo_batch_analysis():
    """演示批量关键词分析"""
    print("\n" + "="*60)
    print("📦 演示3: 批量关键词分析")
    print("="*60)
    
    try:
        from modules.trend_analysis import create_gemini_trend_analyzer
        
        analyzer = create_gemini_trend_analyzer()
        
        # 多组关键词
        keyword_groups = [
            ["AI", "Startup", "AI Agent"],
            ["Efficiency Tool", "Remote Work", "SaaS"]
        ]
        
        demo_context = "Startup founder, looking for the latest trends in the market"
        
        print(f"关键词组: {keyword_groups}")
        print(f"用户背景: {demo_context}")
        print("\n🔍 正在进行批量分析...")
        
        # 执行批量分析
        batch_results = analyzer.batch_analyze_keywords(
            keyword_groups=keyword_groups,
            user_context=demo_context
        )
        
        print(f"\n✅ 批量分析完成! 共分析了 {len(batch_results)} 组关键词")
        
        for i, result in enumerate(batch_results):
            print(f"\n--- 第 {i+1} 组结果 ---")
            print(f"关键词: {result['keywords']}")
            if result["success"]:
                print("状态: ✅ 成功")
                print(f"分析摘要: {result['analysis'][:150]}...")
            else:
                print("状态: ❌ 失败")
                print(f"错误: {result.get('error', '未知错误')}")
                
    except Exception as e:
        print(f"❌ 批量分析演示过程中发生错误: {e}")


def demo_web_search_tool():
    """演示直接使用网络搜索工具"""
    print("\n" + "="*60)
    print("🌐 演示4: 直接网络搜索")
    print("="*60)
    
    try:
        from modules.trend_analysis.web_search_tool import get_trending_topics, WebSearchTrendAnalyzer
        
        # 演示直接搜索
        search_query = "最新AI工具 2024"
        print(f"搜索查询: {search_query}")
        print("\n🔍 正在搜索...")
        
        search_results = get_trending_topics(search_query)
        print("\n📄 搜索结果:")
        print(search_results)
        
        # 演示高级搜索器
        print("\n🔧 使用高级搜索分析器...")
        analyzer = WebSearchTrendAnalyzer()
        
        keywords = ["ChatGPT", "Midjourney", "Claude"]
        top_topics = analyzer.get_top_trending_topics(keywords, total_results=3)
        
        print(f"\n🏆 基于关键词 {keywords} 的前3个热门话题:")
        for i, topic in enumerate(top_topics, 1):
            print(f"\n{i}. {topic['title']}")
            print(f"   关键词: {topic['keyword']}")
            print(f"   摘要: {topic['snippet'][:100]}...")
            
    except Exception as e:
        print(f"❌ 网络搜索演示过程中发生错误: {e}")


def main():
    """主函数"""
    print("🎉 欢迎使用Gemini热门话题分析演示!")
    print("此演示展示了如何使用关键词获取网络热门话题")
    
    # 检查环境变量
    if not check_environment():
        return
    
    # 运行所有演示
    demo_basic_analysis()
    demo_advanced_analysis()
    demo_batch_analysis()
    demo_web_search_tool()
    
    print("\n" + "="*60)
    print("🎊 演示完成!")
    print("="*60)
    print("\n📚 下一步:")
    print("1. 在您的应用中调用 /api/trends/gemini/analyze API端点")
    print("2. 传入您的关键词，如 ['AI', '效率', '创业']")
    print("3. 获取个性化的热门话题分析结果")
    print("\n💡 API端点:")
    print("- POST /api/trends/gemini/analyze - 基本分析")
    print("- POST /api/trends/gemini/summary - 结构化总结")
    print("- GET /api/trends/gemini/quick-demo - 快速演示")
    print("- GET /api/trends/gemini/config-check - 配置检查")


if __name__ == "__main__":
    main() 