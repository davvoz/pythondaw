from dataclasses import dataclass


@dataclass
class MidiNote:
    """Simple MIDI note data for piano roll clips."""
    pitch: int            # MIDI note number (0-127)
    start: float          # start time in seconds (clip-local)
    duration: float       # duration in seconds
    velocity: int = 100   # 1-127

    @property
    def end(self) -> float:
        return float(self.start) + float(self.duration)
