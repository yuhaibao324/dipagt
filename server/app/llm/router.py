from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from loguru import logger

from app.llm import LLM

router = APIRouter(tags=["llm"], prefix="/llm")

# Define request and response models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    vendor: Dict[str, Any] = Field(..., description="Vendor configuration with name and base_url")
    llm_args: Dict[str, Any] = Field(..., description="Model arguments including model name and parameters")
    messages: List[Message] = Field(..., description="List of messages for the chat")

class ChatResponse(BaseModel):
    content: str
    model: str
    usage: Dict[str, int]

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a chat request to the specified LLM.
    """
    logger.info(f"Received chat request for vendor: {request.vendor.get('name')}")
    
    try:
        # Create model configuration
        llm_config = {
            "vendor": request.vendor,
            "llm_args": request.llm_args
        }
        
        # Create LLM instance
        llm = LLM(llm_config)
        
        # Convert messages to the format expected by the LLM
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Send chat request
        response = await llm.aChat(messages)
        
        return response
    except Exception as e:
        logger.error(f"Error in chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 