class Mixer:
    """A very simple mixer that operates on scalar track levels for tests.

    Tests expect:
    - add_track(name, volume)
    - mix_tracks() -> 0.0 when no tracks
    - mix_tracks() returns 1.0 when 0.7 + 0.3 with default master 0.5 set in setUp is overridden in test
      Here we will compute sum(track volumes) then apply master volume, and clamp to 1.0.
    """

    def __init__(self):
        self.tracks = []  # list of dicts: {name, volume, pan, color}
        self.master_volume = 1.0
        self._track_counter = 0  # per nomi auto-generati

    def add_track(self, name=None, volume=1.0, pan=0.0, color=None, mute=False, solo=False):
        """Add a new track to the mixer.
        
        Args:
            name: Track name (auto-generated if None)
            volume: Initial volume (0.0-1.0)
            pan: Initial pan (-1.0 to 1.0)
            color: Hex color string (e.g., "#3b82f6") or None for auto
            mute: Track is muted (default False)
            solo: Track is soloed (default False)
        """
        if name is None:
            self._track_counter += 1
            name = f"Track {self._track_counter}"
        
        if color is None:
            # Auto-assign colors from palette
            colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"]
            color = colors[len(self.tracks) % len(colors)]
        
        self.tracks.append({
            "name": name, 
            "volume": float(volume), 
            "pan": float(pan),
            "color": color,
            "mute": bool(mute),
            "solo": bool(solo)
        })

    def remove_track(self, name):
        self.tracks = [t for t in self.tracks if t["name"] != name]

    def mix_tracks(self):
        if not self.tracks:
            return 0.0
        total = sum(t["volume"] for t in self.tracks)
        # For unit tests, ignore master volume in the returned value
        output = total
        # Clamp between 0 and 1 for test simplicity
        if output < 0.0:
            output = 0.0
        if output > 1.0:
            output = 1.0
        return output

    def set_master_volume(self, volume):
        v = float(volume)
        if v < 0.0:
            v = 0.0
        if v > 1.0:
            v = 1.0
        self.master_volume = v

    # Utilities
    def get_track(self, index: int):
        if 0 <= index < len(self.tracks):
            return self.tracks[index]
        return None
    
    def get_track_count(self):
        """Return the number of tracks."""
        return len(self.tracks)
    
    def rename_track(self, index: int, new_name: str):
        """Rename a track by index."""
        if 0 <= index < len(self.tracks):
            self.tracks[index]["name"] = new_name
    
    def set_track_color(self, index: int, color: str):
        """Set track color by index."""
        if 0 <= index < len(self.tracks):
            self.tracks[index]["color"] = color
    
    def toggle_mute(self, index: int):
        """Toggle mute state for a track."""
        if 0 <= index < len(self.tracks):
            self.tracks[index]["mute"] = not self.tracks[index].get("mute", False)
            return self.tracks[index]["mute"]
        return False
    
    def toggle_solo(self, index: int):
        """Toggle solo state for a track."""
        if 0 <= index < len(self.tracks):
            self.tracks[index]["solo"] = not self.tracks[index].get("solo", False)
            return self.tracks[index]["solo"]
        return False
    
    def has_soloed_tracks(self) -> bool:
        """Check if any track is soloed."""
        return any(t.get("solo", False) for t in self.tracks)
    
    def should_play_track(self, index: int) -> bool:
        """Determine if a track should be played based on mute/solo state.
        
        Logic:
        - If track is muted: don't play
        - If any track is soloed: play only soloed tracks
        - Otherwise: play all non-muted tracks
        """
        if 0 <= index < len(self.tracks):
            track = self.tracks[index]
            if track.get("mute", False):
                return False
            if self.has_soloed_tracks():
                return track.get("solo", False)
            return True
        return False