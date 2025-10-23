"""Centralized instrument registry for the DAW.

This module provides a scalable system for registering and managing instruments.
All instruments should be registered here to be available throughout the application.
"""

from typing import Dict, List, Type, Optional
from .base import BaseInstrument


class InstrumentRegistry:
    """Central registry for all available instruments."""
    
    _instruments: Dict[str, Dict] = {}
    _editors: Dict[str, callable] = {}
    
    @classmethod
    def register(cls, 
                 instrument_id: str,
                 name: str,
                 description: str,
                 instrument_class: Type[BaseInstrument],
                 editor_function: callable,
                 icon: str = "🎵",
                 category: str = "Synthesizer"):
        """Register an instrument in the registry.
        
        Args:
            instrument_id: Unique identifier for the instrument (e.g., 'basic_synth')
            name: Display name (e.g., 'Basic Synthesizer')
            description: Short description of the instrument
            instrument_class: The instrument class (must inherit from BaseInstrument)
            editor_function: Function to open the editor (callable that takes root, instrument, name, on_apply)
            icon: Emoji icon for UI display
            category: Category for grouping instruments
        """
        cls._instruments[instrument_id] = {
            'id': instrument_id,
            'name': name,
            'description': description,
            'class': instrument_class,
            'class_name': instrument_class.__name__,
            'icon': icon,
            'category': category
        }
        cls._editors[instrument_class.__name__] = editor_function
        print(f"✓ Registered instrument: {name} ({instrument_id})")
    
    @classmethod
    def get_all_instruments(cls) -> List[Dict]:
        """Get list of all registered instruments.
        
        Returns:
            List of instrument dictionaries with metadata
        """
        return list(cls._instruments.values())
    
    @classmethod
    def get_instrument_info(cls, instrument_id: str) -> Optional[Dict]:
        """Get information about a specific instrument.
        
        Args:
            instrument_id: The instrument ID to look up
            
        Returns:
            Dictionary with instrument info or None if not found
        """
        return cls._instruments.get(instrument_id)
    
    @classmethod
    def create_instrument(cls, instrument_id: str) -> Optional[BaseInstrument]:
        """Create an instance of an instrument by ID.
        
        Args:
            instrument_id: The instrument ID to instantiate
            
        Returns:
            New instrument instance or None if not found
        """
        info = cls._instruments.get(instrument_id)
        if info:
            try:
                instance = info['class']()
                print(f"DEBUG Registry: Created {instance.__class__.__name__} from ID '{instrument_id}'")
                return instance
            except Exception as e:
                print(f"Error creating instrument {instrument_id}: {e}")
                return None
        else:
            print(f"ERROR: Instrument ID '{instrument_id}' not found in registry!")
            print(f"Available IDs: {list(cls._instruments.keys())}")
        return None
    
    @classmethod
    def get_instrument_id(cls, instrument: BaseInstrument) -> Optional[str]:
        """Get the instrument ID from an instrument instance.
        
        Args:
            instrument: The instrument instance
            
        Returns:
            The instrument ID or None if not found
        """
        class_name = instrument.__class__.__name__
        for inst_id, info in cls._instruments.items():
            if info['class_name'] == class_name:
                return inst_id
        return None
    
    @classmethod
    def open_editor(cls, root, instrument: BaseInstrument, track_name: str, on_apply: callable = None):
        """Open the appropriate editor for an instrument.
        
        Args:
            root: Tkinter root window
            instrument: The instrument instance to edit
            track_name: Name of the track (for display)
            on_apply: Callback when parameters change
        """
        class_name = instrument.__class__.__name__
        editor_func = cls._editors.get(class_name)
        
        print(f"DEBUG Registry: Looking for editor for class '{class_name}'")
        print(f"DEBUG Registry: Registered editors: {list(cls._editors.keys())}")
        
        if editor_func:
            print(f"DEBUG Registry: Opening editor for {class_name}")
            editor_func(root, instrument, track_name, on_apply=on_apply)
        else:
            print(f"⚠ No editor registered for {class_name}")
    
    @classmethod
    def is_registered(cls, instrument_id: str) -> bool:
        """Check if an instrument is registered.
        
        Args:
            instrument_id: The instrument ID to check
            
        Returns:
            True if registered, False otherwise
        """
        return instrument_id in cls._instruments
    
    @classmethod
    def get_categories(cls) -> List[str]:
        """Get list of all instrument categories.
        
        Returns:
            List of unique category names
        """
        categories = set(info['category'] for info in cls._instruments.values())
        return sorted(categories)


def register_builtin_instruments():
    """Register all built-in instruments.
    
    This function should be called at application startup to register
    all available instruments in the system.
    """
    # Import instruments and editors
    from .synthesizer import Synthesizer
    from .advanced_synthesizer import AdvancedSynthesizer
    from ..ui.synth_editor import show_synth_editor, show_advanced_synth_editor
    
    # Register Basic Synthesizer
    InstrumentRegistry.register(
        instrument_id='basic_synth',
        name='Basic Synthesizer',
        description='Simple synthesizer with basic waveforms and ADSR envelope. Perfect for learning and quick sketches.',
        instrument_class=Synthesizer,
        editor_function=show_synth_editor,
        icon='🎹',
        category='Synthesizer'
    )
    
    # Register Advanced Synthesizer
    InstrumentRegistry.register(
        instrument_id='advanced_synth',
        name='Advanced Synthesizer',
        description='Professional synthesizer with dual oscillators, filters, LFO, unison, glide and more. Full-featured for production work.',
        instrument_class=AdvancedSynthesizer,
        editor_function=show_advanced_synth_editor,
        icon='🎛️',
        category='Synthesizer'
    )
    
    # Future instruments will be registered here:
    # InstrumentRegistry.register(
    #     instrument_id='sampler',
    #     name='Sampler',
    #     description='Sample-based instrument...',
    #     instrument_class=Sampler,
    #     editor_function=show_sampler_editor,
    #     icon='🎼',
    #     category='Sampler'
    # )
    
    print(f"✓ Registered {len(InstrumentRegistry.get_all_instruments())} instruments")
