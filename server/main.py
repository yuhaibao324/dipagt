from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.health_check import router as health_router
from app.llm.router import router as llm_router
from app.chat.routes import router as chat_router
from app.utils.logger import get_logger
from app.db.database import db, init_db
# Import the data import functions
from app.db.data.import_data import import_agents, import_tools, import_agent_tools

logger = get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    logger.info("Server starting up...")
    
    # Connect database and initialize schema
    logger.info("Connecting to database...")
    if db.is_closed():
        db.connect()
    logger.info("Initializing database schema...")
    init_db() # Assumes init_db is synchronous
    logger.info("Database schema initialized.")

    # Import initial data (agents, tools, etc.)
    try:
        logger.info("Importing initial agents...")
        await import_agents()
        logger.info("Importing initial tools...")
        await import_tools()
        logger.info("Importing initial agent-tool associations...")
        await import_agent_tools()
        logger.info("Initial data imported successfully.")
    except Exception as e:
        logger.error(f"Error importing initial data: {e}", exc_info=True)
        # Depending on requirements, you might want to raise the error
        # or allow the server to start with a warning.
        # raise

    logger.info("Server startup complete.")
    yield
    
    # Shutdown code
    logger.info("Server shutting down...")
    if not db.is_closed():
        db.close()
        logger.info("Database connection closed.")
    logger.info("Server shutdown complete.")

app = FastAPI(
    title="DipDup Multi-Agent System",
    description="Backend API for the multi-agent collaboration platform.",
    version="0.1.0",
    lifespan=lifespan
)

# CORS Configuration
origins = [
    "http://localhost:3000", # Default Next.js dev origin
    # Add other origins as needed (e.g., your production frontend URL)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(llm_router)
app.include_router(chat_router)

if __name__ == "__main__":
    import uvicorn
    # Ensure logger is configured if running directly
    # (Uvicorn handles logging when run via CMD)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) # Add reload for local dev if needed