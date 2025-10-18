from src.core.project import Project
from src.core.track import Track
from src.core.timeline import Timeline
from src.audio.mixer import Mixer
from src.audio.engine import AudioEngine
from src.audio.clip import AudioClip
from src.audio.player import TimelinePlayer
from src.effects.reverb import Reverb
from src.effects.delay import Delay
from src.effects.compressor import Compressor
from src.effects.equalizer import Equalizer
from src.ui.window import MainWindow
from src.ui.transport import Transport


def main():
    # Initialize the project
    project = Project("Demo Project")

    # Demo: add a couple of tracks (empty for now, clips will be added via UI)
    track1 = Track(name="Track 1")
    track1.set_volume(0.7)
    project.create_track(track1)

    track2 = Track(name="Track 2")
    track2.set_volume(0.3)
    project.create_track(track2)

    # Demo: mix simple scalar levels
    mixer = Mixer()
    mixer.set_master_volume(0.5)
    mixer.add_track("Track 1", 0.7)
    mixer.add_track("Track 2", 0.3)
    mixed_level = mixer.mix_tracks()

    print(f"Mixed scalar level (expected 1.0): {mixed_level}")

    # Demo: process a dummy signal with effects
    signal = [0.5] * 10

    reverb = Reverb()
    reverb.set_parameters({"room_size": 0.5, "damping": 0.5})
    delayed = Delay()
    delayed.set_parameters({"delay_time": 0.3, "feedback": 0.7})
    comp = Compressor()
    comp.set_parameters({"threshold": -10, "ratio": 4})
    eq = Equalizer()
    eq.set_parameters({"frequency": 1000, "gain": 3})

    # Process chain: reverb -> delay -> compressor -> equalizer
    processed = reverb.apply(signal)
    processed = delayed.apply(processed)
    processed = comp.apply(processed)
    processed = eq.apply(processed)
    print(f"Processed signal length: {len(processed)}")

    # --- Timeline & AudioClip demo (offline scheduling) ---
    timeline = Timeline()

    # helper: dummy sine wave buffer
    import math
    sr = 44100
    def sine(freq: float, seconds: float):
        n = int(sr * seconds)
        return [math.sin(2 * math.pi * freq * (i / sr)) * 0.2 for i in range(n)]

    clip1 = AudioClip("sine440", sine(440, 1.0), sr, start_time=0.0)
    clip2 = AudioClip("sine660", sine(660, 1.0), sr, start_time=0.5)
    timeline.add_clip(0, clip1)
    timeline.add_clip(0, clip2)

    engine = AudioEngine()
    engine.initialize()
    window = engine.render_window(timeline, start_time=0.0, duration=1.5, sample_rate=sr)
    print(f"Rendered offline window samples: {len(window)}")

    # Real-time player (graceful fallback if sounddevice/numpy are missing)
    player = TimelinePlayer(timeline, sample_rate=sr, mixer=mixer, project=project)

    # Set up the main user interface
    transport = Transport()
    main_window = MainWindow(project, mixer=mixer, transport=transport, timeline=timeline, player=player)

    # Map UI transport to player in a simple way (monkey patch)
    def on_play():
        try:
            player.start(start_time=0.0)
        except Exception as e:
            print(f"Realtime play error: {e}")
    def on_stop():
        try:
            player.stop()
        except Exception as e:
            print(f"Realtime stop error: {e}")
    # Attempt to assign callbacks if attributes exist
    if hasattr(main_window, "_on_play") and hasattr(main_window, "_on_stop"):
        # Wrap the existing handlers by extending behavior
        orig_play = main_window._on_play
        orig_stop = main_window._on_stop
        def _wrapped_play():
            orig_play()
            on_play()
        def _wrapped_stop():
            orig_stop()
            on_stop()
        main_window._on_play = _wrapped_play
        main_window._on_stop = _wrapped_stop
    main_window.show()

    # Start the application loop (placeholder)
    main_window.run()

if __name__ == "__main__":
    main()