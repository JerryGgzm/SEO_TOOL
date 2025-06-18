"""
Web Search Tool for Trending Topics

This module provides the Google Custom Search API integration
for finding latest trending topics based on keywords.
"""

import os
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
import logging
from datetime import datetime, timedelta
logger = logging.getLogger(__name__)


def get_trending_topics(search_query: str) -> str:
    """
    Use Google Custom Search API to search for the latest 5 trending articles for given query
    
    Args:
        search_query: Search query provided by LLM
        
    Returns:
        Formatted string of top 5 search results
    """
    logger.info(f"--- Executing tool: Search web content about '{search_query}' ---")
    logger.debug(f"DEBUG: Input search_query type: {type(search_query)}, value: '{search_query}'")
    
    # Get API key and search engine ID from environment variables
    SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
    SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
    
    logger.debug(f"DEBUG: API Key present: {bool(SEARCH_API_KEY)}")
    logger.debug(f"DEBUG: Search Engine ID present: {bool(SEARCH_ENGINE_ID)}")
    if SEARCH_API_KEY:
        logger.debug(f"DEBUG: API Key length: {len(SEARCH_API_KEY)}")
    if SEARCH_ENGINE_ID:
        logger.debug(f"DEBUG: Search Engine ID: {SEARCH_ENGINE_ID}")
    
    if not SEARCH_API_KEY or not SEARCH_ENGINE_ID:
        error_msg = "Error: Missing Google Search API key or search engine ID configuration"
        logger.error(f"DEBUG: {error_msg}")
        return error_msg
    
    try:
        logger.debug("DEBUG: Building Custom Search API service object...")
        # Build Custom Search API service object
        service = build("customsearch", "v1", developerKey=SEARCH_API_KEY)
        logger.debug("DEBUG: Service object created successfully")
        
        
        # Construct the final search query
        final_query = f"Newest Trending Topics about {search_query}"
        logger.debug(f"DEBUG: Final search query: '{final_query}'")
        
        # Log all search parameters
        search_params = {
            'q': final_query,
            'cx': SEARCH_ENGINE_ID,
            'num': 5,
            'gl': "us",
            'lr': "lang_en",
            'dateRestrict': 5
        }
        logger.debug(f"DEBUG: Search parameters: {search_params}")
        
        logger.debug("DEBUG: Executing search request...")
        # Execute search request
        result = service.cse().list(**search_params).execute()
        logger.debug("DEBUG: Search request completed successfully")
        logger.debug(f"DEBUG: Raw result keys: {list(result.keys()) if result else 'None'}")
        
        # Format results into clear string for model use
        logger.debug(f"DEBUG: Checking for 'items' in result...")
        if 'items' not in result:
            logger.debug("DEBUG: No 'items' found in result")
            logger.debug(f"DEBUG: Available result keys: {list(result.keys())}")
            if 'searchInformation' in result:
                logger.debug(f"DEBUG: Search info: {result['searchInformation']}")
            no_results_msg = "No relevant articles found."
            logger.debug(f"DEBUG: Returning: {no_results_msg}")
            return no_results_msg
        
        items = result.get('items', [])
        logger.debug(f"DEBUG: Found {len(items)} items in search results")
        
        formatted_results = []
        for i, item in enumerate(items):
            logger.debug(f"DEBUG: Processing item {i+1}/{len(items)}")
            logger.debug(f"DEBUG: Item keys: {list(item.keys())}")
            
            title = item.get('title', 'No title')
            link = item.get('link', 'No link')
            snippet = item.get('snippet', 'No summary')
            
            logger.debug(f"DEBUG: Item {i+1} - Title: {title[:50]}...")
            logger.debug(f"DEBUG: Item {i+1} - Link: {link}")
            logger.debug(f"DEBUG: Item {i+1} - Snippet length: {len(snippet)}")
            
            # Clean summary text
            snippet = snippet.replace('\n', ' ').strip()
            if len(snippet) > 200:
                snippet = snippet[:200] + "..."
            
            formatted_item = f"{i+1}. Title: {title}\n   Link: {link}\n   Summary: {snippet}\n"
            formatted_results.append(formatted_item)
            logger.debug(f"DEBUG: Formatted item {i+1} length: {len(formatted_item)}")
        
        final_result = "\n".join(formatted_results)
        logger.debug(f"DEBUG: Final formatted result length: {len(final_result)}")
        logger.debug(f"DEBUG: Final result preview: {final_result[:200]}...")
        
        return final_result

    except Exception as e:
        error_msg = f"Error occurred during search: {str(e)}"
        logger.error(f"DEBUG: Exception caught: {type(e).__name__}: {str(e)}")
        logger.error(f"DEBUG: Exception details:", exc_info=True)
        logger.error(f"DEBUG: Returning error: {error_msg}")
        return error_msg


