# src/instruments/__init__.py

from .base import BaseInstrument
from .synthesizer import Synthesizer
from .advanced_synthesizer import AdvancedSynthesizer
from .registry import InstrumentRegistry, register_builtin_instruments

__all__ = [
    'BaseInstrument', 
    'Synthesizer', 
    'AdvancedSynthesizer',
    'InstrumentRegistry',
    'register_builtin_instruments'
]