import unittest
from src.core.track import Track

class TestTrack(unittest.TestCase):

    def setUp(self):
        self.track = Track()

    def test_add_audio(self):
        self.track.add_audio("test_audio.wav")
        self.assertIn("test_audio.wav", self.track.audio_files)

    def test_remove_audio(self):
        self.track.add_audio("test_audio.wav")
        self.track.remove_audio("test_audio.wav")
        self.assertNotIn("test_audio.wav", self.track.audio_files)

    def test_set_volume(self):
        self.track.set_volume(0.5)
        self.assertEqual(self.track.volume, 0.5)

    def test_set_volume_out_of_bounds(self):
        with self.assertRaises(ValueError):
            self.track.set_volume(1.5)
        with self.assertRaises(ValueError):
            self.track.set_volume(-0.5)

if __name__ == '__main__':
    unittest.main()