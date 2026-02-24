import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Clear any stale module mocks from other test files
for mod_name in ['vocal_filter', 'audio_recorder', 'audio_compressor']:
    if mod_name in sys.modules and isinstance(sys.modules[mod_name], MagicMock):
        del sys.modules[mod_name]

# Mock torch and sounddevice to prevent actual loading/hardware access during tests
mock_torch = MagicMock()
mock_sounddevice = MagicMock()

sys.modules['torch'] = mock_torch
sys.modules['sounddevice'] = mock_sounddevice

from vocal_filter import VocalFilter

class TestVocalFilter(unittest.TestCase):
    def setUp(self):
        # Reset mocks
        mock_torch.reset_mock()
        mock_sounddevice.reset_mock()
        
        # Setup torch hub load return values
        self.mock_model = MagicMock()
        self.mock_utils = (MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
        mock_torch.hub.load.return_value = (self.mock_model, self.mock_utils)

    def test_initialization(self):
        vf = VocalFilter(threshold=0.7)
        self.assertEqual(vf.threshold, 0.7)
        self.assertFalse(vf.is_voice)
        self.assertEqual(vf.voice_probability, 0.0)
        mock_torch.hub.load.assert_called_once()
        self.mock_model.eval.assert_called_once()

    def test_start_and_stop(self):
        vf = VocalFilter()
        
        # Start
        vf.start()
        self.assertTrue(vf._running)
        mock_sounddevice.InputStream.assert_called_once()
        mock_stream_instance = mock_sounddevice.InputStream.return_value
        mock_stream_instance.start.assert_called_once()
        
        # Stop
        vf.stop()
        self.assertFalse(vf._running)
        mock_stream_instance.stop.assert_called_once()
        mock_stream_instance.close.assert_called_once()

    def test_audio_callback_voice_detected(self):
        vf = VocalFilter(threshold=0.5)
        
        # Mock confidence returned by model
        self.mock_model.return_value.item.return_value = 0.8
        mock_torch.from_numpy.return_value.float.return_value = MagicMock()
        
        # Create dummy numpy array for audio chunk (512, 1)
        indata = np.zeros((512, 1), dtype=np.float32)
        
        # Call the callback directly
        vf._audio_callback(indata, frames=512, time_info=None, status=None)
        
        # Check that it updated the probability and voice flag
        self.assertEqual(vf.voice_probability, 0.8)
        self.assertTrue(vf.is_voice)

    def test_audio_callback_silence(self):
        vf = VocalFilter(threshold=0.5)
        
        # Mock confidence returned by model
        self.mock_model.return_value.item.return_value = 0.2
        mock_torch.from_numpy.return_value.float.return_value = MagicMock()

        indata = np.zeros((512, 1), dtype=np.float32)
        
        vf._audio_callback(indata, frames=512, time_info=None, status=None)
        
        self.assertEqual(vf.voice_probability, 0.2)
        self.assertFalse(vf.is_voice)
        
    def test_get_status(self):
        vf = VocalFilter(threshold=0.4)
        vf._voice_probability = 0.85
        vf._is_voice = True
        vf._running = True
        
        status = vf.get_status()
        self.assertEqual(status['voice_probability'], 0.85)
        self.assertTrue(status['is_voice_dl'])
        self.assertEqual(status['threshold'], 0.4)
        self.assertTrue(status['running'])

if __name__ == '__main__':
    unittest.main()
