USER_MESSAGE_ASSIGNER_PY_HEAD_TEMPLATE = """
# Airalogy Assigner Generator - 第三阶段: 生成assigner.py文件

你是一位科学实验专家，负责协助实验流程的自动化处理。你的任务是分析已有的protocol.aimd文件与model.py内容，然后仅生成相应的assigner.py文件。

注意: 这是Airalogy实验协议处理流程的第三阶段，前两阶段(生成protocol.aimd和model.py)已经完成。你只需专注于生成assigner.py文件。

assigner.py文件的作用是定义变量间的依赖关系和自动计算逻辑，确保实验参数的一致性和准确性。

## 何时必须生成Assigner方法(重要):

以下任一情况出现时,你**必须**生成对应的assigner函数:

- 某个变量的值可以由其他变量**推导或计算**得出(如比值、求和、差值、百分比、单位换算)
- 协议文本中包含**公式或计算指令**(如"计算X"、"X = A ÷ B"、"求比值")
- 某个变量是**派生指标**,例如:抑制率、产率、稀释后浓度、长径比、效率、纯度、回收率等
- 协议要求根据阈值对结果进行**分类或分级**(如"比值≥15为优")

即使计算很简单也不要省略。只要一个变量依赖于其他变量,就必须有对应的assigner函数。
如果协议中没有任何可计算的派生变量，则生成一个只包含导入语句的空文件。

## Assigner语法

使用模块级函数式语法（不要使用已废弃的 class Assigner(AssignerBase) 类语法）:

```python
from airalogy.assigner import AssignerResult, assigner

@assigner(
    assigned_fields=["calculated_field"],
    dependent_fields=["input_field_1", "input_field_2"],
    mode="auto",
)
def calculate_function_name(dependent_fields: dict) -> AssignerResult:
    val_1 = dependent_fields["input_field_1"]
    val_2 = dependent_fields["input_field_2"]
    result = val_1 + val_2
    return AssignerResult(
        assigned_fields={"calculated_field": result},
    )
```

### 关键要素:
1. 从 `airalogy.assigner` 导入 `AssignerResult` 和 `assigner`
2. 使用 `@assigner` 装饰器，明确指定 `assigned_fields`、`dependent_fields` 和 `mode`
3. 函数参数固定为 `dependent_fields: dict`，返回值为 `AssignerResult`
4. `mode` 可选值: `"auto"` (自动触发), `"manual"` (手动触发), `"auto_first"` (仅首次自动), `"auto_readonly"`, `"manual_readonly"`
5. 对于 Variable Table 中的子变量计算，使用 `"table_name.subvar_name"` 格式的字段名

## 参考示例

以下是一个完整的参考示例，展示了protocol.aimd、model.py与对应的assigner.py之间的关系：

============================
protocol.aimd:
# Alice's Protocol

**Objective:** Evaluate the inhibitory effect of a drug on tumor cell proliferation using the CCK-8 assay.

## Basic Information

Experimenter Name: {{var|experimenter_name: UserName}}
Experiment Date: {{var|experiment_date: date}}
Experiment Time: {{var|experiment_time: CurrentTime}}
Experiment Notes: {{var|notes: AiralogyMarkdown}}

## Experimental Steps

{{step|cell_seeding}} Cell Seeding.

Seed {{var|cell_line_name: str = "HeLa"}} cells at a density of {{var|seeding_density: int = 5000}} cells/well into a 96-well plate—with control and treatment groups.
Incubate for {{var|adhesion_time: float = 12}} h to allow cells to adhere.

{{check|check_cell_attachment}} Before proceeding, ensure that the cells have adequately adhered and are in good condition.

{{step|drug_treatment}} Drug Treatment.

Prepare an aqueous solution of the drug {{var|drug_name: str}} at a concentration of {{var|drug_concentration: float}} μM.
Treat the {{ref_var|cell_line_name}} cells prepared in {{ref_step|cell_seeding}} with the drug solution.
Leave the control group untreated.
Incubate for {{var|treatment_duration: float = 24}} h.

Drug per well (nmol): {{var|drug_per_well_nmol: float, title = "Drug Amount Per Well"}}

{{step|cell_viability_assay}} Cell Viability Assay.

Add the CCK-8 reagent according to the manufacturer's instructions and incubate accordingly.
Record the optical density (OD) readings for each sample:
{{var|od_readings, subvars=[sample_id: str, group: str = "control", od_value: float]}}

{{step|calculate_inhibition_rate}} Calculate Inhibition Rate.

Based on the OD data from {{ref_step|cell_viability_assay}}:
- Average Control Group OD: {{var|avg_control_od: float, title = "Average Control OD"}}
- Average Treatment Group OD: {{var|avg_treatment_od: float, title = "Average Treatment OD"}}

Inhibition Rate (%): {{var|inhibition_rate: float}}
Formula: Inhibition Rate = [1 - (Average Treatment OD ÷ Average Control OD)] × 100%


model.py:
from datetime import date

from pydantic import BaseModel, Field

from airalogy.built_in_types import AiralogyMarkdown, CurrentTime, UserName


class OdReading(BaseModel):
    sample_id: str
    group: str = "control"
    od_value: float


class VarModel(BaseModel):
    experimenter_name: UserName
    experiment_date: date
    experiment_time: CurrentTime
    notes: AiralogyMarkdown = ""
    cell_line_name: str = "HeLa"
    seeding_density: int = 5000
    adhesion_time: float = 12
    drug_name: str
    drug_concentration: float
    treatment_duration: float = 24
    drug_per_well_nmol: float
    od_readings: list[OdReading] = []
    avg_control_od: float = Field(title="Average Control OD")
    avg_treatment_od: float = Field(title="Average Treatment OD")
    inhibition_rate: float


assigner.py:
from airalogy.assigner import AssignerResult, assigner


@assigner(
    assigned_fields=["drug_per_well_nmol"],
    dependent_fields=["drug_concentration"],
    mode="auto",
)
def calculate_drug_per_well(dependent_fields: dict) -> AssignerResult:
    concentration_uM = dependent_fields["drug_concentration"]
    volume_mL = 0.1  # 100 μL per well
    drug_nmol = concentration_uM * volume_mL
    return AssignerResult(
        assigned_fields={"drug_per_well_nmol": round(drug_nmol, 2)},
    )


@assigner(
    assigned_fields=["inhibition_rate"],
    dependent_fields=[
        "avg_control_od",
        "avg_treatment_od",
    ],
    mode="auto",
)
def calculate_inhibition_rate(dependent_fields: dict) -> AssignerResult:
    avg_control_od = dependent_fields["avg_control_od"]
    avg_treatment_od = dependent_fields["avg_treatment_od"]
    inhibition_rate = (1 - (avg_treatment_od / avg_control_od)) * 100
    return AssignerResult(
        assigned_fields={
            "inhibition_rate": round(inhibition_rate, 2),
        },
    )

============================

## 生成指南

在assigner.py文件中：
1. 使用模块级函数式语法（@assigner 装饰器 + 普通函数），不要使用已废弃的 class Assigner(AssignerBase) 类语法
2. 每个assigner函数应关注特定的变量计算逻辑
3. 明确指定assigned_fields（被计算的字段）和dependent_fields（计算所依赖的字段）
4. 确保所有数值计算准确，逻辑清晰
5. 返回结果必须使用AssignerResult格式，包含assigned_fields字典

**工作流程:**
1. 扫描protocol.aimd中的所有公式、计算指令和派生变量
2. 对每个派生变量生成一个assigner函数
3. 自检：确认没有遗漏任何可计算的变量

请仔细分析protocol.aimd和model.py中的变量关系及其计算逻辑，只生成assigner.py内容，不需要再创建或修改protocol.aimd和model.py文件。
""".strip()

USER_MESSAGE_ASSIGNER_PY_TAIL_TEMPLATE = """
请根据以下protocol.aimd和model.py内容，生成对应的assigner.py文件（不需要修改或重新创建protocol.aimd和model.py）：

## protocol.aimd:
{USER_MESSAGE_PROTOCOL_AIMD}

## model.py:
{USER_MESSAGE_PROTOCOL_MODEL}

## 请直接生成完整的assigner.py文件内容，注意不要任何解释说明:
"""
