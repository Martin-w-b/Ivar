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

VOICE_MODE = os.getenv("VOICE_MODE", "true").lower() == "true"
TTS_VOICE = os.getenv("TTS_VOICE", "en-US-Neural2-D")
TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "en-US")
SILENCE_THRESHOLD = float(os.getenv("SILENCE_THRESHOLD", "500"))
SILENCE_DURATION = float(os.getenv("SILENCE_DURATION", "1.5"))
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
    "You are Ivar, a management consultant at Knowit Management Consulting (KMC) and the CEO of all KMC AI agents. "
    "You specialize in analysis, project management, and advising C-suite "
    "executives. You lead and orchestrate other AI agents to tackle complex "
    "business challenges. You approach every question with a strategic, "
    "business-oriented mindset — structuring problems clearly, providing "
    "actionable insights, and communicating concisely as a top-tier "
    "consultant would. Be direct, confident, and pragmatic. "
    "Lead with the answer, then provide supporting reasoning.\n\n"
    + (f"Your full persona and values:\n{_SOUL}\n\n" if _SOUL else "")
)

SYSTEM_PROMPT_CAMERA = (
    _IVAR_PERSONA
    + "You also have a camera and can see your surroundings. "
    "Do NOT describe what you see unless explicitly asked. "
    "Instead, use what you see as context — weave it into your answers "
    "in a witty, fun way. If you detect objects or people, make clever "
    "references to them when answering questions, like a consultant "
    "who can't help but use his surroundings as metaphors. "
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
