import json
import aiohttp
from typing import Any, Dict, List, Optional, AsyncIterator
import logging

from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class MCPTool(BaseTool):
    """
    从远程站点查找已有的MCP服务并调用
    """
    
    def __init__(self):
        super().__init__(
            name="MCPTool",
            description="从远程站点查找已有的MCP服务并调用"
        )
        self.registry_url = None
        self.default_auth_token = None
    
    def configure(self, registry_url: str, default_auth_token: Optional[str] = None):
        """
        配置MCP工具
        
        Args:
            registry_url: MCP服务注册中心URL
            default_auth_token: 默认认证令牌
        """
        self.registry_url = registry_url
        self.default_auth_token = default_auth_token
    
    async def list_services(self) -> List[Dict[str, Any]]:
        """
        列出可用的MCP服务
        
        Returns:
            服务列表
        """
        if not self.registry_url:
            raise ValueError("MCP Tool not configured. Call configure() first.")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.registry_url}/services") as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Failed to list MCP services: {response.status}, {error_text}")
                    
                    data = await response.json()
                    return data.get("services", [])
        
        except Exception as e:
            logger.error(f"Error listing MCP services: {str(e)}")
            raise
    
    async def _run(self, 
                   service_name: str, 
                   endpoint: str, 
                   parameters: Optional[Dict[str, Any]] = None, 
                   auth_token: Optional[str] = None,
                   **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """
        执行远程MCP服务并流式返回结果
        
        Args:
            service_name: MCP服务名称
            endpoint: 服务端点 (e.g., /search)
            parameters: 调用参数
            auth_token: 认证令牌（覆盖默认）
            **kwargs: 可选参数，包含 conversation_context
            
        Yields:
            字典，包含状态信息、响应块(如果stream_response=True且成功)、最终结果或错误.
            Example status: {"type": "status", "message": "Calling service..."}
            Example chunk: {"type": "response_chunk", "data": "..."} (for streaming)
            Example final: {"type": "final_result", "status": "success", "result": ..., ...}
            Example error: {"type": "error", "error": "...", "service_name": ...}
        """
        if not self.registry_url:
            yield {"type": "error", "error": "MCP Tool not properly configured (missing registry URL). Call configure() first."}
            return
        
        conversation_context = kwargs.get("conversation_context")
        # Note: conversation_context is retrieved but not used for MCP calls.

        # 使用默认令牌（如果有）
        token = auth_token or self.default_auth_token
        
        headers = {
            "Accept": "application/json"
        }
        if kwargs.get("stream_response", False):
             headers["Accept"] = "application/x-ndjson"
        else:
             headers["Content-Type"] = "application/json"

        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        # 构建完整的服务URL
        if endpoint.startswith("/"):
            service_url = f"{self.registry_url.rstrip('/')}{endpoint}"
        elif not endpoint.startswith(("http://", "https://")):
            # Assuming registry URL points to the base, and endpoint is relative
            service_url = f"{self.registry_url.rstrip('/')}/services/{service_name}{endpoint if endpoint.startswith('/') else '/'+endpoint}"
        else:
            service_url = endpoint # Absolute URL provided
            
        yield {"type": "status", "message": f"Preparing to call MCP service: {service_name} at {service_url}"}
        logger.info(f"Calling MCP service ({service_name}): {service_url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(service_url, headers=headers, json=parameters or {}) as response:
                    yield {"type": "status", "message": f"Received response status: {response.status}"}
                    
                    if response.status != 200:
                        response_text = await response.text()
                        logger.error(f"MCP service call failed ({response.status}): {response_text[:500]}")
                        yield {
                            "type": "error",
                            "service_name": service_name,
                            "endpoint": endpoint,
                            "status_code": response.status,
                            "error": f"MCP service error ({response.status}): {response_text[:500]}..."
                        }
                        return
                    
                    # Handle streaming response if requested and content type matches
                    is_streaming = kwargs.get("stream_response", False) and "application/x-ndjson" in response.headers.get("Content-Type", "")
                    
                    if is_streaming:
                        yield {"type": "status", "message": "Streaming response (ndjson)..."}
                        full_response_data = [] # Store chunks if needed for final summary
                        async for line in response.content:
                             line_str = line.decode('utf-8').strip()
                             if line_str:
                                 try:
                                     chunk_data = json.loads(line_str)
                                     yield {"type": "response_chunk", "data": chunk_data}
                                     full_response_data.append(chunk_data) # Store chunk
                                 except json.JSONDecodeError:
                                     logger.warning(f"Failed to decode ndjson line: {line_str}")
                                     yield {"type": "response_chunk", "data": line_str, "warning": "Non-JSON line received"}
                                     full_response_data.append(line_str) # Store raw line
                        
                        yield {
                            "type": "content_chunk",
                            "status": "success",
                            "service_name": service_name,
                            "endpoint": endpoint,
                            "streamed": True,
                            "content": f"{len(full_response_data)} chunks received"
                        }
                             
                    else:
                        # Handle non-streaming JSON response
                        yield {"type": "status", "message": "Processing non-streaming JSON response..."}
                        try:
                            result = await response.json()
                        except json.JSONDecodeError:
                             response_text = await response.text() # Read text if json fails
                             logger.warning(f"MCP response was not valid JSON. Raw: {response_text[:200]}...")
                             result = {"raw_response": response_text}
                             yield {"type": "warning", "message": "Response was not valid JSON, returning raw text."} 

                        yield {
                            "type": "final_result",
                            "status": "success",
                            "service_name": service_name,
                            "endpoint": endpoint,
                            "streamed": False,
                            "result": result
                        }
        
        except aiohttp.ClientError as e:
            logger.error(f"Network error calling MCP service '{service_name}': {str(e)}")
            yield {"type": "error", "service_name": service_name, "endpoint": endpoint, "error": f"Network error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error calling MCP service '{service_name}': {str(e)}")
            yield {"type": "error", "service_name": service_name, "endpoint": endpoint, "error": f"An unexpected error occurred: {str(e)}"}
    
    def get_schema(self) -> Dict[str, Any]:
        """
        获取工具的JSON Schema
        """
        return {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "MCP服务名称"
                },
                "endpoint": {
                    "type": "string",
                    "description": "服务端点 (相对路径或完整URL)"
                },
                "parameters": {
                    "type": "object",
                    "description": "调用参数"
                },
                "auth_token": {
                    "type": "string",
                    "description": "认证令牌 (覆盖默认)"
                },
                "stream_response": {
                    "type": "boolean",
                    "description": "尝试流式处理响应 (如果服务端点支持NDJSON)",
                    "default": False
                }
            },
            "required": ["service_name", "endpoint"]
        } 