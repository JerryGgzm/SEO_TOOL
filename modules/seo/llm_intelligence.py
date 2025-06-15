"""LLM-Enhanced SEO Intelligence Module

This module integrates Large Language Models into the SEO optimization process
to provide intelligent content enhancement, keyword optimization, and strategic insights.
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
import re

from modules.seo.models import (
    SEOOptimizationRequest, SEOOptimizationResult, ContentOptimizationSuggestions,
    SEOAnalysisContext, SEOContentType, SEOOptimizationLevel
)

logger = logging.getLogger(__name__)

class LLMSEOIntelligence:
    """LLM-powered SEO intelligence for content optimization"""
    
    def __init__(self, llm_client=None, model_name: str = "gpt-3.5-turbo"):
        self.llm_client = llm_client
        self.model_name = model_name
        
        # LLM prompting strategies for different optimization aspects
        self.optimization_prompts = {
            'keyword_integration': self._create_keyword_integration_prompt,
            'hashtag_optimization': self._create_hashtag_optimization_prompt,
            'engagement_enhancement': self._create_engagement_enhancement_prompt,
            'trend_alignment': self._create_trend_alignment_prompt,
            'platform_optimization': self._create_platform_optimization_prompt
        }
    
    async def enhance_content_with_llm(self, request: SEOOptimizationRequest,
                                     context: SEOAnalysisContext,
                                     optimization_strategy: str = "comprehensive") -> Dict[str, Any]:
        """
        Use LLM to enhance content with intelligent SEO optimization
        
        Args:
            request: SEO optimization request
            context: Analysis context
            optimization_strategy: Strategy for optimization
            
        Returns:
            Enhanced content with LLM insights
        """
        try:
            if not self.llm_client:
                logger.warning("No LLM client available for SEO enhancement")
                return self._fallback_enhancement(request)
            
            # Generate different optimization approaches
            optimization_results = {}
            
            if optimization_strategy == "comprehensive":
                # Run multiple optimization strategies
                strategies = ['keyword_integration', 'engagement_enhancement', 'trend_alignment']
                
                for strategy in strategies:
                    try:
                        result = await self._apply_llm_strategy(strategy, request, context)
                        optimization_results[strategy] = result
                    except Exception as e:
                        logger.warning(f"LLM strategy {strategy} failed: {e}")
                        continue
                
                # Synthesize the best optimization
                enhanced_content = await self._synthesize_optimizations(
                    request.content, optimization_results, context
                )
            else:
                # Single strategy optimization
                enhanced_content = await self._apply_llm_strategy(
                    optimization_strategy, request, context
                )
            
            # Generate intelligent SEO suggestions
            seo_suggestions = await self._generate_intelligent_seo_suggestions(
                request.content, enhanced_content, context
            )
            
            # Calculate optimization score
            optimization_score = self._calculate_llm_optimization_score(
                request.content, enhanced_content, seo_suggestions
            )
            
            return {
                'enhanced_content': enhanced_content,
                'seo_suggestions': seo_suggestions,
                'optimization_score': optimization_score,
                'llm_insights': optimization_results,
                'enhancement_metadata': {
                    'strategy_used': optimization_strategy,
                    'llm_model': self.model_name,
                    'enhancement_timestamp': datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"LLM SEO enhancement failed: {e}")
            return self._fallback_enhancement(request)
    
    async def _apply_llm_strategy(self, strategy: str, request: SEOOptimizationRequest,
                                context: SEOAnalysisContext) -> str:
        """Apply specific LLM optimization strategy"""
        
        if strategy not in self.optimization_prompts:
            return request.content
        
        # Create strategy-specific prompt
        prompt = self.optimization_prompts[strategy](request, context)
        
        # Call LLM
        enhanced_content = await self._call_llm_for_optimization(prompt)
        
        return enhanced_content or request.content
    
    def _create_keyword_integration_prompt(self, request: SEOOptimizationRequest,
                                         context: SEOAnalysisContext) -> str:
        """Create prompt for intelligent keyword integration"""
        
        keywords = context.niche_keywords[:5] if context.niche_keywords else []
        product_categories = context.product_categories[:3] if context.product_categories else []
        
        prompt = f"""
