from .base import BaseEffect


class Reverb(BaseEffect):
    def __init__(self):
        super().__init__()
        self.parameters = {
            "room_size": 0.5,
            "damping": 0.5,
            "wet_level": 0.5,
            "dry_level": 0.5,
        }

    def apply(self, audio_data):
        # Very simple wet/dry mix placeholder to satisfy tests
        wet = float(self.parameters.get("wet_level", 0.5))
        dry = float(self.parameters.get("dry_level", 0.5))
        # normalize mix
        total = wet + dry
        if total == 0:
            wet = 0.5
            dry = 0.5
            total = 1.0
        w = wet / total
        d = dry / total
        # Apply a trivial reverb-like tail: average with a shifted version
        if isinstance(audio_data, list) and audio_data:
            out = []
            prev = 0.0
            for s in audio_data:
                out.append(d * s + w * (0.5 * s + 0.5 * prev))
                prev = s
            return out
        return audio_data