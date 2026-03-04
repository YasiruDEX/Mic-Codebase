import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock audio_recorder before importing tracker
sys.modules['audio_recorder'] = MagicMock()

import firebase_tracker

class TestUploaderTracker(unittest.TestCase):

    @patch('usb.core.find')
    def test_initialize_mic_not_found(self, mock_usb_find):
        mock_usb_find.return_value = None

        mic = firebase_tracker.initialize_mic()

        self.assertIsNone(mic)
        mock_usb_find.assert_called_once_with(idVendor=0x2886, idProduct=0x0018)

    @patch('firebase_tracker.time.sleep', side_effect=KeyboardInterrupt)
    @patch('firebase_tracker.sd.InputStream')
    @patch('firebase_tracker.initialize_mic')
    @patch('firebase_tracker.AudioRecorder')
    def test_run_tracker_lifecycle(self, mock_audio_recorder_cls, mock_init_mic, mock_input_stream, _mock_sleep):
        mock_mic = MagicMock()
        mock_mic.direction = 180
        mock_mic.is_voice.return_value = 1
        mock_init_mic.return_value = mock_mic

        recorder_instance = mock_audio_recorder_cls.return_value
        recorder_instance.get_status.return_value = {
            'uploaded': 0,
            'buffer_seconds': 0.0
        }

        stream_instance = mock_input_stream.return_value

        firebase_tracker.run_tracker()

        mock_init_mic.assert_called_once()

        mock_audio_recorder_cls.assert_called_once()
        recorder_kwargs = mock_audio_recorder_cls.call_args.kwargs
        self.assertIn('metadata_provider', recorder_kwargs)
        self.assertTrue(callable(recorder_kwargs['metadata_provider']))

        recorder_instance.start.assert_called_once()
        recorder_instance.stop.assert_called_once()

        stream_instance.start.assert_called_once()
        stream_instance.stop.assert_called_once()
        stream_instance.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
