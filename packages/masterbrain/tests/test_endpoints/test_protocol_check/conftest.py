"""
Configuration for Protocol Check tests.
"""

import pytest

from masterbrain.endpoints.protocol_check.types import (
    ProtocolCheckInput,
    SupportedModels,
)


def pytest_configure(config):
    """Configure pytest markers for Protocol Check tests."""
    config.addinivalue_line(
        "markers", "protocol_check: mark test as a Protocol Check test"
    )


@pytest.fixture(scope="session")
def protocol_check_test_config():
    """Test configuration for Protocol Check tests."""
    return {
        "timeout": 60,
        "max_retries": 3,
        "test_models": ["qwen3.5-flash", "qwen3.5-plus", "gpt-4o-mini"],
    }


@pytest.fixture
def sample_aimd_protocol():
    """Sample AIMD protocol for testing."""
    return """# Triangle-Shaped Gold Nanoplate Synthesis

## Description

This Airalogy protocol describes how to synthesize triangle-shaped gold nanoplates using a seed-mediated growth method.

## Experimental Information

Experimenter: {{var|experimenter}}
Experiment Date: {{var|experiment_date}}

## Experimental Steps

{{step|prepare_seed_solution,1}} Prepare the seed solution.

{{check|seed_solution_preparation_conditions}} Ensure the following conditions are met:
- Add 4.75 mL of deionized water (DI water) to a container.
- Add 50 μL of HAuCl4 (20 mM).
- Add 100 μL of sodium citrate solution (10 mM).
- Avoid storing the mixture above 35°C. Cool the mixture to 3-8°C if necessary.
- Add 100 μL of freshly prepared NaBH4 (0.1 M) solution under vigorous stirring.
- Stir continuously for 2 minutes until the color changes from yellow to brown.
- Allow the seed solution to stand at room temperature for 2 hours.

{{step|prepare_growth_solution,1}} Prepare the growth solution.

{{check|growth_solution_preparation_conditions}} Ensure the following conditions are met:
- Add 108 mL of CTAB (0.025 M) solution to a container.
- Heat the CTAB solution to 60°C if necessary, then cool it to room temperature.
- Add 1.5 mL of HAuCl4 (20 mM) and gently shake.
- Add 600 μL of 0.1 M NaOH and gently shake.
- Add 54 μL of KI (0.1 M) and continue gently shaking.
- Finally, add 600 μL of 0.1 M ascorbic acid (AA) solution and gently shake.
- The solution should change color from yellow to colorless. Discard and repeat steps if the final solution is not colorless.

{{step|synthesize_triangle_nanoplates,1}} Synthesize triangle-shaped gold nanoplates.

{{check|synthesis_conditions}} Ensure the following conditions are met:
- Combine 100 μL of seed solution with 900 μL of growth solution.
- Gently shake for 3 seconds.
- Add 9 mL of growth solution to the mixture.
- Alternatively, add 1 mL of the mixture to 9 mL of growth solution.
- Shake the combined mixture for 4 seconds.
- Mix with 92 mL (or 98 mL) of growth solution.
- Gently shake the final mixture for 6 seconds.
- Let the mixture stand undisturbed for 30 minutes.
- If the ambient temperature is below 20°C, place the bottle in a 30°C oven to prevent CTAB precipitation.
- The solution should deepen to a purple color, indicating the formation of gold nanoparticles.
- Let the nanoplates settle for 24 hours.
- Carefully decant the supernatant without disturbing the precipitate.
- Resuspend the nanoplate precipitate in 10 mL of deionized water.
- For long-term storage, keep the nanoplates in a 10-25 mM CTAB solution to prevent further growth.
- The final solution should appear green.
- If the solution is not green (e.g., pale purple or pink), start the process over.

## Expected Results

Successful synthesis should yield triangular nanoplates with lengths of approximately 150 nm and thicknesses of about 8 nm."""


@pytest.fixture
def sample_py_model():
    """Sample Python model for testing."""
    return """from datetime import date

from pydantic import BaseModel


class VarModel(BaseModel):
    experimenter: str
    experiment_date: date
    hauc14_volume: float
    sodium_citrate_volume: float
    nabh4_volume: float
    ctab_volume: float
    haucl4_volume_growth: float
    naoh_volume: float
    ki_volume: float
    aa_volume: float
    seed_solution_volume: float
    growth_solution_volume_initial: float
    growth_solution_volume_final: float
    settling_time: int
    final_solution_volume: float
    final_solution_color: str"""


@pytest.fixture
def sample_py_assigner():
    """Sample Python assigner for testing."""
    return """from airalogy.assigner import (
    AssignerBase,
    AssignerMode,
    AssignerResult,
    assigner,
)


class Assigner(AssignerBase):
    @assigner(
        assigned_fields=["hauc14_volume"],
        dependent_fields=["ctab_volume"],
        mode=AssignerMode.AUTO,
    )
    def assign_hauc14_volume(dependent_fields: dict) -> AssignerResult:
        ctab_volume = dependent_fields["ctab_volume"]
        hauc14_volume = ctab_volume * 0.0138889  # 1.5 mL in 108 mL CTAB solution
        return AssignerResult(
            success=True,
            assigned_fields={"hauc14_volume": round(hauc14_volume, 2)},
            error_message=None,
        )

    @assigner(
        assigned_fields=["sodium_citrate_volume"],
        dependent_fields=["ctab_volume"],
        mode=AssignerMode.AUTO,
    )
    def assign_sodium_citrate_volume(dependent_fields: dict) -> AssignerResult:
        ctab_volume = dependent_fields["ctab_volume"]
        sodium_citrate_volume = ctab_volume * 0.00092593  # 100 μL in 108 mL CTAB solution
        return AssignerResult(
            success=True,
            assigned_fields={"sodium_citrate_volume": round(sodium_citrate_volume, 2)},
            error_message=None,
        )

    @assigner(
        assigned_fields=["nabh4_volume"],
        dependent_fields=["ctab_volume"],
        mode=AssignerMode.AUTO,
    )
    def assign_nabh4_volume(dependent_fields: dict) -> AssignerResult:
        ctab_volume = dependent_fields["ctab_volume"]
        nabh4_volume = ctab_volume * 0.00092593  # 100 μL in 108 mL CTAB solution
        return AssignerResult(
            success=True,
            assigned_fields={"nabh4_volume": round(nabh4_volume, 2)},
            error_message=None,
        )"""


@pytest.fixture
def mock_protocol_check_request():
    """Mock Protocol Check request body for testing."""

    def _create_request(
        model_name="qwen3.5-flash",
        target_file="protocol",
        aimd_protocol=None,
        py_model=None,
        py_assigner=None,
        feedback="帮我检查一下这个文件是否有语法错误，并做出改正，润色。",
    ):
        return ProtocolCheckInput(
            model=SupportedModels(
                name=model_name, enable_thinking=False, enable_search=False
            ),
            aimd_protocol=aimd_protocol,
            py_model=py_model,
            py_assigner=py_assigner,
            feedback=feedback,
            target_file=target_file,
            check_num=0,
        )

    return _create_request


@pytest.fixture
def sample_feedback_messages():
    """Sample feedback messages for testing."""
    return [
        "帮我检查一下这个文件是否有语法错误，并做出改正，润色。",
        "请优化代码结构，提高可读性。",
        "修正实验步骤中的逻辑错误。",
        "添加更详细的实验参数说明。",
        "确保所有变量都在模型中定义。",
        "验证分配器中的计算公式是否正确。",
    ]
