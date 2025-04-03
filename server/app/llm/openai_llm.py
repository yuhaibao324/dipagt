import os
from typing import Dict, Any, List, Union, AsyncIterator
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionChunk
from app.utils.logger import get_logger
from app.llm.base_llm import BaseLLM
from app.config import Config

logger = get_logger()

class OpenAILLM(BaseLLM):
    """OpenAI implementation of the LLM interface."""
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        Initialize the OpenAI LLM with the given configuration.
        
        Args:
            llm_config: A dictionary containing:
                - vendor: Dict with name and base_url
                - llm_args: Dict with model name and parameters
        """
        super().__init__(llm_config)
        
        # Get configuration
        vendor_config = llm_config.get("vendor", {})
        llm_args = llm_config.get("llm_args", {})
        
        # Set up OpenAI client
        openai_config = {
            "api_key": Config.OPENAI_API_KEY,
            "base_url": vendor_config.get("base_url"),
        }
        
        # Remove None values
        openai_config = {k: v for k, v in openai_config.items() if v is not None}
        
        # Initialize client
        self.client = AsyncOpenAI(**openai_config)
        
        # Store model configuration
        self.model = llm_args.get("model", "gpt-3.5-turbo")
        self.temperature = llm_args.get("temperature", 0)
        self.max_tokens = llm_args.get("max_tokens", None)
    
    async def _stream_openai_response(
        self, 
        params: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """Helper function to handle the streaming response."""
        logger.info(f"Sending streaming chat request to OpenAI")
        response_stream = await self.client.chat.completions.create(**params, stream=True)
        collected_content = []
        finish_reason = None
        model = ""
        prompt_tokens = 0
        completion_tokens = 0

        async for chunk in response_stream:
            model = chunk.model # Capture model from chunk
            choice = chunk.choices[0] if chunk.choices else None
            if choice:
                delta_content = choice.delta.content
                if delta_content:
                    collected_content.append(delta_content)
                    yield {"type": "delta", "content": delta_content}
                
                if choice.finish_reason:
                    finish_reason = choice.finish_reason
                    logger.info(f"OpenAI stream finished with reason: {finish_reason}")
            
            # Attempt to get usage stats if available (often only in last chunk or separate event)
            # Note: Accurate token counts for streams might require specific handling or approximations
            if chunk.usage:
                 prompt_tokens = chunk.usage.prompt_tokens or prompt_tokens
                 completion_tokens = chunk.usage.completion_tokens or completion_tokens
        
        # Yield final aggregated info if needed (optional)
        total_tokens = prompt_tokens + completion_tokens
        yield {
            "type": "final",
            "finish_reason": finish_reason,
            "aggregated_content": "".join(collected_content),
            "model": model,
            "usage": {
                 "prompt_tokens": prompt_tokens,
                 "completion_tokens": completion_tokens,
                 "total_tokens": total_tokens
             }
        }
        logger.info(f"Finished processing OpenAI stream. Total approx tokens: {total_tokens}")

    async def aChat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False
    ) -> Union[Dict[str, Any], AsyncIterator[Dict[str, Any]]]:
        """
        Send a chat request to the OpenAI API and get the response, potentially streaming.
        
        Args:
            messages: A list of message dictionaries, each with 'role' and 'content' keys.
            stream: If True, return an async iterator yielding chunks. Otherwise, return a single dict.
            
        Returns:
            A dictionary containing the model's response OR
            an async iterator yielding response chunks.
        """
        # Validate messages
        await super().aChat(messages, stream=stream) # Pass stream arg to base validation
        
        # Prepare parameters for the API call
        # Filter out max_tokens if None, as it causes issues with some models/versions
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        if self.max_tokens is not None:
            params["max_tokens"] = self.max_tokens

        if stream:
            # Return the async generator directly
            return self._stream_openai_response(params)
        else:
            # Non-streaming request
            logger.info(f"Sending non-streaming chat request to OpenAI with {len(messages)} messages")
            try:
                response = await self.client.chat.completions.create(**params)
                
                result = {
                    "content": response.choices[0].message.content,
                    "model": response.model,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
                logger.info(f"Received non-streaming response from OpenAI, tokens used: {result['usage']['total_tokens']}")
                return result
                
            except Exception as e:
                logger.error(f"Error in non-streaming OpenAI chat request: {str(e)}")
                raise 