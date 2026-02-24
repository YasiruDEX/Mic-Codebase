import unittest
from unittest.mock import patch, MagicMock, mock_open
import numpy as np
import sys
import os
import tempfile
import shutil

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestAudioCompressor(unittest.TestCase):

    def test_write_wav_file(self):
        """Test WAV file creation from float32 samples."""
        from audio_compressor import _write_wav_file

        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = os.path.join(tmpdir, "test.wav")
            samples = np.random.randn(16000).astype(np.float32) * 0.5

            _write_wav_file(samples, 16000, wav_path)

            self.assertTrue(os.path.exists(wav_path))
            self.assertGreater(os.path.getsize(wav_path), 0)

            # Verify WAV headers
            import wave
            with wave.open(wav_path, 'rb') as wf:
                self.assertEqual(wf.getnchannels(), 1)
                self.assertEqual(wf.getsampwidth(), 2)
                self.assertEqual(wf.getframerate(), 16000)
                self.assertEqual(wf.getnframes(), 16000)

    def test_write_wav_bytes(self):
        """Test WAV bytes generation in memory."""
        from audio_compressor import _write_wav_bytes

        samples = np.zeros(8000, dtype=np.float32)
        wav_bytes = _write_wav_bytes(samples, 16000)

        self.assertIsInstance(wav_bytes, bytes)
        self.assertGreater(len(wav_bytes), 44)  # WAV header is 44 bytes
        # RIFF header check
        self.assertTrue(wav_bytes[:4] == b'RIFF')

    def test_compress_audio_fallback_to_wav(self):
        """Test that compression falls back to WAV when ffmpeg is missing."""
        import audio_compressor

        # Force ffmpeg unavailable
        original = audio_compressor.FFMPEG_AVAILABLE
        audio_compressor.FFMPEG_AVAILABLE = False

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                samples = np.random.randn(16000).astype(np.float32) * 0.5
                output_path = os.path.join(tmpdir, "test.opus")

                result = audio_compressor.compress_audio(samples, 16000, output_path)

                # Should have fallen back to WAV
                self.assertTrue(result.endswith(".wav"))
                self.assertTrue(os.path.exists(result))
        finally:
            audio_compressor.FFMPEG_AVAILABLE = original

    @patch('audio_compressor.subprocess')
    def test_compress_audio_opus_success(self, mock_subprocess):
        """Test Opus compression with mocked ffmpeg."""
        import audio_compressor

        original = audio_compressor.FFMPEG_AVAILABLE
        audio_compressor.FFMPEG_AVAILABLE = True

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                samples = np.random.randn(16000).astype(np.float32) * 0.5
                output_path = os.path.join(tmpdir, "test.opus")

                # Mock successful ffmpeg run
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_subprocess.run.return_value = mock_result

                # Create fake opus file so os.path.getsize works
                opus_path = os.path.join(tmpdir, "test.opus")
                with open(opus_path, 'wb') as f:
                    f.write(b'\x00' * 100)

                result = audio_compressor.compress_audio(samples, 16000, output_path)

                # Should have called ffmpeg
                mock_subprocess.run.assert_called_once()
                call_args = mock_subprocess.run.call_args
                cmd = call_args[0][0]
                self.assertEqual(cmd[0], "ffmpeg")
                self.assertIn("libopus", cmd)
        finally:
            audio_compressor.FFMPEG_AVAILABLE = original

    def test_clipping_in_wav_write(self):
        """Test that samples outside [-1, 1] are clipped."""
        from audio_compressor import _write_wav_file

        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = os.path.join(tmpdir, "test.wav")
            # Samples with values > 1 and < -1
            samples = np.array([2.0, -2.0, 0.5, -0.5], dtype=np.float32)

            _write_wav_file(samples, 16000, wav_path)

            import wave
            with wave.open(wav_path, 'rb') as wf:
                frames = wf.readframes(4)
                # Convert back to int16
                import struct
                values = struct.unpack('<4h', frames)
                # Clipped values should be 32767 and -32767
                self.assertEqual(values[0], 32767)
                self.assertEqual(values[1], -32767)


if __name__ == '__main__':
    unittest.main()
