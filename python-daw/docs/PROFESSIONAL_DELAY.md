# Professional Delay Effect - User Guide

## Overview

Il delay professionale è stato completamente riprogettato per offrire qualità da studio di registrazione. Non è più un semplice eco, ma un effetto completo con filtri, stereo e controllo preciso.

## Parametri

### 🎚️ **delay_time_ms** (1 - 2000 ms)
Il tempo di ritardo in millisecondi.

**Valori tipici:**
- **50-150ms**: Slapback delay (rockabilly, country)
- **200-350ms**: Delay ritmico standard (rock, pop)
- **400-600ms**: Delay lungo (atmosferico, ambient)
- **800-1500ms**: Delay molto lungo (effetti speciali)

**Tip**: 
- A 120 BPM, 500ms = 1/4 di nota
- A 120 BPM, 250ms = 1/8 di nota
- A 120 BPM, 125ms = 1/16 di nota

---

### 🔄 **feedback** (0.0 - 0.95)
Quantità di segnale ritardato che viene re-immesso nel delay.

**Valori tipici:**
- **0.2-0.4**: Poche ripetizioni (1-3 echi)
- **0.4-0.6**: Ripetizioni moderate (3-6 echi)
- **0.6-0.8**: Molte ripetizioni (trail lungo)
- **0.8-0.95**: Ripetizioni infinite (attenzione!)

⚠️ **Attenzione**: Valori sopra 0.8 possono creare feedback infinito!

---

### 💧 **mix** (0.0 - 1.0)
Bilanciamento tra segnale originale (dry) e ritardato (wet).

**Valori tipici:**
- **0.0**: Solo segnale originale (effect off)
- **0.2-0.4**: Delay sottile, naturale
- **0.5**: 50/50 (bilanciato)
- **0.6-0.8**: Delay prominente
- **1.0**: Solo delay (no dry signal)

**Tip**: Per la maggior parte delle applicazioni musicali, 0.3-0.5 è ideale.

---

### 🔇 **low_cut** (20 - 2000 Hz)
Filtro passa-alto applicato alle ripetizioni del delay.

**Perché è importante:**
- Rimuove frequenze basse rombanti dalle ripetizioni
- Previene accumulo di bassi nel mix
- Rende il delay più pulito e definito

**Valori tipici:**
- **200-300Hz**: Leggera pulizia (default professionale)
- **400-600Hz**: Suono più sottile, telefonico
- **800-1200Hz**: Effetto vintage, come tape delay vecchio

**Tip**: Per voci e chitarre, 300-400Hz è perfetto.

---

### 🌟 **high_cut** (1000 - 20000 Hz)
Filtro passa-basso applicato alle ripetizioni del delay.

**Perché è importante:**
- Crea un suono più caldo e vintage
- Riduce sibilanti fastidiose nelle ripetizioni
- Simula il comportamento dei delay analogici

**Valori tipici:**
- **8000-12000Hz**: Delay moderno e brillante
- **5000-7000Hz**: Delay caldo, vintage
- **3000-4000Hz**: Suono scuro, come tape delay
- **1500-2500Hz**: Effetto "telefono" o lo-fi

**Tip**: 
- Per voce: 6000Hz (caldo ma chiaro)
- Per chitarra: 5000Hz (vintage)
- Per effetti speciali: 3000Hz (scuro)

---

### 🎭 **ping_pong** (0.0 - 1.0)
Effetto stereo "rimbalzo" tra canale sinistro e destro.

**Come funziona:**
- **0.0**: Delay stereo normale
- **0.5**: Mezzo ping-pong (leggero rimbalzo)
- **1.0**: Ping-pong completo (alternanza L/R)

**Attenzione**: Funziona solo con audio stereo!

**Tip**: Fantastico su voci e synth per creare ampiezza stereo.

---

## 🎨 Preset Suggeriti

### 🎸 **Classic Rock Delay**
```python
delay.set_parameters({
    "delay_time_ms": 380.0,  # ~1/8 note @ 120 BPM
    "feedback": 0.45,
    "mix": 0.35,
    "low_cut": 250.0,
    "high_cut": 6000.0,
    "ping_pong": 0.0
})
```

### 🎤 **Vocal Slapback (Elvis Style)**
```python
delay.set_parameters({
    "delay_time_ms": 120.0,  # Veloce!
    "feedback": 0.2,         # Una sola ripetizione
    "mix": 0.4,
    "low_cut": 400.0,
    "high_cut": 8000.0,
    "ping_pong": 0.0
})
```

### 🌌 **Ambient Wash**
```python
delay.set_parameters({
    "delay_time_ms": 650.0,
    "feedback": 0.7,         # Tante ripetizioni
    "mix": 0.6,
    "low_cut": 500.0,        # Pulito
    "high_cut": 4000.0,      # Scuro e caldo
    "ping_pong": 0.8         # Stereo wide
})
```

