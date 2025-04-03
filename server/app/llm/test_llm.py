import asyncio
import os
import pytest
from typing import Dict, Any
from app.utils.logger import get_logger, setup_logger
from app.config import Config
from app.llm import LLM

logger = get_logger()

pytestmark = pytest.mark.asyncio  # 标记所有测试函数为异步测试

def create_test_config(vendor: str, model: str) -> Dict[str, Any]:
    """
    Create a test configuration for the specified vendor and model.
    
    Args:
        vendor: The vendor name (OpenAI or Anthropic)
        model: The model name
        
    Returns:
        A dictionary containing the model configuration
    """
    return {
        "vendor": Config.get_vendor_config(vendor),
        "llm_args": {
            "model": model,
            "temperature": 0,
            "max_tokens": 100
        }
    }

@pytest.mark.asyncio
async def test_default_config():
    """Test LLM initialization with default configuration."""
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("No API keys available")
    
    llm = LLM()
    messages = [{"role": "user", "content": "Hello"}]
    response = await llm.aChat(messages)
    assert "content" in response
    assert "usage" in response
    assert "model" in response

@pytest.mark.asyncio
async def test_openai_basic():
    """Test basic OpenAI functionality."""
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY environment variable not set")
    
    config = create_test_config("OpenAI", "gpt-3.5-turbo")
    llm = LLM(config)
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, what is the capital of France?"}
    ]
    
    response = await llm.aChat(messages)
    assert "content" in response
    assert "usage" in response
    assert "model" in response
    assert response["model"].startswith("gpt-3.5-turbo")

@pytest.mark.asyncio
async def test_openai_error_handling():
    """Test OpenAI error handling."""
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY environment variable not set")
    
    config = create_test_config("OpenAI", "gpt-3.5-turbo")
    llm = LLM(config)
    
    # Test with invalid messages
    with pytest.raises(Exception):
        await llm.aChat([])
    
    # Test with invalid model
    config["llm_args"]["model"] = "invalid-model"
    llm = LLM(config)
    with pytest.raises(Exception):
        await llm.aChat([{"role": "user", "content": "Hello"}])

@pytest.mark.asyncio
async def test_anthropic_basic():
    """Test basic Anthropic functionality."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY environment variable not set")
    
    config = create_test_config("Anthropic", "claude-3-haiku-20240307")
    llm = LLM(config)
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, what is the capital of Germany?"}
    ]
    
    response = await llm.aChat(messages)
    assert "content" in response
    assert "usage" in response
    assert "model" in response
    assert response["model"].startswith("claude-3-haiku")

@pytest.mark.asyncio
async def test_anthropic_error_handling():
    """Test Anthropic error handling."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY environment variable not set")
    
    config = create_test_config("Anthropic", "claude-3-haiku-20240307")
    llm = LLM(config)
    
    # Test with invalid messages
    with pytest.raises(Exception):
        await llm.aChat([])
    
    # Test with invalid model
    config["llm_args"]["model"] = "invalid-model"
    llm = LLM(config)
    with pytest.raises(Exception):
        await llm.aChat([{"role": "user", "content": "Hello"}])

@pytest.mark.asyncio
async def test_llm_config_validation():
    """Test model configuration validation."""
    # Test missing vendor
    config = {"llm_args": {"model": "gpt-3.5-turbo"}}
    with pytest.raises(ValueError):
        LLM(config)
    
    # Test missing model
    config = {"vendor": {"name": "OpenAI"}}
    with pytest.raises(ValueError):
        LLM(config)

@pytest.mark.asyncio
async def test_config_validation():
    """Test configuration validation."""
    # Test missing API key
    if not os.environ.get("OPENAI_API_KEY"):
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            Config.get_vendor_config("openai")
    
    if not os.environ.get("ANTHROPIC_API_KEY"):
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            Config.get_vendor_config("anthropic")

async def run_all_tests():
    """Run all LLM tests."""
    logger.info("Starting LLM tests")
    
    # Setup logger for tests
    setup_logger(log_level="DEBUG")
    
    # Run tests
    await test_default_config()
    await test_openai_basic()
    await test_openai_error_handling()
    await test_anthropic_basic()
    await test_anthropic_error_handling()
    await test_llm_config_validation()
    await test_config_validation()
    
    logger.info("All LLM tests completed")

if __name__ == "__main__":
    asyncio.run(run_all_tests()) 