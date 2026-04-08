import httpx
import logging
from typing import Optional
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class TikTokService:
    """Service for interacting with TikTok Content Posting API"""

    def __init__(self):
        self.base_url = settings.tiktok_api_base_url
        self.client_key = settings.tiktok_client_key

    async def init_video_upload(
        self,
        access_token: str,
        open_id: str,
        video_size: int,
        description: str = ""
    ) -> dict:
        """
        Initialize video upload with TikTok API.
        Returns upload_id and upload_url for chunked upload.
        """
        url = f"{self.base_url}/v2/post/publish/inbox/video/init/"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "open_id": open_id,
            "source_info": {
                "source": "FILE_UPLOAD",
                "file_name": "video.mp4"
            },
            "post_info": {
                "title": description
            },
            "media_type": 2  # Video type
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                response.raise_for_status()
                data = response.json()

                if data.get("data"):
                    return {
                        "upload_id": data["data"].get("upload_id"),
                        "upload_url": data["data"].get("upload_url")
                    }
                else:
                    raise Exception(f"TikTok API error: {data.get('error', 'Unknown error')}")
        except httpx.HTTPError as e:
            logger.error(f"TikTok init upload error: {str(e)}")
            raise

    async def upload_video_chunk(
        self,
        upload_url: str,
        video_data: bytes,
        chunk_index: int = 0
    ) -> bool:
        """
        Upload video chunk to TikTok's upload URL.
        """
        headers = {
            "Content-Type": "video/mp4"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    upload_url,
                    content=video_data,
                    headers=headers,
                    timeout=120.0
                )
                response.raise_for_status()
                return True
        except httpx.HTTPError as e:
            logger.error(f"TikTok upload chunk error: {str(e)}")
            raise

    async def fetch_upload_status(
        self,
        access_token: str,
        open_id: str,
        upload_id: str
    ) -> dict:
        """
        Check the status of a video upload.
        """
        url = f"{self.base_url}/v2/post/publish/status/fetch/"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "open_id": open_id,
            "upload_id": upload_id
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                response.raise_for_status()
                data = response.json()

                if data.get("data"):
                    return {
                        "status": data["data"].get("status"),  # 0=processing, 1=success, 2=fail
                        "video_id": data["data"].get("video_id"),
                        "create_time": data["data"].get("create_time")
                    }
                else:
                    raise Exception(f"TikTok API error: {data.get('error', 'Unknown error')}")
        except httpx.HTTPError as e:
            logger.error(f"TikTok fetch status error: {str(e)}")
            raise

    async def publish_video(
        self,
        access_token: str,
        open_id: str,
        upload_id: str,
        description: str = ""
    ) -> Optional[str]:
        """
        Publish a video after upload is complete.
        Returns video_id on success.
        """
        url = f"{self.base_url}/v2/post/publish/action/publish/"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "open_id": open_id,
            "media_id": upload_id,
            "post_info": {
                "title": description,
                "privacy_level": "PUBLIC_TO_EVERYONE"
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                response.raise_for_status()
                data = response.json()

                if data.get("data"):
                    return data["data"].get("video_id")
                else:
                    raise Exception(f"TikTok API error: {data.get('error', 'Unknown error')}")
        except httpx.HTTPError as e:
            logger.error(f"TikTok publish error: {str(e)}")
            raise
