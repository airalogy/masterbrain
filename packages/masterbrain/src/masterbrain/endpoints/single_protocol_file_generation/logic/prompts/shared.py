COMMON_OUTPUT_RULES = """
## Output Rules

- Return only the final complete `protocol.aimd` content.
- Do not add explanations, reasoning, preambles, summaries, or any text outside the protocol itself.
- Do not wrap the entire response in an extra outer Markdown code fence unless the protocol content itself requires one.
- Do not use a `unit` parameter in `{{var|...}}`. Write physical units directly in the surrounding natural-language text.
- Each variable ID may only be defined once with `{{var|...}}`. To reference a previously defined variable later in the protocol, use `{{ref_var|variable_name}}` instead. Duplicate `{{var|...}}` definitions for the same ID will cause a parsing error.
""".strip()


COMMON_AIMD_SPEC = """
## AIMD Syntax Specification

### Two Syntax Categories (CRITICAL)

AIMD has exactly two kinds of special syntax. Do not invent or mix them:

**1. Inline template tags** — written inline in the text using double braces `{{...}}`:
- `{{var|...}}` — define a variable (use each ID only ONCE)
- `{{step|...}}` — define a step
- `{{check|...}}` — define a checkpoint
- `{{ref_var|...}}` — reference a previously defined variable
- `{{ref_step|...}}` — reference a previously defined step
- `{{ref_fig|...}}` — reference a previously defined figure
- `{{cite|...}}` — cite a reference

**2. Code fence blocks** — written as fenced code blocks using triple backticks:
- ` ```assigner ` — embedded Python assigner code
- ` ```quiz ` — interactive quiz (YAML)
- ` ```fig ` — figure definition (YAML)
- ` ```refs ` — bibliography in BibTeX format

**NEVER** invent template tags that do not exist. The following are all INVALID:
- `{{assigner|...}}`, `{{assigner_calculation}}`, `{{/assigner...}}`
- `{{quiz|...}}`, `{{quiz_...}}`, `{{/quiz}}`
- `{{fig|...}}`, `{{fig}}`, `{{/fig}}`
- Any other `{{something|...}}` beyond the six listed above

### Basic Variable Syntax

Use Python-like type annotations directly inside `{{var|...}}`:

```aimd
姓名: {{var|name: str}}
年龄: {{var|age: int}}
体重: {{var|weight: float}}
是否通过: {{var|passed: bool}}
```

### Defaults and Field Properties

You may add default values, titles, descriptions, and validation constraints:

```aimd
姓名: {{var|name: str = "未知", title = "学生姓名", description = "学生的全名", max_length = 50}}
年龄: {{var|age: int = 0, title = "学生年龄", description = "学生的年龄,单位为岁", ge = 0}}
学院: {{var|school: str = "生科院"}}
```

Rules:
- String defaults must use double quotes.
- Numeric defaults do not use quotes.
- Boolean defaults use `True` or `False`.

### Variable Uniqueness

Each variable ID may only be defined ONCE with `{{var|...}}`. All subsequent mentions must use `{{ref_var|variable_name}}`. Defining the same variable ID twice is a parsing error.

### Table Variables with `subvars`

For table-like variables with multiple columns:

**Full syntax (when a subvar needs extra properties):**
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
            description="学生的年龄,单位为岁",
            ge=0
        )
    ]
}}
```

**Simplified syntax (when subvars do not need extra properties):**
```aimd
{{var|students: list[Student], subvars=[name: str = "张三", age: int = 18]}}
```

**Important:** In simplified syntax, each subvar only supports `name: type = default`. Do not add kwargs such as `title`, `description`, or `unit` inside simplified `subvars`, or the parser will treat them as separate subvar names and fail. If a subvar needs extra properties, use the full `var(...)` syntax for that subvar.

### Supported Types

- Python built-in types: `str`, `int`, `float`, `bool`, `list`, `dict`, `list[str]`
- Airalogy built-in types from `airalogy.types`:
  - `UserName`
  - `CurrentTime`
  - `AiralogyMarkdown`
  - `file`
  - `date`

### Supported Field Parameters

Common parameters:
- `title`
- `description`

Type-specific parameters:
- For `str`: `max_length`, `min_length`, `pattern`
- For `int` / `float`: `ge`, `le`, `gt`, `lt`, `multiple_of`

### Unit Handling

Physical units must be written in the surrounding natural-language text, not as a variable parameter.

Correct:
```aimd
浓度 (μM): {{var|drug_concentration: float}}
加入 {{var|reagent_volume: float = 10}} mL 试剂。
初始变性: {{var|initial_denat_temp: float = 95}} °C, {{var|initial_denat_time: int = 5}} min
```

Do not attach units as kwargs inside `{{var|...}}`. `unit` is not a supported parameter.
""".strip()


