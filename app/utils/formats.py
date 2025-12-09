"""
Output format definitions with dimensions.
"""
from typing import Dict, Tuple

FORMATS = {
    "phone": ("Phone Wallpaper", 1080, 1920),  # vertical
    "pc": ("Computer Wallpaper", 1920, 1080),  # horizontal
    "a4": ("Print A4", 2480, 3508),  # vertical, 300 dpi
}


def get_format_dimensions(format_key: str) -> Tuple[int, int]:
    """Get width, height for a format."""
    if format_key not in FORMATS:
        raise ValueError(f"Unknown format: {format_key}. Use: {list(FORMATS.keys())}")
    _, width, height = FORMATS[format_key]
    return width, height


def get_format_name(format_key: str) -> str:
    """Get display name for a format."""
    if format_key not in FORMATS:
        raise ValueError(f"Unknown format: {format_key}")
    return FORMATS[format_key][0]

