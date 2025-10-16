try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except Exception:  # pragma: no cover
    tk = None
    ttk = None


class MainWindow:
    def __init__(self, project=None, mixer=None, transport=None, timeline=None, player=None):
        self.title = "Digital Audio Workstation"
        self.is_open = False
        self.project = project
        self.mixer = mixer
        self.transport = transport
        self.timeline = timeline
        self.player = player
        self._root = None
        self._track_list = None
        self._volume_var = None
        self._time_var = None
        # Timeline canvas state
        self._timeline_canvas = None
        self._timeline_scroll = None
        self._cursor_id = None
        self._px_per_sec = 200  # pixels per second
        self._track_height = 40
        self._timeline_left_margin = 60
        
        # Clip interaction state
        self._selected_clip = None  # (track_index, clip_object)
        self._drag_data = None  # {"clip": clip, "track": idx, "start_x": x, "start_time": t}
        self._resize_data = None  # {"clip": clip, "track": idx, "edge": "left"|"right", "orig_time": t}
        self._clip_canvas_ids = {}  # {canvas_id: (track_idx, clip_obj)}
        
        # Loop state
        self._loop_var = None  # BooleanVar for loop on/off
        
        # Grid state
        self._snap_var = None  # BooleanVar for snap to grid
        self._bpm_var = None  # IntVar for BPM
        self._grid_division = 0.25  # quarter notes by default

    def show(self):
        if tk is None:
            # Fallback to console mode
            self.is_open = True
            print(f"{self.title} (console mode) is now open.")
            return

        try:
            self._root = tk.Tk()
        except Exception as e:
            # Fallback to console mode if GUI cannot be created
            print(f"Warning: GUI not available ({e}). Falling back to console mode.")
            self.is_open = True
            print(f"{self.title} (console mode) is now open.")
            return

        self._root.title(self.title)
        self._root.geometry("1200x700")
        self._root.configure(bg="#1e1e1e")

        # Professional dark theme
        try:
            style = ttk.Style(self._root)
            if "clam" in style.theme_names():
                style.theme_use("clam")
            
            # Base colors
            style.configure("TFrame", background="#1e1e1e")
            style.configure("TLabel", background="#1e1e1e", foreground="#f5f5f5", font=("Segoe UI", 9))
            style.configure("TButton", 
                          background="#3b82f6", 
                          foreground="#ffffff",
                          borderwidth=0,
                          focuscolor="none",
                          padding=(12, 6),
                          font=("Segoe UI", 9, "bold"))
            style.map("TButton",
                     background=[("active", "#2563eb"), ("pressed", "#1d4ed8")])
            
            # Sidebar style
            style.configure("Sidebar.TFrame", background="#2d2d2d")
            style.configure("Sidebar.TLabel", background="#2d2d2d", foreground="#f5f5f5", font=("Segoe UI", 9))
            style.configure("SidebarTitle.TLabel", background="#2d2d2d", foreground="#f5f5f5", font=("Segoe UI", 11, "bold"))
            
            # Toolbar
            style.configure("Toolbar.TFrame", background="#252525")
            style.configure("Tool.TButton", 
                          background="#404040",
                          foreground="#f5f5f5",
                          padding=(10, 5),
                          font=("Segoe UI", 9))
            style.map("Tool.TButton",
                     background=[("active", "#4a4a4a"), ("pressed", "#353535")])
            
            # Status bar
            style.configure("Status.TLabel", 
                          background="#252525", 
                          foreground="#a0a0a0",
                          font=("Segoe UI", 8),
                          padding=(8, 4))
            
            # Scales
            style.configure("Horizontal.TScale", 
                          background="#2d2d2d",
                          troughcolor="#1a1a1a",
                          borderwidth=0)
            
            # Meters
            style.configure("Meter.Horizontal.TProgressbar", 
                          troughcolor="#1a1a1a",
                          background="#10b981",
                          borderwidth=0,
                          thickness=16)
        except Exception:
            pass

        # Menu bar
        menubar = tk.Menu(self._root, bg="#252525", fg="#f5f5f5", activebackground="#3b82f6", activeforeground="#ffffff", borderwidth=0)
        file_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="#f5f5f5", activebackground="#3b82f6", activeforeground="#ffffff")
        file_menu.add_command(label="New Project", command=lambda: None, accelerator="Ctrl+N")
        file_menu.add_command(label="Open Project...", command=lambda: None, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Project", command=lambda: None, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Import Audio...", command=self._import_audio_dialog, accelerator="Ctrl+I")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.close, accelerator="Alt+F4")
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="#f5f5f5", activebackground="#3b82f6", activeforeground="#ffffff")
        view_menu.add_command(label="Zoom In", command=lambda: self._zoom(1.25), accelerator="+")
        view_menu.add_command(label="Zoom Out", command=lambda: self._zoom(0.8), accelerator="-")
        view_menu.add_command(label="Fit to Window", command=lambda: self._zoom_reset(), accelerator="0")
        menubar.add_cascade(label="View", menu=view_menu)

        transport_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="#f5f5f5", activebackground="#3b82f6", activeforeground="#ffffff")
        transport_menu.add_command(label="▶ Play", command=self._on_play, accelerator="Space")
        transport_menu.add_command(label="■ Stop", command=self._on_stop)
        menubar.add_cascade(label="Transport", menu=transport_menu)

        help_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="#f5f5f5", activebackground="#3b82f6", activeforeground="#ffffff")
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", "Python DAW\nProfessional Digital Audio Workstation\nVersion 1.0"))
        menubar.add_cascade(label="Help", menu=help_menu)
        self._root.config(menu=menubar)
        
        # Toolbar
        toolbar = ttk.Frame(self._root, style="Toolbar.TFrame", height=48)
        toolbar.pack(fill="x", side="top")
        toolbar.pack_propagate(False)
        
        # Transport controls with icons
        ttk.Button(toolbar, text="▶ Play", command=self._on_play, style="Tool.TButton", width=10).pack(side="left", padx=(12, 4), pady=8)
        ttk.Button(toolbar, text="■ Stop", command=self._on_stop, style="Tool.TButton", width=10).pack(side="left", padx=4, pady=8)
        
        # Separator
        sep1 = ttk.Frame(toolbar, style="Toolbar.TFrame", width=2)
        sep1.pack(side="left", fill="y", padx=12, pady=8)
        
        # Zoom controls
        ttk.Label(toolbar, text="Zoom:", style="Sidebar.TLabel").pack(side="left", padx=(0, 6))
        ttk.Button(toolbar, text="−", command=lambda: self._zoom(0.8), style="Tool.TButton", width=3).pack(side="left", padx=2)
        ttk.Button(toolbar, text="+", command=lambda: self._zoom(1.25), style="Tool.TButton", width=3).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Fit", command=self._zoom_reset, style="Tool.TButton", width=5).pack(side="left", padx=(2, 8))
        
        # Separator
        sep2 = ttk.Frame(toolbar, style="Toolbar.TFrame", width=2)
        sep2.pack(side="left", fill="y", padx=12, pady=8)
        
        # Loop controls
        self._loop_var = tk.BooleanVar(value=False)
        loop_check = ttk.Checkbutton(
            toolbar, 
            text="Loop", 
            variable=self._loop_var, 
            command=self._on_loop_toggle,
            style="Tool.TButton"
        )
        loop_check.pack(side="left", padx=(0, 4))
        ttk.Button(toolbar, text="[", command=self._set_loop_start, style="Tool.TButton", width=3).pack(side="left", padx=2)
        ttk.Button(toolbar, text="]", command=self._set_loop_end, style="Tool.TButton", width=3).pack(side="left", padx=(2, 8))
        
        # Time display on the right
        self._time_var = tk.StringVar(value="00:00.000")
        time_display = ttk.Label(toolbar, textvariable=self._time_var, style="Sidebar.TLabel", font=("Consolas", 14, "bold"))
        time_display.pack(side="right", padx=12)

        # Main container
        main_container = ttk.Frame(self._root)
        main_container.pack(fill="both", expand=True)
        
        # LEFT SIDEBAR (300px width)
        sidebar = ttk.Frame(main_container, style="Sidebar.TFrame", width=300)
        sidebar.pack(fill="y", side="left")
        sidebar.pack_propagate(False)
        
        # Project info in sidebar
        project_name = getattr(self.project, "name", "Untitled Project")
        proj_header = ttk.Frame(sidebar, style="Sidebar.TFrame")
        proj_header.pack(fill="x", padx=12, pady=(12, 8))
        ttk.Label(proj_header, text="PROJECT", style="SidebarTitle.TLabel", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        ttk.Label(proj_header, text=project_name, style="Sidebar.TLabel", font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))
        
        # Tempo & Grid section
        tempo_frame = ttk.Frame(sidebar, style="Sidebar.TFrame")
        tempo_frame.pack(fill="x", padx=12, pady=(12, 8))
        
        ttk.Label(tempo_frame, text="TEMPO & GRID", style="SidebarTitle.TLabel").pack(anchor="w", pady=(0, 8))
        
        # BPM control
        bpm_row = ttk.Frame(tempo_frame, style="Sidebar.TFrame")
        bpm_row.pack(fill="x", pady=4)
        ttk.Label(bpm_row, text="BPM", style="Sidebar.TLabel", width=8).pack(side="left")
        
        current_bpm = int(getattr(self.project, "bpm", 120))
        self._bpm_var = tk.IntVar(value=current_bpm)
        bpm_spinbox = tk.Spinbox(
            bpm_row,
            from_=40,
            to=240,
            textvariable=self._bpm_var,
            command=self._on_bpm_change,
            width=8,
            bg="#1a1a1a",
            fg="#f5f5f5",
            buttonbackground="#3b82f6",
            relief="flat",
            font=("Segoe UI", 9)
        )
        bpm_spinbox.pack(side="left", padx=(8, 0))
        bpm_spinbox.bind("<Return>", lambda e: self._on_bpm_change())
        
        # Time signature (read-only for now)
        ts_row = ttk.Frame(tempo_frame, style="Sidebar.TFrame")
        ts_row.pack(fill="x", pady=4)
        ttk.Label(ts_row, text="Time Sig", style="Sidebar.TLabel", width=8).pack(side="left")
        ts_num = getattr(self.project, "time_signature_num", 4)
        ts_den = getattr(self.project, "time_signature_den", 4)
        ttk.Label(ts_row, text=f"{ts_num}/{ts_den}", style="Sidebar.TLabel", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(8, 0))
        
        # Snap to grid
        snap_row = ttk.Frame(tempo_frame, style="Sidebar.TFrame")
        snap_row.pack(fill="x", pady=4)
        self._snap_var = tk.BooleanVar(value=False)
        snap_check = ttk.Checkbutton(
            snap_row,
            text="Snap to Grid",
            variable=self._snap_var,
            command=self._on_snap_toggle
        )
        snap_check.pack(side="left")
        
        # Grid division selector
        grid_row = ttk.Frame(tempo_frame, style="Sidebar.TFrame")
        grid_row.pack(fill="x", pady=4)
        ttk.Label(grid_row, text="Grid", style="Sidebar.TLabel", width=8).pack(side="left")
        self._grid_var = tk.StringVar(value="1/4")
        grid_combo = ttk.Combobox(
            grid_row,
            textvariable=self._grid_var,
            values=["1/1 (Bar)", "1/2", "1/4", "1/8", "1/16"],
            state="readonly",
            width=10
        )
        grid_combo.pack(side="left", padx=(8, 0))
        grid_combo.bind("<<ComboboxSelected>>", self._on_grid_change)
        grid_combo.current(2)  # 1/4 default
        
        # Tracks section
        tracks_header = ttk.Frame(sidebar, style="Sidebar.TFrame")
        tracks_header.pack(fill="x", padx=12, pady=(16, 4))
        ttk.Label(tracks_header, text="TRACKS", style="SidebarTitle.TLabel").pack(side="left")
        
        # Add Track and Add Clip buttons
        btn_container = ttk.Frame(tracks_header, style="Sidebar.TFrame")
        btn_container.pack(side="right")
        ttk.Button(btn_container, text="+ Track", command=self._add_track_dialog, style="Tool.TButton", width=8).pack(side="left", padx=(0, 4))
        ttk.Button(btn_container, text="+ Clip", command=self._add_dummy_clip, style="Tool.TButton", width=7).pack(side="left")
        
        tracks_list_frame = ttk.Frame(sidebar, style="Sidebar.TFrame")
        tracks_list_frame.pack(fill="both", expand=True, padx=12, pady=4)
        
        self._track_list = tk.Listbox(
            tracks_list_frame, 
            height=8,
            bg="#1a1a1a",
            fg="#f5f5f5",
            selectbackground="#3b82f6",
            selectforeground="#ffffff",
            borderwidth=0,
            highlightthickness=0,
            font=("Segoe UI", 9),
            activestyle="none"
        )
        self._track_list.pack(fill="both", expand=True)
        self._track_list.bind("<<ListboxSelect>>", self._on_select_track)
        
        # Track controls section
        controls_frame = ttk.Frame(sidebar, style="Sidebar.TFrame")
        controls_frame.pack(fill="x", padx=12, pady=(12, 8))
        
        ttk.Label(controls_frame, text="TRACK CONTROLS", style="SidebarTitle.TLabel").pack(anchor="w", pady=(0, 8))
        
        # Volume control
        vol_row = ttk.Frame(controls_frame, style="Sidebar.TFrame")
        vol_row.pack(fill="x", pady=4)
        ttk.Label(vol_row, text="Volume", style="Sidebar.TLabel", width=8).pack(side="left")
        self._volume_var = tk.DoubleVar(value=1.0)
        vol_scale = ttk.Scale(
            vol_row,
            from_=0.0,
            to=1.0,
            orient="horizontal",
            variable=self._volume_var,
            command=self._on_volume_change,
        )
        vol_scale.pack(side="left", fill="x", expand=True, padx=(8, 0))
        
        # Pan control
        pan_row = ttk.Frame(controls_frame, style="Sidebar.TFrame")
        pan_row.pack(fill="x", pady=4)
        ttk.Label(pan_row, text="Pan", style="Sidebar.TLabel", width=8).pack(side="left")
        self._pan_var = tk.DoubleVar(value=0.0)
        pan_scale = ttk.Scale(
            pan_row,
            from_=-1.0,
            to=1.0,
            orient="horizontal",
            variable=self._pan_var,
            command=self._on_pan_change,
        )
        pan_scale.pack(side="left", fill="x", expand=True, padx=(8, 0))
        
        # Meters section
        meters_frame = ttk.Frame(sidebar, style="Sidebar.TFrame")
        meters_frame.pack(fill="x", padx=12, pady=(12, 16))
        
        ttk.Label(meters_frame, text="OUTPUT LEVEL", style="SidebarTitle.TLabel").pack(anchor="w", pady=(0, 8))
        
        meter_L_row = ttk.Frame(meters_frame, style="Sidebar.TFrame")
        meter_L_row.pack(fill="x", pady=2)
        ttk.Label(meter_L_row, text="L", style="Sidebar.TLabel", width=2, font=("Segoe UI", 9, "bold")).pack(side="left")
        self._meter_L = ttk.Progressbar(meter_L_row, mode="determinate", maximum=1.0, style="Meter.Horizontal.TProgressbar")
        self._meter_L.pack(side="left", fill="x", expand=True, padx=(8, 0))
        
        meter_R_row = ttk.Frame(meters_frame, style="Sidebar.TFrame")
        meter_R_row.pack(fill="x", pady=2)
        ttk.Label(meter_R_row, text="R", style="Sidebar.TLabel", width=2, font=("Segoe UI", 9, "bold")).pack(side="left")
        self._meter_R = ttk.Progressbar(meter_R_row, mode="determinate", maximum=1.0, style="Meter.Horizontal.TProgressbar")
        self._meter_R.pack(side="left", fill="x", expand=True, padx=(8, 0))

        
        # RIGHT SIDE: Timeline area
        timeline_container = ttk.Frame(main_container)
        timeline_container.pack(fill="both", expand=True, side="left")
        
        # Timeline canvas
        self._build_timeline_canvas(timeline_container)
        self._redraw_timeline()

        # Populate track list from mixer (if provided)
        self._populate_tracks()

        # Status bar at bottom
        status_bar = ttk.Frame(self._root, style="Toolbar.TFrame", height=28)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)
        
        self._status = tk.StringVar(value="● Ready")
        status_lbl = ttk.Label(status_bar, textvariable=self._status, style="Status.TLabel")
        status_lbl.pack(side="left", padx=8)
        
        zoom_info = ttk.Label(status_bar, text="Zoom: 1.00x", style="Status.TLabel")
        zoom_info.pack(side="right", padx=8)
        self._zoom_label = zoom_info

        # Key bindings
        self._bind_keys()

        self.is_open = True
        print("GUI window created. If you don't see it, check the taskbar and ensure it's not behind other windows.")

    def run(self):
        if tk is None:
            # Console fallback loop to keep app alive until Ctrl+C
            print("Running in console mode. Press Ctrl+C to exit.")
            try:
                import time
                while True:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                self.close()
            return

        if self._root is None:
            self.show()
        try:
            self._root.mainloop()
        finally:
            self.close()

    def close(self):
        self.is_open = False
        # Ensure Tk root is destroyed if exists
        if self._root is not None:
            try:
                self._root.destroy()
            except Exception:
                pass
            self._root = None

    # ----- helpers -----
    def _populate_tracks(self):
        if self._track_list is None or self.mixer is None:
            return
        self._track_list.delete(0, tk.END)
        for idx, t in enumerate(self.mixer.tracks if hasattr(self.mixer, "tracks") else []):
            name = t.get("name", f"Track {idx+1}")
            clips = 0
            if self.timeline is not None:
                try:
                    clips = self.timeline.count_clips_for_track(idx)
                except Exception:
                    clips = 0
            self._track_list.insert(tk.END, f"{name}  (clips: {clips})")
        # refresh timeline as track/clip counts may change
        self._redraw_timeline()

    def _current_track_index(self):
        if self._track_list is None:
            return None
        sel = self._track_list.curselection()
        if not sel:
            return None
        return int(sel[0])

    def _on_select_track(self, _event=None):
        idx = self._current_track_index()
        if idx is None or self.mixer is None:
            return
        vol = float(self.mixer.tracks[idx].get("volume", 1.0))
        if self._volume_var is not None:
            self._volume_var.set(vol)
        pan = float(self.mixer.tracks[idx].get("pan", 0.0))
        if hasattr(self, "_pan_var") and self._pan_var is not None:
            self._pan_var.set(pan)

    def _on_volume_change(self, _value=None):
        idx = self._current_track_index()
        if idx is None or self.mixer is None or self._volume_var is None:
            return
        try:
            self.mixer.tracks[idx]["volume"] = float(self._volume_var.get())
            if hasattr(self, "_status") and self._status is not None:
                self._status.set(f"Set volume of track {idx+1} to {self.mixer.tracks[idx]['volume']:.2f}")
        except Exception:
            pass

    def _on_pan_change(self, _value=None):
        idx = self._current_track_index()
        if idx is None or self.mixer is None or not hasattr(self, "_pan_var"):
            return
        try:
            # Clamp to [-1, 1]
            p = float(self._pan_var.get())
            if p < -1.0:
                p = -1.0
            if p > 1.0:
                p = 1.0
            self.mixer.tracks[idx]["pan"] = p
            if hasattr(self, "_status") and self._status is not None:
                self._status.set(f"Set pan of track {idx+1} to {p:.2f}")
        except Exception:
            pass

    def _on_play(self):
        if self.transport is not None:
            try:
                self.transport.play()
                if hasattr(self, "_status") and self._status is not None:
                    self._status.set("▶ Playing")
            except Exception as e:
                print(f"Play error: {e}")
        # start updating time label if player available
        if self.player is not None and hasattr(self.player, "is_playing"):
            self._schedule_time_update()
            self._schedule_meter_update()

    def _on_stop(self):
        if self.transport is not None:
            try:
                self.transport.stop()
                if hasattr(self, "_status") and self._status is not None:
                    self._status.set("■ Stopped")
            except Exception as e:
                print(f"Stop error: {e}")
        # stop updating time label
        if self._root is not None:
            try:
                self._root.after_cancel(getattr(self, "_time_job", None))
            except Exception:
                pass

    def _on_loop_toggle(self):
        """Toggle loop on/off."""
        if self.player is None:
            return
        enabled = self._loop_var.get()
        loop_info = self.player.get_loop()
        self.player.set_loop(enabled, loop_info[1], loop_info[2])
        self._redraw_timeline()  # redraw to show/hide loop markers
        status = "Loop ON" if enabled else "Loop OFF"
        if hasattr(self, "_status") and self._status is not None:
            self._status.set(status)
        print(f"Loop {status}")

    def _set_loop_start(self):
        """Set loop start to current playback position."""
        if self.player is None:
            return
        current_time = self.player.get_current_time()
        current_time = self._snap_time(current_time)  # Apply snap
        loop_info = self.player.get_loop()
        self.player.set_loop(loop_info[0], current_time, loop_info[2])
        self._redraw_timeline()
        print(f"Loop start set to {current_time:.3f}s")

    def _set_loop_end(self):
        """Set loop end to current playback position."""
        if self.player is None:
            return
        current_time = self.player.get_current_time()
        current_time = self._snap_time(current_time)  # Apply snap
        loop_info = self.player.get_loop()
        self.player.set_loop(loop_info[0], loop_info[1], current_time)
        self._redraw_timeline()
        print(f"Loop end set to {current_time:.3f}s")

    def _on_bpm_change(self):
        """Update project BPM."""
        if self.project is None or self._bpm_var is None:
            return
        try:
            new_bpm = self._bpm_var.get()
            self.project.bpm = float(new_bpm)
            self._redraw_timeline()  # redraw grid
            print(f"BPM set to {new_bpm}")
        except Exception as e:
            print(f"BPM change error: {e}")

    def _on_snap_toggle(self):
        """Toggle snap to grid."""
        enabled = self._snap_var.get() if self._snap_var else False
        status = "ON" if enabled else "OFF"
        print(f"Snap to grid: {status}")
        self._redraw_timeline()

    def _on_grid_change(self, event=None):
        """Change grid division."""
        if self._grid_var is None:
            return
        grid_str = self._grid_var.get()
        # Parse grid string (e.g., "1/4" or "1/1 (Bar)")
        if "(" in grid_str:
            grid_str = grid_str.split()[0]
        
        try:
            parts = grid_str.split("/")
            if len(parts) == 2:
                self._grid_division = float(parts[0]) / float(parts[1])
                print(f"Grid division set to {grid_str}")
                self._redraw_timeline()
        except Exception as e:
            print(f"Grid change error: {e}")

    def _snap_time(self, time: float) -> float:
        """Snap time to grid if snap is enabled."""
        if self.project is None or self._snap_var is None:
            return time
        if not self._snap_var.get():
            return time
        return self.project.snap_to_grid(time, self._grid_division)

    def _schedule_time_update(self):
        if self._root is None or self._time_var is None:
            return
        # Each 100ms, update time readout
        try:
            cur = getattr(self.player, "_current_time", 0.0)
            mins = int(cur // 60)
            secs = cur - mins * 60
            millis = int((secs - int(secs)) * 1000)
            self._time_var.set(f"{mins:02d}:{int(secs):02d}.{millis:03d}")
            self._update_cursor_line(cur)
        except Exception:
            pass
        # reschedule
        self._time_job = self._root.after(100, self._schedule_time_update)

    def _schedule_meter_update(self):
        if self._root is None or not hasattr(self, "_meter_L"):
            return
        try:
            peakL = float(getattr(self.player, "_last_peak_L", 0.0)) if self.player else 0.0
            peakR = float(getattr(self.player, "_last_peak_R", 0.0)) if self.player else 0.0
            self._meter_L['value'] = max(0.0, min(1.0, peakL))
            self._meter_R['value'] = max(0.0, min(1.0, peakR))
        except Exception:
            pass
        self._root.after(100, self._schedule_meter_update)

    def _add_dummy_clip(self):
        """Adds a short 0.25s 440Hz clip at current time on selected track."""
        if self.timeline is None:
            return
        
        # Get selected track index
        track_idx = self._current_track_index()
        if track_idx is None:
            if hasattr(self, "_status"):
                self._status.set("⚠ Select a track first")
            return
        
        import math
        sr = 44100
        seconds = 0.25
        n = int(sr * seconds)
        buf = [math.sin(2 * math.pi * 440 * (i / sr)) * 0.2 for i in range(n)]
        
        # current time from player if available
        cur = 0.0
        try:
            cur = float(getattr(self.player, "_current_time", 0.0))
        except Exception:
            pass
        
        from src.audio.clip import AudioClip
        self.timeline.add_clip(track_idx, AudioClip("sine440", buf, sr, start_time=cur))
        self._populate_tracks()
        self._redraw_timeline()
        if hasattr(self, "_status"):
            track_name = self.mixer.tracks[track_idx].get("name", f"Track {track_idx+1}")
            self._status.set(f"✓ Clip added to {track_name}")
    
    def _import_audio_dialog(self):
        """Import WAV file and add to selected track."""
        if self.timeline is None or self.mixer is None:
            return
        
        track_idx = self._current_track_index()
        if track_idx is None:
            if hasattr(self, "_status"):
                self._status.set("⚠ Select a track first")
            return
        
        try:
            from tkinter import filedialog
            file_path = filedialog.askopenfilename(
                title="Import Audio",
                filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
            
            # Try to load with soundfile
            try:
                import soundfile as sf
                import numpy as np
                
                data, sr = sf.read(file_path)
                # Convert to mono if stereo
                if len(data.shape) > 1:
                    data = np.mean(data, axis=1)
                
                # Convert to list of floats
                buffer = data.tolist()
                
                # Get filename without extension
                import os
                clip_name = os.path.splitext(os.path.basename(file_path))[0]
                
                # Get current playback time or 0
                cur = 0.0
                try:
                    cur = float(getattr(self.player, "_current_time", 0.0))
                except Exception:
                    pass
                
                from src.audio.clip import AudioClip
                clip = AudioClip(clip_name, buffer, sr, start_time=cur, file_path=file_path)
                
                self.timeline.add_clip(track_idx, clip)
                self._populate_tracks()
                self._redraw_timeline()
                
                if hasattr(self, "_status"):
                    track_name = self.mixer.tracks[track_idx].get("name", f"Track {track_idx+1}")
                    self._status.set(f"✓ Imported '{clip_name}' to {track_name} ({len(buffer)} samples)")
                    
            except ImportError:
                messagebox.showerror("Import Error", "soundfile library not available.\nInstall with: pip install soundfile")
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to load audio file:\n{str(e)}")
                
        except Exception as e:
            print(f"Import error: {e}")
    
    def _add_track_dialog(self):
        """Show dialog to add a new track."""
        if self.mixer is None:
            return
        
        # Create dialog
        dialog = tk.Toplevel(self._root)
        dialog.title("Add Track")
        dialog.geometry("380x220")
        dialog.configure(bg="#2d2d2d")
        dialog.resizable(False, False)
        dialog.transient(self._root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = self._root.winfo_x() + (self._root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self._root.winfo_y() + (self._root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Dialog content
        content = ttk.Frame(dialog, style="Sidebar.TFrame")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Track name
        ttk.Label(content, text="Track Name:", style="Sidebar.TLabel").pack(anchor="w", pady=(0, 4))
        name_var = tk.StringVar(value=f"Track {self.mixer.get_track_count() + 1}")
        name_entry = ttk.Entry(content, textvariable=name_var, font=("Segoe UI", 10))
        name_entry.pack(fill="x", pady=(0, 16))
        name_entry.focus_set()
        name_entry.select_range(0, tk.END)
        
        # Track color
        ttk.Label(content, text="Track Color:", style="Sidebar.TLabel").pack(anchor="w", pady=(0, 8))
        
        color_frame = ttk.Frame(content, style="Sidebar.TFrame")
        color_frame.pack(fill="x", pady=(0, 16))
        
        colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"]
        selected_color = tk.StringVar(value=colors[self.mixer.get_track_count() % len(colors)])
        
        def make_color_button(col):
            btn = tk.Button(
                color_frame,
                bg=col,
                width=3,
                height=1,
                relief="raised",
                borderwidth=2,
                command=lambda: [selected_color.set(col), update_preview()]
            )
            return btn
        
        color_buttons = []
        for i, col in enumerate(colors):
            btn = make_color_button(col)
            btn.pack(side="left", padx=2)
            color_buttons.append(btn)
        
        # Preview
        preview_frame = ttk.Frame(content, style="Sidebar.TFrame")
        preview_frame.pack(fill="x", pady=(0, 16))
        ttk.Label(preview_frame, text="Preview:", style="Sidebar.TLabel").pack(side="left", padx=(0, 8))
        preview_canvas = tk.Canvas(preview_frame, width=120, height=24, bg="#1a1a1a", highlightthickness=0)
        preview_canvas.pack(side="left")
        
        def update_preview():
            preview_canvas.delete("all")
            preview_canvas.create_rectangle(2, 2, 118, 22, fill=selected_color.get(), outline=selected_color.get())
            preview_canvas.create_text(60, 12, text=name_var.get() or "Track", fill="#ffffff", font=("Segoe UI", 9, "bold"))
            # Highlight selected button
            for i, col in enumerate(colors):
                if col == selected_color.get():
                    color_buttons[i].config(relief="sunken", borderwidth=3)
                else:
                    color_buttons[i].config(relief="raised", borderwidth=2)
        
        update_preview()
        name_var.trace_add("write", lambda *args: update_preview())
        
        # Buttons
        btn_frame = ttk.Frame(content, style="Sidebar.TFrame")
        btn_frame.pack(fill="x")
        
        def on_ok():
            track_name = name_var.get().strip()
            if not track_name:
                track_name = f"Track {self.mixer.get_track_count() + 1}"
            
            self.mixer.add_track(name=track_name, volume=1.0, pan=0.0, color=selected_color.get())
            self._populate_tracks()
            self._redraw_timeline()
            
            # Select the new track
            if self._track_list is not None:
                self._track_list.selection_clear(0, tk.END)
                self._track_list.selection_set(len(self.mixer.tracks) - 1)
                self._track_list.see(len(self.mixer.tracks) - 1)
                self._on_select_track()
            
            if hasattr(self, "_status"):
                self._status.set(f"✓ Track '{track_name}' added")
            
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        ttk.Button(btn_frame, text="Cancel", command=on_cancel, style="Tool.TButton").pack(side="right", padx=(8, 0))
        ttk.Button(btn_frame, text="OK", command=on_ok, style="Tool.TButton").pack(side="right")
        
        # Enter key to confirm
        dialog.bind('<Return>', lambda e: on_ok())
        dialog.bind('<Escape>', lambda e: on_cancel())

    # ----- timeline canvas helpers -----
    def _build_timeline_canvas(self, parent):
        if parent is None:
            return
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(
            frame, 
            bg="#0d0d0d", 
            highlightthickness=0,
            borderwidth=0
        )
        
        # Scrollbars
        hscroll = ttk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
        vscroll = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        canvas.configure(xscrollcommand=hscroll.set, yscrollcommand=vscroll.set)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        hscroll.grid(row=1, column=0, sticky="ew")
        vscroll.grid(row=0, column=1, sticky="ns")
        
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        self._timeline_canvas = canvas
        self._timeline_scroll = hscroll
        
        # Mouse wheel for horizontal scroll with Shift
        def _on_wheel(event):
            try:
                if event.state & 0x0001:  # Shift pressed
                    delta = (event.delta or -event.num) / 120.0
                    canvas.xview_scroll(int(-delta * 3), 'units')
            except Exception:
                pass
        canvas.bind('<MouseWheel>', _on_wheel)
        
        # Mouse bindings for clip interaction
        canvas.bind('<Button-1>', self._on_timeline_click)
        canvas.bind('<B1-Motion>', self._on_timeline_drag)
        canvas.bind('<ButtonRelease-1>', self._on_timeline_release)
        canvas.bind('<Button-3>', self._on_timeline_right_click)
        canvas.bind('<Motion>', self._on_timeline_motion)

    def _compute_timeline_width(self):
        # determine max end time
        max_end = 5.0
        try:
            if self.timeline is not None:
                for _, clip in self.timeline.all_placements():
                    if getattr(clip, 'end_time', None) is not None:
                        if clip.end_time > max_end:
                            max_end = clip.end_time
        except Exception:
            pass
        width = int(self._timeline_left_margin + max_end * self._px_per_sec + 40)
        return max(width, 800)

    def _redraw_timeline(self):
        cnv = self._timeline_canvas
        if cnv is None:
            return
        cnv.delete("all")
        
        # Calculate dimensions
        width = self._compute_timeline_width()
        tracks_count = max(1, len(getattr(self.mixer, 'tracks', [])))
        ruler_h = 32
        track_h = 60
        height = ruler_h + (track_h * tracks_count) + 20
        
        cnv.config(scrollregion=(0, 0, width, height))

        # Draw ruler background
        cnv.create_rectangle(0, 0, width, ruler_h, fill="#1a1a1a", outline="")
        
        # Check if snap is enabled for musical grid
        snap_enabled = self._snap_var.get() if self._snap_var else False
        
        if snap_enabled and self.project is not None:
            # Draw musical grid (bars and beats)
            bar_duration = self.project.get_bar_duration()
            beat_duration = self.project.get_beat_duration()
            
            max_time = width / self._px_per_sec
            bar_num = 0
            
            # Draw bars
            t = 0.0
            while t < max_time:
                x = self._timeline_left_margin + t * self._px_per_sec
                
                # Bar line (thick)
                cnv.create_line(x, ruler_h, x, height, fill="#2a4a2a", width=2)
                
                # Bar number
                cnv.create_text(
                    x + 4,
                    8,
                    anchor="nw",
                    text=f"{bar_num + 1}",
                    fill="#10b981",
                    font=("Consolas", 9, "bold")
                )
                
                # Beat subdivisions within this bar
                beats_per_bar = self.project.time_signature_num
                for beat in range(1, beats_per_bar):
                    beat_time = t + beat * beat_duration
                    beat_x = self._timeline_left_margin + beat_time * self._px_per_sec
                    if beat_x < width:
                        # Beat line (thin)
                        cnv.create_line(beat_x, ruler_h, beat_x, height, fill="#1a2a1a", width=1)
                        
                        # Sub-beat ticks based on grid division
                        if self._grid_division <= 0.25:  # Show 1/8 or finer
                            for sub in [0.25, 0.5, 0.75]:
                                sub_time = t + (beat + sub) * beat_duration
                                sub_x = self._timeline_left_margin + sub_time * self._px_per_sec
                                if sub_x < width:
                                    cnv.create_line(sub_x, ruler_h, sub_x, ruler_h + 12, fill="#15251a", width=1)
                
                t += bar_duration
                bar_num += 1
        else:
            # Draw time grid (seconds) - original behavior
            total_secs = int(width / self._px_per_sec) + 1
            for sec in range(0, total_secs):
                x = self._timeline_left_margin + sec * self._px_per_sec
                
                # Major gridline
                cnv.create_line(x, ruler_h, x, height, fill="#1f1f1f", width=1)
                
                # Time label
                cnv.create_text(
                    x + 4, 
                    8, 
                    anchor="nw", 
                    text=f"{sec:02d}s", 
                    fill="#888888", 
                    font=("Consolas", 8)
                )
                
                # Minor ticks (quarters)
                for q in range(1, 4):
                    mx = x + q * (self._px_per_sec / 4.0)
                    cnv.create_line(mx, ruler_h - 8, mx, height, fill="#151515", width=1)

        # Draw track lanes with alternating background
        for i in range(tracks_count):
            y0 = ruler_h + i * track_h
            y1 = y0 + track_h
            
            # Alternating background
            bg_color = "#0d0d0d" if i % 2 == 0 else "#111111"
            cnv.create_rectangle(
                self._timeline_left_margin, 
                y0, 
                width, 
                y1, 
                fill=bg_color, 
                outline=""
            )
            
            # Track separator line
            cnv.create_line(
                self._timeline_left_margin, 
                y1, 
                width, 
                y1, 
                fill="#252525", 
                width=1
            )
            
            # Track label on left with color indicator
            label = f"Track {i+1}"
            track_color = "#3b82f6"  # default
            try:
                if self.mixer is not None and i < len(self.mixer.tracks):
                    label = self.mixer.tracks[i].get("name", label)
                    track_color = self.mixer.tracks[i].get("color", "#3b82f6")
            except Exception:
                pass
            
            cnv.create_rectangle(0, y0, self._timeline_left_margin, y1, fill="#1a1a1a", outline="")
            
            # Color indicator strip
            cnv.create_rectangle(2, y0 + 4, 6, y1 - 4, fill=track_color, outline="")
            
            cnv.create_text(
                10, 
                y0 + track_h // 2, 
                anchor="w", 
                text=label, 
                fill="#a0a0a0", 
                font=("Segoe UI", 9, "bold")
            )

        # Clear clip canvas ID mapping
        self._clip_canvas_ids = {}
        
        # Draw clips with track colors and waveforms
        if self.timeline is not None:
            try:
                for ti, clip in self.timeline.all_placements():
                    y0 = ruler_h + int(ti) * track_h
                    y1 = y0 + track_h
                    x0 = self._timeline_left_margin + int(clip.start_time * self._px_per_sec)
                    x1 = self._timeline_left_margin + int(clip.end_time * self._px_per_sec)
                    
                    # Get track color
                    clip_color = "#3b82f6"
                    clip_border = "#60a5fa"
                    try:
                        if self.mixer is not None and ti < len(self.mixer.tracks):
                            clip_color = self.mixer.tracks[ti].get("color", "#3b82f6")
                            # Lighter border
                            clip_border = self._lighten_color(clip_color, 1.3)
                    except Exception:
                        pass
                    
                    # Selection highlight
                    border_width = 3 if getattr(clip, 'selected', False) else 2
                    if getattr(clip, 'selected', False):
                        clip_border = "#ffffff"
                    
                    # Clip rectangle with track color
                    clip_id = cnv.create_rectangle(
                        x0, 
                        y0 + 8, 
                        x1, 
                        y1 - 8, 
                        fill=clip_color, 
                        outline=clip_border,
                        width=border_width
                    )
                    
                    # Store clip ID mapping
                    self._clip_canvas_ids[clip_id] = (ti, clip)
                    
                    # Draw waveform
                    try:
                        clip_width = x1 - x0
                        if clip_width > 20:  # Only draw if clip is wide enough
                            num_points = max(10, int(clip_width / 2))
                            peaks = clip.get_peaks(num_points)
                            
                            wave_y_center = (y0 + y1) / 2
                            wave_h = (y1 - y0 - 20) / 2
                            
                            for i, (min_val, max_val) in enumerate(peaks):
                                px = x0 + (i * clip_width / len(peaks))
                                py_min = wave_y_center - (min_val * wave_h)
                                py_max = wave_y_center - (max_val * wave_h)
                                
                                cnv.create_line(
                                    px, py_min, px, py_max,
                                    fill="#000000",
                                    width=1
                                )
                    except Exception:
                        pass
                    
                    # Clip name
                    clip_name = getattr(clip, 'name', 'clip')
                    cnv.create_text(
                        x0 + 6, 
                        y0 + 14, 
                        anchor="nw", 
                        text=clip_name, 
                        fill="#ffffff", 
                        font=("Segoe UI", 9, "bold")
                    )
            except Exception:
                pass

        # Draw loop markers if loop is enabled
        if self.player is not None:
            try:
                loop_enabled, loop_start, loop_end = self.player.get_loop()
                if loop_enabled:
                    loop_x_start = self._timeline_left_margin + loop_start * self._px_per_sec
                    loop_x_end = self._timeline_left_margin + loop_end * self._px_per_sec
                    
                    # Loop region highlight (semi-transparent overlay)
                    cnv.create_rectangle(
                        loop_x_start, ruler_h,
                        loop_x_end, height,
                        fill="#10b981",
                        stipple="gray25",  # semi-transparent pattern
                        outline=""
                    )
                    
                    # Loop start marker (green line)
                    cnv.create_line(
                        loop_x_start, ruler_h,
                        loop_x_start, height,
                        fill="#10b981",
                        width=3
                    )
                    # Loop start flag
                    cnv.create_polygon(
                        loop_x_start, ruler_h,
                        loop_x_start + 12, ruler_h + 6,
                        loop_x_start, ruler_h + 12,
                        fill="#10b981",
                        outline="#065f46"
                    )
                    cnv.create_text(
                        loop_x_start + 4, ruler_h + 6,
                        text="[",
                        fill="#ffffff",
                        font=("Segoe UI", 10, "bold")
                    )
                    
                    # Loop end marker (green line)
                    cnv.create_line(
                        loop_x_end, ruler_h,
                        loop_x_end, height,
                        fill="#10b981",
                        width=3
                    )
                    # Loop end flag
                    cnv.create_polygon(
                        loop_x_end, ruler_h,
                        loop_x_end - 12, ruler_h + 6,
                        loop_x_end, ruler_h + 12,
                        fill="#10b981",
                        outline="#065f46"
                    )
                    cnv.create_text(
                        loop_x_end - 4, ruler_h + 6,
                        text="]",
                        fill="#ffffff",
                        font=("Segoe UI", 10, "bold")
                    )
            except Exception:
                pass

        # Draw playback cursor
        cur = 0.0
        try:
            cur = float(getattr(self.player, "_current_time", 0.0))
        except Exception:
            pass
        
        cursor_x = self._timeline_left_margin + cur * self._px_per_sec
        self._cursor_id = cnv.create_line(
            cursor_x, 
            0, 
            cursor_x, 
            height, 
            fill="#ef4444", 
            width=3
        )
        
        # Cursor head (triangle)
        cnv.create_polygon(
            cursor_x - 6, 0,
            cursor_x + 6, 0,
            cursor_x, 10,
            fill="#ef4444",
            outline=""
        )
        
        self._update_cursor_line(cur)

    def _update_cursor_line(self, cur_time: float):
        cnv = self._timeline_canvas
        if cnv is None or self._cursor_id is None:
            return
        x = self._timeline_left_margin + cur_time * self._px_per_sec
        # move line
        coords = cnv.coords(self._cursor_id)
        if len(coords) == 4:
            cnv.coords(self._cursor_id, x, 0, x, cnv.winfo_height())
        else:
            height = cnv.winfo_height()
            cnv.coords(self._cursor_id, x, 0, x, height)
        # auto-scroll to keep cursor visible
        try:
            vis_left = cnv.canvasx(0)
            vis_right = cnv.canvasx(cnv.winfo_width())
            if x < vis_left or x > vis_right:
                cnv.xview_moveto(max(0.0, (x - self._timeline_left_margin) / max(1, self._compute_timeline_width())))
        except Exception:
            pass

    # ----- zoom helpers -----
    def _zoom(self, factor: float):
        try:
            self._px_per_sec = max(40, min(800, int(self._px_per_sec * factor)))
            self._redraw_timeline()
            zoom_val = self._px_per_sec / 200.0
            if hasattr(self, "_zoom_label") and self._zoom_label is not None:
                self._zoom_label.config(text=f"Zoom: {zoom_val:.2f}x")
            if hasattr(self, "_status") and self._status is not None:
                self._status.set(f"● Zoom: {zoom_val:.2f}x")
        except Exception:
            pass

    def _zoom_reset(self):
        try:
            self._px_per_sec = 200
            self._redraw_timeline()
            if hasattr(self, "_zoom_label") and self._zoom_label is not None:
                self._zoom_label.config(text="Zoom: 1.00x")
            if hasattr(self, "_status") and self._status is not None:
                self._status.set("● Ready")
        except Exception:
            pass

    # ----- key bindings -----
    def _bind_keys(self):
        if self._root is None:
            return
        try:
            self._root.bind('<space>', lambda e: self._on_play() if not getattr(self.player, 'is_playing', lambda: False)() else self._on_stop())
            self._root.bind('+', lambda e: self._zoom(1.25))
            self._root.bind('-', lambda e: self._zoom(0.8))
            self._root.bind('0', lambda e: self._zoom_reset())
        except Exception:
            pass
    
    # ----- clip interaction helpers -----
    def _on_timeline_click(self, event):
        """Handle mouse click on timeline canvas."""
        if self._timeline_canvas is None:
            return
        
        x = self._timeline_canvas.canvasx(event.x)
        y = self._timeline_canvas.canvasy(event.y)
        
        # Check if Shift is pressed for loop region selection
        if event.state & 0x0001:  # Shift key
            # Start loop region selection
            time = (x - self._timeline_left_margin) / self._px_per_sec
            time = max(0, time)
            if not hasattr(self, '_loop_selection_start'):
                self._loop_selection_start = time
            return
        
        # Find clicked clip
        items = self._timeline_canvas.find_overlapping(x, y, x, y)
        clicked_clip = None
        
        for item in items:
            if item in self._clip_canvas_ids:
                clicked_clip = self._clip_canvas_ids[item]
                break
        
        if clicked_clip:
            track_idx, clip = clicked_clip
            
            # Check if clicking on edge for resize
            clip_x0 = self._timeline_left_margin + clip.start_time * self._px_per_sec
            clip_x1 = self._timeline_left_margin + clip.end_time * self._px_per_sec
            edge_threshold = 8
            
            if abs(x - clip_x0) < edge_threshold:
                # Start resize left
                self._resize_data = {
                    "clip": clip,
                    "track": track_idx,
                    "edge": "left",
                    "orig_start": clip.start_time
                }
            elif abs(x - clip_x1) < edge_threshold:
                # Start resize right
                self._resize_data = {
                    "clip": clip,
                    "track": track_idx,
                    "edge": "right",
                    "orig_end": clip.end_time
                }
            else:
                # Start drag
                self._drag_data = {
                    "clip": clip,
                    "track": track_idx,
                    "start_x": x,
                    "start_time": clip.start_time
                }
            
            # Select clip
            self._select_clip(track_idx, clip)
        else:
            # Deselect
            self._select_clip(None, None)
    
    def _on_timeline_drag(self, event):
        """Handle mouse drag on timeline."""
        if self._timeline_canvas is None:
            return
        
        x = self._timeline_canvas.canvasx(event.x)
        y = self._timeline_canvas.canvasy(event.y)
        
        # Check if we're selecting loop region with Shift
        if hasattr(self, '_loop_selection_start') and (event.state & 0x0001):
            # Draw preview of loop region
            time = (x - self._timeline_left_margin) / self._px_per_sec
            time = max(0, time)
            # We'll set the loop on release, just visual feedback here
            return
        
        if self._resize_data:
            # Resizing
            clip = self._resize_data["clip"]
            new_time = (x - self._timeline_left_margin) / self._px_per_sec
            new_time = max(0, new_time)
            
            # Apply snap to grid
            new_time = self._snap_time(new_time)
            
            if self._resize_data["edge"] == "left":
                # Resize left (change start_time)
                if new_time < clip.end_time - 0.1:  # Min 0.1s duration
                    clip.start_time = new_time
            else:
                # Resize right (change duration)
                if new_time > clip.start_time + 0.1:
                    new_duration = new_time - clip.start_time
                    clip.duration = new_duration
            
            self._redraw_timeline()
            
        elif self._drag_data:
            # Dragging
            clip = self._drag_data["clip"]
            delta_x = x - self._drag_data["start_x"]
            delta_time = delta_x / self._px_per_sec
            new_start = self._drag_data["start_time"] + delta_time
            new_start = max(0, new_start)
            
            # Apply snap to grid
            new_start = self._snap_time(new_start)
            
            clip.start_time = new_start
            
            # Check track change
            ruler_h = 32
            track_h = 60
            track_idx = int((y - ruler_h) / track_h)
            track_idx = max(0, min(track_idx, len(self.mixer.tracks) - 1))
            
            if track_idx != self._drag_data["track"]:
                # Move to different track
                old_track = self._drag_data["track"]
                self.timeline.remove_clip(old_track, clip)
                self.timeline.add_clip(track_idx, clip)
                self._drag_data["track"] = track_idx
                self._selected_clip = (track_idx, clip)
            
            self._redraw_timeline()
    
    def _on_timeline_release(self, event):
        """Handle mouse release on timeline."""
        # Check if we were selecting loop region
        if hasattr(self, '_loop_selection_start'):
            x = self._timeline_canvas.canvasx(event.x)
            end_time = (x - self._timeline_left_margin) / self._px_per_sec
            end_time = max(0, end_time)
            
            # Apply snap to both start and end
            start = self._snap_time(min(self._loop_selection_start, end_time))
            end = self._snap_time(max(self._loop_selection_start, end_time))
            
            if abs(end - start) > 0.1:  # Minimum 0.1s region
                if self.player is not None:
                    self.player.set_loop(True, start, end)
                    if self._loop_var is not None:
                        self._loop_var.set(True)
                    self._redraw_timeline()
                    print(f"Loop region set: {start:.3f}s - {end:.3f}s")
            
            delattr(self, '_loop_selection_start')
            return
        
        self._drag_data = None
        self._resize_data = None
        self._populate_tracks()
    
    def _on_timeline_motion(self, event):
        """Handle mouse motion for cursor changes."""
        if self._timeline_canvas is None or self._drag_data or self._resize_data:
            return
        
        x = self._timeline_canvas.canvasx(event.x)
        y = self._timeline_canvas.canvasy(event.y)
        
        # Check if hovering over clip edge
        items = self._timeline_canvas.find_overlapping(x, y, x, y)
        
        for item in items:
            if item in self._clip_canvas_ids:
                track_idx, clip = self._clip_canvas_ids[item]
                clip_x0 = self._timeline_left_margin + clip.start_time * self._px_per_sec
                clip_x1 = self._timeline_left_margin + clip.end_time * self._px_per_sec
                
                if abs(x - clip_x0) < 8 or abs(x - clip_x1) < 8:
                    self._timeline_canvas.config(cursor="sb_h_double_arrow")
                    return
                else:
                    self._timeline_canvas.config(cursor="hand2")
                    return
        
        self._timeline_canvas.config(cursor="")
    
    def _on_timeline_right_click(self, event):
        """Handle right-click context menu on timeline."""
        if self._timeline_canvas is None:
            return
        
        x = self._timeline_canvas.canvasx(event.x)
        y = self._timeline_canvas.canvasy(event.y)
        
        # Find clicked clip
        items = self._timeline_canvas.find_overlapping(x, y, x, y)
        clicked_clip = None
        
        for item in items:
            if item in self._clip_canvas_ids:
                clicked_clip = self._clip_canvas_ids[item]
                break
        
        if clicked_clip:
            track_idx, clip = clicked_clip
            self._select_clip(track_idx, clip)
            
            # Show context menu
            menu = tk.Menu(self._root, tearoff=0, bg="#2d2d2d", fg="#f5f5f5", activebackground="#3b82f6")
            menu.add_command(label=f"✂ Delete '{clip.name}'", command=lambda: self._delete_selected_clip())
            menu.add_command(label=f"📋 Duplicate '{clip.name}'", command=lambda: self._duplicate_selected_clip())
            menu.add_separator()
            menu.add_command(label="Properties...", command=lambda: self._show_clip_properties())
            
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
    
    def _select_clip(self, track_idx, clip):
        """Select a clip."""
        # Deselect previous
        if self._selected_clip:
            old_track, old_clip = self._selected_clip
            old_clip.selected = False
        
        if clip:
            clip.selected = True
            self._selected_clip = (track_idx, clip)
        else:
            self._selected_clip = None
        
        self._redraw_timeline()
    
    def _delete_selected_clip(self):
        """Delete the selected clip."""
        if not self._selected_clip:
            return
        
        track_idx, clip = self._selected_clip
        self.timeline.remove_clip(track_idx, clip)
        self._selected_clip = None
        self._populate_tracks()
        self._redraw_timeline()
        
        if hasattr(self, "_status"):
            self._status.set(f"✓ Deleted clip '{clip.name}'")
    
    def _duplicate_selected_clip(self):
        """Duplicate the selected clip."""
        if not self._selected_clip:
            return
        
        track_idx, clip = self._selected_clip
        
        from src.audio.clip import AudioClip
        new_clip = AudioClip(
            f"{clip.name} (copy)",
            clip.buffer,
            clip.sample_rate,
            clip.end_time + 0.1,  # Place after original
            duration=clip.duration,
            color=clip.color,
            file_path=clip.file_path
        )
        
        self.timeline.add_clip(track_idx, new_clip)
        self._select_clip(track_idx, new_clip)
        self._populate_tracks()
        self._redraw_timeline()
        
        if hasattr(self, "_status"):
            self._status.set(f"✓ Duplicated clip '{clip.name}'")
    
    def _show_clip_properties(self):
        """Show clip properties dialog."""
        if not self._selected_clip:
            return
        
        track_idx, clip = self._selected_clip
        
        props = f"""Clip Properties
        
Name: {clip.name}
Start Time: {clip.start_time:.3f} s
End Time: {clip.end_time:.3f} s
Duration: {clip.length_seconds:.3f} s
Sample Rate: {clip.sample_rate} Hz
Samples: {len(clip.buffer)}
"""
        if clip.file_path:
            props += f"\nSource: {clip.file_path}"
        
        messagebox.showinfo("Clip Properties", props)

    # ----- color helpers -----
    def _lighten_color(self, hex_color: str, factor: float = 1.3) -> str:
        """Lighten a hex color by a factor."""
        try:
            hex_color = hex_color.lstrip('#')
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            r = min(255, int(r * factor))
            g = min(255, int(g * factor))
            b = min(255, int(b * factor))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return "#60a5fa"