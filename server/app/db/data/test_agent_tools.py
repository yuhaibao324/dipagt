import asyncio
import json
from dotenv import load_dotenv
from app.db import db, Agent
from app.tools.tool_manager import ToolManager

# 加载环境变量
load_dotenv()

async def test_agent_tools():
    """
    测试代理和工具的关联关系
    """
    try:
        # 连接数据库
        db.connect()
        
        # 创建工具管理器
        tool_manager = ToolManager()
        
        # 获取所有代理
        agents = Agent.select().where(Agent.is_active == True)
        
        for agent in agents:
            print(f"\n===== Agent: {agent.name} =====")
            print(f"Description: {agent.description}")
            print(f"Type: {agent.type}")
            
            # 获取代理可用的工具
            tools = tool_manager.get_agent_tools(agent.name)
            
            print(f"\nAvailable Tools ({len(tools)}):")
            for i, tool in enumerate(tools, 1):
                print(f"\n{i}. {tool['name']}")
                print(f"   Description: {tool['description']}")
                print(f"   Function: {tool['function_name']}")
                
                if tool['config']:
                    print(f"   Config: {json.dumps(tool['config'], indent=2)}")
        
        # 测试工具执行（模拟，不实际执行）
        print("\n\n===== Tool Execution Simulation =====")
        
        # 模拟Pliman使用CodeWriter工具
        print("\nSimulating Pliman using CodeWriter tool:")
        result = await tool_manager.execute_tool(
            agent_name="Pliman",
            tool_name="CodeWriter",
            language="python",
            task="Write a hello world program",
            code_style="standard"
        )
        print(f"Result status: {result['status']}")
        if result['status'] == 'error':
            print(f"Error: {result['error']}")
        
        # 模拟Bob尝试使用CodeWriter工具（应该失败，因为没有权限）
        print("\nSimulating Bob trying to use CodeWriter tool (should fail):")
        result = await tool_manager.execute_tool(
            agent_name="Bob",
            tool_name="CodeWriter",
            language="python",
            task="Write a hello world program"
        )
        print(f"Result status: {result['status']}")
        if result['status'] == 'error':
            print(f"Error: {result['error']}")
        
        # 模拟Alice使用DesignGenerator工具
        print("\nSimulating Alice using DesignGenerator tool:")
        result = await tool_manager.execute_tool(
            agent_name="Alice",
            tool_name="DesignGenerator",
            design_type="ui",
            description="A simple login form"
        )
        print(f"Result status: {result['status']}")
        if result['status'] == 'error':
            print(f"Error: {result['error']}")
    
    except Exception as e:
        print(f"Error during test: {str(e)}")
    
    finally:
        # 关闭数据库连接
        if not db.is_closed():
            db.close()

if __name__ == "__main__":
    asyncio.run(test_agent_tools()) 