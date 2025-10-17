class Project:
    def __init__(self, name: str = "Untitled", bpm: float = 120.0, time_signature: tuple = (4, 4)):
        self.name = name
        self.tracks = []
        self.sessions = []
        self.bpm = float(bpm)  # beats per minute
        self.time_signature_num = int(time_signature[0])  # numerator (beats per bar)
        self.time_signature_den = int(time_signature[1])  # denominator (note value)

    def create_track(self, track):
        self.tracks.append(track)

    def remove_track(self, track):
        if track in self.tracks:
            self.tracks.remove(track)

    def save_project(self, file_path, embed_audio=False):
        """Save project with all data (tracks, clips, audio).
        
        Args:
            file_path: Path to save the .daw project file
            embed_audio: If True, embed audio in JSON. If False, save to separate files.
        """
        from ..utils.project_serializer import save_project as serialize_save
        serialize_save(self, file_path, embed_audio)
    
    @staticmethod
    def load_project(file_path):
        """Load a project from file.
        
        Args:
            file_path: Path to the .daw project file
            
        Returns:
            Loaded Project instance
        """
        from ..utils.project_serializer import load_project as serialize_load
        return serialize_load(file_path)

    def get_beat_duration(self) -> float:
        """Return duration of one beat in seconds."""
        return 60.0 / self.bpm

    def get_bar_duration(self) -> float:
        """Return duration of one bar/measure in seconds."""
        # For 4/4 time, one bar = 4 beats
        # For 3/4 time, one bar = 3 beats
        # denominator 4 means quarter note gets the beat
        beats_per_bar = self.time_signature_num * (4.0 / self.time_signature_den)
        return beats_per_bar * self.get_beat_duration()

    def seconds_to_bars(self, seconds: float) -> float:
        """Convert seconds to bars (fractional)."""
        return seconds / self.get_bar_duration()

    def bars_to_seconds(self, bars: float) -> float:
        """Convert bars to seconds."""
        return bars * self.get_bar_duration()

    def snap_to_grid(self, time: float, grid_division: float = 1.0) -> float:
        """Snap time to grid. grid_division: 1.0=bar, 0.5=half bar, 0.25=quarter, etc."""
        grid_size = self.get_bar_duration() * grid_division
        return round(time / grid_size) * grid_size