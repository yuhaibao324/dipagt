from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union, AsyncIterator
from app.utils.logger import get_logger

logger = get_logger()

class BaseLLM(ABC):
    """
    Base class for Large Language Model implementations.
    This is an abstract class that defines the interface for all LLM implementations.
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        Initialize the LLM with the given configuration.
        
        Args:
            llm_config: A dictionary containing the model configuration with the following keys:
                - vendor: Dict with name (str) and base_url (str)
                - llm_args: Dict with model (str), temperature (Optional[float]), and other args
        """
        self._validate_config(llm_config)
        
        self.llm_config = llm_config
        self.vendor = llm_config.get("vendor", {})
        self.llm_args = llm_config.get("llm_args", {})
        
        logger.info(f"Initializing {self.__class__.__name__} with model: {self.llm_args.get('model')}")
    
    def _validate_config(self, llm_config: Dict[str, Any]) -> None:
        """
        Validate the model configuration.
        
        Args:
            llm_config: The model configuration to validate
            
        Raises:
            ValueError: If the configuration is invalid
        """
        if not isinstance(llm_config, dict):
            raise ValueError("llm_config must be a dictionary")
        
        if "vendor" not in llm_config:
            raise ValueError("llm_config must contain a 'vendor' key")
        
        vendor = llm_config["vendor"]
        if not isinstance(vendor, dict):
            raise ValueError("vendor must be a dictionary")
        
        if "name" not in vendor:
            raise ValueError("vendor must contain a 'name' key")
        
        if "llm_args" not in llm_config:
            raise ValueError("llm_config must contain a 'llm_args' key")
        
        llm_args = llm_config["llm_args"]
        if not isinstance(llm_args, dict):
            raise ValueError("llm_args must be a dictionary")
        
        if "model" not in llm_args:
            raise ValueError("llm_args must contain a 'model' key")
    
    @abstractmethod
    async def aChat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False
    ) -> Union[Dict[str, Any], AsyncIterator[Dict[str, Any]]]:
        """
        Send a chat request to the LLM and get the response, potentially streaming.
        
        Args:
            messages: A list of message dictionaries, each with 'role' and 'content' keys.
            stream: If True, return an async iterator yielding chunks. Otherwise, return a single dict.
            
        Returns:
            A dictionary containing the model's response OR
            an async iterator yielding response chunks.
            
        Raises:
            ValueError: If messages is empty or invalid.
        """
        if not messages:
            raise ValueError("messages cannot be empty")
        
        for msg in messages:
            if not isinstance(msg, dict):
                raise ValueError("each message must be a dictionary")
            if "role" not in msg or "content" not in msg:
                raise ValueError("each message must contain 'role' and 'content' keys") 