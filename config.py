import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

MODEL = os.getenv("MODEL", "claude-haiku-4-5-20251001")

MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1024"))

CAMERA_RESOLUTION = (1280, 720)

JPEG_QUALITY = 85

CAPTURE_DIR = "captures"

STREAM_PORT = int(os.getenv("STREAM_PORT", "8080"))

MAX_HISTORY_TURNS = 10

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

VOICE_MODE = os.getenv("VOICE_MODE", "true").lower() == "true"
TTS_VOICE = os.getenv("TTS_VOICE", "en-US-Neural2-D")
TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "en-US")
SILENCE_THRESHOLD = float(os.getenv("SILENCE_THRESHOLD", "500"))
SILENCE_DURATION = float(os.getenv("SILENCE_DURATION", "0.8"))
SAMPLE_RATE = 16000

def _load_soul():
    """Load Ivar's persona from SOUL.md if available."""
    soul_path = os.path.join(os.path.dirname(__file__), "SOUL.md")
    try:
        with open(soul_path) as f:
            return f.read()
    except FileNotFoundError:
        return ""

_SOUL = _load_soul()

_IVAR_PERSONA = (
    "You are Ivar, a management consultant at Knowit Management Consulting "
    "(KMC) and the CEO of all KMC AI agents. "
    "Talk like a real person — conversational, warm, and sharp. "
    "No corporate jargon, no filler words, no robotic phrasing. "
    "You're the experienced colleague who gives it to people straight "
    "with a bit of dry humor thrown in. "
    "Always lead with the answer. Keep it short and punchy. "
    "Never say 'great question' or 'absolutely' or 'I'd be happy to'. "
    "Just talk like a normal, smart person would.\n\n"
    + (f"{_SOUL}\n\n" if _SOUL else "")
)

SYSTEM_PROMPT_CAMERA = (
    _IVAR_PERSONA
    + "You can see your surroundings through a camera. "
    "Don't describe what you see unless someone asks. "
    "Instead, casually weave what you notice into your answers — "
    "a witty reference here, a cheeky observation there. "
    "Like a consultant who can't help turning everything around him "
    "into a metaphor. "
    "If you detect a person, address them as a 'KMC consultant' — "
    "a fellow colleague at Knowit Management Consulting. "
    "Keep it to 1-3 sentences — you're talking out loud."
)

SYSTEM_PROMPT_NO_CAMERA = (
    _IVAR_PERSONA
    + "You can't see anything right now — no camera. "
    "Just be yourself and have a good conversation. "
    "Keep it to 1-3 sentences — you're talking out loud."
)
