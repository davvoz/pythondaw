class AudioBuffer:
    def __init__(self):
        self.buffer = []

    def load_audio(self, audio_data):
        self.buffer.append(audio_data)

    def clear_buffer(self):
        self.buffer.clear()

    def get_buffer_data(self):
        return self.buffer.copy()