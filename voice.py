import io
import re
import wave
import logging

import numpy as np
import sounddevice as sd
from google.cloud import speech, texttospeech

from config import (
    SILENCE_THRESHOLD, SILENCE_DURATION, SAMPLE_RATE,
    TTS_VOICE, TTS_LANGUAGE,
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
        self.stt_client = speech.SpeechClient()
        self.tts_client = texttospeech.TextToSpeechClient()
        self.stt_config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE,
            language_code=TTS_LANGUAGE,
        )
        self.voice_params = texttospeech.VoiceSelectionParams(
            language_code=TTS_LANGUAGE,
            name=TTS_VOICE,
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=24000,
        )
        logger.info("Voice initialized (Google Cloud, voice: %s)", TTS_VOICE)

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
        """Send audio to Google Cloud Speech-to-Text and return transcribed text."""
        if not audio_bytes:
            return ""

        # Extract raw PCM from WAV
        buf = io.BytesIO(audio_bytes)
        with wave.open(buf, "rb") as wf:
            raw_audio = wf.readframes(wf.getnframes())

        audio = speech.RecognitionAudio(content=raw_audio)
        response = self.stt_client.recognize(config=self.stt_config, audio=audio)

        if not response.results:
            return ""

        text = response.results[0].alternatives[0].transcript.strip()
        logger.info("STT result: %s", text)
        return text

    @staticmethod
    def _strip_markdown(text: str) -> str:
        """Remove markdown formatting so TTS reads clean text."""
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*(.+?)\*', r'\1', text)       # *italic*
        text = re.sub(r'__(.+?)__', r'\1', text)       # __bold__
        text = re.sub(r'_(.+?)_', r'\1', text)         # _italic_
        text = re.sub(r'`(.+?)`', r'\1', text)         # `code`
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)  # # headers
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)  # bullet points
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)  # numbered lists
        return text.strip()

    def text_to_speech(self, text: str):
        """Convert text to speech and play through the default audio output."""
        if not text:
            return

        text = self._strip_markdown(text)
        synthesis_input = texttospeech.SynthesisInput(text=text)
        response = self.tts_client.synthesize_speech(
            input=synthesis_input,
            voice=self.voice_params,
            audio_config=self.audio_config,
        )

        # Play the audio (LINEAR16 PCM at 24kHz)
        audio_data = np.frombuffer(response.audio_content, dtype=np.int16)
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
