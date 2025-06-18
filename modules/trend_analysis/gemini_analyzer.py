"""
Gemini LLM Integration for Trending Topics Analysis

This module implements the two-stage process:
1. Inference and Delegation: Send keywords to Gemini with tools
2. Execution and Synthesis: Execute search and get final answer
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
import google.generativeai as genai
from .web_search_tool import get_trending_topics

logger = logging.getLogger(__name__)


class GeminiTrendAnalyzer:
    """
    Trend analyzer based on Google Gemini
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini trend analyzer
        
        Args:
            api_key: Google Gemini API key, if not provided will get from environment variable
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("Missing Gemini API key, please set GEMINI_API_KEY environment variable")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Set up model and provide tools
        self.model = genai.GenerativeModel(
            model_name=os.getenv('GEMINI_MODEL_NAME'),
            tools=[get_trending_topics]  # Provide search tool to the model
        )
    
    def analyze_trending_topics(
        self, 
        keywords: List[str], 
        user_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze trending topics based on keywords
        
        Args:
            keywords: List of keywords provided by user
            user_context: Optional user context information
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Stage 1: Inference and Delegation
            logger.info(f"Starting analysis for keywords: {keywords}")
            
            # Build prompt
            keywords_str = ", ".join(keywords)
            context_str = f"\nUser background: {user_context}" if user_context else ""
            
            prompt = f"""
Based on the following keywords: '{keywords_str}', please help me find the top 5 most trending related topics on the internet right now.{context_str}

Please note:
1. I need the most current and hottest topics
2. Topics should be closely related to the provided keywords
3. Please prioritize searching for English content
4. The returned topics should be valuable for entrepreneurs and product developers

Please use the available tools to search for the latest trending topics.
"""
            
            logger.info(f"Sending prompt to Gemini: {prompt[:100]}...")
            
            # First API call: Send prompt to model
            response = self.model.generate_content(prompt)
            first_response_part = response.candidates[0].content.parts[0]
            
            # Check if model decided to call function
            if first_response_part.function_call:
                logger.info("Model decided to call search tool")
                function_call = first_response_part.function_call
                
                # Extract function name and parameters
                function_name = function_call.name
                function_args = function_call.args
                
                logger.info(f"Calling function: {function_name}, parameters: {function_args}")
                
                # Stage 2: Execution and Synthesis
                if function_name == 'get_trending_topics':
                    # Execute search tool
                    tool_results = get_trending_topics(**function_args)
                    logger.info("Search tool execution completed")
                else:
                    # Handle unknown function call
                    tool_results = "Error: Model called unknown function"
                    logger.error(f"Unknown function call: {function_name}")
                
                # Second API call: Send tool results back to model
                logger.info("Sending search results back to Gemini for final analysis...")
                
                # Build new conversation history
                chat = self.model.start_chat()
                
                # Send original message
                chat_response = chat.send_message(prompt)
                
                # If model requests function call, we manually execute and send results
                if chat_response.candidates[0].content.parts[0].function_call:
                    # Send function execution results
                    function_response = {
                        "function_response": {
                            "name": function_name,
                            "response": {"result": tool_results}
                        }
                    }
                    
                    response_with_results = chat.send_message(function_response)
                
                # Get final answer
                try:
                    final_answer = response_with_results.text
                except:
                    # If unable to get text directly, extract from parts
                    final_answer = ""
                    for part in response_with_results.candidates[0].content.parts:
                        if hasattr(part, 'text'):
                            final_answer += part.text
                logger.info("Gemini analysis completed")
                
                return {
                    "success": True,
                    "keywords": keywords,
                    "analysis": final_answer,
                    "search_results": tool_results,
                    "function_called": function_name,
                    "search_query": function_args.get("search_query", ""),
                    "timestamp": self._get_current_timestamp()
                }
                
            else:
                # Model responded directly without calling tools
                logger.info("Model responded directly without calling search tool")
                try:
                    analysis_text = response.text
                except:
                    analysis_text = ""
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'text'):
                            analysis_text += part.text
                
                return {
                    "success": True,
                    "keywords": keywords,
                    "analysis": analysis_text,
                    "search_results": None,
                    "function_called": None,
                    "search_query": "",
                    "timestamp": self._get_current_timestamp()
                }
                
        except Exception as e:
            logger.error(f"Error occurred during analysis: {e}")
            return {
                "success": False,
                "keywords": keywords,
                "error": str(e),
                "analysis": None,
                "search_results": None,
                "function_called": None,
                "search_query": "",
                "timestamp": self._get_current_timestamp()
            }
    
    def batch_analyze_keywords(
        self, 
        keyword_groups: List[List[str]], 
        user_context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Batch analyze multiple keyword groups
        
        Args:
            keyword_groups: List of keyword groups
            user_context: User context information
            
        Returns:
            List of analysis results
        """
        results = []
        
        for i, keywords in enumerate(keyword_groups):
            logger.info(f"Analyzing group {i+1}/{len(keyword_groups)}: {keywords}")
            
            result = self.analyze_trending_topics(keywords, user_context)
            results.append(result)
            
            # Add delay to avoid API limits
            import time
            time.sleep(1)
        
        return results
    
    def get_trending_summary(
        self, 
        keywords: List[str], 
        max_topics: int = 5,
        user_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get trending topics summary
        
        Args:
            keywords: List of keywords
            max_topics: Maximum number of topics
            user_context: User context
            
        Returns:
            Summary results
        """
        analysis_result = self.analyze_trending_topics(keywords, user_context)
        
        if not analysis_result["success"]:
            return analysis_result
        
        # Parse analysis results to extract specific topics
        analysis_text = analysis_result["analysis"]
        
        try:
            # Use Gemini to further process analysis results and extract structured information
            summary_prompt = f"""
Please extract the top {max_topics} most important trending topics from the following analysis results, and provide for each topic:
1. Topic title
2. Brief description
3. Relevance score (1-10)
4. Why this topic is important

Analysis results:
{analysis_text}

Please return in JSON format as follows:
{{
    "topics": [
        {{
            "title": "Topic title",
            "description": "Brief description",
            "relevance_score": score,
            "importance": "Importance explanation"
        }}
    ]
}}
"""
            
            summary_response = self.model.generate_content(summary_prompt)
            
            # Safely get summary text
            try:
                summary_text = summary_response.text
            except:
                summary_text = ""
                for part in summary_response.candidates[0].content.parts:
                    if hasattr(part, 'text'):
                        summary_text += part.text
            
            return {
                "success": True,
                "keywords": keywords,
                "raw_analysis": analysis_text,
                "structured_summary": summary_text,
                "search_results": analysis_result.get("search_results"),
                "timestamp": self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error occurred while generating summary: {e}")
            return {
                "success": True,  # Original analysis succeeded
                "keywords": keywords,
                "raw_analysis": analysis_text,
                "structured_summary": None,
                "summary_error": str(e),
                "search_results": analysis_result.get("search_results"),
                "timestamp": self._get_current_timestamp()
            }
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


def create_gemini_trend_analyzer(api_key: Optional[str] = None) -> GeminiTrendAnalyzer:
    """
    Factory function to create Gemini trend analyzer instance
    
    Args:
        api_key: Optional API key
        
    Returns:
        GeminiTrendAnalyzer instance
    """
    return GeminiTrendAnalyzer(api_key)


# Convenience function for quick analysis
def quick_analyze_trending_topics(
    keywords: List[str], 
    user_context: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function for quick trending topics analysis
    
    Args:
        keywords: List of keywords
        user_context: User context
        api_key: API key
        
    Returns:
        Analysis results
    """
    analyzer = create_gemini_trend_analyzer(api_key)
    return analyzer.analyze_trending_topics(keywords, user_context) 