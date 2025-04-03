from typing import List, Optional, Dict, Any, Tuple, AsyncIterator
from uuid import uuid4
from app.db.models import Chat, Message, Agent, Tool, AgentTool
from app.intention.recognizer import IntentionRecognizer
from app.intention.factory import IntentionRecognizerFactory
from app.llm.base_llm import BaseLLM
from app.plan.planner import Planner, Action
from app.utils.logger import get_logger
from app.tools.tool_manager import ToolManager
from app.memory.mem0_memory import memory_manager
from peewee import DoesNotExist, JOIN, fn

logger = get_logger()

class ChatManager:
    def __init__(self, llm: BaseLLM):
        self.llm = llm
        self.intention_recognizer = None
        self.planner = None
        self.agents = []  # Will be populated with available agents from database
        self.tool_manager = ToolManager()

    async def initialize(self):
        """Initialize the chat manager with required components"""
        self.intention_recognizer = await IntentionRecognizerFactory.create(self.llm)
        self.planner = Planner(self.llm)
        
        # Load all active agents and their tools from database
        try:
            # Query for active agents and their tools using JOIN
            query = (Agent
                    .select(Agent, Tool, AgentTool)
                    .join(AgentTool, JOIN.LEFT_OUTER)
                    .join(Tool, JOIN.LEFT_OUTER)
                    .where(Agent.is_active == True))
            
            # Group tools by agent
            agent_tools = {}
            for agent in query:
                if agent.id not in agent_tools:
                    agent_tools[agent.id] = {
                        "id": str(agent.id),
                        "name": agent.name,
                        "description": agent.description,
                        "type": agent.type,
                        "config": agent.config,
                        "avatar": agent.avatar,
                        "tools": []
                    }
                
                # Add tool if it exists and is active
                for agent_tool in agent.agent_tools:
                    tool = agent_tool.tool
                    if tool and tool.is_active:
                        agent_tools[agent.id]["tools"].append({
                            "name": tool.name,
                            "description": tool.description,
                            "function_name": tool.function_name,
                            "parameters": tool.parameters,
                            # Note: The actual execute function needs to be loaded separately
                            "execute": None  # Will be populated by the tool registry
                        })
            
            # Convert to list and store in self.agents
            self.agents = list(agent_tools.values())
            logger.info(f"Loaded {len(self.agents)} agents from database")
            
            # Log the tools for each agent
            for agent in self.agents:
                logger.info(f"Agent {agent['name']} loaded with {len(agent['tools'])} tools")
                
        except Exception as e:
            logger.error(f"Error loading agents from database: {str(e)}")
            raise

    async def _generate_chat_title(self, message_content: str) -> str:
        """Uses LLM to generate a concise title for a new chat."""
        try:
            prompt = f"Generate a very short, concise title (max 5 words) for a chat based on this first user message: \n\nUser Message: \"{message_content}\"\n\nTitle:"
            
            llm_response = await self.llm.aChat([
                {"role": "user", "content": prompt}
            ])
            
            generated_title = llm_response.get('content', '').strip().replace('\"', '')
            
            if generated_title:
                logger.info(f"Generated chat title: '{generated_title}'")
                return generated_title[:100] # Limit title length
            else:
                logger.warning("LLM failed to generate a title, using fallback.")
                # Fallback: first few words of the message
                fallback_title = ' '.join(message_content.split()[:5]) + '...'
                return fallback_title
        except Exception as e:
            logger.error(f"Error generating chat title with LLM: {e}")
            # Fallback: first few words of the message
            fallback_title = ' '.join(message_content.split()[:5]) + '...'
            return fallback_title

    async def get_or_create_chat(
        self,
        chat_id: Optional[str] = None,
        owner: Optional[str] = None,
        first_message: Optional[str] = None # Added for title generation on create
    ) -> Chat:
        """Get an existing chat from database or create a new one."""
        if chat_id:
            try:
                chat = Chat.get(Chat.id == chat_id)
                logger.info(f"Retrieved existing chat: {chat_id}")
                return chat
            except DoesNotExist:
                logger.warning(f"Chat {chat_id} not found, will proceed to create if owner is provided.")
                # Fall through to creation logic if owner is present

        # --- Create Chat Logic --- 
        if not owner:
            # Raise error if trying to create without an owner
            logger.error("Attempted to create chat without owner.")
            raise ValueError("Owner is required to create a new chat")
        
        if not first_message:
            # Should not happen if called correctly from process_message for new chat
            logger.error("Attempted to create chat without first message for title generation.")
            fallback_title = "New Chat"
        else:
             # Generate Title using LLM based on the first message
            fallback_title = await self._generate_chat_title(first_message)
        
        # Create the chat record
        chat = Chat.create(
            title=fallback_title,
            status='active',
            metadata={},
            owner=owner
        )
        logger.info(f"Created new chat {chat.id} with title '{fallback_title}'")
        return chat

    async def execute_action(
        self, 
        message: str,
        action: Action, 
        chat: Chat, 
        conversation_context: List[Dict[str, Any]] # Added context parameter
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Execute a single action using the specified agent, yielding message chunks 
        and a final confirmation with the saved message details.
        
        Args:
            action: The action to execute.
            chat: The chat object.
            conversation_context: The current list of messages in the conversation.

        Yields:
            Dicts representing events: {"type": "message_chunk", "content": "..."} or 
                                      {"type": "message_saved", "message": {...}} or
                                      {"type": "error", "error": "..."}
        """
        agent = None # Define agent here to ensure it's available in finally block if needed
        try:
            # Find the agent by name
            agent = next((a for a in self.agents if a["name"] == action.agent_name), None)
            if not agent:
                logger.error(f"Agent {action.agent_name} not found")
                yield {"type": "error", "error": f"Agent {action.agent_name} not found"}
                return

            content_accumulator = []
            tool_stream = self.tool_manager.execute_tool(
                agent_name=action.agent_name,
                tool_name=action.action_type,
                **action.parameters,
                conversation_context=conversation_context,
                message=message
            )
            
            # Process the stream from the tool
            async for chunk in tool_stream:
                if chunk.get("status") == "error":
                    error_message = chunk.get("error", "Unknown tool error")
                    logger.error(f"Error from tool '{action.action_type}' for agent '{action.agent_name}': {error_message}")
                    yield {"type": "error", "error": error_message}
                    # Decide if we should stop or continue after a tool error
                    # For now, let's stop the action on tool error
                    return 
                
                # Assuming successful chunks have status="success" and data
                tool_data = chunk.get("data", {})
                # Assuming data contains {"type": "content_chunk", "content": "..."} or other types
                if tool_data.get("type") == "content_chunk":
                    chunk_content = tool_data.get("content")
                    if chunk_content:
                        content_accumulator.append(str(chunk_content)) # Ensure string
                        # Yield the content chunk up the chain
                        yield {"type": "message_chunk", "content": chunk_content}
                # Handle other potential data chunk types from tool if necessary

            # --- Stream finished, save the complete message --- 
            full_content = "".join(content_accumulator)
            if not full_content:
                 logger.warning(f"Tool {action.action_type} executed by {action.agent_name} produced no text content after streaming.")
                 full_content = "(Action produced no text content)"

            # Save the complete message to the database
            db_message = Message.create(
                chat=chat,
                agent_id=agent["id"], 
                content=full_content,
                role="assistant",
                type="text", # Assuming text for now
                metadata={
                    "action_type": action.action_type,
                    "agent_name": action.agent_name,
                    "explanation": action.explanation
                    # Add any other relevant metadata if needed
                }
            )
            
            # Prepare the final message data object
            db_message_data = {
                "id": str(db_message.id),
                "chat_id": str(chat.id),
                "content": db_message.content,
                "role": db_message.role,
                "type": db_message.type,
                "agent_id": str(db_message.agent_id) if db_message.agent_id else None,
                "agent_name": agent.get("name"),
                "agent_avatar": agent.get("avatar"),
                "metadata": db_message.metadata,
                "created_at": db_message.created_at.isoformat(),
                "action_explanation": action.explanation 
            }
            # Yield the final confirmation with the saved message object
            yield {"type": "message_saved", "message": db_message_data}

        except Exception as e:
            logger.exception(f"Error executing action {action.action_type} by {action.agent_name}: {e}")
            yield {"type": "error", "error": str(e), "agent_name": action.agent_name, "action_type": action.action_type}

    async def process_message_stream(
        self, 
        message: str, 
        chat_id: Optional[str] = None, 
        owner: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Processes a user message and yields progress updates as an async iterator."""
        try:
            # 1. Get or create chat
            yield {"type": "progress", "data": {"step": "status", "message": "Initializing chat..."}}
            chat = await self.get_or_create_chat(
                chat_id=chat_id, 
                owner=owner, 
                first_message=message if not chat_id else None 
            )
            current_chat_id = str(chat.id)
            # Create a dictionary representation of the chat object

            # If chat is newly created, send the full chat object
            if chat_id is None:
                chat_data = {
                    "id": str(chat.id),
                    "title": chat.title,
                    "description": chat.description,
                    "status": chat.status,
                    # message_count will likely be 0 or 1 initially
                    "message_count": 1 if not chat_id else chat.select_extend(fn.COUNT(Message.id).alias('mc')).where(Message.chat == chat).first().mc, 
                    "created_at": chat.created_at.isoformat(),
                    "updated_at": chat.updated_at.isoformat()
                }
                yield {"type": "progress", "data": {"step": "chat_created", "chat": chat_data}} # Send full chat object

            # 2. Get Relevant History using Memory Manager
            yield {"type": "progress", "data": {"step": "status", "message": "Retrieving relevant history..."}}
            history = await memory_manager.get_relevant_history(
                chat_id=current_chat_id,
                query=message,
                user_id=owner, 
                limit=10
            )
            yield {"type": "progress", "data": {"step": "history_retrieved", "count": len(history)}}
            logger.info(f"Retrieved {len(history)} relevant messages from memory for chat {current_chat_id}")

            # 3. Store User Message in Database and Memory
            yield {"type": "progress", "data": {"step": "status", "message": "Saving user message..."}}
            user_message_db = Message.create(
                chat=chat,
                content=message,
                role="user",
                type="text"
            )
            # Yield confirmation with DB ID
            user_message_data = {
                "id": str(user_message_db.id),
                "chat_id": current_chat_id,
                "role": user_message_db.role,
                "content": user_message_db.content,
                "created_at": user_message_db.created_at.isoformat()
            }
            yield {"type": "progress", "data": {"step": "user_message_saved", "message": user_message_data}}
            
            await memory_manager.add_message(
                chat_id=current_chat_id, 
                role="user", 
                content=message, 
                user_id=owner
            )

            # 4. Recognize Intention
            yield {"type": "progress", "data": {"step": "status", "message": "Recognizing intention..."}}
            current_context = history + [{"role": "user", "content": message}]
            intention = await self.intention_recognizer.recognize(
                user_input=message,
                conversation_history=current_context 
            )
            yield {"type": "progress", "data": {"step": "intention_recognized", "intention": intention}}

            # 5. Create Action Plan
            yield {"type": "progress", "data": {"step": "status", "message": "Generating action plan..."}}
            actions = await self.planner.create_plan(intention, self.agents, current_context)
            yield {"type": "progress", "data": {"step": "plan_generated", "actions": [action.dict() for action in actions]}}

            # 6. Execute Actions (Modified)
            yield {"type": "progress", "data": {"step": "status", "message": f"Executing {len(actions)} actions..."}}
            all_assistant_messages = [] # Store final assistant message objects
            for i, action in enumerate(actions):
                yield {"type": "progress", "data": {"step": "action_started", "index": i, "agent_name": action.agent_name, "action_type": action.action_type}}
                assistant_message_data = None # To store the final message from this action
                try:
                    # Iterate over the stream from execute_action, passing the current context
                    async for event in self.execute_action(message, action, chat, current_context):
                        if event.get("type") == "message_chunk":
                             yield {
                                 "type": "progress", 
                                 "data": {
                                     "step": "message_chunk", 
                                     "content": event["content"], 
                                     "index": i, # Include index for client to target correct message
                                     "agent_name": action.agent_name 
                                 }
                             }
                        elif event.get("type") == "message_saved":
                            assistant_message_data = event["message"]
                            # Yield confirmation that this action's message is fully saved
                            yield {"type": "progress", "data": {"step": "action_result", "index": i, "result": assistant_message_data}}
                            # NOTE: Context update happens *outside* this loop after break
                            break # Action finished successfully
                        elif event.get("type") == "error":
                             logger.error(f"Error during action {i} ({action.action_type} by {action.agent_name}): {event['error']}")
                             yield {"type": "progress", "data": {"step": "action_error", "index": i, "error": event["error"], "agent_name": action.agent_name}}
                             # Decide if we continue to next action or stop? Let's stop for now.
                             raise Exception(f"Action failed: {event['error']}") # Raise to break outer loop
                    
                    # If loop finished and we got a final message, store it and update context
                    if assistant_message_data:
                        all_assistant_messages.append(assistant_message_data)
                        # Add successful assistant message to context for next actions
                        context_message = {
                            "role": "assistant",
                            "content": f"""agent: {action.agent_name}
                            agent action: {action.action_type}
                            agent explanation: {action.explanation}
                            agent result: {assistant_message_data.get("content", "")}""",
                        }
                        current_context.append(context_message)
                        logger.debug(f"Appended action {i} result to context.")
                    else:
                         # Should not happen if execute_action always yields message_saved or error
                         logger.warning(f"Action {i} ({action.action_type}) stream finished without saved message or error.")
                         # Yield a generic error for this action? 
                         yield {"type": "progress", "data": {"step": "action_error", "index": i, "error": "Action stream ended unexpectedly", "agent_name": action.agent_name}}

                except Exception as action_exception:
                    # Catch exceptions from iterating execute_action or the re-raised error
                    logger.exception(f"Exception during action {i} ({action.action_type} by {action.agent_name}): {action_exception}")
                    # Yield error for this specific action (already yielded by execute_action if it was an internal error)
                    # If it wasn't yielded yet (e.g., exception before yield), yield it now.
                    if not str(action_exception).startswith("Action failed:"): # Avoid duplicate yield
                         yield {"type": "progress", "data": {"step": "action_error", "index": i, "error": str(action_exception), "agent_name": action.agent_name}}
                    # Stop processing further actions on error
                    raise
            
            # 7. Add Assistant Responses to Memory
            if all_assistant_messages:
                combined_content = "\n".join([msg.get("content", "") for msg in all_assistant_messages if msg.get("content")])
                if combined_content:
                     yield {"type": "progress", "data": {"step": "status", "message": "Saving assistant responses to memory..."}}
                     await memory_manager.add_message(
                         chat_id=current_chat_id, 
                         role="assistant", 
                         content=combined_content, 
                         user_id=owner
                     )

            # 8. Signal completion
            final_data = {}
            if all_assistant_messages:
                final_data["last_assistant_message"] = all_assistant_messages[-1]
            yield {"type": "done", "data": final_data}

        except Exception as e:
            logger.exception(f"Error processing message stream for chat {chat_id}: {e}")
            yield {"type": "progress", "data": {"step": "fatal_error", "error": str(e)}}
            yield {"type": "done", "data": {}} # Still signal done

    async def get_chats_by_owner(
        self,
        owner: str,
        page: int = 1,
        page_size: int = 20,
        search_query: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """Get paginated chat list for a specific owner, optionally filtered by search query."""
        try:
            offset = (page - 1) * page_size
            
            # Base query
            base_query = Chat.select().where(Chat.owner == owner)
            
            # Apply search filter if provided (searching title and description)
            if search_query:
                search_term = f'%{search_query}%' # Prepare for LIKE query
                base_query = base_query.where(
                    (Chat.title ** search_term) | (Chat.description ** search_term)
                )
                # Note: Using ** for case-insensitive LIKE
                # You might need different syntax depending on Peewee version or DB adapter
                # Alternatively, use fn.LOWER(Chat.title).contains(search_query.lower())

            # Get total count based on the potentially filtered query
            total_count = base_query.count()
            
            # Apply grouping, ordering, and pagination to the base query
            chats_query = (base_query
                    .select_extend(fn.COUNT(Message.id).alias('message_count')) # Use select_extend
                    .join(Message, JOIN.LEFT_OUTER, on=(Chat.id == Message.chat))
                    .group_by(Chat.id)
                    .order_by(Chat.updated_at.desc())
                    .limit(page_size)
                    .offset(offset))
            
            chat_list = [
                {
                    "id": str(chat.id),
                    "title": chat.title,
                    "description": chat.description,
                    "status": chat.status,
                    "message_count": getattr(chat, 'message_count', 0), # Safely access alias
                    "created_at": chat.created_at.isoformat(),
                    "updated_at": chat.updated_at.isoformat()
                }
                for chat in chats_query
            ]
            
            return chat_list, total_count
            
        except Exception as e:
            logger.error(f"Error getting chats for owner {owner} (search: {search_query}): {str(e)}")
            raise

    async def get_chat_messages(self, chat_id: str, page: int = 1, page_size: int = 20) -> Tuple[List[Dict], int]:
        """Get paginated messages for a specific chat"""
        try:
            offset = (page - 1) * page_size
            total_count = Message.select().where(Message.chat_id == chat_id).count()
            
            messages = (Message
                      .select()
                      .where(Message.chat_id == chat_id)
                      .order_by(Message.created_at.desc()) # Fetching latest first for pagination
                      .limit(page_size)
                      .offset(offset))
            
            # Create a dictionary for quick agent lookup from self.agents
            agents_dict = {agent["id"]: agent for agent in self.agents}
            
            message_list = []
            for msg in reversed(messages): # Reverse here to get chronological order for the page
                agent_info = None
                agent_id_str = str(msg.agent_id) if msg.agent_id else None
                
                if agent_id_str and agent_id_str in agents_dict:
                    agent_info = agents_dict[agent_id_str]
                    
                message_data = {
                    "id": str(msg.id),
                    "content": msg.content,
                    "role": msg.role,
                    "type": msg.type,
                    "agent_id": agent_id_str,
                    "metadata": msg.metadata,
                    "created_at": msg.created_at.isoformat(),
                    # Add agent details if found
                    "agent_name": agent_info.get("name") if agent_info else None,
                    "agent_avatar": agent_info.get("avatar") if agent_info else None 
                }
                message_list.append(message_data)
            
            # Note: message_list is now in chronological order (oldest to newest for the page)
            return message_list, total_count
            
        except Exception as e:
            logger.error(f"Error getting messages for chat {chat_id}: {str(e)}")
            raise 