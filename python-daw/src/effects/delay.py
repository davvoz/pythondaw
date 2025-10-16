from .base import BaseEffect


class Delay(BaseEffect):
    def __init__(self):
        super().__init__()
        self.parameters = {
            "delay_time": 0.3,  # seconds (for real engine); here used as fraction of buffer length
            "feedback": 0.5,
            "mix": 0.5,
        }

    def apply(self, audio_data):
        if not isinstance(audio_data, list) or not audio_data:
            return audio_data
        length = len(audio_data)
        delay_samples = max(1, int(self.parameters.get("delay_time", 0.3) * length))
        fb = float(self.parameters.get("feedback", 0.5))
        mix = float(self.parameters.get("mix", 0.5))
        out = audio_data[:]
        for i in range(delay_samples, length):
            delayed = out[i - delay_samples] * fb
            out[i] = (1 - mix) * out[i] + mix * delayed
        return out