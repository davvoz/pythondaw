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
        
        # TTK Style for dynamic colors
        self.style = None
        
    def build_ui(self):
        """Build the track controls UI."""
        if self.parent is None or tk is None:
            return
        
        # Initialize style
        self.style = ttk.Style()
        
        # Track list with Treeview (no header, cleaner look)
        tracks_list_frame = ttk.Frame(self.parent, style="Sidebar.TFrame")
        tracks_list_frame.pack(fill="both", expand=True, padx=12, pady=4)
        
        columns = ("name",)
        self.track_tree = ttk.Treeview(
            tracks_list_frame, columns=columns,
            show="tree headings", selectmode="browse"
        )
        
        self.track_tree.heading("#0", text="")
        self.track_tree.heading("name", text="Track")
        
        self.track_tree.column("#0", width=0, stretch=False)
        self.track_tree.column("name", anchor="w")
        
        self.track_tree.pack(fill="both", expand=True)
        self.track_tree.bind("<<TreeviewSelect>>", self._on_select_track)
        self.track_tree.bind("<Button-3>", self._on_track_right_click)  # Right-click menu
        
        # Track controls section
        self.controls_frame = ttk.Frame(self.parent, style="TrackControl.TFrame")
        self.controls_frame.pack(fill="x", padx=12, pady=(8, 4))
        
        # Separator
        separator = ttk.Frame(self.controls_frame, height=1, style="TrackControl.TFrame")
        separator.pack(fill="x", pady=(0, 8))
        
        # Volume control
        self.vol_row = ttk.Frame(self.controls_frame, style="TrackControl.TFrame")
        self.vol_row.pack(fill="x", pady=2)
        self.vol_label = ttk.Label(
            self.vol_row, text="Vol", style="TrackControl.TLabel",
            width=4, font=("Segoe UI", 8, "bold")
        )
        self.vol_label.pack(side="left")
        
        self.volume_var = tk.DoubleVar(value=1.0)
        vol_scale = ttk.Scale(
            self.vol_row, from_=0.0, to=1.0, orient="horizontal",
            variable=self.volume_var, command=self._on_volume_change
        )
        vol_scale.pack(side="left", fill="x", expand=True, padx=(4, 0))
        
        # Pan control
        self.pan_row = ttk.Frame(self.controls_frame, style="TrackControl.TFrame")
        self.pan_row.pack(fill="x", pady=2)
        self.pan_label = ttk.Label(
            self.pan_row, text="Pan", style="TrackControl.TLabel",
            width=4, font=("Segoe UI", 8, "bold")
        )
        self.pan_label.pack(side="left")
        
        self.pan_var = tk.DoubleVar(value=0.0)
        pan_scale = ttk.Scale(
            self.pan_row, from_=-1.0, to=1.0, orient="horizontal",
            variable=self.pan_var, command=self._on_pan_change
        )
        pan_scale.pack(side="left", fill="x", expand=True, padx=(4, 0))
        
        # Meters section (MASTER OUTPUT - always neutral)
        self.meters_frame = ttk.Frame(self.parent, style="Sidebar.TFrame")
        self.meters_frame.pack(fill="x", padx=12, pady=(8, 12))
        
        self.output_label = ttk.Label(
            self.meters_frame, text="OUTPUT", style="SidebarTitle.TLabel",
            font=("Segoe UI", 8, "bold")
        )
        self.output_label.pack(anchor="w", pady=(0, 4))
        
        # Left meter
        self.meter_L_row = ttk.Frame(self.meters_frame, style="Sidebar.TFrame")
        self.meter_L_row.pack(fill="x", pady=1)
        self.meter_L_label = ttk.Label(
            self.meter_L_row, text="L", style="Sidebar.TLabel",
            width=2, font=("Segoe UI", 8, "bold")
        )
        self.meter_L_label.pack(side="left")
        
        self.meter_L = ttk.Progressbar(
            self.meter_L_row, mode="determinate", maximum=1.0,
            style="Meter.Horizontal.TProgressbar"
        )
        self.meter_L.pack(side="left", fill="x", expand=True, padx=(4, 0))
        
        # Right meter
        self.meter_R_row = ttk.Frame(self.meters_frame, style="Sidebar.TFrame")
        self.meter_R_row.pack(fill="x", pady=1)
        self.meter_R_label = ttk.Label(
            self.meter_R_row, text="R", style="Sidebar.TLabel",
            width=2, font=("Segoe UI", 8, "bold")
        )
        self.meter_R_label.pack(side="left")
        
        self.meter_R = ttk.Progressbar(
            self.meter_R_row, mode="determinate", maximum=1.0,
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
        
        # Add tracks (solo nome, senza # e clips)
        for idx, track in enumerate(self.mixer.tracks):
            name = track.get("name", f"Track {idx+1}")
            color = track.get("color", "#3b82f6")
            
            print(f"  Inserting track {idx}: '{name}'")
            
            self.track_tree.insert(
                "", "end", iid=str(idx),
                values=(name,),
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
        
        # Update control area color to match track color
        self._update_control_colors(idx)
    
    def _on_volume_change(self, value=None):
        """Handle volume change."""
        idx = self.get_current_track_index()
        if self.mixer is None or self.volume_var is None:
            return
        
        # Se nessuna traccia è selezionata, controlla il volume master
        if idx is None:
            try:
                master_vol = float(self.volume_var.get())
                # Applica il volume a tutte le tracce (master)
                for track in self.mixer.tracks:
                    track["volume"] = master_vol
                print(f"🎚️ Master volume set to {master_vol:.2f}")
            except Exception:
                pass
        else:
            try:
                self.mixer.tracks[idx]["volume"] = float(self.volume_var.get())
            except Exception:
                pass
    
    def _on_pan_change(self, value=None):
        """Handle pan change."""
        idx = self.get_current_track_index()
        if self.mixer is None or self.pan_var is None:
            return
        
        # Se nessuna traccia è selezionata, controlla il pan master
        if idx is None:
            try:
                p = float(self.pan_var.get())
                p = max(-1.0, min(1.0, p))  # Clamp to [-1, 1]
                # Applica il pan a tutte le tracce (master)
                for track in self.mixer.tracks:
                    track["pan"] = p
                print(f"🎚️ Master pan set to {p:.2f}")
            except Exception:
                pass
        else:
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
    
    def _update_control_colors(self, track_idx):
        """Update control area background to match track color."""
        if self.mixer is None or track_idx >= len(self.mixer.tracks):
            return
        
        if self.style is None:
            return
        
        try:
            # Get track color
            track_color = self.mixer.tracks[track_idx].get("color", "#3b82f6")
            
            # Convert hex to RGB and darken for background
            track_color = track_color.lstrip('#')
            r, g, b = tuple(int(track_color[i:i+2], 16) for i in (0, 2, 4))
            
            # Darken the color for background (multiply by 0.3 for subtle effect)
            bg_r = int(r * 0.3)
            bg_g = int(g * 0.3)
            bg_b = int(b * 0.3)
            bg_color = f'#{bg_r:02x}{bg_g:02x}{bg_b:02x}'
            
            # White text for better contrast
            fg_color = "#ffffff"
            
            # Configure ttk styles with track color
            self.style.configure(
                "TrackControl.TFrame",
                background=bg_color
            )
            
            self.style.configure(
                "TrackControl.TLabel",
                background=bg_color,
                foreground=fg_color
            )
            
            print(f"✓ Control colors updated to track {track_idx} color: {bg_color}")
                
        except Exception as e:
            print(f"Error updating control colors: {e}")
    
    def _on_track_right_click(self, event):
        """Show context menu for track operations."""
        if self.track_tree is None or tk is None:
            return
        
        # Identify which track was clicked
        item = self.track_tree.identify_row(event.y)
        if not item:
            return
        
        # Select the track
        self.track_tree.selection_set(item)
        track_idx = int(item)
        
        if self.mixer is None or track_idx >= len(self.mixer.tracks):
            return
        
        track_name = self.mixer.tracks[track_idx].get("name", f"Track {track_idx + 1}")
        
        # Create context menu
        menu = tk.Menu(self.track_tree, tearoff=0, bg="#2d2d2d", fg="#f5f5f5", activebackground="#3b82f6")
        
        menu.add_command(
            label=f"💾 Export '{track_name}' as Audio...",
            command=lambda: self._export_track_audio(track_idx)
        )
        
        menu.add_command(
            label=f"📦 Save '{track_name}' as Template...",
            command=lambda: self._save_track_template(track_idx)
        )
        
        menu.add_separator()
        
        menu.add_command(
            label=f"🗑️ Delete '{track_name}'",
            command=lambda: self._delete_track(track_idx)
        )
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
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
                solo_tracks=[track_idx]  # Solo this track
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
            print(f"✗ Save template error: {e}")
            import traceback
            traceback.print_exc()
            try:
                from tkinter import messagebox
                messagebox.showerror("Save Error", f"Failed to save template:\n\n{str(e)}")
            except:
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
