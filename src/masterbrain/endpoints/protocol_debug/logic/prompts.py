"""Protocol debug related prompt templates"""

SYSTEM_MESSAGE_PROTOCOL_DEBUG_PROMPT = """
You are Airalogy Masterbrain, a syntax-checking assistant for the Airalogy platform at Westlake University.
Your task is to identify and fix syntax errors in AIMD (Airalogy Markdown) protocol documents based on the official AIMD syntax specification.
你是 Airalogy 平台的 AIMD 语法检查助手，负责根据官方语法规范识别并修复 protocol.aimd 文件中的语法错误。
""".strip()

USER_MESSAGE_PROTOCOL_DEBUG_TEMPLATE = r"""
你现在是一个 AIMD 语法错误检查助手。接下来我将给你完整的 AIMD 语法规则、完整的 AIMD 文档上下文，以及可能存在语法错误的片段。请根据语法规则检查片段是否有错误。

1. AIMD 语法规则：
===========================================================
{AIMD_SYNTAX}
===========================================================

2. 完整的 AIMD 文档（提供上下文，帮助你理解变量、步骤、检查点之间的关系）：
===========================================================
{FULL_PROTOCOL}
===========================================================

3. 可能存在语法错误的片段：
===========================================================
{SUSPECT_PROTOCOL}
===========================================================

请仔细检查片段中的以下常见错误类型：
- 使用了不存在的模板标签（如 `{{assigner|...}}`、`{{quiz|...}}`、`{{fig|...}}`）
- 变量 ID 重复定义（同一个 var_id 被 `{{var|...}}` 定义了多次，后续应使用 `{{ref_var|...}}`）
- 使用了不支持的参数（如 `unit`）
- `subvars` 简化语法中混入了 kwargs（如 title、description）
- 代码围栏块语法不正确（assigner/quiz/fig/refs 应使用 ``` 代码块）
- 变量类型、默认值、kwargs 格式不正确
- step/check 的参数格式不正确
- 引用了未定义的变量或步骤
- **`assigner` 代码块内部缺少必要组件**（这是非常常见的错误，必须逐项检查）：
  - 缺少 `from airalogy.assigner import AssignerResult, assigner` 导入语句
  - 缺少 `@assigner(...)` 装饰器
  - `@assigner(...)` 装饰器缺少必要参数：`assigned_fields`、`dependent_fields`、`mode`
  - 函数签名不正确（应为 `def func_name(dep: dict) -> AssignerResult:`）
  - 函数未返回 `AssignerResult(assigned_fields={{...}})` 对象
  - `assigned_fields` 或 `dependent_fields` 中引用了未在协议中定义的变量名
- 存在派生变量（由其他变量计算得出的值）但缺少对应的 `assigner` 代码块

你必须严格按照以下 JSON 格式返回结果（不要返回其他任何内容）：

如果片段中**存在**语法错误：
{{"has_errors": true, "fixed_segment": "修正后的完整片段内容", "reason": "列出每处修改及其原因"}}

如果片段中**没有**语法错误：
{{"has_errors": false, "fixed_segment": "", "reason": "该片段语法正确，无需修复。"}}

注意：
- `has_errors` 必须是布尔值 true 或 false
- 当 `has_errors` 为 false 时，`fixed_segment` 必须为空字符串
- 当 `has_errors` 为 true 时，`fixed_segment` 必须包含修正后的完整片段
- `reason` 必须是字符串
""".strip()


