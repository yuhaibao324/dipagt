import os
import json
from typing import Any, Dict, Optional, AsyncIterator
import aiohttp
import logging
from app.llm.llm import LLM

from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class CodeWriterTool(BaseTool):
    """
    编写各种编程语言的代码的工具
    """
    
    def __init__(self):
        super().__init__(
            name="CodeWriter",
            description="编写各种编程语言的代码"
        )
        # 初始化时直接配置LLM，使用gpt-4o
        self.llm = LLM({
            "vendor": {
                "name": "openai"
            },
            "llm_args": {
                "model": "gpt-4o",
                "temperature": 0.2  # 使用较低的temperature以保证代码生成的稳定性
            }
        })
        self.output_dir = "generated_code"
        # 确保输出目录存在
        try:
            os.makedirs(self.output_dir, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create output directory '{self.output_dir}': {e}")
    
    async def _run(self, 
                   language: str, 
                   task: str, 
                   code_style: str = "standard",
                   **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """
        生成代码并流式返回
        
        Args:
            language: 编程语言
            task: 编程任务描述
            code_style: 代码风格，默认为standard
            **kwargs: 可选参数，包含 conversation_context
            
        Yields:
            字典，包含代码块、状态信息或错误.
            Example chunk: {"type": "code_chunk", "data": "..."}
            Example status: {"type": "status", "message": "Generating code..."}
            Example final: {"type": "final_summary", "status": "success", "file_path": ..., ...}
            Example error: {"type": "error", "error": "..."}
        """

        # 确保输出目录存在
        if not os.path.isdir(self.output_dir):
             yield {"type": "error", "error": f"Output directory '{self.output_dir}' does not exist or is not a directory."}
             return

        conversation_context = kwargs.get("conversation_context")

        # 构建提示词
        context_str = ""
        if conversation_context:
            context_str = "\n\nConsider the following conversation history for context:\n" + "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_context])

        system_prompt = f"""You are an expert {language} programmer. 
Your task is to write clean, efficient, and well-documented {language} code following {code_style} style guidelines.
{context_str}
Provide only the code without any explanations or markdown formatting. Start directly with the code."""
        
        user_prompt = f"Write {language} code to {task}. Be thorough and handle edge cases."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        generated_code = ""
        
        try:
            yield {"type": "status", "message": "Generating code..."}
            
            # 使用LLM类的流式接口
            async for chunk in await self.llm.aChat(messages, stream=True):
                if "content" in chunk:
                    code_delta = chunk["content"]
                    if code_delta:
                        generated_code += code_delta
                        yield {"type": "content", "content": str(code_delta)}
            
            if not generated_code:
                 yield {"type": "error", "error": "No code content received from the LLM."}
                 return

            yield {"type": "status", "message": "Code generation complete. Saving file..."}
            
            # 确定文件扩展名
            extension_map = {
                "python": "py", "javascript": "js", "typescript": "ts",
                "java": "java", "c++": "cpp", "go": "go", "rust": "rs",
                "php": "php", "html": "html", "css": "css", "shell": "sh",
                "bash": "sh", "sql": "sql", "markdown": "md"
            }
            extension = extension_map.get(language.lower(), "txt")
            
            # 生成文件名
            safe_task_part = "".join(c if c.isalnum() else '_' for c in task[:20])
            filename = f"{language.lower()}_{safe_task_part}_{hash(task) % 10000}.{extension}"
            filepath = os.path.join(self.output_dir, filename)
            
            # 保存代码到文件
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(generated_code)
                logger.info(f"Generated code saved to: {filepath}")
                yield {
                    "type": "final_summary",
                    "status": "success",
                    "language": language,
                    "task": task,
                    "code_style": code_style,
                    "file_path": filepath,
                }
            except IOError as e:
                logger.error(f"Failed to write code to file '{filepath}': {e}")
                yield {"type": "error", "error": f"Failed to save generated code to file: {e}"}
        
        except Exception as e:
            logger.error(f"An unexpected error occurred during code generation: {str(e)}")
            yield {"type": "error", "error": f"An unexpected error occurred: {str(e)}"}
    
    def get_schema(self) -> Dict[str, Any]:
        """
        获取工具的JSON Schema
        """
        return {
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "description": "编程语言",
                    "enum": ["python", "javascript", "typescript", "java", "c++", "go", "rust", "php", "html", "css", "shell", "bash", "sql", "markdown"]
                },
                "task": {
                    "type": "string",
                    "description": "编程任务描述"
                },
                "code_style": {
                    "type": "string",
                    "description": "代码风格",
                    "default": "standard"
                }
            },
            "required": ["language", "task"]
        } 