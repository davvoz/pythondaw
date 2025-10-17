"""Track controls for volume, pan, and meters."""

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover
    tk = None
    ttk = None


class TrackControls:
    """Manages track control UI (volume, pan, meters) in the sidebar."""

    def __init__(self, parent, mixer=None):
        self.mixer = mixer
        self.parent = parent
        
        # Track list
        self.track_tree = None
        self.track_icons = {}
        
        # Control variables
        self.volume_var = None
        self.pan_var = None
        
        # Meters
        self.meter_L = None
        self.meter_R = None
        
        # Current selection
        self.current_track_idx = None
        
    def build_ui(self):
        """Build the track controls UI."""
        if self.parent is None or tk is None:
            return
            
        # Tracks section header
        tracks_header = ttk.Frame(self.parent, style="Sidebar.TFrame")
        tracks_header.pack(fill="x", padx=12, pady=(8, 4))
        ttk.Label(tracks_header, text="TRACKS", style="SidebarTitle.TLabel").pack(side="left")
        
        # Track list with Treeview
        tracks_list_frame = ttk.Frame(self.parent, style="Sidebar.TFrame")
        tracks_list_frame.pack(fill="both", expand=True, padx=12, pady=4)
        
        columns = ("#", "name", "clips")
        self.track_tree = ttk.Treeview(
            tracks_list_frame, columns=columns,
            show="headings", selectmode="browse"
        )
        
        self.track_tree.heading("#", text="#")
        self.track_tree.heading("name", text="Track")
        self.track_tree.heading("clips", text="Clips")
        
        self.track_tree.column("#", width=40, anchor="center")
        self.track_tree.column("name", anchor="w")
        self.track_tree.column("clips", width=60, anchor="center")
        
        self.track_tree.pack(fill="both", expand=True)
        self.track_tree.bind("<<TreeviewSelect>>", self._on_select_track)
        
        # Track controls section
        controls_frame = ttk.Frame(self.parent, style="Sidebar.TFrame")
        controls_frame.pack(fill="x", padx=12, pady=(8, 4))
        
        # Separator
        separator = ttk.Frame(controls_frame, height=1, style="Sidebar.TFrame")
        separator.pack(fill="x", pady=(0, 8))
        
        # Volume control
        vol_row = ttk.Frame(controls_frame, style="Sidebar.TFrame")
        vol_row.pack(fill="x", pady=2)
        ttk.Label(
            vol_row, text="Vol", style="Sidebar.TLabel",
            width=4, font=("Segoe UI", 8, "bold")
        ).pack(side="left")
        
        self.volume_var = tk.DoubleVar(value=1.0)
        vol_scale = ttk.Scale(
            vol_row, from_=0.0, to=1.0, orient="horizontal",
            variable=self.volume_var, command=self._on_volume_change
        )
        vol_scale.pack(side="left", fill="x", expand=True, padx=(4, 0))
        
        # Pan control
        pan_row = ttk.Frame(controls_frame, style="Sidebar.TFrame")
        pan_row.pack(fill="x", pady=2)
        ttk.Label(
            pan_row, text="Pan", style="Sidebar.TLabel",
            width=4, font=("Segoe UI", 8, "bold")
        ).pack(side="left")
        
        self.pan_var = tk.DoubleVar(value=0.0)
        pan_scale = ttk.Scale(
            pan_row, from_=-1.0, to=1.0, orient="horizontal",
            variable=self.pan_var, command=self._on_pan_change
        )
        pan_scale.pack(side="left", fill="x", expand=True, padx=(4, 0))
        
        # Meters section
        meters_frame = ttk.Frame(self.parent, style="Sidebar.TFrame")
        meters_frame.pack(fill="x", padx=12, pady=(8, 12))
        
        ttk.Label(
            meters_frame, text="OUTPUT", style="SidebarTitle.TLabel",
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w", pady=(0, 4))
        
        # Left meter
        meter_L_row = ttk.Frame(meters_frame, style="Sidebar.TFrame")
        meter_L_row.pack(fill="x", pady=1)
        ttk.Label(
            meter_L_row, text="L", style="Sidebar.TLabel",
            width=2, font=("Segoe UI", 8, "bold")
        ).pack(side="left")
        
        self.meter_L = ttk.Progressbar(
            meter_L_row, mode="determinate", maximum=1.0,
            style="Meter.Horizontal.TProgressbar"
        )
        self.meter_L.pack(side="left", fill="x", expand=True, padx=(4, 0))
        
        # Right meter
        meter_R_row = ttk.Frame(meters_frame, style="Sidebar.TFrame")
        meter_R_row.pack(fill="x", pady=1)
        ttk.Label(
            meter_R_row, text="R", style="Sidebar.TLabel",
            width=2, font=("Segoe UI", 8, "bold")
        ).pack(side="left")
        
        self.meter_R = ttk.Progressbar(
            meter_R_row, mode="determinate", maximum=1.0,
            style="Meter.Horizontal.TProgressbar"
        )
        self.meter_R.pack(side="left", fill="x", expand=True, padx=(4, 0))
    
    def populate_tracks(self, timeline=None):
        """Populate track list from mixer."""
        if self.mixer is None or self.track_tree is None:
            print(f"populate_tracks: mixer={self.mixer}, track_tree={self.track_tree}")
            return
        
        print(f"populate_tracks: Found {len(self.mixer.tracks)} tracks in mixer")
            
        # Clear existing items
        for item in self.track_tree.get_children():
            self.track_tree.delete(item)
        
        # Add tracks
        for idx, track in enumerate(self.mixer.tracks):
            name = track.get("name", f"Track {idx+1}")
            color = track.get("color", "#3b82f6")
            
            clips = 0
            if timeline is not None:
                try:
                    clips = timeline.count_clips_for_track(idx)
                except Exception as e:
                    print(f"  Error counting clips for track {idx}: {e}")
                    clips = 0
            
            print(f"  Inserting track {idx}: '{name}' with {clips} clips")
            
            self.track_tree.insert(
                "", "end", iid=str(idx),
                values=(idx + 1, name, clips),
                tags=(f"t{idx}",)
            )
            
            try:
                self.track_tree.tag_configure(f"t{idx}", foreground=color)
            except Exception:
                pass
        
        print(f"populate_tracks: Tree now has {len(self.track_tree.get_children())} items")
    
    def get_current_track_index(self):
        """Get currently selected track index."""
        if self.track_tree is None:
            return None
            
        sel = self.track_tree.selection()
        if not sel:
            return None
            
        try:
            return int(sel[0])
        except Exception:
            return None
    
    def _on_select_track(self, event=None):
        """Handle track selection."""
        idx = self.get_current_track_index()
        if idx is None or self.mixer is None:
            return
            
        self.current_track_idx = idx
        
        # Update controls
        vol = float(self.mixer.tracks[idx].get("volume", 1.0))
        if self.volume_var is not None:
            self.volume_var.set(vol)
        
        pan = float(self.mixer.tracks[idx].get("pan", 0.0))
        if self.pan_var is not None:
            self.pan_var.set(pan)
    
    def _on_volume_change(self, value=None):
        """Handle volume change."""
        idx = self.get_current_track_index()
        if idx is None or self.mixer is None or self.volume_var is None:
            return
            
        try:
            self.mixer.tracks[idx]["volume"] = float(self.volume_var.get())
        except Exception:
            pass
    
    def _on_pan_change(self, value=None):
        """Handle pan change."""
        idx = self.get_current_track_index()
        if idx is None or self.mixer is None or self.pan_var is None:
            return
            
        try:
            p = float(self.pan_var.get())
            p = max(-1.0, min(1.0, p))  # Clamp to [-1, 1]
            self.mixer.tracks[idx]["pan"] = p
        except Exception:
            pass
    
    def update_meters(self, player):
        """Update meter display from player."""
        if player is None:
            return
            
        try:
            peakL = float(getattr(player, "_last_peak_L", 0.0))
            peakR = float(getattr(player, "_last_peak_R", 0.0))
            
            if self.meter_L is not None:
                self.meter_L['value'] = max(0.0, min(1.0, peakL))
            
            if self.meter_R is not None:
                self.meter_R['value'] = max(0.0, min(1.0, peakR))
        except Exception:
            pass
