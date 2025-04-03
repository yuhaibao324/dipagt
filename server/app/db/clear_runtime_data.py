from app.db.database import db
from app.db.models import Chat, Message, Task
from app.utils.logger import get_logger
from dotenv import load_dotenv

load_dotenv()
logger = get_logger()

def clear_runtime_data():
    """Clear all runtime data (Chat, Message, Task) from the database"""
    try:
        db.connect(reuse_if_open=True)
        logger.info("Connected to database")
        
        # Delete all data from runtime tables in correct order
        # (respecting foreign key constraints)
        with db.atomic():
            # First delete messages as they reference chats
            message_count = Message.delete().execute()
            logger.info(f"Deleted {message_count} messages")
            
            # Then delete tasks as they reference chats
            task_count = Task.delete().execute()
            logger.info(f"Deleted {task_count} tasks")
            
            # Finally delete chats
            chat_count = Chat.delete().execute()
            logger.info(f"Deleted {chat_count} chats")
            
        logger.info("Successfully cleared all runtime data")
        
    except Exception as e:
        logger.error(f"Error clearing runtime data: {e}")
        raise
    finally:
        if not db.is_closed():
            db.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    clear_runtime_data() 