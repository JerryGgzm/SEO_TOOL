"""
LLM趋势匹配服务
使用大语言模型进行智能的趋势话题匹配
"""

import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)
from dotenv import load_dotenv
load_dotenv('.env')

@dataclass
class TrendMatch:
    """趋势匹配结果"""
    trend_name: str
    trend_data: Dict[str, Any]
    relevance_score: float
    matching_reasons: List[str]
    semantic_keywords: List[str]

class LLMTrendMatcher:
    """使用LLM进行趋势匹配的服务"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.model_name = "gpt-3.5-turbo"
        
    def match_trends_with_keywords(self, 
                                 trends: List[Dict[str, Any]], 
                                 keywords: List[str],
                                 max_matches: int = 10) -> List[TrendMatch]:
        """
        使用LLM匹配趋势和关键词
        
        Args:
            trends: Twitter趋势数据列表
            keywords: 用户关键词列表  
            max_matches: 最大匹配数量
            
        Returns:
            匹配结果列表，按相关性排序
        """
        try:
            if not trends or not keywords:
                return []
                
            # 构建LLM prompt
            prompt = self._build_matching_prompt(trends, keywords)
            
            # 调用LLM（如果没有LLM客户端，使用规则匹配作为回退）
            if self.llm_client:
                llm_response = self._call_llm(prompt)
                matches = self._parse_llm_response(llm_response, trends)
            else:
                # 回退到增强的规则匹配
                matches = self._enhanced_rule_matching(trends, keywords)
            
            # 限制返回数量并排序
            matches.sort(key=lambda x: x.relevance_score, reverse=True)
            return matches[:max_matches]
            
        except Exception as e:
            logger.error(f"LLM趋势匹配失败: {e}")
            # 回退到简单匹配
            return self._simple_fallback_matching(trends, keywords, max_matches)
    
    def _build_matching_prompt(self, trends: List[Dict[str, Any]], keywords: List[str]) -> str:
        """构建LLM匹配prompt"""
        
        # 格式化趋势数据
        trends_text = []
        for i, trend in enumerate(trends, 1):
            trend_name = trend.get('name', '')
            tweet_volume = trend.get('tweet_volume', 0)
            trends_text.append(f"{i}. {trend_name} (热度: {tweet_volume})")
        
        # 构建prompt
        prompt = f"""
你是一个专业的社交媒体趋势分析师。请分析以下Twitter热门话题，找出与用户关键词最相关的话题。

用户关键词: {', '.join(keywords)}

当前Twitter热门话题:
{chr(10).join(trends_text)}

请按照以下JSON格式返回分析结果，选出最相关的话题（最多{min(10, len(trends))}个）:

```json
{{
  "matches": [
    {{
      "trend_name": "话题名称",
      "relevance_score": 0.85,
      "matching_reasons": ["匹配原因1", "匹配原因2"],
      "semantic_keywords": ["相关语义词1", "相关语义词2"]
    }}
  ]
}}
```

评分标准:
- 1.0: 完全匹配，话题直接相关
- 0.8-0.9: 高度相关，有强烈语义联系
- 0.6-0.7: 相关，有一定语义联系
- 0.4-0.5: 弱相关，有间接联系
- 0.0-0.3: 不相关

请考虑:
1. 直接关键词匹配
2. 语义相关性（同义词、相关概念）
3. 行业关联性
4. 上下文相关性
5. 热度和实用性

