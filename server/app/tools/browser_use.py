from typing import Dict, Any, Optional, AsyncIterator
import asyncio
import logging
from .base_tool import BaseTool

try:
    from browser_use import Agent
    from langchain_openai import ChatOpenAI
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False
    Agent = None
    ChatOpenAI = None

logger = logging.getLogger(__name__)

class BrowserUseTool(BaseTool):
    """
    使用 browser-use 库实现的浏览器操作工具。
    可以使用自然语言来控制浏览器，无需手动指定操作序列。
    """
    
    def __init__(self):
        super().__init__(
            name= "browser_use",
            description= "使用 browser-use 库实现的浏览器操作工具。可以使用自然语言来控制浏览器，无需手动指定操作序列。",
        )
        self.agent = None
    
    async def _initialize_agent(self, model: str = "gpt-4o", task: str = "") -> Optional[Agent]:
        """
        初始化 browser-use agent
        
        Args:
            model: 使用的 LLM 模型名称
            task: The task description for the agent.
            
        Returns:
            Initialized Agent instance or None if initialization fails.
        """
        if not BROWSER_USE_AVAILABLE:
             logger.error(
                "browser-use is required. Install it with 'pip install browser-use' "
                "and run 'playwright install chromium'"
            )
             return None
        
        try:
            if self.agent is None:
                logger.info(f"Initializing browser-use agent with model {model} for task: '{task[:50]}...'")
                self.agent = Agent(
                    task=task,
                    llm=ChatOpenAI(model=model),
                )
            return self.agent
        except Exception as e:
            logger.error(f"Failed to initialize browser-use agent: {e}")
            self.agent = None
            return None

    
    async def _run(self, 
                   task: str, 
                   url: Optional[str] = None, 
                   model: str = "gpt-4o",
                   **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """
        使用BrowserUse执行任务并流式返回
        
        Args:
            task: 要执行的任务描述（自然语言）
            url: 起始URL（可选）
            model: 使用的LLM模型名称
            **kwargs: 可选参数，包含 conversation_context
            
        Yields:
            字典，包含状态更新、最终结果或错误信息.
            Example status: {"type": "status", "message": "Initializing browser..."}
            Example result: {"type": "final_result", "status": "success", "result": ..., "task": ...}
            Example error: {"type": "error", "error": "...", "task": ...}
        """
        agent_instance = None
        try:
            full_task = task
            if url:
                full_task = f"Go to {url} and then {task}"
            yield {"type": "status", "message": f"Preparing browser task: '{full_task[:50]}...'"}

            agent_instance = await self._initialize_agent(model, full_task)
            
            if not agent_instance:
                yield {"type": "error", "error": "Failed to initialize browser agent. Check logs and installation.", "task": full_task}
                return
            
            yield {"type": "status", "message": "Starting browser execution..."}
            
            result = await agent_instance.run()
            
            yield {"type": "status", "message": "Browser task finished."}
            
            yield {
                "type": "content_chunk",
                "status": "success",
                "task": full_task,
                "content": str(result),
            }
                
        except ImportError as e:
             yield {"type": "error", "error": str(e), "task": task}
        except Exception as e:
            logger.error(f"Browser operation error: {str(e)}")
            yield {
                "type": "error",
                "task": task,
                "error": f"Browser operation failed: {str(e)}"
            }
        
        finally:
            if agent_instance:
                 yield {"type": "status", "message": "Cleaning up browser resources..."}
                 self.agent = None
                 logger.info("Browser agent resources potentially cleaned.")

        conversation_context = kwargs.get("conversation_context")
        # Note: conversation_context is retrieved but not directly used in the current logic
        # as browser-use handles context internally based on the task description.
        # It's available here if needed for future enhancements.

    def get_schema(self) -> Dict[str, Any]:
        """
        获取工具的JSON Schema
        """
        return {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "要执行的任务描述（使用自然语言）"
                },
                "url": {
                    "type": "string",
                    "description": "起始URL（可选）"
                },
                "model": {
                    "type": "string",
                    "description": "使用的LLM模型名称",
                    "default": "gpt-4o"
                }
            },
            "required": ["task"]
        } 