Optimize this social media content for SEO by naturally integrating relevant keywords while maintaining readability and authenticity.

Original Content: "{request.content}"

Target Keywords: {', '.join(keywords)}
Product Categories: {', '.join(product_categories)}
Target Audience: {context.target_audience}
Content Type: {request.content_type.value}

Instructions:
1. Naturally integrate 2-3 target keywords into the content
2. Maintain the original tone and message
3. Ensure the content flows naturally and doesn't feel keyword-stuffed
4. Keep within character limits for {request.content_type.value}
5. Preserve any existing hashtags that are relevant

Return only the optimized content, no additional commentary.
"""
        return prompt
    
    def _create_hashtag_optimization_prompt(self, request: SEOOptimizationRequest,
                                          context: SEOAnalysisContext) -> str:
        """Create prompt for intelligent hashtag optimization"""
        
        prompt = f"""
Optimize this social media content by adding or improving hashtags for maximum discoverability and engagement.

Original Content: "{request.content}"

Context:
- Target Audience: {context.target_audience}
- Niche: {', '.join(context.niche_keywords[:3]) if context.niche_keywords else 'general'}
- Industry: {context.industry_vertical or 'technology'}
- Content Type: {request.content_type.value}

Instructions:
1. Add 3-5 relevant hashtags that will help the content reach the target audience
2. Mix popular and niche-specific hashtags
3. Ensure hashtags are relevant to the content and industry
4. Remove any irrelevant existing hashtags
5. Consider trending hashtags that align with the content
6. Keep total character count appropriate for {request.content_type.value}

Return only the optimized content with hashtags, no additional commentary.
"""
        return prompt
    
    def _create_engagement_enhancement_prompt(self, request: SEOOptimizationRequest,
                                            context: SEOAnalysisContext) -> str:
        """Create prompt for engagement optimization"""
        
        prompt = f"""
Enhance this social media content to maximize engagement while maintaining SEO value.

Original Content: "{request.content}"

Context:
- Target Audience: {context.target_audience}
- Content Type: {request.content_type.value}
- Brand Voice: {context.brand_voice.get('tone', 'professional') if context.brand_voice else 'professional'}

Instructions:
1. Add elements that encourage interaction (questions, calls-to-action, etc.)
2. Use engaging language that resonates with the target audience
3. Include emotional triggers or compelling hooks
4. Maintain professional quality appropriate for the brand
5. Ensure content invites responses or shares
6. Keep within platform character limits

Return only the enhanced content, no additional commentary.
"""
        return prompt
    
    def _create_trend_alignment_prompt(self, request: SEOOptimizationRequest,
                                     context: SEOAnalysisContext) -> str:
        """Create prompt for trend alignment optimization"""
        
        trend_context = context.trend_context or {}
        trending_keywords = trend_context.get('keywords', [])
        
        prompt = f"""
Optimize this content to align with current trends while maintaining its core message and SEO value.

Original Content: "{request.content}"

Trending Context:
- Trending Keywords: {', '.join(trending_keywords[:5]) if trending_keywords else 'innovation, technology, growth'}
- Target Audience: {context.target_audience}
- Industry: {context.industry_vertical or 'technology'}

Instructions:
1. Naturally incorporate 1-2 trending keywords that are relevant
2. Update language to reflect current industry conversations
3. Add contemporary references that resonate with the audience
4. Maintain the original message and value proposition
5. Ensure content feels current and relevant
6. Keep appropriate length for {request.content_type.value}

Return only the trend-optimized content, no additional commentary.
"""
        return prompt
    
    def _create_platform_optimization_prompt(self, request: SEOOptimizationRequest,
                                           context: SEOAnalysisContext) -> str:
        """Create prompt for platform-specific optimization"""
        
        platform_guidelines = {
            SEOContentType.TWEET: "Twitter: 280 chars max, hashtags at end, engaging and concise",
            SEOContentType.LINKEDIN_POST: "LinkedIn: Professional tone, longer form allowed, industry insights",
            SEOContentType.FACEBOOK_POST: "Facebook: Conversational, community-focused, storytelling",
            SEOContentType.BLOG_POST: "Blog: Long-form, SEO-optimized, comprehensive coverage"
        }
        
        guidelines = platform_guidelines.get(request.content_type, "Social media: engaging and concise")
        
        prompt = f"""
