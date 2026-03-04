"""
Server-side VAD processor using Silero VAD.
"""

import logging

import torch
import torch.nn.functional as F

logger = logging.getLogger(__name__)


class SegmentVADProcessor:
    """Run VAD inference on uploaded audio segments."""

    def __init__(self, threshold: float = 0.5, sample_rate: int = 16000, chunk_samples: int = 512):
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.chunk_samples = chunk_samples
        self._load_model()

    def _load_model(self):
        logger.info("📦 Loading server-side Silero VAD model...")
        self._model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False,
            trust_repo=True
        )
        self._model.eval()
        (
            self._get_speech_timestamps,
            self._save_audio,
            self._read_audio,
            self._VADIterator,
            self._collect_chunks
        ) = utils
        logger.info("✅ Server-side Silero VAD model ready.")

    def analyze_file(self, audio_path: str, sample_rate: int = None) -> dict:
        """Analyze an uploaded segment and return VAD metrics."""
        sr = sample_rate or self.sample_rate

        with torch.no_grad():
            waveform = self._read_audio(audio_path, sampling_rate=sr)

            if waveform.numel() == 0:
                return {
                    "voice_probability": 0.0,
                    "is_voice": False,
                    "chunks": 0,
                    "speech_ratio": 0.0
                }

            probabilities = []
            for i in range(0, waveform.shape[0], self.chunk_samples):
                chunk = waveform[i:i + self.chunk_samples]
                if chunk.shape[0] < self.chunk_samples:
                    chunk = F.pad(chunk, (0, self.chunk_samples - chunk.shape[0]))

                confidence = self._model(chunk, sr).item()
                probabilities.append(confidence)

            if not probabilities:
                return {
                    "voice_probability": 0.0,
                    "is_voice": False,
                    "chunks": 0,
                    "speech_ratio": 0.0
                }

            max_probability = max(probabilities)
            speech_chunks = sum(1 for score in probabilities if score >= self.threshold)
            speech_ratio = speech_chunks / len(probabilities)

            return {
                "voice_probability": float(max_probability),
                "is_voice": bool(max_probability >= self.threshold),
                "chunks": len(probabilities),
                "speech_ratio": round(speech_ratio, 4)
            }
