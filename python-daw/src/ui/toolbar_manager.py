"""Toolbar manager for transport controls and settings."""

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover
    tk = None
    ttk = None


class ToolbarManager:
    """Manages the application toolbar with transport and settings."""

    def __init__(self, parent, project=None, callbacks=None):
        self.parent = parent
        self.project = project
        self.callbacks = callbacks or {}
        
        # State variables
        self.loop_var = None
        self.snap_var = None
        self.bpm_var = None
        self.grid_var = None
        self.time_var = None
        
        self.toolbar = None
        self.bpm_change_job = None

    def build_toolbar(self):
        """Build the toolbar UI."""
        if self.parent is None or tk is None:
            return
            
        self.toolbar = ttk.Frame(self.parent, style="Toolbar.TFrame", height=48)
        self.toolbar.pack(fill="x", side="top")
        self.toolbar.pack_propagate(False)
        
        self._build_transport_controls()
        self._add_separator()
        self._build_track_controls()
        self._add_separator()
        self._build_zoom_controls()
        self._add_separator()
        self._build_loop_controls()
        self._add_separator()
        self._build_tempo_controls()
        self._build_time_display()

    def _build_transport_controls(self):
        """Build play/stop buttons."""
        ttk.Button(
            self.toolbar, text="▶ Play",
            command=self.callbacks.get('play', lambda: None),
            style="Tool.TButton", width=10
        ).pack(side="left", padx=(12, 4), pady=8)
        
        ttk.Button(
            self.toolbar, text="■ Stop",
            command=self.callbacks.get('stop', lambda: None),
            style="Tool.TButton", width=10
        ).pack(side="left", padx=4, pady=8)
    
    def _build_track_controls(self):
        """Build track management controls."""
        ttk.Button(
            self.toolbar, text="+ Track",
            command=self.callbacks.get('add_track', lambda: None),
            style="Tool.TButton", width=10
        ).pack(side="left", padx=4, pady=8)

    def _build_zoom_controls(self):
        """Build zoom controls."""
        ttk.Label(
            self.toolbar, text="Zoom:",
            style="Sidebar.TLabel"
        ).pack(side="left", padx=(0, 6))
        
        ttk.Button(
            self.toolbar, text="−",
            command=self.callbacks.get('zoom_out', lambda: None),
            style="Tool.TButton", width=3
        ).pack(side="left", padx=2)
        
        ttk.Button(
            self.toolbar, text="+",
            command=self.callbacks.get('zoom_in', lambda: None),
            style="Tool.TButton", width=3
        ).pack(side="left", padx=2)
        
        ttk.Button(
            self.toolbar, text="Fit",
            command=self.callbacks.get('zoom_reset', lambda: None),
            style="Tool.TButton", width=5
        ).pack(side="left", padx=(2, 8))

    def _build_loop_controls(self):
        """Build loop controls."""
        self.loop_var = tk.BooleanVar(value=False)
        
        # Solo checkbox loop - i marker si trascinano sulla timeline
        loop_check = ttk.Checkbutton(
            self.toolbar, text="🔁 Loop",
            variable=self.loop_var,
            command=self.callbacks.get('loop_toggle', lambda: None),
            style="Tool.TButton"
        )
        loop_check.pack(side="left", padx=(0, 8))

    def _build_tempo_controls(self):
        """Build tempo and grid controls."""
        # BPM
        current_bpm = int(getattr(self.project, "bpm", 120))
        self.bpm_var = tk.IntVar(value=current_bpm)
        self.bpm_var.trace_add("write", lambda *args: self._on_bpm_change())
        
        ttk.Label(
            self.toolbar, text="BPM:",
            style="Sidebar.TLabel"
        ).pack(side="left", padx=(0, 6))
        
        bpm_spin = tk.Spinbox(
            self.toolbar, from_=40, to=240,
            textvariable=self.bpm_var, width=5,
            bg="#1a1a1a", fg="#f5f5f5",
            buttonbackground="#3b82f6", relief="flat",
            font=("Segoe UI", 9)
        )
        bpm_spin.pack(side="left", padx=(0, 8))
        
        # Snap
        self.snap_var = tk.BooleanVar(value=False)
        snap_chk = ttk.Checkbutton(
            self.toolbar, text="Snap",
            variable=self.snap_var,
            command=self.callbacks.get('snap_toggle', lambda: None)
        )
        snap_chk.pack(side="left", padx=(0, 8))
        
        # Grid
        ttk.Label(
            self.toolbar, text="Grid:",
            style="Sidebar.TLabel"
        ).pack(side="left", padx=(0, 6))
        
        self.grid_var = tk.StringVar(value="1/4")
        grid_combo = ttk.Combobox(
            self.toolbar, textvariable=self.grid_var,
            values=["1/1 (Bar)", "1/2", "1/4", "1/8", "1/16"],
            state="readonly", width=8
        )
        grid_combo.pack(side="left")
        grid_combo.bind(
            "<<ComboboxSelected>>",
            self.callbacks.get('grid_change', lambda e: None)
        )
        grid_combo.current(2)

    def _build_time_display(self):
        """Build time display."""
        self.time_var = tk.StringVar(value="00:00.000")
        time_display = ttk.Label(
            self.toolbar, textvariable=self.time_var,
            style="Sidebar.TLabel",
            font=("Consolas", 14, "bold")
        )
        time_display.pack(side="right", padx=12)

    def _add_separator(self):
        """Add visual separator."""
        sep = ttk.Frame(self.toolbar, style="Toolbar.TFrame", width=2)
        sep.pack(side="left", fill="y", padx=12, pady=8)

    def _on_bpm_change(self):
        """Handle BPM change with debouncing."""
        if self.toolbar is not None and self.bpm_change_job is not None:
            try:
                self.toolbar.after_cancel(self.bpm_change_job)
            except Exception:
                pass
        
        if self.toolbar is not None:
            self.bpm_change_job = self.toolbar.after(
                300,
                lambda: self.callbacks.get('bpm_change', lambda: None)()
            )

    def update_time(self, time_seconds):
        """Update time display."""
        if self.time_var is None:
            return
            
        mins = int(time_seconds // 60)
        secs = time_seconds - mins * 60
        millis = int((secs - int(secs)) * 1000)
        self.time_var.set(f"{mins:02d}:{int(secs):02d}.{millis:03d}")

    def get_bpm(self):
        """Get current BPM value."""
        if self.bpm_var is None:
            return 120
        return self.bpm_var.get()

    def get_snap_enabled(self):
        """Get snap enabled state."""
        if self.snap_var is None:
            return False
        return self.snap_var.get()

    def get_loop_enabled(self):
        """Get loop enabled state."""
        if self.loop_var is None:
            return False
        return self.loop_var.get()

    def set_loop_enabled(self, enabled):
        """Set loop enabled state."""
        if self.loop_var is not None:
            self.loop_var.set(enabled)

    def get_grid_division(self):
        """Get grid division value."""
        if self.grid_var is None:
            return 0.25
            
        grid_str = self.grid_var.get()
        if "(" in grid_str:
            grid_str = grid_str.split()[0]
        
        try:
            parts = grid_str.split("/")
            if len(parts) == 2:
                return float(parts[0]) / float(parts[1])
        except Exception:
            pass
        
        return 0.25
