from typing import Dict, Any, List, Optional, Union, AsyncIterator
from app.utils.logger import get_logger
from app.config import Config

logger = get_logger()

class LLM:
    """
    Factory class for creating Large Language Model instances.
    This class is responsible for creating and managing LLM instances based on configuration.
    """
    
    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LLM factory with the given configuration.
        
        Args:
            llm_config: A dictionary containing the model configuration with the following keys:
                - vendor: Dict with name (str) and base_url (str)
                - llm_args: Dict with model (str), temperature (Optional[float]), and other args
                If None, uses default configuration from environment variables.
        """
        if llm_config is None:
            llm_config = {
                "vendor": Config.get_vendor_config(),
                "llm_args": {
                    "model": "gpt-3.5-turbo" if Config.DEFAULT_VENDOR.lower() == "openai" else "claude-3-haiku-20240307",
                    "temperature": 0
                }
            }
        
        vendor_name = llm_config.get("vendor", {}).get("name", "").lower()
        logger.info(f"Creating LLM instance with vendor: {vendor_name}")
        
        # Create the appropriate LLM instance
        if vendor_name == "openai":
            from app.llm.openai_llm import OpenAILLM
            self._llm = OpenAILLM(llm_config)
        elif vendor_name == "anthropic":
            from app.llm.anthropic_llm import AnthropicLLM
            self._llm = AnthropicLLM(llm_config)
        else:
            logger.error(f"Unsupported vendor: {vendor_name}")
            raise ValueError(f"Unsupported vendor: {vendor_name}")
    
    async def aChat(
        self, 
        messages: List[Dict[str, str]],
        stream: bool = False
    ) -> Union[Dict[str, Any], AsyncIterator[Dict[str, Any]]]:
        """
        Send a chat request to the underlying LLM and get the response, potentially streaming.
        
        Args:
            messages: A list of message dictionaries, each with 'role' and 'content' keys.
            stream: If True, return an async iterator yielding chunks.
            
        Returns:
            A dictionary containing the model's response or an async iterator.
        """
        return await self._llm.aChat(messages, stream=stream) 