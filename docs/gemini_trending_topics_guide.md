# Gemini热门话题分析功能使用指南

## 概述

本功能基于Google Gemini LLM和Custom Search API，实现了智能的基于关键词的互联网热门话题分析。用户只需提供关键词（如"AI"、"效率"、"创业"），系统就能返回当前互联网上最相关的热门话题。

## 架构特点

### 两阶段处理机制
1. **推理和委托**：Gemini LLM分析用户关键词并决定搜索策略
2. **执行和合成**：执行网络搜索并由LLM生成最终分析结果

### 核心组件
- `modules/trend_analysis/gemini_analyzer.py` - Gemini LLM集成
- `modules/trend_analysis/web_search_tool.py` - Google Custom Search API集成
- `api/routes/trend_analysis.py` - API端点（新增的Gemini端点）

## 环境配置

### 必需的环境变量
```bash
# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Google Custom Search API
GOOGLE_SEARCH_API_KEY=your_google_search_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
```

### 获取API密钥

#### 1. Gemini API密钥
- 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
- 创建新的API密钥
- 复制密钥并设置为`GEMINI_API_KEY`环境变量

#### 2. Google Search API密钥
- 访问 [Google Cloud Console](https://console.cloud.google.com/)
- 创建新项目或选择现有项目
- 启用"Custom Search API"
- 在"凭据"页面创建API密钥
- 设置为`GOOGLE_SEARCH_API_KEY`环境变量

#### 3. 搜索引擎ID
- 访问 [Programmable Search Engine](https://programmablesearchengine.google.com/)
- 创建新的搜索引擎，配置为搜索整个网络
- 从控制面板复制"搜索引擎ID"
- 设置为`GOOGLE_SEARCH_ENGINE_ID`环境变量

## API端点

### 1. 基本分析 - `/api/trends/gemini/analyze`
**POST请求**

使用Gemini分析关键词并返回热门话题。

**请求参数：**
```json
{
  "keywords": ["AI", "效率", "创业"],
  "user_context": "科技创业者，关注最新技术趋势",
  "max_topics": 5
}
```

**响应示例：**
```json
{
  "success": true,
  "keywords": ["AI", "效率", "创业"],
  "analysis": "基于您的关键词，我找到了以下5个热门话题...",
  "search_query_used": "AI 效率 创业 最新趋势",
  "function_called": "get_trending_topics",
  "has_search_results": true,
  "timestamp": "2024-01-01T12:00:00",
  "user_id": 123
}
```

### 2. 结构化总结 - `/api/trends/gemini/summary`
**POST请求**

获取结构化的热门话题总结，包含标题、描述、相关性评分等。

**请求参数：**
```json
{
  "keywords": ["区块链", "Web3"],
  "max_topics": 3,
  "user_context": "投资者，寻找新兴技术机会"
}
```

### 3. 快速演示 - `/api/trends/gemini/quick-demo`
**GET请求**

使用预设关键词进行快速演示，无需额外参数。

### 4. 配置检查 - `/api/trends/gemini/config-check`
**GET请求**

检查Google API配置状态。

**响应示例：**
```json
{
  "configured": true,
  "config_status": {
    "gemini_api_key": true,
    "google_search_api_key": true,
    "google_search_engine_id": true
  },
  "message": "所有配置完整"
}
```

## 编程接口

### 直接使用Python模块

```python
from modules.trend_analysis import quick_analyze_trending_topics

# 快速分析
result = quick_analyze_trending_topics(
    keywords=["人工智能", "创业"],
    user_context="技术创业者"
)

print(result["analysis"])
```

### 高级用法

```python
from modules.trend_analysis import create_gemini_trend_analyzer

# 创建分析器
analyzer = create_gemini_trend_analyzer()

# 详细分析
result = analyzer.analyze_trending_topics(
    keywords=["效率工具", "SaaS"],
    user_context="产品经理"
)

# 获取结构化总结
summary = analyzer.get_trending_summary(
    keywords=["AI工具"],
    max_topics=5
)
```

### 批量分析

```python
# 批量分析多组关键词
keyword_groups = [
    ["区块链", "DeFi"],
    ["元宇宙", "VR"],
    ["新能源", "电动车"]
]

batch_results = analyzer.batch_analyze_keywords(
    keyword_groups=keyword_groups,
    user_context="投资研究员"
)
```

## 运行演示

项目包含了完整的演示脚本：

```bash
python demo_gemini_trending_topics.py
```

演示脚本会展示：
1. 基本关键词分析
2. 高级分析功能
3. 批量关键词分析
4. 直接网络搜索

## 错误处理

### 常见错误及解决方案

1. **缺少API密钥**
   ```
   错误：缺少Gemini API密钥，请设置GEMINI_API_KEY环境变量
   解决：设置相应的环境变量
   ```

2. **API限制**
   ```
   错误：API调用频率过高
   解决：系统自动在批量处理中添加延迟
   ```

3. **搜索结果为空**
   ```
   错误：未找到相关文章
   解决：尝试更通用的关键词或检查搜索引擎配置
   ```

## 性能优化建议

1. **关键词优化**
   - 使用具体且相关的关键词
   - 避免过于宽泛的词汇
   - 考虑使用中英文混合

2. **批量处理**
   - 使用批量接口处理多组关键词
   - 系统自动处理API限制

3. **缓存策略**
   - 相同关键词的结果可以缓存24小时
   - 考虑在数据库中存储热门分析结果

## 扩展功能

### 计划中的功能
1. 支持更多搜索源（Twitter、Reddit等）
2. 情感分析和话题分类
3. 趋势预测和历史对比
4. 个性化推荐算法

### 自定义扩展
开发者可以：
1. 添加新的搜索工具函数
2. 自定义Gemini提示词
3. 集成其他LLM服务
4. 实现专业领域的分析逻辑

## 注意事项

1. **API成本**：Gemini和Google Search API按使用量计费
2. **速度**：每次分析需要2-3个API调用，耗时约10-30秒
3. **语言**：当前优化为中文搜索，可根据需要调整
4. **准确性**：结果基于搜索内容，质量取决于网络信息的及时性

## 支持与反馈

如有问题或建议，请：
1. 检查配置状态：`GET /api/trends/gemini/config-check`
2. 运行演示脚本验证环境
3. 查看日志输出了解详细错误信息
4. 联系技术支持团队 