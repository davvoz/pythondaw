"""Synthesizer Editor dialog for MIDI tracks."""

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover
    tk = None
    ttk = None

from typing import Optional, Callable, Dict, Any


def show_synth_editor(parent, synthesizer, track_name: str = "Synth", on_apply: Optional[Callable] = None):
    """Open synthesizer editor for a Synthesizer instance.
    
    Parameters:
        parent: Tk parent window
        synthesizer: Synthesizer instance to edit (in-place)
        track_name: Name of the track (for window title)
        on_apply: optional callback invoked when properties change
    """
    if tk is None or ttk is None or parent is None or synthesizer is None:
        return
    
    win = tk.Toplevel(parent)
    win.title(f"Synthesizer - {track_name}")
    win.resizable(False, False)
    win.configure(bg="#1e1e1e")
    win.geometry("500x600")
    
    # Main container
    frm = ttk.Frame(win, padding=24)
    frm.pack(fill="both", expand=True)
    frm.columnconfigure(1, weight=1)
    
    def on_change(*args):
        """Called whenever any parameter changes."""
        try:
            # Update synthesizer properties
            synthesizer.oscillator_type = osc_var.get()
            synthesizer.volume = volume_var.get()
            synthesizer.attack = attack_var.get()
            synthesizer.decay = decay_var.get()
            synthesizer.sustain = sustain_var.get()
            synthesizer.release = release_var.get()
            
            # Update display labels
            volume_label.config(text=f"{volume_var.get():.2f}")
            attack_label.config(text=f"{attack_var.get():.3f} s")
            decay_label.config(text=f"{decay_var.get():.3f} s")
            sustain_label.config(text=f"{sustain_var.get():.2f}")
            release_label.config(text=f"{release_var.get():.3f} s")
            
            # Trigger callback
            if callable(on_apply):
                on_apply(synthesizer)
        except Exception as ex:
            print(f"Synth Editor: error updating: {ex}")
    
    # Title
    title_label = ttk.Label(
        frm,
        text="🎹 Synthesizer Settings",
        font=("Segoe UI", 14, "bold"),
        foreground="#3b82f6"
    )
    title_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 16))
    
    row = 1
    
    # OSCILLATOR TYPE
    ttk.Label(frm, text="Oscillator", font=("Segoe UI", 10, "bold")).grid(
        row=row, column=0, sticky="w", padx=(0, 12), pady=(0, 8)
    )
    row += 1
    
    osc_var = tk.StringVar(value=getattr(synthesizer, 'oscillator_type', 'sine'))
    osc_var.trace_add('write', on_change)
    
    osc_frame = ttk.Frame(frm)
    osc_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 16))
    
    oscillators = [
        ("Sine", "sine"),
        ("Square", "square"),
        ("Sawtooth", "saw"),
        ("Triangle", "triangle")
    ]
    
    for i, (label, value) in enumerate(oscillators):
        btn = ttk.Radiobutton(
            osc_frame,
            text=label,
            value=value,
            variable=osc_var
        )
        btn.pack(side="left", padx=8)
    
    row += 1
    
    # VOLUME
    ttk.Separator(frm, orient="horizontal").grid(
        row=row, column=0, columnspan=2, sticky="ew", pady=(4, 12)
    )
    row += 1
    
    ttk.Label(frm, text="Volume", font=("Segoe UI", 10, "bold")).grid(
        row=row, column=0, sticky="w", padx=(0, 12), pady=(0, 4)
    )
    volume_label = ttk.Label(frm, text="1.00", foreground="#3b82f6")
    volume_label.grid(row=row, column=1, sticky="e", pady=(0, 4))
    row += 1
    
    volume_var = tk.DoubleVar(value=getattr(synthesizer, 'volume', 1.0))
    volume_var.trace_add('write', on_change)
    
    volume_slider = ttk.Scale(
        frm, from_=0.0, to=2.0, orient="horizontal",
        variable=volume_var, length=400
    )
    volume_slider.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 16))
    row += 1
    
    # ADSR ENVELOPE
    ttk.Separator(frm, orient="horizontal").grid(
        row=row, column=0, columnspan=2, sticky="ew", pady=(4, 12)
    )
    row += 1
    
    ttk.Label(frm, text="ADSR Envelope", font=("Segoe UI", 10, "bold")).grid(
        row=row, column=0, columnspan=2, sticky="w", pady=(0, 12)
    )
    row += 1
    
    # Attack
    ttk.Label(frm, text="Attack", font=("Segoe UI", 9)).grid(
        row=row, column=0, sticky="w", padx=(0, 12), pady=(0, 4)
    )
    attack_label = ttk.Label(frm, text="0.005 s", foreground="#3b82f6")
    attack_label.grid(row=row, column=1, sticky="e", pady=(0, 4))
    row += 1
    
    attack_var = tk.DoubleVar(value=getattr(synthesizer, 'attack', 0.005))
    attack_var.trace_add('write', on_change)
    
    attack_slider = ttk.Scale(
        frm, from_=0.0, to=1.0, orient="horizontal",
        variable=attack_var, length=400
    )
    attack_slider.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
    row += 1
    
    # Decay
    ttk.Label(frm, text="Decay", font=("Segoe UI", 9)).grid(
        row=row, column=0, sticky="w", padx=(0, 12), pady=(0, 4)
    )
    decay_label = ttk.Label(frm, text="0.050 s", foreground="#3b82f6")
    decay_label.grid(row=row, column=1, sticky="e", pady=(0, 4))
    row += 1
    
    decay_var = tk.DoubleVar(value=getattr(synthesizer, 'decay', 0.05))
    decay_var.trace_add('write', on_change)
    
    decay_slider = ttk.Scale(
        frm, from_=0.0, to=1.0, orient="horizontal",
        variable=decay_var, length=400
    )
    decay_slider.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
    row += 1
    
    # Sustain
    ttk.Label(frm, text="Sustain", font=("Segoe UI", 9)).grid(
        row=row, column=0, sticky="w", padx=(0, 12), pady=(0, 4)
    )
    sustain_label = ttk.Label(frm, text="0.70", foreground="#3b82f6")
    sustain_label.grid(row=row, column=1, sticky="e", pady=(0, 4))
    row += 1
    
    sustain_var = tk.DoubleVar(value=getattr(synthesizer, 'sustain', 0.7))
    sustain_var.trace_add('write', on_change)
    
    sustain_slider = ttk.Scale(
        frm, from_=0.0, to=1.0, orient="horizontal",
        variable=sustain_var, length=400
    )
    sustain_slider.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
    row += 1
    
    # Release
    ttk.Label(frm, text="Release", font=("Segoe UI", 9)).grid(
        row=row, column=0, sticky="w", padx=(0, 12), pady=(0, 4)
    )
    release_label = ttk.Label(frm, text="0.100 s", foreground="#3b82f6")
    release_label.grid(row=row, column=1, sticky="e", pady=(0, 4))
    row += 1
    
    release_var = tk.DoubleVar(value=getattr(synthesizer, 'release', 0.1))
    release_var.trace_add('write', on_change)
    
    release_slider = ttk.Scale(
        frm, from_=0.0, to=2.0, orient="horizontal",
        variable=release_var, length=400
    )
    release_slider.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 16))
    row += 1
    
    # ADSR Diagram (simple visual representation)
    ttk.Separator(frm, orient="horizontal").grid(
        row=row, column=0, columnspan=2, sticky="ew", pady=(4, 12)
    )
    row += 1
    
    diagram_frame = ttk.Frame(frm)
    diagram_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 16))
    row += 1
    
    canvas = tk.Canvas(diagram_frame, width=460, height=100, bg="#0d0d0d", highlightthickness=0)
    canvas.pack()
    
    def draw_adsr():
        """Draw ADSR envelope visualization."""
        canvas.delete("all")
        
        # Get current values
        a = attack_var.get() * 100
        d = decay_var.get() * 100
        s = sustain_var.get()
        r = release_var.get() * 100
        
        # Normalize to canvas width
        total = a + d + 50 + r  # 50 for sustain portion
        if total <= 0:
            total = 1
        scale = 400 / total
        
        # Points
        x0 = 30
        y0 = 90
        
        # Attack
        x1 = x0 + (a * scale)
        y1 = 10
        
        # Decay
        x2 = x1 + (d * scale)
        y2 = 10 + (1 - s) * 70
        
        # Sustain
        x3 = x2 + (50 * scale)
        y3 = y2
        
        # Release
        x4 = x3 + (r * scale)
        y4 = y0
        
        # Draw envelope
        points = [x0, y0, x1, y1, x2, y2, x3, y3, x4, y4]
        canvas.create_line(points, fill="#3b82f6", width=2, smooth=True)
        
        # Labels
        canvas.create_text(x0, y0 + 10, text="A", fill="#888", font=("Segoe UI", 8))
        canvas.create_text(x2, y0 + 10, text="D", fill="#888", font=("Segoe UI", 8))
        canvas.create_text((x2 + x3) / 2, y0 + 10, text="S", fill="#888", font=("Segoe UI", 8))
        canvas.create_text(x4, y0 + 10, text="R", fill="#888", font=("Segoe UI", 8))
    
    # Update diagram on parameter change
    original_on_change = on_change
    def on_change_with_diagram(*args):
        original_on_change(*args)
        draw_adsr()
    
    # Re-assign all traces to use new on_change with diagram
    for var in [osc_var, volume_var, attack_var, decay_var, sustain_var, release_var]:
        # Remove old traces
        traces = var.trace_info()
        for trace in traces:
            try:
                var.trace_remove('write', trace[1])
            except Exception:
                pass
        # Add new trace
        var.trace_add('write', on_change_with_diagram)
    
    draw_adsr()
    
    # PRESETS
    ttk.Separator(frm, orient="horizontal").grid(
        row=row, column=0, columnspan=2, sticky="ew", pady=(4, 12)
    )
    row += 1
    
    ttk.Label(frm, text="Presets", font=("Segoe UI", 10, "bold")).grid(
        row=row, column=0, columnspan=2, sticky="w", pady=(0, 8)
    )
    row += 1
    
    preset_frame = ttk.Frame(frm)
    preset_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 16))
    row += 1
    
    def load_preset(preset_name):
        """Load a preset configuration."""
        presets = {
            "default": {"osc": "sine", "vol": 1.0, "a": 0.005, "d": 0.05, "s": 0.7, "r": 0.1},
            "pad": {"osc": "sine", "vol": 0.8, "a": 0.3, "d": 0.2, "s": 0.6, "r": 0.5},
            "pluck": {"osc": "triangle", "vol": 1.0, "a": 0.001, "d": 0.1, "s": 0.0, "r": 0.2},
            "bass": {"osc": "saw", "vol": 1.2, "a": 0.01, "d": 0.05, "s": 0.8, "r": 0.1},
            "lead": {"osc": "square", "vol": 1.0, "a": 0.01, "d": 0.1, "s": 0.7, "r": 0.2},
        }
        
        if preset_name in presets:
            p = presets[preset_name]
            osc_var.set(p["osc"])
            volume_var.set(p["vol"])
            attack_var.set(p["a"])
            decay_var.set(p["d"])
            sustain_var.set(p["s"])
            release_var.set(p["r"])
    
    presets_buttons = [
        ("Default", "default"),
        ("Pad", "pad"),
        ("Pluck", "pluck"),
        ("Bass", "bass"),
        ("Lead", "lead"),
    ]
    
    for label, preset in presets_buttons:
        btn = ttk.Button(
            preset_frame,
            text=label,
            command=lambda p=preset: load_preset(p),
            width=10
        )
        btn.pack(side="left", padx=4)
    
    # BUTTONS
    ttk.Separator(frm, orient="horizontal").grid(
        row=row, column=0, columnspan=2, sticky="ew", pady=(4, 12)
    )
    row += 1
    
    button_frame = ttk.Frame(frm)
    button_frame.grid(row=row, column=0, columnspan=2, pady=(4, 0))
    
    # Close button
    def apply_and_close():
        if callable(on_apply):
            on_apply(synthesizer)
        win.destroy()
    
    close_btn = ttk.Button(button_frame, text="✓ Apply & Close", command=apply_and_close)
    close_btn.pack(side="left", padx=4)
    
    cancel_btn = ttk.Button(button_frame, text="✕ Close", command=win.destroy)
    cancel_btn.pack(side="left", padx=4)
    

