import unittest
from src.audio.mixer import Mixer

class TestMixer(unittest.TestCase):

    def setUp(self):
        self.mixer = Mixer()
        self.mixer.set_master_volume(0.5)

    def test_mix_tracks(self):
        # Assuming we have a method to add tracks for mixing
        self.mixer.add_track('Track 1', 0.7)
        self.mixer.add_track('Track 2', 0.3)
        mixed_output = self.mixer.mix_tracks()
        self.assertEqual(mixed_output, 1.0)  # Example assertion

    def test_set_master_volume(self):
        self.mixer.set_master_volume(0.8)
        self.assertEqual(self.mixer.master_volume, 0.8)

    def test_mixing_with_no_tracks(self):
        mixed_output = self.mixer.mix_tracks()
        self.assertEqual(mixed_output, 0.0)  # No tracks should yield 0 output

if __name__ == '__main__':
    unittest.main()