from typing import Any

import httpx

from src.app.core.config import settings


class WhatsAppMediaService:
    @staticmethod
    def _media_metadata_endpoint(media_id: str) -> str:
        return f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{media_id}"

    @staticmethod
    def _headers() -> dict[str, str]:
        if not settings.WHATSAPP_ACCESS_TOKEN:
            raise ValueError("Missing WHATSAPP_ACCESS_TOKEN")
        return {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        }

    @classmethod
    async def get_media_url(cls, media_id: str) -> tuple[str, str | None]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                cls._media_metadata_endpoint(media_id),
                headers=cls._headers(),
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()

        media_url = payload.get("url")
        mime_type = payload.get("mime_type")
        if not media_url:
            raise ValueError("WhatsApp media URL missing in metadata response")
        return media_url, mime_type

    @classmethod
    async def download_media_bytes(cls, media_id: str) -> tuple[bytes, str | None]:
        media_url, mime_type = await cls.get_media_url(media_id)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(media_url, headers=cls._headers())
            response.raise_for_status()

        return response.content, mime_type
