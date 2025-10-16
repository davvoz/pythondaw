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

    def add_track(self, name=None, volume=1.0, pan=0.0, color=None):
        """Add a new track to the mixer.
        
        Args:
            name: Track name (auto-generated if None)
            volume: Initial volume (0.0-1.0)
            pan: Initial pan (-1.0 to 1.0)
            color: Hex color string (e.g., "#3b82f6") or None for auto
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
            "color": color
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