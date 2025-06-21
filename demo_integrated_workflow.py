"""
Demo of the integrated workflow combining Trend Analysis, Content Generation, and SEO Optimization.
"""

import sys
import os
import asyncio
import logging
import re
from dotenv import load_dotenv
from typing import List, Dict, Any

# --- Path and Environment Setup ---
# This must be at the very top before any other custom imports
load_dotenv()
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Module Imports ---
from config.llm_config import LLM_CONFIG
from config.llm_selector import llm_selector
from modules.llm.client import LLMClient
from modules.trend_analysis import create_gemini_trend_analyzer
from modules.content_generation.service import ContentGenerationService
from modules.content_generation.models import ContentGenerationRequest, ContentType
from modules.seo.llm_intelligence import LLMSEOIntelligence
from modules.seo.models import SEOOptimizationRequest, SEOAnalysisContext, SEOContentType

# --- Helper Functions ---

def select_llm_provider():
    """Interactively selects the LLM provider and returns the provider, config, and client."""
    selected_provider_name = llm_selector.interactive_select_provider()
    if not selected_provider_name:
        return None, None, None

    try:
        provider_key = selected_provider_name.lower()
        llm_config = LLM_CONFIG.get(provider_key, {})
        
        llm_config['provider'] = provider_key
        
        llm_client = LLMClient(
            provider=provider_key,
            api_key=llm_config.get('api_key'),
            model_name=llm_config.get('model_name')
        )

        print(f"🤖 Using LLM Provider: {provider_key.upper()}")
        if llm_client.is_available():
            print(f"✅ {provider_key.capitalize()} LLM client initialized successfully.")
        else:
             print(f"⚠️ {provider_key.capitalize()} LLM client initialized but API key is missing or invalid.")
        
        return provider_key, llm_config, llm_client
        
    except Exception as e:
        print(f"❌ Error initializing LLM client: {e}")
        return None, None, None

def print_header(title: str, level: int = 1):
    """Prints a formatted header."""
    if level == 1:
        print("\n" + "=" * 60)
        print(f"✅ {title}")
        print("=" * 60)
    elif level == 2:
        print(f"\n--- {title} ---")
    else:
        print(f"-> {title}")

def get_user_inputs() -> Dict[str, Any]:
    """Prompts the user for keywords, persona, and target audience."""
    inputs = {}
    print("\n--- Configure Your Demo ---")

    # Keywords
    default_keywords = "AI, SaaS, Future of Work"
    keywords_str = input(f"Enter keywords (e.g., {default_keywords}): ")
    inputs['keywords'] = [k.strip() for k in (keywords_str or default_keywords).split(',')]

    # Persona
    default_persona = "SaaS founder"
    persona_str = input(f"Describe your persona (e.g., {default_persona}): ")
    inputs['persona'] = (persona_str or default_persona).strip()

    # Target Audience
    default_audience = "enterprise clients"
    audience_str = input(f"Describe your target audience (e.g., {default_audience}): ")
    inputs['target_audience'] = (audience_str or default_audience).strip()

    # User Context
    default_context = "I am looking for new market opportunities."
    context_str = input(f"Describe your goal or background (e.g., {default_context}): ")
    inputs['user_context'] = (context_str or default_context).strip()

    print("\n✅ Configuration Complete. Starting workflow with:")
    print(f"  > Keywords: {', '.join(inputs['keywords'])}")
    print(f"  > Persona: {inputs['persona']}")
    print(f"  > Target Audience: {inputs['target_audience']}")
    print(f"  > User Context: {inputs['user_context']}")
    return inputs

