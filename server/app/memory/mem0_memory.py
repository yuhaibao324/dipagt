from typing import List, Dict, Optional, Any
from mem0 import Memory
from app.utils.logger import get_logger

logger = get_logger()

class Mem0Memory:
    """
    A wrapper around the mem0 library to provide conversational memory management.
    It allows adding messages and searching for relevant history based on a query.
    """
    def __init__(self):
        # Initialize mem0 client. Configuration might be needed based on deployment.
        # For now, using default in-memory storage.
        try:
            self.mem0_client = Memory.from_config({
              "vector_store": {
                  "provider": "qdrant",
                  "config": {
                      "host": "localhost",
                      "port": 6333,
                  }
              },
            })
            logger.info("Mem0Memory initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Mem0Memory: {e}")
            # Depending on requirements, might want to raise or handle differently
            self.mem0_client = None

    async def add_message(self, chat_id: str, role: str, content: str, user_id: Optional[str] = None):
        """
        Adds a message to the memory associated with a specific chat ID.

        Args:
            chat_id: The unique identifier for the chat session. Used as the memory ID.
            role: The role of the message sender ('user' or 'assistant').
            content: The text content of the message.
            user_id: Optional user identifier for multi-tenant scenarios.
        """
        if not self.mem0_client:
            logger.error("Mem0 client not initialized. Cannot add message.")
            return

        try:
            # Use chat_id as the run_id for mem0
            # Include role in the message content or metadata if needed for retrieval filtering
            message_data = [{"role": role, "content": content}] # Simple combination for now
            
            # In mem0, user_id helps isolate memories in multi-user scenarios if needed.
            # If your app is single-user or chat_id is globally unique, user_id might be optional.
            # Let's use chat_id as the primary identifier.
            result = self.mem0_client.add(message_data, run_id=chat_id, user_id=user_id, metadata={"role": role}) 
            logger.debug(f"Added message to mem0 for chat {chat_id} result: {result}")
        except Exception as e:
            logger.error(f"Error adding message to mem0 for chat {chat_id}: {e}")

    async def get_relevant_history(
        self, 
        chat_id: str, 
        query: str, 
        limit: int = 5, 
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves relevant historical messages from the memory for a given chat and query.

        Args:
            chat_id: The unique identifier for the chat session.
            query: The query (e.g., the latest user message) to find relevant history for.
            limit: The maximum number of relevant messages to retrieve.
            user_id: Optional user identifier.

        Returns:
            A list of relevant messages, potentially formatted as {"role": ..., "content": ...}.
            Returns an empty list if the client isn't initialized or an error occurs.
        """
        if not self.mem0_client:
            logger.error("Mem0 client not initialized. Cannot get history.")
            return []

        try:
            # Search memory using the query
            relevant_memories = self.mem0_client.search(
                query=query, 
                run_id=chat_id, 
                user_id=user_id, 
                limit=limit
            )
            
            # Process the results from mem0. 
            # The default output might be a list of strings or dicts.
            # We need to parse them back into the {"role": ..., "content": ...} format if possible.
            history = []
            # Iterate over the list of results within the dictionary
            for memory in relevant_memories.get('results', []):
                # Assuming memory['text'] stores the "role: content" format used in add_message
                text = memory.get("memory") 
                history.append({"role": memory.get("metadata", {}).get("role", "user"), "content": text}) 
                    
            logger.debug(f"Retrieved {len(history)} relevant messages for chat {chat_id} using query: '{query}'")
            return history
        except Exception as e:
            logger.error(f"Error searching mem0 for chat {chat_id}: {e}")
            return []

# Global instance (or manage via dependency injection if preferred)
memory_manager = Mem0Memory() 