from typing import List


class AudioEngine:
    def __init__(self):
        self.is_initialized = False

    def initialize(self):
        # Initialize audio system (placeholder)
        self.is_initialized = True

    def start_playback(self):
        if not self.is_initialized:
            raise RuntimeError("AudioEngine not initialized.")
        # Start audio playback (placeholder)

    def stop_playback(self):
        if not self.is_initialized:
            raise RuntimeError("AudioEngine not initialized.")
        # Stop audio playback (placeholder)

    # Offline rendering for a time window
    def render_window(self, timeline, start_time: float, duration: float, sample_rate: int) -> List[float]:
        """Render a mono buffer for [start_time, start_time+duration).

        Combina i clip sovrapposti sommandoli e clampando in [-1, 1].
        """
        if duration <= 0:
            return []
        total_samples = int(duration * sample_rate)
        output = [0.0] * total_samples
        end_time = start_time + duration
        for track_index, clip in timeline.get_clips_for_range(start_time, end_time):
            # determina gli intervalli di sovrapposizione
            overlap_start = max(start_time, clip.start_time)
            overlap_end = min(end_time, clip.end_time)
            if overlap_end <= overlap_start:
                continue
            # campioni nel buffer di output
            out_start_idx = int((overlap_start - start_time) * sample_rate)
            out_end_idx = int((overlap_end - start_time) * sample_rate)
            # campioni nel buffer del clip (local time)
            clip_local_start = overlap_start - clip.start_time
            clip_local_end = overlap_end - clip.start_time
            clip_samples = clip.slice_samples(clip_local_start, clip_local_end)
            # mix semplice (somma e clamp)
            for i, s in enumerate(clip_samples):
                idx = out_start_idx + i
                if 0 <= idx < total_samples:
                    mixed = output[idx] + float(s)
                    if mixed > 1.0:
                        mixed = 1.0
                    elif mixed < -1.0:
                        mixed = -1.0
                    output[idx] = mixed
        return output