class WebSearchTrendAnalyzer:
    """
    Web search trend analyzer using Google Custom Search API
    """
    
    def __init__(self):
        logger.debug("DEBUG: Initializing WebSearchTrendAnalyzer...")
        self.search_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        
        logger.debug(f"DEBUG: API Key present: {bool(self.search_api_key)}")
        logger.debug(f"DEBUG: Search Engine ID present: {bool(self.search_engine_id)}")
        
        if not self.search_api_key or not self.search_engine_id:
            error_msg = "Missing required Google Search API configuration"
            logger.error(f"DEBUG: {error_msg}")
            raise ValueError(error_msg)
        
        logger.debug("DEBUG: WebSearchTrendAnalyzer initialized successfully")
    
    def search_trending_topics_by_keywords(
        self, 
        keywords: List[str], 
        max_results_per_keyword: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search trending topics based on keyword list
        
        Args:
            keywords: List of keywords
            max_results_per_keyword: Maximum number of results per keyword
            
        Returns:
            Dictionary of search results grouped by keyword
        """
        logger.debug(f"DEBUG: Starting batch search for {len(keywords)} keywords: {keywords}")
        logger.debug(f"DEBUG: Max results per keyword: {max_results_per_keyword}")
        results = {}
        
        try:
            logger.debug("DEBUG: Building service for batch search...")
            service = build("customsearch", "v1", developerKey=self.search_api_key)
            logger.debug("DEBUG: Service built successfully for batch search")
            
            for i, keyword in enumerate(keywords):
                logger.info(f"Searching keyword {i+1}/{len(keywords)}: {keyword}")
                logger.debug(f"DEBUG: Processing keyword: '{keyword}'")
                
                # Construct search query
                search_query = f"latest trending hot topics {keyword}"
                logger.debug(f"DEBUG: Search query for '{keyword}': '{search_query}'")
                
                # Execute search for each keyword
                search_params = {
                    'q': search_query,
                    'cx': self.search_engine_id,
                    'num': max_results_per_keyword,
                    'gl': "us",
                    'lr': "lang_en"
                }
                logger.debug(f"DEBUG: Keyword '{keyword}' search params: {search_params}")
                
                search_result = service.cse().list(**search_params).execute()
                logger.debug(f"DEBUG: Search completed for keyword '{keyword}'")
                logger.debug(f"DEBUG: Result keys for '{keyword}': {list(search_result.keys())}")
                
                # Format results
                keyword_results = []
                if 'items' in search_result:
                    items = search_result['items']
                    logger.debug(f"DEBUG: Found {len(items)} items for keyword '{keyword}'")
                    
                    for j, item in enumerate(items):
                        logger.debug(f"DEBUG: Processing item {j+1}/{len(items)} for keyword '{keyword}'")
                        result_item = {
                            'title': item.get('title', ''),
                            'link': item.get('link', ''),
                            'snippet': item.get('snippet', '').replace('\n', ' ').strip(),
                            'published_date': item.get('pagemap', {}).get('metatags', [{}])[0].get('article:published_time', ''),
                            'keyword': keyword
                        }
                        keyword_results.append(result_item)
                        logger.debug(f"DEBUG: Item {j+1} for '{keyword}' - Title: {result_item['title'][:50]}...")
                else:
                    logger.debug(f"DEBUG: No items found for keyword '{keyword}'")
                    if 'searchInformation' in search_result:
                        logger.debug(f"DEBUG: Search info for '{keyword}': {search_result['searchInformation']}")
                
                results[keyword] = keyword_results
                logger.debug(f"DEBUG: Stored {len(keyword_results)} results for keyword '{keyword}'")
                
        except Exception as e:
            error_msg = f"Error occurred during batch search: {e}"
            logger.error(f"DEBUG: Exception in batch search: {type(e).__name__}: {str(e)}")
            logger.error(f"DEBUG: Exception details:", exc_info=True)
            logger.error(error_msg)
            
        logger.debug(f"DEBUG: Batch search completed. Total keywords processed: {len(results)}")
        return results
    
    def get_top_trending_topics(
        self, 
        keywords: List[str], 
        total_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get top N trending topics for all keywords
        
        Args:
            keywords: List of keywords
            total_results: Total number of results to return
            
        Returns:
            Sorted list of top N trending topics
        """
        logger.debug(f"DEBUG: Getting top {total_results} trending topics for keywords: {keywords}")
        
        all_results = self.search_trending_topics_by_keywords(
            keywords, 
            max_results_per_keyword=2
        )
        logger.debug(f"DEBUG: Batch search returned results for {len(all_results)} keywords")
        
        # Combine all results
        combined_results = []
        for keyword, results in all_results.items():
            logger.debug(f"DEBUG: Keyword '{keyword}' has {len(results)} results")
            combined_results.extend(results)
        
        logger.debug(f"DEBUG: Combined total results: {len(combined_results)}")
        
        # Simple sorting (more complex sorting logic can be implemented here)
        # Currently sort by keyword relevance and time
        logger.debug("DEBUG: Sorting combined results...")
        sorted_results = sorted(
            combined_results, 
            key=lambda x: (len(x['title']), x['title']), 
            reverse=True
        )
        logger.debug(f"DEBUG: Sorted results count: {len(sorted_results)}")
        
        final_results = sorted_results[:total_results]
        logger.debug(f"DEBUG: Returning top {len(final_results)} results")
        
        return final_results 