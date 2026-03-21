USER_MESSAGE_PROTOCOL_HEAD_TEMPLATE = """
# Airalogy 实验协议助手 (V3)

请基于 system prompt 中的 AIMD 规范，将用户输入转换为统一的 `protocol.aimd` 文件。
输出内容只包含协议正文以及必要的 `assigner` 代码块，不要输出解释说明。
""".strip()

USER_MESSAGE_PROTOCOL_TAIL_TEMPLATE = """
## 你的任务

现在,请分析以下内容并生成带有类型注解和嵌入式assigner代码块的标准化protocol.aimd格式:

{USER_MESSAGE_REF_PROTOCOL}

请只提供完整的protocol.aimd内容,不要任何解释说明。按以下工作流程生成:

**第一步:提取变量** — 识别所有可测量/输入值,使用 {{var|name: type}} 注解。
**第二步:识别派生变量** — 找出所有可由其他变量计算得出的值(公式、比值、百分比、分级判断、单位换算等),同样定义为 {{var|...}}。
**第三步:生成assigner代码块** — 对第二步识别的**每一个**派生变量,必须在相关段落后紧跟一个 ```assigner 代码块。没有assigner的派生变量意味着协议不完整。
**第四步:自检** — 完成后扫描全文,如果存在依赖其他变量但缺少 ```assigner 代码块的变量,补上缺失的assigner。

格式要求:
1. 遵循Airalogy平台的protocol.aimd标准格式
2. 所有变量都包含类型注解(使用 {{var|name: type}} 语法)
3. 每个变量ID只能用 {{var|...}} 定义一次，后续引用使用 {{ref_var|...}}
4. 为变量添加合适的默认值和属性(如 title, description, max_length, ge 等)
5. 包括适当的步骤标记({{step}}, {{check}})
6. 字符串默认值使用双引号包裹,数字和布尔值不使用引号
7. **必须**为所有可由其他变量推导的值添加 ```assigner 代码块——包括比值、百分比、分级判断等,即使计算很简单也不能省略
8. 每个assigner函数明确指定 assigned_fields 和 dependent_fields
9. 在引用前文变量或步骤时使用 {{ref_var|...}} 和 {{ref_step|...}} 语法
10. 物理量纲的单位写在自然语言描述中(如"浓度 (μM)")，不使用 unit 参数
11. `subvars` 的简化语法只允许 `name: type = default`，需要额外属性时改用 `var(...)` 子字段写法
12. assigner/quiz/fig 使用代码围栏(```)，**不要**发明 `{{assigner|...}}`、`{{quiz|...}}`、`{{fig|...}}` 等模板标签

**关键模式(必须遵循)** — 派生变量定义后必须紧跟assigner代码块,示例:

长径比：{{var|ratio: float}}
判断标准：≥15为优...
```assigner
from airalogy.assigner import AssignerResult, assigner
@assigner(assigned_fields=["ratio"], dependent_fields=["length", "thickness"], mode="auto")
def calc_ratio(dep: dict) -> AssignerResult:
    return AssignerResult(assigned_fields={{"ratio": dep["length"] / dep["thickness"]}})
```
不要只用文字描述公式而省略assigner代码块。
"""
