class BaseEffect:
    """Base effect with dict-based parameters and a simple interface.

    Tests call set_parameters with a dict. Subclasses should read/write from
    self.parameters.
    """

    def __init__(self):
        self.parameters = {}

    def apply(self, audio_data):
        raise NotImplementedError("Subclasses should implement this method.")

    def set_parameters(self, params: dict):
        if not isinstance(params, dict):
            raise TypeError("set_parameters expects a dict")
        self.parameters.update(params)