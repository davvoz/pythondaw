# Guida: Aggiungere Nuovi Strumenti

## Sistema di Registry Centralizzato

Il DAW utilizza un sistema di **registry centralizzato** (`InstrumentRegistry`) per gestire tutti gli strumenti disponibili. Questo rende il sistema completamente scalabile e modulare.

## Come Aggiungere un Nuovo Strumento

### Passo 1: Creare la Classe dello Strumento

Crea un nuovo file nella cartella `src/instruments/`, ad esempio `sampler.py`:

```python
"""Sampler instrument."""

import math
from .base import BaseInstrument


class Sampler(BaseInstrument):
    """Sample-based instrument for playing audio samples."""
    
    def __init__(self):
        super().__init__()
        self.sample_data = []
        self.sample_rate = 44100
        self.volume = 1.0
        # ... altri parametri ...
    
    def set_sample(self, audio_data, sample_rate):
        """Load a sample into the sampler."""
        self.sample_data = audio_data
        self.sample_rate = sample_rate
    
    def render_notes(self, notes, start_sec, end_sec, sample_rate):
        """Render MIDI notes using the loaded sample."""
        # Implementa la logica di rendering
        pass
```

### Passo 2: Creare l'Editor UI

Crea la funzione editor in `src/ui/synth_editor.py` (o crea un nuovo file):

```python
def show_sampler_editor(root, sampler, track_name, on_apply=None):
    """Open sampler editor window.
    
    Args:
        root: Tkinter root window
        sampler: Sampler instance to edit
        track_name: Name of the track
        on_apply: Callback when parameters change
    """
    editor = tk.Toplevel(root)
    editor.title(f"🎼 Sampler Editor - {track_name}")
    editor.geometry("600x400")
    
    # ... crea i controlli UI per il sampler ...
    
    def update_param():
        # Aggiorna i parametri del sampler
        if on_apply:
            on_apply(sampler)
    
    # ... binding dei controlli ...
```

### Passo 3: Registrare lo Strumento

Modifica `src/instruments/registry.py`, nella funzione `register_builtin_instruments()`:

```python
def register_builtin_instruments():
    """Register all built-in instruments."""
    
    # Import instruments and editors
    from .synthesizer import Synthesizer
    from .advanced_synthesizer import AdvancedSynthesizer
    from .sampler import Sampler  # ← Nuovo import
    from ..ui.synth_editor import (
        show_synth_editor, 
        show_advanced_synth_editor,
        show_sampler_editor  # ← Nuovo import
    )
    
    # ... registrazioni esistenti ...
    
    # Register Sampler (NUOVO)
    InstrumentRegistry.register(
        instrument_id='sampler',  # ID univoco
        name='Sampler',  # Nome visualizzato
        description='Sample-based instrument for playing audio samples across the keyboard.',
        instrument_class=Sampler,  # Classe dello strumento
        editor_function=show_sampler_editor,  # Funzione editor
        icon='🎼',  # Emoji per la UI
        category='Sampler'  # Categoria
    )
```

### Passo 4: Esportare la Classe (opzionale)

Aggiorna `src/instruments/__init__.py`:

```python
from .base import BaseInstrument
from .synthesizer import Synthesizer
from .advanced_synthesizer import AdvancedSynthesizer
from .sampler import Sampler  # ← Nuovo
from .registry import InstrumentRegistry, register_builtin_instruments

__all__ = [
    'BaseInstrument', 
    'Synthesizer', 
    'AdvancedSynthesizer',
    'Sampler',  # ← Nuovo
    'InstrumentRegistry',
    'register_builtin_instruments'
]
```

## Fatto! 🎉

Il nuovo strumento apparirà automaticamente:
- ✅ Nel dialog di selezione strumenti
- ✅ Nel menu contestuale "Change Instrument"
- ✅ Nel sistema di salvataggio/caricamento progetti
- ✅ In tutti i flussi di gestione MIDI

## Vantaggi del Sistema Registry

1. **Nessuna Modifica al Core**: Non devi toccare `track_clip_manager.py`, `window.py`, ecc.
2. **Scalabilità**: Aggiungi quanti strumenti vuoi senza complicare il codice
3. **Manutenibilità**: Tutto centralizzato in un unico punto
4. **Type Safety**: Il registry valida le classi e mantiene i riferimenti corretti
5. **Automatico**: Il dialog e tutti i sistemi si aggiornano automaticamente

## Parametri di Registrazione

- **instrument_id**: ID univoco (es: `'sampler'`, `'drum_machine'`)
- **name**: Nome leggibile (es: `'Sampler'`, `'Drum Machine'`)
- **description**: Breve descrizione per il dialog di selezione
- **instrument_class**: Classe Python (deve ereditare da `BaseInstrument`)
- **editor_function**: Funzione che apre l'editor UI
- **icon**: Emoji per visualizzazione (es: `'🎼'`, `'🥁'`)
- **category**: Categoria per raggruppamento futuro (es: `'Synthesizer'`, `'Sampler'`, `'Drum'`)

## Struttura Consigliata

```
src/instruments/
├── __init__.py
├── base.py               # BaseInstrument (interfaccia)
├── registry.py           # InstrumentRegistry (sistema centrale)
├── synthesizer.py        # Basic Synthesizer
├── advanced_synthesizer.py  # Advanced Synthesizer
├── sampler.py            # ← Nuovo strumento
└── drum_machine.py       # ← Altro strumento futuro
```

## Debug

Il sistema stampa messaggi utili:
```
✓ Registered instrument: Basic Synthesizer (basic_synth)
✓ Registered instrument: Advanced Synthesizer (advanced_synth)
✓ Registered instrument: Sampler (sampler)
✓ Registered 3 instruments
```

Se qualcosa non funziona:
1. Verifica che la classe erediti da `BaseInstrument`
2. Controlla che `instrument_id` sia univoco
3. Assicurati che la funzione editor abbia la firma corretta
4. Controlla la console per errori di import
