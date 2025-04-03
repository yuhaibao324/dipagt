import json
from typing import Dict, List, Any, Optional, Type, AsyncIterator
import logging
from app.db.models import Agent, Tool, AgentTool

from app.tools import (
    BaseTool,
    AnswerTool,
    AnalyzeTool,
    BrowserUseTool,
    CodeWriterTool,
    CommandLineTool,
    DesignGeneratorTool,
    MCPTool,
    TavilySearchTool,
    WebContentFetcherTool
)

class ToolManager:
    """
    工具管理器，负责管理代理可用的工具
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tool_classes = {
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
        self.tool_instances = {}
    
    def get_agent_tools(self, agent_name: str) -> List[Dict[str, Any]]:
        """
        获取代理可用的工具列表
        
        Args:
            agent_name: 代理名称
            
        Returns:
            工具列表，按优先级排序
        """
        try:
            # 获取代理
            agent = Agent.get(Agent.name == agent_name)
            
            # 获取代理的工具关联
            agent_tools = (AgentTool
                          .select(AgentTool, Tool)
                          .join(Tool)
                          .where(AgentTool.agent == agent, Tool.is_active == True))
            
            tools = []
            for agent_tool in agent_tools:
                tool = agent_tool.tool
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "function_name": tool.function_name,
                    "parameters": tool.parameters,
                    "config": agent_tool.config
                })
            
            return tools
        
        except Agent.DoesNotExist:
            self.logger.error(f"Agent not found: {agent_name}")
            return []
        
        except Exception as e:
            self.logger.error(f"Error getting agent tools: {str(e)}")
            return []
    
    def get_tool_instance(self, tool_name: str) -> Optional[BaseTool]:
        """
        获取工具实例
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具实例
        """
        # 如果已经有实例，直接返回
        if tool_name in self.tool_instances:
            return self.tool_instances[tool_name]
        
        # 否则创建新实例
        if tool_name in self.tool_classes:
            try:
                tool_class = self.tool_classes[tool_name]
                tool_instance = tool_class()
                self.tool_instances[tool_name] = tool_instance
                return tool_instance
            except Exception as e:
                self.logger.error(f"Error creating tool instance: {str(e)}")
                return None
        
        self.logger.error(f"Tool not found: {tool_name}")
        return None
    
    def configure_tool(self, tool_name: str, config: Dict[str, Any]) -> bool:
        """
        配置工具
        
        Args:
            tool_name: 工具名称
            config: 配置参数
            
        Returns:
            是否配置成功
        """
        tool_instance = self.get_tool_instance(tool_name)
        if not tool_instance:
            return False
        
        try:
            # 根据工具类型调用不同的配置方法
            if tool_name == "Analyze":
                # AnalyzeTool 不需要配置，LLM 在初始化时已经设置好了
                return True
            
            elif tool_name == "TavilySearch":
                # TavilySearch 不需要配置，API key 在初始化时从环境变量获取
                return True
            
            elif tool_name == "DesignGenerator":
                if "api_key" in config:
                    tool_instance.configure(
                        api_key=config["api_key"],
                        output_dir=config.get("output_dir")
                    )
                    return True
            
            elif tool_name == "CodeWriter":
                # CodeWriter 现在也不需要配置，在初始化时已经设置好了
                if "api_key" in config:
                    tool_instance.configure(
                        api_key=config["api_key"],
                        model=config.get("model"),
                        output_dir=config.get("output_dir")
                    )
                    return True
            
            elif tool_name == "WebContentFetcher":
                tool_instance.configure(
                    headers=config.get("headers")
                )
                return True
            
            elif tool_name == "MCPTool":
                if "registry_url" in config:
                    tool_instance.configure(
                        registry_url=config["registry_url"],
                        default_auth_token=config.get("default_auth_token")
                    )
                    return True
            
            elif tool_name == "CommandLineTool":
                tool_instance.configure(
                    allowed_commands=config.get("allowed_commands"),
                    blocked_commands=config.get("blocked_commands")
                )
                return True
            
            return False
        
        except Exception as e:
            self.logger.error(f"Error configuring tool: {str(e)}")
            return False
    
    async def execute_tool(
        self, 
        agent_name: str, 
        tool_name: str, 
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        执行工具并流式返回结果。
        
        Args:
            agent_name: 代理名称
            tool_name: 工具名称
            **kwargs: 工具参数
            
        Yields:
            字典包含状态 ('status') 和数据 ('data') 或错误 ('error').
        """
        try:
            # 检查代理是否有权限使用该工具
            try:
                agent = Agent.get(Agent.name == agent_name)
            except Agent.DoesNotExist:
                 yield {"status": "error", "error": f"Agent '{agent_name}' not found"}
                 return # Stop execution if agent not found

            try:
                agent_tool = (AgentTool
                             .select()
                             .join(Tool)
                             .where(
                                 AgentTool.agent == agent,
                                 Tool.name == tool_name,
                                 Tool.is_active == True
                             )
                             .get())
            except AgentTool.DoesNotExist:
                yield {
                    "status": "error",
                    "error": f"Agent '{agent_name}' does not have permission to use tool '{tool_name}' or tool is inactive"
                }
                return # Stop execution
            
            # 获取工具实例
            tool_instance = self.get_tool_instance(tool_name)
            if not tool_instance:
                yield {
                    "status": "error",
                    "error": f"Tool '{tool_name}' not found or could not be instantiated"
                }
                return # Stop execution
            
            # 应用代理特定的工具配置（如果有）
            if hasattr(agent_tool, 'config') and agent_tool.config:
                # Assuming configure_tool returns True/False, but we might not need to check here
                # if the goal is just to apply the config if it exists.
                self.configure_tool(tool_name, agent_tool.config)
            
            # 执行工具并流式返回结果
            # The tool's run method now returns an async iterator
            async for chunk in tool_instance.run(**kwargs):
                yield chunk # Pass the chunk (which already includes status/data/error)
        
        except Exception as e:
            self.logger.exception(f"Unexpected error executing tool '{tool_name}' for agent '{agent_name}': {str(e)}")
            yield {
                "status": "error",
                "error": f"Unexpected error during tool execution: {str(e)}"
            } 