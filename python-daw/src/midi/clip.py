from __future__ import annotations

from typing import List, Sequence, Optional
from dataclasses import dataclass, field

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None  # type: ignore

from .note import MidiNote


@dataclass
class MidiClip:
    """A MIDI clip containing notes and rendering through an instrument.

    This integrates with the existing audio engine by exposing:
    - start_time, end_time, duration, sample_rate, name
    - slice_samples(start_sec, end_sec) -> Sequence[float]
    - get_peaks(num_points) for visualization
    """

    name: str
    notes: List[MidiNote] = field(default_factory=list)
    start_time: float = 0.0
    duration: Optional[float] = None  # clip duration in seconds; if None, derived from last note end
    color: Optional[str] = None
    instrument: object = None  # Expected to provide render(pitches, times, velocities)
    sample_rate: int = 44100

    # Visual helpers
    selected: bool = False

    @property
    def length_seconds(self) -> float:
        """Return the effective length considering both duration and notes.
        
        Returns the maximum between:
        - Explicit duration (if set)
        - Last note end time (if notes exist)
        
        Note: For empty clips, returns 0.0. The UI/timeline should handle
        minimum visual size separately, ideally in musical time (beats/bars).
        """
        explicit_duration = float(self.duration) if self.duration is not None else 0.0
        
        # Calculate duration from notes
        notes_duration = 0.0
        if self.notes:
            last_end = max((n.end for n in self.notes), default=0.0)
            notes_duration = float(last_end)
        
        # Return the maximum - no artificial minimum in seconds
        return max(explicit_duration, notes_duration)

    @property
    def end_time(self) -> float:
        return float(self.start_time) + float(self.length_seconds)

    def add_note(self, note: MidiNote):
        self.notes.append(note)

    # --- Audio interface ---
    def slice_samples(self, start_sec: float, end_sec: float) -> Sequence[float]:
        """Render notes overlapping [start_sec, end_sec) in clip-local time.

        The instrument must provide a `render_notes(notes, start_sec, end_sec, sample_rate)` method
        returning a mono buffer (list[float]). If not available, we fallback to silence.
        """
        if end_sec <= start_sec or self.sample_rate <= 0:
            return []

        local_start = float(start_sec)
        local_end = float(end_sec)

        # Collect overlapping notes in this window
        overlapping: List[MidiNote] = []
        for n in self.notes:
            if n.end > local_start and n.start < local_end:
                overlapping.append(n)

        if not overlapping:
            return [0.0] * int(round((local_end - local_start) * self.sample_rate))

        # Instrument-based rendering
        inst = self.instrument
        if inst is not None and hasattr(inst, 'render_notes'):
            try:
                return inst.render_notes(overlapping, local_start, local_end, self.sample_rate)
            except Exception:
                pass

        # Fallback: simple sine rendering if no instrument
        return _fallback_render(overlapping, local_start, local_end, self.sample_rate)

    def get_peaks(self, num_points: int = 100) -> list:
        """Return simple peaks for drawing. We'll synthesize a low-res preview."""
        win = min(2.0, self.length_seconds)  # render up to 2 seconds for preview
        sr = min(22050, self.sample_rate)
        buf = self.slice_samples(0.0, max(0.05, win))
        if not buf:
            return [(0.0, 0.0)] * num_points
        # Downsample to num_points ranges
        total = len(buf)
        if total <= num_points:
            # simple grouping
            step = 1
        else:
            step = total // num_points
        peaks = []
        for i in range(num_points):
            s = i * step
            e = min(len(buf), s + step)
            if s >= len(buf):
                peaks.append((0.0, 0.0))
            else:
                seg = buf[s:e]
                if seg:
                    peaks.append((min(seg), max(seg)))
                else:
                    peaks.append((0.0, 0.0))
        return peaks


def _fallback_render(notes: List[MidiNote], start_sec: float, end_sec: float, sample_rate: int) -> List[float]:
    """Very simple additive sine rendering for fallback."""
    import math
    n_samples = int(round((end_sec - start_sec) * sample_rate))
    if n_samples <= 0:
        return []
    out = [0.0] * n_samples

    def midi_to_freq(m: int) -> float:
        return 440.0 * (2.0 ** ((m - 69) / 12.0))

    for note in notes:
        f = midi_to_freq(int(note.pitch))
        amp = max(0.0, min(1.0, note.velocity / 127.0)) * 0.2
        # overlap within [start_sec, end_sec)
        n0 = max(0, int(round((note.start - start_sec) * sample_rate)))
        n1 = min(n_samples, int(round((note.end - start_sec) * sample_rate)))
        phase = 0.0
        for i in range(n0, max(n0, n1)):
            t = (start_sec + i / sample_rate) - note.start
            # simple decay envelope
            env = 1.0
            if note.duration > 0:
                env = max(0.0, 1.0 - (t / note.duration))
            out[i] += math.sin(2 * math.pi * f * (i / sample_rate)) * amp * env

    # clamp
    for i in range(n_samples):
        v = out[i]
        if v > 1.0:
            v = 1.0
        elif v < -1.0:
            v = -1.0
        out[i] = v
    return out
