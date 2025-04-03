"""
Intention Recognizer Factory

This module provides a factory for creating intention recognizer instances.
"""

from typing import Dict, Any, Optional
from app.llm.base_llm import BaseLLM
from app.intention.recognizer import IntentionRecognizer
from app.utils.logger import get_logger

logger = get_logger()

class IntentionRecognizerFactory:
    """
    Factory class for creating intention recognizer instances.
    """
    
    @staticmethod
    async def create(llm: BaseLLM, config: Optional[Dict[str, Any]] = None) -> IntentionRecognizer:
        """
        Create an intention recognizer instance.
        
        Args:
            llm: The LLM instance to use for intention recognition
            config: Optional configuration for the intention recognizer
            
        Returns:
            An initialized intention recognizer instance
        """
        # Merge default config with provided config
        default_config = {
            "max_history": 5,  # Maximum number of conversation history items to include
            "default_confidence_threshold": 0.5,  # Default confidence threshold
        }
        
        merged_config = default_config.copy()
        if config:
            merged_config.update(config)
        
        # Create and return the recognizer
        recognizer = IntentionRecognizer(llm, merged_config)
        logger.info("Created IntentionRecognizer instance")
        
        return recognizer 