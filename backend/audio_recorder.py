"""
Audio Recorder — Networked Segment Uploader
=============================================
Records live audio from the VocalFilter stream, splits into timed segments,
compresses with Opus, and sends to the Storage Server via HTTP POST.

Falls back to local storage if the storage server is unreachable.
"""

import os
import json
import threading
import time
import tempfile
import logging
from datetime import datetime
from collections import deque

import numpy as np
import requests

from audio_compressor import compress_audio

logger = logging.getLogger(__name__)

# Defaults
DEFAULT_SEGMENT_SECONDS = 30
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_STORAGE_SERVER_URL = "http://localhost:5050"
LOCAL_FALLBACK_DIR = "audio_storage_fallback"

# HTTP upload timeout in seconds
UPLOAD_TIMEOUT = 15
MAX_RETRIES = 2


class AudioRecorder:
    """
    Thread-safe audio recorder that buffers raw audio chunks,
    splits them into timed segments, compresses with Opus,
    and uploads to the storage server over the network.
    """

    def __init__(self, storage_server_url: str = None,
                 segment_seconds: int = None,
                 sample_rate: int = DEFAULT_SAMPLE_RATE):
        """
        Args:
            storage_server_url: URL of the storage server (e.g. http://192.168.1.100:5050).
            segment_seconds: Duration of each audio segment in seconds.
            sample_rate: Audio sample rate (must match VocalFilter).
        """
        self.sample_rate = sample_rate
        self.segment_seconds = segment_seconds or DEFAULT_SEGMENT_SECONDS
        self.samples_per_segment = self.sample_rate * self.segment_seconds
        self.storage_server_url = storage_server_url or DEFAULT_STORAGE_SERVER_URL

        # Local fallback directory (if server unreachable)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self._fallback_dir = os.path.join(project_root, LOCAL_FALLBACK_DIR)

        self._buffer = []
        self._buffer_samples = 0
        self._lock = threading.Lock()
        self._running = False
        self._save_thread = None
        self._save_queue = deque()
        self._segment_count = 0
        self._upload_count = 0
        self._fallback_count = 0
        self._total_duration = 0.0
        self._server_reachable = True

    def start(self):
        """Start the audio recorder."""
        if self._running:
            logger.warning("Audio recorder is already running.")
            return

        self._running = True
        self._segment_start_time = datetime.now()

        # Check server connectivity
        self._check_server()

        # Background thread for uploading (so we don't block audio callback)
        self._save_thread = threading.Thread(
            target=self._save_worker,
            daemon=True,
            name="AudioRecorder-UploadWorker"
        )
        self._save_thread.start()

        logger.info(f"🔴 Audio Recorder started")
        logger.info(f"   Storage server: {self.storage_server_url}")
        logger.info(f"   Segment duration: {self.segment_seconds}s")
        logger.info(f"   Sample rate: {self.sample_rate}Hz")
        logger.info(f"   Server reachable: {'✅' if self._server_reachable else '❌ (will save locally)'}")

    def _check_server(self):
        """Check if the storage server is reachable."""
        try:
            resp = requests.get(
                f"{self.storage_server_url}/health",
                timeout=3
            )
            if resp.status_code == 200:
                self._server_reachable = True
                logger.info(f"✅ Storage server is online: {self.storage_server_url}")
                return
        except Exception:
            pass

        self._server_reachable = False
        logger.warning(f"⚠️  Storage server unreachable at {self.storage_server_url}")
        logger.warning(f"   Will save locally to {self._fallback_dir}")

    def stop(self):
        """Stop recording and flush any remaining buffered audio."""
        if not self._running:
            return

        logger.info("⏹️  Stopping audio recorder...")
        self._running = False

        # Flush remaining buffer
        with self._lock:
            if self._buffer_samples > 0:
                self._enqueue_segment()

        # Signal save thread to finish
        self._save_queue.append(None)  # Sentinel

        if self._save_thread and self._save_thread.is_alive():
            self._save_thread.join(timeout=15)

        logger.info(f"📊 Audio Recorder stopped. "
                    f"Segments: {self._segment_count} | "
                    f"Uploaded: {self._upload_count} | "
                    f"Local fallback: {self._fallback_count} | "
                    f"Duration: {self._total_duration:.1f}s")

    def on_audio_chunk(self, chunk: np.ndarray):
        """
        Callback to receive raw audio chunks from VocalFilter.
        Called from the audio stream thread — must be fast.
        """
        if not self._running:
            return

        with self._lock:
            self._buffer.append(chunk.copy())
            self._buffer_samples += len(chunk)

            # Check if we've accumulated a full segment
            if self._buffer_samples >= self.samples_per_segment:
                self._enqueue_segment()

    def _enqueue_segment(self):
        """Concatenate buffered chunks and queue for upload. Must hold self._lock."""
        if not self._buffer:
            return

        segment_audio = np.concatenate(self._buffer)

        if len(segment_audio) > self.samples_per_segment:
            save_audio = segment_audio[:self.samples_per_segment]
            overflow = segment_audio[self.samples_per_segment:]
            self._buffer = [overflow]
            self._buffer_samples = len(overflow)
        else:
            save_audio = segment_audio
            self._buffer = []
            self._buffer_samples = 0

        timestamp = self._segment_start_time
        self._segment_start_time = datetime.now()

        self._save_queue.append((save_audio, timestamp))

    def _save_worker(self):
        """Background thread that uploads queued segments."""
        while True:
            if not self._save_queue:
                if not self._running:
                    break
                time.sleep(0.1)
                continue

            item = self._save_queue.popleft()

            if item is None:
                while self._save_queue:
                    remaining = self._save_queue.popleft()
                    if remaining is not None:
                        self._process_segment(*remaining)
                break

            self._process_segment(*item)

    def _process_segment(self, audio: np.ndarray, timestamp: datetime):
        """Compress and upload a single audio segment."""
        tmp_dir = None
        try:
            # Create temp directory for compression
            tmp_dir = tempfile.mkdtemp(prefix="audio_seg_")

            ts_str = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
            base_name = f"audio_{ts_str}"
            output_path = os.path.join(tmp_dir, base_name)

            # Compress audio
            actual_path = compress_audio(
                samples=audio,
                sample_rate=self.sample_rate,
                output_path=output_path
            )

            duration = len(audio) / self.sample_rate
            self._segment_count += 1
            self._total_duration += duration

            # Build metadata
            metadata = {
                "timestamp": timestamp.isoformat(),
                "timestamp_unix": int(timestamp.timestamp() * 1000),
                "duration_seconds": round(duration, 2),
                "sample_rate": self.sample_rate,
                "num_samples": len(audio),
                "format": os.path.splitext(actual_path)[1].lstrip('.'),
                "original_filename": os.path.basename(actual_path),
                "file_size_bytes": os.path.getsize(actual_path)
            }

            # Try uploading to server
            uploaded = self._upload_to_server(actual_path, metadata)

            if not uploaded:
                # Fallback: save locally
                self._save_locally(actual_path, metadata)

        except Exception as e:
            logger.error(f"❌ Failed to process audio segment: {e}")
        finally:
            # Clean up temp files
            if tmp_dir and os.path.exists(tmp_dir):
                import shutil
                shutil.rmtree(tmp_dir, ignore_errors=True)

    def _upload_to_server(self, filepath: str, metadata: dict) -> bool:
        """Upload compressed audio to the storage server. Returns True on success."""
        filename = os.path.basename(filepath)

        for attempt in range(MAX_RETRIES + 1):
            try:
                with open(filepath, 'rb') as f:
                    resp = requests.post(
                        f"{self.storage_server_url}/upload",
                        files={'file': (filename, f)},
                        data={'metadata': json.dumps(metadata)},
                        timeout=UPLOAD_TIMEOUT
                    )

                if resp.status_code == 201:
                    self._upload_count += 1
                    self._server_reachable = True
                    logger.info(
                        f"📤 Uploaded segment #{self._segment_count}: "
                        f"{filename} ({metadata['file_size_bytes']:,}B, "
                        f"{metadata['duration_seconds']:.1f}s)"
                    )
                    return True
                else:
                    logger.warning(f"⚠️  Server returned {resp.status_code}: {resp.text}")

            except requests.ConnectionError:
                if attempt == 0:
                    logger.warning(f"⚠️  Storage server unreachable (attempt {attempt + 1}/{MAX_RETRIES + 1})")
                self._server_reachable = False
            except requests.Timeout:
                logger.warning(f"⚠️  Upload timed out (attempt {attempt + 1}/{MAX_RETRIES + 1})")
            except Exception as e:
                logger.error(f"❌ Upload error: {e}")
                break

            if attempt < MAX_RETRIES:
                time.sleep(1)

        return False

    def _save_locally(self, filepath: str, metadata: dict):
        """Fallback: save file to local disk."""
        import shutil
        os.makedirs(self._fallback_dir, exist_ok=True)

        filename = os.path.basename(filepath)
        dest_path = os.path.join(self._fallback_dir, filename)
        shutil.copy2(filepath, dest_path)

        json_path = os.path.splitext(dest_path)[0] + ".json"
        metadata["saved_locally"] = True
        metadata["local_fallback_reason"] = "storage_server_unreachable"
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        self._fallback_count += 1
        logger.warning(
            f"💾 Saved locally (fallback): {filename} "
            f"({metadata['file_size_bytes']:,}B)"
        )

    def get_status(self):
        """Get current recorder status."""
        with self._lock:
            buffered_seconds = self._buffer_samples / self.sample_rate
        return {
            "running": self._running,
            "storage_server_url": self.storage_server_url,
            "server_reachable": self._server_reachable,
            "segment_seconds": self.segment_seconds,
            "segments_processed": self._segment_count,
            "uploaded": self._upload_count,
            "local_fallback": self._fallback_count,
            "total_duration": round(self._total_duration, 2),
            "buffer_seconds": round(buffered_seconds, 2)
        }
