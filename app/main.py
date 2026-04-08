import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.tasks.scheduler import start_scheduler, stop_scheduler
from app.api import auth, videos, status
from app.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("Starting up...")
    init_db()
    start_scheduler()
    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down...")
    stop_scheduler()
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="AutoPost API",
    description="Auto-upload videos to TikTok and other social media",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(videos.router)
app.include_router(status.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AutoPost API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
