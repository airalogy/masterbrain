"""
生成Abstract摘要
"""

from pydantic import BaseModel

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

from masterbrain.endpoints.paper_generation.logic.config import Configuration
from masterbrain.endpoints.paper_generation.logic.utils import set_openai_api_base, create_chat_model


class Abstract(BaseModel):
    """Abstract内容"""
    content: str


async def generate_abstract(
        title: str,
        introduction: str,
        methods: str,
        results: str,
        discussion: str,
        config: Configuration
) -> Abstract:
    """
    生成摘要
    
    Args:
        title: 题目
        introduction: 引言
        methods: 方法
        results: 结果
        discussion: 讨论
        config: 配置
        
    Returns:
        摘要文本
    """
    set_openai_api_base()

    abstract_prompt = f"""Write a concise abstract for a Nature journal research paper.

Title: {title}

Key elements to include:
- Background (introduction): {introduction}...
- Methods (brief): {methods}...
- Results (key findings): {results}...
- Conclusions (from discussion): {discussion}...

Requirements:
1. Single paragraph, 150-250 words
2. No citations
3. Structured: background, methods, results, conclusions
4. Emphasize significance and novelty
5. Use active voice where possible

Return as JSON with:
- "content": The abstract text
"""

    writer_model = create_chat_model(config)

    structured_llm = writer_model.with_structured_output(Abstract)

    abstarct = await structured_llm.ainvoke([
        SystemMessage(content="You are an expert scientific writer for Nature journal."),
        HumanMessage(content=abstract_prompt)
    ])

    return abstarct
