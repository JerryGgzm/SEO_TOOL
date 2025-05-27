# API文档

## 概述
Ideation平台提供RESTful API接口，支持用户管理、内容生成、趋势分析等功能。

## 认证
所有API请求需要在请求头中包含认证信息： 

## 端点

### 用户管理
- `GET /api/users` - 获取用户列表
- `POST /api/users` - 创建用户
- `GET /api/users/{id}` - 获取用户详情
- `PUT /api/users/{id}` - 更新用户信息

### 内容管理
- `GET /api/contents` - 获取内容列表
- `POST /api/contents` - 创建内容
- `GET /api/contents/{id}` - 获取内容详情
- `PUT /api/contents/{id}` - 更新内容

### 趋势分析
- `GET /api/trends` - 获取趋势数据
- `POST /api/trends/analyze` - 分析趋势

## 错误处理
API使用标准HTTP状态码，错误响应格式： 