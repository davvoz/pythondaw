"""Track controls for volume, pan, and meters."""

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover
    tk = None
    ttk = None


class TrackControls:
    """Manages track control UI (volume, pan, meters) in the sidebar."""

    def __init__(self, parent, mixer=None, timeline=None, project=None, redraw_cb=None):
        self.mixer = mixer
        self.parent = parent
        # Direct references to app state passed from MainWindow
        self.timeline = timeline
        self.project = project
        self._redraw_cb = redraw_cb
        
        # Track list (custom frames instead of Treeview)
        self.track_list_container = None
        self.track_frames = {}  # {track_idx: frame} or {"master": frame}
        self.track_labels = {}  # {track_idx: label}
        self.mute_buttons = {}  # {track_idx: button}
        self.solo_buttons = {}  # {track_idx: button}
        self.track_controls = {}  # {track_idx: controls_frame} for inline vol/pan
        
        # Control variables per track
        self.volume_vars = {}  # {track_idx: tk.DoubleVar}
        self.pan_vars = {}  # {track_idx: tk.DoubleVar}
        
        # Meters
        self.meter_L = None
        self.meter_R = None
        
        # Current selection
        self.current_track_idx = None
        
        # Control frames that need color update
        self.controls_frame = None
        self.meters_frame = None
        self.vol_row = None
        self.pan_row = None
        self.meter_L_row = None
        self.meter_R_row = None
        self.vol_label = None
        self.pan_label = None
        self.output_label = None
        self.meter_L_label = None
        self.meter_R_label = None
        self.mute_solo_row = None
        
        # TTK Style for dynamic colors
        self.style = None
        
    def build_ui(self):
        """Build the track controls UI - fixed list with optional scrollbar."""
        if self.parent is None or tk is None:
            return
        
        # Initialize style
        self.style = ttk.Style()
        
        # Scrollable container for track list
        tracks_outer = ttk.Frame(self.parent, style="Sidebar.TFrame")
        tracks_outer.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Canvas with scrollbar for many tracks
        self.canvas = tk.Canvas(tracks_outer, bg="#2d2d2d", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(tracks_outer, orient="vertical", command=self.canvas.yview)
        
        self.track_list_container = ttk.Frame(self.canvas, style="Sidebar.TFrame")
        self.track_list_container.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.track_list_container, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Bind mouse wheel for sidebar scrolling
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))
        
        # Bind canvas resize
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bottom section: OUTPUT meters (fixed at bottom)
        self.meters_frame = ttk.Frame(self.parent, style="Sidebar.TFrame")
        self.meters_frame.pack(fill="x", padx=12, pady=(12, 12), side="bottom")
        
        # Separator line at top
        separator = tk.Frame(self.meters_frame, height=2, bg="#404040")
        separator.pack(fill="x", padx=12, pady=(0, 8))
        
        self.output_label = ttk.Label(
            self.meters_frame, text="OUTPUT", style="SidebarTitle.TLabel",
            font=("Segoe UI", 9, "bold")
        )
        self.output_label.pack(anchor="w", padx=12, pady=(0, 8))
        
        # Left meter with improved layout
        self.meter_L_row = ttk.Frame(self.meters_frame, style="Sidebar.TFrame")
        self.meter_L_row.pack(fill="x", padx=12, pady=2)
        self.meter_L_label = ttk.Label(
            self.meter_L_row, text="L", style="Sidebar.TLabel",
            width=3, font=("Segoe UI", 8, "bold")
        )
        self.meter_L_label.pack(side="left", padx=(0, 8))
        
        self.meter_L = ttk.Progressbar(
            self.meter_L_row, mode="determinate", maximum=1.0,
            style="Meter.Horizontal.TProgressbar"
        )
        self.meter_L.pack(side="left", fill="x", expand=True, padx=0)
        
        # Right meter with improved layout
        self.meter_R_row = ttk.Frame(self.meters_frame, style="Sidebar.TFrame")
        self.meter_R_row.pack(fill="x", padx=12, pady=2)
        self.meter_R_label = ttk.Label(
            self.meter_R_row, text="R", style="Sidebar.TLabel",
            width=3, font=("Segoe UI", 8, "bold")
        )
        self.meter_R_label.pack(side="left", padx=(0, 8))
        
        self.meter_R = ttk.Progressbar(
            self.meter_R_row, mode="determinate", maximum=1.0,
            style="Meter.Horizontal.TProgressbar"
        )
        self.meter_R.pack(side="left", fill="x", expand=True, padx=0)
    
    def populate_tracks(self, timeline=None):
        """Populate track list from mixer - fixed controls."""
        if self.mixer is None or self.track_list_container is None:
            print(f"populate_tracks: mixer={self.mixer}, container={self.track_list_container}")
            return
        
        print(f"populate_tracks: Found {len(self.mixer.tracks)} tracks in mixer")
        
        # Clear existing widgets
        for widget in self.track_list_container.winfo_children():
            widget.destroy()
        self.track_frames.clear()
        self.track_labels.clear()
        self.mute_buttons.clear()
        self.solo_buttons.clear()
        
        # Add Master first (no M/S buttons)
        self._create_track_row("master", "Master", None, show_ms=False)
        
        # Add all tracks
        for idx, track in enumerate(self.mixer.tracks):
            name = track.get("name", f"Track {idx+1}")
            color = track.get("color", "#3b82f6")
            self._create_track_row(idx, name, color, show_ms=True)
        
        print(f"populate_tracks: Created {len(self.track_frames)} track rows")
    
    def _create_track_row(self, track_id, name, color, show_ms=True, container=None):
        """Create a single track row with name + M/S buttons + inline controls.
        
        Args:
            track_id: "master" or int (track index)
            name: Track name to display
            color: Hex color for the track (None for master)
            show_ms: Whether to show M/S buttons (False for master)
            container: Parent container (defaults to track_list_container if None)
        """
        if container is None:
            container = self.track_list_container
        
        # Main row frame (no fixed height, independent scrolling)
        row_frame = tk.Frame(
            container,
            bg="#2d2d2d" if track_id == "master" else "#1e1e1e",
            highlightthickness=0
        )
        row_frame.pack(fill="x", padx=4, pady=2)
        
        # Top bar with name and buttons
        top_bar = tk.Frame(row_frame, bg=row_frame["bg"])
        top_bar.pack(fill="x", padx=4, pady=4)
        
        # Make row clickable for selection
        top_bar.bind("<Button-1>", lambda e, tid=track_id: self._on_track_click(tid))
        
        # Track name label
        label = tk.Label(
            top_bar,
            text=name,
            fg=color if color else "#f5f5f5",
            bg=row_frame["bg"],
            font=("Segoe UI", 10, "bold" if track_id == "master" else "normal"),
            anchor="w"
        )
        label.pack(side="left", fill="x", expand=True)
        label.bind("<Button-1>", lambda e, tid=track_id: self._on_track_click(tid))
        
        # Right-click menu
        if track_id != "master":
            top_bar.bind("<Button-3>", lambda e, tid=track_id: self._on_track_right_click_new(e, tid))
            label.bind("<Button-3>", lambda e, tid=track_id: self._on_track_right_click_new(e, tid))
        else:
            top_bar.bind("<Button-3>", lambda e: self._on_master_right_click(e))
            label.bind("<Button-3>", lambda e: self._on_master_right_click(e))
        
        # M/S buttons (only for tracks, not master) - improved sizing
        if show_ms and track_id != "master":
            idx = track_id
            is_muted = self.mixer.tracks[idx].get("mute", False)
            is_soloed = self.mixer.tracks[idx].get("solo", False)
            
            # Buttons container for consistent spacing
            buttons_frame = tk.Frame(top_bar, bg=row_frame["bg"])
            buttons_frame.pack(side="right", padx=0)
            
            # Solo button with improved style
            solo_btn = tk.Button(
                buttons_frame,
                text="S",
                width=2,
                height=1,
                bg="#eab308" if is_soloed else "#404040",
                fg="#ffffff",
                font=("Segoe UI", 9, "bold"),
                relief="flat",
                cursor="hand2",
                borderwidth=0,
                command=lambda: self._toggle_solo(idx)
            )
            solo_btn.pack(side="right", padx=2)
            self.solo_buttons[idx] = solo_btn
            
            # Mute button with improved style
            mute_btn = tk.Button(
                buttons_frame,
                text="M",
                width=2,
                height=1,
                bg="#dc2626" if is_muted else "#404040",
                fg="#ffffff",
                font=("Segoe UI", 9, "bold"),
                relief="flat",
                cursor="hand2",
                borderwidth=0,
                command=lambda: self._toggle_mute(idx)
            )
            mute_btn.pack(side="right", padx=2)
            self.mute_buttons[idx] = mute_btn
        
        # Inline controls frame (Vol/Pan) - for ALL tracks including master
        # Master: inline in top_bar to fit in 32px, Tracks: separate frame
        
        # Controls frame for vol/pan sliders
        controls_frame = tk.Frame(row_frame, bg=row_frame["bg"])
        controls_frame.pack(fill="x", padx=4, pady=(0, 4))
        
        if track_id == "master":
            # Master: only volume control
            vol_row = tk.Frame(controls_frame, bg=row_frame["bg"])
            vol_row.pack(fill="x", padx=4, pady=2)
            
            vol_label = tk.Label(
                vol_row, text="Vol", bg=row_frame["bg"], fg="#a0a0a0",
                font=("Segoe UI", 8), width=3, anchor="w"
            )
            vol_label.pack(side="left", padx=(0, 4))
            
            vol_var = tk.DoubleVar(value=getattr(self.mixer, 'master_volume', 1.0))
            vol_scale = ttk.Scale(
                vol_row, from_=0.0, to=1.0, orient="horizontal",
                variable=vol_var, 
                command=lambda v: self._on_master_volume_change(v)
            )
            vol_scale.pack(side="left", fill="x", expand=True, padx=(0, 4))
            
            vol_value_label = tk.Label(
                vol_row, text="1.00", bg=row_frame["bg"], fg="#f5f5f5",
                font=("Segoe UI", 8, "bold"), width=4, anchor="e"
            )
            vol_value_label.pack(side="left")
            
            self.track_controls["master"] = controls_frame
            self.volume_vars["master"] = vol_var
            if not hasattr(self, 'value_labels'):
                self.value_labels = {}
            self.value_labels[("master", "vol")] = vol_value_label
            
        else:
            # Regular tracks: vol + pan controls
            idx = track_id
            
            # Volume control
            vol_row = tk.Frame(controls_frame, bg=row_frame["bg"])
            vol_row.pack(fill="x", padx=4, pady=2)
            
            vol_label = tk.Label(
                vol_row, text="Vol", bg=row_frame["bg"], fg="#a0a0a0",
                font=("Segoe UI", 8), width=3, anchor="w"
            )
            vol_label.pack(side="left", padx=(0, 4))
            
            vol_var = tk.DoubleVar(value=self.mixer.tracks[idx].get("volume", 1.0))
            vol_scale = ttk.Scale(
                vol_row, from_=0.0, to=1.0, orient="horizontal",
                variable=vol_var, 
                command=lambda v, i=idx: self._on_volume_change_inline(i, v)
            )
            vol_scale.pack(side="left", fill="x", expand=True, padx=(0, 4))
            
            vol_value_label = tk.Label(
                vol_row, text=f"{self.mixer.tracks[idx].get('volume', 1.0):.2f}", 
                bg=row_frame["bg"], fg="#f5f5f5",
                font=("Segoe UI", 8, "bold"), width=4, anchor="e"
            )
            vol_value_label.pack(side="left")
            
            # Pan control
            pan_row = tk.Frame(controls_frame, bg=row_frame["bg"])
            pan_row.pack(fill="x", padx=4, pady=2)
            
            pan_label = tk.Label(
                pan_row, text="Pan", bg=row_frame["bg"], fg="#a0a0a0",
                font=("Segoe UI", 8), width=3, anchor="w"
            )
            pan_label.pack(side="left", padx=(0, 4))
            
            pan_var = tk.DoubleVar(value=self.mixer.tracks[idx].get("pan", 0.0))
            pan_scale = ttk.Scale(
                pan_row, from_=-1.0, to=1.0, orient="horizontal",
                variable=pan_var,
                command=lambda v, i=idx: self._on_pan_change_inline(i, v)
            )
            pan_scale.pack(side="left", fill="x", expand=True, padx=(0, 4))
            
            # Value label (L/C/R format)
            pan_value = self.mixer.tracks[idx].get("pan", 0.0)
            pan_text = "C" if abs(pan_value) < 0.05 else (f"L{abs(pan_value):.1f}" if pan_value < 0 else f"R{pan_value:.1f}")
            pan_value_label = tk.Label(
                pan_row, text=pan_text, 
                bg=row_frame["bg"], fg="#f5f5f5",
                font=("Segoe UI", 8, "bold"), width=4, anchor="e"
            )
            pan_value_label.pack(side="left")
            
            self.track_controls[idx] = controls_frame
            self.volume_vars[idx] = vol_var
            self.pan_vars[idx] = pan_var
            
            # Store value labels for updates
            if not hasattr(self, 'value_labels'):
                self.value_labels = {}
            self.value_labels[(idx, "vol")] = vol_value_label
            self.value_labels[(idx, "pan")] = pan_value_label
        
        self.track_frames[track_id] = row_frame
        self.track_labels[track_id] = label
    
    def get_current_track_index(self):
        """Get currently selected track index."""
        return self.current_track_idx
    
    def _on_track_click(self, track_id):
        """Handle track selection by clicking on track row."""
        if track_id == "master":
            self.current_track_idx = -1
        else:
            self.current_track_idx = track_id
        
        self._on_select_track()
        self._update_selection_highlight()
    
    def _update_selection_highlight(self):
        """Update visual highlight for selected track - controls are always visible."""
        for tid, frame in self.track_frames.items():
            if tid == self.current_track_idx or (tid == "master" and self.current_track_idx == -1):
                # Selected track - subtle blue-gray background
                selected_bg = "#2d4a6b"  # More subtle blue-gray color
                frame.configure(bg=selected_bg)
                if tid in self.track_labels:
                    self.track_labels[tid].configure(bg=selected_bg)
                
                # Update all child frames and labels bg
                for child in frame.winfo_children():
                    if isinstance(child, tk.Frame):
                        child.configure(bg=selected_bg)
                        for subchild in child.winfo_children():
                            if isinstance(subchild, (tk.Label, tk.Frame)):
                                try:
                                    subchild.configure(bg=selected_bg)
                                except:
                                    pass
            else:
                # Unselected track - dark background
                bg_color = "#2d2d2d" if tid == "master" else "#1e1e1e"
                frame.configure(bg=bg_color)
                if tid in self.track_labels:
                    self.track_labels[tid].configure(bg=bg_color)
                
                # Update all child frames and labels bg
                for child in frame.winfo_children():
                    if isinstance(child, tk.Frame):
                        child.configure(bg=bg_color)
                        for subchild in child.winfo_children():
                            if isinstance(subchild, (tk.Label, tk.Frame)):
                                try:
                                    subchild.configure(bg=bg_color)
                                except:
                                    pass
    
    def _on_select_track(self, event=None):
        """Handle track selection."""
        idx = self.get_current_track_index()
        if idx is None or self.mixer is None:
            return
        
        # No need to update global vol/pan vars - using inline controls now
        # Just trigger color update if needed
        pass
    
    def _on_volume_change_inline(self, track_idx, value=None):
        """Handle volume change for inline track control."""
        if self.mixer is None or track_idx >= len(self.mixer.tracks):
            return
        try:
            if track_idx in self.volume_vars:
                vol = float(self.volume_vars[track_idx].get())
                self.mixer.tracks[track_idx]["volume"] = vol
                
                # Update value label
                if hasattr(self, 'value_labels') and (track_idx, "vol") in self.value_labels:
                    self.value_labels[(track_idx, "vol")].configure(text=f"{vol:.2f}")
        except Exception as e:
            print(f"Error updating volume: {e}")
    
    def _on_master_volume_change(self, value=None):
        """Handle master volume change."""
        if self.mixer is None:
            return
        try:
            if "master" in self.volume_vars:
                vol = float(self.volume_vars["master"].get())
                if hasattr(self.mixer, 'set_master_volume'):
                    self.mixer.set_master_volume(vol)
                else:
                    self.mixer.master_volume = vol
                
                # Update value label
                if hasattr(self, 'value_labels') and ("master", "vol") in self.value_labels:
                    self.value_labels[("master", "vol")].configure(text=f"{vol:.2f}")
        except Exception as e:
            print(f"Error updating master volume: {e}")
    
    def _on_pan_change_inline(self, track_idx, value=None):
        """Handle pan change for inline track control."""
        if self.mixer is None or track_idx >= len(self.mixer.tracks):
            return
        try:
            if track_idx in self.pan_vars:
                pan = float(self.pan_vars[track_idx].get())
                pan = max(-1.0, min(1.0, pan))
                self.mixer.tracks[track_idx]["pan"] = pan
                
                # Update value label (L/C/R format)
                pan_text = "C" if abs(pan) < 0.05 else (f"L{abs(pan):.1f}" if pan < 0 else f"R{pan:.1f}")
                if hasattr(self, 'value_labels') and (track_idx, "pan") in self.value_labels:
                    self.value_labels[(track_idx, "pan")].configure(text=pan_text)
        except Exception as e:
            print(f"Error updating pan: {e}")
    
    def _on_volume_change(self, value=None):
        """Old volume change handler - no longer used with inline controls."""
        pass
    
    def _on_pan_change(self, value=None):
        """Old pan change handler - no longer used with inline controls."""
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
    
    def _update_control_colors(self, track_idx):
        """Old method - no longer needed with inline controls."""
        pass

    def _on_track_right_click_new(self, event, track_idx):
        """Show context menu for track operations (new frame-based version)."""
        if tk is None or self.mixer is None:
            return
        
        # Select the track first
        self.current_track_idx = track_idx
        self._on_select_track()
        self._update_selection_highlight()
        
        # Build menu
        menu = tk.Menu(None, tearoff=0, bg="#2d2d2d", fg="#f5f5f5", activebackground="#3b82f6")
        track_name = self.mixer.tracks[track_idx].get("name", f"Track {track_idx + 1}")
        menu.add_command(label=f"💾 Export '{track_name}' as Audio...", command=lambda: self._export_track_audio(track_idx))
        menu.add_command(label=f"📦 Save '{track_name}' as Template...", command=lambda: self._save_track_template(track_idx))
        menu.add_separator()
        menu.add_command(label=f"🗑️ Delete '{track_name}'", command=lambda: self._delete_track(track_idx))
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def _on_master_right_click(self, event):
        """Show context menu for master operations."""
        if tk is None:
            return
        
        # Select master first
        self.current_track_idx = -1
        self._on_select_track()
        self._update_selection_highlight()
        
        # Build menu
        menu = tk.Menu(None, tearoff=0, bg="#2d2d2d", fg="#f5f5f5", activebackground="#3b82f6")
        menu.add_command(label="💾 Export Master Audio...", command=self._export_master_audio)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def _on_track_right_click(self, event):
        """Old Treeview-based right-click handler - kept for compatibility."""
        # This method is no longer used with the new frame-based UI
        pass
    
    def _export_track_audio(self, track_idx):
        """Export audio from a single track."""
        if self.mixer is None or track_idx >= len(self.mixer.tracks):
            return
        
        try:
            from tkinter import filedialog, messagebox
            
            track_name = self.mixer.tracks[track_idx].get("name", f"Track {track_idx + 1}")
            
            # Ask user for file path
            file_path = filedialog.asksaveasfilename(
                title=f"Export '{track_name}' Audio",
                defaultextension=".wav",
                initialfile=f"{track_name}.wav",
                filetypes=[
                    ("WAV Audio", "*.wav"),
                    ("All Files", "*.*")
                ]
            )
            
            if not file_path:
                return
            
            print(f"🎵 Exporting track {track_idx} ('{track_name}') to {file_path}...")
            
            # Get the timeline
            timeline = self.timeline
            if timeline is None:
                messagebox.showerror("Export Error", "Timeline not available")
                return
            
            # Find the extent of clips in this track
            clips = list(timeline.get_clips_for_track(track_idx))
            if not clips:
                messagebox.showwarning("Export Warning", f"Track '{track_name}' has no clips to export.")
                return
            
            max_end = max(clip.end_time for clip in clips)
            duration = max_end
            
            # Get track volume
            track_volume = self.mixer.tracks[track_idx].get("volume", 1.0)
            track_volumes = {track_idx: track_volume}
            
            # Render the audio using AudioEngine
            from src.audio.engine import AudioEngine
            engine = AudioEngine()
            engine.initialize()
            
            sample_rate = 44100
            audio_buffer = engine.render_window(
                timeline,
                start_time=0.0,
                duration=duration,
                sample_rate=sample_rate,
                track_volumes=track_volumes,
                solo_tracks=[track_idx],  # Solo this track
                mixer=self.mixer  # Pass mixer for mute/solo state
            )
            
            if not audio_buffer or len(audio_buffer) == 0:
                messagebox.showwarning("Export Warning", "No audio data to export.")
                return
            
            # Save to WAV file
            from src.utils.audio_io import save_audio_file
            save_audio_file(audio_buffer, file_path, sample_rate, format="wav")
            
            # Success message
            import os
            file_size = os.path.getsize(file_path) / 1024  # KB
            messagebox.showinfo(
                "Export Complete",
                f"Track '{track_name}' exported successfully!\n\n"
                f"File: {os.path.basename(file_path)}\n"
                f"Duration: {duration:.2f}s\n"
                f"Size: {file_size:.1f} KB"
            )
            
            print(f"✓ Track exported: {file_path} ({file_size:.1f} KB)")
            
        except Exception as e:
            print(f"✗ Export error: {e}")
            import traceback
            traceback.print_exc()
            try:
                from tkinter import messagebox
                messagebox.showerror("Export Error", f"Failed to export track:\n\n{str(e)}")
            except:
                pass

    def _export_master_audio(self):
        """Export the full master mix as WAV."""
        try:
            from tkinter import filedialog, messagebox
            track_name = "Master"
            file_path = filedialog.asksaveasfilename(
                title=f"Export {track_name} Audio",
                defaultextension=".wav",
                initialfile="master.wav",
                filetypes=[("WAV Audio", "*.wav"), ("All Files", "*.*")]
            )
            if not file_path:
                return

            timeline = self.timeline
            if not timeline:
                messagebox.showerror("Export Error", "Timeline not available")
                return

            # Determine end time across all clips
            max_end = 0.0
            for _, clip in timeline.all_placements():
                if hasattr(clip, 'end_time'):
                    max_end = max(max_end, clip.end_time)
            if max_end <= 0:
                messagebox.showwarning("Export Warning", "No clips to export.")
                return

            from src.audio.engine import AudioEngine
            engine = AudioEngine()
            engine.initialize()
            sample_rate = 44100
            # No solo_tracks -> full mix
            audio_buffer = engine.render_window(
                timeline,
                start_time=0.0,
                duration=max_end,
                sample_rate=sample_rate,
                track_volumes={i: t.get("volume", 1.0) for i, t in enumerate(self.mixer.tracks)},
                mixer=self.mixer  # Pass mixer for mute/solo state
            )
            # Apply mixer master volume if present
            try:
                mv = float(getattr(self.mixer, 'master_volume', 1.0))
                if mv != 1.0:
                    audio_buffer = [max(-1.0, min(1.0, s * mv)) for s in audio_buffer]
            except Exception:
                pass
            if not audio_buffer:
                messagebox.showwarning("Export Warning", "No audio data to export.")
                return

            from src.utils.audio_io import save_audio_file
            save_audio_file(audio_buffer, file_path, sample_rate, format="wav")

            import os
            size_kb = os.path.getsize(file_path) / 1024
            messagebox.showinfo("Export Complete", f"Master exported to {os.path.basename(file_path)}\nSize: {size_kb:.1f} KB")
            print(f"✓ Master exported: {file_path}")
        except Exception as e:
            print(f"✗ Export master error: {e}")
            try:
                from tkinter import messagebox
                messagebox.showerror("Export Error", f"Failed to export master:\n\n{e}")
            except Exception:
                pass
    
    def _save_track_template(self, track_idx):
        """Save track configuration and clips as a template."""
        if self.mixer is None or track_idx >= len(self.mixer.tracks):
            return
        
        try:
            from tkinter import filedialog, messagebox
            import json
            
            track_name = self.mixer.tracks[track_idx].get("name", f"Track {track_idx + 1}")
            
            # Ask user for file path
            file_path = filedialog.asksaveasfilename(
                title=f"Save '{track_name}' Template",
                defaultextension=".dawtrack",
                initialfile=f"{track_name}.dawtrack",
                filetypes=[
                    ("DAW Track Template", "*.dawtrack"),
                    ("All Files", "*.*")
                ]
            )
            
            if not file_path:
                return
            
            print(f"📦 Saving track {track_idx} ('{track_name}') template to {file_path}...")
            
            # Get timeline
            timeline = self.timeline
            if timeline is None:
                messagebox.showerror("Save Error", "Timeline not available")
                return
            
            # Collect track data
            track_data = {
                "name": track_name,
                "color": self.mixer.tracks[track_idx].get("color", "#3b82f6"),
                "volume": self.mixer.tracks[track_idx].get("volume", 1.0),
                "pan": self.mixer.tracks[track_idx].get("pan", 0.0),
                "clips": []
            }
            
            # Collect clips
            clips = list(timeline.get_clips_for_track(track_idx))
            for clip in clips:
                clip_data = {
                    "name": clip.name,
                    "start_time": clip.start_time,
                    "duration": clip.duration,
                    "file_path": getattr(clip, 'file_path', None),
                    "color": getattr(clip, 'color', None),
                    "volume": getattr(clip, 'volume', 1.0),
                    "pitch_semitones": getattr(clip, 'pitch_semitones', 0.0),
                    "fade_in": getattr(clip, 'fade_in', 0.0),
                    "fade_out": getattr(clip, 'fade_out', 0.0),
                    "start_offset": getattr(clip, 'start_offset', 0.0),
                    "end_offset": getattr(clip, 'end_offset', 0.0),
                }
                track_data["clips"].append(clip_data)
            
            # Save to JSON file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(track_data, f, indent=2)
            
            # Success message
            messagebox.showinfo(
                "Template Saved",
                f"Track template saved successfully!\n\n"
                f"Track: {track_name}\n"
                f"Clips: {len(clips)}\n"
                f"File: {file_path}"
            )
            
            print(f"✓ Track template saved: {file_path}")
            
        except Exception as e:
            print(f"✗ Delete track error: {e}")
            import traceback
            traceback.print_exc()
            try:
                from tkinter import messagebox
                messagebox.showerror("Delete Error", f"Failed to delete track:\n\n{str(e)}")
            except:
                pass
    
    def _toggle_mute(self, idx=None):
        """Toggle mute for a track (current selection if idx is None)."""
        if idx is None:
            idx = self.get_current_track_index()
        if self.mixer is None or idx is None or idx < 0:
            return
        
        try:
            is_muted = self.mixer.toggle_mute(idx)
            track_name = self.mixer.tracks[idx].get("name", f"Track {idx + 1}")
            
            print(f"🔇 Muted: {track_name}" if is_muted else f"🔊 Unmuted: {track_name}")
            
            # Update button appearance
            if idx in self.mute_buttons:
                self.mute_buttons[idx].configure(bg="#dc2626" if is_muted else "#404040")
        except Exception as e:
            print(f"Error toggling mute: {e}")
    
    def _toggle_solo(self, idx=None):
        """Toggle solo for a track (current selection if idx is None)."""
        if idx is None:
            idx = self.get_current_track_index()
        if self.mixer is None or idx is None or idx < 0:
            return
        
        try:
            is_soloed = self.mixer.toggle_solo(idx)
            track_name = self.mixer.tracks[idx].get("name", f"Track {idx + 1}")
            
            print(f"🎯 Soloed: {track_name}" if is_soloed else f"▶ Unsoloed: {track_name}")
            
            # Update button appearance
            if idx in self.solo_buttons:
                self.solo_buttons[idx].configure(bg="#eab308" if is_soloed else "#404040")
        except Exception as e:
            print(f"Error toggling solo: {e}")
    
    def _update_track_indicators(self):
        """Update track visual indicators - not needed with button-based UI."""
        pass
    
    def _update_track_row(self, idx: int):
        """Update a single track row - not needed with button-based UI."""
        pass
    
    def _on_tree_click(self, event):
        """Old Treeview click handler - no longer used."""
        pass
    
    def _delete_track(self, track_idx):
        """Delete a track from the project."""
        if self.mixer is None or track_idx >= len(self.mixer.tracks):
            return
        
        try:
            from tkinter import messagebox
            
            track_name = self.mixer.tracks[track_idx].get("name", f"Track {track_idx + 1}")
            
            # Confirm deletion
            result = messagebox.askyesno(
                "Delete Track",
                f"Are you sure you want to delete '{track_name}'?\n\n"
                f"This will remove all clips on this track."
            )
            
            if not result:
                return
            
            print(f"🗑️ Deleting track {track_idx} ('{track_name}')...")
            
            # Get timeline
            timeline = self.timeline
            if timeline:
                # Rebuild the placements list:
                # 1. Remove all clips from the deleted track
                # 2. Shift down track indices for tracks after the deleted one
                new_placements = []
                removed_count = 0
                
                for ti, clip in timeline._placements:
                    if ti == track_idx:
                        # Skip clips from the deleted track
                        removed_count += 1
                        continue
                    elif ti > track_idx:
                        # Shift track index down by 1 for tracks after the deleted one
                        new_placements.append((ti - 1, clip))
                    else:
                        # Keep clips from tracks before the deleted one
                        new_placements.append((ti, clip))
                
                timeline._placements = new_placements
                print(f"  Removed {removed_count} clips from track {track_idx}")
                print(f"  Remaining clips: {len(new_placements)}")
            
            # Get project and remove track from project.tracks as well
            project = self.project
            if project and track_idx < len(project.tracks):
                project.tracks.pop(track_idx)
                print(f"  Removed track from project.tracks")
            
            # Remove from mixer
            self.mixer.tracks.pop(track_idx)
            print(f"  Removed track from mixer")
            
            # Repopulate track list
            self.populate_tracks(timeline)
            
            # Redraw timeline
            if self._redraw_cb:
                try:
                    self._redraw_cb()
                except Exception:
                    pass
            
            print(f"✓ Track '{track_name}' deleted successfully")
            
        except Exception as e:
            print(f"✗ Delete track error: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling in sidebar."""
        if self.canvas:
            # Only scroll if content height exceeds canvas height
            try:
                bbox = self.canvas.bbox("all") or (0, 0, 0, 0)
                content_h = max(0, bbox[3] - bbox[1])
                ch = max(1, self.canvas.winfo_height())
                if content_h <= ch + 1:
                    return
            except Exception:
                pass
            # Windows uses event.delta, divide by 120 for smooth scrolling
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _on_canvas_configure(self, event):
        """Update the canvas window width when canvas is resized."""
        if self.canvas and self.canvas_window:
            canvas_width = event.width
            self.canvas.itemconfig(self.canvas_window, width=canvas_width)
