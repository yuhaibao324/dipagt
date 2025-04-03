from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health_check")
async def health_check():
    """
    Health check endpoint that returns a success status and 'ok' message.
    """
    return {"success": True, "message": "ok"} 