AIMD_SYNTAX = r"""
## AIMD 两类语法（关键）

AIMD 有且仅有两类特殊语法，不要发明或混用：

**1. 内联模板标签** — 使用双花括号 `{{...}}` 写在正文中：
- `{{var|...}}` — 定义变量（每个变量 ID 只能定义一次）
- `{{step|...}}` — 定义步骤
- `{{check|...}}` — 定义检查点
- `{{ref_var|...}}` — 引用已定义的变量
- `{{ref_step|...}}` — 引用已定义的步骤
- `{{ref_fig|...}}` — 引用已定义的图表
- `{{cite|...}}` — 引用文献

**2. 代码围栏块** — 使用三个反引号的代码块：
- ` ```assigner ` — 嵌入式 Python 赋值器代码
- ` ```quiz ` — 交互式测验题（YAML 格式）
- ` ```fig ` — 图表定义（YAML 格式）
- ` ```refs ` — BibTeX 格式的参考文献

**绝对不要**发明不存在的模板标签。以下写法全部是**非法的**：
- `{{assigner|...}}`、`{{assigner_...}}`、`{{/assigner...}}`
- `{{quiz|...}}`、`{{quiz_...}}`、`{{/quiz}}`
- `{{fig|...}}`、`{{fig}}`、`{{/fig}}`
- 除上述 7 种内联模板标签以外的任何 `{{something|...}}`

## Variable 语法

### 基本语法

```aimd
{{var|<var_id>}}
{{var|<var_id>: <type>}}
{{var|<var_id>: <type> = <default_value>}}
{{var|<var_id>: <type> = <default_value>, **kwargs}}
```

该语法本质等价于一次抽象的 Python 函数调用：`def var(<var_id>: <type> = <default_value>, **kwargs)`。因此 `default_value` 的引号包裹原则和 Python 完全一致：`str` 类型的默认值必须使用双引号 `""` 包裹，`int`、`float`、`bool` 等类型的默认值不需要引号。

示例：

```aimd
姓名: {{var|name: str}}
年龄: {{var|age: int}}
体重: {{var|weight: float}}
是否通过: {{var|passed: bool}}
姓名: {{var|name: str = "未知", title = "学生姓名", description = "学生的全名", max_length = 50}}
年龄: {{var|age: int = 0, title = "学生年龄", description = "学生的年龄，单位为岁", ge = 0}}
学院: {{var|school: str = "生科院"}}
```

### 变量唯一性（重要）

每个变量 ID 只能用 `{{var|...}}` 定义**一次**。后续所有引用必须使用 `{{ref_var|variable_name}}`。重复定义同一变量 ID 会导致解析错误。

### `<var_id>` 命名规则

- 不得以 `_` 开头
- 多个 `<var_id>` 不得仅通过 `_` 的数量不同进行区分（如 `user_a` 和 `user__a` 被视为重名）
- 遵循 Python 变量命名规则：只能包含字母、数字和下划线，不能以数字开头，不得包含空格
- `var`、`step`、`check` 模板下的 ID 不得重名

### 支持的类型

- Python 内置类型：`str`, `int`, `float`, `bool`, `list`, `dict`, `list[str]` 等
- Airalogy 自定义类型（来自 `airalogy.types`）：
  - `UserName`：自动填充当前用户名
  - `CurrentTime`：自动填充当前时间戳
  - `AiralogyMarkdown`：富文本输入，支持 Markdown 格式
  - `file`：文件上传输入
  - `date`：日期选择器输入
- 类型不使用引号包裹

### 支持的 kwargs 参数

**通用参数（适用于所有类型）：**
- `title`: Optional[str] — 显示标题
- `description`: Optional[str] — 字段描述

**类型特定参数：**
- `str` 类型：`max_length`, `min_length`, `pattern`
- `int`/`float` 类型：`ge`(>=), `le`(<=), `gt`(>), `lt`(<), `multiple_of`

**注意：`unit` 不是支持的参数。** 物理量纲的单位应直接写在协议的自然语言描述中。

正确写法：
```aimd
浓度 (μM): {{var|drug_concentration: float}}
加入 {{var|reagent_volume: float = 10}} mL 试剂。
初始变性: {{var|initial_denat_temp: float = 95}} °C, {{var|initial_denat_time: int = 5}} min
```

### 表格变量（subvars）

**完整语法（子字段需要额外属性时）：**
```aimd
{{var|students: list[Student],
    title="学生信息",
    description="记录学生的姓名和年龄",
    subvars=[
        var(
            name: str = "张三",
            title="学生姓名",
            description="学生的全名",
            max_length=50
        ),
        var(
            age: int = 18,
            title="学生年龄",
            description="学生的年龄，单位为岁",
            ge=0
        )
    ]
}}
```

**简化语法（子字段不需要额外属性时）：**
```aimd
{{var|students: list[Student], subvars=[name: str = "张三", age: int = 18]}}
```

**重要：** 简化语法中每个子字段**只支持** `name: type = default` 格式。**不要**在简化语法的子字段中添加 `title`、`description`、`unit` 等额外属性 — 解析器会将它们误识别为独立的子字段名导致解析失败。如果子字段需要额外属性，请对该子字段使用完整的 `var(...)` 语法。

## Step 语法

```aimd
{{step|<step_id>}}
{{step|<step_id>, <step_level>}}
{{step|<step_id>, <step_level>, check=True}}
{{step|<step_id>, <step_level>, check=True, checked_message="<message>"}}
```

- `<step_level>` 为步骤层级，取值为整数 `1`, `2`, `3`，默认为 `1`
- `check=True` 时会在前端渲染一个 checkbox
- `checked_message` 仅在显式定义 `check=True` 时生效

示例：
```aimd
{{step|step_1}} 步骤一
{{step|step_1_1, 2}} 子步骤 1.1
{{step|step_2, 1, check=True}} 步骤二（带检查）
{{step|step_3, 1, check=True, checked_message="请注意下一步非常重要。"}} 步骤三
```

## Checkpoint 语法

```aimd
{{check|<checkpoint_id>}}
{{check|<checkpoint_id>, checked_message="<message>"}}
```

示例：
```aimd
{{check|prepare_pcr_reaction_on_ice}} 是否在冰上进行 PCR 反应体系的制备。
{{check|check_cell_attachment, checked_message="请确保细胞已充分贴壁。"}}
```

## 引用语法

引用已定义的变量、步骤和图表：

```aimd
{{ref_var|variable_name}}    — 引用已定义的变量值
{{ref_step|step_id}}         — 引用已定义的步骤标签
{{ref_fig|figure_id}}        — 引用已定义的图表编号
```

示例：
```aimd
{{step|preparation}} 试剂准备。
加入 {{var|reagent_volume: float = 10}} mL 试剂。

{{step|analysis}} 分析。
验证 {{ref_step|preparation}} 中的试剂: {{ref_var|reagent_volume}} 已正确加入。
```

## 嵌入式 Assigner 代码块

使用 ` ```assigner ` 代码围栏（**不是** `{{assigner|...}}` 模板标签）：

```assigner
from airalogy.assigner import AssignerResult, assigner

@assigner(
    assigned_fields=["calculated_field"],
    dependent_fields=["input_field_1", "input_field_2"],
    mode="auto",
)
def calculate_function_name(dep: dict) -> AssignerResult:
    result = dep["input_field_1"] + dep["input_field_2"]
    return AssignerResult(
        assigned_fields={"calculated_field": result},
    )
```

Assigner 模式：
- `"auto"`：依赖字段变化时自动触发
- `"manual"`：用户点击按钮手动触发
- `"auto_first"`：首次自动触发，之后手动
- `"auto_readonly"`：自动触发，赋值后禁止手动修改
- `"manual_readonly"`：手动触发，赋值后禁止手动修改

## Quiz 代码块

仅用于教学/考核类协议。使用 ` ```quiz ` 代码围栏（**不是** `{{quiz|...}}` 模板标签），内容为 YAML 格式。

支持题型：`choice`（选择题）、`blank`（填空题）、`open`（问答题）

示例（选择题）：
```quiz
id: quiz_choice_1
type: choice
mode: single
stem: "以下哪项是正确的？"
score: 2
options:
  - key: A
    text: "选项 A"
  - key: B
    text: "选项 B"
answer: A
```

## Figure 代码块

使用 ` ```fig ` 代码围栏（**不是** `{{fig|...}}` 模板标签），内容为 YAML 格式。

```fig
id: fig1
src: "path/to/image.png"
title: "实验装置图"
legend: "图例说明"
```

在正文中引用图表：`{{ref_fig|fig1}}`

## 文献引用

使用 `{{cite|ref_id}}` 在正文中引用，使用 ` ```refs ` 代码围栏放置 BibTeX 格式的参考文献。

多个引用用逗号分隔：`{{cite|ref_id_1,ref_id_2}}`
""".strip()
