import json
import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from app.db.database import db, init_db
from app.db.models import Agent, Tool, AgentTool

# 加载环境变量
load_dotenv()

# Get the data directory path
DATA_DIR = os.path.dirname(os.path.abspath(__file__))

async def import_agents():
    """
    从agents.json导入代理数据
    """
    try:
        with open(os.path.join(DATA_DIR, 'agents.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        agents = data.get('agents', [])
        print(f"Found {len(agents)} agents to import")
        
        for agent_data in agents:
            # 检查代理是否已存在
            existing_agent = Agent.select().where(Agent.name == agent_data['name']).first()
            
            if existing_agent:
                print(f"Updating existing agent: {agent_data['name']}")
                existing_agent.description = agent_data['description']
                existing_agent.type = agent_data['type']
                existing_agent.config = agent_data['config']
                existing_agent.is_active = agent_data['is_active']
                existing_agent.avatar = agent_data['avatar']
                existing_agent.save()
            else:
                print(f"Creating new agent: {agent_data['name']}")
                Agent.create(
                    name=agent_data['name'],
                    description=agent_data['description'],
                    type=agent_data['type'],
                    config=agent_data['config'],
                    is_active=agent_data['is_active'],
                    avatar=agent_data['avatar']
                )
        
        print("Agents import completed successfully")
    
    except Exception as e:
        print(f"Error importing agents: {str(e)}")
        raise

async def import_tools():
    """
    从tools.json导入工具数据
    """
    try:
        with open(os.path.join(DATA_DIR, 'tools.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        tools = data.get('tools', [])
        print(f"Found {len(tools)} tools to import")
        
        for tool_data in tools:
            # 检查工具是否已存在
            existing_tool = Tool.select().where(Tool.name == tool_data['name']).first()
            
            if existing_tool:
                print(f"Updating existing tool: {tool_data['name']}")
                existing_tool.description = tool_data['description']
                existing_tool.function_name = tool_data['function_name']
                existing_tool.parameters = tool_data['parameters']
                existing_tool.is_active = tool_data['is_active']
                existing_tool.save()
            else:
                print(f"Creating new tool: {tool_data['name']}")
                Tool.create(
                    name=tool_data['name'],
                    description=tool_data['description'],
                    function_name=tool_data['function_name'],
                    parameters=tool_data['parameters'],
                    is_active=tool_data['is_active']
                )
        
        print("Tools import completed successfully")
    
    except Exception as e:
        print(f"Error importing tools: {str(e)}")
        raise

async def import_agent_tools():
    """
    从agent_tools.json导入代理和工具的关联关系
    """
    try:
        with open(os.path.join(DATA_DIR, 'agent_tools.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        agent_tools_data = data.get('agent_tools', [])
        print(f"Found {len(agent_tools_data)} agent-tool relationships to import")
        
        # 先清除现有的关联关系
        AgentTool.delete().execute()
        
        for agent_tool_data in agent_tools_data:
            agent_name = agent_tool_data['agent_name']
            tools = agent_tool_data['tools']
            
            # 获取代理
            try:
                agent = Agent.get(Agent.name == agent_name)
            except Agent.DoesNotExist:
                print(f"Agent not found: {agent_name}, skipping")
                continue
            
            print(f"Processing tools for agent: {agent_name}")
            
            for tool_data in tools:
                tool_name = tool_data['tool_name']
                config = tool_data['config']
                
                # 获取工具
                try:
                    tool = Tool.get(Tool.name == tool_name)
                except Tool.DoesNotExist:
                    print(f"Tool not found: {tool_name}, skipping")
                    continue
                
                # 创建关联关系
                AgentTool.create(
                    agent=agent,
                    tool=tool,
                    config=config
                )
                
                print(f"  - Added tool '{tool_name}' to agent '{agent_name}'")
        
        print("Agent-Tool relationships import completed successfully")
    
    except Exception as e:
        print(f"Error importing agent-tool relationships: {str(e)}")
        raise

async def main():
    """
    主函数
    """
    try:
        # 连接数据库
        db.connect()
        
        # 创建表（如果不存在）
        init_db()
        
        # 导入代理和工具
        await import_agents()
        await import_tools()
        
        # 导入代理和工具的关联关系
        await import_agent_tools()
        
        print("Data import completed successfully")
    
    except Exception as e:
        print(f"Error during import: {str(e)}")
    
    finally:
        # 关闭数据库连接
        if not db.is_closed():
            db.close()

if __name__ == "__main__":
    asyncio.run(main()) 
