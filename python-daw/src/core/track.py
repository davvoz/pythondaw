class Track:
    """
    Minimal Track model aligned with test expectations.

    - Constructor requires no args
    - Manages a list named `audio_files`
    - Volume clamped between 0.0 and 1.0 via set_volume
    """

    def __init__(self, name: str = None):
        self.audio_files = []
        self.volume = 1.0
        self.name = name  # Optional track name

    def add_audio(self, audio_file):
        self.audio_files.append(audio_file)

    def remove_audio(self, audio_file):
        if audio_file in self.audio_files:
            self.audio_files.remove(audio_file)

    def set_volume(self, volume):
        if 0.0 <= volume <= 1.0:
            self.volume = float(volume)
        else:
            raise ValueError("Volume must be between 0.0 and 1.0")