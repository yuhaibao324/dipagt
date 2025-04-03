import json
import aiohttp
from typing import Any, Dict, Optional, AsyncIterator
from bs4 import BeautifulSoup
import logging

from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class WebContentFetcherTool(BaseTool):
    """
    获取网页内容的工具
    """
    
    def __init__(self):
        super().__init__(
            name="WebContentFetcher",
            description="获取网页内容，支持HTML解析和内容提取"
        )
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    def configure(self, headers: Optional[Dict[str, str]] = None):
        """
        配置请求头
        
        Args:
            headers: 自定义请求头
        """
        if headers:
            self.headers.update(headers)
    
    async def _run(self, 
                   url: str, 
                   selector: Optional[str] = None, 
                   extract_type: str = "text", 
                   attribute: Optional[str] = None,
                   **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """
        获取网页内容并流式返回
        
        Args:
            url: 要获取内容的URL
            selector: CSS选择器或XPath (可选)
            extract_type: 提取类型 (text, html, attribute)
            attribute: 要提取的属性名称 (当extract_type=attribute时)
            **kwargs: 可选参数，包含 conversation_context
            
        Yields:
            字典，包含提取的内容片段或状态信息.
            Example chunk: {"type": "content_chunk", "data": "..."}
            Example chunk: {"type": "attribute_chunk", "data": "..."}
            Example chunk: {"type": "element_html_chunk", "data": "..."}
            Example status: {"type": "status", "message": "..."}
            Example final: {"type": "final_summary", "status": "success", "url": url, ...}
            Example error: {"type": "error", "error": "...", "url": url}
        """
        try:
            conversation_context = kwargs.get("conversation_context")
            # Note: conversation_context is retrieved but not currently used for fetching web content.

            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
                yield {"type": "status", "message": f"Fetching content from {url}..."}
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        yield {
                            "type": "error",
                            "url": url,
                            "status_code": response.status,
                            "error": f"Failed to fetch content: HTTP {response.status}"
                        }
                        return
                    
                    yield {"type": "status", "message": "Parsing HTML content..."}
                    html_content = await response.text()
                    
                    # 如果没有选择器，流式返回整个页面内容（分块）
                    if not selector:
                        yield {"type": "status", "message": "No selector provided, streaming raw HTML (truncated)."}
                        chunk_size = 1000
                        content_length = len(html_content)
                        for i in range(0, content_length, chunk_size):
                           yield {"type": "content_chunk", "data": html_content[i:i+chunk_size]}
                        
                        yield {
                            "type": "final_summary",
                            "status": "success",
                            "url": url,
                            "content_type": "html",
                            "truncated": content_length > 10000, # Indicate if truncated for summary
                            "content_length": content_length
                        }
                        return
                    
                    # 使用BeautifulSoup解析HTML
                    soup = BeautifulSoup(html_content, "html.parser")
                    
                    # 查找选择器匹配的元素
                    elements = soup.select(selector)
                    
                    if not elements:
                        yield {
                            "type": "error",
                            "url": url,
                            "selector": selector,
                            "error": f"No elements found matching selector: {selector}"
                        }
                        return
                    
                    yield {"type": "status", "message": f"Found {len(elements)} elements matching '{selector}'. Extracting..."}
                    results_collected = [] # To collect for final summary
                    
                    # 根据提取类型获取内容并流式返回
                    for i, element in enumerate(elements):
                        extracted_data = None
                        yield_type = "content_chunk" # Default
                        if extract_type == "text":
                            extracted_data = element.get_text(strip=True)
                        elif extract_type == "html":
                            extracted_data = str(element)
                            yield_type = "element_html_chunk"
                        elif extract_type == "attribute" and attribute:
                            yield_type = "attribute_chunk"
                            if element.has_attr(attribute):
                                extracted_data = element[attribute]
                            else:
                                extracted_data = None # Explicitly None if attribute missing
                        
                        if extracted_data is not None: # Only yield if data was extracted
                           yield {"type":"content_chunk", "content": extracted_data, "index": i}
                           results_collected.append(extracted_data) # Collect for summary
                           
                    yield {
                        "type": "final_summary",
                        "status": "success",
                        "url": url,
                        "selector": selector,
                        "extract_type": extract_type,
                        "attribute": attribute if extract_type == "attribute" else None,
                        # "results": results_collected, # Optionally exclude full list from final summary
                        "count": len(results_collected)
                    }
        
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching web content from {url}: {str(e)}")
            yield {"type": "error", "url": url, "error": f"Network error fetching content: {str(e)}"}
        except Exception as e:
            logger.error(f"Error processing web content from {url}: {str(e)}")
            yield {"type": "error", "url": url, "error": f"Error processing web content: {str(e)}"}
    
    def get_schema(self) -> Dict[str, Any]:
        """
        获取工具的JSON Schema
        """
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "要获取内容的URL"
                },
                "selector": {
                    "type": "string",
                    "description": "CSS选择器或XPath，用于提取特定内容"
                },
                "extract_type": {
                    "type": "string",
                    "description": "提取类型",
                    "enum": ["text", "html", "attribute"],
                    "default": "text"
                },
                "attribute": {
                    "type": "string",
                    "description": "要提取的属性名称，当extract_type为attribute时使用"
                }
            },
            "required": ["url"]
        } 