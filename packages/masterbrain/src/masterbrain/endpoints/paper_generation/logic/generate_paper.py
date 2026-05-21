"""
Paper Generation Logic

论文生成的核心逻辑
"""

from datetime import datetime
from typing import List, Optional

from masterbrain.endpoints.paper_generation.types import SupportedModels
from masterbrain.endpoints.paper_generation.logic.config import Configuration, SearchAPI
from masterbrain.endpoints.paper_generation.logic.functions.generate_title import generate_title
from masterbrain.endpoints.paper_generation.logic.functions.generate_introduction import generate_introduction
from masterbrain.endpoints.paper_generation.logic.functions.generate_methods import generate_methods
from masterbrain.endpoints.paper_generation.logic.functions.generate_results import generate_results
from masterbrain.endpoints.paper_generation.logic.functions.generate_discussion import generate_discussion
from masterbrain.endpoints.paper_generation.logic.functions.generate_abstract import generate_abstract


def clean_markdown(markdown: str) -> str:
    """
    清理markdown中的转义字符

    Args:
        markdown: 原始markdown字符串

    Returns:
        清理后的markdown
    """
    return markdown.replace("\\n", "\n").replace("\\t", "\t")


async def generate_paper(
        protocols: List[str],
        model: SupportedModels,
        enable_external_reference_search: bool,
        output_file: Optional[str] = None,
        config: Optional[Configuration] = None
) -> str:
    """
    主函数：生成完整的Nature论文

    Args:
        protocols: Protocol markdown文本列表（每个元素是一个protocol的markdown，应包含实验数据）
        model: 模型配置对象
        output_file: 输出文件路径（可选，如果不提供则不保存文件）
        config: 配置对象（可选，如果不提供则使用默认配置）

    Returns:
        论文生成响应
    """
    print("🔬 Nature论文生成器启动...")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 清理protocol markdown中的转义字符
    protocols_content = [clean_markdown(p) for p in protocols]
    print(f"📋 已加载 {len(protocols_content)} 个实验protocol\n")
    print("💡 提示: Protocol应包含完整的实验步骤和结果数据\n")

    # 将 SupportedModels 转换为 Configuration
    if config is None:
        from typing import get_args
        from masterbrain.configs import (
            AvailableOpenAIModel,
            AvailableQwenModel,
            OPENAI_API_KEY,
            OPENAI_BASE_URL,
            DASHSCOPE_API_KEY,
            DASHSCOPE_BASE_URL,
        )
        
        model_name = model.name
        
        # 使用与 select_client 相同的逻辑判断模型类型
        if model_name in get_args(AvailableQwenModel):
            # Qwen 模型使用 DashScope API
            api_key = DASHSCOPE_API_KEY
            base_url = DASHSCOPE_BASE_URL or "https://dashscope.aliyuncs.com/compatible-mode/v1"
            writer_provider = "openai"
            writer_model = model_name
        elif model_name in get_args(AvailableOpenAIModel):
            # OpenAI 模型
            api_key = OPENAI_API_KEY
            base_url = OPENAI_BASE_URL
            writer_provider = "openai"
            writer_model = model_name
        else:
            # 默认使用 OpenAI 配置
            api_key = OPENAI_API_KEY
            base_url = OPENAI_BASE_URL
            writer_provider = "openai"
            writer_model = model_name
        
        if not api_key:
            raise ValueError(f"API key not set for model {model_name}. Please check environment variables.")
        
        # 构建 model_kwargs
        model_kwargs = {"api_key": api_key}
        if base_url:
            model_kwargs["base_url"] = base_url

        config = Configuration(
            search_api=SearchAPI.TAVILY if enable_external_reference_search else SearchAPI.TAVILY,
            number_of_queries=3,
            max_search_depth=1,
            writer_provider=writer_provider,
            writer_model=writer_model,
            writer_model_kwargs=model_kwargs,
        )

    # 步骤1: 生成题目
    print("📝 步骤 1/6: 生成论文题目...")
    title = await generate_title(protocols_content, config)
    print(f"   ✅ 题目: {title.content}\n")

    # 步骤2: 生成Introduction
    if enable_external_reference_search:
        print("📚 步骤 2/6: 生成Introduction（包含文献搜索）...")
    else:
        print("📚 步骤 2/6: 生成Introduction（无搜索）...")
    introduction = await generate_introduction(title.content, protocols_content, config, enable_external_reference_search)
    print(f"   ✅ 完成，包含 {len(introduction.references)} 个引用\n")

    # 步骤3: 生成Results
    print("📊 步骤 3/6: 生成Results...")
    results = await generate_results(protocols_content, config)
    print(f"   ✅ 完成\n")

    # 步骤4: 生成Discussion
    print("💡 步骤 4/6: 生成Discussion...")
    discussion = await generate_discussion(title.content, introduction.content, results.content, config)
    print(f"   ✅ 完成\n")

    # 步骤5: 生成Methods
    print("🔬 步骤 5/6: 生成Methods...")
    methods = await generate_methods(protocols_content, config)
    print(f"   ✅ 完成\n")

    # 步骤6: 生成Abstract
    print("📄 步骤 6/6: 生成Abstract...")
    abstract = await generate_abstract(
        title.content, introduction.content, methods.content, results.content, discussion.content, config
    )
    print(f"   ✅ 完成\n")

    # 合并所有引用（只来自Introduction，Discussion不再包含引用）
    unique_references = introduction.references

    # 生成References章节（仅当有引用时）
    references_section = ""
    if len(unique_references) > 0:
        references_section = f"""## References

{"\n".join(f"{i + 1}. {ref.citation}: {ref.title} ({ref.source})" for i, ref in enumerate(unique_references))}

"""

    # 清理所有生成内容中的转义字符
    cleaned_title = clean_markdown(title.content)
    cleaned_abstract = clean_markdown(abstract.content)
    cleaned_introduction = clean_markdown(introduction.content)
    cleaned_methods = clean_markdown(methods.content)
    cleaned_results = clean_markdown(results.content)
    cleaned_discussion = clean_markdown(discussion.content)

    # 生成完整的Markdown论文
    paper_markdown = f"""# {cleaned_title}

## Abstract

{cleaned_abstract}

---

## Introduction

{cleaned_introduction}

---

## Results

{cleaned_results}

---

## Discussion

{cleaned_discussion}

---

## Methods

{cleaned_methods}

{references_section}

---

*Generated by Airalogy Paper Generator*  
*Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    # 保存到文件（如果提供了输出文件路径）
    if output_file is not None:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(paper_markdown)
        print(f"✅ 论文生成完成！")
        print(f"📁 保存位置: {output_file}")
    else:
        print(f"✅ 论文生成完成！")
    print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    return paper_markdown