Optimize this content specifically for {request.content_type.value} to maximize platform-specific performance.

Original Content: "{request.content}"

Platform Guidelines: {guidelines}
Target Audience: {context.target_audience}

Instructions:
1. Adapt content format and style for optimal {request.content_type.value} performance
2. Use platform-appropriate language and structure
3. Include platform-specific engagement elements
4. Optimize for platform algorithm preferences
5. Maintain SEO value while platform-optimizing
6. Follow character limits and best practices

Return only the platform-optimized content, no additional commentary.
"""
        return prompt
    
    async def _synthesize_optimizations(self, original_content: str,
                                      optimization_results: Dict[str, str],
                                      context: SEOAnalysisContext) -> str:
        """Synthesize multiple optimization strategies into final content"""
        try:
            if not optimization_results or not self.llm_client:
                return original_content
            
            # Get the best optimization result
            best_result = None
            for strategy, result in optimization_results.items():
                if result and len(result.strip()) > 0:
                    best_result = result
                    break
            
            return best_result or original_content
            
        except Exception as e:
            logger.error(f"Optimization synthesis failed: {e}")
            return original_content
    
    async def _generate_intelligent_seo_suggestions(self, original_content: str,
                                                  enhanced_content: str,
                                                  context: SEOAnalysisContext) -> ContentOptimizationSuggestions:
        """Generate intelligent SEO suggestions using LLM"""
        try:
            if not self.llm_client:
                return self._fallback_seo_suggestions()
            
            prompt = f"""
Analyze the SEO optimization of this content and provide specific suggestions.

Original: "{original_content}"
Optimized: "{enhanced_content}"
Target Audience: {context.target_audience}
Industry: {context.industry_vertical}
Niche Keywords: {', '.join(context.niche_keywords[:5])}

Provide SEO suggestions in this exact JSON format:
{{
    "recommended_hashtags": ["hashtag1", "hashtag2", "hashtag3"],
    "primary_keywords": ["keyword1", "keyword2"],
    "secondary_keywords": ["keyword3", "keyword4"],
    "trending_terms": ["term1", "term2"],
    "optimal_length": 280,
    "call_to_action": "suggested CTA",
    "engagement_tactics": ["tactic1", "tactic2"]
}}

