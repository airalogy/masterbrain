# Protocol Debug 测试模块

本模块包含对 `protocol_debug` 功能的全面测试，包括单元测试、集成测试和端到端测试。

## 测试结构

```
test_protocol_debug/
├── __init__.py                 # 模块初始化文件
├── conftest.py                 # 测试配置和fixtures
├── demo_protocol_debug_input.json  # 测试输入数据
├── demo_protocol_debug_output.txt  # 测试输出数据
├── test_router.py              # 路由测试
├── test_types.py               # 类型定义测试
├── test_logic.py               # 业务逻辑测试
├── test_integration.py         # 集成测试
└── README.md                   # 本文件
```

## 测试覆盖范围

### 1. 路由测试 (`test_router.py`)
- 测试 `/protocol_debug` 端点的基本功能
- 验证响应状态码和结构
- 测试边界情况（如空的 suspect_protocol）
- 测试无效输入的处理

### 2. 类型测试 (`test_types.py`)
- 测试 `SupportedModels` 类的验证逻辑
- 测试 `ProtocolDebugInput` 类的字段验证
- 验证默认值和可选字段
- 测试无效数据的错误处理

### 3. 逻辑测试 (`test_logic.py`)
- 测试 `generate_debug_result` 函数的核心逻辑
- 模拟LLM客户端的响应
- 测试各种输入场景
- 验证超时设置和模型配置

### 4. 集成测试 (`test_integration.py`)
- 测试完整的协议调试流程
- 测试不同模型配置
- 测试错误处理和边界情况
- 验证响应一致性

## 测试数据

### 输入数据 (`demo_protocol_debug_input.json`)
包含一个完整的金三角形纳米片合成协议，用于测试协议调试功能。

### 输出数据 (`demo_protocol_debug_output.txt`)
包含预期的调试结果，包括修正后的协议片段和修复说明。

## 运行测试

### 运行所有测试
```bash
pytest tests/test_endpoints/test_protocol_debug/
```

### 运行特定测试文件
```bash
pytest tests/test_endpoints/test_protocol_debug/test_router.py
pytest tests/test_endpoints/test_protocol_debug/test_types.py
pytest tests/test_endpoints/test_protocol_debug/test_logic.py
pytest tests/test_endpoints/test_protocol_debug/test_integration.py
```

### 运行特定测试类
```bash
pytest tests/test_endpoints/test_protocol_debug/test_types.py::TestSupportedModels
pytest tests/test_endpoints/test_protocol_debug/test_logic.py::TestGenerateDebugResult
```

### 运行特定测试方法
```bash
pytest tests/test_endpoints/test_protocol_debug/test_types.py::TestSupportedModels::test_valid_model_names
```

## 测试配置

测试使用 `conftest.py` 中的 fixtures：
- `client`: FastAPI 测试客户端
- `sample_protocol_debug_input`: 示例输入数据

## 注意事项

1. **异步测试**: 逻辑测试使用 `@pytest.mark.asyncio` 装饰器
2. **模拟**: 使用 `unittest.mock` 模拟外部依赖
3. **数据验证**: 测试包含输入验证和输出结构验证
4. **错误处理**: 测试覆盖各种错误场景和边界情况

## 维护

- 当 `protocol_debug` 模块的接口或逻辑发生变化时，需要相应更新测试
- 添加新的测试用例时，请确保遵循现有的测试模式和命名约定
- 定期检查测试覆盖率，确保所有关键功能都有测试覆盖