COMMON_BLOCK_SPEC = """
## Assigner, Reference, Quiz, and Figure Syntax

### Embedded Assigner Blocks

Use ` ```assigner ` code fences for assigner blocks. Do NOT use template tags like `{{assigner|...}}`.

Whenever a variable can be derived from other variables, you must generate an inline assigner block immediately after the relevant section:

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

Generate an assigner block whenever any of the following is true:
- A value is derived from other variables
- The protocol contains a formula or calculation instruction
- A variable is a derived metric such as inhibition rate, yield, recovery, purity, efficiency, aspect ratio, or diluted concentration
- A result must be classified or graded using thresholds

Do not omit an assigner block just because the calculation looks simple.

### Inline References

Use inline tags to reference previously defined items:

```aimd
{{ref_var|variable_name}}
{{ref_step|step_id}}
{{ref_fig|figure_id}}
```

Example:
```aimd
{{step|preparation}} Sample Preparation.
Add {{var|reagent_volume: float = 10}} mL of reagent.

{{step|analysis}} Analysis.
Verify the reagent from {{ref_step|preparation}}: {{ref_var|reagent_volume}} should be correctly dispensed.
```

### Quiz Blocks (educational protocols only)

Only generate quiz blocks for educational, training, or exam-oriented protocols. Do NOT generate quiz blocks for standard laboratory SOP-style protocols unless the user clearly asks for them.

Use ` ```quiz ` code fences (NOT `{{quiz|...}}` template tags):

```quiz
id: quiz_choice_1
type: choice
mode: single
stem: "What is the correct answer?"
score: 2
options:
  - key: A
    text: "Option A"
  - key: B
    text: "Option B"
answer: B
```

### Figure Blocks

Use ` ```fig ` code fences (NOT `{{fig|...}}` or `{{fig}}` template tags):

```fig
id: fig1
src: "path/to/image.png"
title: "Experiment Setup"
legend: "Figure caption describing the image"
```

Reference a figure inline with `{{ref_fig|fig1}}`.
""".strip()


REFERENCE_PROTOCOL_EXAMPLE = """
## Reference Example

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

Seed {{var|cell_line_name: str = "HeLa"}} cells at a density of {{var|seeding_density: int = 5000}} cells/well into a 96-well plate with control and treatment groups.
Incubate for {{var|adhesion_time: float = 12}} h to allow cells to adhere.

{{check|check_cell_attachment}} Before proceeding, ensure that the cells have adequately adhered and are in good condition.

{{step|drug_treatment}} Drug Treatment.

Prepare an aqueous solution of the drug {{var|drug_name: str}} at a concentration of {{var|drug_concentration: float}} μM.
Treat the {{ref_var|cell_line_name}} cells prepared in {{ref_step|cell_seeding}} with the drug solution.
Leave the control group untreated.
Incubate for {{var|treatment_duration: float = 24}} h.

Total drug per well (nmol): {{var|drug_per_well_nmol: float, title = "Drug Amount Per Well"}}

```assigner
from airalogy.assigner import AssignerResult, assigner

@assigner(
    assigned_fields=["drug_per_well_nmol"],
    dependent_fields=["drug_concentration"],
    mode="auto",
)
def calculate_drug_per_well(dep: dict) -> AssignerResult:
    concentration_uM = dep["drug_concentration"]
    volume_mL = 0.1  # 100 μL per well
    drug_nmol = concentration_uM * volume_mL
    return AssignerResult(
        assigned_fields={"drug_per_well_nmol": round(drug_nmol, 2)},
    )
```

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

```assigner
from airalogy.assigner import AssignerResult, assigner

@assigner(
    assigned_fields=["inhibition_rate"],
    dependent_fields=["avg_control_od", "avg_treatment_od"],
    mode="auto",
)
def calculate_inhibition_rate(dep: dict) -> AssignerResult:
    avg_control_od = dep["avg_control_od"]
    avg_treatment_od = dep["avg_treatment_od"]
    inhibition_rate = (1 - (avg_treatment_od / avg_control_od)) * 100
    return AssignerResult(
        assigned_fields={"inhibition_rate": round(inhibition_rate, 2)},
    )
```

============================
""".strip()
