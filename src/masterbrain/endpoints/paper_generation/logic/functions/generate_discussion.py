"""
生成Discussion部分
"""

from pydantic import BaseModel

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

from masterbrain.endpoints.paper_generation.logic.config import Configuration
from masterbrain.endpoints.paper_generation.logic.utils import set_openai_api_base, create_chat_model


class Discussion(BaseModel):
    """讨论部分"""
    content: str


async def generate_discussion(
        title: str,
        introduction: str,
        results: str,
        config: Configuration
) -> Discussion:
    """
    生成Discussion部分
    
    Args:
        title: 论文题目
        introduction: 引言部分
        results: 结果部分
        config: 配置
        
    Returns:
        Discussion内容
    """
    set_openai_api_base()

    discussion_prompt = f"""Write a comprehensive Discussion section for a Nature journal research paper.

Title: {title}

Introduction:
{introduction}...

Results:
{results}

Requirements:
1. Interpret the findings in the context of the research question
2. Compare with general scientific knowledge and established understanding
3. DO NOT include any citations or references
4. Discuss limitations
5. Suggest future directions
6. Conclude with the broader significance
7. Use present tense for established facts, past tense for study findings
8. Length: 4-5 paragraphs
9. Be factual and avoid making unverifiable claims

Return as JSON with:
- "content": The discussion text (WITHOUT any citations)
"""

    writer_model = create_chat_model(config)

    structured_llm = writer_model.with_structured_output(Discussion)

    discussion = await structured_llm.ainvoke([
        SystemMessage(
            content="You are an expert scientific writer for Nature journal. Write factually without citations."),
        HumanMessage(content=discussion_prompt)
    ])

    return discussion
