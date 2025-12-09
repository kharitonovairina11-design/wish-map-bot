"""Configuration for Wish Map Bot."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Kolors API Configuration
KOLORS_API_URL = os.getenv("KOLORS_API_URL", "https://api.gen-api.ru/api/v1/networks/kling-image")
KOLORS_API_KEY = os.getenv("KOLORS_API_KEY", "")

# Backend Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Storage Configuration
BASE_DIR = Path(__file__).resolve().parent
TMP_DIR = BASE_DIR / "tmp"
TMP_DIR.mkdir(exist_ok=True)

# Image Storage (for generated images)
IMAGES_DIR = BASE_DIR / "images"
IMAGES_DIR.mkdir(exist_ok=True)


