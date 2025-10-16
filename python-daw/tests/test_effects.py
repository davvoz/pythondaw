import unittest
from src.effects.reverb import Reverb
from src.effects.delay import Delay
from src.effects.compressor import Compressor
from src.effects.equalizer import Equalizer

class TestEffects(unittest.TestCase):

    def setUp(self):
        self.reverb = Reverb()
        self.delay = Delay()
        self.compressor = Compressor()
        self.equalizer = Equalizer()

    def test_reverb_parameters(self):
        self.reverb.set_parameters({'room_size': 0.5, 'damping': 0.5})
        self.assertEqual(self.reverb.parameters['room_size'], 0.5)
        self.assertEqual(self.reverb.parameters['damping'], 0.5)

    def test_delay_parameters(self):
        self.delay.set_parameters({'delay_time': 0.3, 'feedback': 0.7})
        self.assertEqual(self.delay.parameters['delay_time'], 0.3)
        self.assertEqual(self.delay.parameters['feedback'], 0.7)

    def test_compressor_parameters(self):
        self.compressor.set_parameters({'threshold': -10, 'ratio': 4})
        self.assertEqual(self.compressor.parameters['threshold'], -10)
        self.assertEqual(self.compressor.parameters['ratio'], 4)

    def test_equalizer_parameters(self):
        self.equalizer.set_parameters({'frequency': 1000, 'gain': 3})
        self.assertEqual(self.equalizer.parameters['frequency'], 1000)
        self.assertEqual(self.equalizer.parameters['gain'], 3)

    def test_reverb_apply(self):
        input_signal = [0.5] * 10
        output_signal = self.reverb.apply(input_signal)
        self.assertIsNotNone(output_signal)

    def test_delay_apply(self):
        input_signal = [0.5] * 10
        output_signal = self.delay.apply(input_signal)
        self.assertIsNotNone(output_signal)

    def test_compressor_apply(self):
        input_signal = [0.5] * 10
        output_signal = self.compressor.apply(input_signal)
        self.assertIsNotNone(output_signal)

    def test_equalizer_apply(self):
        input_signal = [0.5] * 10
        output_signal = self.equalizer.apply(input_signal)
        self.assertIsNotNone(output_signal)

if __name__ == '__main__':
    unittest.main()