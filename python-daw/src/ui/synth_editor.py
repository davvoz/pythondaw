"""Synthesizer Editor dialog for MIDI tracks."""

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover
    tk = None
    ttk = None

from typing import Optional, Callable


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
    
    win.transient(parent)
    win.grab_set()
    parent.wait_window(win)