class IntegratedWorkflowDemo:
    """Demonstrates the full workflow from trend analysis to SEO-optimized content."""

    def __init__(self, llm_client, llm_provider):
        if not llm_client or not llm_client.is_available():
            raise ValueError("A valid and configured LLM client is required.")
            
        self.llm_client = llm_client
        self.llm_provider = llm_provider
        
        # Correctly instantiate services based on findings from other demo scripts.
        # These services manage their own LLM clients or are configured via a provider name.
        self.trend_analyzer = create_gemini_trend_analyzer()
        
        self.content_generator = ContentGenerationService(
            data_flow_manager=None,
            user_service=None,
            llm_provider=self.llm_provider 
        )
        
        self.seo_optimizer = LLMSEOIntelligence(
            llm_provider=self.llm_provider, 
            llm_client=self.llm_client
        )

    async def run(self, keywords: List[str], persona: str, target_audience: str, user_context: str):
        """Executes the integrated workflow demo based on user-provided inputs."""
        print_header("🚀 Integrated Workflow Demo Started")

        # --- Step 1: Trend Analysis (Now a Two-Stage Process) ---
        print_header(f"Step 1: Trend Analysis for '{', '.join(keywords)}'", level=2)
        
        # Stage 1: Perform deep analysis to get foundational insights
        print("\n conducting initial deep analysis...")
        initial_analysis_result = self.trend_analyzer.analyze_trending_topics(
            keywords=keywords,
            user_context=user_context
        )

        if not initial_analysis_result.get("success") or not initial_analysis_result.get("analysis"):
            print("❌ Initial trend analysis failed. Aborting demo.")
            return

        detailed_analysis_report = initial_analysis_result["analysis"]
        print("\n✅ Initial Analysis Report (Top-level insights):")
        print("--------------------------------------------------")
        print(detailed_analysis_report)
        print("--------------------------------------------------")

        # Stage 2: Generate structured, actionable summary from the deep analysis
        print("\n generating structured summary and actionable strategies...")
        summary_result = self.trend_analyzer.get_trending_summary(
            keywords=keywords,
            user_context=user_context
        )

        if not summary_result.get("success") or not summary_result.get("structured_summary"):
            print("❌ Structured summary generation failed. Aborting demo.")
            return

        raw_trend_report = summary_result["structured_summary"]

        # The trend analyzer returned a text report, not a JSON object. We will use it directly.
        if not isinstance(raw_trend_report, str) or not raw_trend_report.strip():
            print(f"❌ Trend Analysis returned empty or invalid report. Aborting demo.")
            print(f"   Received: {raw_trend_report}")
            return

        print("\n✅ Trend Analysis Output (Full Actionable Report):")
        print("--------------------------------------------------")
        print(raw_trend_report) # Print the full report
        print("--------------------------------------------------")

        # --- Step 2: Content Generation (The "写初稿" step) ---
        print_header("Step 2: Content Generation", level=2)
        print("Using the full trend report to generate a content draft...")

        # A more robust prompt that uses the entire raw report as context.
        content_prompt = f"""
Based on the following detailed market analysis report on "{', '.join(keywords)}", please write a single, compelling tweet for a {persona} targeting {target_audience}.
The tweet should be professional, insightful, and directly inspired by the key opportunities mentioned in the report.

## Market Analysis Report
{raw_trend_report}
## End of Report

Now, generate only the text of the tweet based on the report.
"""
        # Corrected method call to the actual available method: `generate_response`
        generated_draft = await self.llm_client.generate_response(prompt=content_prompt, max_tokens=280)

        if not generated_draft:
            print("❌ Content Generation failed. Aborting demo.")
            return

        print("\n📝 Generated Content Draft:")
        print(f"  > {generated_draft}")


        # --- Step 3: SEO Optimization (The "精加工" step) ---
        print_header("Step 3: SEO Optimization", level=2)
        print("Optimizing the generated draft for SEO...")
        
        # Extract hashtags from the report to use as trend context for SEO
        trend_hashtags = re.findall(r'#(\w+)', raw_trend_report)
        print(f"  > Extracted {len(trend_hashtags)} hashtags from trend report for SEO context.")

        seo_context = SEOAnalysisContext(
            content_type=SEOContentType.TWEET,
            target_audience=target_audience,
            niche_keywords=keywords,
            brand_voice={"tone": "professional"},
            trend_context={"keywords": trend_hashtags}
        )
        seo_request = SEOOptimizationRequest(content=generated_draft, context=seo_context)
        
        # The method `enhance_content_with_llm` expects both the request and context objects.
        optimized_result = await self.seo_optimizer.enhance_content_with_llm(seo_request, seo_context)

        if not optimized_result or 'enhanced_content' not in optimized_result:
            print("❌ SEO Optimization failed. Aborting demo.")
            return

        print("\n✨ Final Optimized Content:")
        print(f"  > {optimized_result['enhanced_content']}")
        
        final_hashtags = optimized_result.get('seo_suggestions', {}).recommended_hashtags
        if final_hashtags:
            print(f"\n🏷️  Final Tactical Hashtags: {' '.join(['#' + tag for tag in final_hashtags])}")


        # --- Step 4: Final Output (The "存入数据库" step) ---
        print_header("Step 4: Simulate Saving to Database", level=2)
        print("✅ Workflow complete. The following content is ready for review.")
        print("--------------------------------------------------")
        print(f"Content: {optimized_result['enhanced_content']}")
        print(f"Status: pending_review")
        print("--------------------------------------------------")
        
        print_header("🎉 Integrated Workflow Demo Completed")


async def main():
    """Main function to run the integrated demo."""
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # --- LLM Provider Selection ---
    llm_provider, llm_config, llm_client = select_llm_provider()
    if not llm_client or not llm_client.is_available():
        print("❌ A valid LLM client could not be initialized. Demo cancelled.")
        return

    # --- Get Keywords from User ---
    user_inputs = get_user_inputs()

    # --- Run Demo ---
    try:
        demo = IntegratedWorkflowDemo(llm_client, llm_provider)
        await demo.run(
            keywords=user_inputs['keywords'],
            persona=user_inputs['persona'],
            target_audience=user_inputs['target_audience'],
            user_context=user_inputs['user_context']
        )
    except ValueError as e:
        print(f"❌ {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == '__main__':
    asyncio.run(main()) 