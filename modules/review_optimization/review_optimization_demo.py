"""Review Optimization Module - Demo

This demo showcases the key features of the review optimization module,
including content review workflows, batch operations, and analytics.

Command: python -m modules.review_optimization.review_optimization_demo
"""
import sys
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any

from modules.review_optimization.models import (
    ContentDraftReview, ReviewDecision, ReviewDecisionRequest, BatchReviewRequest, BatchReviewDecision,
    ContentRegenerationRequest, DraftStatus, ContentPriority
)
from modules.review_optimization.database_adapter import ReviewOptimizationSQLiteSyncAdapter
from modules.content_generation.models import ContentDraft

MENU = """
==== Review Optimization Demo ====
1. 创建草稿
2. 查看待审核草稿
3. 审核草稿
4. 批量审核
5. 内容再生成
6. 查看审核统计
7. 退出
"""

def print_section(title: str):
    print(f"\n{'=' * 50}\n{title}\n{'=' * 50}")

def input_with_default(prompt, default):
    val = input(f"{prompt} (默认: {default}): ").strip()
    return val if val else default

def ensure_table():
    with sqlite3.connect("ideation_db.sqlite") as conn:
        conn.execute("DROP TABLE IF EXISTS generated_content_drafts;")
        conn.execute("""
CREATE TABLE generated_content_drafts (
    id TEXT PRIMARY KEY,
    founder_id TEXT,
    content_type TEXT,
    generated_text TEXT,
    current_content TEXT,
    status TEXT,
    priority TEXT,
    tags TEXT,
    analyzed_trend_id TEXT,
    ai_generation_metadata TEXT,
    seo_suggestions TEXT,
    quality_score REAL,
    edit_history TEXT,
    review_feedback TEXT,
    reviewed_at TEXT,
    reviewer_id TEXT,
    review_decision TEXT,
    scheduled_post_time TEXT,
    posted_at TEXT,
    posted_tweet_id TEXT,
    created_at TEXT,
    updated_at TEXT
);
""")

ensure_table()

