"""
生成Methods部分
"""

from typing import List
from pydantic import BaseModel
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

from masterbrain.endpoints.paper_generation.logic.config import Configuration
from masterbrain.endpoints.paper_generation.logic.utils import set_openai_api_base, create_chat_model


class Methods(BaseModel):
    """Methods部分"""
    content: str


async def generate_methods(
        protocols_content: List[str],
        config: Configuration
) -> Methods:
    """
    生成Methods部分
    
    Args:
        protocols_content: Protocol原始内容列表
        config: 配置
        
    Returns:
        Methods内容
    """
    set_openai_api_base()

    # 合并所有protocol内容
    protocols_text = "\n\n---\n\n".join([
        f"Protocol {i + 1}:\n{content}"
        for i, content in enumerate(protocols_content)
    ])

    methods_prompt = f"""Write a detailed Methods section for a Nature journal research paper based on the experimental protocols.

Experimental Protocols:
{protocols_text}

Requirements:
1. Organize by subsections (e.g., "Cell Culture", "Drug Treatment", "Statistical Analysis")
2. Write in past tense
3. Include all relevant details for reproducibility
4. Specify materials, reagents, and equipment
5. Describe statistical methods
6. Follow Nature journal format
7. Format the output as scientific prose, not as bullet points.

Return as JSON with:
- "content": The methods markdown text, directly start with #### subsection title ...
"""

    writer_model = create_chat_model(config)

    structured_llm = writer_model.with_structured_output(Methods)

    methods = await structured_llm.ainvoke([
        SystemMessage(content="You are an expert scientific writer for Nature journal."),
        HumanMessage(content=methods_prompt)
    ])

    return methods
