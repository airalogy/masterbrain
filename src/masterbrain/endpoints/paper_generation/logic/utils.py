"""
工具函数
"""

import os
from typing import TYPE_CHECKING
from langchain.chat_models import init_chat_model

if TYPE_CHECKING:
    from masterbrain.endpoints.paper_generation.logic.config import Configuration


def set_openai_api_base():
    """
    设置OpenAI API的基础URL。
    如果环境变量OPENAI_BASE_URL存在，则将其设置为OpenAI API的基础URL。
    """
    openai_api_base = os.environ.get('OPENAI_BASE_URL')
    if openai_api_base:
        try:
            import openai
            openai.api_base = openai_api_base
            print(f"已设置OpenAI API基础URL: {openai_api_base}")
        except ImportError:
            print("未找到openai包，无法设置API基础URL")


def create_chat_model(config: "Configuration"):
    """
    创建聊天模型实例
    
    Args:
        config: Configuration 对象，包含模型配置
        
    Returns:
        初始化的聊天模型
    """
    # 从 writer_model_kwargs 中提取 api_key 和 base_url
    model_kwargs = (config.writer_model_kwargs or {}).copy()
    api_key = model_kwargs.pop("api_key", None)
    base_url = model_kwargs.pop("base_url", None)
    
    # 构建 init_chat_model 的参数
    init_params = {
        "model": config.writer_model,
        "model_provider": config.writer_provider,
        "model_kwargs": model_kwargs
    }
    if api_key:
        init_params["api_key"] = api_key
    if base_url:
        init_params["base_url"] = base_url
    
    return init_chat_model(**init_params)
