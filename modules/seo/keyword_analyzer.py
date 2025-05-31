
"""Keyword analysis and optimization engine"""
import re
import math
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import Counter, defaultdict
import logging

from .models import (
    KeywordAnalysis, KeywordDifficulty, SEOContentType,
    KeywordOptimizationRequest, SEOAnalysisContext
)

logger = logging.getLogger(__name__)

class KeywordAnalyzer:
    """Advanced keyword analysis and optimization"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Keyword categories and their search volume multipliers
        self.keyword_categories = {
            'brand_terms': 1.2,
            'product_terms': 1.5,
            'problem_solving': 1.8,
            'how_to': 2.0,
            'trending': 1.6,
            'long_tail': 1.3,
            'commercial': 1.4,
            'informational': 1.1
        }
        
        # Intent-based keyword patterns
        self.intent_patterns = {
            'commercial': [
                'buy', 'purchase', 'price', 'cost', 'cheap', 'discount',
                'deal', 'sale', 'review', 'compare', 'best', 'top'
            ],
            'informational': [
                'what', 'how', 'why', 'when', 'where', 'guide', 'tutorial',
                'learn', 'explain', 'definition', 'meaning', 'examples'
            ],
            'navigational': [
                'login', 'sign up', 'download', 'website', 'official',
                'contact', 'support', 'help', 'documentation'
            ],
            'transactional': [
                'free', 'trial', 'demo', 'signup', 'register', 'subscribe',
                'join', 'start', 'get', 'access', 'unlock'
            ]
        }
        
        # Semantic keyword relationships
        self.semantic_relationships = {
            'synonyms': {},
            'related_terms': {},
            'broader_terms': {},
            'narrower_terms': {}
        }
        
        # Initialize semantic relationships
        self._initialize_semantic_relationships()
    
    def _initialize_semantic_relationships(self):
        """Initialize semantic keyword relationships"""
        self.semantic_relationships = {
            'synonyms': {
                'ai': ['artificial intelligence', 'machine learning', 'ml'],
                'startup': ['new business', 'entrepreneurship', 'company'],
                'growth': ['expansion', 'scaling', 'development'],
                'innovation': ['breakthrough', 'advancement', 'disruption'],
                'productivity': ['efficiency', 'optimization', 'performance']
            },
            'related_terms': {
                'ai': ['automation', 'robotics', 'data science', 'algorithms'],
                'startup': ['venture capital', 'funding', 'mvp', 'pivot'],
                'marketing': ['advertising', 'promotion', 'branding', 'seo'],
                'technology': ['software', 'hardware', 'digital', 'tech']
            }
        }
    
    def analyze_keywords(self, content: str, context: SEOAnalysisContext,
                        target_keywords: List[str] = None) -> List[KeywordAnalysis]:
        """
        Analyze keywords in content and suggest optimizations
        
        Args:
            content: Content to analyze
            context: SEO analysis context
            target_keywords: Specific keywords to analyze
            
        Returns:
            List of keyword analysis results
        """
        try:
            logger.info("Starting keyword analysis")
            
            # Extract keywords from content
            extracted_keywords = self._extract_keywords_from_content(content)
            
            # Combine with target keywords
            all_keywords = set(extracted_keywords)
            if target_keywords:
                all_keywords.update(target_keywords)
            
            # Add niche-specific keywords
            all_keywords.update(context.niche_keywords)
            
            # Generate semantic variations
            semantic_keywords = self._generate_semantic_variations(list(all_keywords))
            all_keywords.update(semantic_keywords)
            
            # Analyze each keyword
            keyword_analyses = []
            for keyword in all_keywords:
                if len(keyword.strip()) > 2:  # Skip very short keywords
                    analysis = self._analyze_single_keyword(keyword, content, context)
                    if analysis:
                        keyword_analyses.append(analysis)
            
            # Sort by relevance and search volume
            keyword_analyses.sort(
                key=lambda k: (k.relevance_score * math.log(k.search_volume + 1)), 
                reverse=True
            )
            
            return keyword_analyses[:50]  # Limit to top 50 keywords
            
        except Exception as e:
            logger.error(f"Keyword analysis failed: {e}")
            return []
    
    def _extract_keywords_from_content(self, content: str) -> List[str]:
        """Extract potential keywords from content"""
        # Clean content
        content = re.sub(r'[^\w\s]', ' ', content.lower())
        words = content.split()
        
        # Remove stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
        
        # Single word keywords
        single_keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Multi-word keywords (2-3 words)
        multi_keywords = []
        for i in range(len(words) - 1):
            if words[i] not in stop_words and words[i+1] not in stop_words:
                two_word = f"{words[i]} {words[i+1]}"
                if len(two_word) > 5:
                    multi_keywords.append(two_word)
                
                # Three word phrases
                if i < len(words) - 2 and words[i+2] not in stop_words:
                    three_word = f"{words[i]} {words[i+1]} {words[i+2]}"
                    if len(three_word) <= 50:  # Reasonable length limit
                        multi_keywords.append(three_word)
        
        # Combine and deduplicate
        all_keywords = list(set(single_keywords + multi_keywords))
        
        # Filter by frequency (keep keywords that appear more than once for longer content)
        if len(content) > 500:
            keyword_counts = Counter(all_keywords)
            all_keywords = [kw for kw, count in keyword_counts.items() if count >= 2 or len(kw.split()) > 1]
        
        return all_keywords
    
    def _generate_semantic_variations(self, keywords: List[str]) -> List[str]:
        """Generate semantic variations of keywords"""
        variations = []
        
        for keyword in keywords:
            # Add synonyms
            if keyword in self.semantic_relationships['synonyms']:
                variations.extend(self.semantic_relationships['synonyms'][keyword])
            
            # Add related terms
            if keyword in self.semantic_relationships['related_terms']:
                variations.extend(self.semantic_relationships['related_terms'][keyword])
            
            # Generate morphological variations
            variations.extend(self._generate_morphological_variations(keyword))
        
        return list(set(variations))
    
    def _generate_morphological_variations(self, keyword: str) -> List[str]:
        """Generate morphological variations of a keyword"""
        variations = []
        
        # Single word variations
        if ' ' not in keyword:
            word = keyword.lower()
            
            # Plural/singular variations
            if word.endswith('s'):
                variations.append(word[:-1])  # Remove 's'
            else:
                variations.append(word + 's')  # Add 's'
            
            # Verb variations
            if word.endswith('ing'):
                base = word[:-3]
                variations.extend([base, base + 'e', base + 'ed'])
            elif word.endswith('ed'):
                base = word[:-2]
                variations.extend([base, base + 'ing'])
            else:
                variations.extend([word + 'ing', word + 'ed'])
        
        # Multi-word variations
        else:
            words = keyword.split()
            if len(words) == 2:
                # Reverse order
                variations.append(f"{words[1]} {words[0]}")
                
                # Add modifiers
                variations.extend([
                    f"best {keyword}",
                    f"top {keyword}",
                    f"{keyword} guide",
                    f"{keyword} tips"
                ])
        
        return [v for v in variations if len(v) > 2 and len(v) <= 50]
    
    def _analyze_single_keyword(self, keyword: str, content: str, 
                              context: SEOAnalysisContext) -> Optional[KeywordAnalysis]:
        """Analyze a single keyword"""
        try:
            # Calculate search volume (estimated)
            search_volume = self._estimate_search_volume(keyword, context)
            
            # Determine difficulty
            difficulty = self._calculate_keyword_difficulty(keyword)
            
            # Calculate relevance
            relevance_score = self._calculate_keyword_relevance(keyword, content, context)
            
            # Generate semantic variations
            semantic_variations = self._get_semantic_variations_for_keyword(keyword)
            
            # Determine sentiment association
            sentiment = self._analyze_keyword_sentiment(keyword)
            
            # Check trending status
            is_trending = self._is_keyword_trending(keyword)
            
            # Generate usage suggestions
            usage_suggestions = self._generate_keyword_usage_suggestions(keyword, context)
            
            return KeywordAnalysis(
                keyword=keyword,
                search_volume=search_volume,
                difficulty=difficulty,
                relevance_score=relevance_score,
                semantic_variations=semantic_variations,
                sentiment_association=sentiment,
                trending_status=is_trending,
                suggested_usage=usage_suggestions
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze keyword '{keyword}': {e}")
            return None
    
    def _estimate_search_volume(self, keyword: str, context: SEOAnalysisContext) -> int:
        """Estimate search volume for keyword"""
        # Base volume calculation
        base_volume = 1000
        
        # Length factor
        word_count = len(keyword.split())
        if word_count == 1:
            base_volume *= 3  # Single words have higher volume
        elif word_count == 2:
            base_volume *= 2
        else:
            base_volume *= 1.5  # Long tail keywords
        
        # Keyword category multipliers
        keyword_lower = keyword.lower()
        
        # Commercial intent keywords
        if any(term in keyword_lower for term in self.intent_patterns['commercial']):
            base_volume = int(base_volume * self.keyword_categories['commercial'])
        
        # How-to keywords
        elif any(term in keyword_lower for term in ['how to', 'guide', 'tutorial']):
            base_volume = int(base_volume * self.keyword_categories['how_to'])
        
        # Problem-solving keywords
        elif any(term in keyword_lower for term in ['solve', 'fix', 'problem', 'issue']):
            base_volume = int(base_volume * self.keyword_categories['problem_solving'])
        
        # Industry-specific adjustments
        industry = context.industry_vertical
        if industry:
            industry_multipliers = {
                'technology': 1.5,
                'marketing': 1.3,
                'finance': 1.2,
                'healthcare': 1.1,
                'education': 1.4
            }
            multiplier = industry_multipliers.get(industry.lower(), 1.0)
            base_volume = int(base_volume * multiplier)
        
        # Niche keyword adjustment
        if keyword in context.niche_keywords:
            base_volume = int(base_volume * 0.7)  # Niche keywords have lower volume but higher relevance
        
        return max(10, base_volume)
    
    def _calculate_keyword_difficulty(self, keyword: str) -> KeywordDifficulty:
        """Calculate keyword competition difficulty"""
        # Simplified difficulty calculation
        word_count = len(keyword.split())
        keyword_length = len(keyword)
        
        # Very competitive keywords
        high_competition_terms = [
            'business', 'marketing', 'money', 'success', 'best', 'top',
            'free', 'online', 'digital', 'service', 'product'
        ]
        
        if any(term in keyword.lower() for term in high_competition_terms):
            if word_count <= 2:
                return KeywordDifficulty.VERY_HIGH
            else:
                return KeywordDifficulty.HIGH
        
        # Length-based difficulty
        if word_count == 1 and keyword_length <= 8:
            return KeywordDifficulty.HIGH
        elif word_count == 2 and keyword_length <= 15:
            return KeywordDifficulty.MEDIUM
        elif word_count >= 3:
            return KeywordDifficulty.LOW
        else:
            return KeywordDifficulty.MEDIUM
    
    def _calculate_keyword_relevance(self, keyword: str, content: str, 
                                   context: SEOAnalysisContext) -> float:
        """Calculate keyword relevance to content and context"""
        score = 0.0
        keyword_lower = keyword.lower()
        content_lower = content.lower()
        
        # Direct presence in content
        if keyword_lower in content_lower:
            score += 0.4
        
        # Word overlap with content
        keyword_words = set(keyword_lower.split())
        content_words = set(content_lower.split())
        overlap_ratio = len(keyword_words & content_words) / len(keyword_words)
        score += overlap_ratio * 0.3
        
        # Relevance to niche keywords
        niche_text = ' '.join(context.niche_keywords).lower()
        if keyword_lower in niche_text:
            score += 0.3
        
        niche_words = set(niche_text.split())
        niche_overlap = len(keyword_words & niche_words) / len(keyword_words)
        score += niche_overlap * 0.2
        
        # Target audience relevance
        if context.target_audience:
            audience_words = set(context.target_audience.lower().split())
            audience_overlap = len(keyword_words & audience_words) / len(keyword_words)
            score += audience_overlap * 0.1
        
        # Brand voice alignment
        brand_voice = context.brand_voice
        if brand_voice:
            tone = brand_voice.get('tone', '').lower()
            if tone in keyword_lower:
                score += 0.1
        
        return min(1.0, score)
    
    def _get_semantic_variations_for_keyword(self, keyword: str) -> List[str]:
        """Get semantic variations for a specific keyword"""
        variations = []
        keyword_lower = keyword.lower()
        
        # Direct lookup in semantic relationships
        if keyword_lower in self.semantic_relationships['synonyms']:
            variations.extend(self.semantic_relationships['synonyms'][keyword_lower])
        
        if keyword_lower in self.semantic_relationships['related_terms']:
            variations.extend(self.semantic_relationships['related_terms'][keyword_lower])
        
        # Generate contextual variations
        if ' ' not in keyword:
            variations.extend([
                f"{keyword} tips",
                f"{keyword} guide",
                f"best {keyword}",
                f"{keyword} strategy"
            ])
        
        return list(set(variations))[:10]  # Limit to 10 variations
    
    def _analyze_keyword_sentiment(self, keyword: str) -> str:
        """Analyze sentiment association of keyword"""
        positive_indicators = [
            'best', 'top', 'great', 'amazing', 'excellent', 'success',
            'growth', 'improve', 'optimize', 'win', 'achieve'
        ]
        
        negative_indicators = [
            'problem', 'issue', 'fail', 'worst', 'bad', 'terrible',
            'fix', 'solve', 'mistake', 'error', 'wrong'
        ]
        
        keyword_lower = keyword.lower()
        
        if any(pos in keyword_lower for pos in positive_indicators):
            return 'positive'
        elif any(neg in keyword_lower for neg in negative_indicators):
            return 'negative'
        else:
            return 'neutral'
    
    def _is_keyword_trending(self, keyword: str) -> bool:
        """Check if keyword is currently trending"""
        # Simplified trending detection
        trending_indicators = [
            '2024', '2025', 'new', 'latest', 'trending', 'viral',
            'ai', 'automation', 'remote', 'digital transformation'
        ]
        
        return any(indicator in keyword.lower() for indicator in trending_indicators)
    
    def _generate_keyword_usage_suggestions(self, keyword: str, 
                                          context: SEOAnalysisContext) -> List[str]:
        """Generate usage suggestions for keyword"""
        suggestions = []
        
        # Content type specific suggestions
        content_type = context.content_type
        
        if content_type == SEOContentType.TWEET:
            suggestions.extend([
                f"Use '{keyword}' in the first half of the tweet",
                f"Combine with trending hashtags",
                f"Ask a question including '{keyword}'"
            ])
        
        elif content_type == SEOContentType.THREAD:
            suggestions.extend([
                f"Use '{keyword}' in the first tweet of the thread",
                f"Repeat '{keyword}' 2-3 times throughout the thread",
                f"Include in thread summary"
            ])
        
        elif content_type == SEOContentType.REPLY:
            suggestions.extend([
                f"Use '{keyword}' naturally in conversation",
                f"Reference original post's use of '{keyword}'"
            ])
        
        # General suggestions
        suggestions.extend([
            f"Use naturally in context, avoid keyword stuffing",
            f"Consider semantic variations",
            f"Monitor performance and adjust usage"
        ])
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def optimize_keyword_density(self, content: str, target_keywords: List[str],
                                target_density: float = 0.02) -> str:
        """Optimize keyword density in content"""
        try:
            words = content.split()
            total_words = len(words)
            
            optimized_content = content
            
            for keyword in target_keywords:
                current_count = content.lower().count(keyword.lower())
                current_density = current_count / total_words if total_words > 0 else 0
                
                target_count = int(total_words * target_density)
                
                if current_density < target_density:
                    # Need to add keyword
                    additions_needed = target_count - current_count
                    
                    # Find natural places to insert keyword
                    sentences = content.split('.')
                    for i, sentence in enumerate(sentences):
                        if additions_needed > 0 and len(sentence.strip()) > 20:
                            # Try to insert keyword naturally
                            if keyword.lower() not in sentence.lower():
                                # Insert at the beginning of sentence
                                sentences[i] = f" {keyword} " + sentence
                                additions_needed -= 1
                    
                    optimized_content = '.'.join(sentences)
                
                elif current_density > target_density * 2:  # Too high density
                    # Remove some instances
                    removals_needed = current_count - target_count
                    
                    # Remove from less important positions
                    optimized_content = optimized_content.replace(f" {keyword} ", " ", removals_needed)
            
            return optimized_content.strip()
            
        except Exception as e:
            logger.error(f"Keyword density optimization failed: {e}")
            return content
    
    def generate_keyword_suggestions(self, context: SEOAnalysisContext,
                                   suggestion_count: int = 20) -> List[str]:
        """Generate keyword suggestions based on context"""
        try:
            suggestions = set()
            
            # Add niche keywords
            suggestions.update(context.niche_keywords)
            
            # Generate variations of niche keywords
            for keyword in context.niche_keywords:
                variations = self._generate_morphological_variations(keyword)
                suggestions.update(variations[:3])  # Limit variations per keyword
            
            # Add product category keywords
            suggestions.update(context.product_categories)
            
            # Add audience-based keywords
            if context.target_audience:
                audience_words = context.target_audience.lower().split()
                suggestions.update([word for word in audience_words if len(word) > 3])
            
            # Add trend-based keywords
            if context.trend_context:
                trend_keywords = context.trend_context.get('keywords', [])
                suggestions.update(trend_keywords[:10])
            
            # Add industry-specific keywords
            if context.industry_vertical:
                industry_keywords = self._get_industry_keywords(context.industry_vertical)
                suggestions.update(industry_keywords)
            
            # Filter and prioritize
            filtered_suggestions = [
                kw for kw in suggestions 
                if len(kw.strip()) > 2 and len(kw) <= 50
            ]
            
            return list(set(filtered_suggestions))[:suggestion_count]
            
        except Exception as e:
            logger.error(f"Keyword suggestion generation failed: {e}")
            return []
    
    def _get_industry_keywords(self, industry: str) -> List[str]:
        """Get keywords specific to an industry"""
        industry_keywords = {
            'technology': [
                'software', 'hardware', 'digital', 'innovation', 'automation',
                'ai', 'machine learning', 'data', 'cloud', 'cybersecurity'
            ],
            'marketing': [
                'branding', 'advertising', 'campaign', 'content', 'social media',
                'seo', 'conversion', 'engagement', 'analytics', 'roi'
            ],
            'finance': [
                'investment', 'banking', 'cryptocurrency', 'fintech', 'trading',
                'portfolio', 'wealth', 'insurance', 'loans', 'financial planning'
            ],
            'healthcare': [
                'medical', 'wellness', 'treatment', 'diagnosis', 'therapy',
                'health tech', 'telemedicine', 'pharmaceutical', 'clinical', 'patient care'
            ],
            'education': [
                'learning', 'training', 'curriculum', 'online education', 'e-learning',
                'skills', 'certification', 'academic', 'tutoring', 'knowledge'
            ]
        }
        
        return industry_keywords.get(industry.lower(), [])