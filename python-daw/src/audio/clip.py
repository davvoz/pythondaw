from typing import Optional, Sequence


class AudioClip:
    """Represents an audio clip placed on a timeline.

    Attributes:
        name: Optional label for UI.
        buffer: Sequence[float] mono samples in range [-1, 1] (placeholder for real buffers)
        start_time: Start time on timeline (seconds)
        duration: Optional override for clip duration (seconds); if None, derived from buffer length and sample_rate
        sample_rate: Samples per second of buffer
    """

    def __init__(
        self,
        name: str,
        buffer: Sequence[float],
        sample_rate: int,
        start_time: float,
        duration: Optional[float] = None,
        color: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> None:
        self.name = name
        self.buffer = buffer
        self.sample_rate = int(sample_rate)
        self.start_time = float(start_time)
        self.duration = float(duration) if duration is not None else None
        self.color = color  # Optional override color
        self.file_path = file_path  # Source file path if imported
        self.selected = False  # Selection state for UI

    @property
    def length_seconds(self) -> float:
        if self.duration is not None:
            return self.duration
        return len(self.buffer) / float(self.sample_rate) if self.sample_rate > 0 else 0.0

    @property
    def end_time(self) -> float:
        return self.start_time + self.length_seconds

    def slice_samples(self, start_sec: float, end_sec: float) -> Sequence[float]:
        """Return samples for the clip region [start_sec, end_sec) in clip-local time.

        Note: This is a simple list slice on the placeholder buffer.
        """
        start_idx = max(0, int(start_sec * self.sample_rate))
        end_idx = max(start_idx, int(end_sec * self.sample_rate))
        return self.buffer[start_idx:end_idx]
    
    def get_peaks(self, num_points: int = 100) -> list:
        """Get simplified waveform peaks for visualization.
        
        Args:
            num_points: Number of peak points to return
            
        Returns:
            List of (min, max) tuples representing peaks
        """
        if not self.buffer or len(self.buffer) == 0:
            return [(0.0, 0.0)] * num_points
        
        samples_per_point = max(1, len(self.buffer) // num_points)
        peaks = []
        
        for i in range(num_points):
            start = i * samples_per_point
            end = min(start + samples_per_point, len(self.buffer))
            
            if start < len(self.buffer):
                segment = self.buffer[start:end]
                if segment:
                    min_val = min(segment)
                    max_val = max(segment)
                    peaks.append((min_val, max_val))
                else:
                    peaks.append((0.0, 0.0))
            else:
                peaks.append((0.0, 0.0))
        
        return peaks
