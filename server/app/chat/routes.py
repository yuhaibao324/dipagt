from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
import json
import asyncio
from typing import Optional, Dict, Any, List, AsyncIterator
from pydantic import BaseModel
from app.chat.chat_manager import ChatManager
from app.llm.llm import LLM
from app.config import Config
import logging

router = APIRouter(prefix="/chat", tags=["chat"])

# Singleton instance of ChatManager
_chat_manager: Optional[ChatManager] = None

async def get_chat_manager() -> ChatManager:
    """Get or create the ChatManager singleton instance"""
    global _chat_manager
    if _chat_manager is None:
        # Initialize LLM with config
        openai_config = Config.get_vendor_config("openai")
        llm_config = {
            "vendor": openai_config,
            "llm_args": {
                "model": "gpt-4o",
                "temperature": 0,
                "max_tokens": 1000
            }
        }
        llm = LLM(llm_config)
        
        # Create and initialize ChatManager
        _chat_manager = ChatManager(llm)
        await _chat_manager.initialize()
    return _chat_manager

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    chat_id: Optional[str] = None
    owner: str  # Add owner field

class ChatResponse(BaseModel):
    """Chat response model"""
    chat_id: str
    user_message: Dict[str, Any]
    intention: Dict[str, Any]
    actions: list
    results: list

class PaginatedResponse(BaseModel):
    """Base paginated response model"""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int

# Helper to format data for SSE
async def sse_format(iterator: AsyncIterator[Dict[str, Any]]) -> AsyncIterator[str]:
    async for item in iterator:
        yield f"data: {json.dumps(item)}\n\n"

# Modify the existing POST endpoint or create a new one for streaming
# Let's modify the existing one. Remove response_model for streaming.
@router.post("/") 
async def process_message_stream_endpoint(
    request: ChatRequest,
    chat_manager: ChatManager = Depends(get_chat_manager)
) -> StreamingResponse:
    """
    Process a chat message via streaming Server-Sent Events.
    
    Args:
        request: The chat request containing the message, owner and optional chat_id.
        chat_manager: The ChatManager instance.
        
    Returns:
        A StreamingResponse sending SSE events.
    """
    try:
        # Get the async generator from the chat manager
        stream_generator = chat_manager.process_message_stream(
            message=request.message,
            chat_id=request.chat_id,
            owner=request.owner
        )
        
        # Format it for SSE and return the StreamingResponse
        return StreamingResponse(sse_format(stream_generator), media_type="text/event-stream")
        
    except Exception as e:
        # For streaming, handling the exception here is tricky.
        # Ideally, errors during the stream are yielded by the generator itself.
        # This top-level handler catches errors *before* the stream starts.
        logging.exception(f"Error starting message stream: {e}") 
        # We can't easily return a standard HTTPException with StreamingResponse.
        # Option 1: Return a simple text error (client needs to handle non-SSE response)
        # return StreamingResponse(content=f"Error starting stream: {e}", status_code=500, media_type="text/plain")
        # Option 2: Start a stream that immediately sends an error event and closes (better)
        async def error_stream():
            yield f"data: {json.dumps({'type': 'progress', 'data': {'step': 'fatal_error', 'error': f'Failed to start stream: {e}'}})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'data': {}})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream", status_code=500)

@router.get("/list/{owner}", response_model=PaginatedResponse)
async def get_chats(
    owner: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, alias="searchQuery"),
    chat_manager: ChatManager = Depends(get_chat_manager)
) -> Dict[str, Any]:
    """
    Get paginated chat list for a specific owner, optionally filtered by search query.
    
    Args:
        owner: The owner of the chats
        page: Page number (1-based)
        page_size: Number of items per page
        search: Optional search query to filter chats by title or description
        chat_manager: The ChatManager instance
        
    Returns:
        Paginated list of chats
    """
    try:
        chats, total = await chat_manager.get_chats_by_owner(
            owner=owner,
            page=page,
            page_size=page_size,
            search_query=search
        )
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "items": chats,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    except Exception as e:
        logger.error(f"Error in get_chats for owner {owner} (search: {search}): {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{chat_id}/messages", response_model=PaginatedResponse)
async def get_messages(
    chat_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    chat_manager: ChatManager = Depends(get_chat_manager)
) -> Dict[str, Any]:
    """
    Get paginated messages for a specific chat
    
    Args:
        chat_id: The ID of the chat
        page: Page number (1-based)
        page_size: Number of items per page
        chat_manager: The ChatManager instance
        
    Returns:
        Paginated list of messages
    """
    try:
        messages, total = await chat_manager.get_chat_messages(
            chat_id=chat_id,
            page=page,
            page_size=page_size
        )
        
        return {
            "items": messages,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 