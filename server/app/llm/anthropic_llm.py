import os
from typing import Dict, Any, List
import anthropic
from app.utils.logger import get_logger
from app.llm.base_llm import BaseLLM
from app.config import Config

logger = get_logger()

class AnthropicLLM(BaseLLM):
    """
    Anthropic implementation of the LLM interface.
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        Initialize the Anthropic LLM with the given configuration.
        
        Args:
            llm_config: A dictionary containing:
                - vendor: Dict with name and base_url
                - llm_args: Dict with model name and parameters
        """
        super().__init__(llm_config)
        
        # Get configuration
        vendor_config = llm_config.get("vendor", {})
        llm_args = llm_config.get("llm_args", {})
        
        # Set up Anthropic client
        anthropic_config = {
            "api_key": Config.ANTHROPIC_API_KEY,
            "base_url": vendor_config.get("base_url"),
        }
        
        # Remove None values
        anthropic_config = {k: v for k, v in anthropic_config.items() if v is not None}
        
        # Initialize client
        self.client = anthropic.AsyncAnthropic(**anthropic_config)
        
        # Store model configuration
        self.model = llm_args.get("model", "claude-3-haiku-20240307")
        self.temperature = llm_args.get("temperature", 0)
        self.max_tokens = llm_args.get("max_tokens", None)
        
        # Extract any additional parameters
        self.additional_params = {k: v for k, v in llm_args.items() 
                                if k not in ["model", "temperature", "max_tokens"]}
        
        logger.info(f"Anthropic LLM initialized with model: {self.model}")
    
    async def aChat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Send a chat request to the Anthropic API and get the response.
        
        Args:
            messages: A list of message dictionaries, each with 'role' and 'content' keys
            
        Returns:
            A dictionary containing the model's response
        """
        # Validate messages
        await super().aChat(messages)
        
        logger.info(f"Sending chat request to Anthropic with {len(messages)} messages")
        
        try:
            # Convert OpenAI-style messages to Anthropic format if needed
            anthropic_messages = []
            system_message = None

            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                
                # Map OpenAI roles to Anthropic roles
                if role == "system":
                    system_message = content
                elif role == "user":
                    anthropic_messages.append({"role": "user", "content": content})
                elif role == "assistant":
                    anthropic_messages.append({"role": "assistant", "content": content})
                else:
                    logger.warning(f"Unknown message role: {role}, treating as user message")
                    anthropic_messages.append({"role": "user", "content": content})

            # Prepare parameters for the API call
            params = {
                "model": self.model,
                "messages": anthropic_messages,
                "temperature": self.temperature,
                **self.additional_params
            }

            # Now use system_message as a top-level parameter if it exists
            if system_message:
                params["system"] = system_message
            
            # Make the API call
            response = await self.client.messages.create(**params)
            
            # Extract and return the response
            result = {
                "content": response.content[0].text,
                "model": response.model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            }
            
            logger.info(f"Received response from Anthropic, tokens used: {result['usage']['total_tokens']}")
            return result
            
        except Exception as e:
            logger.error(f"Error in Anthropic chat request: {str(e)}")
            raise 