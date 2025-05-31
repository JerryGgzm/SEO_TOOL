"""Main SEO optimizer that orchestrates all SEO optimization components"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
import re

from .models import (
    SEOOptimizationRequest, SEOOptimizationResult, ContentOptimizationSuggestions,
    SEOAnalysisContext, SEOContentType, SEOOptimizationLevel, HashtagStrategy,
    HashtagMetrics, KeywordAnalysis
)
from .hashtag_generator import HashtagGenerator
from .keyword_analyzer import KeywordAnalyzer
from .content_enhancer import ContentEnhancer

logger = logging.getLogger(__name__)

class SEOOptimizer:
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
            SEOOptimizationLevel.BASIC: {
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
    
    async def optimize_content(self, request: SEOOptimizationRequest) -> SEOOptimizationResult:
        """
        Main content optimization method
        
        Args:
            request: SEO optimization request
            
        Returns:
            SEO optimization result with enhanced content and suggestions
        """
        try:
            logger.info(f"Starting SEO optimization for {request.content_type} content")
            
            # Get optimization parameters
            thresholds = self.optimization_thresholds.get(
                request.optimization_level, 
                self.optimization_thresholds[SEOOptimizationLevel.MODERATE]
            )
            
            # Phase 1: Analyze current content
            initial_analysis = await self._analyze_current_content(request)
            
            # Phase 2: Generate keyword recommendations
            keyword_analysis = await self._analyze_keywords(request)
            
            # Phase 3: Generate hashtag recommendations
            hashtag_analysis = await self._analyze_hashtags(request)
            
            # Phase 4: Optimize content structure and wording
            optimized_content = await self._optimize_content_structure(
                request, keyword_analysis, hashtag_analysis, thresholds
            )
            
            # Phase 5: Calculate optimization scores
            optimization_score = self._calculate_optimization_score(
                request.content, optimized_content, keyword_analysis, hashtag_analysis
            )
            
            # Phase 6: Generate improvement suggestions
            suggestions = self._generate_optimization_suggestions(
                request, keyword_analysis, hashtag_analysis, optimization_score
            )
            
            # Phase 7: Estimate reach improvement
            reach_improvement = self._estimate_reach_improvement(
                initial_analysis, optimization_score
            )
            
            return SEOOptimizationResult(
                original_content=request.content,
                optimized_content=optimized_content,
                optimization_score=optimization_score,
                improvements_made=self._list_improvements_made(request.content, optimized_content),
                suggestions=suggestions,
                hashtag_analysis=hashtag_analysis,
                keyword_analysis=keyword_analysis,
                seo_score_breakdown=self._create_score_breakdown(
                    keyword_analysis, hashtag_analysis, optimization_score
                ),
                estimated_reach_improvement=reach_improvement,
                optimization_metadata={
                    'optimization_level': request.optimization_level.value,
                    'hashtag_strategy': request.hashtag_strategy.value,
                    'optimization_timestamp': datetime.utcnow().isoformat(),
                    'thresholds_used': thresholds
                }
            )
            
        except Exception as e:
            logger.error(f"SEO optimization failed: {e}")
            return self._create_fallback_result(request)
    
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
        from .models import HashtagGenerationRequest
        
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
    
    def _calculate_optimization_score(self, original_content: str, optimized_content: str,
                                    keyword_analysis: List[KeywordAnalysis],
                                    hashtag_analysis: List[HashtagMetrics]) -> float:
        """Calculate overall optimization score"""
        
        score = 0.0
        
        # Keyword optimization score (30%)
        keyword_score = self._calculate_keyword_score(optimized_content, keyword_analysis)
        score += keyword_score * 0.3
        
        # Hashtag optimization score (25%)
        hashtag_score = self._calculate_hashtag_score(hashtag_analysis)
        score += hashtag_score * 0.25
        
        # Content structure score (20%)
        structure_score = self._calculate_structure_score(optimized_content)
        score += structure_score * 0.2
        
        # Engagement potential score (15%)
        engagement_score = self._calculate_engagement_score(optimized_content)
        score += engagement_score * 0.15
        
        # Readability score (10%)
        readability_score = self._calculate_readability_score(optimized_content)
        score += readability_score * 0.1
        
        return min(1.0, score)
    
    def _calculate_keyword_score(self, content: str, keyword_analysis: List[KeywordAnalysis]) -> float:
        """Calculate keyword optimization score"""
        if not keyword_analysis:
            return 0.0
        
        score = 0.0
        content_lower = content.lower()
        
        for keyword_data in keyword_analysis[:5]:  # Top 5 keywords
            keyword = keyword_data.keyword.lower()
            
            # Check if keyword is present
            if keyword in content_lower:
                score += 0.2 * keyword_data.relevance_score
        
        return min(1.0, score)
    
    def _calculate_hashtag_score(self, hashtag_analysis: List[HashtagMetrics]) -> float:
        """Calculate hashtag optimization score"""
        if not hashtag_analysis:
            return 0.0
        
        # Average relevance and engagement scores
        avg_relevance = sum(ht.relevance_score for ht in hashtag_analysis) / len(hashtag_analysis)
        avg_engagement = sum(ht.engagement_rate for ht in hashtag_analysis) / len(hashtag_analysis)
        
        return (avg_relevance * 0.6 + avg_engagement * 100 * 0.4)  # Scale engagement rate
    
    def _calculate_structure_score(self, content: str) -> float:
        """Calculate content structure score"""
        score = 0.0
        
        # Has call to action
        if self._has_call_to_action(content):
            score += 0.3
        
        # Has question for engagement
        if '?' in content:
            score += 0.3
        
        # Appropriate length
        word_count = len(content.split())
        if 10 <= word_count <= 25:  # Good length for social media
            score += 0.2
        
        # Has hashtags
        if '#' in content:
            score += 0.2
        
        return score
    
    def _calculate_engagement_score(self, content: str) -> float:
        """Calculate engagement potential score"""
        score = 0.0
        
        # Personal pronouns
        if any(pronoun in content.lower() for pronoun in ['you', 'your', 'we', 'us']):
            score += 0.3
        
        # Action words
        action_words = ['discover', 'learn', 'share', 'join', 'explore', 'get', 'find']
        if any(word in content.lower() for word in action_words):
            score += 0.2
        
        # Numbers (tend to get attention)
        if any(char.isdigit() for char in content):
            score += 0.2
        
        # Emotional words
        emotional_words = ['amazing', 'incredible', 'fantastic', 'love', 'excited', 'thrilled']
        if any(word in content.lower() for word in emotional_words):
            score += 0.3
        
        return min(1.0, score)
    
    def _calculate_readability_score(self, content: str) -> float:
        """Calculate readability score (simplified)"""
        words = content.split()
        sentences = content.split('.')
        
        if not sentences:
            return 0.0
        
        avg_words_per_sentence = len(words) / len(sentences)
        
        # Optimal for social media: 10-15 words per sentence
        if 10 <= avg_words_per_sentence <= 15:
            return 1.0
        elif 8 <= avg_words_per_sentence <= 20:
            return 0.8
        elif 5 <= avg_words_per_sentence <= 25:
            return 0.6
        else:
            return 0.3
    
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
    
    def _generate_optimization_suggestions(self, request: SEOOptimizationRequest,
                                         keyword_analysis: List[KeywordAnalysis],
                                         hashtag_analysis: List[HashtagMetrics],
                                         optimization_score: float) -> ContentOptimizationSuggestions:
        """Generate optimization suggestions"""
        
        # Select top recommendations
        recommended_hashtags = [ht.hashtag for ht in hashtag_analysis[:request.max_hashtags]]
        primary_keywords = [ka.keyword for ka in keyword_analysis[:3]]
        secondary_keywords = [ka.keyword for ka in keyword_analysis[3:8]]
        
        # Generate engagement tactics
        engagement_tactics = []
        if '?' not in request.content:
            engagement_tactics.append("Add a question to encourage replies")
        
        if not self._has_call_to_action(request.content):
            engagement_tactics.append("Include a clear call-to-action")
        
        if optimization_score < 0.7:
            engagement_tactics.append("Consider adding more relevant keywords")
            engagement_tactics.append("Use trending hashtags for better discovery")
        
        return ContentOptimizationSuggestions(
            recommended_hashtags=recommended_hashtags,
            primary_keywords=primary_keywords,
            secondary_keywords=secondary_keywords,
            semantic_keywords=[ka.keyword for ka in keyword_analysis if ka.semantic_variations],
            trending_terms=[ka.keyword for ka in keyword_analysis if ka.trending_status],
            optimal_length=self._suggest_optimal_length(request.content_type),
            call_to_action=self._suggest_call_to_action(request.content_type),
            timing_recommendation=self._suggest_optimal_timing(),
            engagement_tactics=engagement_tactics
        )
    
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
            seo_score_breakdown={'overall_score': 0.5},
            estimated_reach_improvement=0.0,
            optimization_metadata={
                'optimization_failed': True,
                'error_timestamp': datetime.utcnow().isoformat()
            }
        )
    
    # Public interface methods for integration with ContentGenerationModule
    
    async def get_content_suggestions(self, trend_info: Dict[str, Any],
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
                call_to_action=self._suggest_call_to_action(content_type)
            )
            
        except Exception as e:
            logger.error(f"Failed to get content suggestions: {e}")
            return ContentOptimizationSuggestions()
    
    def optimize_content_simple(self, text: str, content_type: SEOContentType,
                              context: Dict[str, Any] = None) -> str:
        """
        Simple content optimization for integration with ContentGenerationModule
        """
        try:
            # Create basic optimization request
            seo_context = SEOAnalysisContext(
                content_type=content_type,
                niche_keywords=context.get('seo_keywords', []) if context else [],
                target_audience=context.get('target_audience', 'professionals') if context else 'professionals'
            )
            
            request = SEOOptimizationRequest(
                content=text,
                content_type=content_type,
                context=seo_context,
                optimization_level=SEOOptimizationLevel.MODERATE
            )
            
            # Run optimization synchronously (simplified)
            result = asyncio.run(self.optimize_content(request))
            return result.optimized_content
            
        except Exception as e:
            logger.error(f"Simple content optimization failed: {e}")
            return text