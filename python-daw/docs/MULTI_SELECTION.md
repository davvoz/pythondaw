# Multi-Selection and Copy/Paste Features

## Panoramica

Sono state implementate funzionalità avanzate di selezione multipla e copia/incolla per le clip audio nel DAW.

## Funzionalità Implementate

### 1. Selezione Multipla di Clip

**Come usare:**
- **Clic singolo**: Seleziona una clip (deseleziona le altre)
- **Ctrl + Clic**: Aggiunge/rimuove clip dalla selezione
- Le clip selezionate vengono evidenziate con un bordo bianco spesso

**Implementazione:**
- `TimelineCanvas.selected_clips`: Lista di tuple `[(track_idx, clip), ...]`
- `TimelineCanvas.toggle_clip_selection()`: Aggiunge o rimuove clip dalla selezione
- `TimelineCanvas.clear_selection()`: Cancella tutte le selezioni

### 2. Copia e Incolla Clip

**Scorciatoie da tastiera:**
- **Ctrl+C**: Copia le clip selezionate negli appunti
- **Ctrl+V**: Incolla le clip dalla clipboard

**Come scegliere dove incollare:**
1. **Click sulla timeline**: Clicca in un punto vuoto della timeline per impostare la posizione di paste
   - Un cursore verde tratteggiato appare per indicare dove verrà incollato
   - Il tempo viene mostrato vicino al cursore
2. **Right-click sulla timeline**: Click destro su un'area vuota mostra un menu con "Paste here"
3. **Ctrl+V**: Incolla alla posizione del cursore verde (o al tempo di playback corrente se non impostato)

**Funzionalità:**
- Preserva tutte le proprietà delle clip (fade, pitch, volume, trim, ecc.)
- Mantiene la disposizione relativa delle clip
- Le clip incollate vengono automaticamente selezionate
- Le clip incollate hanno " (paste)" aggiunto al nome
- **Cursore di paste visibile**: Indica visivamente dove verranno incollate le clip
- **Snap to grid**: La posizione di paste si adatta automaticamente alla griglia se attiva

**Workflow tipico:**
1. Seleziona una o più clip (Ctrl+Click per multi-selezione)
2. Premi Ctrl+C per copiare
3. Un cursore verde appare al tempo corrente
4. Clicca sulla timeline dove vuoi incollare (opzionale)
5. Premi Ctrl+V per incollare

**Implementazione:**
- `TimelineCanvas.clipboard`: Lista di dati delle clip copiate
- `TimelineCanvas.paste_position`: Tempo dove verranno incollate le clip
- `TimelineCanvas.paste_cursor_visible`: Mostra/nasconde il cursore di paste
- `TimelineCanvas.copy_selected_clips()`: Copia clip negli appunti
- `TimelineCanvas.paste_clips(at_time)`: Incolla clip ad un tempo specifico

### 3. Copia e Incolla Loop

**Scorciatoie da tastiera:**
- **Ctrl+Shift+C**: Copia tutte le clip nella regione di loop
- **Ctrl+Shift+V**: Incolla le clip alla fine della regione di loop
- **Ctrl+D**: Duplica la regione di loop (funzionalità esistente)

**Funzionalità:**
- Copia automaticamente tutte le clip all'interno della regione di loop
- Incolla mantenendo la disposizione relativa
- Se non c'è un loop attivo, incolla al tempo corrente

**Implementazione:**
- `MainWindow._copy_loop()`: Seleziona e copia clip nel loop
- `MainWindow._paste_loop()`: Incolla alla fine del loop

### 4. Menu Contestuale Migliorato

**Click destro su clip:**
- Mostra opzioni per:
  - 📋 Copia (singola o multipla)
  - 📌 Incolla
  - ✂ Elimina (singola o multipla)
  - 📋 Duplica (solo selezione singola)
  - ⚙ Proprietà (solo selezione singola)

**Click destro su timeline vuota:**
- 📍 Mostra la posizione corrente del cursore
- 📌 Opzione "Paste N clip(s) here" per incollare direttamente
- Imposta automaticamente la posizione di paste al punto cliccato

**Selezione multipla nel menu:**
- Se sono selezionate più clip, il menu mostra "N clips" invece del nome
- Le operazioni vengono applicate a tutte le clip selezionate

### 5. Eliminazione Clip

**Scorciatoie:**
- **Delete**: Elimina tutte le clip selezionate
- **Menu contestuale**: Elimina clip selezionate

## Struttura del Codice

### File Modificati

1. **src/ui/timeline_canvas.py**
   - Aggiunto `selected_clips` per multi-selezione
   - Aggiunto `clipboard` per copia/incolla
   - Metodi: `toggle_clip_selection()`, `clear_selection()`, `copy_selected_clips()`, `paste_clips()`
   - Gestione Ctrl+Click per multi-selezione

