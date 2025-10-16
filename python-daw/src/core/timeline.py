from typing import List, Tuple


class Timeline:
    """Simple timeline managing (track_index, clip) placements.

    API keeps it lean and OOP; no overengineering, but ready to scale.
    """

    def __init__(self):
        self._placements: List[Tuple[int, object]] = []  # (track_index, clip)

    def add_clip(self, track_index: int, clip):
        self._placements.append((int(track_index), clip))

    def remove_clip(self, track_index: int, clip):
        try:
            self._placements.remove((int(track_index), clip))
        except ValueError:
            pass

    def get_clips_for_range(self, start_time: float, end_time: float):
        """Yield (track_index, clip) for clips overlapping [start_time, end_time)."""
        s = float(start_time)
        e = float(end_time)
        for ti, clip in self._placements:
            if getattr(clip, "start_time", None) is None:
                continue
            if clip.end_time > s and clip.start_time < e:
                yield ti, clip

    def all_placements(self):
        return list(self._placements)

    def get_clips_for_track(self, track_index: int):
        lst = [c for ti, c in self._placements if ti == int(track_index)]
        try:
            lst.sort(key=lambda c: getattr(c, "start_time", 0.0))
        except Exception:
            pass
        return lst

    def count_clips_for_track(self, track_index: int) -> int:
        return sum(1 for ti, _ in self._placements if ti == int(track_index))