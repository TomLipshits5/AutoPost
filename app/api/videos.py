import logging
import os
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import UploadJobResponse, UploadJobCreate, UploadJobListResponse
from app.models import User, UploadJob, UploadStatus, TikTokCredential
from app.security import get_current_user
from app.config import get_settings

router = APIRouter(prefix="/api/videos", tags=["videos"])
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("/upload", response_model=UploadJobResponse)
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    tiktok_credential_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a video file for posting to TikTok.
    Stores the video locally and creates an upload job.
    """
    # Verify credential belongs to user
    credential = db.query(TikTokCredential).filter(
        TikTokCredential.id == tiktok_credential_id,
        TikTokCredential.user_id == current_user.id
    ).first()

    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="TikTok credential not found"
        )

    # Create uploads directory if it doesn't exist
    os.makedirs(settings.upload_dir, exist_ok=True)

    # Save uploaded file
    file_path = os.path.join(
        settings.upload_dir,
        f"user_{current_user.id}_{file.filename}"
    )

    try:
        # Read and save file
        content = await file.read()
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        file_size = len(content)

        # Create upload job
        job = UploadJob(
            user_id=current_user.id,
            tiktok_credential_id=tiktok_credential_id,
            title=title,
            description=description,
            video_path=file_path,
            file_size=file_size,
            status=UploadStatus.PENDING
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        logger.info(f"Upload job created: {job.id} for user {current_user.email}")

        return {
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "status": job.status,
            "tiktok_video_id": job.tiktok_video_id,
            "error_message": job.error_message,
            "retry_count": job.retry_count,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "completed_at": job.completed_at
        }

    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        # Clean up file if something went wrong
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload video: {str(e)}"
        )


@router.get("/{job_id}", response_model=UploadJobResponse)
async def get_upload_status(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get status of an upload job"""
    job = db.query(UploadJob).filter(
        UploadJob.id == job_id,
        UploadJob.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload job not found"
        )

    return {
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "status": job.status,
        "tiktok_video_id": job.tiktok_video_id,
        "error_message": job.error_message,
        "retry_count": job.retry_count,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "completed_at": job.completed_at
    }


@router.get("", response_model=list[UploadJobListResponse])
async def list_uploads(
    status: UploadStatus = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all upload jobs for current user.
    Optional status filter.
    """
    query = db.query(UploadJob).filter(
        UploadJob.user_id == current_user.id
    )

    if status:
        query = query.filter(UploadJob.status == status)

    jobs = query.order_by(UploadJob.created_at.desc()).offset(offset).limit(limit).all()

    return [
        {
            "id": job.id,
            "title": job.title,
            "status": job.status,
            "created_at": job.created_at,
            "updated_at": job.updated_at
        }
        for job in jobs
    ]
