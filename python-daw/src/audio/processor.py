class AudioProcessor:
    def __init__(self):
        self.effects = []

    def apply_effects(self, audio_data):
        for effect in self.effects:
            audio_data = effect.apply(audio_data)
        return audio_data

    def set_effect_parameters(self, effect_name, parameters):
        for effect in self.effects:
            if effect.__class__.__name__.lower() == effect_name.lower():
                effect.set_parameters(parameters)
                break

    def add_effect(self, effect):
        self.effects.append(effect)

    def remove_effect(self, effect):
        self.effects.remove(effect)