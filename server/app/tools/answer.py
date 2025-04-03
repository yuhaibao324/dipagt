from typing import Dict, Any, Optional, AsyncIterator
from app.tools.base_tool import BaseTool
from app.llm import LLM
from app.utils.logger import get_logger

logger = get_logger()

class AnswerTool(BaseTool):
    """Tool for directly answering user questions using GPT-4"""
    
    def __init__(self):
        super().__init__(
            name="Answer",
            description="直接回答用户的问题，提供清晰准确的答复"
        )
        self.llm = LLM({
            "vendor": {
                "name": "openai",
            },
            "llm_args": {
                "model": "gpt-4o",
                "temperature": 0,
                "max_tokens": 2000
            }
        })
    
    async def _run(self, 
                     query: str = "",
                     format: str = "text",
                     style: str = "professional",
                     **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """
        Execute the answer tool, streaming the response from the LLM.
        
        Args:
            query: The user's question
            format: Response format (text/markdown/html)
            style: Response style (concise/detailed/professional/friendly)
            **kwargs: Additional arguments
            
        Yields:
            Dict chunks containing parts of the response content.
            Example: {"type": "content_chunk", "content": "..."}
            Finally yields: {"type": "final_info", "format": format, "style": style}
        """
        try:
            if query == "":
                query = kwargs.get("message", "")

            conversation_context = kwargs.get("conversation_context", [])

            # Construct system prompt
            system_prompt = f"You are a {style} assistant. "
            if format == "markdown":
                system_prompt += "Format your response in markdown. "
            elif format == "html":
                system_prompt += "Format your response in HTML. "
                
            if style == "concise":
                system_prompt += "Be brief and to the point. "
            elif style == "detailed":
                system_prompt += "Provide comprehensive and detailed explanations. "
            elif style == "friendly":
                system_prompt += "Use a warm and conversational tone. "
            
            # Get streaming response from LLM
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_context)  # Include conversation history if any
            messages.extend([{"role": "user", "content": query}])
            llm_stream = await self.llm.aChat(
                messages=messages,
                stream=True
            )
            
            # Yield content chunks as they arrive
            async for chunk in llm_stream:
                 # Process only delta chunks containing content
                 if chunk.get("type") == "delta" and chunk.get("content"):
                    yield {"type": "content_chunk", "content": chunk["content"]}
                 elif chunk.get("type") == "final":
                    # Optionally log usage from the final chunk if needed
                    logger.info(f"AnswerTool LLM stream finished. Usage: {chunk.get('usage')}")
                    break # Stop processing after the final chunk from LLM
                 # Ignore other potential chunk types from LLM for now
                    
            # Yield final metadata about the response format/style
            yield {"type": "final_info", "format": format, "style": style}
            
        except Exception as e:
            logger.error(f"Error in AnswerTool stream: {str(e)}")
            # Yield an error chunk
            yield {
                "type": "error", 
                "error": f"Failed to get answer: {str(e)}",
            } 