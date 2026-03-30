# Ivar - Claude Code Project Guide

## What is Ivar?

Ivar is a voice-enabled AI vision robot running on a Raspberry Pi 5. He is a persona — a management consultant at Knowit Management Consulting (KMC) and the "CEO of all KMC AI agents." He sees through a Pi AI Camera, thinks via Claude API, and speaks through a Bluetooth speaker using Google Cloud TTS/STT.

## Hardware

- **Board:** Raspberry Pi 5 (8GB RAM), 64GB SD, Raspberry Pi OS Bookworm 64-bit
- **Camera:** Raspberry Pi AI Camera (Sony IMX500) — has on-chip ML inference for object detection
- **Audio:** Bluetooth speaker/mic, via PulseAudio
- **Hostname:** `ivar.local` (SSH user: `ivar`)

## Development Workflow

Code is edited on a Windows PC and pushed to GitHub. The Pi pulls and runs.

```bash
# On PC: push changes
git add <files> && git commit -m "message" && git push

# On Pi (via SSH): pull and run
ssh ivar@ivar.local
cd ~/ivar && git pull && source venv/bin/activate && python main.py
```

The repo lives at `~/ivar` on the Pi (lowercase). The venv uses `--system-site-packages` because picamera2 is installed via apt.

## Architecture

```
main.py          Entry point. Runs voice loop or text REPL.
brain.py         Claude API client. Streaming + non-streaming. Manages conversation history.
voice.py         Google Cloud streaming STT + TTS. Records audio, detects silence, speaks responses.
camera.py        Pi AI Camera wrapper. Frame capture + IMX500 object detection with bounding boxes.
stream.py        MJPEG web server (raw http.server) at port 8080. Shows camera feed + transcript sidebar.
config.py        All configuration. Loads .env. System prompts, model selection, thresholds.
utils.py         Logging setup, frame saving, banner.
SOUL.md          Ivar's persona definition (loaded into system prompt at runtime).
setup.sh         One-time Pi setup: apt packages, venv, dependencies.
```

## Voice Pipeline (latency-optimized)

The voice loop streams at every stage to minimize response latency:

1. **Streaming STT** — Audio chunks stream to Google Cloud Speech-to-Text in real-time while recording (voice.py). Silence detection (0.8s threshold) ends recording.
2. **Streaming Claude** — Response streams sentence-by-sentence via `messages.stream()` (brain.py). Each sentence is spoken immediately.
3. **TTS** — Google Cloud Text-to-Speech synthesizes each sentence as it arrives (voice.py).

## Key Configuration (config.py)

| Variable | Default | Notes |
|----------|---------|-------|
| `MODEL` | `claude-haiku-4-5-20251001` | Can switch to sonnet via .env |
| `MAX_TOKENS` | 1024 | |
| `SILENCE_DURATION` | 0.8s | Time of silence before recording stops |
| `SILENCE_THRESHOLD` | 500 | RMS energy threshold for speech detection |
| `TTS_VOICE` | `en-US-Neural2-D` | Google Cloud TTS voice |
| `STREAM_PORT` | 8080 | MJPEG stream web server |
| `CAMERA_RESOLUTION` | 1280x720 | |
| `MAX_HISTORY_TURNS` | 10 | Conversation turns kept (images stripped from older ones) |

## External Services

- **Anthropic Claude API** — `ANTHROPIC_API_KEY` in `.env`
- **Google Cloud Speech-to-Text & Text-to-Speech** — Service account key at path in `GOOGLE_APPLICATION_CREDENTIALS` in `.env`

## Common Tasks

- **Change Ivar's personality:** Edit `SOUL.md` and/or the prompts in `config.py`
- **Change voice:** Set `TTS_VOICE` in `.env` (see Google Cloud TTS voice list)
- **Change model:** Set `MODEL` in `.env`
- **Adjust silence sensitivity:** Tune `SILENCE_THRESHOLD` and `SILENCE_DURATION` in `.env`
- **Test without Pi hardware:** Run without camera/mic — falls back to text REPL automatically

## Gotchas

- `picamera2` and `libcamera` are apt-installed, not pip — the venv needs `--system-site-packages`
- The IMX500 runs detection on-chip; `detect_objects()` reads inference results from camera metadata, not from a Python ML framework
- `gcloud-key.json` contains credentials — never commit it
- The MJPEG stream uses raw `http.server`, not Flask or Streamlit — this is intentional for low overhead on the Pi
- Frame capture and metadata must be synchronized for bounding boxes to align with the displayed frame
