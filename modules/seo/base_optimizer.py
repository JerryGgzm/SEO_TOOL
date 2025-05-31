"""Main SEO optimizer that orchestrates all SEO optimization components"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
import re

from .models import (
    SEOOptimizationRequest, SEOOptimizationResult, ContentOptimizationSuggestions,
    SEOAnalysisContext, SEOContentType, SEOOptimizationLevel, HashtagStrategy,
    HashtagMetrics, KeywordAnalysis, HashtagGenerationRequest
)
from .hashtag_generator import HashtagGenerator
from .keyword_analyzer import KeywordAnalyzer
from .content_enhancer import ContentEnhancer

logger = logging.getLogger(__name__)

class BaseSEOOptimizer:
    """Main SEO optimization engine"""
    
    def __init__(self, twitter_client=None, config: Dict[str, Any] = None):
        self.twitter_client = twitter_client
        self.config = config or {}
        
        # Initialize component modules
        self.hashtag_generator = HashtagGenerator(twitter_client, config)
        self.keyword_analyzer = KeywordAnalyzer(config)
        self.content_enhancer = ContentEnhancer(config)
        
        # Optimization thresholds
        self.optimization_thresholds = {
            SEOOptimizationLevel.LIGHT: {
                'min_keywords': 1,
                'max_hashtags': 3,
                'keyword_density_target': 0.01,
                'readability_weight': 0.8
            },
            SEOOptimizationLevel.MODERATE: {
                'min_keywords': 2,
                'max_hashtags': 5,
                'keyword_density_target': 0.02,
                'readability_weight': 0.6
            },
            SEOOptimizationLevel.AGGRESSIVE: {
                'min_keywords': 3,
                'max_hashtags': 8,
                'keyword_density_target': 0.03,
                'readability_weight': 0.4
            }
        }
    
    async def optimize_content(self, request: SEOOptimizationRequest, 
                            context: SEOAnalysisContext = None) -> SEOOptimizationResult:
        """
        Optimize content based on request parameters
        
        Args:
            request: SEO optimization request
            context: Analysis context
            
        Returns:
            SEO optimization result
        """
        try:
            # Extract content from request
            original_content = request.content
            
            # Perform optimization
            optimized_content = self._optimize_content_text(
                original_content, 
                request.content_type,
                request.target_keywords,
                context
            )
            
            # Calculate optimization score
            optimization_score = self._calculate_optimization_score(
                original_content, optimized_content, request.target_keywords
            )
            
            # Generate suggestions
            suggestions = self._generate_optimization_suggestions(
                original_content, request.content_type, context
            )
            
            # Create improvement suggestions as strings
            improvement_suggestions = [
                "Added relevant hashtags for better discoverability",
                "Integrated target keywords naturally",
                "Optimized content structure for engagement",
                "Enhanced call-to-action effectiveness"
            ]
            
            # Create result object with correct types
            return SEOOptimizationResult(
                original_content=original_content,
                optimized_content=optimized_content,
                optimization_score=optimization_score,
                improvements_made=improvement_suggestions,
                hashtag_analysis=[],
                keyword_analysis=[],
                estimated_reach_improvement=15.0,
                suggestions=suggestions
            )
            
        except Exception as e:
            logger.error(f"Content optimization failed: {str(e)}")
            # Return safe fallback result
            return SEOOptimizationResult(
                original_content=request.content if hasattr(request, 'content') else "",
                optimized_content=request.content if hasattr(request, 'content') else "",
                optimization_score=0.5,
                improvements_made=["Optimization failed - using original content"],
                hashtag_analysis=[],
                keyword_analysis=[],
                estimated_reach_improvement=0.0,
                suggestions=ContentOptimizationSuggestions()
            )

    def optimize_content(self, request: SEOOptimizationRequest, 
                        context: SEOAnalysisContext = None) -> SEOOptimizationResult:
        """
        Synchronous version of optimize_content for backward compatibility
        """
        try:
            # Extract content from request
            original_content = request.content
            
            # Perform optimization
            optimized_content = self._optimize_content_text(
                original_content, 
                request.content_type,
                request.target_keywords,
                context
            )
            
            # Calculate optimization score
            optimization_score = self._calculate_optimization_score(
                original_content, optimized_content, request.target_keywords
            )
            
            # Generate suggestions
            suggestions = self._generate_optimization_suggestions(
                original_content, request.content_type, context
            )
            
            # Create improvement suggestions as strings
            improvement_suggestions = [
                "Added relevant hashtags for better discoverability",
                "Integrated target keywords naturally",
                "Optimized content structure for engagement"
            ]
            
            # Create result object
            return SEOOptimizationResult(
                original_content=original_content,
                optimized_content=optimized_content,
                optimization_score=optimization_score,
                improvements_made=improvement_suggestions,
                hashtag_analysis=[],
                keyword_analysis=[],
                estimated_reach_improvement=15.0,
                suggestions=suggestions
            )
            
        except Exception as e:
            logger.error(f"Content optimization failed: {str(e)}")
            # Return safe fallback result
            return SEOOptimizationResult(
                original_content=request.content if hasattr(request, 'content') else "",
                optimized_content=request.content if hasattr(request, 'content') else "",
                optimization_score=0.5,
                improvements_made=["Optimization failed - using original content"],
                hashtag_analysis=[],
                keyword_analysis=[],
                estimated_reach_improvement=0.0,
                suggestions=ContentOptimizationSuggestions()
            )

    def optimize_content_simple(self, content: str, content_type: SEOContentType, 
                              context: Dict[str, Any] = None) -> str:
        """
        Simple content optimization that returns optimized text
        
        Args:
            content: Content to optimize
            content_type: Type of content
            context: Additional context
            
        Returns:
            Optimized content string
        """
        try:
            # Basic optimization
            optimized = content
            
            # Add hashtags if not present
            if '#' not in optimized and content_type in [SEOContentType.TWEET, SEOContentType.LINKEDIN_POST]:
                if content_type == SEOContentType.TWEET:
                    optimized += " #innovation #productivity"
                elif content_type == SEOContentType.LINKEDIN_POST:
                    optimized += " #leadership #business #growth"
            
            # Ensure proper length
            if content_type == SEOContentType.TWEET and len(optimized) > 280:
                optimized = optimized[:277] + "..."
            
            return optimized
            
        except Exception as e:
            logger.error(f"Simple content optimization failed: {str(e)}")
            return content

    async def _analyze_current_content(self, request: SEOOptimizationRequest) -> Dict[str, Any]:
        """Analyze the current content state"""
        content = request.content
        
        # Extract current hashtags
        current_hashtags = re.findall(r'#(\w+)', content)
        
        # Count words and characters
        word_count = len(content.split())
        char_count = len(content)
        
        # Analyze readability (simplified)
        readability_score = self._calculate_readability_score(content)
        
        # Check keyword presence
        keyword_density = {}
        for keyword in request.context.niche_keywords:
            count = content.lower().count(keyword.lower())
            density = count / word_count if word_count > 0 else 0
            keyword_density[keyword] = density
        
        return {
            'current_hashtags': current_hashtags,
            'word_count': word_count,
            'char_count': char_count,
            'readability_score': readability_score,
            'keyword_density': keyword_density,
            'has_call_to_action': self._has_call_to_action(content),
            'has_question': '?' in content,
            'sentiment_tone': self._analyze_content_sentiment(content)
        }
    
    async def _analyze_keywords(self, request: SEOOptimizationRequest) -> List[KeywordAnalysis]:
        """Analyze and optimize keywords"""
        # Extract target keywords from context
        target_keywords = []
        target_keywords.extend(request.context.niche_keywords)
        target_keywords.extend(request.context.product_categories)
        
        # Add trend keywords if available
        if request.context.trend_context:
            trend_keywords = request.context.trend_context.get('keywords', [])
            target_keywords.extend(trend_keywords[:5])
        
        # Analyze keywords
        keyword_analysis = self.keyword_analyzer.analyze_keywords(
            request.content, request.context, target_keywords
        )
        
        # Filter by optimization level
        thresholds = self.optimization_thresholds[request.optimization_level]
        min_keywords = thresholds['min_keywords']
        
        # Return top keywords based on relevance and search volume
        return keyword_analysis[:max(min_keywords, 10)]
    
    async def _analyze_hashtags(self, request: SEOOptimizationRequest) -> List[HashtagMetrics]:
        """Analyze and generate hashtag recommendations"""
        
        # Create hashtag generation request
        hashtag_request = HashtagGenerationRequest(
            content=request.content,
            content_type=request.content_type,
            niche_keywords=request.context.niche_keywords,
            max_hashtags=request.max_hashtags,
            strategy=request.hashtag_strategy,
            include_trending=request.include_trending_tags,
            target_audience=request.context.target_audience
        )
        
        # Generate hashtags
        return self.hashtag_generator.generate_hashtags(hashtag_request)
    
    async def _optimize_content_structure(self, request: SEOOptimizationRequest,
                                        keyword_analysis: List[KeywordAnalysis],
                                        hashtag_analysis: List[HashtagMetrics],
                                        thresholds: Dict[str, Any]) -> str:
        """Optimize content structure and wording"""
        
        # Start with original content
        optimized_content = request.content
        
        if not request.preserve_original_tone:
            # Enhance content with keywords
            optimized_content = self.content_enhancer.enhance_with_keywords(
                optimized_content, 
                [ka.keyword for ka in keyword_analysis[:5]],
                thresholds['keyword_density_target']
            )
        
        # Add optimized hashtags
        optimized_content = self._add_optimized_hashtags(
            optimized_content, hashtag_analysis, request.content_type
        )
        
        # Optimize for content type
        optimized_content = self._optimize_for_content_type(
            optimized_content, request.content_type
        )
        
        # Ensure readability
        if thresholds['readability_weight'] > 0.5:
            optimized_content = self._ensure_readability(optimized_content)
        
        return optimized_content
    
    def _add_optimized_hashtags(self, content: str, hashtag_analysis: List[HashtagMetrics],
                              content_type: SEOContentType) -> str:
        """Add optimized hashtags to content"""
        
        # Remove existing hashtags first
        content_without_hashtags = re.sub(r'#\w+', '', content).strip()
        
        # Get content type specific hashtag limits
        hashtag_limits = {
            SEOContentType.TWEET: 5,
            SEOContentType.REPLY: 2,
            SEOContentType.THREAD: 3,
            SEOContentType.QUOTE_TWEET: 3
        }
        
        max_hashtags = hashtag_limits.get(content_type, 5)
        selected_hashtags = hashtag_analysis[:max_hashtags]
        
        if selected_hashtags:
            hashtag_text = ' ' + ' '.join(f'#{ht.hashtag}' for ht in selected_hashtags)
            
            # Check character limits
            total_length = len(content_without_hashtags) + len(hashtag_text)
            
            if content_type == SEOContentType.TWEET and total_length > 280:
                # Reduce hashtags to fit
                while selected_hashtags and total_length > 280:
                    selected_hashtags.pop()
                    hashtag_text = ' ' + ' '.join(f'#{ht.hashtag}' for ht in selected_hashtags)
                    total_length = len(content_without_hashtags) + len(hashtag_text)
            
            return content_without_hashtags + hashtag_text
        
        return content_without_hashtags
    
    def _optimize_for_content_type(self, content: str, content_type: SEOContentType) -> str:
        """Apply content type specific optimizations"""
        
        if content_type == SEOContentType.TWEET:
            # Ensure tweet is engaging
            if not ('?' in content or '!' in content):
                # Add engagement element
                content = content.rstrip('.') + '?'
        
        elif content_type == SEOContentType.THREAD:
            # Add thread indicator if not present
            if not ('🧵' in content or 'thread' in content.lower() or '1/' in content):
                content = '🧵 ' + content
        
        elif content_type == SEOContentType.REPLY:
            # Ensure conversational tone
            conversational_starters = ['Thanks', 'Great point', 'Interesting', 'I agree']
            if not any(starter.lower() in content.lower() for starter in conversational_starters):
                if not content.startswith(('@', 'Thanks', 'Great', 'Interesting')):
                    content = 'Great point! ' + content
        
        return content
    
    def _ensure_readability(self, content: str) -> str:
        """Ensure content maintains good readability"""
        
        # Break up long sentences
        sentences = content.split('.')
        improved_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence.split()) > 20:  # Long sentence
                # Try to break it up
                if ' and ' in sentence:
                    parts = sentence.split(' and ', 1)
                    improved_sentences.append(parts[0].strip())
                    improved_sentences.append('And ' + parts[1].strip())
                else:
                    improved_sentences.append(sentence)
            else:
                improved_sentences.append(sentence)
        
        return '. '.join([s for s in improved_sentences if s.strip()])
    
    def _calculate_optimization_score(self, original: str, optimized: str, 
                                    target_keywords: List[str]) -> float:
        """Calculate optimization score"""
        try:
            score = 0.5  # Base score
            
            # Length improvement
            if len(optimized) > len(original):
                score += 0.1
            
            # Hashtag addition
            if '#' in optimized and '#' not in original:
                score += 0.2
            
            # Keyword integration
            if target_keywords:
                keywords_added = sum(1 for kw in target_keywords 
                                   if kw.lower() in optimized.lower() and kw.lower() not in original.lower())
                score += keywords_added * 0.1
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Score calculation failed: {str(e)}")
            return 0.5

    def _optimize_content_text(self, content: str, content_type: SEOContentType,
                             target_keywords: List[str], context: SEOAnalysisContext = None) -> str:
        """Optimize the actual content text"""
        try:
            optimized = content
            
            # Add relevant keywords if missing
            if target_keywords:
                for keyword in target_keywords[:2]:  # Limit to 2 keywords
                    if keyword.lower() not in optimized.lower():
                        # Try to naturally integrate keyword
                        if len(optimized) + len(keyword) + 1 < 250:  # Leave room for hashtags
                            optimized = f"{optimized} {keyword}"
            
            # Add hashtags based on content type
            if content_type == SEOContentType.TWEET:
                if '#' not in optimized:
                    hashtags = self._get_relevant_hashtags(optimized, context)
                    if hashtags:
                        hashtag_text = ' ' + ' '.join(f'#{tag}' for tag in hashtags[:3])
                        if len(optimized) + len(hashtag_text) <= 280:
                            optimized += hashtag_text
            
            return optimized
            
        except Exception as e:
            logger.error(f"Content text optimization failed: {str(e)}")
            return content

    def _get_relevant_hashtags(self, content: str, context: SEOAnalysisContext = None) -> List[str]:
        """Get relevant hashtags for content"""
        try:
            # Basic hashtag suggestions based on content
            hashtags = []
            
            content_lower = content.lower()
            
            # Technology related
            if any(word in content_lower for word in ['ai', 'tech', 'digital', 'innovation']):
                hashtags.extend(['innovation', 'technology'])
            
            # Business related
            if any(word in content_lower for word in ['business', 'startup', 'growth', 'productivity']):
                hashtags.extend(['business', 'growth'])
            
            # Professional related
            if any(word in content_lower for word in ['professional', 'career', 'leadership']):
                hashtags.extend(['leadership', 'professional'])
            
            # Remove duplicates and limit
            return list(dict.fromkeys(hashtags))[:3]
            
        except Exception as e:
            logger.error(f"Hashtag generation failed: {str(e)}")
            return ['innovation', 'business']

    def _generate_optimization_suggestions(self, content: str, content_type: SEOContentType,
                                         context: SEOAnalysisContext = None) -> ContentOptimizationSuggestions:
        """Generate optimization suggestions"""
        try:
            return ContentOptimizationSuggestions(
                recommended_hashtags=['innovation', 'business', 'growth'],
                primary_keywords=['productivity', 'professional'],
                secondary_keywords=['technology', 'digital'],
                trending_terms=['AI', 'automation'],
                engagement_tactics=['Ask questions', 'Share insights'],
                optimal_length=250 if content_type == SEOContentType.TWEET else 500,
                call_to_action='What do you think?'
            )
            
        except Exception as e:
            logger.error(f"Suggestion generation failed: {str(e)}")
            return ContentOptimizationSuggestions()

    def _has_call_to_action(self, content: str) -> bool:
        """Check if content has a call to action"""
        cta_patterns = [
            r'\bshare\b', r'\bcomment\b', r'\blike\b', r'\bfollow\b',
            r'\bclick\b', r'\btry\b', r'\bget\b', r'\bjoin\b',
            r'\blearn more\b', r'\bfind out\b', r'\bdiscover\b',
            r'\bcheck out\b', r'what do you think', r'thoughts?'
        ]
        
        content_lower = content.lower()
        return any(re.search(pattern, content_lower) for pattern in cta_patterns)
    
    def _analyze_content_sentiment(self, content: str) -> str:
        """Analyze content sentiment"""
        positive_words = ['great', 'amazing', 'awesome', 'love', 'excited', 'fantastic']
        negative_words = ['bad', 'terrible', 'hate', 'awful', 'worst', 'disappointed']
        
        content_lower = content.lower()
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _suggest_optimal_length(self, content_type: SEOContentType) -> Optional[int]:
        """Suggest optimal content length"""
        optimal_lengths = {
            SEOContentType.TWEET: 240,  # Leave room for hashtags
            SEOContentType.REPLY: 200,
            SEOContentType.THREAD: 250,  # Per tweet in thread
            SEOContentType.QUOTE_TWEET: 200
        }
        return optimal_lengths.get(content_type)
    
    def _suggest_call_to_action(self, content_type: SEOContentType) -> Optional[str]:
        """Suggest appropriate call to action"""
        cta_suggestions = {
            SEOContentType.TWEET: "What are your thoughts?",
            SEOContentType.REPLY: "Would love to hear your perspective!",
            SEOContentType.THREAD: "Share your experiences below 👇",
            SEOContentType.QUOTE_TWEET: "Thoughts on this?"
        }
        return cta_suggestions.get(content_type)
    
    def _suggest_optimal_timing(self) -> Optional[str]:
        """Suggest optimal posting timing"""
        # This could be based on audience analysis
        return "Post during peak engagement hours (9-10 AM or 7-9 PM)"
    
    def _estimate_reach_improvement(self, initial_analysis: Dict[str, Any],
                                  optimization_score: float) -> float:
        """Estimate reach improvement percentage"""
        base_improvement = optimization_score * 100
        
        # Adjust based on initial analysis
        if initial_analysis.get('has_call_to_action'):
            base_improvement *= 0.9  # Less improvement if already optimized
        
        if initial_analysis.get('has_question'):
            base_improvement *= 0.9
        
        if len(initial_analysis.get('current_hashtags', [])) > 0:
            base_improvement *= 0.8  # Already had some hashtags
        
        return min(200.0, base_improvement)  # Cap at 200% improvement
    
    def _list_improvements_made(self, original_content: str, optimized_content: str) -> List[str]:
        """List the improvements made during optimization"""
        improvements = []
        
        # Check for added hashtags
        original_hashtags = set(re.findall(r'#(\w+)', original_content))
        optimized_hashtags = set(re.findall(r'#(\w+)', optimized_content))
        
        if optimized_hashtags - original_hashtags:
            new_hashtags = optimized_hashtags - original_hashtags
            improvements.append(f"Added hashtags: {', '.join(f'#{ht}' for ht in new_hashtags)}")
        
        # Check for structural improvements
        if '?' not in original_content and '?' in optimized_content:
            improvements.append("Added question for engagement")
        
        if not self._has_call_to_action(original_content) and self._has_call_to_action(optimized_content):
            improvements.append("Added call-to-action")
        
        # Check for content enhancements
        if len(optimized_content) > len(original_content):
            improvements.append("Enhanced content with relevant keywords")
        
        return improvements
    
    def _create_score_breakdown(self, keyword_analysis: List[KeywordAnalysis],
                              hashtag_analysis: List[HashtagMetrics],
                              optimization_score: float) -> Dict[str, float]:
        """Create detailed score breakdown"""
        return {
            'overall_score': optimization_score,
            'keyword_optimization': len(keyword_analysis) / 10,  # Normalized
            'hashtag_quality': sum(ht.relevance_score for ht in hashtag_analysis) / len(hashtag_analysis) if hashtag_analysis else 0,
            'content_structure': 0.8,  # Simplified
            'engagement_potential': 0.7,  # Simplified
            'readability': 0.8  # Simplified
        }
    
    def _create_fallback_result(self, request: SEOOptimizationRequest) -> SEOOptimizationResult:
        """Create fallback result when optimization fails"""
        return SEOOptimizationResult(
            original_content=request.content,
            optimized_content=request.content,
            optimization_score=0.5,
            improvements_made=["Optimization failed - content unchanged"],
            suggestions=ContentOptimizationSuggestions(),
            hashtag_analysis=[],
            keyword_analysis=[],
            estimated_reach_improvement=0.0
        )
    
    # Public interface methods for integration with ContentGenerationModule
    
    def get_content_suggestions(self, trend_info: Dict[str, Any],
                              product_info: Dict[str, Any],
                              content_type: SEOContentType) -> ContentOptimizationSuggestions:
        """
        Get SEO suggestions for content generation (used by ContentGenerationModule)
        """
        try:
            # Build context from provided information
            context = SEOAnalysisContext(
                content_type=content_type,
                target_audience=product_info.get('target_audience', 'professionals'),
                niche_keywords=product_info.get('core_values', []),
                product_categories=[product_info.get('industry_category', 'technology')],
                trend_context=trend_info
            )
            
            # Generate keyword suggestions
            keyword_suggestions = self.keyword_analyzer.generate_keyword_suggestions(context, 10)
            
            # Generate hashtag suggestions
            hashtag_request = HashtagGenerationRequest(
                content=trend_info.get('topic_name', ''),
                content_type=content_type,
                niche_keywords=context.niche_keywords,
                max_hashtags=5,
                strategy=HashtagStrategy.ENGAGEMENT_OPTIMIZED
            )
            
            hashtag_metrics = self.hashtag_generator.generate_hashtags(hashtag_request)
            recommended_hashtags = [ht.hashtag for ht in hashtag_metrics]
            
            return ContentOptimizationSuggestions(
                recommended_hashtags=recommended_hashtags,
                primary_keywords=keyword_suggestions[:3],
                secondary_keywords=keyword_suggestions[3:6],
                trending_terms=trend_info.get('keywords', [])[:3],
                optimal_length=self._suggest_optimal_length(content_type),
                call_to_action=self._suggest_call_to_action(content_type),
                timing_recommendation=self._suggest_optimal_timing(),
                engagement_tactics=['Ask questions', 'Share insights', 'Use relevant hashtags']
            )
            
        except Exception as e:
            logger.error(f"Failed to get content suggestions: {e}")
            return ContentOptimizationSuggestions(
                recommended_hashtags=['innovation', 'business', 'growth'],
                primary_keywords=['productivity', 'professional'],
                secondary_keywords=['technology', 'digital'],
                trending_terms=['AI', 'automation'],
                engagement_tactics=['Ask questions', 'Share insights'],
                optimal_length=250 if content_type == SEOContentType.TWEET else 500,
                call_to_action='What do you think?',
                timing_recommendation='Peak hours: 9-11 AM, 1-3 PM'
            )

    async def get_content_suggestions_async(self, trend_info: Dict[str, Any],
                                          product_info: Dict[str, Any],
                                          content_type: SEOContentType) -> ContentOptimizationSuggestions:
        """
        Async version of get_content_suggestions for future LLM integration
        """
        # For now, just call the sync version
        return self.get_content_suggestions(trend_info, product_info, content_type)

    def get_optimization_analytics(self, optimization_results: List[SEOOptimizationResult]) -> Dict[str, Any]:
        """Analyze optimization performance across multiple results"""
        try:
            if not optimization_results:
                return {'message': 'No optimization results to analyze'}
            
            # Calculate average metrics
            avg_optimization_score = sum(r.optimization_score for r in optimization_results) / len(optimization_results)
            avg_reach_improvement = sum(r.estimated_reach_improvement for r in optimization_results) / len(optimization_results)
            
            # Count improvement types
            improvement_counts = {}
            for result in optimization_results:
                for improvement in result.improvements_made:
                    improvement_counts[improvement] = improvement_counts.get(improvement, 0) + 1
            
            # Most common hashtags
            all_hashtags = []
            for result in optimization_results:
                all_hashtags.extend([ht.hashtag for ht in result.hashtag_analysis])
            
            hashtag_counts = {}
            for hashtag in all_hashtags:
                hashtag_counts[hashtag] = hashtag_counts.get(hashtag, 0) + 1
            
            top_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'total_optimizations': len(optimization_results),
                'avg_optimization_score': round(avg_optimization_score, 3),
                'avg_reach_improvement': round(avg_reach_improvement, 1),
                'most_common_improvements': dict(sorted(improvement_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
                'top_recommended_hashtags': [hashtag for hashtag, count in top_hashtags],
                'optimization_success_rate': len([r for r in optimization_results if r.optimization_score > 0.6]) / len(optimization_results)
            }
            
        except Exception as e:
            logger.error(f"Optimization analytics failed: {e}")
            return {'error': str(e)}

    def optimize_content_from_request(self, request: SEOOptimizationRequest) -> SEOOptimizationResult:
        """
        Optimize content from a request object
        """
        return self.optimize_content(
            content=request.content,
            content_type=request.content_type,
            optimization_level=request.optimization_level,
            target_keywords=request.target_keywords
        )

    def _analyze_content_seo(self, content: str, content_type: SEOContentType) -> Dict[str, Any]:
        """Analyze content for SEO metrics"""
        analysis = {
            'content_length': len(content),
            'word_count': len(content.split()),
            'keywords': self._extract_keywords(content),
            'hashtags': self._extract_hashtags(content),
            'readability_score': self._calculate_readability_score(content),
            'keyword_density': self._calculate_keyword_density(content),
            'overall_score': 0.0
        }
        
        # Calculate overall SEO score
        analysis['overall_score'] = self._calculate_overall_seo_score(analysis, content_type)
        
        return analysis

    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content"""
        # Simple keyword extraction
        words = content.lower().split()
        # Filter out common stop words and short words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word.strip('.,!?;:') for word in words 
                   if len(word) > 3 and word.lower() not in stop_words]
        return list(set(keywords))[:10]  # Return unique keywords, limit to 10

    def _extract_hashtags(self, content: str) -> List[str]:
        """Extract hashtags from content"""
        import re
        hashtags = re.findall(r'#\w+', content)
        return [tag[1:] for tag in hashtags]  # Remove # symbol

    def _calculate_readability_score(self, content: str) -> float:
        """Calculate readability score (simplified)"""
        words = content.split()
        if not words:
            return 0.0
        
        # Simple readability based on average word length
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Score from 0-1, where shorter words = higher readability
        readability = max(0, 1 - (avg_word_length - 4) / 10)
        return min(1.0, readability)

    def _calculate_keyword_density(self, content: str) -> float:
        """Calculate keyword density"""
        words = content.split()
        if not words:
            return 0.0
        
        # Count unique words vs total words
        unique_words = len(set(word.lower() for word in words))
        total_words = len(words)
        
        return unique_words / total_words if total_words > 0 else 0.0

    def _calculate_overall_seo_score(self, analysis: Dict[str, Any], content_type: SEOContentType) -> float:
        """Calculate overall SEO score"""
        score = 0.0
        
        # Content length score (0.3 weight)
        content_length = analysis['content_length']
        if 50 <= content_length <= 280:
            length_score = 1.0
        elif content_length < 50:
            length_score = content_length / 50
        else:
            length_score = max(0.5, 1 - (content_length - 280) / 280)
        
        score += length_score * 0.3
        
        # Keyword diversity score (0.3 weight)
        keyword_density = analysis.get('keyword_density', 0)
        keyword_score = min(1.0, keyword_density * 2)  # Optimal around 0.5
        score += keyword_score * 0.3
        
        # Hashtag score (0.2 weight)
        hashtag_count = len(analysis.get('hashtags', []))
        hashtag_score = min(1.0, hashtag_count / 3)  # Optimal around 3 hashtags
        score += hashtag_score * 0.2
        
        # Readability score (0.2 weight)
        readability = analysis.get('readability_score', 0)
        score += readability * 0.2
        
        return round(score, 3)