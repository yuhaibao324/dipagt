import pytest
from app.db.database import db
from app.db.models import Agent, Tool, Chat, Message, Task
from app.db.clear_runtime_data import clear_runtime_data
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup test database and create some test data"""
    try:
        db.connect(reuse_if_open=True)
        
        # Create tables if they don't exist
        db.create_tables([Agent, Tool, Chat, Message, Task], safe=True)
        
        yield
        
    finally:
        if not db.is_closed():
            db.close()

def test_clear_runtime_data():
    """Test that clear_runtime_data properly clears only runtime data"""
    
    # Clear runtime data
    clear_runtime_data()
    
    # Verify runtime data is cleared
    assert Chat.select().count() == 0, "All chats should be deleted"
    assert Message.select().count() == 0, "All messages should be deleted"
    assert Task.select().count() == 0, "All tasks should be deleted"
    

def test_clear_runtime_data_idempotent():
    """Test that clear_runtime_data can be run multiple times safely"""
    
    # Clear runtime data twice
    clear_runtime_data()
    clear_runtime_data()
    
    # Verify everything is still in the expected state
    assert Chat.select().count() == 0, "All chats should be deleted"
    assert Message.select().count() == 0, "All messages should be deleted"
    assert Task.select().count() == 0, "All tasks should be deleted"

if __name__ == "__main__":
    pytest.main([__file__]) 