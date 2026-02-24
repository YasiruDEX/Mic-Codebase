"""
Deep Learning Vocal Filter using Silero VAD
============================================
Uses a pre-trained Silero VAD neural network to detect voice activity
from raw audio captured via the system microphone.

Provides a non-blocking interface that runs audio capture in a
background thread and exposes real-time voice probability.
"""

import threading
import time
import logging
import numpy as np

logger = logging.getLogger(__name__)

# Audio configuration for Silero VAD
SAMPLE_RATE = 16000       # Silero VAD requires 16kHz
CHUNK_SAMPLES = 512       # 512 samples = 32ms at 16kHz (Silero expects 512)
CHANNELS = 1              # Mono audio


class VocalFilter:
    """
    Deep learning-based vocal filter using Silero VAD.
    
    Captures audio from the default system microphone, runs it through
    Silero VAD, and provides real-time voice probability scores.
    """

    def __init__(self, threshold=0.5):
        """
        Args:
            threshold: Confidence threshold for voice detection (0.0 - 1.0).
                       Values above this are classified as voice.
        """
        self.threshold = threshold
        self._voice_probability = 0.0
        self._is_voice = False
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self._model = None
        self._audio_observers = []
        self._stream = None

        # Load the Silero VAD model
        self._load_model()

    def _load_model(self):
        """Load the Silero VAD model from torch hub."""
        import torch

        logger.info("📦 Loading Silero VAD model from torch hub...")
        start = time.time()

        self._model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False,
            trust_repo=True
        )
        self._model.eval()

        # Extract the helper functions
        (
            self._get_speech_timestamps,
            self._save_audio,
            self._read_audio,
            self._VADIterator,
            self._collect_chunks
        ) = utils

        elapsed = time.time() - start
        logger.info(f"✅ Silero VAD model loaded successfully in {elapsed:.2f}s")

    def add_audio_observer(self, callback):
        """Register a callback that receives raw audio chunks (np.ndarray float32)."""
        self._audio_observers.append(callback)

    def _audio_callback(self, indata, frames, time_info, status):
        """Called by sounddevice for each audio chunk."""
        import torch

        if status:
            logger.warning(f"⚠️  Audio stream status: {status}")

        try:
            # Convert to float32 mono tensor
            audio_chunk = indata[:, 0].copy()
            audio_tensor = torch.from_numpy(audio_chunk).float()

            # Run through Silero VAD
            confidence = self._model(audio_tensor, SAMPLE_RATE).item()

            with self._lock:
                self._voice_probability = confidence
                self._is_voice = confidence >= self.threshold

            # Forward raw audio to observers (e.g. AudioRecorder)
            for observer in self._audio_observers:
                try:
                    observer(audio_chunk)
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"❌ Error in audio callback: {e}")

    def start(self):
        """Start capturing audio and running vocal filter in background."""
        import sounddevice as sd

        if self._running:
            logger.warning("Vocal filter is already running.")
            return

        logger.info(f"🎤 Starting vocal filter (threshold={self.threshold})...")
        logger.info(f"   Sample rate: {SAMPLE_RATE}Hz | Chunk: {CHUNK_SAMPLES} samples")

        # List available audio devices
        try:
            devices = sd.query_devices()
            default_input = sd.query_devices(kind='input')
            logger.info(f"   Default input device: {default_input['name']}")
        except Exception as e:
            logger.warning(f"   Could not query audio devices: {e}")

        self._running = True

        # Start the audio stream
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            blocksize=CHUNK_SAMPLES,
            dtype='float32',
            callback=self._audio_callback
        )
        self._stream.start()
        logger.info("🟢 Vocal filter is now active and processing audio.")

    def stop(self):
        """Stop the vocal filter."""
        if not self._running:
            return

        logger.info("🔴 Stopping vocal filter...")
        self._running = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        logger.info("Vocal filter stopped.")

    @property
    def voice_probability(self):
        """Get the current voice probability (0.0 - 1.0)."""
        with self._lock:
            return self._voice_probability

    @property
    def is_voice(self):
        """Get whether voice is currently detected (based on threshold)."""
        with self._lock:
            return self._is_voice

    def get_status(self):
        """Get a dict with the current filter status."""
        with self._lock:
            return {
                'voice_probability': round(self._voice_probability, 4),
                'is_voice_dl': self._is_voice,
                'threshold': self.threshold,
                'running': self._running
            }

    def __del__(self):
        self.stop()