2. **src/ui/window.py**
   - Aggiunte scorciatoie: Ctrl+C, Ctrl+V, Ctrl+Shift+C, Ctrl+Shift+V, Delete
   - Metodi: `_copy_selection()`, `_paste_clips()`, `_copy_loop()`, `_paste_loop()`, `_delete_selected_clips()`
   - Aggiornato menu contestuale per supportare multi-selezione

3. **src/ui/context_menus.py**
   - Aggiunto supporto per callback `on_copy` e `on_paste`
   - Parametro `multi_selection` per adattare le etichette del menu
   - Menu adattivo basato sul numero di clip selezionate

### Test

**tests/test_multi_selection.py**
- Test per selezione multipla
- Test per copia/incolla singola clip
- Test per copia/incolla multiple clip
- Test preservazione proprietà
- Test clear selection
- Test clipboard vuota
- Test copia senza selezione

## Esempi d'Uso

### Esempio 1: Selezione Multipla e Copia con Posizionamento Preciso

```python
# In un'applicazione GUI:
# 1. Ctrl+Clic su più clip per selezionarle
# 2. Ctrl+C per copiare (appare cursore verde al tempo corrente)
# 3. Cliccare sulla timeline dove si vuole incollare
#    - Il cursore verde si sposta alla posizione cliccata
# 4. Ctrl+V per incollare
# oppure
# 3. Click destro sulla timeline nel punto desiderato
# 4. Selezionare "Paste N clip(s) here" dal menu
```

### Esempio 2: Copia Loop

```python
# 1. Shift+Drag sulla timeline per creare un loop
# 2. Ctrl+Shift+C per copiare tutte le clip nel loop
# 3. Ctrl+Shift+V per incollare alla fine del loop
# o
# 3. Ctrl+V per incollare al tempo corrente
```

### Esempio 3: Programmatico

```python
from src.ui.timeline_canvas import TimelineCanvas

# Selezione multipla
canvas.toggle_clip_selection(0, clip1)
canvas.toggle_clip_selection(0, clip2)
canvas.toggle_clip_selection(1, clip3)

# Copia
canvas.copy_selected_clips()

# Incolla ad un tempo specifico
pasted_clips = canvas.paste_clips(at_time=10.0)

# Cancella selezione
canvas.clear_selection()
```

## Compatibilità

- Mantiene la compatibilità con la selezione singola esistente
- `selected_clip` viene mantenuto per backward compatibility
- Tutti i test esistenti continuano a funzionare

## Note Tecniche

### Cursore di Paste Position

Il sistema implementa un cursore visivo verde che indica dove verranno incollate le clip:
- **Automatico**: Appare quando si copia, posizionato al tempo corrente
- **Click sulla timeline**: Si sposta dove si clicca (solo se clipboard non è vuoto)
- **Right-click**: Menu contestuale con "Paste here" imposta e incolla in un'unica operazione
- **Visuale**: Linea verde tratteggiata con triangolo e etichetta del tempo
- **Snap to grid**: Si allinea automaticamente alla griglia se attiva

### Gestione della Posizione di Paste

Priorità nella scelta della posizione:
1. `at_time` parametro esplicito (se fornito)
2. `paste_position` se cursore visibile
3. Tempo di playback corrente (fallback)

```python
# Impostare manualmente la posizione
canvas.paste_position = 5.0
canvas.paste_cursor_visible = True
canvas.redraw()

# Incollare alla posizione impostata
canvas.paste_clips()  # userà paste_position

# Incollare ad un tempo specifico (override)
canvas.paste_clips(at_time=10.0)  # ignora paste_position
```

### Preservazione Proprietà

Quando si copiano le clip, vengono preservate tutte le proprietà:
- Buffer audio e sample rate
- Trim (start_offset, end_offset)
- Fade (fade_in, fade_out, fade_in_shape, fade_out_shape)
- Pitch (pitch_semitones)
- Volume
- Color
- File path
- Duration

### Gestione del Tempo

Il tempo di incollamento mantiene la disposizione relativa delle clip:
```
Original:  [clip1@1.0] [clip2@2.5] [clip3@1.5]
Paste@10:  [clip1@10.0] [clip2@11.5] [clip3@10.5]
           ^offset = 10.0 - 1.0 (min_start)
```

## Testing

Eseguire i test:

```bash
# Test specifici per multi-selezione
python -m pytest tests/test_multi_selection.py -v

# Tutti i test
python -m pytest tests/ -v
```

## Future Enhancement Ideas

- [ ] Box selection (drag to select area)
- [ ] Select all in track (Ctrl+A)
- [ ] Ripple edit (shift clips when editing)
- [ ] Smart snap during paste
- [ ] Undo/Redo per copy/paste
- [ ] Drag & drop multi-selection
- [ ] Copy con offset temporale specifico
