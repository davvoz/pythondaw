from .base import BaseEffect


class Compressor(BaseEffect):
    def __init__(self):
        super().__init__()
        self.parameters = {
            "threshold": -20.0,  # dBFS
            "ratio": 4.0,
            "attack": 0.01,
            "release": 0.1,
            "makeup_gain": 0.0,  # dB
        }

    def apply(self, audio_data):
        if not isinstance(audio_data, list) or not audio_data:
            return audio_data
        thr_db = float(self.parameters.get("threshold", -20.0))
        ratio = max(1.0, float(self.parameters.get("ratio", 4.0)))
        makeup_db = float(self.parameters.get("makeup_gain", 0.0))

        import math

        def db(x):
            x = max(1e-8, abs(x))
            return 20.0 * math.log10(x)

        def from_db(d):
            return 10 ** (d / 20.0)

        out = []
        for s in audio_data:
            level_db = db(s)
            if level_db > thr_db:
                exceeded = level_db - thr_db
                reduced = thr_db + exceeded / ratio
                gain_db = reduced - level_db + makeup_db
            else:
                gain_db = makeup_db
            out.append(s * from_db(gain_db))
        return out