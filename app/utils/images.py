"""Image utilities for downloading and processing."""
import base64
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx
from PIL import Image
from loguru import logger

from app.config import TMP_DIR


async def download_image(url: str, output_path: Optional[Path] = None) -> Optional[Path]:
    """
    Download image from URL and save to local file.
    
    Args:
        url: Image URL
        output_path: Optional path to save image. If None, generates temp path.
    
    Returns:
        Path to downloaded image, or None if failed
    """
    if output_path is None:
        ext = Path(urlparse(url).path).suffix or ".png"
        output_path = TMP_DIR / f"downloaded-{hash(url) % 100000}{ext}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            output_path.write_bytes(response.content)
            
            # Verify it's a valid image
            Image.open(output_path).verify()
            logger.info(f"Downloaded image: {url} -> {output_path}")
            return output_path
    except Exception as e:
        logger.error(f"Failed to download image from {url}: {e}")
        return None


def create_placeholder(width: int, height: int, text: str = "", output_path: Optional[Path] = None) -> Path:
    """
    Create a placeholder image with optional text.
    
    Args:
        width: Image width
        height: Image height
        text: Optional text to display
        output_path: Optional path to save. If None, generates temp path.
    
    Returns:
        Path to created placeholder
    """
    if output_path is None:
        output_path = TMP_DIR / f"placeholder-{hash(text) % 100000}.png"
    
    # Create gradient background
    img = Image.new("RGB", (width, height), (150, 150, 200))
    from PIL import ImageDraw, ImageFont
    
    draw = ImageDraw.Draw(img)
    
    # Add gradient effect
    for y in range(height):
        r = int(150 + (y / height) * 50)
        g = int(150 + (y / height) * 50)
        b = int(200 + (y / height) * 30)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Add text if provided
    if text:
        try:
            font_size = min(width // 15, height // 15, 48)
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # Center text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Draw with shadow
        draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0))
        draw.text((x, y), text, font=font, fill=(255, 255, 255))
    
    img.save(output_path, "PNG")
    logger.info(f"Created placeholder: {output_path}")
    return output_path


