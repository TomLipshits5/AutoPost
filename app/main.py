import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
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
STATIC_DIR = Path(__file__).resolve().parent / "static"


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


_TAGS_METADATA = [
    {
        "name": "auth",
        "description": "User registration, login, API key management, and TikTok credential storage.",
    },
    {
        "name": "videos",
        "description": "Upload video files and track their posting status on TikTok.",
    },
    {
        "name": "status",
        "description": "Health check and job summary endpoints.",
    },
]

# Create FastAPI app
app = FastAPI(
    title="AutoPost API",
    description=(
        "Automatically upload videos to TikTok and other social media platforms.\n\n"
        "## Authentication\n"
        "All video and credential endpoints require an `X-API-Key` header.\n"
        "Obtain your key by calling **POST /api/auth/register** or **POST /api/auth/login**.\n\n"
        "Click **Authorize** (the lock icon) and enter your key to authenticate in this UI."
    ),
    version="1.0.0",
    openapi_tags=_TAGS_METADATA,
    contact={"name": "AutoPost", "url": "https://github.com"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
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

# Serve the frontend app from /app
app.mount("/app", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")


@app.get("/")
async def root():
    """Redirect to the frontend app"""
    return RedirectResponse(url="/app")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        tags=_TAGS_METADATA,
        routes=app.routes,
    )

    # Register API key security scheme
    schema.setdefault("components", {}).setdefault("securitySchemes", {})["ApiKeyAuth"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
    }

    # Apply security globally so every endpoint shows the lock icon
    schema["security"] = [{"ApiKeyAuth": []}]

    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
