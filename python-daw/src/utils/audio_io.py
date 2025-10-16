from pydub import AudioSegment
import os

def load_audio_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    return AudioSegment.from_file(file_path)

def save_audio_file(audio_segment, file_path):
    audio_segment.export(file_path, format="wav")  # You can change the format as needed.