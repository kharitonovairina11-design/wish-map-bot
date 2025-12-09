"""Map assembler for creating final wish map collage."""
from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont
from loguru import logger

from app.utils.images import download_image, create_placeholder
from app.utils.grid import choose_grid, place_cells


class MapAssembler:
    """Assembles generated images into a final wish map."""

    def __init__(self):
        self.title = "Wish Map 2026"
        self.margin = 40
        self.padding = 20
        self.title_height = 100

    def _get_title_font(self, width: int) -> ImageFont.FreeTypeFont:
        try:
            font_size = min(width // 18, 70)
            return ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
            except:
                return ImageFont.load_default()

    def _get_label_font(self, cell_size: int) -> ImageFont.FreeTypeFont:
        try:
            font_size = max(cell_size // 18, 16)
            return ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
            except:
                return ImageFont.load_default()

    async def assemble(
        self,
        image_urls: List[str],
        labels: List[str],
        output_path: Path,
        width: int,
        height: int
    ) -> Path:

        logger.info("🧩 Starting wish map assembly...")
        logger.info(f"➡️ Images: {len(image_urls)} | Labels: {labels}")
        logger.info(f"➡️ Target size: {width}x{height}")

        if not image_urls or not labels:
            raise ValueError("image_urls and labels must not be empty")

        count = len(image_urls)
        rows, cols = choose_grid(count)

        logger.info(f"📐 Grid configuration: {rows} rows x {cols} cols")

        available_width = width - 2 * self.margin
        available_height = height - 2 * self.margin - self.title_height

        cell_width = (available_width - (cols - 1) * self.padding) // cols
        cell_height = (available_height - (rows - 1) * self.padding) // rows

        logger.info(f"🧱 Cell size: {cell_width}x{cell_height}")

        canvas = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)

        # Title
        title_font = self._get_title_font(width)
        title_bbox = draw.textbbox((0, 0), self.title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_width) // 2
        title_y = self.margin // 2
        draw.text((title_x, title_y), self.title, fill=(30, 30, 30), font=title_font)

        # Layout placement
        boxes = place_cells(rows, cols, available_width, available_height, count)
        grid_start_x = self.margin
        grid_start_y = self.margin + self.title_height

        label_font = self._get_label_font(min(cell_width, cell_height))

        # Processing each image
        for idx, (image_url, label, box) in enumerate(zip(image_urls, labels, boxes)):
            logger.info(f"⬇️ Downloading image {idx+1}/{count}: {image_url}")

            image_path = await download_image(image_url)
            if image_path is None:
                logger.error(f"❌ Failed to download image {idx}, using placeholder")
                image_path = create_placeholder(cell_width, cell_height, label[:30])

            try:
                img = Image.open(image_path).convert("RGB")

                # KOLORS always returns 1:1 → but we may still enforce it:
                img_w, img_h = img.size
                ratio = img_w / img_h

                if abs(ratio - 1) > 0.01:
                    logger.warning("⚠️ Image is not 1:1 — forcing square crop")
                    min_side = min(img_w, img_h)
                    left = (img_w - min_side) // 2
                    top = (img_h - min_side) // 2
                    img = img.crop((left, top, left + min_side, top + min_side))

                img = img.resize((cell_width, cell_height), Image.Resampling.LANCZOS)

                cell_x0, cell_y0, _, _ = box
                paste_x = grid_start_x + cell_x0
                paste_y = grid_start_y + cell_y0

                canvas.paste(img, (paste_x, paste_y))

                # Label
                label_bbox = draw.textbbox((0, 0), label, font=label_font)
                label_width = label_bbox[2] - label_bbox[0]
                label_x = paste_x + (cell_width - label_width) // 2
                label_y = paste_y + cell_height - label_font.size - 10

                draw.text((label_x + 2, label_y + 2), label, fill="black", font=label_font)
                draw.text((label_x, label_y), label, fill="white", font=label_font)

            except Exception as e:
                logger.error(f"❌ Image processing failed ({idx}): {e}")
                try:
                    cell_x0, cell_y0, _, _ = box
                    paste_x = grid_start_x + cell_x0
                    paste_y = grid_start_y + cell_y0
                    placeholder_img = Image.open(create_placeholder(cell_width, cell_height, label[:30]))
                    canvas.paste(placeholder_img, (paste_x, paste_y))
                except Exception as placeholder_err:
                    logger.error(f"Failed to create placeholder: {placeholder_err}")

        # Save final map
        output_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output_path, "PNG")
        logger.info(f"🎉 Wish map successfully saved to {output_path}")

        return output_path


# Singleton instance
_assembler: Optional[MapAssembler] = None


def get_assembler() -> MapAssembler:
    global _assembler
    if _assembler is None:
        _assembler = MapAssembler()
    return _assembler
