# SEO工具完整工作流程演示

这个演示系统展示了从用户注册到内容发布的完整SEO工具工作流程，包括所有核心模块的功能。

## 🚀 快速开始

### 方法1: 一键启动演示 (推荐)
```bash
python start_demo.py
```

### 方法2: 手动运行演示
```bash
# 1. 运行完整演示
python demo_complete_workflow.py --demo

# 2. 运行特定步骤
python demo_complete_workflow.py --step 1

# 3. 环境检查
python demo_complete_workflow.py --setup
```

## 📋 演示流程

### 步骤0: 服务器检查
- 检查API服务器是否运行
- 验证连接状态

### 步骤1: 用户注册/登录
- 用户注册（如果不存在）
- 用户登录获取认证令牌
- 更新产品信息

### 步骤2: Twitter OAuth集成
- 获取Twitter OAuth授权URL
- 处理用户授权回调
- 存储访问令牌

### 步骤3: 趋势分析
- 获取Twitter热门趋势
- 分析趋势数据
- 识别内容机会

### 步骤4: 内容生成
- 生成基础宣传内容
- 创建多个内容变体
- 生成病毒式内容

### 步骤5: SEO优化
- 优化内容关键词
- 生成推荐标签
- 计算SEO评分

### 步骤6: 审核与优化
- 内容质量审核
- 用户决策（批准/编辑/拒绝）
- 内容最终确认

### 步骤7: 调度与发布
- 选择发布方式
- 立即发布或调度发布
- 发布到Twitter

## 🔧 环境配置

### 必需的环境变量

创建 `.env` 文件并填入以下配置：

```env
# Twitter API配置
TWITTER_CLIENT_ID=your_twitter_client_id
TWITTER_CLIENT_SECRET=your_twitter_client_secret
TWITTER_REDIRECT_URI=http://localhost:8000/auth/twitter/callback

# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/ideation_db

# 安全配置
SECRET_KEY=your-secret-key-change-in-production
ENCRYPTION_KEY=your-encryption-key

# AI配置 (可选)
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# 调试模式
DEBUG=true
```

### Twitter API设置

1. 前往 [Twitter Developer Portal](https://developer.twitter.com/)
2. 创建应用程序
3. 获取 Client ID 和 Client Secret
4. 设置回调URL: `http://localhost:8000/auth/twitter/callback`

## 📊 使用说明

### 运行完整演示

```bash
python demo_complete_workflow.py --demo
```

演示将依次执行所有步骤，每步完成后会暂停等待用户确认。

### 运行特定步骤

```bash
# 运行步骤1 (用户注册)
python demo_complete_workflow.py --step 1

# 运行步骤3 (趋势分析)
python demo_complete_workflow.py --step 3
```

可用步骤：
- 0: 服务器检查
- 1: 用户注册/登录
- 2: Twitter OAuth
- 3: 趋势分析
- 4: 内容生成
- 5: SEO优化
- 6: 审核优化
- 7: 调度发布

### 环境检查

```bash
python demo_complete_workflow.py --setup
```

检查所需的环境变量和依赖。

## 🎯 演示特性

### 智能回退机制
- 当API不可用时自动使用模拟数据
- 保证演示流程的连续性

### 交互式体验
- 用户可以在关键步骤做出选择
- 支持内容编辑和发布决策

### 完整日志
- 彩色输出显示进度
- 详细的成功/警告/错误信息

### 灵活配置
- 支持自定义API服务器地址
- 可配置演示参数

## 🔍 故障排除

### 常见问题

**问题1: 服务器启动失败**
```
解决方案:
1. 检查是否安装了uvicorn: pip install uvicorn
2. 确保端口8000未被占用
3. 检查主应用程序文件是否存在
```

**问题2: Twitter授权失败**
```
解决方案:
1. 检查TWITTER_CLIENT_ID和TWITTER_CLIENT_SECRET是否正确
2. 确认回调URL配置正确
3. 检查Twitter应用程序权限设置
```

**问题3: 数据库连接失败**
```
解决方案:
1. 检查数据库是否运行
2. 验证DATABASE_URL配置
3. 确保数据库已创建
```

**问题4: 模块导入错误**
```
解决方案:
1. 确保在项目根目录运行
2. 检查所有依赖是否安装: pip install -r requirements.txt
3. 验证Python路径配置
```

### 日志信息说明

- 🔹 **步骤信息**: 当前执行的步骤
- ✅ **成功**: 操作成功完成
- ⚠️ **警告**: 非致命错误，使用备用方案
- ❌ **错误**: 严重错误，需要用户处理

## 📈 演示数据

演示系统会生成以下示例数据：

### 用户信息
- 邮箱: demo@example.com
- 公司: DemoTech
- 产品: AI智能助手

### 生成内容示例
- 企业级AI助手宣传文案
- 包含相关hashtag
- SEO优化建议

### 趋势数据
- AI技术相关趋势
- 创业公司动态
- 行业热点分析

## 🛠️ 开发与扩展

### 添加新步骤

1. 在 `CompleteWorkflowDemo` 类中添加新方法
2. 更新 `run_complete_demo` 中的步骤列表
3. 添加到 `run_specific_step` 的步骤映射

### 自定义演示数据

修改 `demo_user` 字典中的默认值：

```python
self.demo_user = {
    "email": "your@email.com",
    "product_name": "您的产品名称",
    # ... 其他配置
}
```

### 扩展API客户端

在 `APIClient` 类中添加新的API调用方法。

## 🤝 支持

如有问题或建议，请：

1. 检查本文档的故障排除部分
2. 查看项目日志文件
3. 联系开发团队

---

**注意**: 这是一个演示系统，生产环境使用前请确保所有配置正确，并进行充分测试。 