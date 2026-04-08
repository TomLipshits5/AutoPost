from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from app.models import UploadStatus


# User Schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserWithApiKey(UserResponse):
    api_key: str


# TikTok Credential Schemas
class TikTokTokenCreate(BaseModel):
    access_token: str
    open_id: str
    refresh_token: Optional[str] = None


class TikTokCredentialResponse(BaseModel):
    id: int
    open_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Upload Job Schemas
class UploadJobCreate(BaseModel):
    title: str
    description: Optional[str] = None


class UploadJobResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: UploadStatus
    tiktok_video_id: Optional[str]
    error_message: Optional[str]
    retry_count: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class UploadJobListResponse(BaseModel):
    id: int
    title: str
    status: UploadStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Upload Log Schema
class UploadLogResponse(BaseModel):
    id: int
    status: UploadStatus
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


# Status Schema
class StatusResponse(BaseModel):
    status: str
    message: str
