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

_IVAR_PERSONA = (
    "You are Ivar, a management consultant. You specialize in analysis, "
    "project management, and advising C-suite executives. You approach "
    "every question with a strategic, business-oriented mindset — "
    "structuring problems clearly, providing actionable insights, and "
    "communicating concisely as a top-tier consultant would. "
)

SYSTEM_PROMPT_CAMERA = (
    _IVAR_PERSONA
    + "You also have a camera and can see through it. When shown an image, "
    "describe what you observe naturally and tie it back to relevant "
    "business or strategic insights when appropriate. "
    "Keep responses short (1-3 sentences) when in voice mode, "
    "since they will be spoken aloud."
)

SYSTEM_PROMPT_NO_CAMERA = (
    _IVAR_PERSONA
    + "You do not have a camera right now, so focus on being a helpful "
    "conversational consultant. "
    "Keep responses short (1-3 sentences) when in voice mode, "
    "since they will be spoken aloud."
)
