"""
生成引言部分
"""

import json
from typing import List
from pydantic import BaseModel
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

from masterbrain.endpoints.paper_generation.logic.config import Configuration
from masterbrain.endpoints.paper_generation.logic.utils import set_openai_api_base, create_chat_model
from masterbrain.endpoints.paper_generation.logic.search_utils import (
    select_and_execute_search,
    get_search_params
)


class Reference(BaseModel):
    """引用"""
    citation: str
    title: str
    source: str


class Introduction(BaseModel):
    """引言部分"""
    content: str
    references: List[Reference] = []


async def generate_introduction(
        title: str,
        protocols_content: List[str],
        config: Configuration,
        enable_external_reference_search: bool = False
) -> Introduction:
    """
    生成引言部分
    
    Args:
        title: 论文题目
        protocols_content: Protocol原始内容列表
        config: 配置
        use_search: 是否使用搜索引擎查找文献（默认True，False则不包含任何引用）
        
    Returns:
        引言内容和引用
    """
    set_openai_api_base()

    # 合并所有protocol内容
    protocols_text = "\n\n---\n\n".join([
        f"Protocol {i + 1}:\n{content}"
        for i, content in enumerate(protocols_content)
    ])

    writer_model = create_chat_model(config)

    structured_writer_model = writer_model.with_structured_output(Introduction)

    # 如果不使用搜索，直接生成Introduction（不包含引用）
    if not enable_external_reference_search:
        print(f"   ⚠️  跳过文献搜索")

        intro_prompt_no_search = f"""Write a comprehensive Introduction section for a Nature journal research paper.

Title: {title}

Experimental Protocols:
{protocols_text}

Requirements:
1. Start with broad context and narrow to specific research question
2. DO NOT include any citations or references
3. Highlight the gap in current knowledge based on general scientific understanding
4. Clearly state the study objectives
5. Length: 3-4 paragraphs
6. Use scientific, formal language
7. Be factual and avoid making unverifiable claims

Return as JSON with:
- "content": The introduction text (WITHOUT any citations)
- "references": Empty array []
"""

        introduction = await structured_writer_model.ainvoke([
            SystemMessage(
                content="You are an expert scientific writer for Nature journal. Write factually without citations."),
            HumanMessage(content=intro_prompt_no_search)
        ])

        return introduction

    # 使用搜索引擎
    search_query_prompt = f"""Based on this research paper title and experimental protocols, generate 3-5 scientific literature search queries to find relevant background research.

Title: {title}

Experimental Protocols Summary:
{protocols_text}

Generate search queries that will find:
1. Background on the biological mechanisms
2. Previous similar studies
3. Current state of the field
4. Relevant methodologies

Return as a JSON array of strings.
"""

    # 生成搜索查询
    queries_response = await writer_model.ainvoke([
        SystemMessage(content="You are a scientific literature search expert."),
        HumanMessage(content=search_query_prompt)
    ])

    # 解析查询
    try:
        queries = json.loads(queries_response.content)
        if not isinstance(queries, list):
            queries = [title]  # fallback
    except:
        queries = [title]

    # 执行文献搜索（使用配置中指定的搜索API）
    search_api = config.search_api.value if hasattr(config.search_api, 'value') else str(config.search_api).lower()
    params = get_search_params(search_api, config.search_api_config or {})

    print(f"   🔍 使用 {search_api} 搜索引擎，执行 {len(queries[:3])} 个查询...")
    search_results = await select_and_execute_search(search_api, queries[:3], params)
    print(f"   ✅ 搜索完成")

    # 生成引言
    intro_prompt = f"""Write a comprehensive Introduction section for a Nature journal research paper.

Title: {title}

Experimental Protocols:
{protocols_text}

Literature Search Results:
{search_results}

Requirements:
1. Start with broad context and narrow to specific research question
2. Cite relevant literature using [Author et al., Year] format
3. Highlight the gap in current knowledge
4. Clearly state the study objectives
5. Length: 3-4 paragraphs
6. Use scientific, formal language
7. Include at least 5-8 references

Return as JSON with:
- "content": The introduction text with inline citations
- "references": Array of Reference objects, each with:
  * "citation": e.g., "Smith et al., 2023"
  * "title": Full paper title
  * "source": Journal/source name
"""

    introduction = await structured_writer_model.ainvoke([
        SystemMessage(content="You are an expert scientific writer for Nature journal."),
        HumanMessage(content=intro_prompt)
    ])

    return introduction