Focus on actionable, specific recommendations.
"""
            
            response = await self._call_llm_for_optimization(prompt)
            
            if not response:
                return self._fallback_seo_suggestions()
            
            try:
                # Parse JSON response
                suggestions_data = json.loads(response)
                
                return ContentOptimizationSuggestions(
                    recommended_hashtags=suggestions_data.get('recommended_hashtags', []),
                    primary_keywords=suggestions_data.get('primary_keywords', []),
                    secondary_keywords=suggestions_data.get('secondary_keywords', []),
                    trending_terms=suggestions_data.get('trending_terms', []),
                    optimal_length=suggestions_data.get('optimal_length', 280),
                    call_to_action=suggestions_data.get('call_to_action', ''),
                    engagement_tactics=suggestions_data.get('engagement_tactics', [])
                )
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM JSON response: {e}")
                return self._fallback_seo_suggestions()
            
        except Exception as e:
            logger.error(f"Failed to generate intelligent SEO suggestions: {e}")
            return self._fallback_seo_suggestions()
    
    async def _call_llm_for_optimization(self, prompt: str) -> str:
        """Call LLM for content optimization"""
        try:
            if not self.llm_client:
                return None
            
            # Use the correct async method name
            response = await self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert SEO content optimizer. Provide optimized content that maintains the original message while improving SEO potential."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"LLM optimization call failed: {e}")
            return None
    
    def _calculate_llm_optimization_score(self, original: str, enhanced: str,
                                        suggestions: ContentOptimizationSuggestions) -> float:
        """Calculate optimization score based on LLM enhancements"""
        
        score = 0.5  # Base score
        
        # Length improvement
        if len(enhanced) > len(original):
            score += 0.1
        
        # Hashtag additions
        original_hashtags = len(re.findall(r'#\w+', original))
        enhanced_hashtags = len(re.findall(r'#\w+', enhanced))
        if enhanced_hashtags > original_hashtags:
            score += 0.15
        
        # Keyword integration
        if suggestions.primary_keywords:
            keywords_found = sum(1 for kw in suggestions.primary_keywords 
                               if kw.lower() in enhanced.lower())
            score += (keywords_found / len(suggestions.primary_keywords)) * 0.15
        
        # Engagement elements
        engagement_indicators = ['?', '!', 'what', 'how', 'why', 'share', 'think']
        if any(indicator in enhanced.lower() for indicator in engagement_indicators):
            score += 0.1
        
        # Quality suggestions
        if len(suggestions.engagement_tactics) >= 2:
            score += 0.1
        
        return min(1.0, score)
    
    def _fallback_seo_suggestions(self) -> ContentOptimizationSuggestions:
        """Fallback SEO suggestions when LLM fails"""
        return ContentOptimizationSuggestions(
            recommended_hashtags=['innovation', 'business', 'growth'],
            primary_keywords=['productivity', 'professional'],
            secondary_keywords=['technology', 'digital'],
            trending_terms=['AI', 'automation'],
            optimal_length=280,
            call_to_action='What are your thoughts?',
            engagement_tactics=['Ask questions', 'Share insights', 'Use emojis']
        )
    
    def _fallback_enhancement(self, request: SEOOptimizationRequest) -> Dict[str, Any]:
        """Fallback enhancement when LLM is unavailable"""
        return {
            'enhanced_content': request.content,
            'seo_suggestions': self._fallback_seo_suggestions(),
            'optimization_score': 0.5,
            'llm_insights': {},
            'enhancement_metadata': {
                'strategy_used': 'fallback',
                'llm_model': 'none',
                'enhancement_timestamp': datetime.utcnow().isoformat()
            }
        }

    async def analyze_optimization_result(self, result: 'SEOOptimizationResult', 
                                        request: 'SEOOptimizationRequest',
                                        context: 'SEOAnalysisContext') -> Dict[str, Any]:
        """
        Analyze an optimization result to provide insights
        
        Args:
            result: The optimization result to analyze
            request: Original optimization request
            context: Analysis context
            
        Returns:
            Dictionary containing analysis insights
        """
        try:
            if not self.llm_client:
                return {}
            
            # Create analysis prompt
            analysis_prompt = f"""
            Analyze this SEO optimization result and provide insights:
            
            Original Content: {result.original_content}
            Optimized Content: {result.optimized_content}
            Optimization Score: {result.optimization_score}
            Improvements Made: {', '.join(result.improvements_made)}
            
            Content Type: {request.content_type.value if hasattr(request.content_type, 'value') else str(request.content_type)}
            Target Audience: {context.target_audience}
            
            Please provide:
            1. Quality assessment of the optimization
            2. Potential improvements
            3. SEO strength analysis
            4. Engagement potential
            
            Respond in JSON format with keys: quality_score, improvements, seo_analysis, engagement_potential
            """
            
            # Get LLM response
            response = await self._call_llm_for_optimization(analysis_prompt)
            
            # Parse response
            try:
                insights = json.loads(response)
            except json.JSONDecodeError:
                # Fallback to basic insights
                insights = {
                    "quality_score": result.optimization_score,
                    "improvements": ["Content structure could be enhanced"],
                    "seo_analysis": "Basic SEO optimization applied",
                    "engagement_potential": "Moderate engagement expected"
                }
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to analyze optimization result: {e}")
            return {}

    async def generate_content_variations(self, content: str, context: 'SEOAnalysisContext', 
                                        num_variations: int = 3) -> List[str]:
        """
        Generate content variations for A/B testing
        
        Args:
            content: Original content
            context: Analysis context
            num_variations: Number of variations to generate
            
        Returns:
            List of content variations
        """
        try:
            if not self.llm_client:
                return []
            
            variation_prompt = f"""
            Create {num_variations} variations of this content for A/B testing:
            
            Original: {content}
            Target Audience: {context.target_audience}
            Content Type: {context.content_type.value if hasattr(context.content_type, 'value') else str(context.content_type)}
            
            Each variation should:
            1. Maintain the core message
            2. Use different wording/structure
            3. Be optimized for engagement
            4. Stay within appropriate length limits
            
            Return as JSON array of strings.
            """
            
            response = await self._call_llm_for_optimization(variation_prompt)
            
            try:
                variations = json.loads(response)
                if isinstance(variations, list):
                    return variations[:num_variations]
            except json.JSONDecodeError:
                pass
            
            # Fallback variations
            return [
                f"🚀 {content}",
                f"💡 {content} #innovation",
                f"✨ {content} What do you think?"
            ][:num_variations]
            
        except Exception as e:
            logger.error(f"Failed to generate content variations: {e}")
            return []

class LLMSEOAnalyzer:
    """LLM-powered SEO content analysis and insights"""
    
    def __init__(self, llm_client=None, model_name: str = "gpt-3.5-turbo"):
        self.llm_client = llm_client
        self.model_name = model_name
    
    async def analyze_content_seo_potential(self, content: str, 
                                          context: SEOAnalysisContext) -> Dict[str, Any]:
        """Analyze content's SEO potential using LLM"""
        
        try:
            if not self.llm_client:
                return self._basic_seo_analysis(content)
            
            prompt = f"""
Analyze the SEO potential of this social media content:

Content: "{content}"
Platform: {context.content_type.value}
Target Audience: {context.target_audience}
Industry: {context.industry_vertical}
Niche Keywords: {', '.join(context.niche_keywords[:5])}

Provide analysis in this JSON format:
{{
    "seo_strength_score": 0.7,
    "keyword_optimization": {{
        "current_keywords": ["keyword1", "keyword2"],
        "missing_opportunities": ["keyword3", "keyword4"],
        "keyword_density": "optimal"
    }},
    "discoverability": {{
        "search_potential": "high",
        "hashtag_effectiveness": "good",
        "trending_alignment": "moderate"
    }},
    "engagement_factors": {{
        "call_to_action_strength": "strong",
        "emotional_appeal": "high",
        "shareability": "good"
    }},
    "improvement_recommendations": ["suggestion1", "suggestion2"],
    "competitive_advantages": ["advantage1", "advantage2"]
}}

Score from 0.0 to 1.0. Be specific and actionable.
"""
            
            response = await self._call_llm(prompt)
            
            if not response:
                return self._basic_seo_analysis(content)
            
            try:
                analysis = json.loads(response)
                return analysis
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse SEO analysis JSON: {e}")
                return self._basic_seo_analysis(content)
            
        except Exception as e:
            logger.error(f"SEO potential analysis failed: {e}")
            return self._basic_seo_analysis(content)
    
    async def generate_content_variations(self, content: str, context: SEOAnalysisContext,
                                        variation_count: int = 3) -> List[Dict[str, Any]]:
        """Generate SEO-optimized content variations"""
        
        if not self.llm_client:
            return [{'content': content, 'strategy': 'original', 'seo_focus': 'none'}]
        
        variation_prompt = f"""
Create {variation_count} SEO-optimized variations of this content, each with a different optimization strategy.

Original Content: "{content}"

Context:
- Target Audience: {context.target_audience}
- Industry: {context.industry_vertical or 'technology'}
- Niche Keywords: {', '.join(context.niche_keywords[:5]) if context.niche_keywords else 'general business'}

For each variation, provide:
1. Keyword-focused optimization
2. Engagement-focused optimization  
3. Trend-focused optimization

Return as JSON array:
[
    {{
        "variation_number": 1,
        "content": "optimized content",
        "strategy": "keyword-focused",
        "seo_focus": "description of optimization approach",
        "expected_improvement": "expected benefit"
    }},
    ...
]

Make each variation distinctly different while maintaining the core message.
"""
        
        try:
            response = await self._call_llm(variation_prompt)
            
            if not response or response.strip() == '':
                logger.warning("Empty response from LLM")
                return [{'content': content, 'strategy': 'original', 'seo_focus': 'none'}]
            
            # Try to parse JSON response
            try:
                variations = json.loads(response)
                return variations if isinstance(variations, list) else []
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse variation JSON: {e}")
                logger.debug(f"Raw response: {response[:200]}...")
                # Return fallback variations
                return [
                    {'content': content + " #innovation", 'strategy': 'hashtag-focused', 'seo_focus': 'discoverability'},
                    {'content': content + " What do you think?", 'strategy': 'engagement-focused', 'seo_focus': 'interaction'},
                    {'content': content + " Learn more!", 'strategy': 'action-focused', 'seo_focus': 'conversion'}
                ]
                
        except Exception as e:
            logger.error(f"Content variation generation failed: {e}")
            return [{'content': content, 'strategy': 'original', 'seo_focus': 'none'}]
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM for analysis"""
        try:
            if not self.llm_client:
                logger.warning("No LLM client available")
                return None
            
            # Use the correct async method name
            response = await self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert SEO analyst specializing in social media optimization. "
                                 "Provide detailed, actionable insights in valid JSON format only. "
                                 "Do not include any text outside the JSON structure."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            if content:
                content = content.strip()
                
                # Remove any markdown code blocks if present
                if content.startswith('```json'):
                    content = content[7:]
                if content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                
                return content.strip()
            else:
                logger.warning("Empty content from LLM response")
                return None
            
        except Exception as e:
            logger.error(f"LLM analysis call failed: {e}")
            return None
    
    def _basic_seo_analysis(self, content: str) -> Dict[str, Any]:
        """Basic SEO analysis when LLM unavailable"""
        
        return {
            'seo_strength_score': 0.5,
            'keyword_optimization': {
                'current_keywords': [],
                'missing_opportunities': ['industry-specific terms'],
                'keyword_density': 'moderate'
            },
            'discoverability': {
                'search_potential': 'medium',
                'hashtag_effectiveness': 'moderate',
                'trending_alignment': 'unknown'
            },
            'engagement_factors': {
                'call_to_action_strength': 'weak' if '?' not in content else 'moderate',
                'emotional_appeal': 'medium',
                'shareability': 'medium'
            },
            'improvement_recommendations': [
                'Add relevant hashtags',
                'Include call-to-action',
                'Use trending keywords'
            ],
            'competitive_advantages': ['authentic voice']
        }

class LLMSEOOrchestrator:
    """Main orchestrator for LLM-enhanced SEO optimization"""
    
    def __init__(self, llm_client=None, model_name: str = "gpt-3.5-turbo"):
        self.llm_intelligence = LLMSEOIntelligence(llm_client, model_name)
        self.llm_analyzer = LLMSEOAnalyzer(llm_client, model_name)
    
    async def comprehensive_llm_optimization(self, request: SEOOptimizationRequest,
                                           context: SEOAnalysisContext) -> Dict[str, Any]:
        """Comprehensive LLM-powered SEO optimization"""
        
        try:
            # Phase 1: Analyze current content
            current_analysis = await self.llm_analyzer.analyze_content_seo_potential(
                request.content, context
            )
            
            # Phase 2: Generate optimized content
            enhancement_result = await self.llm_intelligence.enhance_content_with_llm(
                request, context, "comprehensive"
            )
            
            # Phase 3: Generate alternative variations
            variations = await self.llm_analyzer.generate_content_variations(
                enhancement_result['enhanced_content'], context, 2
            )
            
            # Phase 4: Final analysis of optimized content
            optimized_analysis = await self.llm_analyzer.analyze_content_seo_potential(
                enhancement_result['enhanced_content'], context
            )
            
            return {
                'original_content': request.content,
                'optimized_content': enhancement_result['enhanced_content'],
                'optimization_score': enhancement_result['optimization_score'],
                'seo_suggestions': enhancement_result['seo_suggestions'],
                'current_analysis': current_analysis,
                'optimized_analysis': optimized_analysis,
                'content_variations': variations,
                'llm_insights': enhancement_result['llm_insights'],
                'improvement_metrics': {
                    'seo_score_improvement': optimized_analysis.get('seo_strength_score', 0.5) - 
                                           current_analysis.get('seo_strength_score', 0.5),
                    'optimization_applied': True,
                    'llm_enhanced': True
                },
                'metadata': enhancement_result['enhancement_metadata']
            }
            
        except Exception as e:
            logger.error(f"Comprehensive LLM optimization failed: {e}")
            return {
                'original_content': request.content,
                'optimized_content': request.content,
                'optimization_score': 0.5,
                'error': str(e)
            }