"""
搜索工具函数
"""

import asyncio
from typing import List, Optional, Dict, Any
from tavily import AsyncTavilyClient


def get_search_params(search_api: str, search_api_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Filters the search_api_config dictionary to include only parameters accepted by the specified search API.

    Args:
        search_api (str): The search API identifier (e.g., "exa", "tavily").
        search_api_config (Optional[Dict[str, Any]]): The configuration dictionary for the search API.

    Returns:
        Dict[str, Any]: A dictionary of parameters to pass to the search function.
    """
    # Define accepted parameters for each search API
    SEARCH_API_PARAMS = {
        "exa": ["max_characters", "num_results", "include_domains", "exclude_domains", "subpages"],
        "tavily": ["max_results", "topic", "include_images", "include_image_descriptions"],
        "perplexity": [],  # Perplexity accepts no additional parameters
        "arxiv": ["load_max_docs", "get_full_documents", "load_all_available_meta"],
        "pubmed": ["top_k_results", "email", "api_key", "doc_content_chars_max"],
        "linkup": ["depth"],
    }

    # Get the list of accepted parameters for the given search API
    accepted_params = SEARCH_API_PARAMS.get(search_api, [])

    # If no config provided, return an empty dict
    if not search_api_config:
        return {}

    # Filter the config to only include accepted parameters
    return {k: v for k, v in search_api_config.items() if k in accepted_params}


async def tavily_search_async(
        search_queries,
        max_results: int = 5,
        topic: str = "general",
        include_raw_content: bool = True,
        include_images: bool = False,
        include_image_descriptions: bool = False
):
    """
    Performs concurrent web searches with the Tavily API

    Args:
        search_queries (List[str]): List of search queries to process
        max_results (int): Maximum number of results to return
        topic (str): Search topic
        include_raw_content (bool): Whether to include raw content
        include_images (bool): Whether to include images
        include_image_descriptions (bool): Whether to include image descriptions

    Returns:
        List[dict]: List of search responses from Tavily API
    """
    tavily_async_client = AsyncTavilyClient()
    search_tasks = []
    for query in search_queries:
        search_tasks.append(
            tavily_async_client.search(
                query,
                max_results=max_results,
                include_raw_content=include_raw_content,
                topic=topic,
                include_images=include_images,
                include_image_descriptions=include_image_descriptions
            )
        )

    # Execute all searches concurrently
    search_docs = await asyncio.gather(*search_tasks)
    return search_docs


async def tavily_search(queries: List[str], max_results: int = 5, topic: str = "general", 
                        include_images: bool = False, include_image_descriptions: bool = False) -> str:
    """
    Fetches results from Tavily search API.
    
    Args:
        queries (List[str]): List of search queries
        max_results (int): Maximum number of results to return
        topic (str): Search topic
        include_images (bool): Whether to include images in results
        include_image_descriptions (bool): Whether to include image descriptions
        
    Returns:
        str: A formatted string of search results
    """
    print(f"tavily_search函数接收到的参数:")
    print(f"  queries: {queries}")
    print(f"  max_results: {max_results}")
    print(f"  topic: {topic}")
    print(f"  include_images: {include_images}")
    print(f"  include_image_descriptions: {include_image_descriptions}")

    # Use tavily_search_async with include_raw_content=True to get content directly
    search_results = await tavily_search_async(
        queries,
        max_results=max_results,
        topic=topic,
        include_raw_content=True,
        include_images=include_images,
        include_image_descriptions=include_image_descriptions
    )

    # Format the search results directly using the raw_content already provided
    formatted_output = f"Search results: \n\n"

    # Deduplicate results by URL
    unique_results = {}
    for response in search_results:
        for result in response['results']:
            url = result['url']
            if url not in unique_results:
                unique_results[url] = result

    # Format the unique results
    for i, (url, result) in enumerate(unique_results.items()):
        formatted_output += f"\n\n--- SOURCE {i + 1}: {result['title']} ---\n"
        formatted_output += f"URL: {url}\n\n"
        formatted_output += f"SUMMARY:\n{result['content']}\n\n"
        if result.get('raw_content'):
            formatted_output += f"FULL CONTENT:\n{result['raw_content'][:30000]}"  # Limit content size
        formatted_output += "\n\n" + "-" * 80 + "\n"

    # 添加图像结果处理
    if include_images:
        formatted_output += "\n\n--- IMAGES ---\n\n"
        image_count = 0
        for response in search_results:
            if 'images' in response and response['images']:
                for image in response['images']:
                    image_count += 1
                    formatted_output += f"IMAGE {image_count}:\n"
                    formatted_output += f"URL: {image.get('url', 'No URL')}\n"
                    if include_image_descriptions and 'description' in image:
                        formatted_output += f"DESCRIPTION: {image.get('description', 'No description')}\n"
                    formatted_output += "\n"

        if image_count == 0:
            formatted_output += "No images found in search results.\n"
        formatted_output += "-" * 80 + "\n"

    print(formatted_output)

    if unique_results:
        return formatted_output
    else:
        return "No valid search results found. Please try different search queries or use a different search API."


async def select_and_execute_search(search_api: str, query_list: list[str], params_to_pass: dict) -> str:
    """Select and execute the appropriate search API.
    
    Args:
        search_api: Name of the search API to use
        query_list: List of search queries to execute
        params_to_pass: Parameters to pass to the search API
        
    Returns:
        Formatted string containing search results
        
    Raises:
        ValueError: If an unsupported search API is specified
    """
    if search_api == "tavily":
        # Tavily search
        all_params = {"queries": query_list}
        all_params.update(params_to_pass)
        print(f"调用tavily_search，合并后的参数: {all_params}")
        return await tavily_search(**all_params)
    else:
        raise ValueError(f"Unsupported search API: {search_api}. Only 'tavily' is currently supported.")
