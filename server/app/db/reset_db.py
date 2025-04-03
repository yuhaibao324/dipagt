import pytest
from app.db.database import db
from app.db.models import Agent, Tool, AgentTool, Chat, Message, Task
from dotenv import load_dotenv

load_dotenv()

def reset_database():
    """
    删除所有模型对应的表
    注意：这个操作会删除所有数据，请谨慎使用
    """
    try:
        # 确保数据库连接是打开的
        if db.is_closed():
            db.connect(reuse_if_open=True)
        
        # 按照依赖关系顺序删除表
        # 先删除有外键依赖的表
        tables = [Message, Task, AgentTool, Agent, Tool, Chat]
        db.drop_tables(tables, safe=True)
        
        print("所有表已成功删除")
        
    except Exception as e:
        print(f"删除表时发生错误: {e}")
        raise e
    finally:
        if not db.is_closed():
            db.close()

def test_reset_database():
    """
    测试重置数据库功能
    """
    # 创建一些测试数据
    agent = Agent.create(
        name="Test Agent",
        description="A test agent",
        type="assistant"
    )
    
    chat = Chat.create(
        title="Test Chat",
        description="A test chat"
    )
    
    # 验证数据已创建
    assert Agent.select().count() == 1
    assert Chat.select().count() == 1
    
    # 重置数据库
    reset_database()
    
    # 验证所有表都已删除
    assert Agent.select().count() == 0
    assert Chat.select().count() == 0
    assert Message.select().count() == 0
    assert Task.select().count() == 0
    assert Tool.select().count() == 0
    assert AgentTool.select().count() == 0

if __name__ == "__main__":
    pytest.main([__file__]) 