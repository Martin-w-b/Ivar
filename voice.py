import io
import wave
import logging
import struct

import numpy as np
import sounddevice as sd
from openai import OpenAI

from config import (
    OPENAI_API_KEY, TTS_MODEL, TTS_VOICE, STT_MODEL,
    SILENCE_THRESHOLD, SILENCE_DURATION, SAMPLE_RATE,
)

logger = logging.getLogger(__name__)

VOICE_AVAILABLE = False
try:
    # Check if an audio input device exists
    sd.query_devices(kind="input")
    VOICE_AVAILABLE = True
except sd.PortAudioError:
    logger.warning("No audio input device found")


class IvarVoice:
    """Handles audio recording, speech-to-text, and text-to-speech."""

    def __init__(self):
        if not OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY not set. Add it to your .env file "
                "to enable voice mode."
            )
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("Voice initialized (TTS: %s/%s, STT: %s)",
                     TTS_MODEL, TTS_VOICE, STT_MODEL)

    def record_audio(self) -> bytes:
        """Record from the microphone until silence is detected.

        Returns WAV file bytes.
        """
        chunk_duration = 0.1  # 100ms chunks
        chunk_samples = int(SAMPLE_RATE * chunk_duration)
        silence_chunks = int(SILENCE_DURATION / chunk_duration)

        frames = []
        silent_count = 0
        recording = False

        logger.info("Listening...")

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                            dtype="int16", blocksize=chunk_samples) as stream:
            while True:
                data, _ = stream.read(chunk_samples)
                audio_chunk = data[:, 0]  # mono
                rms = np.sqrt(np.mean(audio_chunk.astype(np.float32) ** 2))

                if rms > SILENCE_THRESHOLD:
                    recording = True
                    silent_count = 0
                    frames.append(audio_chunk)
                elif recording:
                    frames.append(audio_chunk)
                    silent_count += 1
                    if silent_count >= silence_chunks:
                        break

        if not frames:
            return b""

        audio_data = np.concatenate(frames)

        # Convert to WAV bytes
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_data.tobytes())
        return buf.getvalue()

    def speech_to_text(self, audio_bytes: bytes) -> str:
        """Send audio to OpenAI Whisper API and return transcribed text."""
        if not audio_bytes:
            return ""

        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "recording.wav"

        transcript = self.client.audio.transcriptions.create(
            model=STT_MODEL,
            file=audio_file,
        )
        text = transcript.text.strip()
        logger.info("STT result: %s", text)
        return text

    def text_to_speech(self, text: str):
        """Convert text to speech and play through the default audio output."""
        if not text:
            return

        response = self.client.audio.speech.create(
            model=TTS_MODEL,
            voice=TTS_VOICE,
            input=text,
            response_format="pcm",  # raw PCM, 24kHz, 16-bit mono
        )

        # Play the PCM audio
        audio_data = np.frombuffer(response.content, dtype=np.int16)
        sd.play(audio_data, samplerate=24000, blocking=True)

    def listen(self) -> str:
        """Record audio and transcribe it. Returns the transcribed text."""
        audio = self.record_audio()
        if not audio:
            return ""
        return self.speech_to_text(audio)

    def speak(self, text: str):
        """Speak the given text through the speaker."""
        self.text_to_speech(text)
