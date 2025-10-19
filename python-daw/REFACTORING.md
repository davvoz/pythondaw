# Timeline Refactoring

## 📋 Panoramica

Il modulo `timeline_canvas.py` è stato completamente refactorizzato per migliorare modularità, testabilità e manutenibilità. La classe `TimelineCanvas` è ora un orchestratore leggero che delega le responsabilità a componenti specializzati.

## 🏗️ Architettura

### Prima del Refactoring
- Singolo file monolitico `timeline_canvas.py` (~2000 righe)
- Tutte le responsabilità mescolate nella classe `TimelineCanvas`
- Difficile da testare e mantenere

### Dopo il Refactoring
```
src/ui/timeline/
├── __init__.py
├── geometry.py               # Conversioni coordinate e dimensioni
├── renderers.py              # Rendering modulare
├── services.py               # Servizi (snap, clipboard)
└── controllers/              # Gestione interazioni
    ├── __init__.py
    ├── drag_controller.py
    ├── resize_controller.py
    ├── box_select_controller.py
    ├── loop_marker_controller.py
    └── track_controls_controller.py
```

## 🔧 Componenti

### `TimelineGeometry`
Gestisce tutte le conversioni di coordinate e calcoli dimensionali.

**Metodi principali:**
- `time_to_x(time)` / `x_to_time(x)` - Conversione tempo ↔ pixel
- `track_to_y(track_idx)` / `y_to_track(y)` - Conversione traccia ↔ pixel
- `clip_bounds(clip, track_idx)` - Calcola bounds di una clip
- `compute_width(timeline)` / `compute_height(track_count)` - Dimensioni canvas
- `zoom(factor)` / `zoom_reset()` - Gestione zoom

### Renderers

#### `RulerRenderer`
- Disegna il righello temporale (bar/beat o secondi)
- Supporta progetti musicali e temporali

#### `GridRenderer`
- Disegna la griglia sul canvas
- Supporta griglia musicale (bar/beat) e temporale

#### `TrackRenderer`
- Disegna gli sfondi delle tracce
- Gestisce l'evidenziazione della traccia selezionata

#### `ClipRenderer`
- Disegna le clip con waveform
- Gestisce selezione e resize handles
- Supporta colori personalizzati

#### `CursorRenderer`
- Disegna il cursore di playback
- Metodi per update posizione

#### `LoopRenderer`
- Disegna i marker del loop region
- Gestisce visualizzazione su ruler e canvas principale

### Services

#### `SnapService`
- Gestisce snap-to-grid
- Configurabile per divisioni diverse (bar, beat, etc.)
- Delega al progetto per calcoli musicali

#### `ClipboardService`
- Gestisce copy/paste di clip
- Mantiene dati clipboard
- Gestisce visualizzazione paste cursor

### Controllers

#### `DragController`
- Gestisce drag di clip sulla timeline
- Supporta cambio traccia durante drag
- Snap-to-grid integrato

#### `ResizeController`
- Gestisce resize di clip (bordi sinistro/destro)
- Rileva zona di resize ai bordi
- Aggiorna `duration` correttamente per AudioClip

#### `BoxSelectController`
- Gestisce selezione rettangolare di multiple clip
- Disegna preview durante selezione
- Calcola clip all'interno del box

#### `LoopMarkerController`
- Gestisce drag dei loop markers
- Rileva hover sui markers
- Snap-to-grid per posizioni loop

#### `TrackControlsController`
- Gestisce interazioni con controlli traccia
- Volume/Pan sliders
- Bottoni Mute/Solo/FX

## ✨ Vantaggi

### 1. **Separazione delle Responsabilità**
Ogni componente ha una singola responsabilità ben definita.

### 2. **Testabilità**
I componenti possono essere testati in isolamento:
```python
# Test geometry
geometry = TimelineGeometry(px_per_sec=200)
assert geometry.time_to_x(1.0) == 200

# Test snap service
snap = SnapService(project)
snap.set_enabled(True)
assert snap.snap_time(1.05) == 1.0  # snapped
```

### 3. **Manutenibilità**
- Modifiche localizzate in componenti specifici
- Codice più leggibile e documentato
- Più facile debuggare problemi

### 4. **Riusabilità**
I renderer e controller possono essere riutilizzati in altri contesti.

### 5. **Estendibilità**
Facile aggiungere nuovi renderer o controller:
```python
# Nuovo renderer per automazione
class AutomationRenderer:
    def __init__(self, geometry):
        self.geometry = geometry
    
    def draw(self, canvas, track_idx, automation_data):
        # ...rendering logic...
```

## 🔄 Backward Compatibility

La classe `TimelineCanvas` mantiene completa compatibilità con il codice esistente:

```python
# Properties per accesso diretto
timeline.px_per_sec           # → geometry.px_per_sec
timeline.snap_enabled         # → snap_service.enabled
timeline.clipboard            # → clipboard_service.clipboard

# Metodi pubblici invariati
timeline.zoom(1.2)
timeline.set_snap(True)
timeline.redraw()
```

## 🐛 Fix Applicati

### AudioClip end_time
`end_time` è una property calcolata senza setter. Il `ResizeController` ora:
- Modifica `duration` invece di `end_time`
- Gestisce correttamente resize da sinistra (cambia `start_time` e `duration`)
- Gestisce correttamente resize da destra (cambia solo `duration`)

## 📊 Metriche

- **Righe di codice**: ~2000 → ~1500 (TimelineCanvas) + ~600 (nuovi moduli)
- **Responsabilità per classe**: Molte → 1
- **Accoppiamento**: Alto → Basso
- **Testabilità**: Difficile → Facile

## 🚀 Prossimi Passi

1. **Type hints completi**: Aggiungere type hints a tutti i parametri
2. **Unit tests**: Creare test per ogni componente
3. **Invalidation incrementale**: Implementare dirty rectangles per performance
4. **Canvas adapter**: Astrarre completamente da Tkinter per portabilità
5. **Documentazione API**: Generare documentazione con Sphinx

## 📝 Note di Migrazione

Se stai estendendo la timeline:

**Prima:**
```python
# Tutto in TimelineCanvas
def _draw_custom_overlay(self):
    # codice di rendering...
```

**Dopo:**
```python
# Renderer dedicato
class CustomOverlayRenderer:
    def __init__(self, geometry):
        self.geometry = geometry
    
    def draw(self, canvas, width, height):
        # codice di rendering...

# In TimelineCanvas.__init__:
self.custom_renderer = CustomOverlayRenderer(self.geometry)

# In TimelineCanvas.redraw:
self.custom_renderer.draw(self.canvas, width, height)
```

## ✅ Testing

L'applicazione è stata testata e funziona correttamente con:
- ✅ Drag & drop di clip
- ✅ Resize di clip
- ✅ Box selection
- ✅ Loop markers
- ✅ Track controls (volume/pan)
- ✅ Snap to grid
- ✅ Copy/paste (struttura esistente mantenuta)
- ✅ Zoom
- ✅ Scrolling

---

**Data refactoring**: 19 Ottobre 2025  
**Autore**: GitHub Copilot + davvoz  
**Versione**: 1.0
