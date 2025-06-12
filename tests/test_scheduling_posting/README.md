# Scheduling & Posting Module Tests

这是 `scheduling_posting` 模块的完整测试套件，包含单元测试、集成测试和性能测试。

## 测试结构

```
tests/test_scheduling_posting/
├── conftest.py                        # 测试配置和夹具
├── test_scheduling_service.py         # 调度服务单元测试
├── test_rules_engine.py              # 规则引擎单元测试
├── test_models.py                     # 数据模型测试
├── test_publishing_integration.py    # 端到端集成测试
├── test_performance.py               # 性能和负载测试
├── test_runner.py                     # 测试运行器脚本
├── __init__.py                        # 测试包初始化
└── README.md                          # 本文档
```

## 测试类别

### 1. 单元测试
- **test_scheduling_service.py**: 测试 `SchedulingPostingService` 的所有方法
- **test_rules_engine.py**: 测试 `InternalRulesEngine` 的规则验证逻辑
- **test_models.py**: 测试数据模型的验证、序列化和属性

### 2. 集成测试
- **test_publishing_integration.py**: 测试端到端的发布工作流程，包括调度、发布、错误处理等完整场景

### 3. 性能测试
- **test_performance.py**: 测试批量操作性能、并发处理能力、内存使用等

## 快速开始

### 安装依赖

```bash
pip install pytest pytest-asyncio pytest-cov psutil
```

### 运行所有测试

```bash
# 使用测试运行器
python tests/test_scheduling_posting/test_runner.py --all

# 或直接使用 pytest
pytest tests/test_scheduling_posting/ -v
```

### 运行特定类别的测试

```bash
# 单元测试
python tests/test_scheduling_posting/test_runner.py --unit

# 集成测试
python tests/test_scheduling_posting/test_runner.py --integration

# 性能测试
python tests/test_scheduling_posting/test_runner.py --performance

# 快速测试（不包括性能测试）
python tests/test_scheduling_posting/test_runner.py --fast
```

### 生成覆盖率报告

```bash
python tests/test_scheduling_posting/test_runner.py --coverage
```

## 测试夹具说明

### 主要夹具

- `scheduling_service`: 完整配置的调度服务实例
- `mock_data_flow_manager`: 模拟的数据流管理器
- `mock_twitter_client`: 模拟的Twitter客户端
- `mock_user_profile_service`: 模拟的用户配置服务
- `test_user_id`: 测试用户ID
- `test_content_id`: 测试内容ID
- `setup_test_data`: 预配置的测试数据

### 辅助函数

- `create_content_drafts()`: 创建多个内容草稿
- `create_scheduled_content()`: 创建预定内容
- `wait_for_condition()`: 等待条件满足

## 测试覆盖范围

### 核心功能测试
- ✅ 内容调度 (立即和预定)
- ✅ 批量操作 (调度和发布)
- ✅ 发布规则验证
- ✅ 队列处理
- ✅ 错误处理和重试
- ✅ 分析和历史记录

### 边界情况测试
- ✅ 无效输入验证
- ✅ 权限检查
- ✅ 并发操作
- ✅ 网络错误
- ✅ 数据库故障
- ✅ 资源限制

### 性能测试
- ✅ 批量操作性能
- ✅ 并发处理能力
- ✅ 内存使用监控
- ✅ 错误处理性能影响
- ✅ 可扩展性模拟

## 示例用法

### 运行单个测试
```bash
pytest tests/test_scheduling_posting/test_scheduling_service.py::TestSchedulingService::test_schedule_content_success -v
```

### 运行特定标记的测试
```bash
pytest tests/test_scheduling_posting/ -m "asyncio" -v
```

### 运行失败的测试
```bash
python tests/test_scheduling_posting/test_runner.py --failed
```

### 烟雾测试（快速验证）
```bash
python tests/test_scheduling_posting/test_runner.py --smoke
```

## Mock 对象说明

### MockDataFlowManager
提供所有数据访问方法的模拟实现，包括：
- 内容草稿管理
- 调度内容管理
- 用户偏好设置
- 分析数据

### MockTwitterClient
模拟Twitter API客户端：
- 可控制成功/失败状态
- 记录API调用
- 生成模拟tweet ID

### MockUserProfileService
模拟用户配置服务：
- 管理访问令牌
- 用户权限检查

## 性能基准

### 批量操作基准
- 100个内容调度: < 30秒
- 50个内容发布: < 60秒
- 20个并发调度: < 10秒
- 15个并发发布: < 15秒

### 规则检查基准
- 100次规则检查: < 5秒
- 1000次文本相似度计算: < 1秒

### 内存使用基准
- 200个内容批量操作: 内存增长 < 100MB

## 故障排除

### 常见问题

1. **导入错误**
   ```
   ModuleNotFoundError: No module named 'modules.scheduling_posting'
   ```
   确保项目根目录在Python路径中，或从项目根目录运行测试。

2. **异步测试失败**
   ```
   RuntimeError: Event loop is closed
   ```
   确保安装了 `pytest-asyncio` 并正确配置。

3. **性能测试超时**
   某些性能测试可能在较慢的机器上超时，可以调整测试中的时间限制。

### 调试技巧

1. **详细输出**
   ```bash
   pytest tests/test_scheduling_posting/ -v -s
   ```

2. **停在第一个失败**
   ```bash
   pytest tests/test_scheduling_posting/ -x
   ```

3. **显示完整回溯**
   ```bash
   pytest tests/test_scheduling_posting/ --tb=long
   ```

## 贡献指南

### 添加新测试

1. 选择适当的测试文件
2. 使用现有夹具
3. 遵循命名约定: `test_功能_场景`
4. 添加适当的文档字符串
5. 确保测试独立性

### 测试最佳实践

1. **使用描述性的测试名称**
   ```python
   def test_schedule_content_with_invalid_time_should_fail(self):
   ```

2. **遵循 AAA 模式**
   ```python
   # Arrange - 准备测试数据
   # Act - 执行被测试的操作  
   # Assert - 验证结果
   ```

3. **一个测试只验证一个功能**

4. **使用适当的断言消息**
   ```python
   assert result.success, f"Expected success but got: {result.message}"
   ```

## 持续集成

这些测试可以集成到CI/CD流水线中：

```yaml
# GitHub Actions 示例
- name: Run Tests
  run: |
    python tests/test_scheduling_posting/test_runner.py --all
    
- name: Run Performance Tests
  run: |
    python tests/test_scheduling_posting/test_runner.py --performance
```

## 许可证

这些测试与主项目使用相同的许可证。 