def main():
    print("🎉 欢迎使用 Review Optimization Module 终端演示！（同步版）")
    db_adapter = ReviewOptimizationSQLiteSyncAdapter()
    founder_id = "demo_founder"

    # 自动生成测试草稿
    print_section("自动生成测试草稿")
    demo_contents = [
        ("AI创业5大趋势洞察", "trend_analysis"),
        ("产品增长实战经验分享", "experience_sharing"),
        ("2024年AI投资市场报告", "news_commentary")
    ]
    for content, ctype in demo_contents:
        draft = ContentDraftReview(
            founder_id=founder_id,
            content_type=ctype,
            original_content=content,
            current_content=content
        )
        db_adapter.create_draft(draft)
        print(f"✅ 已生成草稿: {content} [{ctype}]")

    while True:
        print(MENU)
        choice = input("请选择操作: ").strip()
        if choice == "1":
            print_section("创建草稿")
            content = input_with_default("请输入内容", "新内容草稿")
            ctype = input_with_default("内容类型(trend_analysis/experience_sharing/news_commentary)", "trend_analysis")
            draft = ContentDraftReview(
                founder_id=founder_id,
                content_type=ctype,
                original_content=content,
                current_content=content
            )
            db_adapter.create_draft(draft)
            print("✅ 草稿创建成功！")
        elif choice == "2":
            print_section("待审核草稿列表")
            drafts = db_adapter.get_pending_content_drafts(founder_id, limit=10)
            if not drafts:
                print("暂无待审核草稿。")
            for d in drafts:
                print(f"ID: {d.id} | 类型: {d.content_type} | 状态: {getattr(d, 'status', '')} | 内容: {getattr(d, 'current_content', '')[:30]}")
        elif choice == "3":
            print_section("审核草稿")
            drafts = db_adapter.get_pending_content_drafts(founder_id, limit=10)
            if not drafts:
                print("暂无待审核草稿。")
                continue
            for idx, d in enumerate(drafts):
                print(f"{idx+1}. ID: {d.id} | 内容: {getattr(d, 'current_content', '')[:30]}")
            idx = int(input_with_default("选择要审核的草稿编号", "1")) - 1
            draft = drafts[idx]
            print(f"草稿内容: {getattr(draft, 'current_content', '')}")
            print("审核决策: 1-通过 2-编辑并通过 3-拒绝")
            dec = input_with_default("选择决策", "1")
            update_data = {}
            if dec == "1":
                update_data = {
                    "status": DraftStatus.APPROVED.value,
                    "review_decision": ReviewDecision.APPROVE.value,
                    "updated_at": datetime.utcnow().isoformat()
                }
                print("✅ 审核通过！")
            elif dec == "2":
                new_content = input_with_default("请输入编辑后内容", getattr(draft, 'current_content', ''))
                update_data = {
                    "status": DraftStatus.APPROVED.value,
                    "review_decision": ReviewDecision.EDIT_AND_APPROVE.value,
                    "current_content": new_content,
                    "updated_at": datetime.utcnow().isoformat()
                }
                print("✅ 编辑并通过！")
            else:
                update_data = {
                    "status": DraftStatus.REJECTED.value,
                    "review_decision": ReviewDecision.REJECT.value,
                    "updated_at": datetime.utcnow().isoformat()
                }
                print("✅ 已拒绝！")
            db_adapter.update_content_draft(draft.id, update_data)
        elif choice == "4":
            print_section("批量审核")
            drafts = db_adapter.get_pending_content_drafts(founder_id, limit=5)
            if not drafts:
                print("暂无待审核草稿。")
                continue
            for d in drafts:
                print(f"ID: {d.id} | 内容: {getattr(d, 'current_content', '')[:30]}")
                dec = input_with_default(f"草稿[{d.id}]决策(1-通过 2-编辑并通过 3-拒绝)", "1")
                update_data = {}
                if dec == "1":
                    update_data = {
                        "status": DraftStatus.APPROVED.value,
                        "review_decision": ReviewDecision.APPROVE.value,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    print(f"✅ {d.id} 审核通过！")
                elif dec == "2":
                    new_content = input_with_default("请输入编辑后内容", getattr(d, 'current_content', ''))
                    update_data = {
                        "status": DraftStatus.APPROVED.value,
                        "review_decision": ReviewDecision.EDIT_AND_APPROVE.value,
                        "current_content": new_content,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    print(f"✅ {d.id} 编辑并通过！")
                else:
                    update_data = {
                        "status": DraftStatus.REJECTED.value,
                        "review_decision": ReviewDecision.REJECT.value,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    print(f"✅ {d.id} 已拒绝！")
                db_adapter.update_content_draft(d.id, update_data)
        elif choice == "5":
            print_section("内容再生成")
            from modules.content_generation.service import ContentGenerationService
            from modules.content_generation.models import ContentType, GenerationMode, ContentGenerationRequest, ContentGenerationContext, BrandVoice
            from config.llm_config import DEFAULT_LLM_PROVIDER

            if not hasattr(main, "_content_service"):
                main._content_service = ContentGenerationService(
                    data_flow_manager=None, user_service=None, llm_provider=DEFAULT_LLM_PROVIDER
                )
            content_service = main._content_service

            drafts = db_adapter.get_pending_content_drafts(founder_id, limit=5)
            if not drafts:
                print("暂无可再生成草稿。")
                continue
            for idx, d in enumerate(drafts):
                print(f"{idx+1}. ID: {d.id} | 内容: {getattr(d, 'current_content', '')[:30]}")
            idx = int(input_with_default("选择要再生成的草稿编号", "1")) - 1
            draft = drafts[idx]
            # 构造再生成专用prompt
            from modules.content_generation.prompts import PromptEngine
            original_content = getattr(draft, 'current_content', '')
            feedback = input_with_default("请输入再生需求/反馈", "需要更多数据支持")
            custom_instruction = (
                "你是资深内容优化专家。请根据以下原始草稿和用户反馈，对草稿进行优化和重写，确保内容更有深度、更具吸引力，并满足反馈要求。\n\n"
                f"【原始草稿】：\n{original_content}\n\n"
                f"【用户反馈/优化要求】：\n{feedback}\n\n"
                "请输出优化后的完整内容，保持原有主题，但提升表达质量和专业性。"
            )

            import asyncio

            async def regenerate_content_custom():
                req = ContentGenerationRequest(
                    founder_id=founder_id,
                    content_type=ContentType.TWEET,
                    generation_mode=GenerationMode.STANDARD,
                    quantity=1,
                    custom_prompt=custom_instruction
                )
                context = ContentGenerationContext(
                    trend_info=None,
                    product_info={},
                    brand_voice=BrandVoice(),
                    recent_content=[],
                    successful_patterns=[],
                    target_audience=None,
                    content_preferences={}
                )
                prompt_engine = PromptEngine()
                # 用自定义prompt生成最终prompt
                custom_prompt = prompt_engine.create_custom_prompt(custom_instruction, context)
                try:
                    # 直接用llm_adapter生成内容
                    raw_content = await content_service.generator.llm_adapter.generate_content(custom_prompt)
                    # 清洗内容
                    cleaned_content = content_service.generator._clean_generated_content(raw_content, ContentType.TWEET)
                    # 质量评估
                    if content_service.generator.quality_checker:
                        temp_draft = ContentDraft(
                            founder_id=founder_id,
                            content_type=ContentType.TWEET,
                            generated_text=cleaned_content,
                            quality_score=0.0
                        )
                        quality_assessment = await content_service.generator.quality_checker.assess_quality(temp_draft, context)
                        quality_score = quality_assessment.overall_score
                    else:
                        quality_score = 0.7
                    if quality_score < 0.6:
                        print(f"⚠️ 质量分过低: {quality_score:.2f}")
                        # return None # 如果不想返回低质量内容，取消这里的注释
                    return cleaned_content
                except Exception as e:
                    print(f"❌ 大模型调用失败: {e}")
                return None

            try:
                new_content = asyncio.run(regenerate_content_custom())
            except Exception as e:
                print(f"❌ 大模型调用失败: {e}")
                new_content = None

            if new_content:
                print("\n📄 大模型生成的新内容：\n" + "="*40)
                print(new_content)
                print("="*40)
                confirm = input_with_default("是否用该内容覆盖草稿？(y/n)", "y")
                if confirm.lower() == "y":
                    update_data = {
                        "current_content": new_content,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    db_adapter.update_content_draft(draft.id, update_data)
                    print("✅ 草稿已更新为大模型生成的新内容！")
                else:
                    print("未更新草稿。")
            else:
                print("❌ 再生成失败")
        elif choice == "6":
            print_section("审核统计")
            with sqlite3.connect("ideation_db.sqlite") as conn:
                cursor = conn.execute("SELECT status, COUNT(*) FROM generated_content_drafts GROUP BY status")
                status_counts = {row[0]: row[1] for row in cursor.fetchall()}
                total = sum(status_counts.values())
                print(f"总草稿数: {total}")
                for status in [
                    DraftStatus.PENDING_REVIEW.value,
                    DraftStatus.APPROVED.value,
                    DraftStatus.REJECTED.value,
                    DraftStatus.EDITING.value,
                    DraftStatus.SCHEDULED.value,
                    DraftStatus.POSTED.value
                ]:
                    print(f"{status}: {status_counts.get(status, 0)}")
                # 已编辑数
                cursor = conn.execute("SELECT COUNT(*) FROM generated_content_drafts WHERE review_decision = ?", (ReviewDecision.EDIT_AND_APPROVE.value,))
                edited_count = cursor.fetchone()[0]
                print(f"已编辑数: {edited_count}")
                # 平均质量分
                cursor = conn.execute("SELECT AVG(quality_score) FROM generated_content_drafts WHERE quality_score IS NOT NULL")
                avg_score = cursor.fetchone()[0]
                print(f"平均质量分: {avg_score:.2f}" if avg_score is not None else "平均质量分: 无")
        elif choice == "7":
            print("退出 demo。再见！")
            break
        else:
            print("无效选择，请重试。")

if __name__ == "__main__":
    main() 