def show_advanced_synth_editor(parent, synthesizer, track_name: str = "Advanced Synth", 
                               on_apply: Optional[Callable] = None):
    """Open advanced synthesizer editor for an AdvancedSynthesizer instance.
    
    Parameters:
        parent: Tk parent window
        synthesizer: AdvancedSynthesizer instance to edit (in-place)
        track_name: Name of the track (for window title)
        on_apply: optional callback invoked when properties change
    """
    if tk is None or ttk is None or parent is None or synthesizer is None:
        return
    
    win = tk.Toplevel(parent)
    win.title(f"Advanced Synthesizer - {track_name}")
    win.resizable(True, True)
    win.configure(bg="#0d0d0d")
    win.geometry("900x800")
    
    # Create scrollable frame
    main_frame = ttk.Frame(win)
    main_frame.pack(fill="both", expand=True)
    
    canvas = tk.Canvas(main_frame, bg="#0d0d0d", highlightthickness=0)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Main container
    frm = ttk.Frame(scrollable_frame, padding=24)
    frm.pack(fill="both", expand=True)
    frm.columnconfigure(1, weight=1)
    frm.columnconfigure(3, weight=1)
    
    # Storage for all variables
    vars_dict: Dict[str, Any] = {}
    labels_dict: Dict[str, Any] = {}
    
    def on_change(*args):
        """Called whenever any parameter changes."""
        try:
            # OSC 1
            synthesizer.osc1_type = vars_dict['osc1_type'].get()
            synthesizer.osc1_octave = int(vars_dict['osc1_octave'].get())
            synthesizer.osc1_semitone = int(vars_dict['osc1_semitone'].get())
            synthesizer.osc1_detune = vars_dict['osc1_detune'].get()
            synthesizer.osc1_level = vars_dict['osc1_level'].get()
            synthesizer.osc1_pwm = vars_dict['osc1_pwm'].get()
            
            # OSC 2
            synthesizer.osc2_type = vars_dict['osc2_type'].get()
            synthesizer.osc2_octave = int(vars_dict['osc2_octave'].get())
            synthesizer.osc2_semitone = int(vars_dict['osc2_semitone'].get())
            synthesizer.osc2_detune = vars_dict['osc2_detune'].get()
            synthesizer.osc2_level = vars_dict['osc2_level'].get()
            synthesizer.osc2_pwm = vars_dict['osc2_pwm'].get()
            
            # MIXER
            synthesizer.osc_mix = vars_dict['osc_mix'].get()
            
            # SUB
            synthesizer.sub_enabled = vars_dict['sub_enabled'].get()
            synthesizer.sub_level = vars_dict['sub_level'].get()
            synthesizer.sub_octave = int(vars_dict['sub_octave'].get())
            
            # UNISON
            synthesizer.unison_enabled = vars_dict['unison_enabled'].get()
            synthesizer.unison_voices = int(vars_dict['unison_voices'].get())
            synthesizer.unison_detune = vars_dict['unison_detune'].get()
            synthesizer.unison_spread = vars_dict['unison_spread'].get()
            
            # FILTER
            synthesizer.filter_enabled = vars_dict['filter_enabled'].get()
            synthesizer.filter_type = vars_dict['filter_type'].get()
            synthesizer.filter_cutoff = vars_dict['filter_cutoff'].get()
            synthesizer.filter_resonance = vars_dict['filter_resonance'].get()
            synthesizer.filter_envelope_amount = vars_dict['filter_envelope_amount'].get()
            
            # FILTER ENV
            synthesizer.filter_attack = vars_dict['filter_attack'].get()
            synthesizer.filter_decay = vars_dict['filter_decay'].get()
            synthesizer.filter_sustain = vars_dict['filter_sustain'].get()
            synthesizer.filter_release = vars_dict['filter_release'].get()
            
            # AMP ENV
            synthesizer.attack = vars_dict['attack'].get()
            synthesizer.decay = vars_dict['decay'].get()
            synthesizer.sustain = vars_dict['sustain'].get()
            synthesizer.release = vars_dict['release'].get()
            
            # GLIDE
            synthesizer.glide_enabled = vars_dict['glide_enabled'].get()
            synthesizer.glide_time = vars_dict['glide_time'].get()
            
            # LFO
            synthesizer.lfo_enabled = vars_dict['lfo_enabled'].get()
            synthesizer.lfo_rate = vars_dict['lfo_rate'].get()
            synthesizer.lfo_type = vars_dict['lfo_type'].get()
            synthesizer.lfo_amount = vars_dict['lfo_amount'].get()
            synthesizer.lfo_target = vars_dict['lfo_target'].get()
            
            # MASTER
            synthesizer.volume = vars_dict['volume'].get()
            
            # Update labels
            update_all_labels()
            
            # Trigger callback
            if callable(on_apply):
                on_apply(synthesizer)
        except Exception as ex:
            print(f"Advanced Synth Editor: error updating: {ex}")
    
    def update_all_labels():
        """Update all value labels."""
        try:
            labels_dict['osc1_octave'].config(text=f"{int(vars_dict['osc1_octave'].get()):+d}")
            labels_dict['osc1_semitone'].config(text=f"{int(vars_dict['osc1_semitone'].get()):+d}")
            labels_dict['osc1_detune'].config(text=f"{vars_dict['osc1_detune'].get():+.1f}¢")
            labels_dict['osc1_level'].config(text=f"{vars_dict['osc1_level'].get():.2f}")
            labels_dict['osc1_pwm'].config(text=f"{vars_dict['osc1_pwm'].get():.2f}")
            
            labels_dict['osc2_octave'].config(text=f"{int(vars_dict['osc2_octave'].get()):+d}")
            labels_dict['osc2_semitone'].config(text=f"{int(vars_dict['osc2_semitone'].get()):+d}")
            labels_dict['osc2_detune'].config(text=f"{vars_dict['osc2_detune'].get():+.1f}¢")
            labels_dict['osc2_level'].config(text=f"{vars_dict['osc2_level'].get():.2f}")
            labels_dict['osc2_pwm'].config(text=f"{vars_dict['osc2_pwm'].get():.2f}")
            
            labels_dict['osc_mix'].config(text=f"{vars_dict['osc_mix'].get():.2f}")
            labels_dict['sub_level'].config(text=f"{vars_dict['sub_level'].get():.2f}")
            labels_dict['sub_octave'].config(text=f"{int(vars_dict['sub_octave'].get()):+d}")
            
            labels_dict['unison_voices'].config(text=f"{int(vars_dict['unison_voices'].get())}")
            labels_dict['unison_detune'].config(text=f"{vars_dict['unison_detune'].get():.1f}¢")
            labels_dict['unison_spread'].config(text=f"{vars_dict['unison_spread'].get():.2f}")
            
            labels_dict['filter_cutoff'].config(text=f"{vars_dict['filter_cutoff'].get():.0f} Hz")
            labels_dict['filter_resonance'].config(text=f"{vars_dict['filter_resonance'].get():.2f}")
            labels_dict['filter_envelope_amount'].config(text=f"{vars_dict['filter_envelope_amount'].get():+.2f}")
            
            labels_dict['filter_attack'].config(text=f"{vars_dict['filter_attack'].get():.3f} s")
            labels_dict['filter_decay'].config(text=f"{vars_dict['filter_decay'].get():.3f} s")
            labels_dict['filter_sustain'].config(text=f"{vars_dict['filter_sustain'].get():.2f}")
            labels_dict['filter_release'].config(text=f"{vars_dict['filter_release'].get():.3f} s")
            
            labels_dict['attack'].config(text=f"{vars_dict['attack'].get():.3f} s")
            labels_dict['decay'].config(text=f"{vars_dict['decay'].get():.3f} s")
            labels_dict['sustain'].config(text=f"{vars_dict['sustain'].get():.2f}")
            labels_dict['release'].config(text=f"{vars_dict['release'].get():.3f} s")
            
            labels_dict['glide_time'].config(text=f"{vars_dict['glide_time'].get():.3f} s")
            labels_dict['lfo_rate'].config(text=f"{vars_dict['lfo_rate'].get():.2f} Hz")
            labels_dict['lfo_amount'].config(text=f"{vars_dict['lfo_amount'].get():.2f}")
            labels_dict['volume'].config(text=f"{vars_dict['volume'].get():.2f}")
        except Exception as ex:
            print(f"Label update error: {ex}")
    
    row = 0
    
    # Title
    title_label = ttk.Label(
        frm,
        text="🎹 Advanced Synthesizer",
        font=("Segoe UI", 16, "bold"),
        foreground="#3b82f6"
    )
    title_label.grid(row=row, column=0, columnspan=4, sticky="w", pady=(0, 20))
    row += 1
    
    # ============ OSCILLATOR 1 ============
    section_label = ttk.Label(frm, text="OSCILLATOR 1", font=("Segoe UI", 11, "bold"), 
                             foreground="#10b981")
    section_label.grid(row=row, column=0, columnspan=2, sticky="w", pady=(8, 8))
    row += 1
    
    # OSC 1 Type
    vars_dict['osc1_type'] = tk.StringVar(value=getattr(synthesizer, 'osc1_type', 'saw'))
    ttk.Label(frm, text="Waveform:").grid(row=row, column=0, sticky="w", pady=4)
    osc1_combo = ttk.Combobox(frm, textvariable=vars_dict['osc1_type'], 
                              values=['sine', 'square', 'saw', 'triangle', 'noise'], 
                              state='readonly', width=15)
    osc1_combo.grid(row=row, column=1, sticky="w", pady=4)
    osc1_combo.bind('<<ComboboxSelected>>', on_change)
    row += 1
    
    # OSC 1 Octave
    vars_dict['osc1_octave'] = tk.DoubleVar(value=getattr(synthesizer, 'osc1_octave', 0))
    ttk.Label(frm, text="Octave:").grid(row=row, column=0, sticky="w", pady=4)
    labels_dict['osc1_octave'] = ttk.Label(frm, text="+0", foreground="#3b82f6")
    labels_dict['osc1_octave'].grid(row=row, column=1, sticky="e", pady=4)
    row += 1
    ttk.Scale(frm, from_=-2, to=2, orient="horizontal", variable=vars_dict['osc1_octave'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=4)
    row += 1
    
    # OSC 1 Semitone
    vars_dict['osc1_semitone'] = tk.DoubleVar(value=getattr(synthesizer, 'osc1_semitone', 0))
    ttk.Label(frm, text="Semitone:").grid(row=row, column=0, sticky="w", pady=4)
    labels_dict['osc1_semitone'] = ttk.Label(frm, text="+0", foreground="#3b82f6")
    labels_dict['osc1_semitone'].grid(row=row, column=1, sticky="e", pady=4)
    row += 1
    ttk.Scale(frm, from_=-12, to=12, orient="horizontal", variable=vars_dict['osc1_semitone'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=4)
    row += 1
    
    # OSC 1 Detune
    vars_dict['osc1_detune'] = tk.DoubleVar(value=getattr(synthesizer, 'osc1_detune', 0.0))
    ttk.Label(frm, text="Detune:").grid(row=row, column=0, sticky="w", pady=4)
    labels_dict['osc1_detune'] = ttk.Label(frm, text="+0.0¢", foreground="#3b82f6")
    labels_dict['osc1_detune'].grid(row=row, column=1, sticky="e", pady=4)
    row += 1
    ttk.Scale(frm, from_=-100, to=100, orient="horizontal", variable=vars_dict['osc1_detune'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=4)
    row += 1
    
    # OSC 1 Level
    vars_dict['osc1_level'] = tk.DoubleVar(value=getattr(synthesizer, 'osc1_level', 1.0))
    ttk.Label(frm, text="Level:").grid(row=row, column=0, sticky="w", pady=4)
    labels_dict['osc1_level'] = ttk.Label(frm, text="1.00", foreground="#3b82f6")
    labels_dict['osc1_level'].grid(row=row, column=1, sticky="e", pady=4)
    row += 1
    ttk.Scale(frm, from_=0, to=1, orient="horizontal", variable=vars_dict['osc1_level'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=4)
    row += 1
    
    # OSC 1 PWM
    vars_dict['osc1_pwm'] = tk.DoubleVar(value=getattr(synthesizer, 'osc1_pwm', 0.5))
    ttk.Label(frm, text="PWM:").grid(row=row, column=0, sticky="w", pady=4)
    labels_dict['osc1_pwm'] = ttk.Label(frm, text="0.50", foreground="#3b82f6")
    labels_dict['osc1_pwm'].grid(row=row, column=1, sticky="e", pady=4)
    row += 1
    ttk.Scale(frm, from_=0.1, to=0.9, orient="horizontal", variable=vars_dict['osc1_pwm'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(4, 16))
    row += 1
    
    # Reset row for OSC 2 (right column)
    osc2_start_row = 1
    
    # ============ OSCILLATOR 2 ============
    section_label2 = ttk.Label(frm, text="OSCILLATOR 2", font=("Segoe UI", 11, "bold"), 
                              foreground="#10b981")
    section_label2.grid(row=osc2_start_row, column=2, columnspan=2, sticky="w", pady=(8, 8))
    osc2_start_row += 1
    
    # OSC 2 Type
    vars_dict['osc2_type'] = tk.StringVar(value=getattr(synthesizer, 'osc2_type', 'square'))
    ttk.Label(frm, text="Waveform:").grid(row=osc2_start_row, column=2, sticky="w", pady=4)
    osc2_combo = ttk.Combobox(frm, textvariable=vars_dict['osc2_type'], 
                              values=['sine', 'square', 'saw', 'triangle', 'noise'], 
                              state='readonly', width=15)
    osc2_combo.grid(row=osc2_start_row, column=3, sticky="w", pady=4)
    osc2_combo.bind('<<ComboboxSelected>>', on_change)
    osc2_start_row += 1
    
    # OSC 2 Octave
    vars_dict['osc2_octave'] = tk.DoubleVar(value=getattr(synthesizer, 'osc2_octave', 0))
    ttk.Label(frm, text="Octave:").grid(row=osc2_start_row, column=2, sticky="w", pady=4)
    labels_dict['osc2_octave'] = ttk.Label(frm, text="+0", foreground="#3b82f6")
    labels_dict['osc2_octave'].grid(row=osc2_start_row, column=3, sticky="e", pady=4)
    osc2_start_row += 1
    ttk.Scale(frm, from_=-2, to=2, orient="horizontal", variable=vars_dict['osc2_octave'], 
             length=200, command=lambda v: on_change()).grid(row=osc2_start_row, column=2, columnspan=2, sticky="ew", pady=4)
    osc2_start_row += 1
    
    # OSC 2 Semitone
    vars_dict['osc2_semitone'] = tk.DoubleVar(value=getattr(synthesizer, 'osc2_semitone', 0))
    ttk.Label(frm, text="Semitone:").grid(row=osc2_start_row, column=2, sticky="w", pady=4)
    labels_dict['osc2_semitone'] = ttk.Label(frm, text="+0", foreground="#3b82f6")
    labels_dict['osc2_semitone'].grid(row=osc2_start_row, column=3, sticky="e", pady=4)
    osc2_start_row += 1
    ttk.Scale(frm, from_=-12, to=12, orient="horizontal", variable=vars_dict['osc2_semitone'], 
             length=200, command=lambda v: on_change()).grid(row=osc2_start_row, column=2, columnspan=2, sticky="ew", pady=4)
    osc2_start_row += 1
    
    # OSC 2 Detune
    vars_dict['osc2_detune'] = tk.DoubleVar(value=getattr(synthesizer, 'osc2_detune', 0.0))
    ttk.Label(frm, text="Detune:").grid(row=osc2_start_row, column=2, sticky="w", pady=4)
    labels_dict['osc2_detune'] = ttk.Label(frm, text="+0.0¢", foreground="#3b82f6")
    labels_dict['osc2_detune'].grid(row=osc2_start_row, column=3, sticky="e", pady=4)
    osc2_start_row += 1
    ttk.Scale(frm, from_=-100, to=100, orient="horizontal", variable=vars_dict['osc2_detune'], 
             length=200, command=lambda v: on_change()).grid(row=osc2_start_row, column=2, columnspan=2, sticky="ew", pady=4)
    osc2_start_row += 1
    
    # OSC 2 Level
    vars_dict['osc2_level'] = tk.DoubleVar(value=getattr(synthesizer, 'osc2_level', 0.5))
    ttk.Label(frm, text="Level:").grid(row=osc2_start_row, column=2, sticky="w", pady=4)
    labels_dict['osc2_level'] = ttk.Label(frm, text="0.50", foreground="#3b82f6")
    labels_dict['osc2_level'].grid(row=osc2_start_row, column=3, sticky="e", pady=4)
    osc2_start_row += 1
    ttk.Scale(frm, from_=0, to=1, orient="horizontal", variable=vars_dict['osc2_level'], 
             length=200, command=lambda v: on_change()).grid(row=osc2_start_row, column=2, columnspan=2, sticky="ew", pady=4)
    osc2_start_row += 1
    
    # OSC 2 PWM
    vars_dict['osc2_pwm'] = tk.DoubleVar(value=getattr(synthesizer, 'osc2_pwm', 0.5))
    ttk.Label(frm, text="PWM:").grid(row=osc2_start_row, column=2, sticky="w", pady=4)
    labels_dict['osc2_pwm'] = ttk.Label(frm, text="0.50", foreground="#3b82f6")
    labels_dict['osc2_pwm'].grid(row=osc2_start_row, column=3, sticky="e", pady=4)
    osc2_start_row += 1
    ttk.Scale(frm, from_=0.1, to=0.9, orient="horizontal", variable=vars_dict['osc2_pwm'], 
             length=200, command=lambda v: on_change()).grid(row=osc2_start_row, column=2, columnspan=2, sticky="ew", pady=(4, 16))
    osc2_start_row += 1
    
    # Continue from max row
    row = max(row, osc2_start_row)
    
    ttk.Separator(frm, orient="horizontal").grid(row=row, column=0, columnspan=4, sticky="ew", pady=12)
    row += 1
    
    # ============ MIXER & SUB ============
    section_label = ttk.Label(frm, text="MIXER & SUB OSCILLATOR", font=("Segoe UI", 11, "bold"), 
                             foreground="#f59e0b")
    section_label.grid(row=row, column=0, columnspan=4, sticky="w", pady=(8, 8))
    row += 1
    
    # Osc Mix
    vars_dict['osc_mix'] = tk.DoubleVar(value=getattr(synthesizer, 'osc_mix', 0.5))
    ttk.Label(frm, text="Osc Mix (1→2):").grid(row=row, column=0, sticky="w", pady=4)
    labels_dict['osc_mix'] = ttk.Label(frm, text="0.50", foreground="#3b82f6")
    labels_dict['osc_mix'].grid(row=row, column=1, sticky="e", pady=4)
    row += 1
    ttk.Scale(frm, from_=0, to=1, orient="horizontal", variable=vars_dict['osc_mix'], 
             length=400, command=lambda v: on_change()).grid(row=row, column=0, columnspan=4, sticky="ew", pady=4)
    row += 1
    
    # Sub Enable
    vars_dict['sub_enabled'] = tk.BooleanVar(value=getattr(synthesizer, 'sub_enabled', False))
    sub_check = ttk.Checkbutton(frm, text="Sub Oscillator Enabled", variable=vars_dict['sub_enabled'], 
                                command=on_change)
    sub_check.grid(row=row, column=0, columnspan=2, sticky="w", pady=8)
    row += 1
    
    # Sub Level
    vars_dict['sub_level'] = tk.DoubleVar(value=getattr(synthesizer, 'sub_level', 0.3))
    ttk.Label(frm, text="Sub Level:").grid(row=row, column=0, sticky="w", pady=4)
    labels_dict['sub_level'] = ttk.Label(frm, text="0.30", foreground="#3b82f6")
    labels_dict['sub_level'].grid(row=row, column=1, sticky="e", pady=4)
    row += 1
    ttk.Scale(frm, from_=0, to=1, orient="horizontal", variable=vars_dict['sub_level'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=4)
    row += 1
    
    # Sub Octave
    vars_dict['sub_octave'] = tk.DoubleVar(value=getattr(synthesizer, 'sub_octave', -1))
    ttk.Label(frm, text="Sub Octave:").grid(row=row, column=0, sticky="w", pady=4)
    labels_dict['sub_octave'] = ttk.Label(frm, text="-1", foreground="#3b82f6")
    labels_dict['sub_octave'].grid(row=row, column=1, sticky="e", pady=4)
    row += 1
    ttk.Scale(frm, from_=-2, to=0, orient="horizontal", variable=vars_dict['sub_octave'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(4, 16))
    row += 1
    
    ttk.Separator(frm, orient="horizontal").grid(row=row, column=0, columnspan=4, sticky="ew", pady=12)
    row += 1
    
    # ============ UNISON ============
    section_label = ttk.Label(frm, text="UNISON", font=("Segoe UI", 11, "bold"), 
                             foreground="#8b5cf6")
    section_label.grid(row=row, column=0, columnspan=4, sticky="w", pady=(8, 8))
    row += 1
    
    vars_dict['unison_enabled'] = tk.BooleanVar(value=getattr(synthesizer, 'unison_enabled', False))
    unison_check = ttk.Checkbutton(frm, text="Unison Enabled", variable=vars_dict['unison_enabled'], 
                                   command=on_change)
    unison_check.grid(row=row, column=0, columnspan=2, sticky="w", pady=8)
    row += 1
    
    # Voices
    vars_dict['unison_voices'] = tk.DoubleVar(value=getattr(synthesizer, 'unison_voices', 3))
    ttk.Label(frm, text="Voices:").grid(row=row, column=0, sticky="w", pady=4)
    labels_dict['unison_voices'] = ttk.Label(frm, text="3", foreground="#3b82f6")
    labels_dict['unison_voices'].grid(row=row, column=1, sticky="e", pady=4)
    row += 1
    ttk.Scale(frm, from_=1, to=7, orient="horizontal", variable=vars_dict['unison_voices'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=4)
    row += 1
    
    # Detune
    vars_dict['unison_detune'] = tk.DoubleVar(value=getattr(synthesizer, 'unison_detune', 10.0))
    ttk.Label(frm, text="Detune:").grid(row=row, column=0, sticky="w", pady=4)
    labels_dict['unison_detune'] = ttk.Label(frm, text="10.0¢", foreground="#3b82f6")
    labels_dict['unison_detune'].grid(row=row, column=1, sticky="e", pady=4)
    row += 1
    ttk.Scale(frm, from_=0, to=50, orient="horizontal", variable=vars_dict['unison_detune'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=4)
    row += 1
    
    # Spread
    vars_dict['unison_spread'] = tk.DoubleVar(value=getattr(synthesizer, 'unison_spread', 0.5))
    ttk.Label(frm, text="Stereo Spread:").grid(row=row, column=0, sticky="w", pady=4)
    labels_dict['unison_spread'] = ttk.Label(frm, text="0.50", foreground="#3b82f6")
    labels_dict['unison_spread'].grid(row=row, column=1, sticky="e", pady=4)
    row += 1
    ttk.Scale(frm, from_=0, to=1, orient="horizontal", variable=vars_dict['unison_spread'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(4, 16))
    row += 1
    
    ttk.Separator(frm, orient="horizontal").grid(row=row, column=0, columnspan=4, sticky="ew", pady=12)
    row += 1
    
    # ============ FILTER ============
    section_label = ttk.Label(frm, text="FILTER", font=("Segoe UI", 11, "bold"), 
                             foreground="#ec4899")
    section_label.grid(row=row, column=0, columnspan=4, sticky="w", pady=(8, 8))
    row += 1
    
    vars_dict['filter_enabled'] = tk.BooleanVar(value=getattr(synthesizer, 'filter_enabled', True))
    filter_check = ttk.Checkbutton(frm, text="Filter Enabled", variable=vars_dict['filter_enabled'], 
                                   command=on_change)
    filter_check.grid(row=row, column=0, columnspan=2, sticky="w", pady=8)
    row += 1
    
    # Filter Type
    vars_dict['filter_type'] = tk.StringVar(value=getattr(synthesizer, 'filter_type', 'lowpass'))
    ttk.Label(frm, text="Type:").grid(row=row, column=0, sticky="w", pady=4)
    filter_combo = ttk.Combobox(frm, textvariable=vars_dict['filter_type'], 
                                values=['lowpass', 'highpass', 'bandpass'], 
                                state='readonly', width=15)
    filter_combo.grid(row=row, column=1, sticky="w", pady=4)
    filter_combo.bind('<<ComboboxSelected>>', on_change)
    row += 1
    
    # Cutoff
    vars_dict['filter_cutoff'] = tk.DoubleVar(value=getattr(synthesizer, 'filter_cutoff', 8000.0))
    ttk.Label(frm, text="Cutoff:").grid(row=row, column=0, sticky="w", pady=4)
    labels_dict['filter_cutoff'] = ttk.Label(frm, text="8000 Hz", foreground="#3b82f6")
    labels_dict['filter_cutoff'].grid(row=row, column=1, sticky="e", pady=4)
    row += 1
    ttk.Scale(frm, from_=20, to=20000, orient="horizontal", variable=vars_dict['filter_cutoff'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=4)
    row += 1
    
    # Resonance
    vars_dict['filter_resonance'] = tk.DoubleVar(value=getattr(synthesizer, 'filter_resonance', 0.7))
    ttk.Label(frm, text="Resonance:").grid(row=row, column=0, sticky="w", pady=4)
    labels_dict['filter_resonance'] = ttk.Label(frm, text="0.70", foreground="#3b82f6")
    labels_dict['filter_resonance'].grid(row=row, column=1, sticky="e", pady=4)
    row += 1
    ttk.Scale(frm, from_=0.5, to=10.0, orient="horizontal", variable=vars_dict['filter_resonance'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=4)
    row += 1
    
    # Envelope Amount
    vars_dict['filter_envelope_amount'] = tk.DoubleVar(value=getattr(synthesizer, 'filter_envelope_amount', 0.0))
    ttk.Label(frm, text="Env Amount:").grid(row=row, column=0, sticky="w", pady=4)
    labels_dict['filter_envelope_amount'] = ttk.Label(frm, text="+0.00", foreground="#3b82f6")
    labels_dict['filter_envelope_amount'].grid(row=row, column=1, sticky="e", pady=4)
    row += 1
    ttk.Scale(frm, from_=-1, to=1, orient="horizontal", variable=vars_dict['filter_envelope_amount'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(4, 8))
    row += 1
    
    # Filter Envelope
    ttk.Label(frm, text="Filter Envelope:", font=("Segoe UI", 9, "bold")).grid(
        row=row, column=0, columnspan=2, sticky="w", pady=(8, 4))
    row += 1
    
    vars_dict['filter_attack'] = tk.DoubleVar(value=getattr(synthesizer, 'filter_attack', 0.01))
    ttk.Label(frm, text="Attack:").grid(row=row, column=0, sticky="w", pady=2)
    labels_dict['filter_attack'] = ttk.Label(frm, text="0.010 s", foreground="#3b82f6")
    labels_dict['filter_attack'].grid(row=row, column=1, sticky="e", pady=2)
    row += 1
    ttk.Scale(frm, from_=0, to=2, orient="horizontal", variable=vars_dict['filter_attack'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=2)
    row += 1
    
    vars_dict['filter_decay'] = tk.DoubleVar(value=getattr(synthesizer, 'filter_decay', 0.1))
    ttk.Label(frm, text="Decay:").grid(row=row, column=0, sticky="w", pady=2)
    labels_dict['filter_decay'] = ttk.Label(frm, text="0.100 s", foreground="#3b82f6")
    labels_dict['filter_decay'].grid(row=row, column=1, sticky="e", pady=2)
    row += 1
    ttk.Scale(frm, from_=0, to=2, orient="horizontal", variable=vars_dict['filter_decay'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=2)
    row += 1
    
    vars_dict['filter_sustain'] = tk.DoubleVar(value=getattr(synthesizer, 'filter_sustain', 0.5))
    ttk.Label(frm, text="Sustain:").grid(row=row, column=0, sticky="w", pady=2)
    labels_dict['filter_sustain'] = ttk.Label(frm, text="0.50", foreground="#3b82f6")
    labels_dict['filter_sustain'].grid(row=row, column=1, sticky="e", pady=2)
    row += 1
    ttk.Scale(frm, from_=0, to=1, orient="horizontal", variable=vars_dict['filter_sustain'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=2)
    row += 1
    
    vars_dict['filter_release'] = tk.DoubleVar(value=getattr(synthesizer, 'filter_release', 0.2))
    ttk.Label(frm, text="Release:").grid(row=row, column=0, sticky="w", pady=2)
    labels_dict['filter_release'] = ttk.Label(frm, text="0.200 s", foreground="#3b82f6")
    labels_dict['filter_release'].grid(row=row, column=1, sticky="e", pady=2)
    row += 1
    ttk.Scale(frm, from_=0, to=3, orient="horizontal", variable=vars_dict['filter_release'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(2, 16))
    row += 1
    
    ttk.Separator(frm, orient="horizontal").grid(row=row, column=0, columnspan=4, sticky="ew", pady=12)
    row += 1
    
    # ============ AMPLITUDE ENVELOPE ============
    section_label = ttk.Label(frm, text="AMPLITUDE ENVELOPE", font=("Segoe UI", 11, "bold"), 
                             foreground="#06b6d4")
    section_label.grid(row=row, column=0, columnspan=4, sticky="w", pady=(8, 8))
    row += 1
    
    vars_dict['attack'] = tk.DoubleVar(value=getattr(synthesizer, 'attack', 0.01))
    ttk.Label(frm, text="Attack:").grid(row=row, column=0, sticky="w", pady=2)
    labels_dict['attack'] = ttk.Label(frm, text="0.010 s", foreground="#3b82f6")
    labels_dict['attack'].grid(row=row, column=1, sticky="e", pady=2)
    row += 1
    ttk.Scale(frm, from_=0, to=2, orient="horizontal", variable=vars_dict['attack'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=2)
    row += 1
    
    vars_dict['decay'] = tk.DoubleVar(value=getattr(synthesizer, 'decay', 0.1))
    ttk.Label(frm, text="Decay:").grid(row=row, column=0, sticky="w", pady=2)
    labels_dict['decay'] = ttk.Label(frm, text="0.100 s", foreground="#3b82f6")
    labels_dict['decay'].grid(row=row, column=1, sticky="e", pady=2)
    row += 1
    ttk.Scale(frm, from_=0, to=2, orient="horizontal", variable=vars_dict['decay'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=2)
    row += 1
    
    vars_dict['sustain'] = tk.DoubleVar(value=getattr(synthesizer, 'sustain', 0.7))
    ttk.Label(frm, text="Sustain:").grid(row=row, column=0, sticky="w", pady=2)
    labels_dict['sustain'] = ttk.Label(frm, text="0.70", foreground="#3b82f6")
    labels_dict['sustain'].grid(row=row, column=1, sticky="e", pady=2)
    row += 1
    ttk.Scale(frm, from_=0, to=1, orient="horizontal", variable=vars_dict['sustain'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=2)
    row += 1
    
    vars_dict['release'] = tk.DoubleVar(value=getattr(synthesizer, 'release', 0.2))
    ttk.Label(frm, text="Release:").grid(row=row, column=0, sticky="w", pady=2)
    labels_dict['release'] = ttk.Label(frm, text="0.200 s", foreground="#3b82f6")
    labels_dict['release'].grid(row=row, column=1, sticky="e", pady=2)
    row += 1
    ttk.Scale(frm, from_=0, to=3, orient="horizontal", variable=vars_dict['release'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(2, 16))
    row += 1
    
    ttk.Separator(frm, orient="horizontal").grid(row=row, column=0, columnspan=4, sticky="ew", pady=12)
    row += 1
    
    # ============ GLIDE ============
    section_label = ttk.Label(frm, text="GLIDE / PORTAMENTO", font=("Segoe UI", 11, "bold"), 
                             foreground="#f97316")
    section_label.grid(row=row, column=0, columnspan=4, sticky="w", pady=(8, 8))
    row += 1
    
    vars_dict['glide_enabled'] = tk.BooleanVar(value=getattr(synthesizer, 'glide_enabled', False))
    glide_check = ttk.Checkbutton(frm, text="Glide Enabled", variable=vars_dict['glide_enabled'], 
                                  command=on_change)
    glide_check.grid(row=row, column=0, columnspan=2, sticky="w", pady=8)
    row += 1
    
    vars_dict['glide_time'] = tk.DoubleVar(value=getattr(synthesizer, 'glide_time', 0.1))
    ttk.Label(frm, text="Glide Time:").grid(row=row, column=0, sticky="w", pady=4)
    labels_dict['glide_time'] = ttk.Label(frm, text="0.100 s", foreground="#3b82f6")
    labels_dict['glide_time'].grid(row=row, column=1, sticky="e", pady=4)
    row += 1
    ttk.Scale(frm, from_=0, to=1, orient="horizontal", variable=vars_dict['glide_time'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(4, 16))
    row += 1
    
    ttk.Separator(frm, orient="horizontal").grid(row=row, column=0, columnspan=4, sticky="ew", pady=12)
    row += 1
    
    # ============ LFO ============
    section_label = ttk.Label(frm, text="LFO", font=("Segoe UI", 11, "bold"), 
                             foreground="#14b8a6")
    section_label.grid(row=row, column=0, columnspan=4, sticky="w", pady=(8, 8))
    row += 1
    
    vars_dict['lfo_enabled'] = tk.BooleanVar(value=getattr(synthesizer, 'lfo_enabled', False))
    lfo_check = ttk.Checkbutton(frm, text="LFO Enabled", variable=vars_dict['lfo_enabled'], 
                                command=on_change)
    lfo_check.grid(row=row, column=0, columnspan=2, sticky="w", pady=8)
    row += 1
    
    # LFO Type
    vars_dict['lfo_type'] = tk.StringVar(value=getattr(synthesizer, 'lfo_type', 'sine'))
    ttk.Label(frm, text="Waveform:").grid(row=row, column=0, sticky="w", pady=4)
    lfo_combo = ttk.Combobox(frm, textvariable=vars_dict['lfo_type'], 
                             values=['sine', 'square', 'saw', 'triangle'], 
                             state='readonly', width=15)
    lfo_combo.grid(row=row, column=1, sticky="w", pady=4)
    lfo_combo.bind('<<ComboboxSelected>>', on_change)
    row += 1
    
    # LFO Target
    vars_dict['lfo_target'] = tk.StringVar(value=getattr(synthesizer, 'lfo_target', 'pitch'))
    ttk.Label(frm, text="Target:").grid(row=row, column=0, sticky="w", pady=4)
    lfo_target_combo = ttk.Combobox(frm, textvariable=vars_dict['lfo_target'], 
                                    values=['pitch', 'filter', 'amplitude', 'pwm'], 
                                    state='readonly', width=15)
    lfo_target_combo.grid(row=row, column=1, sticky="w", pady=4)
    lfo_target_combo.bind('<<ComboboxSelected>>', on_change)
    row += 1
    
    # LFO Rate
    vars_dict['lfo_rate'] = tk.DoubleVar(value=getattr(synthesizer, 'lfo_rate', 5.0))
    ttk.Label(frm, text="Rate:").grid(row=row, column=0, sticky="w", pady=4)
    labels_dict['lfo_rate'] = ttk.Label(frm, text="5.00 Hz", foreground="#3b82f6")
    labels_dict['lfo_rate'].grid(row=row, column=1, sticky="e", pady=4)
    row += 1
    ttk.Scale(frm, from_=0.1, to=20, orient="horizontal", variable=vars_dict['lfo_rate'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=4)
    row += 1
    
    # LFO Amount
    vars_dict['lfo_amount'] = tk.DoubleVar(value=getattr(synthesizer, 'lfo_amount', 0.2))
    ttk.Label(frm, text="Amount:").grid(row=row, column=0, sticky="w", pady=4)
    labels_dict['lfo_amount'] = ttk.Label(frm, text="0.20", foreground="#3b82f6")
    labels_dict['lfo_amount'].grid(row=row, column=1, sticky="e", pady=4)
    row += 1
    ttk.Scale(frm, from_=0, to=1, orient="horizontal", variable=vars_dict['lfo_amount'], 
             length=200, command=lambda v: on_change()).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(4, 16))
    row += 1
    
    ttk.Separator(frm, orient="horizontal").grid(row=row, column=0, columnspan=4, sticky="ew", pady=12)
    row += 1
    
    # ============ MASTER ============
    section_label = ttk.Label(frm, text="MASTER", font=("Segoe UI", 11, "bold"), 
                             foreground="#ef4444")
    section_label.grid(row=row, column=0, columnspan=4, sticky="w", pady=(8, 8))
    row += 1
    
    vars_dict['volume'] = tk.DoubleVar(value=getattr(synthesizer, 'volume', 0.8))
    ttk.Label(frm, text="Volume:").grid(row=row, column=0, sticky="w", pady=4)
    labels_dict['volume'] = ttk.Label(frm, text="0.80", foreground="#3b82f6")
    labels_dict['volume'].grid(row=row, column=1, sticky="e", pady=4)
    row += 1
    ttk.Scale(frm, from_=0, to=2, orient="horizontal", variable=vars_dict['volume'], 
             length=400, command=lambda v: on_change()).grid(row=row, column=0, columnspan=4, sticky="ew", pady=(4, 16))
    row += 1
    
    ttk.Separator(frm, orient="horizontal").grid(row=row, column=0, columnspan=4, sticky="ew", pady=12)
    row += 1
    
    # ============ PRESETS ============
    section_label = ttk.Label(frm, text="PRESETS", font=("Segoe UI", 11, "bold"))
    section_label.grid(row=row, column=0, columnspan=4, sticky="w", pady=(8, 8))
    row += 1
    
    def load_preset(preset_name):
        """Load a preset configuration."""
        presets = {
            "classic_lead": {
                "osc1_type": "saw", "osc1_level": 1.0, "osc2_type": "square", "osc2_level": 0.6,
                "osc_mix": 0.4, "filter_cutoff": 2000, "filter_resonance": 3.0, "glide_enabled": True,
                "glide_time": 0.15, "attack": 0.01, "decay": 0.2, "sustain": 0.6, "release": 0.3
            },
            "fat_bass": {
                "osc1_type": "saw", "osc1_octave": -1, "osc1_level": 1.0, "osc2_type": "square",
                "osc2_octave": -1, "osc2_semitone": -5, "osc2_level": 0.7, "sub_enabled": True,
                "sub_level": 0.5, "filter_cutoff": 800, "filter_resonance": 2.0, "unison_enabled": True,
                "unison_voices": 3, "unison_detune": 15, "attack": 0.001, "decay": 0.1, "sustain": 0.9
            },
            "warm_pad": {
                "osc1_type": "sine", "osc1_level": 0.8, "osc2_type": "triangle", "osc2_detune": 5,
                "osc2_level": 0.6, "osc_mix": 0.5, "unison_enabled": True, "unison_voices": 5,
                "unison_detune": 8, "filter_cutoff": 3000, "lfo_enabled": True, "lfo_type": "sine",
                "lfo_target": "filter", "lfo_rate": 0.3, "lfo_amount": 0.3, "attack": 0.8,
                "decay": 0.4, "sustain": 0.7, "release": 1.5
            },
            "pluck": {
                "osc1_type": "triangle", "osc1_level": 1.0, "filter_cutoff": 5000,
                "filter_envelope_amount": 0.8, "filter_attack": 0.001, "filter_decay": 0.15,
                "filter_sustain": 0.0, "attack": 0.001, "decay": 0.2, "sustain": 0.0, "release": 0.1
            },
            "wobble_bass": {
                "osc1_type": "saw", "osc1_octave": -1, "sub_enabled": True, "sub_level": 0.6,
                "filter_cutoff": 1500, "filter_resonance": 5.0, "lfo_enabled": True,
                "lfo_type": "sine", "lfo_target": "filter", "lfo_rate": 4.0, "lfo_amount": 0.8,
                "attack": 0.01, "sustain": 1.0
            }
        }
        
        if preset_name in presets:
            p = presets[preset_name]
            for key, value in p.items():
                if key in vars_dict:
                    vars_dict[key].set(value)
    
    preset_frame = ttk.Frame(frm)
    preset_frame.grid(row=row, column=0, columnspan=4, sticky="ew", pady=(0, 16))
    row += 1
    
    presets_buttons = [
        ("Classic Lead", "classic_lead"),
        ("Fat Bass", "fat_bass"),
        ("Warm Pad", "warm_pad"),
        ("Pluck", "pluck"),
        ("Wobble Bass", "wobble_bass"),
    ]
    
    for label, preset in presets_buttons:
        btn = ttk.Button(
            preset_frame,
            text=label,
            command=lambda p=preset: load_preset(p),
            width=15
        )
        btn.pack(side="left", padx=4, pady=4)
    
    # Initialize labels
    update_all_labels()
    
    # ============ BUTTONS ============
    ttk.Separator(frm, orient="horizontal").grid(row=row, column=0, columnspan=4, sticky="ew", pady=12)
    row += 1
    
    button_frame = ttk.Frame(frm)
    button_frame.grid(row=row, column=0, columnspan=4, pady=(4, 0))
    
    def apply_and_close():
        if callable(on_apply):
            on_apply(synthesizer)
        win.destroy()
    
    close_btn = ttk.Button(button_frame, text="✓ Apply & Close", command=apply_and_close)
    close_btn.pack(side="left", padx=4)
    
    cancel_btn = ttk.Button(button_frame, text="✕ Close", command=win.destroy)
    cancel_btn.pack(side="left", padx=4)
    
    # Enable mousewheel scrolling
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    canvas.bind_all("<MouseWheel>", on_mousewheel)
    
    win.transient(parent)
    win.grab_set()
    parent.wait_window(win)


