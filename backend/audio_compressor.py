"""
Audio Compressor — Opus Encoding via FFmpeg
============================================
Compresses raw audio (numpy float32 arrays) into Opus format using ffmpeg.
Falls back to uncompressed WAV if ffmpeg is not available.

Opus is the state-of-the-art codec for speech audio:
  - ~10:1 compression ratio at 32kbps
  - Designed specifically for speech and low-latency audio
  - Open standard, royalty-free
"""

import subprocess
import shutil
import tempfile
import os
import struct
import wave
import logging
import numpy as np

logger = logging.getLogger(__name__)

# Check for ffmpeg availability once at module load
FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None

if not FFMPEG_AVAILABLE:
    logger.warning("⚠️  ffmpeg not found on PATH. Audio will be saved as uncompressed WAV.")
    logger.warning("   Install ffmpeg for Opus compression: brew install ffmpeg")


def _write_wav_bytes(samples: np.ndarray, sample_rate: int) -> bytes:
    """Convert float32 numpy array to WAV bytes (16-bit PCM) in memory."""
    # Clip and convert float32 [-1.0, 1.0] to int16
    samples_clipped = np.clip(samples, -1.0, 1.0)
    samples_int16 = (samples_clipped * 32767).astype(np.int16)

    # Build WAV in memory
    import io
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(samples_int16.tobytes())
    return buf.getvalue()


def _write_wav_file(samples: np.ndarray, sample_rate: int, path: str):
    """Write float32 numpy array to a WAV file (16-bit PCM)."""
    samples_clipped = np.clip(samples, -1.0, 1.0)
    samples_int16 = (samples_clipped * 32767).astype(np.int16)

    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(samples_int16.tobytes())


def compress_audio(samples: np.ndarray, sample_rate: int, output_path: str,
                   bitrate: str = "32k") -> str:
    """
    Compress audio samples to Opus format.

    Args:
        samples: 1D float32 numpy array of audio samples.
        sample_rate: Sample rate in Hz (e.g. 16000).
        output_path: Desired output file path (without extension — extension
                     will be set to .opus or .wav depending on availability).
        bitrate: Opus encoding bitrate (default: "32k" — excellent for speech).

    Returns:
        Actual output file path (may differ in extension if fallback was used).
    """
    # Strip any existing extension and re-add the correct one
    base_path = os.path.splitext(output_path)[0]

    if FFMPEG_AVAILABLE:
        return _compress_opus(samples, sample_rate, base_path, bitrate)
    else:
        # Fallback: save as WAV
        wav_path = base_path + ".wav"
        logger.warning(f"💾 Saving as uncompressed WAV (ffmpeg not available): {wav_path}")
        _write_wav_file(samples, sample_rate, wav_path)
        return wav_path


def _compress_opus(samples: np.ndarray, sample_rate: int, base_path: str,
                   bitrate: str) -> str:
    """Encode audio to Opus using ffmpeg subprocess."""
    opus_path = base_path + ".opus"

    # Write WAV to a temporary file (ffmpeg reads from it)
    tmp_wav = None
    try:
        tmp_fd, tmp_wav = tempfile.mkstemp(suffix=".wav")
        os.close(tmp_fd)
        _write_wav_file(samples, sample_rate, tmp_wav)

        # ffmpeg: WAV → Opus
        cmd = [
            "ffmpeg",
            "-y",                   # Overwrite output
            "-i", tmp_wav,          # Input WAV
            "-c:a", "libopus",      # Opus codec
            "-b:a", bitrate,        # Bitrate
            "-ar", str(sample_rate),# Preserve sample rate
            "-ac", "1",             # Mono
            "-application", "voip", # Optimized for speech
            "-frame_duration", "20",# 20ms frames (good for speech)
            opus_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            logger.error(f"❌ ffmpeg error: {result.stderr}")
            # Fallback to WAV
            wav_path = base_path + ".wav"
            _write_wav_file(samples, sample_rate, wav_path)
            logger.warning(f"💾 Fell back to WAV: {wav_path}")
            return wav_path

        # Log compression stats
        wav_size = os.path.getsize(tmp_wav)
        opus_size = os.path.getsize(opus_path)
        ratio = wav_size / opus_size if opus_size > 0 else 0
        logger.info(f"🗜️  Compressed: {wav_size:,}B → {opus_size:,}B ({ratio:.1f}x)")

        return opus_path

    finally:
        # Clean up temp WAV
        if tmp_wav and os.path.exists(tmp_wav):
            os.unlink(tmp_wav)


def decompress_audio(input_path: str, output_path: str = None) -> str:
    """
    Decompress an Opus file back to WAV.

    Args:
        input_path: Path to the .opus file.
        output_path: Optional output WAV path. If None, replaces extension with .wav.

    Returns:
        Path to the decompressed WAV file.
    """
    if not FFMPEG_AVAILABLE:
        raise RuntimeError("ffmpeg is required for decompression. Install it: brew install ffmpeg")

    if output_path is None:
        output_path = os.path.splitext(input_path)[0] + ".wav"

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-c:a", "pcm_s16le",   # 16-bit PCM
        "-ar", "16000",         # 16kHz
        "-ac", "1",             # Mono
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg decompression failed: {result.stderr}")

    logger.info(f"📂 Decompressed: {input_path} → {output_path}")
    return output_path