### 📻 **Vintage Tape Echo**
```python
delay.set_parameters({
    "delay_time_ms": 450.0,
    "feedback": 0.55,
    "mix": 0.45,
    "low_cut": 300.0,
    "high_cut": 3500.0,      # Molto scuro = vintage!
    "ping_pong": 0.0
})
```

### 🎹 **Synth Rhythm**
```python
delay.set_parameters({
    "delay_time_ms": 250.0,  # 1/16 @ 120 BPM
    "feedback": 0.5,
    "mix": 0.5,
    "low_cut": 200.0,
    "high_cut": 10000.0,     # Brillante
    "ping_pong": 1.0         # Full ping-pong!
})
```

### ☎️ **Telephone/Lo-Fi Effect**
```python
delay.set_parameters({
    "delay_time_ms": 300.0,
    "feedback": 0.4,
    "mix": 0.5,
    "low_cut": 800.0,        # Taglia molto basso
    "high_cut": 2000.0,      # Taglia molto alto = telefono!
    "ping_pong": 0.0
})
```

---

## 💡 Suggerimenti per l'uso

### 1. **Sincronizza con il tempo della canzone**
Calcola il delay time in base al BPM:
- Delay (ms) = (60000 / BPM) / divisione
- Es: 120 BPM, 1/4 nota = 60000 / 120 / 1 = 500ms
- Es: 140 BPM, 1/8 nota = 60000 / 140 / 2 = 214ms

### 2. **Usa il feedback con moderazione**
- Più feedback = più ripetizioni = più "muddy" può diventare il mix
- Per mix puliti: feedback 0.3-0.5
- Per effetti creativi: feedback 0.6-0.8

### 3. **I filtri sono essenziali**
- **Sempre** usa low_cut per rimuovere il rumble
- Regola high_cut in base al mood:
  - Moderno/brillante = 7000-10000 Hz
  - Vintage/caldo = 4000-6000 Hz
  - Scuro/atmosferico = 2000-4000 Hz

### 4. **Mix conservativo**
- Nella maggior parte dei mix, il delay dovrebbe essere "sentito" ma non "invadente"
- Inizia con mix = 0.3 e aumenta lentamente
- Solo per effetti speciali usa mix > 0.6

### 5. **Ping-pong per width**
- Ottimo per voci principali (width senza muddy al centro)
- Fantastico su synth pad
- Evita su bassi e kick (mantienili mono!)

---

## 🔧 Differenze dal vecchio delay

### ❌ Vecchio Delay (Problematico)
- Timing impreciso (basato su lunghezza buffer)
- Nessun filtering
- Feedback scadente
- Suono "digitale" e poco musicale
- Solo mono

### ✅ Nuovo Delay (Professionale)
- Timing preciso in millisecondi
- Filtri passa-alto e passa-basso
- Feedback pulito e musicale
- Circular buffer (come hardware professionale)
- Supporto stereo e ping-pong
- Qualità studio

---

## 🎛️ Uso nell'interfaccia

1. Aggiungi il delay alla catena effetti della traccia
2. Apri il dialog dei parametri
3. Regola i parametri con gli slider:
   - **delay_time_ms**: 1-2000ms (regolazione precisa!)
   - **feedback**: 0-0.95 (attenzione sopra 0.8!)
   - **mix**: 0-1.0
   - **low_cut**: 20-2000Hz
   - **high_cut**: 1000-20000Hz
   - **ping_pong**: 0-1.0

**Tutti i parametri sono controllabili in tempo reale durante la riproduzione!**

---

## 🎓 Quando usare il Delay

### ✅ Perfetto per:
- Voce (slapback o rhythmic delay)
- Chitarra elettrica (classic rock delay)
- Synth lead (rhythmic o ambient)
- Snare drum (per energia)
- Effetti speciali e transizioni

### ⚠️ Usa con cautela su:
- Bassi (può fare "muddy" il mix)
- Kick drum (meglio riverbero corto)
- Mix già molto densi

---

## 🚀 Quick Start

```python
from effects.delay import Delay

# Crea delay
delay = Delay(sample_rate=44100)

# Preset per chitarra rock
delay.set_parameters({
    "delay_time_ms": 375.0,
    "feedback": 0.45,
    "mix": 0.35,
    "low_cut": 250.0,
    "high_cut": 6000.0,
    "ping_pong": 0.0
})

# Aggiungi alla traccia
track.add_effect(delay, name="Rock Delay", wet=0.35)
```

---

**Ora hai un delay professionale! 🎉**

Sperimenta con i preset e trova il tuo suono!
