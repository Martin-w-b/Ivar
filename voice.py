import io
import re
import wave
import logging
import threading
import queue

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
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=SAMPLE_RATE,
                language_code=TTS_LANGUAGE,
            ),
            interim_results=False,
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

    def listen(self) -> str:
        """Record audio with streaming STT — transcribes while recording.

        Streams audio chunks to Google as the user speaks and returns the
        final transcript once silence is detected.
        """
        chunk_duration = 0.1  # 100ms chunks
        chunk_samples = int(SAMPLE_RATE * chunk_duration)
        silence_chunks = int(SILENCE_DURATION / chunk_duration)

        audio_queue = queue.Queue()
        stop_event = threading.Event()

        def request_generator():
            """Yield StreamingRecognizeRequests from the audio queue."""
            while not stop_event.is_set():
                try:
                    data = audio_queue.get(timeout=0.2)
                except queue.Empty:
                    continue
                if data is None:
                    break
                yield speech.StreamingRecognizeRequest(audio_content=data)

        # Start streaming recognition in a background thread
        transcript_result = [None]

        def run_recognition():
            try:
                responses = self.stt_client.streaming_recognize(
                    config=self.streaming_config,
                    requests=request_generator(),
                )
                for response in responses:
                    for result in response.results:
                        if result.is_final:
                            transcript_result[0] = result.alternatives[0].transcript.strip()
            except Exception as e:
                logger.error("Streaming STT error: %s", e)

        recognition_thread = threading.Thread(target=run_recognition, daemon=True)
        recognition_thread.start()

        # Record audio, feeding chunks to STT in real time
        silent_count = 0
        recording = False

        logger.info("Listening...")

        try:
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                                dtype="int16", blocksize=chunk_samples) as stream:
                while True:
                    data, _ = stream.read(chunk_samples)
                    audio_chunk = data[:, 0]  # mono
                    rms = np.sqrt(np.mean(audio_chunk.astype(np.float32) ** 2))

                    if rms > SILENCE_THRESHOLD:
                        recording = True
                        silent_count = 0
                        audio_queue.put(audio_chunk.tobytes())
                    elif recording:
                        audio_queue.put(audio_chunk.tobytes())
                        silent_count += 1
                        if silent_count >= silence_chunks:
                            break
        except KeyboardInterrupt:
            raise
        finally:
            # Signal the generator to stop and wait for recognition
            audio_queue.put(None)
            stop_event.set()
            recognition_thread.join(timeout=5)

        if not recording:
            return ""

        text = transcript_result[0] or ""
        if text:
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
        text = re.sub(r'\s*[—–-]{1,3}\s*', '. ', text)  # dashes to pause
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

    def speak(self, text: str):
        """Speak the given text through the speaker."""
        self.text_to_speech(text)
