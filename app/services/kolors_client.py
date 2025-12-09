import asyncio
import httpx
from typing import Optional
from loguru import logger

from app.config import KOLORS_API_URL, KOLORS_API_KEY


class KolorsClient:
    """Client for Kolors (Kling Image) API with polling support."""

    def __init__(self):
        self.api_url = KOLORS_API_URL
        self.api_key = KOLORS_API_KEY

    async def _poll_result(self, request_id, timeout: int = 120) -> Optional[str]:
        """Poll Kolors API until the image is ready."""
        status_url = f"https://api.gen-api.ru/api/v1/tasks/{request_id}"
        logger.info(f"🔄 Polling task result: {status_url}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            for attempt in range(timeout):
                await asyncio.sleep(2)

                try:
                    resp = await client.get(status_url, headers=headers)
                    logger.debug(f"⬅️ Kolors poll response {resp.status_code}: {resp.text}")

                    if resp.status_code != 200:
                        continue

                    data = resp.json()

                    if data.get("status") == "success" or data.get("status") == "completed":
                        # Try multiple possible response structures
                        output = data.get("output") or data.get("data") or data.get("result") or {}
                        
                        # Extract URL from various possible structures
                        url = None
                        if isinstance(output, dict):
                            url = output.get("url") or output.get("image_url")
                        elif isinstance(output, list) and len(output) > 0:
                            url = output[0].get("url") or output[0].get("image_url")
                        
                        if not url:
                            url = data.get("url") or data.get("image_url")
                        
                        if url:
                            logger.info(f"✅ Image URL ready: {url}")
                            return url
                        logger.warning(f"Status is success but no URL found. Response: {data}")

                    if data.get("status") == "error":
                        logger.error(f"❌ Kolors error during polling: {data}")
                        return None

                except Exception as e:
                    logger.error(f"Polling error: {e}")
                    continue

        logger.error("❌ Polling timeout — Kolors did not return an image in time")
        return None

    async def generate_image(self, prompt: str, photo_url: str, aspect_ratio: str) -> Optional[str]:
        """Send generation request to Kolors API and poll for the result."""

        # Kolors API может принимать image как строку URL или как объект
        # Попробуем сначала как строку (более простой вариант)
        payload = {
            "callback_url": None,
            "translate_input": True,
            "prompt": prompt,
            "negative_prompt": (
                "ugly, distorted face, deformed body, extra limbs, bad anatomy, "
                "low quality, plastic skin, cartoonish, AI-looking, weird eyes"
            ),
            "image": photo_url,  # Просто URL строка
            "model": "kling-v1",
            "image_fidelity": 1,
            "aspect_ratio": aspect_ratio,
            "n": 1
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # FULL LOGGING BEFORE REQUEST
        logger.warning("🚀 SENDING REQUEST TO KOLORS")
        logger.warning(f"➡️ API URL: {self.api_url}")
        logger.warning(f"➡️ HEADERS: {headers}")
        logger.warning(f"➡️ PAYLOAD: {payload}")
        logger.warning(f"➡️ PHOTO_URL: {photo_url}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(self.api_url, json=payload, headers=headers)

                logger.warning(f"⬅️ RAW RESPONSE STATUS: {resp.status_code}")
                logger.warning(f"⬅️ RAW RESPONSE BODY: {resp.text}")

                if resp.status_code != 200:
                    logger.error(f"❌ Kolors request failed: {resp.text}")
                    return None

                data = resp.json()
                
                # Try different possible response formats
                request_id = (
                    data.get("request_id") or 
                    data.get("id") or 
                    data.get("task_id") or
                    (data.get("data", {}).get("request_id") if isinstance(data.get("data"), dict) else None) or
                    (data.get("result", {}).get("request_id") if isinstance(data.get("result"), dict) else None)
                )

                if not request_id:
                    logger.error(f"❌ Kolors did not return request_id. Response: {data}")
                    # Try to extract direct URL if available
                    direct_url = None
                    if isinstance(data.get("output"), dict):
                        direct_url = data.get("output", {}).get("url")
                    elif isinstance(data.get("data"), dict):
                        direct_url = data.get("data", {}).get("url")
                    else:
                        direct_url = data.get("url") or data.get("image_url")
                    
                    if direct_url:
                        logger.info(f"✅ Got direct URL from Kolors: {direct_url}")
                        return direct_url
                    return None

                logger.info(f"📨 Received request_id from Kolors: {request_id}")
                logger.info("⏳ Starting polling...")

                return await self._poll_result(request_id)

            except Exception as e:
                logger.error(f"❌ Exception during POST to Kolors: {e}")
                return None

    async def generate_wish_image(self, wish_text: str, photo_url: str, width: int, height: int) -> Optional[str]:
        """Generate 1:1 image for the wish (regardless of final map format)."""

        prompt = (
            f"Generate a photorealistic scene featuring the person from the reference image. "
            f"Preserve their exact facial features, age, gender, and ethnicity. "
            f"The person should appear naturally integrated into the environment. "
            f"Scene theme: {wish_text}. "
            f"Style: cinematic, natural lighting, high realism."
        )

        # ALWAYS 1:1 FOR INDIVIDUAL WISH IMAGES
        aspect_ratio = "1:1"

        logger.info(f"🧠 Generating wish image with AR={aspect_ratio}, wish='{wish_text}'")

        return await self.generate_image(prompt, photo_url, aspect_ratio)


# Singleton instance
_client: Optional[KolorsClient] = None


def get_client() -> KolorsClient:
    global _client
    if _client is None:
        _client = KolorsClient()
    return _client

