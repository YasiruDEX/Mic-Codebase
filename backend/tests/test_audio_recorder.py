import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import sys
import os
import tempfile
import json
import time

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestAudioRecorder(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @patch('audio_recorder.requests')
    @patch('audio_recorder.compress_audio')
    def test_initialization(self, mock_compress, mock_requests):
        from audio_recorder import AudioRecorder

        rec = AudioRecorder(
            storage_server_url="http://192.168.1.100:5050",
            segment_seconds=10,
            sample_rate=16000
        )

        self.assertEqual(rec.sample_rate, 16000)
        self.assertEqual(rec.segment_seconds, 10)
        self.assertEqual(rec.samples_per_segment, 160000)
        self.assertEqual(rec.storage_server_url, "http://192.168.1.100:5050")
        self.assertFalse(rec._running)
        self.assertEqual(rec._segment_count, 0)

    @patch('audio_recorder.requests')
    @patch('audio_recorder.compress_audio')
    def test_start_stop_lifecycle(self, mock_compress, mock_requests):
        from audio_recorder import AudioRecorder

        # Mock health check
        mock_requests.get.return_value = MagicMock(status_code=200)

        rec = AudioRecorder(storage_server_url="http://localhost:5050", segment_seconds=10)
        rec.start()
        self.assertTrue(rec._running)

        rec.stop()
        self.assertFalse(rec._running)

    @patch('audio_recorder.requests')
    @patch('audio_recorder.compress_audio')
    def test_chunk_buffering(self, mock_compress, mock_requests):
        from audio_recorder import AudioRecorder

        mock_requests.get.return_value = MagicMock(status_code=200)

        rec = AudioRecorder(storage_server_url="http://localhost:5050", segment_seconds=10, sample_rate=16000)
        rec.start()

        chunk = np.random.randn(512).astype(np.float32)
        rec.on_audio_chunk(chunk)
        self.assertEqual(rec._buffer_samples, 512)

        rec.stop()

    @patch('audio_recorder.requests')
    @patch('audio_recorder.compress_audio')
    def test_segment_upload_to_server(self, mock_compress, mock_requests):
        from audio_recorder import AudioRecorder

        # Mock health check
        mock_requests.get.return_value = MagicMock(status_code=200)

        # Create a fake compressed file for compress_audio to "return"
        fake_opus = os.path.join(self.tmpdir, "test.opus")
        with open(fake_opus, 'wb') as f:
            f.write(b'\x00' * 100)
        mock_compress.return_value = fake_opus

        # Mock successful upload
        mock_resp = MagicMock(status_code=201)
        mock_requests.post.return_value = mock_resp

        rec = AudioRecorder(storage_server_url="http://localhost:5050", segment_seconds=1, sample_rate=16000)
        rec.start()

        # Send enough chunks for 1 second
        for _ in range(32):
            chunk = np.random.randn(512).astype(np.float32)
            rec.on_audio_chunk(chunk)

        time.sleep(1.0)
        rec.stop()

        # Verify upload was attempted
        self.assertTrue(mock_requests.post.called)

    @patch('audio_recorder.requests')
    @patch('audio_recorder.compress_audio')
    def test_fallback_to_local_when_server_down(self, mock_compress, mock_requests):
        from audio_recorder import AudioRecorder
        import requests as real_requests

        # Mock health check fails
        mock_requests.get.side_effect = real_requests.ConnectionError("Connection refused")
        mock_requests.ConnectionError = real_requests.ConnectionError
        mock_requests.Timeout = real_requests.Timeout

        # Mock upload also fails
        mock_requests.post.side_effect = real_requests.ConnectionError("Connection refused")

        # Create a fake compressed file
        fake_opus = os.path.join(self.tmpdir, "test.opus")
        with open(fake_opus, 'wb') as f:
            f.write(b'\x00' * 100)
        mock_compress.return_value = fake_opus

        rec = AudioRecorder(storage_server_url="http://unreachable:5050", segment_seconds=1, sample_rate=16000)
        rec._fallback_dir = os.path.join(self.tmpdir, "fallback")
        rec.start()

        self.assertFalse(rec._server_reachable)

        # Send enough chunks for 1 second
        for _ in range(32):
            chunk = np.random.randn(512).astype(np.float32)
            rec.on_audio_chunk(chunk)

        time.sleep(2.0)
        rec.stop()

        # Verify fallback files were saved locally
        self.assertGreater(rec._fallback_count, 0)

    @patch('audio_recorder.requests')
    @patch('audio_recorder.compress_audio')
    def test_no_recording_when_stopped(self, mock_compress, mock_requests):
        from audio_recorder import AudioRecorder

        rec = AudioRecorder(storage_server_url="http://localhost:5050")

        chunk = np.random.randn(512).astype(np.float32)
        rec.on_audio_chunk(chunk)

        self.assertEqual(rec._buffer_samples, 0)

    @patch('audio_recorder.requests')
    @patch('audio_recorder.compress_audio')
    def test_get_status(self, mock_compress, mock_requests):
        from audio_recorder import AudioRecorder

        rec = AudioRecorder(storage_server_url="http://localhost:5050", segment_seconds=30)
        status = rec.get_status()

        self.assertFalse(status['running'])
        self.assertEqual(status['segment_seconds'], 30)
        self.assertEqual(status['segments_processed'], 0)
        self.assertEqual(status['uploaded'], 0)
        self.assertEqual(status['local_fallback'], 0)
        self.assertIn('storage_server_url', status)


if __name__ == '__main__':
    unittest.main()
