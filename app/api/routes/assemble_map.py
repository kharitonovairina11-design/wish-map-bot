"""Assemble map route handler."""
import traceback
import base64
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from app.services.kolors_client import get_client
from app.services.map_assembler import get_assembler
from app.utils.formats import get_format_dimensions
from app.config import TMP_DIR
from app.utils.images import create_placeholder

router = APIRouter()


class AssembleMapRequest(BaseModel):
    wishes: List[str]
    format: str  # "phone", "pc", "a4"
    selfie_url: str  # URL to selfie image


class AssembleMapResponse(BaseModel):
    status: str
    generated_image_urls: List[str]
    final_map_url: str
    map_b64: str


@router.post("/assemble_map", response_model=AssembleMapResponse)
async def assemble_map_endpoint(payload: AssembleMapRequest):
    try:
        # Validate format
        try:
            width, height = get_format_dimensions(payload.format)
        except ValueError as format_err:
            logger.error(f"Invalid format: {payload.format}")
            raise HTTPException(status_code=400, detail=str(format_err))

        # Validate wishes
        if len(payload.wishes) < 3 or len(payload.wishes) > 9:
            raise HTTPException(
                status_code=400,
                detail=f"Must have 3-9 wishes, got {len(payload.wishes)}"
            )

        # Validate selfie URL
        if not payload.selfie_url.startswith("http"):
            raise HTTPException(400, "Invalid selfie URL")

        logger.info("📌 Starting assemble_map")
        logger.info(f"➡ Wishes: {payload.wishes}")
        logger.info(f"➡ Selfie URL: {payload.selfie_url}")
        logger.info(f"➡ Format: {payload.format} = {width}x{height}")

        kolors_client = get_client()
        assembler = get_assembler()

        generated_urls = []

        # Generate each wish image
        for idx, wish in enumerate(payload.wishes):
            logger.info(f"🖼 Generating image {idx+1}/{len(payload.wishes)}: {wish}")

            try:
                image_url = await kolors_client.generate_wish_image(
                    wish_text=wish,
                    photo_url=payload.selfie_url,   # ✔ FIXED
                    width=width,
                    height=height
                )

                if image_url:
                    logger.info(f"✔ Image generated: {image_url}")
                    generated_urls.append(image_url)
                else:
                    logger.warning(f"❌ Kolors failed, making placeholder...")
                    placeholder_path = TMP_DIR / f"placeholder-{uuid.uuid4().hex}.png"
                    create_placeholder(width, height, wish[:50], placeholder_path)
                    generated_urls.append(f"placeholder:{placeholder_path}")

            except Exception as e:
                logger.error(f"❌ Exception during generation: {e}")
                traceback.print_exc()
                placeholder_path = TMP_DIR / f"placeholder-{uuid.uuid4().hex}.png"
                create_placeholder(width, height, wish[:50], placeholder_path)
                generated_urls.append(f"placeholder:{placeholder_path}")

        # No images?
        if not generated_urls:
            fallback = TMP_DIR / f"fallback-{uuid.uuid4().hex}.png"
            create_placeholder(width, height, "Wish Map", fallback)
            generated_urls = [f"placeholder:{fallback}"]

        # Convert placeholder paths
        images_for_assembly = [
            url.replace("placeholder:", "") if url.startswith("placeholder:") else url
            for url in generated_urls
        ]

        # FINAL MAP
        map_path = TMP_DIR / f"final-map-{uuid.uuid4().hex}.png"

        await assembler.assemble(
            image_urls=images_for_assembly,
            labels=payload.wishes,
            output_path=map_path,
            width=width,
            height=height
        )

        map_b64 = base64.b64encode(map_path.read_bytes()).decode()

        return AssembleMapResponse(
            status="success",
            generated_image_urls=generated_urls,
            final_map_url=f"file://{map_path}",
            map_b64=map_b64
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"🔥 INTERNAL ERROR: {e}")
        traceback.print_exc()
        # Try to return a fallback response instead of raising 500
        try:
            fallback_path = TMP_DIR / f"error-fallback-{uuid.uuid4().hex}.png"
            create_placeholder(1024, 1024, "Ошибка генерации", fallback_path)
            map_b64 = base64.b64encode(fallback_path.read_bytes()).decode()
            return AssembleMapResponse(
                status="error",
                generated_image_urls=[],
                final_map_url=f"file://{fallback_path}",
                map_b64=map_b64
            )
        except:
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
