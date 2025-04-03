import os
import aiohttp
from typing import Any, Dict, Optional, AsyncIterator
import logging
from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class TavilySearchTool(BaseTool):
    """
    使用Tavily搜索引擎进行网络搜索的工具
    """
    
    def __init__(self):
        super().__init__(
            name="TavilySearch",
            description="使用Tavily搜索引擎进行网络搜索，支持实时新闻和通用搜索"
        )
        # 从环境变量获取API密钥
        self.api_key = os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            logger.error("TAVILY_API_KEY environment variable not set")
    
    async def _run(self, 
                   query: str, 
                   topic: str = "general",
                   search_depth: str = "basic",
                   max_results: int = 5,
                   include_answer: bool = False,
                   **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """
        执行Tavily搜索并流式返回结果
        
        Args:
            query: 搜索查询
            topic: 搜索类型，general或news
            search_depth: 搜索深度，basic或advanced
            max_results: 返回结果数量，范围0-20
            include_answer: 是否包含AI生成的答案总结
            **kwargs: 可选参数，包含 conversation_context
            
        Yields:
            字典，包含搜索结果或状态信息
            Example chunk: {"type": "content_chunk", "data": {"title": ..., "url": ..., ...}}
            Example answer: {"type": "answer", "data": "..."}
            Example final: {"type": "final_status", "status": "success"}
            Example error: {"type": "error", "error": "..."}
        """
        if not self.api_key:
            yield {"type": "error", "error": "Tavily API key not found in environment variables"}
            return
        
        conversation_context = kwargs.get("conversation_context")
        # Note: conversation_context is retrieved but not currently used for Tavily search.
        # Tavily might implicitly use context in its ranking, but we don't pass it explicitly.

        url = "https://api.tavily.com/search"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建请求参数
        payload = {
            "query": query,
            "topic": topic,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_answer": include_answer
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                yield {"type": "status", "message": f"Searching for '{query}' using Tavily..."}
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        yield {"type": "error", "error": f"Tavily API error: {response.status}, {error_text}"}
                        return
                    
                    data = await response.json()
                    
                    # 如果包含AI生成的答案，先返回答案
                    if include_answer and "answer" in data:
                        yield {"type": "answer", "data": data["answer"]}
                    
                    # 返回搜索结果
                    if "results" in data:
                        for result in data["results"]:
                            result_data = {
                                "title": result.get("title", ""),
                                "url": result.get("url", ""),
                                "content": result.get("content", ""),
                                "score": result.get("score", 0)
                            }
                            # Convert result_data dictionary to a formatted string
                            result_text = f"Title: {result_data['title']}\n"
                            result_text += f"URL: {result_data['url']}\n"
                            result_text += f"Content: {result_data['content']}\n\n"
                            
                            yield {"type": "content_chunk", "content": result_text}
                    
                    # 返回响应时间
                    if "response_time" in data:
                        yield {"type": "status", "message": f"Search completed in {data['response_time']} seconds"}
                    
                    yield {"type": "final_status", "status": "success"}
                    
        except aiohttp.ClientError as e:
            yield {"type": "error", "error": f"Network error during Tavily search: {str(e)}"}
        except Exception as e:
            yield {"type": "error", "error": f"An unexpected error occurred: {str(e)}"}
    
    def get_schema(self) -> Dict[str, Any]:
        """
        获取工具的JSON Schema
        """
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询"
                },
                "topic": {
                    "type": "string",
                    "description": "搜索类型，news用于实时新闻，general用于通用搜索",
                    "enum": ["general", "news"],
                    "default": "general"
                },
                "search_depth": {
                    "type": "string",
                    "description": "搜索深度，basic为基础搜索(1 API Credit)，advanced为高级搜索(2 API Credits)",
                    "enum": ["basic", "advanced"],
                    "default": "basic"
                },
                "max_results": {
                    "type": "integer",
                    "description": "返回结果数量，范围0-20",
                    "default": 5
                },
                "include_answer": {
                    "type": "boolean",
                    "description": "是否包含AI生成的答案总结",
                    "default": false
                }
            },
            "required": ["query"]
        } 