# Copilot instructions for this repository

This repo is a Python-based Digital Audio Workstation (DAW) scaffold. Audio is represented as simple mono lists of floats in [-1, 1] with lightweight components wired by a timeline. Realtime playback is optional and gracefully degrades if native deps are missing.

## Architecture at a glance
- Core timeline flow
  - `src/core/timeline.py` holds placements `(track_index, clip)` and exposes `get_clips_for_range(start, end)` used by both offline and realtime engines.
  - `src/audio/clip.py::AudioClip` stores mono samples, time placement (`start_time`, `end_time`), and `slice_samples(start_sec, end_sec)`.
  - `src/audio/engine.py::AudioEngine.render_window(timeline, start, duration, sample_rate)` does offline mixdown: sums overlapping clips and clamps to [-1, 1].
  - `src/audio/player.py::TimelinePlayer` does realtime playback via `sounddevice`. It pulls ranges from the timeline in a callback, mixes, clips, and advances current time.
- Mixing & tracks
  - `src/audio/mixer.py::Mixer` is a simple scalar mixer for tests. `add_track(name, volume)` and `mix_tracks()` returns the clamped sum of track volumes (master volume is stored but ignored in tests).
  - `src/core/track.py::Track` manages `audio_files` and a clamped `volume`.
- Effects
  - All effects subclass `src/effects/base.py::BaseEffect` with `parameters: dict`, `set_parameters(dict)`, and `apply(audio_data: list[float]) -> list[float]`.
  - Example implementations: `Reverb`, `Delay`, `Compressor`, `Equalizer` operate on Python lists (not numpy) and keep behavior deterministic for unit tests.
- UI & main
  - `src/main.py` wires a demo project, mixer, effects chain, offline render via `AudioEngine`, and optional realtime `TimelinePlayer`. UI classes in `src/ui/*` are placeholders.

## Key seams and contracts (don’t break)
- Timeline contract: `Timeline.get_clips_for_range(start, end)` yields `(track_index, clip)` where clip has `.start_time`, `.end_time`, and `.slice_samples(start, end)`.
- Signal representation: use plain Python lists of float for processing in `effects/*` and engine code. Only `TimelinePlayer` uses numpy internally if available.
- Levels/clipping: summing then clamp to [-1, 1] in mixing/render paths.
- Mixer tests rely on: `0.7 + 0.3 -> 1.0` regardless of `master_volume`.

## Conventions & patterns
- Effects pattern:
  - Initialize defaults in `__init__` by setting `self.parameters`.
  - `set_parameters` merges dict values; validate types minimally.
  - `apply` returns a new list or a transformed copy; avoid in-place mutation of the input list.
- Time units are seconds; sample_rate defaults to 44100 in examples.
- Be tolerant of missing native deps: if `numpy` or `sounddevice` are missing, `TimelinePlayer.start()` prints a message and no-ops.

## Developer workflow
- Setup
  - Install deps: `pip install -r requirements.txt`
  - Windows note: `sounddevice` requires PortAudio; if installation fails, realtime playback will be disabled but tests still pass.
- Run app
  - `python src/main.py`
- Run tests (unittest discovery from repo root; tests import `src.*`):
  - `python -m unittest discover -s tests -p "test_*.py" -v`

## Examples
- Add a clip to the timeline:
  - Create `AudioClip(name, buffer: list[float], sample_rate, start_time)` and `timeline.add_clip(track_index, clip)`; see `src/main.py` for a sine-buffer demo.
- Implement a new effect:
  - Subclass `BaseEffect`; define defaults and override `apply(list[float])`. Keep list-based processing and deterministic behavior like in `effects/reverb.py`.

## File map (start here)
- Offline engine: `src/audio/engine.py`
- Realtime player: `src/audio/player.py`
- Timeline & clips: `src/core/timeline.py`, `src/audio/clip.py`
- Mixer & tracks: `src/audio/mixer.py`, `src/core/track.py`
- Effects: `src/effects/*`
- Tests: `tests/test_mixer.py`, `tests/test_track.py`, `tests/test_effects.py`

## Guidance for AI edits
- Preserve the timeline and clip contracts; new features should compose via these seams.
- Keep effects list-based to match tests; don’t introduce numpy types in effect APIs.
- When changing `Mixer`, ensure tests expectations continue to hold.
- Favor small, pure functions and explicit parameters; add unit tests alongside changes in `tests/` following current patterns.