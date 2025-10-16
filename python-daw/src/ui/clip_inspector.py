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
    """Open a small editor for a single AudioClip.

    Parameters:
        parent: Tk parent window
        clip: AudioClip instance to edit (in-place)
        on_apply: optional callback invoked with the updated clip
    """
    if tk is None or ttk is None or parent is None or clip is None:
        return

    win = tk.Toplevel(parent)
    win.title(f"Clip Inspector - {getattr(clip, 'name', 'clip')}")
    win.resizable(False, False)
    win.configure(bg="#1e1e1e")

    frm = ttk.Frame(win, padding=10)
    frm.grid(sticky="nsew")

    def add_row(r, label, widget):
        ttk.Label(frm, text=label).grid(row=r, column=0, sticky="e", padx=6, pady=4)
        widget.grid(row=r, column=1, sticky="we", padx=6, pady=4)

    # Entries
    e_start = ttk.Entry(frm)
    e_start.insert(0, f"{float(getattr(clip, 'start_offset', 0.0)):.3f}")

    e_end = ttk.Entry(frm)
    e_end.insert(0, f"{float(getattr(clip, 'end_offset', 0.0)):.3f}")

    e_fi = ttk.Entry(frm)
    e_fi.insert(0, f"{float(getattr(clip, 'fade_in', 0.0)):.3f}")

    cb_fi = ttk.Combobox(frm, values=FADE_SHAPES, state="readonly")
    fi_shape = getattr(clip, 'fade_in_shape', 'linear') or 'linear'
    cb_fi.set(fi_shape if fi_shape in FADE_SHAPES else 'linear')

    e_fo = ttk.Entry(frm)
    e_fo.insert(0, f"{float(getattr(clip, 'fade_out', 0.0)):.3f}")

    cb_fo = ttk.Combobox(frm, values=FADE_SHAPES, state="readonly")
    fo_shape = getattr(clip, 'fade_out_shape', 'linear') or 'linear'
    cb_fo.set(fo_shape if fo_shape in FADE_SHAPES else 'linear')

    e_pitch = ttk.Entry(frm)
    e_pitch.insert(0, f"{float(getattr(clip, 'pitch_semitones', 0.0)):.3f}")

    add_row(0, "Start offset (s)", e_start)
    add_row(1, "End offset (s)", e_end)
    add_row(2, "Fade-in (s)", e_fi)
    add_row(3, "Fade-in shape", cb_fi)
    add_row(4, "Fade-out (s)", e_fo)
    add_row(5, "Fade-out shape", cb_fo)
    add_row(6, "Pitch (semitones)", e_pitch)

    btns = ttk.Frame(frm)
    btns.grid(row=7, column=0, columnspan=2, pady=(10, 0))

    def apply_and_close():
        try:
            clip.start_offset = max(0.0, float(e_start.get()))
            clip.end_offset = max(0.0, float(e_end.get()))
            clip.fade_in = max(0.0, float(e_fi.get()))
            clip.fade_in_shape = cb_fi.get()
            clip.fade_out = max(0.0, float(e_fo.get()))
            clip.fade_out_shape = cb_fo.get()
            clip.pitch_semitones = float(e_pitch.get())
            if callable(on_apply):
                on_apply(clip)
        except Exception as ex:
            print(f"Clip Inspector: invalid input: {ex}")
        win.destroy()

    ttk.Button(btns, text="Apply", command=apply_and_close).grid(row=0, column=0, padx=6)
    ttk.Button(btns, text="Close", command=win.destroy).grid(row=0, column=1, padx=6)

    win.transient(parent)
    win.grab_set()
    parent.wait_window(win)
