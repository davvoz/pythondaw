"""
Project Manager - Handles project lifecycle operations (new, open, save, export).
"""

import os
try:
    from tkinter import filedialog, messagebox
except ImportError:
    filedialog = None
    messagebox = None


class ProjectManager:
    """Manages project file operations and audio export."""
    
    def __init__(self, main_window):
        """Initialize project manager.
        
        Args:
            main_window: Reference to MainWindow instance
        """
        self.window = main_window
        self._project_file_path = None
    
    @property
    def project_file_path(self):
        """Get current project file path."""
        return self._project_file_path
    
    @project_file_path.setter
    def project_file_path(self, value):
        """Set project file path."""
        self._project_file_path = value
    
    def new_project(self):
        """Create a new project."""
        if messagebox is None:
            return
        
        # Check if current project has unsaved changes (future enhancement)
        result = messagebox.askyesno(
            "New Project",
            "Create a new project? Current project will be cleared."
        )
        
        if not result:
            return
        
        # Clear current project
        if self.window.timeline:
            # Remove all clips from timeline using Timeline's API
            all_clips = list(self.window.timeline.all_placements())
            for track_idx, clip in all_clips:
                self.window.timeline.remove_clip(track_idx, clip)
        
        # Reset project properties
        self.window.project.name = "Untitled"
        self.window.project.bpm = 120.0
        self.window.project.time_signature_num = 4
        self.window.project.time_signature_den = 4
        
        # Clear project file path
        self._project_file_path = None
        
        # Update UI
        if self.window._toolbar_manager:
            self.window._toolbar_manager.bpm_var.set(120.0)
        
        if self.window._timeline_canvas:
            self.window._timeline_canvas.redraw()
        
        if self.window._status:
            self.window._status.set("✓ New project created")
        
        self.window._root.title(f"{self.window.title} - Untitled")
    
    def open_project(self):
        """Open an existing project file."""
        if filedialog is None:
            return
        
        file_path = filedialog.askopenfilename(
            title="Open Project",
            filetypes=[
                ("DAW Project", "*.daw"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            if self.window._status:
                self.window._status.set("⏳ Loading project...")
            
            # Load project
            from src.core.project import Project
            loaded_project = Project.load_project(file_path)
            
            # Replace current project
            self.window.project.name = loaded_project.name
            self.window.project.bpm = loaded_project.bpm
            self.window.project.time_signature_num = loaded_project.time_signature_num
            self.window.project.time_signature_den = loaded_project.time_signature_den
            self.window.project.tracks = loaded_project.tracks
            
            # Update timeline - clear existing clips and add loaded ones
            if self.window.timeline:
                # Clear all existing clips from timeline
                self.window.timeline._placements.clear()
                
                # Add all clips from loaded tracks to timeline
                for track_idx, track in enumerate(self.window.project.tracks):
                    print(f"  Track {track_idx}: {len(track.audio_files)} clip(s)")
                    for clip in track.audio_files:
                        # Check if it's a MIDI clip
                        try:
                            from src.midi.clip import MidiClip
                            is_midi = isinstance(clip, MidiClip)
                        except:
                            is_midi = False
                        
                        if is_midi:
                            print(f"    - {clip.name}: {clip.start_time}s, MIDI clip with {len(getattr(clip, 'notes', []))} notes")
                        else:
                            print(f"    - {clip.name}: {clip.start_time}s, buffer={len(clip.buffer)} samples")
                        
                        # Ensure MIDI clips reference the track's synthesizer
                        try:
                            from src.midi.clip import MidiClip
                            if isinstance(clip, MidiClip) and getattr(clip, 'instrument', None) is None:
                                clip.instrument = getattr(track, 'instrument', None)
                        except Exception:
                            pass
                        
                        # Add clip to timeline
                        self.window.timeline.add_clip(track_idx, clip)
            
            # Stop player if running and reset position
            if self.window.player:
                was_playing = self.window.player.is_playing()
                if was_playing:
                    self.window.player.stop()
                self.window.player.set_current_time(0.0)
            
            # Update mixer
            if self.window.mixer:
                # Clear existing tracks
                while self.window.mixer.get_track_count() > 0:
                    self.window.mixer.tracks.pop()
                
                print(f"Loading {len(self.window.project.tracks)} tracks into mixer...")
                
                # Add loaded tracks
                for idx, track in enumerate(self.window.project.tracks):
                    track_name = getattr(track, 'name', None) or f"Track {idx + 1}"
                    track_type = getattr(track, 'type', 'audio')
                    print(f"  Adding mixer track {idx}: '{track_name}' (volume={track.volume}, type={track_type})")
                    self.window.mixer.add_track(
                        name=track_name,
                        volume=track.volume,
                        pan=0.0
                    )
                    # Set track type in mixer
                    self.window.mixer.tracks[-1]["type"] = track_type
                
                print(f"Mixer now has {self.window.mixer.get_track_count()} tracks")
            
            # Update UI
            if self.window._toolbar_manager:
                self.window._toolbar_manager.bpm_var.set(self.window.project.bpm)
            
            if self.window._timeline_canvas:
                self.window._timeline_canvas.redraw()
            
            # Save project file path
            self._project_file_path = file_path
            
            # Update window title
            project_name = os.path.basename(file_path)
            self.window._root.title(f"{self.window.title} - {project_name}")
            
            if self.window._status:
                track_count = len(self.window.project.tracks)
                clip_count = sum(len(track.audio_files) for track in self.window.project.tracks)
                self.window._status.set(
                    f"✓ Loaded '{self.window.project.name}' - "
                    f"{track_count} track(s), {clip_count} clip(s)"
                )
            
            print(f"✓ Project loaded: {file_path}")
            
        except Exception as e:
            if messagebox:
                messagebox.showerror(
                    "Load Error",
                    f"Failed to load project:\n\n{str(e)}"
                )
            if self.window._status:
                self.window._status.set(f"⚠ Failed to load project: {str(e)}")
            print(f"✗ Load error: {e}")
    
    def save_project(self):
        """Save the current project."""
        if self._project_file_path:
            # Save to existing file
            self._do_save_project(self._project_file_path)
        else:
            # No file path yet, do Save As
            self.save_project_as()
    
    def save_project_as(self):
        """Save the current project with a new name."""
        if filedialog is None:
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Project As",
            defaultextension=".daw",
            filetypes=[
                ("DAW Project", "*.daw"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        self._do_save_project(file_path)
        self._project_file_path = file_path
        
        # Update window title
        project_name = os.path.basename(file_path)
        self.window._root.title(f"{self.window.title} - {project_name}")
    
    def _do_save_project(self, file_path: str):
        """Perform the actual save operation.
        
        Args:
            file_path: Path to save the project file
        """
        try:
            if self.window._status:
                self.window._status.set("⏳ Saving project...")
            
            # Sync data from timeline and mixer to project tracks before saving
            if self.window.mixer and self.window.timeline:
                for i in range(len(self.window.mixer.tracks)):
                    mixer_track = self.window.mixer.tracks[i]
                    
                    # Ensure project has corresponding track
                    if i >= len(self.window.project.tracks):
                        print(f"Warning: Track {i} exists in mixer but not in project")
                        continue
                    
                    project_track = self.window.project.tracks[i]
                    
                    # Sync track name from mixer
                    project_track.name = mixer_track.get("name", f"Track {i + 1}")
                    
                    # Sync track volume from mixer
                    project_track.volume = mixer_track.get("volume", 1.0)
                    
                    # Sync clips from timeline to track
                    project_track.audio_files = []
                    clips = self.window.timeline.get_clips_for_track(i)
                    for clip in clips:
                        project_track.audio_files.append(clip)
                    print(f"Syncing track {i}: '{project_track.name}' vol={project_track.volume:.2f} with {len(project_track.audio_files)} clips")
            
            # Save project
            self.window.project.save_project(file_path, embed_audio=False)
            
            if self.window._status:
                size = os.path.getsize(file_path) / 1024  # KB
                track_count = len(self.window.project.tracks)
                clip_count = sum(len(track.audio_files) for track in self.window.project.tracks)
                self.window._status.set(
                    f"✓ Saved '{os.path.basename(file_path)}' - "
                    f"{track_count} track(s), {clip_count} clip(s) ({size:.1f} KB)"
                )
            
            print(f"✓ Project saved: {file_path}")
            
        except Exception as e:
            if messagebox:
                messagebox.showerror(
                    "Save Error",
                    f"Failed to save project:\n\n{str(e)}"
                )
            if self.window._status:
                self.window._status.set(f"⚠ Failed to save project: {str(e)}")
            print(f"✗ Save error: {e}")
    
    def export_audio_dialog(self):
        """Export the song as WAV file, respecting loop if present."""
        if filedialog is None:
            return
        
        # Ask user for file path
        file_path = filedialog.asksaveasfilename(
            title="Export Audio",
            defaultextension=".wav",
            filetypes=[
                ("WAV Audio", "*.wav"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            if self.window._status:
                self.window._status.set("⏳ Exporting audio...")
            
            # Determine export range
            start_time = 0.0
            end_time = 0.0
            use_loop = False
            
            # Check if loop is enabled
            if self.window.player and hasattr(self.window.player, 'loop_enabled') and self.window.player.loop_enabled:
                # Use loop range
                start_time = getattr(self.window.player, 'loop_start', 0.0)
                end_time = getattr(self.window.player, 'loop_end', 0.0)
                use_loop = True
                print(f"🔁 Exporting loop region: {start_time:.3f}s to {end_time:.3f}s")
            else:
                # Find the extent of all clips in the timeline
                if self.window.timeline:
                    max_end = 0.0
                    clip_count = 0
                    for track_idx, clip in self.window.timeline.all_placements():
                        if hasattr(clip, 'end_time'):
                            max_end = max(max_end, clip.end_time)
                            clip_count += 1
                    
                    if clip_count == 0:
                        if messagebox:
                            messagebox.showwarning(
                                "Export Warning",
                                "No clips found in the timeline. Nothing to export."
                            )
                        if self.window._status:
                            self.window._status.set("⚠ No clips to export")
                        return
                    
                    start_time = 0.0
                    end_time = max_end
                    print(f"📄 Exporting full song: 0.0s to {end_time:.3f}s ({clip_count} clips)")
            
            if end_time <= start_time:
                if messagebox:
                    messagebox.showwarning(
                        "Export Warning",
                        "Invalid time range. Cannot export."
                    )
                if self.window._status:
                    self.window._status.set("⚠ Invalid export range")
                return
            
            duration = end_time - start_time
            sample_rate = 44100  # Standard CD quality
            
            # Collect track volumes from the project
            track_volumes = {}
            if self.window.project and self.window.project.tracks:
                for i, track in enumerate(self.window.project.tracks):
                    track_volumes[i] = track.volume
                print(f"📊 Track volumes: {track_volumes}")
            
            # Render the audio using AudioEngine
            from src.audio.engine import AudioEngine
            engine = AudioEngine()
            engine.initialize()
            
            print(f"🎵 Rendering audio: duration={duration:.3f}s, sample_rate={sample_rate} Hz")
            audio_buffer = engine.render_window(
                self.window.timeline,
                start_time=start_time,
                duration=duration,
                sample_rate=sample_rate,
                track_volumes=track_volumes,
                mixer=self.window.mixer,
                project=self.window.project
            )
            
            if not audio_buffer or len(audio_buffer) == 0:
                if messagebox:
                    messagebox.showwarning(
                        "Export Warning",
                        "No audio data to export. The timeline may be empty."
                    )
                if self.window._status:
                    self.window._status.set("⚠ No audio data")
                return
            
            # Save to WAV file
            from src.utils.audio_io import save_audio_file
            save_audio_file(audio_buffer, file_path, sample_rate, format="wav")
            
            # Show success message
            file_size = os.path.getsize(file_path) / 1024  # KB
            if self.window._status:
                loop_text = " (loop region)" if use_loop else ""
                self.window._status.set(
                    f"✓ Exported '{os.path.basename(file_path)}'{loop_text} - "
                    f"{duration:.2f}s, {file_size:.1f} KB"
                )
            
            print(f"✓ Audio exported: {file_path}")
            print(f"  Duration: {duration:.2f}s")
            print(f"  Sample rate: {sample_rate} Hz")
            print(f"  Samples: {len(audio_buffer):,}")
            print(f"  File size: {file_size:.1f} KB")
            
            if messagebox:
                messagebox.showinfo(
                    "Export Complete",
                    f"Audio successfully exported to:\n{file_path}\n\n"
                    f"Duration: {duration:.2f}s\n"
                    f"Sample rate: {sample_rate} Hz\n"
                    f"File size: {file_size:.1f} KB"
                )
                
        except Exception as e:
            if messagebox:
                messagebox.showerror(
                    "Export Error",
                    f"Failed to export audio:\n\n{str(e)}"
                )
            if self.window._status:
                self.window._status.set(f"⚠ Export failed: {str(e)}")
            print(f"✗ Export error: {e}")
            import traceback
            traceback.print_exc()
