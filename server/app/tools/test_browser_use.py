import pytest
from unittest.mock import patch
from app.tools.browser_use import BrowserUseTool

@pytest.mark.asyncio
async def test_browser_use_successful_task():
    """测试成功执行浏览器任务的场景
    
    验证：
    1. Agent正确初始化
    2. 任务正确执行
    3. 返回预期的成功结果格式
    """
    tool = BrowserUseTool()
    result = await tool._run(
        task="Search for Python documentation",
        url="https://www.python.org",
        model="gpt-4o"
    )
    
    # 验证结果
    assert result["status"] == "success"
    assert result["error"] is None
        
@pytest.mark.asyncio
async def test_browser_use_initialization_error():
    """测试初始化失败的场景
    
    验证：
    1. 当browser-use不可用时的错误处理
    2. 返回预期的错误结果格式
    """
    with patch('app.tools.browser_use.BROWSER_USE_AVAILABLE', False):
        tool = BrowserUseTool()
        result = await tool._run(
            task="Any task",
            model="gpt-4o"
        )
        
        # 验证结果
        assert result["status"] == "error"
        assert "browser-use is required" in result["error"]
        assert result["result"] is None 