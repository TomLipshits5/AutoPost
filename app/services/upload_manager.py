import logging
import os
import aiofiles
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import UploadJob, UploadLog, UploadStatus, TikTokCredential
from app.services.tiktok_service import TikTokService
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class UploadManager:
    """Manages the entire video upload process"""

    def __init__(self):
        self.tiktok_service = TikTokService()

    async def process_upload(self, job: UploadJob, db: Session) -> None:
        """
        Process a single upload job.
        Updates job status and logs throughout the process.
        """
        try:
            # Get TikTok credentials
            credential = db.query(TikTokCredential).filter(
                TikTokCredential.id == job.tiktok_credential_id
            ).first()

            if not credential or not credential.is_active:
                raise Exception("TikTok credential not found or inactive")

            # Update job status to processing
            job.status = UploadStatus.PROCESSING
            job.updated_at = datetime.utcnow()
            db.commit()

            await self._log_upload(db, job, UploadStatus.PROCESSING, "Starting video upload")

            # Step 1: Initialize upload
            logger.info(f"Initializing upload for job {job.id}")
            init_result = await self.tiktok_service.init_video_upload(
                access_token=credential.access_token,
                open_id=credential.open_id,
                video_size=job.file_size,
                description=job.description or ""
            )

            upload_id = init_result.get("upload_id")
            upload_url = init_result.get("upload_url")

            if not upload_id or not upload_url:
                raise Exception("Failed to get upload URL from TikTok")

            job.tiktok_upload_id = upload_id
            db.commit()

            # Step 2: Read and upload video file
            logger.info(f"Uploading video file for job {job.id}")
            await self._log_upload(db, job, UploadStatus.PROCESSING, "Uploading video file")

            async with aiofiles.open(job.video_path, "rb") as f:
                video_data = await f.read()

            await self.tiktok_service.upload_video_chunk(
                upload_url=upload_url,
                video_data=video_data,
                chunk_index=0
            )

            await self._log_upload(db, job, UploadStatus.PROCESSING, "Video file uploaded")

            # Step 3: Check upload status
            logger.info(f"Checking upload status for job {job.id}")
            status_result = await self.tiktok_service.fetch_upload_status(
                access_token=credential.access_token,
                open_id=credential.open_id,
                upload_id=upload_id
            )

            status_code = status_result.get("status")  # 0=processing, 1=success, 2=fail

            if status_code == 2:
                raise Exception("TikTok rejected the video upload")
            elif status_code == 0:
                # Still processing, will check again later
                await self._log_upload(db, job, UploadStatus.PROCESSING, "TikTok processing video")
                job.updated_at = datetime.utcnow()
                db.commit()
                return

            # Step 4: Publish video
            logger.info(f"Publishing video for job {job.id}")
            video_id = await self.tiktok_service.publish_video(
                access_token=credential.access_token,
                open_id=credential.open_id,
                upload_id=upload_id,
                description=job.description or ""
            )

            if video_id:
                job.tiktok_video_id = video_id
                job.status = UploadStatus.COMPLETED
                job.completed_at = datetime.utcnow()
                job.updated_at = datetime.utcnow()
                db.commit()

                await self._log_upload(
                    db, job, UploadStatus.COMPLETED,
                    f"Video published successfully. TikTok Video ID: {video_id}"
                )

                # Clean up video file
                await self._cleanup_video(job.video_path)

                logger.info(f"Upload completed for job {job.id}")
            else:
                raise Exception("Failed to get video ID after publishing")

        except Exception as e:
            logger.error(f"Upload failed for job {job.id}: {str(e)}")
            job.retry_count += 1

            if job.retry_count >= settings.max_retries:
                job.status = UploadStatus.FAILED
                job.error_message = str(e)
                job.updated_at = datetime.utcnow()
                db.commit()

                await self._log_upload(
                    db, job, UploadStatus.FAILED,
                    f"Upload failed after {job.retry_count} retries: {str(e)}"
                )

                # Clean up video file on final failure
                await self._cleanup_video(job.video_path)
            else:
                job.updated_at = datetime.utcnow()
                db.commit()

                await self._log_upload(
                    db, job, UploadStatus.PENDING,
                    f"Retry {job.retry_count}/{settings.max_retries}: {str(e)}"
                )

    async def _log_upload(
        self,
        db: Session,
        job: UploadJob,
        status: UploadStatus,
        message: str
    ) -> None:
        """Create a log entry for an upload"""
        log = UploadLog(
            job_id=job.id,
            status=status,
            message=message
        )
        db.add(log)
        db.commit()

    async def _cleanup_video(self, video_path: str) -> None:
        """Remove video file after successful upload"""
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                logger.info(f"Cleaned up video file: {video_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup video file {video_path}: {str(e)}")
