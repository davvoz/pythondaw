"""Simple Clip Inspector dialog for editing AudioClip parameters."""

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover
    tk = None
    ttk = None

from typing import Callable, Optional
from src.audio.clip import AudioClip

FADE_SHAPES = ["linear", "exp", "log", "s-curve"]


def show_clip_inspector(parent, clip: AudioClip, on_apply: Optional[Callable[[AudioClip], None]] = None):
    """Open a small editor for a single AudioClip with real-time updates.

    Parameters:
        parent: Tk parent window
        clip: AudioClip instance to edit (in-place)
        on_apply: optional callback invoked when properties change (for live updates)
    """
    if tk is None or ttk is None or parent is None or clip is None:
        return

    win = tk.Toplevel(parent)
    win.title(f"Clip Inspector - {getattr(clip, 'name', 'clip')}")
    win.resizable(False, False)
    win.configure(bg="#1e1e1e")

    frm = ttk.Frame(win, padding=16)
    frm.grid(sticky="nsew")
    
    # Configure grid weights for better layout
    frm.columnconfigure(1, weight=1)
    
    def on_change(*args):
        """Called whenever any parameter changes - updates clip in real-time."""
        try:
            # Update clip properties
            clip.volume = volume_var.get()
            clip.start_offset = max(0.0, start_var.get())
            clip.end_offset = max(0.0, end_var.get())
            clip.fade_in = max(0.0, fade_in_var.get())
            clip.fade_in_shape = fade_in_shape_var.get()
            clip.fade_out = max(0.0, fade_out_var.get())
            clip.fade_out_shape = fade_out_shape_var.get()
            clip.pitch_semitones = pitch_var.get()
            
            # Update display labels
            volume_label.config(text=f"{volume_var.get():.2f}")
            start_label.config(text=f"{start_var.get():.3f} s")
            end_label.config(text=f"{end_var.get():.3f} s")
            fade_in_label.config(text=f"{fade_in_var.get():.3f} s")
            fade_out_label.config(text=f"{fade_out_var.get():.3f} s")
            pitch_label.config(text=f"{pitch_var.get():.1f} st")
            
            # Trigger callback for live preview
            if callable(on_apply):
                on_apply(clip)
        except Exception as ex:
            print(f"Clip Inspector: error updating: {ex}")
    
    # Variables with trace for real-time updates
    volume_var = tk.DoubleVar(value=getattr(clip, 'volume', 1.0))
    start_var = tk.DoubleVar(value=getattr(clip, 'start_offset', 0.0))
    end_var = tk.DoubleVar(value=getattr(clip, 'end_offset', 0.0))
    fade_in_var = tk.DoubleVar(value=getattr(clip, 'fade_in', 0.0))
    fade_in_shape_var = tk.StringVar(value=getattr(clip, 'fade_in_shape', 'linear'))
    fade_out_var = tk.DoubleVar(value=getattr(clip, 'fade_out', 0.0))
    fade_out_shape_var = tk.StringVar(value=getattr(clip, 'fade_out_shape', 'linear'))
    pitch_var = tk.DoubleVar(value=getattr(clip, 'pitch_semitones', 0.0))
    
    # Add traces for real-time updates
    volume_var.trace_add('write', on_change)
    start_var.trace_add('write', on_change)
    end_var.trace_add('write', on_change)
    fade_in_var.trace_add('write', on_change)
    fade_in_shape_var.trace_add('write', on_change)
    fade_out_var.trace_add('write', on_change)
    fade_out_shape_var.trace_add('write', on_change)
    pitch_var.trace_add('write', on_change)
    
    row = 0
    
    # VOLUME
    ttk.Label(frm, text="Volume", font=("Segoe UI", 9, "bold")).grid(
        row=row, column=0, sticky="w", padx=(0, 12), pady=(0, 4)
    )
    volume_label = ttk.Label(frm, text=f"{volume_var.get():.2f}", foreground="#3b82f6")
    volume_label.grid(row=row, column=1, sticky="e", pady=(0, 4))
    row += 1
    
    volume_slider = ttk.Scale(
        frm, from_=0.0, to=2.0, orient="horizontal",
        variable=volume_var, length=300
    )
    volume_slider.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 12))
    row += 1
    
    # PITCH
    ttk.Label(frm, text="Pitch", font=("Segoe UI", 9, "bold")).grid(
        row=row, column=0, sticky="w", padx=(0, 12), pady=(0, 4)
    )
    pitch_label = ttk.Label(frm, text=f"{pitch_var.get():.1f} st", foreground="#3b82f6")
    pitch_label.grid(row=row, column=1, sticky="e", pady=(0, 4))
    row += 1
    
    pitch_slider = ttk.Scale(
        frm, from_=-12.0, to=12.0, orient="horizontal",
        variable=pitch_var, length=300
    )
    pitch_slider.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 12))
    row += 1
    
    # TRIM SECTION
    ttk.Separator(frm, orient="horizontal").grid(
        row=row, column=0, columnspan=2, sticky="ew", pady=(4, 12)
    )
    row += 1
    
    ttk.Label(frm, text="Trim", font=("Segoe UI", 9, "bold")).grid(
        row=row, column=0, columnspan=2, sticky="w", pady=(0, 8)
    )
    row += 1
    
    # Start offset
    ttk.Label(frm, text="Start offset", font=("Segoe UI", 9)).grid(
        row=row, column=0, sticky="w", padx=(0, 12), pady=(0, 4)
    )
    start_label = ttk.Label(frm, text=f"{start_var.get():.3f} s", foreground="#3b82f6")
    start_label.grid(row=row, column=1, sticky="e", pady=(0, 4))
    row += 1
    
    start_slider = ttk.Scale(
        frm, from_=0.0, to=5.0, orient="horizontal",
        variable=start_var, length=300
    )
    start_slider.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
    row += 1
    
    # End offset
    ttk.Label(frm, text="End offset", font=("Segoe UI", 9)).grid(
        row=row, column=0, sticky="w", padx=(0, 12), pady=(0, 4)
    )
    end_label = ttk.Label(frm, text=f"{end_var.get():.3f} s", foreground="#3b82f6")
    end_label.grid(row=row, column=1, sticky="e", pady=(0, 4))
    row += 1
    
    end_slider = ttk.Scale(
        frm, from_=0.0, to=5.0, orient="horizontal",
        variable=end_var, length=300
    )
    end_slider.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 12))
    row += 1
    
    # FADES SECTION
    ttk.Separator(frm, orient="horizontal").grid(
        row=row, column=0, columnspan=2, sticky="ew", pady=(4, 12)
    )
    row += 1
    
    ttk.Label(frm, text="Fades", font=("Segoe UI", 9, "bold")).grid(
        row=row, column=0, columnspan=2, sticky="w", pady=(0, 8)
    )
    row += 1
    
    # Fade In
    fade_in_frame = ttk.Frame(frm)
    fade_in_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 4))
    fade_in_frame.columnconfigure(0, weight=1)
    
    ttk.Label(fade_in_frame, text="Fade in", font=("Segoe UI", 9)).pack(side="left")
    fade_in_label = ttk.Label(fade_in_frame, text=f"{fade_in_var.get():.3f} s", foreground="#3b82f6")
    fade_in_label.pack(side="right", padx=(0, 8))
    
    fade_in_shape_combo = ttk.Combobox(
        fade_in_frame, textvariable=fade_in_shape_var,
        values=FADE_SHAPES, state="readonly", width=10
    )
    fade_in_shape_combo.pack(side="right")
    row += 1
    
    fade_in_slider = ttk.Scale(
        frm, from_=0.0, to=2.0, orient="horizontal",
        variable=fade_in_var, length=300
    )
    fade_in_slider.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
    row += 1
    
    # Fade Out
    fade_out_frame = ttk.Frame(frm)
    fade_out_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 4))
    fade_out_frame.columnconfigure(0, weight=1)
    
    ttk.Label(fade_out_frame, text="Fade out", font=("Segoe UI", 9)).pack(side="left")
    fade_out_label = ttk.Label(fade_out_frame, text=f"{fade_out_var.get():.3f} s", foreground="#3b82f6")
    fade_out_label.pack(side="right", padx=(0, 8))
    
    fade_out_shape_combo = ttk.Combobox(
        fade_out_frame, textvariable=fade_out_shape_var,
        values=FADE_SHAPES, state="readonly", width=10
    )
    fade_out_shape_combo.pack(side="right")
    row += 1
    
    fade_out_slider = ttk.Scale(
        frm, from_=0.0, to=2.0, orient="horizontal",
        variable=fade_out_var, length=300
    )
    fade_out_slider.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 12))
    row += 1
    
    # CLOSE BUTTON
    ttk.Separator(frm, orient="horizontal").grid(
        row=row, column=0, columnspan=2, sticky="ew", pady=(4, 12)
    )
    row += 1
    
    close_btn = ttk.Button(frm, text="Close", command=win.destroy)
    close_btn.grid(row=row, column=0, columnspan=2, pady=(4, 0))

    win.transient(parent)
    win.grab_set()
    parent.wait_window(win)

