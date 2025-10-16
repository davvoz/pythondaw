from .base import BaseEffect


class Equalizer(BaseEffect):
    def __init__(self):
        super().__init__()
        self.parameters = {
            "frequency": 1000.0,
            "gain": 0.0,  # dB
            "q": 1.0,
        }

    def apply(self, audio_data):
        # Simple gain for placeholder: apply linear gain derived from dB
        if not isinstance(audio_data, list) or not audio_data:
            return audio_data
        import math

        g_db = float(self.parameters.get("gain", 0.0))
        linear = 10 ** (g_db / 20.0)
        return [s * linear for s in audio_data]