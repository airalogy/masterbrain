"""
生成Results部分
"""

from typing import List
from pydantic import BaseModel
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

from masterbrain.endpoints.paper_generation.logic.config import Configuration
from masterbrain.endpoints.paper_generation.logic.utils import set_openai_api_base, create_chat_model


class Results(BaseModel):
    """结果部分"""
    content: str


async def generate_results(
        protocols_content: List[str],
        config: Configuration
) -> Results:
    """
    生成Results部分

    Args:
        protocols_content: Protocol原始内容列表
        config: 配置

    Returns:
        Results内容
    """
    set_openai_api_base()

    # 合并所有protocol内容（包含实验数据）
    protocols_text = "\n\n---\n\n".join([
        f"Protocol {i + 1}:\n{content}"
        for i, content in enumerate(protocols_content)
    ])

    results_prompt = f"""Write a comprehensive Results section for a Nature journal research paper.

Experimental Protocols (including results data):
{protocols_text}

Requirements:
1. Present results in logical order
2. Include statistical significance where applicable
3. Highlight key findings
4. Use past tense
5. Be objective and factual
6. Length: 3-4 paragraphs
7. If the data is suitable for tabular presentation, create markdown tables directly in the text
8. Use proper markdown table syntax: | Column 1 | Column 2 | ... |
9. Tables should have headers and be properly formatted
10. Do NOT reference figures - only tables if you create them

Example of markdown table:
| Treatment | Control OD | Treatment OD | Inhibition Rate (%) |
|-----------|------------|--------------|---------------------|
| Paclitaxel | 1.85 | 0.92 | 50.27 |

Return as JSON with:
- "content": The results text (may include markdown tables)
"""

    writer_model = create_chat_model(config)

    structured_llm = writer_model.with_structured_output(Results)

    results = await structured_llm.ainvoke([
        SystemMessage(content="You are an expert scientific writer for Nature journal."),
        HumanMessage(content=results_prompt)
    ])

    return results
