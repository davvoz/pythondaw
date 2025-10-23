"""Professional Clip Inspector dialog with waveform editor."""

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover
    tk = None
    ttk = None

from typing import Callable, Optional
from src.audio.clip import AudioClip
from src.midi.clip import MidiClip
from src.ui.waveform_editor import WaveformEditor

FADE_SHAPES = ["linear", "exp", "log", "s-curve"]


def show_midi_clip_info(parent, midi_clip, on_apply: Optional[Callable] = None, player=None, project=None):
    """Open Piano Roll editor directly for MIDI clip.
    
    Parameters:
        parent: Tk parent window
        midi_clip: MidiClip instance
        on_apply: optional callback invoked when changes are made
        player: optional Player instance for playhead tracking
        project: optional Project instance for BPM sync
    """
    if tk is None or ttk is None or parent is None or midi_clip is None:
        return
    
    try:
        from src.ui.piano_roll import PianoRollEditor
        
        def on_piano_apply(clip):
            if callable(on_apply):
                on_apply(clip)
        
        editor = PianoRollEditor(parent, midi_clip, on_apply=on_piano_apply, player=player, project=project)
        editor.show()
    except Exception as e:
        print(f"Error opening Piano Roll: {e}")
        import traceback
        traceback.print_exc()


def show_clip_inspector(parent, clip: AudioClip, on_apply: Optional[Callable[[AudioClip], None]] = None, player=None):
    """Open a small editor for a single AudioClip with real-time updates.

    Parameters:
        parent: Tk parent window
        clip: AudioClip instance to edit (in-place)
        on_apply: optional callback invoked when properties change (for live updates)
        player: optional Player instance for playhead tracking in Piano Roll
    """
    if tk is None or ttk is None or parent is None or clip is None:
        return
    
    # Check if this is a MIDI clip - if so, show different editor
    if isinstance(clip, MidiClip):
        # For MIDI clips, just show a simple message and open piano roll
        show_midi_clip_info(parent, clip, on_apply, player=player)
        return

    win = tk.Toplevel(parent)
    win.title(f"Clip Inspector - {getattr(clip, 'name', 'clip')}")
    win.resizable(True, True)
    win.configure(bg="#1e1e1e")
    win.geometry("800x700")  # Larger window for waveform display
    
    # Configure window grid
    win.columnconfigure(0, weight=1)
    win.rowconfigure(0, weight=0)  # Waveform section
    win.rowconfigure(1, weight=1)  # Controls section

    # --- WAVEFORM SECTION ---
    waveform_frame = ttk.Frame(win, padding=8)
    waveform_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 0))
    waveform_frame.columnconfigure(0, weight=1)
    waveform_frame.rowconfigure(1, weight=1)
    
    # Waveform title
    title_label = ttk.Label(
        waveform_frame,
        text=f"🎵 {getattr(clip, 'name', 'Clip')}",
        font=("Segoe UI", 12, "bold"),
        foreground="#3b82f6"
    )
    title_label.grid(row=0, column=0, sticky="w", pady=(0, 8))
    
    # Waveform editor
    waveform_editor = WaveformEditor(
        waveform_frame,
        clip,
        on_change=None,  # Will be set later
        height=250
    )
    waveform_editor.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
    
    # Waveform controls
    waveform_controls = ttk.Frame(waveform_frame)
    waveform_controls.grid(row=2, column=0, sticky="ew")
    
    ttk.Label(
        waveform_controls,
        text="💡 Tip: Drag the handles (S=Start, E=End, FI=Fade In, FO=Fade Out) to edit the clip",
        font=("Segoe UI", 8),
        foreground="#6b7280"
    ).pack(side="left", padx=4)

    # --- CONTROLS SECTION ---
    # Scrollable frame for controls
    canvas = tk.Canvas(win, bg="#1e1e1e", highlightthickness=0)
    scrollbar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
    frm = ttk.Frame(canvas, padding=16)
    
    frm.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=frm, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.grid(row=1, column=0, sticky="nsew", padx=(8, 0), pady=8)
    scrollbar.grid(row=1, column=1, sticky="ns", pady=8, padx=(0, 8))
    
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
            
            # Update waveform display
            if waveform_editor:
                waveform_editor.redraw()
            
            # Trigger callback for live preview
            if callable(on_apply):
                on_apply(clip)
        except Exception as ex:
            print(f"Clip Inspector: error updating: {ex}")
    
    def on_waveform_change():
        """Called when waveform editor changes clip (via dragging handles)."""
        try:
            # Sync variables with clip values
            volume_var.set(clip.volume)
            start_var.set(clip.start_offset)
            end_var.set(clip.end_offset)
            fade_in_var.set(clip.fade_in)
            fade_out_var.set(clip.fade_out)
            # Note: on_change will be triggered by variable changes
        except Exception as ex:
            print(f"Clip Inspector: error syncing from waveform: {ex}")
    
    # Set waveform editor callback
    waveform_editor.on_change = on_waveform_change
    
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
    
    # ACTIONS SECTION
    ttk.Separator(frm, orient="horizontal").grid(
        row=row, column=0, columnspan=2, sticky="ew", pady=(4, 12)
    )
    row += 1
    
    # Info display
    info_frame = ttk.Frame(frm)
    info_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 12))
    info_frame.columnconfigure(0, weight=1)
    row += 1
    
    def update_info():
        """Update clip information display."""
        try:
            duration = clip.length_seconds
            total_duration = len(clip.buffer) / float(clip.sample_rate) if clip.sample_rate > 0 else 0
            info_text = (
                f"📊 Duration: {duration:.2f}s | "
                f"Original: {total_duration:.2f}s | "
                f"Sample Rate: {clip.sample_rate}Hz | "
                f"Samples: {len(clip.buffer):,}"
            )
            info_label.config(text=info_text)
        except Exception:
            pass
    
    info_label = ttk.Label(
        info_frame,
        text="",
        font=("Segoe UI", 8),
        foreground="#9ca3af"
    )
    info_label.pack(fill="x")
    update_info()
    
    # Update info on changes
    original_on_change = on_change
    def on_change_with_info(*args):
        original_on_change(*args)
        update_info()
    
    # Re-assign traces with the new on_change function
    for var in [volume_var, start_var, end_var, fade_in_var, fade_in_shape_var, 
                fade_out_var, fade_out_shape_var, pitch_var]:
        # Remove old traces
        traces = var.trace_info()
        for trace in traces:
            try:
                var.trace_remove('write', trace[1])
            except Exception:
                pass
        # Add new trace
        var.trace_add('write', on_change_with_info)
    
    # Button frame
    button_frame = ttk.Frame(frm)
    button_frame.grid(row=row, column=0, columnspan=2, pady=(4, 0))
    row += 1
    
    # Reset button
    def reset_clip():
        """Reset clip to default values."""
        clip.start_offset = 0.0
        clip.end_offset = 0.0
        clip.fade_in = 0.0
        clip.fade_out = 0.0
        clip.pitch_semitones = 0.0
        clip.volume = 1.0
        
        volume_var.set(1.0)
        start_var.set(0.0)
        end_var.set(0.0)
        fade_in_var.set(0.0)
        fade_out_var.set(0.0)
        pitch_var.set(0.0)
        
        waveform_editor.redraw()
        if callable(on_apply):
            on_apply(clip)
    
    reset_btn = ttk.Button(button_frame, text="🔄 Reset", command=reset_clip)
    reset_btn.pack(side="left", padx=4)
    
    # Apply button
    def apply_changes():
        """Apply changes and close."""
        if callable(on_apply):
            on_apply(clip)
        win.destroy()
    
    apply_btn = ttk.Button(button_frame, text="✓ Apply & Close", command=apply_changes)
    apply_btn.pack(side="left", padx=4)
    
    # Close button
    close_btn = ttk.Button(button_frame, text="✕ Close", command=win.destroy)
    close_btn.pack(side="left", padx=4)

    # Enable mousewheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def _on_closing():
        canvas.unbind_all("<MouseWheel>")
        win.destroy()
    
    win.protocol("WM_DELETE_WINDOW", _on_closing)

    win.transient(parent)
    win.grab_set()
    parent.wait_window(win)

