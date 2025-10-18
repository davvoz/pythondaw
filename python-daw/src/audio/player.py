from __future__ import annotations

from typing import Optional
import threading

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None  # type: ignore

try:
    import sounddevice as sd
except Exception:  # pragma: no cover
    sd = None  # type: ignore


class TimelinePlayer:
    """Simple real-time player that reads from a Timeline in a callback.

    Now stereo with per-track volume/pan (equal-power) and master volume support.
    Gracefully degrades if sounddevice/numpy is missing.
    """

    def __init__(self, timeline, sample_rate: int = 44100, block_size: int = 512, mixer=None, project=None):
        self.timeline = timeline
        self.sample_rate = int(sample_rate)
        self.block_size = int(block_size)
        self.mixer = mixer
        self.project = project  # New: reference to project for effects
        self._stream: Optional[object] = None
        self._playing = False
        self._current_time = 0.0
        self._lock = threading.Lock()
        # expose last-processed block peaks for simple UI meters
        self._last_peak_L: float = 0.0
        self._last_peak_R: float = 0.0
        # loop state
        self._loop_enabled = False
        self._loop_start = 0.0
        self._loop_end = 4.0  # default 4 seconds

    def start(self, start_time: float = 0.0):
        if sd is None or np is None:
            print("TimelinePlayer: sounddevice/numpy not available. Real-time playback disabled.")
            return
        with self._lock:
            # Protection: if already playing, ignore the request
            if self._playing:
                print("TimelinePlayer: Already playing, ignoring start request.")
                return
            self._current_time = float(start_time)
            self._stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=2,
                dtype="float32",
                blocksize=self.block_size,
                callback=self._callback,
            )
            self._stream.start()
            self._playing = True
            print("Playback started (real-time).")

    def stop(self):
        with self._lock:
            if self._stream is not None:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception:
                    pass
                self._stream = None
            if self._playing:
                print("Playback stopped (real-time).")
            self._playing = False

    def is_playing(self) -> bool:
        return self._playing

    def set_loop(self, enabled: bool, start: float = None, end: float = None):
        """Enable/disable loop and optionally set loop points."""
        with self._lock:
            self._loop_enabled = bool(enabled)
            if start is not None:
                self._loop_start = float(start)
            if end is not None:
                self._loop_end = float(end)
            # ensure start < end
            if self._loop_start >= self._loop_end:
                self._loop_end = self._loop_start + 1.0

    def get_loop(self) -> tuple:
        """Return (enabled, start, end)."""
        with self._lock:
            return (self._loop_enabled, self._loop_start, self._loop_end)

    def set_current_time(self, time: float):
        """Set playback position."""
        with self._lock:
            self._current_time = float(time)

    def get_current_time(self) -> float:
        """Get current playback position."""
        with self._lock:
            return self._current_time

    # ----- internal -----
    def _callback(self, outdata, frames, time, status):  # pragma: no cover - realtime
        if status:
            print(f"Audio status: {status}")
        # Prepare stereo output buffer
        outL = np.zeros(frames, dtype=np.float32)
        outR = np.zeros(frames, dtype=np.float32)
        with self._lock:
            start_t = self._current_time
        end_t = start_t + frames / float(self.sample_rate)

        # Group clips by track (same as render_window for effects)
        track_clips = {}
        for track_index, clip in self.timeline.get_clips_for_range(start_t, end_t):
            # Check mute/solo state
            if self.mixer is not None and hasattr(self.mixer, 'should_play_track'):
                if not self.mixer.should_play_track(track_index):
                    continue  # Skip this track
            
            if track_index not in track_clips:
                track_clips[track_index] = []
            track_clips[track_index].append(clip)
        
        # Process each track separately (render clips, apply effects, then pan/mix)
        for track_index, clips in track_clips.items():
            # Create mono buffer for this track
            track_mono = np.zeros(frames, dtype=np.float32)
            
            # Mix all clips of this track
            for clip in clips:
                overlap_start = max(start_t, clip.start_time)
                overlap_end = min(end_t, clip.end_time)
                if overlap_end <= overlap_start:
                    continue
                out_start = int((overlap_start - start_t) * self.sample_rate)
                out_end = int((overlap_end - start_t) * self.sample_rate)
                clip_local_start = overlap_start - clip.start_time
                clip_local_end = overlap_end - clip.start_time
                
                # Get clip samples
                samples = clip.slice_samples(clip_local_start, clip_local_end)
                if not samples:
                    continue
                
                seg = np.asarray(samples, dtype=np.float32)
                seg_len = min(len(seg), out_end - out_start)
                if seg_len <= 0:
                    continue
                
                # Mix into track buffer (clips already have their volume applied)
                track_mono[out_start:out_start + seg_len] += seg[:seg_len]
            
            # Apply per-track effects (if project available)
            if self.project is not None and hasattr(self.project, 'tracks'):
                try:
                    if 0 <= int(track_index) < len(self.project.tracks):
                        tr = self.project.tracks[int(track_index)]
                        fx_chain = getattr(tr, 'effects', None)
                        if fx_chain and getattr(fx_chain, 'slots', None):
                            # Convert to list for effects processing
                            track_list = track_mono.tolist()
                            track_list = fx_chain.process(track_list)
                            track_mono = np.asarray(track_list, dtype=np.float32)
                except Exception as e:
                    # Fail-safe: ignore effect errors in real-time
                    pass
            
            # Clamp track buffer
            np.clip(track_mono, -1.0, 1.0, out=track_mono)
            
            # Apply track gain and pan
            gain = 1.0
            pan = 0.0
            if self.mixer is not None and hasattr(self.mixer, "get_track"):
                tr = self.mixer.get_track(track_index)
                if tr is not None:
                    gain = float(tr.get("volume", 1.0))
                    pan = float(tr.get("pan", 0.0))  # -1..1
            
            # Equal-power pan
            import math
            angle = (pan + 1) * (math.pi / 4)  # map [-1,1] -> [0, pi/2]
            gL = math.cos(angle) * gain
            gR = math.sin(angle) * gain

            # Mix into stereo output
            outL += track_mono * gL
            outR += track_mono * gR

        # Master volume
        mv = 1.0
        if self.mixer is not None:
            mv = float(getattr(self.mixer, "master_volume", 1.0))
        outL *= mv
        outR *= mv

        # clamp
        np.clip(outL, -1.0, 1.0, out=outL)
        np.clip(outR, -1.0, 1.0, out=outR)
        outdata[:, 0] = outL
        outdata[:, 1] = outR

        # advance time and handle loop
        with self._lock:
            self._current_time = end_t
            # check if we need to loop back
            if self._loop_enabled:
                if self._current_time >= self._loop_end:
                    # wrap around to loop start
                    self._current_time = self._loop_start
            # update peaks for UI
            try:
                self._last_peak_L = float(np.max(np.abs(outL)))
                self._last_peak_R = float(np.max(np.abs(outR)))
            except Exception:
                self._last_peak_L = 0.0
                self._last_peak_R = 0.0
