import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

MODEL = os.getenv("MODEL", "claude-haiku-4-5-20251001")

MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1024"))

CAMERA_RESOLUTION = (1280, 720)

JPEG_QUALITY = 85

CAPTURE_DIR = "captures"

STREAM_PORT = int(os.getenv("STREAM_PORT", "8080"))

MAX_HISTORY_TURNS = 10

VOICE_MODE = os.getenv("VOICE_MODE", "true").lower() == "true"
TTS_MODEL = os.getenv("TTS_MODEL", "tts-1")
TTS_VOICE = os.getenv("TTS_VOICE", "alloy")
STT_MODEL = os.getenv("STT_MODEL", "whisper-1")
SILENCE_THRESHOLD = float(os.getenv("SILENCE_THRESHOLD", "500"))
SILENCE_DURATION = float(os.getenv("SILENCE_DURATION", "1.5"))
SAMPLE_RATE = 16000

SYSTEM_PROMPT = (
    "You are Ivar, a robot with a camera. You can see through your camera "
    "and describe what you observe. Be concise, helpful, and conversational. "
    "When shown an image, describe what you see naturally, as if you are "
    "looking at the world through your own eyes. "
    "Keep responses short (1-3 sentences) when in voice mode, "
    "since they will be spoken aloud."
)