只返回JSON格式的结果，不要其他解释。
"""
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """调用LLM获取匹配结果"""
        try:
            # 这里应该调用实际的LLM服务（如OpenAI GPT）
            # 目前返回一个示例响应作为演示
            
            if hasattr(self.llm_client, 'chat'):
                response = self.llm_client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "你是一个专业的趋势分析师。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1000
                )
                return response.choices[0].message.content
            else:
                # 模拟LLM响应
                return self._simulate_llm_response(prompt)
                
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return None
    
    def _simulate_llm_response(self, prompt: str) -> str:
        """模拟LLM响应（用于测试）"""
        # 这是一个简化的模拟响应，实际使用时应该接入真正的LLM
        return '''```json
{
  "matches": [
    {
      "trend_name": "#AI",
      "relevance_score": 0.95,
      "matching_reasons": ["直接匹配AI关键词", "人工智能技术相关"],
      "semantic_keywords": ["人工智能", "机器学习", "深度学习"]
    },
    {
      "trend_name": "#Innovation",
      "relevance_score": 0.80,
      "matching_reasons": ["与创新关键词高度相关", "技术创新概念"],
      "semantic_keywords": ["创新", "技术进步", "革新"]
    }
  ]
}
```'''
    
    def _parse_llm_response(self, llm_response: str, original_trends: List[Dict[str, Any]]) -> List[TrendMatch]:
        """解析LLM响应"""
        try:
            if not llm_response:
                logger.warning("LLM response is empty")
                return []
            
            logger.debug(f"Parsing LLM response: {llm_response[:200]}...")
            
            # 提取JSON部分
            json_start = llm_response.find('```json')
            json_end = llm_response.find('```', json_start + 7)
            
            if json_start == -1 or json_end == -1:
                logger.debug("No JSON code block found, trying to parse entire response")
                # 尝试直接解析整个响应
                response_data = json.loads(llm_response.strip())
            else:
                json_content = llm_response[json_start + 7:json_end].strip()
                logger.debug(f"Extracted JSON content: {json_content}")
                response_data = json.loads(json_content)
            
            matches = []
            for match_data in response_data.get('matches', []):
                trend_name = match_data.get('trend_name', '')
                
                # 更灵活的趋势匹配 - 支持部分匹配
                trend_data = None
                for trend in original_trends:
                    if (trend.get('name', '') == trend_name or 
                        trend_name.lower() in trend.get('name', '').lower() or
                        trend.get('name', '').lower() in trend_name.lower()):
                        trend_data = trend
                        break
                
                # 如果找不到精确匹配，使用第一个趋势作为模板
                if not trend_data and original_trends:
                    logger.warning(f"Could not find exact match for '{trend_name}', using generic trend data")
                    trend_data = {
                        'name': trend_name,
                        'tweet_volume': 10000,  # 默认热度
                        'url': f'https://twitter.com/search?q={trend_name.replace(" ", "+")}'
                    }
                
                if trend_data:
                    match = TrendMatch(
                        trend_name=trend_name,
                        trend_data=trend_data,
                        relevance_score=float(match_data.get('relevance_score', 0.5)),
                        matching_reasons=match_data.get('matching_reasons', []),
                        semantic_keywords=match_data.get('semantic_keywords', [])
                    )
                    matches.append(match)
                    logger.debug(f"Added match: {trend_name} (score: {match.relevance_score})")
            
            logger.info(f"Successfully parsed {len(matches)} matches from LLM response")
            return matches
            
        except Exception as e:
            logger.error(f"解析LLM响应失败: {e}", exc_info=True)
            logger.error(f"原始LLM响应: {llm_response}")
            return []
    
    def _enhanced_rule_matching(self, trends: List[Dict[str, Any]], keywords: List[str]) -> List[TrendMatch]:
        """增强的规则匹配（LLM不可用时的回退方案）"""
        matches = []
        
        # 定义语义关联词典
        semantic_dict = {
            'ai': ['人工智能', 'artificial intelligence', 'machine learning', 'deep learning', 'chatgpt', 'gpt'],
            '智能': ['ai', 'smart', 'intelligent', '人工智能', 'automation'],
            '科技': ['tech', 'technology', 'innovation', '技术', '创新'],
            '创新': ['innovation', 'innovative', '科技', 'tech', 'startup'],
            '效率': ['efficiency', 'productivity', '生产力', 'optimization'],
            '自动化': ['automation', 'automatic', 'ai', '智能', 'bot']
        }
        
        for trend in trends:
            trend_name = trend.get('name', '').lower()
            relevance_score = 0.0
            matching_reasons = []
            semantic_keywords = []
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                # 直接匹配
                if keyword_lower in trend_name:
                    relevance_score += 0.9
                    matching_reasons.append(f"直接匹配关键词: {keyword}")
                    semantic_keywords.append(keyword)
                    continue
                
                # 语义匹配
                if keyword_lower in semantic_dict:
                    for semantic_word in semantic_dict[keyword_lower]:
                        if semantic_word.lower() in trend_name:
                            relevance_score += 0.7
                            matching_reasons.append(f"语义匹配: {keyword} -> {semantic_word}")
                            semantic_keywords.append(semantic_word)
                            break
                
                # 反向匹配
                for semantic_key, semantic_words in semantic_dict.items():
                    if keyword_lower in semantic_words and semantic_key in trend_name:
                        relevance_score += 0.8
                        matching_reasons.append(f"概念匹配: {keyword} -> {semantic_key}")
                        semantic_keywords.append(semantic_key)
            
            # 归一化分数
            relevance_score = min(1.0, relevance_score)
            
            if relevance_score > 0.3:  # 只保留相关度较高的
                match = TrendMatch(
                    trend_name=trend.get('name', ''),
                    trend_data=trend,
                    relevance_score=relevance_score,
                    matching_reasons=matching_reasons,
                    semantic_keywords=semantic_keywords
                )
                matches.append(match)
        
        return matches
    
    def _simple_fallback_matching(self, trends: List[Dict[str, Any]], keywords: List[str], max_matches: int) -> List[TrendMatch]:
        """简单的回退匹配"""
        matches = []
        
        for trend in trends:
            trend_name = trend.get('name', '').lower()
            
            for keyword in keywords:
                if keyword.lower() in trend_name:
                    match = TrendMatch(
                        trend_name=trend.get('name', ''),
                        trend_data=trend,
                        relevance_score=0.5,
                        matching_reasons=[f"简单匹配: {keyword}"],
                        semantic_keywords=[keyword]
                    )
                    matches.append(match)
                    break
        
        return matches[:max_matches]

# 工厂函数
def create_llm_trend_matcher(llm_client=None) -> LLMTrendMatcher:
    """创建LLM趋势匹配器"""
    return LLMTrendMatcher(llm_client) 