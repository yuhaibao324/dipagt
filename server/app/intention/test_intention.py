"""
Example Usage of the Intention Recognition Module

This module demonstrates how to use the intention recognition module.
"""

import asyncio
from app.config import Config
from app.intention.factory import IntentionRecognizerFactory
from app.llm.llm import LLM
from app.utils.logger import get_logger
import pytest

logger = get_logger()


@pytest.mark.asyncio
async def test_intention_recognition():
    """
    Test the intention recognition functionality
    """
    # Initialize the LLM

    openai_config = Config.get_vendor_config("openai")
    llm_config = {
        "vendor": openai_config,
        "llm_args": {
            "model": "gpt-4o",
            "temperature": 0,
            "max_tokens": 1000
        }
    }
    
    llm = LLM(llm_config)
    
    # Create the intention recognizer
    recognizer = await IntentionRecognizerFactory.create(llm, {
        "max_history": 3
    })
    
    # Test case 1: Weather query
    weather_result = await recognizer.recognize(
        user_input="我想查询明天上海的天气情况",
        conversation_history=[],
        user_data={"preferences": {"location": "上海"}}
    )
    
    assert weather_result["intent"] == "query"
    
    # Test case 2: Meeting reminder
    reminder_result = await recognizer.recognize(
        user_input="帮我创建一个提醒，明天下午3点参加会议",
        conversation_history=[],
        user_data={}
    )
    
    assert reminder_result["intent"] == "action"
    assert reminder_result["sub_intent"] == "create"

if __name__ == "__main__":
    # Run the example
    asyncio.run(test_intention_recognition()) 