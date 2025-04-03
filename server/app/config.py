import os
from typing import Dict, Any
from dotenv import load_dotenv
from app.utils.logger import get_logger

logger = get_logger()

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration management class."""
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    # Anthropic Configuration
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    
    # Default Vendor
    DEFAULT_VENDOR = os.getenv("DEFAULT_VENDOR", "OpenAI")
    
    @classmethod
    def get_vendor_config(cls, vendor_name: str = None) -> Dict[str, Any]:
        """
        Get the configuration for a specific vendor.
        
        Args:
            vendor_name: The name of the vendor. If None, uses DEFAULT_VENDOR.
            
        Returns:
            A dictionary containing the vendor configuration.
            
        Raises:
            ValueError: If the vendor is not supported or configuration is missing.
        """
        vendor_name = vendor_name or cls.DEFAULT_VENDOR
        vendor_name = vendor_name.lower()
        
        if vendor_name == "openai":
            if not cls.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            return {
                "name": "OpenAI",
                "base_url": cls.OPENAI_BASE_URL
            }
        elif vendor_name == "anthropic":
            if not cls.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
            return {
                "name": "Anthropic",
                "base_url": cls.ANTHROPIC_BASE_URL
            }
        else:
            raise ValueError(f"Unsupported vendor: {vendor_name}")
    
    @classmethod
    def validate_config(cls) -> None:
        """
        Validate the configuration.
        
        Raises:
            ValueError: If required configuration is missing.
        """
        if not cls.DEFAULT_VENDOR:
            raise ValueError("DEFAULT_VENDOR environment variable is not set")
        
        # Validate default vendor configuration
        cls.get_vendor_config() 