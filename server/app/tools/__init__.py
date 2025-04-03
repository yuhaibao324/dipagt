from typing import Dict, Type
from .base_tool import BaseTool
from .answer import AnswerTool
from .analyze import AnalyzeTool
from .browser_use import BrowserUseTool
from .code_writer import CodeWriterTool
from .command_line_tool import CommandLineTool
from .design_generator import DesignGeneratorTool
from .mcp_tool import MCPTool
from .tavily_search import TavilySearchTool
from .web_content_fetcher import WebContentFetcherTool

__all__ = [
    "BaseTool",
    "AnswerTool",
    "AnalyzeTool",
    "BrowserUseTool",
    "CodeWriterTool",
    "CommandLineTool",
    "DesignGeneratorTool",
    "MCPTool",
    "TavilySearchTool",
    "WebContentFetcherTool",
    "TOOL_CLASSES"
]

# Register all available tools
AVAILABLE_TOOLS: Dict[str, Type[BaseTool]] = {
    "Answer": AnswerTool,
    "Analyze": AnalyzeTool,
    "BrowserUse": BrowserUseTool,
    "CodeWriter": CodeWriterTool,
    "CommandLineTool": CommandLineTool,
    "DesignGenerator": DesignGeneratorTool,
    "MCPTool": MCPTool,
    "TavilySearch": TavilySearchTool,
    "WebContentFetcher": WebContentFetcherTool
} 