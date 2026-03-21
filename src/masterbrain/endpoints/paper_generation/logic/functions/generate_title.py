"""
生成论文题目
"""

from typing import List
from pydantic import BaseModel
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

from masterbrain.endpoints.paper_generation.logic.config import Configuration
from masterbrain.endpoints.paper_generation.logic.utils import set_openai_api_base, create_chat_model


class PaperTitle(BaseModel):
    """论文题目"""
    content: str


async def generate_title(
        protocols_content: List[str],
        config: Configuration
) -> PaperTitle:
    """
    生成论文题目

    Args:
        protocols_content: Protocol原始内容列表
        config: 配置对象

    Returns:
        论文题目
    """
    set_openai_api_base()

    # 合并所有protocol内容
    protocols_text = "\n\n---\n\n".join([
        f"Protocol {i + 1}:\n{content}"
        for i, content in enumerate(protocols_content)
    ])

    system_prompt = f"""You are an expert scientific writer specialized in creating Nature journal paper titles.

Based on the experimental protocols provided below, generate a compelling research paper title that:
1. Accurately reflects the scientific content
2. Is concise (maybe 10-15 words)
3. Uses active voice when possible
4. Includes key terms for discoverability
5. Follows Nature journal style

Experimental Protocols:
{protocols_text}

Return your response as a JSON object with:
- "content": The title
"""

    writer_model = create_chat_model(config)

    structured_llm = writer_model.with_structured_output(PaperTitle)

    result = await structured_llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content="Generate the paper title based on the protocols provided.")
    ])

    return result
