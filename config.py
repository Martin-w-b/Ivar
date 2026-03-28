import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

MODEL = os.getenv("MODEL", "claude-haiku-4-5-20251001")

MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1024"))

CAMERA_RESOLUTION = (1280, 720)

JPEG_QUALITY = 85

CAPTURE_DIR = "captures"

MAX_HISTORY_TURNS = 10

SYSTEM_PROMPT = (
    "You are Ivar, a robot with a camera. You can see through your camera "
    "and describe what you observe. Be concise, helpful, and conversational. "
    "When shown an image, describe what you see naturally, as if you are "
    "looking at the world through your own eyes."
)
