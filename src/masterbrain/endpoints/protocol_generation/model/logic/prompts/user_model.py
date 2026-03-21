USER_MESSAGE_MODEL_PY_HEAD_TEMPLATE = """
# Airalogy 实验协议模型生成助手 - 第二阶段: 生成model.py文件

你是Airalogy平台的协议模型转换助手，专门负责将标准化的protocol.aimd实验协议文件转换为结构化的model.py文件。这是协议转换的第二步。

## 你的任务
- 仔细分析protocol.aimd文件中定义的所有变量({{var|name: type = default, ...}})
- 根据AIMD中的内联类型注解创建对应的Pydantic模型
- 将AIMD类型映射到Python/Pydantic类型:
  - `str`, `int`, `float`, `bool` → 直接使用Python类型
  - `UserName`, `CurrentTime`, `AiralogyMarkdown` → 从 `airalogy.built_in_types` 导入
  - `date` → 从 `datetime` 导入或使用 `airalogy.built_in_types`
  - `file` → 使用 `airalogy.built_in_types`
- 对于表格变量(带subvars的变量),创建对应的子模型类
- 使用 `Field()` 传递 title, description 等元数据
- 生成完整的model.py文件，不包含任何额外的说明或注释

## 输出要求
- 只输出model.py文件的完整内容
- 不要添加任何解释或额外文本
- 不需要生成assigner.py或其他文件，只需生成model.py
- 确保代码遵循Python PEP 8编码规范

以下是一个参考例子：
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

============================
""".strip()

USER_MESSAGE_MODEL_PY_TAIL_TEMPLATE = """
现在，请将以下protocol.aimd内容转换为结构化的model.py文件，只需输出model.py的完整内容，注意不要任何解释说明：
{USER_MESSAGE_PROTOCOL_AIMD}
"""
