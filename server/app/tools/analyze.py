import os
from typing import Any, Dict, Optional, AsyncIterator
import logging
from app.llm.llm import LLM
from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class AnalyzeTool(BaseTool):
    """
    对提供的数据或文本进行分析的工具
    """
    
    def __init__(self):
        super().__init__(
            name="Analyze",
            description="对提供的数据或文本进行分析，提取关键信息、生成摘要或进行情感分析等"
        )
        # 初始化时直接配置LLM，可以使用环境变量配置模型或默认gpt-4o
        llm_model = os.getenv("ANALYZE_TOOL_LLM_MODEL", "gpt-4o")
        self.llm = LLM({
            "vendor": {
                "name": "openai" # Assuming OpenAI for now, could be configurable
            },
            "llm_args": {
                "model": llm_model,
                "temperature": 0.1 # Low temp for consistent analysis
            }
        })
    
    async def _run(self, 
                   data: str, 
                   analysis_type: str = "summary",
                   instructions: Optional[str] = None,
                   **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """
        执行分析任务并流式返回结果
        
        Args:
            data: 需要分析的数据或文本
            analysis_type: 分析类型 (e.g., summary, keywords, sentiment)
            instructions: 具体的分析指令或要求（可选）
            **kwargs: 可选参数，包含 conversation_context
            
        Yields:
            字典，包含分析结果块、状态信息或错误.
            Example chunk: {"type": "content_chunk", "data": "..."}
            Example status: {"type": "status", "message": "Analyzing data..."}
            Example final: {"type": "final_summary", "status": "success", "result": "..."}
            Example error: {"type": "error", "error": "..."}
        """
        if not self.llm:
            yield {"type": "error", "error": "Analyze tool LLM not configured."}
            return

        conversation_context = kwargs.get("conversation_context")

            
        system_prompt = f"You are an expert data analyst. Your task is to perform '{analysis_type}' analysis on the provided data."
        if instructions:
            system_prompt += f" Follow these specific instructions: {instructions}"
        system_prompt += "\nProvide only the analysis result without any explanations or markdown formatting. Start directly with the result."
        
        user_prompt = f"""Analyze the following data:\n\n---
{data}
---"""
        
        messages = [{"role": "system", "content": system_prompt}]

        if conversation_context:
          messages.extend(conversation_context)
          
        messages.extend([{"role": "user", "content": user_prompt}])
        
        analysis_result = ""
        
        try:
            yield {"type": "status", "message": f"Performing '{analysis_type}' analysis..."}
            
            # 使用LLM类的流式接口
            async for chunk in await self.llm.aChat(messages, stream=True):
                if "content" in chunk:
                    result_delta = chunk["content"]
                    if result_delta:
                        analysis_result += result_delta
                        yield {"type": "content_chunk", "content": result_delta}
            
            if not analysis_result:
                 yield {"type": "error", "error": "No analysis result received from the LLM."}
                 return

            yield {
                "type": "final_summary",
                "status": "success",
                "analysis_type": analysis_type,
                "result": analysis_result
            }
        
        except Exception as e:
            logger.error(f"An unexpected error occurred during analysis: {str(e)}")
            yield {"type": "error", "error": f"An unexpected error occurred during analysis: {str(e)}"}
    
    def get_schema(self) -> Dict[str, Any]:
        """
        获取工具的JSON Schema
        """
        return {
            "type": "object",
            "properties": {
                "data": {
                    "type": "string",
                    "description": "需要分析的数据或文本"
                },
                "analysis_type": {
                    "type": "string",
                    "description": "分析类型 (e.g., summary, keywords, sentiment)",
                    "default": "summary"
                },
                "instructions": {
                    "type": "string",
                    "description": "具体的分析指令或要求（可选）"
                }
            },
            "required": ["data", "analysis_type"]
        } 