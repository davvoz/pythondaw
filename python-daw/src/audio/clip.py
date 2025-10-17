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

        # --- Clip editing parameters (trim, fades, pitch) ---
        # Trim offsets in seconds (applied to source buffer)
        self.start_offset: float = 0.0
        self.end_offset: float = 0.0

        # Fade durations in seconds and shapes
        self.fade_in: float = 0.0
        self.fade_in_shape: str = "linear"  # 'linear' | 'exp' | 'log' | 's-curve'
        self.fade_out: float = 0.0
        self.fade_out_shape: str = "linear"

        # Pitch shift in semitones (simple resampling, tempo changes)
        self.pitch_semitones: float = 0.0
        
        # Volume control (0.0 to 2.0, where 1.0 is unity gain)
        self.volume: float = 1.0

    @property
    def length_seconds(self) -> float:
        """Logical clip length shown on the timeline.

        If an explicit duration is provided, it is used.
        Otherwise derive from buffer length minus trims.
        """
        if self.duration is not None:
            return self.duration
        if self.sample_rate <= 0:
            return 0.0
        total = len(self.buffer) / float(self.sample_rate)
        eff = max(0.0, total - float(self.start_offset) - float(self.end_offset))
        return eff

    @property
    def end_time(self) -> float:
        return self.start_time + self.length_seconds

    def _playback_rate(self) -> float:
        # 2^(n/12)
        import math
        return float(math.pow(2.0, self.pitch_semitones / 12.0))

    def _shape_envelope(self, x, shape: str):
        """Map x in [0,1] to shaped envelope in [0,1]. x can be scalar or numpy array."""
        try:
            import numpy as np  # type: ignore
        except Exception:  # pragma: no cover - fallback to scalar math used below
            np = None

        s = (shape or "linear").lower()
        if np is None or not hasattr(x, "__array__"):
            # scalar-ish fallback
            xv = max(0.0, min(1.0, float(x)))
            if s == "linear":
                return xv
            if s in ("exp", "exponential"):
                return xv ** 2.0
            if s in ("log", "logarithmic"):
                import math
                return math.log1p(9 * xv) / math.log(10.0)
            if s in ("s-curve", "scurve", "sigmoid"):
                return xv * xv * (3.0 - 2.0 * xv)
            return xv

        # numpy path
        x = np.clip(x, 0.0, 1.0)
        if s == "linear":
            return x
        if s in ("exp", "exponential"):
            return np.power(x, 2.0)
        if s in ("log", "logarithmic"):
            eps = 1e-6
            return np.log1p(9 * x) / np.log(10.0 + eps)
        if s in ("s-curve", "scurve", "sigmoid"):
            return x * x * (3.0 - 2.0 * x)
        return x

    def _apply_fades_np(self, seg_np, seg_start_t: float):
        """Apply fade-in/out envelope to numpy segment in-place and return it."""
        import numpy as np

        sr = float(self.sample_rate)
        n = seg_np.shape[0]
        if n == 0:
            return seg_np

        # time inside the clip playback (seconds from clip start)
        t = seg_start_t + (np.arange(n, dtype=np.float32) / sr)

        g_in = 1.0
        if self.fade_in > 0.0:
            g_in = self._shape_envelope(t / float(self.fade_in), self.fade_in_shape)

        g_out = 1.0
        if self.fade_out > 0.0:
            clip_len = max(0.0, float(self.length_seconds))
            dist_to_end = (clip_len - t) / float(self.fade_out)
            g_out = self._shape_envelope(dist_to_end, self.fade_out_shape)

        seg_np *= (g_in * g_out)
        return seg_np

    def slice_samples(self, start_sec: float, end_sec: float) -> Sequence[float]:
        """Return samples for [start_sec, end_sec) in clip-local time, applying:
        - start/end trims
        - pitch via resampling (tempo changes)
        - fade-in/out envelopes
        """
        sr = int(self.sample_rate)
        if sr <= 0:
            return []

        start_sec = float(start_sec)
        end_sec = float(end_sec)
        if end_sec <= start_sec:
            return []

        out_len = int(round((end_sec - start_sec) * sr))
        if out_len <= 0:
            return []

        # playback rate determined by pitch
        rate = self._playback_rate()

        # effective source end index constrained by end_offset
        total_samps = len(self.buffer)
        if total_samps == 0:
            return []

        # last allowed source time (seconds) and index due to end_offset
        max_time_allowed = max(0.0, (total_samps / float(sr)) - float(self.end_offset))
        max_index_allowed = int(max_time_allowed * sr) - 1  # inclusive

        # starting source time (seconds) after start_offset and pitch rate
        s0_sec = float(self.start_offset) + start_sec * rate

        # numpy path if available for better quality (linear interpolation + shaped fades)
        try:
            import numpy as np  # type: ignore
        except Exception:
            np = None

        if np is None:
            # Fallback: nearest-neighbor with simple linear fades
            out = []
            for i in range(out_len):
                t_clip = start_sec + (i / sr)
                s_sec = s0_sec + (i / sr) * rate
                s_idx = int(round(s_sec * sr))
                if s_idx < 0 or s_idx > max_index_allowed or s_idx >= total_samps:
                    sample = 0.0
                else:
                    sample = float(self.buffer[s_idx])
                # linear fade-in
                if self.fade_in > 0.0:
                    phase_in = max(0.0, min(1.0, t_clip / self.fade_in))
                    sample *= phase_in
                # linear fade-out
                if self.fade_out > 0.0:
                    clip_len = max(0.0, float(self.length_seconds))
                    phase_out = max(0.0, min(1.0, (clip_len - t_clip) / self.fade_out))
                    sample *= phase_out
                # apply volume
                sample *= float(self.volume)
                out.append(sample)
            return out

        # numpy interpolation
        src_np = np.asarray(self.buffer, dtype=np.float32)
        out_idx = np.arange(out_len, dtype=np.float32)
        pos_sec = s0_sec + (out_idx / float(sr)) * rate
        pos_idx = pos_sec * float(sr)

        y = np.interp(
            pos_idx,
            np.arange(total_samps, dtype=np.float32),
            src_np,
            left=0.0,
            right=0.0,
        ).astype(np.float32)

        # zero out samples past allowed end due to end_offset
        if max_index_allowed < (total_samps - 1):
            mask = pos_idx <= float(max_index_allowed)
            y = y * mask.astype(np.float32)

        # apply fades relative to clip-local time
        y = self._apply_fades_np(y, seg_start_t=start_sec)
        
        # apply volume
        y = y * float(self.volume)

        return y.astype(float).tolist()
    
    def get_peaks(self, num_points: int = 100) -> list:
        """Get simplified waveform peaks for visualization.
        
        Args:
            num_points: Number of peak points to return
            
        Returns:
            List of (min, max) tuples representing peaks
        """
        if not self.buffer or len(self.buffer) == 0:
            return [(0.0, 0.0)] * num_points
        # visualize trimmed region of the buffer
        sr = max(1, int(self.sample_rate))
        start_idx = max(0, int(float(self.start_offset) * sr))
        end_limit = len(self.buffer) - int(float(self.end_offset) * sr)
        end_limit = max(start_idx, min(len(self.buffer), end_limit))
        buf = self.buffer[start_idx:end_limit]
        if not buf:
            return [(0.0, 0.0)] * num_points

        samples_per_point = max(1, len(buf) // num_points)
        peaks = []
        
        for i in range(num_points):
            start = i * samples_per_point
            end = min(start + samples_per_point, len(buf))
            
            if start < len(buf):
                segment = buf[start:end]
                if segment:
                    min_val = min(segment)
                    max_val = max(segment)
                    peaks.append((min_val, max_val))
                else:
                    peaks.append((0.0, 0.0))
            else:
                peaks.append((0.0, 0.0))
        
        return peaks
