import pytest
from app.db.database import db
from app.db.models import Agent, Tool, Chat, Message, Task
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup
    try:
        db.connect(reuse_if_open=True)
    except Exception as e:
        print(f"Connection error: {e}")
    
    # Create tables if they don't exist
    try:
        db.create_tables([Agent, Tool, Chat, Message, Task], safe=True)
    except Exception as e:
        print(f"Table creation error: {e}")
    
    yield
    
    # Teardown
    try:
        db.drop_tables([Agent, Tool, Chat, Message, Task], safe=True)
    except Exception as e:
        print(f"Table drop error: {e}")
    
    if not db.is_closed():
        db.close()

def test_database_connection():
    assert not db.is_closed()
    
def test_create_agent():
    agent = Agent.create(
        name="Test Agent",
        description="A test agent",
        type="assistant"
    )
    assert Agent.select().count() == 1
    assert agent.name == "Test Agent"

def test_create_chat_with_messages():
    # Create an agent
    agent = Agent.create(
        name="Test Agent",
        description="A test agent",
        type="assistant"
    )
    
    # Create a chat
    chat = Chat.create(
        title="Test Chat",
        description="A test chat"
    )
    
    # Create a message
    message = Message.create(
        chat=chat,
        agent=agent,
        content="Hello, world!",
        role="assistant"
    )
    
    assert Chat.select().count() == 1
    assert Message.select().count() == 1
    assert message.chat.id == chat.id
    assert message.agent.id == agent.id

def test_create_task():
    # Create an agent
    agent = Agent.create(
        name="Test Agent",
        description="A test agent",
        type="assistant"
    )
    
    # Create a chat
    chat = Chat.create(
        title="Test Chat",
        description="A test chat"
    )
    
    # Create a task
    task = Task.create(
        name="Test Task",
        description="A test task",
        chat=chat,
        agent=agent,
        input_data={"test": "data"}
    )
    
    assert Task.select().count() == 1
    assert task.chat.id == chat.id
    assert task.agent.id == agent.id
    
if __name__ == "__main__":
    pytest.main([__file__]) 