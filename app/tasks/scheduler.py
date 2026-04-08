import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from app.models import UploadJob, UploadStatus
from app.services.upload_manager import UploadManager
from app.database import SessionLocal
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
upload_manager = UploadManager()


async def process_pending_uploads():
    """Background job that processes pending uploads"""
    db = SessionLocal()
    try:
        # Find jobs that are pending or processing and need retry
        jobs = db.query(UploadJob).filter(
            UploadJob.status.in_([UploadStatus.PENDING, UploadStatus.PROCESSING])
        ).all()

        logger.info(f"Processing {len(jobs)} pending/processing uploads")

        for job in jobs:
            try:
                await upload_manager.process_upload(job, db)
            except Exception as e:
                logger.error(f"Error processing job {job.id}: {str(e)}")
                db.rollback()

    except Exception as e:
        logger.error(f"Error in upload scheduler: {str(e)}")
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler"""
    try:
        # Add job to process uploads every X seconds
        scheduler.add_job(
            process_pending_uploads,
            trigger=IntervalTrigger(seconds=settings.upload_check_interval),
            id="process_uploads",
            name="Process Pending Uploads",
            replace_existing=True
        )

        if not scheduler.running:
            scheduler.start()
            logger.info(f"Scheduler started. Upload check interval: {settings.upload_check_interval}s")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")


def stop_scheduler():
    """Stop the background scheduler"""
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("Scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")
