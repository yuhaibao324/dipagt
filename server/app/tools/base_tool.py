from abc import ABC, abstractmethod
import json
from typing import Any, Dict, Optional, AsyncIterator

class BaseTool(ABC):
    """
    基础工具类，所有工具都应该继承这个类
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def _run(self, **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """
        工具的具体实现逻辑, 异步迭代器，流式返回结果。
        每个yield的结果应该是一个包含部分数据的字典。
        例如: {"type": "chunk", "content": "..."}
        """
        if False: 
             yield {}
        pass
    
    async def run(self, **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """
        运行工具并通过异步迭代器流式返回结果。
        Yields dictionaries with 'status' and 'data' or 'error'.
        """
        try:
            async for result_chunk in self._run(**kwargs):
                 yield {
                     "status": "success",
                     "data": result_chunk
                 }
        except Exception as e:
            yield {
                "status": "error",
                "error": str(e)
            }
    
    def get_schema(self) -> Dict[str, Any]:
        """
        获取工具的JSON Schema
        """
        raise NotImplementedError("Subclasses must implement get_schema method")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将工具转换为字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "schema": self.get_schema()
        }
    
    def __str__(self) -> str:
        return f"{self.name}: {self.description}" 