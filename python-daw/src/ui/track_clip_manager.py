"""Track and Clip management operations - Refactored from MainWindow."""

try:
    from tkinter import messagebox, filedialog
except Exception:
    messagebox = None
    filedialog = None


class TrackClipManager:
    """Manages track and clip operations (add, delete, duplicate, etc.)."""
    
    def __init__(self, window):
        """Initialize the track/clip manager.
        
        Args:
            window: Reference to the MainWindow instance
        """
        self.window = window
    
    @property
    def project(self):
        """Get project from window."""
        return self.window.project
    
    @property
    def mixer(self):
        """Get mixer from window."""
        return self.window.mixer
    
    @property
    def timeline(self):
        """Get timeline from window."""
        return self.window.timeline
    
    @property
    def player(self):
        """Get player from window."""
        return self.window.player
    
    @property
    def _timeline_canvas(self):
        """Get timeline canvas from window."""
        return self.window._timeline_canvas
    
    @property
    def _status(self):
        """Get status var from window."""
        return self.window._status
    
    def _get_current_track_index(self):
        """Get currently selected track index."""
        return self.window._current_track_idx
    
    def _set_current_track_index(self, idx):
        """Set currently selected track index."""
        if idx is not None and 0 <= idx < len(self.mixer.tracks):
            self.window._current_track_idx = idx
    
    # Import methods
    
    def import_audio_dialog(self):
        """Import audio file (WAV, MP3, FLAC, OGG, etc.) and add to selected track."""
        if self.timeline is None or self.mixer is None or filedialog is None:
            return
        
        track_idx = self._get_current_track_index()
        if track_idx is None:
            if self._status:
                self._status.set("⚠ Select a track first")
            return
        
        try:
            # Get supported formats from audio_io utility
            from src.utils.audio_io import get_supported_formats, load_audio_file, get_audio_info
            
            filetypes = get_supported_formats()
            
            file_path = filedialog.askopenfilename(
                title="Import Audio",
                filetypes=filetypes
            )
            
            if not file_path:
                return
            
            # Show loading status
            if self._status:
                self._status.set("⏳ Loading audio file...")
            
            try:
                # Get file info first (fast)
                import os
                clip_name = os.path.splitext(os.path.basename(file_path))[0]
                
                try:
                    info = get_audio_info(file_path)
                    duration = info.get('duration', 0)
                    original_sr = info.get('sample_rate', 44100)
                    
                    # Show info dialog for long files
                    if duration > 60:  # More than 1 minute
                        if messagebox:
                            proceed = messagebox.askyesno(
                                "Large File",
                                f"File duration: {duration:.1f} seconds\n"
                                f"Sample rate: {original_sr} Hz\n"
                                f"This may take a moment to load.\n\n"
                                f"Continue?"
                            )
                            if not proceed:
                                if self._status:
                                    self._status.set("● Ready")
                                return
                except Exception:
                    pass  # Info not available, proceed anyway
                
                # Load the audio file
                target_sr = 44100  # Standard sample rate for DAW
                buffer, sr = load_audio_file(file_path, target_sr=target_sr)
                
                # Get current time for clip placement
                cur = 0.0
                try:
                    cur = float(getattr(self.player, "_current_time", 0.0))
                except Exception:
                    pass
                
                # Create clip
                from src.audio.clip import AudioClip
                clip = AudioClip(clip_name, buffer, sr, start_time=cur, file_path=file_path)
                
                # Add to timeline
                self.timeline.add_clip(track_idx, clip)
                if self._timeline_canvas:
                    self._timeline_canvas.redraw()
                
                # Success feedback
                if self._status:
                    track_name = self.mixer.tracks[track_idx].get("name", f"Track {track_idx+1}")
                    duration_str = f"{clip.length_seconds:.2f}s"
                    size_mb = len(buffer) * 4 / (1024 * 1024)  # Approximate size in MB
                    self._status.set(
                        f"✓ Imported '{clip_name}' to {track_name} "
                        f"({duration_str}, {sr}Hz, {size_mb:.1f}MB)"
                    )
                
                print(f"✓ Successfully imported: {file_path}")
                print(f"  - Duration: {clip.length_seconds:.2f}s")
                print(f"  - Sample rate: {sr} Hz")
                print(f"  - Samples: {len(buffer):,}")
                    
            except ImportError as e:
                if messagebox:
                    messagebox.showerror(
                        "Import Error",
                        f"Required audio library not available.\n\n{str(e)}\n\n"
                        "Install with:\n"
                        "  pip install soundfile\n"
                        "or\n"
                        "  pip install pydub"
                    )
                if self._status:
                    self._status.set("⚠ Audio library missing")
                    
            except Exception as e:
                if messagebox:
                    messagebox.showerror(
                        "Import Error",
                        f"Failed to load audio file:\n\n{str(e)}\n\n"
                        f"File: {os.path.basename(file_path)}"
                    )
                if self._status:
                    self._status.set(f"⚠ Import failed: {str(e)}")
                print(f"✗ Import error: {e}")
                return
                    
        except Exception as e:
            print(f"Import dialog error: {e}")
            if self._status:
                self._status.set("⚠ Import error")
    
    def import_audio_file(self, file_path: str):
        """Import a specific audio file (used by browser and drag-drop).
        
        Args:
            file_path: Absolute path to audio file
        """
        if not self.timeline or not self.mixer:
            return
        
        track_idx = self._get_current_track_index()
        if track_idx is None:
            if self._status:
                self._status.set("⚠ Select a track first")
            return
        
        try:
            from src.utils.audio_io import load_audio_file
            import os
            
            if self._status:
                self._status.set(f"⏳ Loading {os.path.basename(file_path)}...")
            
            # Load file
            buffer, sr = load_audio_file(file_path, target_sr=44100)
            
            # Get clip name
            clip_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # Get current time
            cur = 0.0
            try:
                cur = float(getattr(self.player, "_current_time", 0.0))
            except Exception:
                pass
            
            # Create and add clip
            from src.audio.clip import AudioClip
            clip = AudioClip(clip_name, buffer, sr, start_time=cur, file_path=file_path)
            
            self.timeline.add_clip(track_idx, clip)
            if self._timeline_canvas:
                self._timeline_canvas.redraw()
            
            # Success feedback
            if self._status:
                track_name = self.mixer.tracks[track_idx].get("name", f"Track {track_idx+1}")
                self._status.set(f"✓ Imported '{clip_name}' to {track_name}")
            
            print(f"✓ Imported: {file_path}")
            
        except Exception as e:
            if self._status:
                self._status.set(f"⚠ Failed to import: {str(e)}")
            print(f"✗ Import error: {e}")
    
    # Track management methods
    
    def add_track_dialog(self):
        """Show dialog to add a new track."""
        if self.mixer is None:
            return
        
        try:
            import tkinter as tk
        except:
            return
        
        # Delegate to dialog class
        from .dialogs.add_track_dialog import AddTrackDialog
        
        suggested_name = f"Track {self.mixer.get_track_count() + 1}"
        colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"]
        default_color = colors[self.mixer.get_track_count() % len(colors)]
        
        dialog = AddTrackDialog(self.window._root, suggested_name, colors)
        result = dialog.show()
        
        if not result:
            return
        
        track_name, color, track_type = result
        # Add to mixer with type info
        self.mixer.add_track(name=track_name, volume=1.0, pan=0.0, color=color)
        # annotate last added track with type
        try:
            self.mixer.tracks[-1]["type"] = track_type.lower()
        except Exception:
            pass

        # Also add to project.tracks so it persists in save/load
        from src.core.track import Track
        track = Track(name=track_name)
        track.set_volume(1.0)
        # attach a basic instrument if MIDI
        if track_type.lower() == 'midi':
            try:
                from src.instruments.synthesizer import Synthesizer
                track.instrument = Synthesizer()
            except Exception:
                track.instrument = None
        self.project.create_track(track)
        
        if self._timeline_canvas:
            self._timeline_canvas.redraw()
        
        if self._status:
            self._status.set(f"✓ Track '{track_name}' added")
    
    def add_audio_clip_to_track(self, track_idx):
        """Add an audio clip to a specific track."""
        if self.timeline is None or self.mixer is None or filedialog is None:
            return
        
        if track_idx >= len(self.mixer.tracks):
            if self._status:
                self._status.set("⚠ Invalid track index")
            return
        
        try:
            from src.utils.audio_io import get_supported_formats, load_audio_file
            from src.audio.clip import AudioClip
            import os
            
            filetypes = get_supported_formats()
            
            file_path = filedialog.askopenfilename(
                title="Add Audio Clip",
                filetypes=filetypes
            )
            
            if not file_path:
                return
            
            if self._status:
                self._status.set("⏳ Loading audio file...")
            
            # Load audio file
            target_sr = 44100
            buffer, sr = load_audio_file(file_path, target_sr=target_sr)
            
            # Get current playhead position
            cur = 0.0
            try:
                cur = float(getattr(self.player, "_current_time", 0.0))
            except Exception:
                pass
            
            # Create clip
            clip_name = os.path.splitext(os.path.basename(file_path))[0]
            clip = AudioClip(clip_name, buffer, sr, start_time=cur, file_path=file_path)
            
            # Add to timeline
            self.timeline.add_clip(track_idx, clip)
            if self._timeline_canvas:
                self._timeline_canvas.redraw()
            
            # Success feedback
            track_name = self.mixer.tracks[track_idx].get("name", f"Track {track_idx+1}")
            if self._status:
                self._status.set(f"✓ Added '{clip_name}' to '{track_name}'")
            print(f"🎵 Added clip '{clip_name}' to track {track_idx} ('{track_name}')")
            
        except Exception as e:
            if self._status:
                self._status.set(f"⚠ Error loading audio: {e}")
            print(f"Error loading audio: {e}")

    def add_midi_demo_clip_to_track(self, track_idx):
        """Add an empty MIDI clip to a MIDI track."""
        if self.timeline is None or self.mixer is None:
            return
        try:
            # Validate track type
            track_type = (self.mixer.tracks[track_idx].get("type") or "audio").lower()
            if track_type != 'midi':
                if self._status:
                    self._status.set("⚠ Selected track is not a MIDI track")
                return
            from src.midi.clip import MidiClip
            # pick instrument from project track if present
            instrument = None
            if self.project and hasattr(self.project, 'tracks') and track_idx < len(self.project.tracks):
                instrument = getattr(self.project.tracks[track_idx], 'instrument', None)
            if instrument is None:
                try:
                    from src.instruments.synthesizer import Synthesizer
                    instrument = Synthesizer()
                except Exception:
                    instrument = None

            # Create empty clip at current time with 4 seconds default length
            cur = 0.0
            try:
                cur = float(getattr(self.player, "_current_time", 0.0))
            except Exception:
                pass
            
            # Empty notes list - user will add notes via Piano Roll
            notes = []
            mclip = MidiClip(name="MIDI Clip", notes=notes, start_time=cur, duration=4.0, color="#22c55e", instrument=instrument)
            
            self.timeline.add_clip(track_idx, mclip)
            if self._timeline_canvas:
                self._timeline_canvas.redraw()
            if self._status:
                tn = self.mixer.tracks[track_idx].get("name", f"Track {track_idx+1}")
                self._status.set(f"✓ Added empty MIDI clip to '{tn}' - Double-click to edit notes")
        except Exception as e:
            print(f"Error adding MIDI clip: {e}")
    
    def edit_track_synth(self, track_idx):
        """Open synthesizer editor for a MIDI track."""
        if self.project is None or self.mixer is None:
            return
        
        try:
            # Validate track type
            track_type = (self.mixer.tracks[track_idx].get("type") or "audio").lower()
            if track_type != 'midi':
                if self._status:
                    self._status.set("⚠ Selected track is not a MIDI track")
                return
            
            # Get track and synthesizer
            if track_idx >= len(self.project.tracks):
                if self._status:
                    self._status.set("⚠ Track not found in project")
                return
            
            track = self.project.tracks[track_idx]
            synth = getattr(track, 'instrument', None)
            
            if synth is None:
                # Create a new synthesizer if none exists
                from src.instruments.synthesizer import Synthesizer
                synth = Synthesizer()
                track.instrument = synth
                print(f"✓ Created new synthesizer for track {track_idx + 1}")
            
            # Open synth editor
            from .synth_editor import show_synth_editor
            track_name = self.mixer.tracks[track_idx].get("name", f"Track {track_idx + 1}")
            
            def on_synth_change(s):
                """Called when synth parameters change."""
                # No need to redraw timeline, but could update status
                if self._status:
                    self._status.set(f"🎛️ Synth updated: {track_name}")
            
            show_synth_editor(self.window._root, synth, track_name, on_apply=on_synth_change)
            
        except Exception as e:
            if self._status:
                self._status.set(f"⚠ Error opening synth editor: {e}")
            print(f"Error opening synth editor: {e}")
            import traceback
            traceback.print_exc()
    
    def rename_track(self, track_idx):
        """Rename a track."""
        if self.mixer is None or track_idx >= len(self.mixer.tracks):
            return
        
        import tkinter.simpledialog as simpledialog
        current_name = self.mixer.tracks[track_idx].get("name", f"Track {track_idx+1}")
        
        new_name = simpledialog.askstring(
            "Rename Track",
            f"Enter new name for '{current_name}':",
            initialvalue=current_name
        )
        
        if new_name and new_name.strip():
            self.mixer.tracks[track_idx]["name"] = new_name.strip()
            if self._timeline_canvas:
                self._timeline_canvas.redraw()
            if self._status:
                self._status.set(f"✓ Track renamed to '{new_name.strip()}'")
    
    def delete_track(self, track_idx):
        """Delete a track."""
        if self.mixer is None or track_idx >= len(self.mixer.tracks):
            return
        
        track_name = self.mixer.tracks[track_idx].get("name", f"Track {track_idx+1}")
        
        # Confirm deletion
        if messagebox:
            confirm = messagebox.askyesno(
                "Delete Track",
                f"Are you sure you want to delete '{track_name}'?\nAll clips on this track will be removed."
            )
            if not confirm:
                return
        try:
            # Remove from timeline placements and shift indices after deleted track
            if self.timeline and hasattr(self.timeline, '_placements'):
                new_placements = []
                for ti, clip in self.timeline._placements:
                    if ti == track_idx:
                        continue  # drop clips on deleted track
                    elif ti > track_idx:
                        new_placements.append((ti - 1, clip))
                    else:
                        new_placements.append((ti, clip))
                self.timeline._placements = new_placements

            # Remove from project.tracks if present
            if self.project and hasattr(self.project, 'tracks') and track_idx < len(self.project.tracks):
                try:
                    self.project.tracks.pop(track_idx)
                except Exception:
                    pass

            # Remove from mixer
            self.mixer.tracks.pop(track_idx)

            # Update selection to a valid index
            if hasattr(self.window, '_current_track_idx'):
                if self.window._current_track_idx is not None:
                    if len(self.mixer.tracks) == 0:
                        self.window._current_track_idx = None
                    else:
                        self.window._current_track_idx = max(0, min(self.window._current_track_idx, len(self.mixer.tracks) - 1))
            # Reflect selection in canvas
            if self._timeline_canvas and hasattr(self._timeline_canvas, 'selected_track_idx'):
                sel = self._timeline_canvas.selected_track_idx
                if sel is not None:
                    if len(self.mixer.tracks) == 0:
                        self._timeline_canvas.selected_track_idx = None
                    else:
                        self._timeline_canvas.selected_track_idx = max(0, min(sel if sel != track_idx else sel - 1, len(self.mixer.tracks) - 1))

            # Redraw UI immediately
            if self._timeline_canvas:
                self._timeline_canvas.redraw()

            if self._status:
                self._status.set(f"✓ Track '{track_name}' deleted")
        except Exception as e:
            if self._status:
                self._status.set(f"⚠ Failed to delete track: {e}")
            print(f"Delete track error: {e}")
    
    def duplicate_track(self, track_idx):
        """Duplicate a track with all its clips."""
        if self.mixer is None or track_idx >= len(self.mixer.tracks):
            return
        
        # Duplicate mixer track
        original_track = self.mixer.tracks[track_idx]
        new_track = {
            "name": original_track.get("name", f"Track {track_idx+1}") + " (copy)",
            "volume": original_track.get("volume", 1.0),
            "pan": original_track.get("pan", 0.0),
            "mute": original_track.get("mute", False),
            "solo": original_track.get("solo", False),
            "color": original_track.get("color", "#3b82f6")
        }
        self.mixer.tracks.append(new_track)
        
        # Duplicate timeline clips
        self.timeline.tracks.append([])
        for clip in self.timeline.tracks[track_idx]:
            new_clip = clip.copy()
            self.timeline.tracks[-1].append(new_clip)
        
        if self._timeline_canvas:
            self._timeline_canvas.redraw()
        
        if self._status:
            self._status.set(f"✓ Track duplicated: '{new_track['name']}'")
    
    def change_track_color(self, track_idx):
        """Change the color of a track."""
        if self.mixer is None or track_idx >= len(self.mixer.tracks):
            return
        
        from tkinter import colorchooser
        
        current_color = self.mixer.tracks[track_idx].get("color", "#3b82f6")
        color = colorchooser.askcolor(
            title="Choose Track Color",
            initialcolor=current_color
        )
        
        if color and color[1]:  # color[1] is the hex value
            self.mixer.tracks[track_idx]["color"] = color[1]
            if self._timeline_canvas:
                self._timeline_canvas.redraw()
            if self._status:
                self._status.set(f"✓ Track color changed")
    
    # Clip management methods
    
    def delete_selected_clip(self):
        """Delete the selected clip."""
        if not self._timeline_canvas:
            return
        
        selected = self._timeline_canvas.get_selected_clip()
        if not selected:
            return
        
        track_idx, clip = selected
        self.timeline.remove_clip(track_idx, clip)
        self._timeline_canvas.selected_clip = None
        self._timeline_canvas.selected_clips = []
        if self._timeline_canvas:
            self._timeline_canvas.redraw()
        
        if self._status:
            self._status.set(f"✓ Deleted clip '{clip.name}'")
    
    def delete_selected_clips(self):
        """Delete all selected clips."""
        if not self._timeline_canvas:
            return
        
        selected_clips = self._timeline_canvas.get_selected_clips()
        if not selected_clips:
            return
        
        count = len(selected_clips)
        
        for track_idx, clip in selected_clips:
            self.timeline.remove_clip(track_idx, clip)
        
        self._timeline_canvas.clear_selection()
        if self._timeline_canvas:
            self._timeline_canvas.redraw()
        
        if self._status:
            self._status.set(f"✓ Deleted {count} clip(s)")
    
    def copy_selection(self):
        """Copy selected clips to clipboard."""
        if not self._timeline_canvas:
            return
        
        if self._timeline_canvas.copy_selected_clips():
            if self._status:
                count = len(self._timeline_canvas.clipboard)
                self._status.set(f"📋 Copied {count} clip(s)")
        else:
            if self._status:
                self._status.set("⚠ No clips selected to copy")
    
    def paste_clips(self):
        """Paste clips from clipboard."""
        if not self._timeline_canvas:
            return
        
        if not self._timeline_canvas.clipboard:
            if self._status:
                self._status.set("⚠ Clipboard is empty")
            return
        
        pasted_clips = self._timeline_canvas.paste_clips()
        
        if pasted_clips:
            if self._timeline_canvas:
                self._timeline_canvas.redraw()
            if self._status:
                self._status.set(f"📌 Pasted {len(pasted_clips)} clip(s)")
        else:
            if self._status:
                self._status.set("⚠ Failed to paste clips")
    
    def copy_loop(self):
        """Copy all clips within the loop region to clipboard."""
        if not self.player or not self.timeline or not self._timeline_canvas:
            if self._status:
                self._status.set("⚠ No player or timeline available")
            return
        
        try:
            loop_enabled, loop_start, loop_end = self.player.get_loop()
            
            if not loop_enabled:
                if self._status:
                    self._status.set("⚠ Loop is not enabled. Set loop points first (Shift+drag on timeline)")
                return
            
            # Get all clips in the loop region
            clips_in_loop = list(self.timeline.get_clips_for_range(loop_start, loop_end))
            
            if not clips_in_loop:
                if self._status:
                    self._status.set("⚠ No clips found in loop region")
                return
            
            # Select clips in loop and copy them
            self._timeline_canvas.selected_clips = clips_in_loop
            
            if self._timeline_canvas.copy_selected_clips():
                if self._status:
                    count = len(clips_in_loop)
                    self._status.set(f"📋 Copied loop region: {count} clip(s) | {loop_start:.2f}s - {loop_end:.2f}s")
                print(f"🔁 Copied {count} clips from loop region [{loop_start:.3f}s - {loop_end:.3f}s]")
        
        except Exception as e:
            if self._status:
                self._status.set(f"⚠ Error copying loop: {e}")
            print(f"Error copying loop: {e}")
    
    def paste_loop(self):
        """Paste clips from loop clipboard at loop end position."""
        if not self.player or not self.timeline or not self._timeline_canvas:
            if self._status:
                self._status.set("⚠ No player or timeline available")
            return
        
        if not self._timeline_canvas.clipboard:
            if self._status:
                self._status.set("⚠ Clipboard is empty")
            return
        
        try:
            loop_enabled, loop_start, loop_end = self.player.get_loop()
            
            if not loop_enabled:
                # Paste at current time if no loop
                self.paste_clips()
                return
            
            # Paste at loop end
            pasted_clips = self._timeline_canvas.paste_clips(at_time=loop_end)
            
            if pasted_clips:
                if self._timeline_canvas:
                    self._timeline_canvas.redraw()
                if self._status:
                    self._status.set(f"📌 Pasted {len(pasted_clips)} clip(s) at loop end ({loop_end:.2f}s)")
            else:
                if self._status:
                    self._status.set("⚠ Failed to paste clips")
        
        except Exception as e:
            if self._status:
                self._status.set(f"⚠ Error pasting loop: {e}")
            print(f"Error pasting loop: {e}")

    def duplicate_selected_clip(self):
        """Duplicate the selected clip."""
        if not self._timeline_canvas:
            return
        
        selected = self._timeline_canvas.get_selected_clip()
        if not selected:
            return
        
        track_idx, clip = selected
        
        # Create cloned clip carrying all editing properties
        new_start = clip.end_time + 0.1
        new_clip = self._clone_clip(clip, new_start, name=f"{clip.name} (copy)")
        
        self.timeline.add_clip(track_idx, new_clip)
        self._timeline_canvas.select_clip(track_idx, new_clip)
        if self._timeline_canvas:
            self._timeline_canvas.redraw()
        
        if self._status:
            self._status.set(f"✓ Duplicated clip '{clip.name}'")

    def duplicate_loop(self):
        """Duplicate all clips within the current loop region."""
        if not self.player or not self.timeline:
            if self._status:
                self._status.set("⚠ No player or timeline available")
            return
        
        try:
            loop_enabled, loop_start, loop_end = self.player.get_loop()
            
            if not loop_enabled:
                if self._status:
                    self._status.set("⚠ Loop is not enabled. Set loop points first (Shift+drag on timeline)")
                return
            
            # Get all clips in the loop region
            clips_in_loop = list(self.timeline.get_clips_for_range(loop_start, loop_end))
            
            if not clips_in_loop:
                if self._status:
                    self._status.set("⚠ No clips found in loop region")
                return
            
            loop_duration = loop_end - loop_start
            
            # Duplicate each clip
            duplicated_count = 0
            
            for track_idx, clip in clips_in_loop:
                # Calculate offset from loop start
                clip_offset_from_loop_start = clip.start_time - loop_start
                
                # Calculate new start time (right after the loop end)
                new_start_time = loop_end + clip_offset_from_loop_start
                
                # Clone clip with all properties (trim/fades/pitch/color/file_path/duration)
                new_clip = self._clone_clip(clip, new_start_time)
                
                self.timeline.add_clip(track_idx, new_clip)
                duplicated_count += 1
            
            # Update UI
            if self._timeline_canvas:
                self._timeline_canvas.redraw()
            
            if self._status:
                self._status.set(f"✓ Duplicated loop region: {duplicated_count} clip(s) | {loop_start:.2f}s - {loop_end:.2f}s")
            
            print(f"🔁 Duplicated {duplicated_count} clips from loop region [{loop_start:.3f}s - {loop_end:.3f}s]")
            
        except Exception as e:
            if self._status:
                self._status.set(f"⚠ Error duplicating loop: {e}")
            print(f"Error duplicating loop: {e}")

    def _clone_clip(self, clip, new_start_time: float, name=None):
        """Create a new clip (Audio or MIDI) copying all user-editable properties.
        
        Args:
            clip: Source clip to clone (AudioClip or MidiClip)
            new_start_time: Start time for the new clip
            name: Optional name override (defaults to source clip name)
            
        Returns:
            New clip instance with all properties copied
        """
        # Try to detect MIDI vs Audio at runtime to avoid hard imports up-top
        try:
            from src.midi.clip import MidiClip
            from src.midi.note import MidiNote
            is_midi = isinstance(clip, MidiClip)
        except Exception:
            MidiClip = None  # type: ignore
            MidiNote = None  # type: ignore
            is_midi = False

        if is_midi:
            # Deep copy notes; note times are clip-local, so keep as-is
            try:
                notes = [
                    MidiNote(pitch=n.pitch, start=n.start, duration=n.duration, velocity=getattr(n, 'velocity', 100))
                    for n in getattr(clip, 'notes', [])
                ] if MidiNote is not None else []
            except Exception:
                notes = []

            new_clip = MidiClip(
                name=name or clip.name,
                notes=notes,
                start_time=new_start_time,
                duration=getattr(clip, 'duration', None),
                color=getattr(clip, 'color', None),
                instrument=getattr(clip, 'instrument', None),
                sample_rate=getattr(clip, 'sample_rate', 44100),
            )
            return new_clip

        # Fallback: treat as AudioClip
        from src.audio.clip import AudioClip

        new_clip = AudioClip(
            name or getattr(clip, 'name', 'clip'),
            getattr(clip, 'buffer', []),
            getattr(clip, 'sample_rate', 44100),
            new_start_time,
            duration=getattr(clip, 'duration', None),
            color=getattr(clip, 'color', None),
            file_path=getattr(clip, 'file_path', None),
        )

        # Copy editing properties (trim, fades, pitch, volume) when available
        try:
            new_clip.start_offset = getattr(clip, 'start_offset', 0.0)
            new_clip.end_offset = getattr(clip, 'end_offset', 0.0)
            new_clip.fade_in = getattr(clip, 'fade_in', 0.0)
            new_clip.fade_in_shape = getattr(clip, 'fade_in_shape', 'linear')
            new_clip.fade_out = getattr(clip, 'fade_out', 0.0)
            new_clip.fade_out_shape = getattr(clip, 'fade_out_shape', 'linear')
            new_clip.pitch_semitones = getattr(clip, 'pitch_semitones', 0.0)
            new_clip.volume = getattr(clip, 'volume', 1.0)
        except Exception:
            pass

        return new_clip

    def show_clip_properties(self):
        """Open Clip Inspector to edit clip parameters (trim/fade/pitch)."""
        if not self._timeline_canvas:
            return

        selected = self._timeline_canvas.get_selected_clip()
        if not selected:
            return

        track_idx, clip = selected

        try:
            from .clip_inspector import show_clip_inspector
        except Exception:
            show_clip_inspector = None

        if show_clip_inspector is None or self.window._root is None:
            # Fallback: simple message box with info
            if messagebox is None:
                return
            
            # Check if it's a MIDI clip
            try:
                from src.midi.clip import MidiClip
                is_midi = isinstance(clip, MidiClip)
            except:
                is_midi = False
            
            if is_midi:
                props = f"""MIDI Clip Properties

Name: {clip.name}
Start Time: {clip.start_time:.3f} s
End Time: {clip.end_time:.3f} s
Duration: {clip.length_seconds:.3f} s
Sample Rate: {clip.sample_rate} Hz
Notes: {len(getattr(clip, 'notes', []))}
"""
            else:
                props = f"""Clip Properties

Name: {clip.name}
Start Time: {clip.start_time:.3f} s
End Time: {clip.end_time:.3f} s
Duration: {clip.length_seconds:.3f} s
Sample Rate: {clip.sample_rate} Hz
Samples: {len(clip.buffer)}
"""
                if hasattr(clip, 'file_path') and clip.file_path:
                    props += f"\nSource: {clip.file_path}"
            messagebox.showinfo("Clip Properties", props)
            return

        def on_apply(_clip):
            # Redraw timeline to reflect changes (length/peaks)
            if self._timeline_canvas:
                self._timeline_canvas.redraw()

        show_clip_inspector(self.window._root, clip, on_apply=on_apply, player=self.player)
