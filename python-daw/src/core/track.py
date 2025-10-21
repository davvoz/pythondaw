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
        self.type = "audio"  # Track type: "audio" or "midi"
        self.instrument = None  # For MIDI tracks: Synthesizer instance
        # Per-track effects chain (optional)
        self.effects = None
        try:
            from ..effects.chain import EffectChain
            self.effects = EffectChain()
        except Exception:
            try:
                # Fallback for when run from examples/tests
                import sys
                from pathlib import Path
                src_path = Path(__file__).parent.parent
                if str(src_path) not in sys.path:
                    sys.path.insert(0, str(src_path))
                from effects.chain import EffectChain
                self.effects = EffectChain()
            except Exception:
                self.effects = None

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

    # --- Effects convenience methods (no-ops if chain not available) ---
    def add_effect(self, effect, name: str = None, wet: float = 1.0) -> int:
        if getattr(self, 'effects', None) is None:
            return -1
        return self.effects.add(effect, name=name, wet=wet)

    def remove_effect(self, index: int) -> None:
        if getattr(self, 'effects', None) is None:
            return
        self.effects.remove(index)

    def move_effect(self, old_index: int, new_index: int) -> None:
        if getattr(self, 'effects', None) is None:
            return
        self.effects.move(old_index, new_index)

    def clear_effects(self) -> None:
        if getattr(self, 'effects', None) is None:
            return
        self.effects.clear()