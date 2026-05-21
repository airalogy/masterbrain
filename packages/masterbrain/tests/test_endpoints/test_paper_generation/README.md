# Paper Generation Tests

测试 paper_generation 端点的完整测试套件。

## 测试文件结构

```
test_paper_generation/
├── __init__.py                    # 模块初始化
├── conftest.py                    # pytest 配置和 fixtures
├── test_types.py                  # 测试数据类型和验证
├── test_logic.py                  # 测试核心逻辑函数
├── test_router.py                 # 测试 API 路由
├── test_integration.py            # 集成测试（需要真实 LLM 调用）
├── README.md                      # 本文件
├── example_input_protocol.md      # 示例输入协议
├── example_output_paper.md        # 示例输出论文
├── test_input_with_ref.json       # 带外部引用搜索的测试输入
└── test_input_without_ref.json    # 不带外部引用搜索的测试输入
```

## 运行测试

### 运行所有测试（不包括集成测试）
```bash
pytest tests/test_endpoints/test_paper_generation/ -v
```

### 只运行单元测试
```bash
pytest tests/test_endpoints/test_paper_generation/test_types.py -v
pytest tests/test_endpoints/test_paper_generation/test_logic.py -v
pytest tests/test_endpoints/test_paper_generation/test_router.py -v
```

### 运行集成测试（需要真实 LLM API）
```bash
pytest tests/test_endpoints/test_paper_generation/test_integration.py -v -m integration
```

### 跳过集成测试
```bash
pytest tests/test_endpoints/test_paper_generation/ -v -m "not integration"
```

## 测试覆盖

### test_types.py
- ✅ 测试 `SupportedModels` 数据类
  - 有效/无效模型名称
  - 默认配置
  - 可选参数（thinking, search）
- ✅ 测试 `PaperGenerationInput` 数据类
  - 输入验证
  - 默认值
  - 多个协议
- ✅ 测试 `PaperGenerationOutput` 数据类
  - 输出格式验证

### test_logic.py
- ✅ 测试 `clean_markdown` 函数
  - 清理转义的换行符
  - 清理转义的制表符
  - 混合转义字符
- ✅ 测试 `generate_paper` 函数
  - 不使用外部搜索生成论文
  - 使用外部搜索生成论文
  - 多个协议输入
  - 输出文件保存
  - 转义字符清理

### test_router.py
- ✅ 测试 `/paper_generation` API 端点
  - 基本功能（有/无外部搜索）
  - 输入验证（无效模型、空协议列表）
  - 多个协议处理
  - 不同模型支持
  - 默认值处理
  - 响应结构验证

### test_integration.py
- ✅ 完整流程测试（需要真实 LLM）
  - 完整论文生成（无搜索）
  - 完整论文生成（有搜索）
  - 多协议集成
  - 输出质量验证

## 测试数据

### example_input_protocol.md
示例输入协议，描述金纳米螺旋桨粒子的合成实验。

### test_input_with_ref.json
```json
{
  "model": { "name": "qwen3.5-flash" },
  "protocol_markdown_list": ["..."],
  "enable_external_reference_search": true
}
```

### test_input_without_ref.json
```json
{
  "model": { "name": "qwen3.5-flash" },
  "protocol_markdown_list": ["..."],
  "enable_external_reference_search": false
}
```

## Fixtures

### client
FastAPI 测试客户端，用于发送 HTTP 请求。

### test_data_dir
测试数据目录的 Path 对象。

### sample_protocol_markdown
加载示例协议 markdown 文本。

### paper_generation_input_with_ref
加载带外部引用搜索的输入配置。

### paper_generation_input_without_ref
加载不带外部引用搜索的输入配置。

### expected_output_paper
加载示例输出论文（用于参考）。

## Mock 策略

### 单元测试（test_logic.py）
使用 `unittest.mock` 模拟所有 LLM 调用：
- `generate_title`
- `generate_introduction`
- `generate_methods`
- `generate_results`
- `generate_discussion`
- `generate_abstract`

### 集成测试（test_integration.py）
使用真实的 LLM API 调用，标记为 `@pytest.mark.integration`。

## 环境变量

运行集成测试需要设置以下环境变量：
```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="your-base-url"  # 可选
export TAVILY_API_KEY="your-tavily-key"  # 如果使用外部搜索
```

## CI/CD 配置

在 CI/CD 管道中，建议跳过集成测试：
```bash
pytest tests/test_endpoints/test_paper_generation/ -m "not integration"
```

## 贡献指南

添加新测试时：
1. 在适当的测试文件中添加测试类/函数
2. 使用描述性的测试名称
3. 添加文档字符串说明测试目的
4. 对于需要 LLM 调用的测试，使用 mock 或标记为 integration
5. 更新本 README 文档

