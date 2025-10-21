try:
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover
    tk = None
    ttk = None


class PianoRollEditor:
    """Very simple piano roll for editing MidiClip notes.

    Features:
    - Grid of pitches (rows) and time (columns)
    - Left-click to add a note at grid cell (fixed duration)
    - Right-click to remove note at position
    - Updates provided MidiClip.notes in place and calls on_apply when closed
    """

    def __init__(self, parent, midi_clip, on_apply=None, px_per_sec=200, pitch_min=48, pitch_max=72):
        self.parent = parent
        self.clip = midi_clip
        self.on_apply = on_apply
        self.px_per_sec = px_per_sec
        self.pitch_min = int(pitch_min)
        self.pitch_max = int(pitch_max)
        self.grid_step = 0.25  # seconds per column (quarter second)
        self.note_dur = 0.25   # fixed note duration in seconds
        self._win = None
        self._canvas = None
        self._notes_ids = {}

    def show(self):
        if tk is None:
            return
        self._win = tk.Toplevel(self.parent)
        self._win.title(f"Piano Roll - {getattr(self.clip, 'name', 'MIDI')}")
        self._win.geometry("900x400")
        self._win.configure(bg="#1e1e1e")
        self._win.protocol("WM_DELETE_WINDOW", self._close)

        # Toolbar
        toolbar = ttk.Frame(self._win)
        toolbar.pack(fill="x")
        ttk.Label(toolbar, text="Grid: 1/4s").pack(side="left", padx=8)
        ttk.Button(toolbar, text="Close", command=self._close).pack(side="right", padx=8)

        # Canvas with scroll
        frame = ttk.Frame(self._win)
        frame.pack(fill="both", expand=True)
        self._canvas = tk.Canvas(frame, bg="#0d0d0d", highlightthickness=0)
        vs = ttk.Scrollbar(frame, orient="vertical", command=self._canvas.yview)
        hs = ttk.Scrollbar(frame, orient="horizontal", command=self._canvas.xview)
        self._canvas.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        self._canvas.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self._canvas.bind("<Button-1>", self._on_left_click)
        self._canvas.bind("<Button-3>", self._on_right_click)

        self._redraw()

    def _close(self):
        if callable(self.on_apply):
            try:
                self.on_apply(self.clip)
            except Exception:
                pass
        if self._win is not None:
            try:
                self._win.destroy()
            except Exception:
                pass
            self._win = None

    # --- Drawing ---
    def _content_size(self):
        # Width based on clip length
        w = max(800, int(self.clip.length_seconds * self.px_per_sec))
        # Height based on pitch range
        rows = self.pitch_max - self.pitch_min + 1
        h = max(300, rows * 16)
        return w, h

    def _redraw(self):
        if self._canvas is None:
            return
        self._canvas.delete("all")
        w, h = self._content_size()
        self._canvas.configure(scrollregion=(0, 0, w, h))
        # Grid vertical lines (time)
        total_secs = int(self.clip.length_seconds) + 4
        for s in [i * self.grid_step for i in range(int(total_secs / self.grid_step) + 1)]:
            x = int(s * self.px_per_sec)
            color = "#1e40af" if abs((s / self.grid_step) % 4) < 1e-6 else "#111827"
            self._canvas.create_line(x, 0, x, h, fill=color)
        # Grid horizontal lines (pitches)
        for p in range(self.pitch_min, self.pitch_max + 1):
            y = self._pitch_to_y(p)
            col = "#111827" if (p % 12) in (1, 3, 6, 8, 10) else "#0b1220"  # darker for black keys
            self._canvas.create_rectangle(0, y, w, y + 16, fill=col, outline="#0f172a")

        # Draw notes
        self._notes_ids.clear()
        color = getattr(self.clip, 'color', '#22c55e') or '#22c55e'
        for n in getattr(self.clip, 'notes', []) or []:
            nx0 = int(n.start * self.px_per_sec)
            nx1 = int((n.start + n.duration) * self.px_per_sec)
            ny = self._pitch_to_y(int(n.pitch))
            rid = self._canvas.create_rectangle(nx0, ny + 2, nx1, ny + 14, fill=color, outline="#052e16")
            self._notes_ids[rid] = n

    def _pitch_to_y(self, p: int) -> int:
        p = max(self.pitch_min, min(self.pitch_max, int(p)))
        row = self.pitch_max - p
        return int(row * 16)

    def _xy_to_pitch_time(self, x, y):
        t = max(0.0, x / float(self.px_per_sec))
        # quantize time to grid
        q = round(t / self.grid_step) * self.grid_step
        row = int(y // 16)
        pitch = self.pitch_max - row
        return int(pitch), max(0.0, q)

    # --- Events ---
    def _on_left_click(self, event):
        if self._canvas is None:
            return
        x = self._canvas.canvasx(event.x)
        y = self._canvas.canvasy(event.y)
        p, t = self._xy_to_pitch_time(x, y)
        # add note
        try:
            from src.midi.note import MidiNote
        except Exception:
            MidiNote = None
        if MidiNote is None:
            return
        self.clip.notes.append(MidiNote(pitch=p, start=t, duration=self.note_dur, velocity=100))
        self._redraw()

    def _on_right_click(self, event):
        if self._canvas is None:
            return
        x = self._canvas.canvasx(event.x)
        y = self._canvas.canvasy(event.y)
        p, t = self._xy_to_pitch_time(x, y)
        # remove closest note at this pitch near time within one grid step
        target = None
        best = 999999
        for n in list(getattr(self.clip, 'notes', []) or []):
            if int(n.pitch) != int(p):
                continue
            dt = abs(n.start - t)
            if dt < best and dt <= self.grid_step * 0.6:
                best = dt
                target = n
        if target is not None:
            try:
                self.clip.notes.remove(target)
            except ValueError:
                pass
            self._redraw()
