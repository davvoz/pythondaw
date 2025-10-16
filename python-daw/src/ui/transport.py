class Transport:
    def __init__(self):
        self.is_playing = False
        self.is_recording = False

    def play(self):
        if not self.is_playing:
            self.is_playing = True
            print("Playback started.")

    def stop(self):
        if self.is_playing:
            self.is_playing = False
            print("Playback stopped.")

    def record(self):
        if not self.is_recording:
            self.is_recording = True
            print("Recording started.")

    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            print("Recording stopped.")