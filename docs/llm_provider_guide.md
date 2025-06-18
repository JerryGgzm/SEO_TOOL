# LLM Provider Configuration Guide

## 概述

SEO_TOOL 现在支持多种 LLM 提供商，包括 Gemini 和 OpenAI。系统会自动检测和适配不同的 LLM 响应格式。

## 支持的 LLM 提供商

### 1. Gemini (默认)
- **模型**: `gemini-2.0-flash-lite`
- **特点**: 经常返回 markdown 格式的 JSON
- **解析策略**: 自动移除 markdown 代码块并提取 JSON
- **API 密钥**: `GEMINI_API_KEY`

### 2. OpenAI/GPT
- **模型**: `gpt-4-turbo-preview`
- **特点**: 通常返回干净的 JSON
- **解析策略**: 直接解析，支持 markdown 清理
- **API 密钥**: `OPENAI_API_KEY`

## 配置方法

### 方法 1: 环境变量配置

创建 `.env` 文件：

```bash
# 选择 LLM 提供商
LLM_PROVIDER=gemini  # 或 openai, gpt

# Gemini 配置
GEMINI_API_KEY=your_gemini_api_key_here

# OpenAI 配置
OPENAI_API_KEY=your_openai_api_key_here
```

### 方法 2: 代码中指定

```python
from config.llm_selector import get_llm_client, get_llm_provider

# 自动检测可用的提供商
provider = get_llm_provider()
print(f"Using provider: {provider}")

# 手动指定提供商
llm_client = get_llm_client("openai")
```

## 使用示例

### 基本使用

```python
from modules.seo.llm_intelligence import LLMSEOIntelligence

# 自动检测提供商
llm_client = get_llm_client()
llm_intelligence = LLMSEOIntelligence(llm_client=llm_client)

# 手动指定提供商
llm_client = get_llm_client("openai")
llm_intelligence = LLMSEOIntelligence(
    llm_client=llm_client,
    llm_provider="openai"
)
```

### 提供商比较

```python
async def compare_providers():
    providers = ["gemini", "openai"]
    
    for provider in providers:
        llm_client = get_llm_client(provider)
        if llm_client:
            llm_intelligence = LLMSEOIntelligence(
                llm_client=llm_client,
                llm_provider=provider
            )
            # 测试优化功能
            result = await llm_intelligence.optimize_content(
                "Working on new AI features"
            )
            print(f"{provider}: {result}")
```

## 响应格式适配

### Gemini 响应处理

Gemini 经常返回这样的格式：
```markdown
```json
{
  "seo_score": 85,
  "keywords": ["AI", "productivity"]
}
```
```

系统会自动：
1. 移除 markdown 代码块标记
2. 提取 JSON 内容
3. 验证 JSON 格式
4. 返回清理后的 JSON

### OpenAI 响应处理

OpenAI 通常返回干净的 JSON：
```json
{
  "seo_score": 85,
  "keywords": ["AI", "productivity"]
}
```

系统会：
1. 直接解析 JSON
2. 如果失败，尝试清理 markdown 格式
3. 使用正则表达式提取 JSON

## 错误处理

### 常见问题

1. **API 密钥未设置**
   ```
   ❌ Gemini API key not found. Set GEMINI_API_KEY in your .env file
   ```

2. **包未安装**
   ```
   ❌ Google Generative AI package not installed. Install with: pip install google-generativeai
   ```

3. **JSON 解析失败**
   ```
   Failed to parse LLM JSON response: Expecting value: line 1 column 1 (char 0)
   ```

### 解决方案

1. **设置 API 密钥**
   ```bash
   # 在 .env 文件中设置
   GEMINI_API_KEY=your_key_here
   OPENAI_API_KEY=your_key_here
   ```

2. **安装依赖**
   ```bash
   pip install google-generativeai openai
   ```

3. **检查提供商配置**
   ```python
   from config.llm_selector import is_llm_available
   
   if is_llm_available("gemini"):
       print("Gemini is available")
   ```

## 性能优化

### 提供商选择建议

- **Gemini**: 适合快速原型和测试，免费额度较大
- **OpenAI**: 适合生产环境，响应质量较高
- **自动检测**: 系统会根据可用的 API 密钥自动选择

### 缓存策略

```python
# 缓存 LLM 客户端实例
llm_client = get_llm_client()
llm_intelligence = LLMSEOIntelligence(llm_client=llm_client)

# 重用同一个实例进行多次优化
for content in content_list:
    result = await llm_intelligence.optimize_content(content)
```

## 测试和验证

运行提供商比较测试：

```bash
python modules/seo/demo_seo.py
```

这将：
1. 测试所有可用的提供商
2. 比较 JSON 响应格式
3. 验证解析功能
4. 显示性能对比

## 故障排除

### 检查提供商状态

```python
from config.llm_selector import llm_selector

# 检查所有可用提供商
available = llm_selector.get_available_providers()
print(f"Available providers: {available}")

# 验证特定提供商
is_valid, message = llm_selector.validate_provider_setup("gemini")
print(f"Gemini setup: {message}")
```

### 调试模式

启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 现在会显示详细的 LLM 响应和解析过程
```

## 最佳实践

1. **环境变量管理**: 使用 `.env` 文件管理 API 密钥
2. **提供商检测**: 让系统自动检测可用的提供商
3. **错误处理**: 实现适当的错误处理和回退机制
4. **性能监控**: 监控不同提供商的响应时间和成功率
5. **成本控制**: 根据使用场景选择合适的提供商 