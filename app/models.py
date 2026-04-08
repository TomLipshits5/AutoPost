from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class UploadStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    api_key = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tiktok_credentials = relationship("TikTokCredential", back_populates="user", cascade="all, delete-orphan")
    upload_jobs = relationship("UploadJob", back_populates="user", cascade="all, delete-orphan")


class TikTokCredential(Base):
    __tablename__ = "tiktok_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    access_token = Column(String)
    open_id = Column(String, index=True)
    refresh_token = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="tiktok_credentials")


class UploadJob(Base):
    __tablename__ = "upload_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    tiktok_credential_id = Column(Integer, ForeignKey("tiktok_credentials.id"))
    title = Column(String)
    description = Column(Text, nullable=True)
    video_path = Column(String)
    file_size = Column(Integer)
    status = Column(Enum(UploadStatus), default=UploadStatus.PENDING, index=True)
    tiktok_video_id = Column(String, nullable=True, index=True)
    tiktok_upload_id = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="upload_jobs")
    logs = relationship("UploadLog", back_populates="job", cascade="all, delete-orphan")


class UploadLog(Base):
    __tablename__ = "upload_logs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("upload_jobs.id"), index=True)
    status = Column(Enum(UploadStatus))
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("UploadJob", back_populates="logs")
