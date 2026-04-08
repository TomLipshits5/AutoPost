import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import StatusResponse
from app.models import User, UploadJob, UploadStatus
from app.security import get_current_user

router = APIRouter(prefix="/api", tags=["status"])
logger = logging.getLogger(__name__)


@router.get("/status", response_model=StatusResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Try to query database
        db.query(UploadJob).count()
        return {
            "status": "healthy",
            "message": "API is running"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}"
        }


@router.get("/jobs-summary")
async def get_jobs_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary of upload jobs for current user"""
    total = db.query(UploadJob).filter(UploadJob.user_id == current_user.id).count()
    pending = db.query(UploadJob).filter(
        UploadJob.user_id == current_user.id,
        UploadJob.status == UploadStatus.PENDING
    ).count()
    processing = db.query(UploadJob).filter(
        UploadJob.user_id == current_user.id,
        UploadJob.status == UploadStatus.PROCESSING
    ).count()
    completed = db.query(UploadJob).filter(
        UploadJob.user_id == current_user.id,
        UploadJob.status == UploadStatus.COMPLETED
    ).count()
    failed = db.query(UploadJob).filter(
        UploadJob.user_id == current_user.id,
        UploadJob.status == UploadStatus.FAILED
    ).count()

    return {
        "total": total,
        "pending": pending,
        "processing": processing,
        "completed": completed,
        "failed": failed
    }
