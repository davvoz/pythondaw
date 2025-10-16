"""Audio file browser and drag-drop support for the DAW."""

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DRAG_DROP_AVAILABLE = True
except ImportError:
    tk = None
    ttk = None
    messagebox = None
    DRAG_DROP_AVAILABLE = False

import os
from typing import Callable, Optional


class AudioBrowser:
    """Audio file browser with preview and drag-drop support."""
    
    def __init__(self, parent, on_file_selected: Optional[Callable] = None):
        self.parent = parent
        self.on_file_selected = on_file_selected
        self.window = None
        
    def show(self):
        """Show the audio browser window."""
        if tk is None:
            print("Audio browser not available (tkinter not installed)")
            return
        
        self.window = tk.Toplevel(self.parent)
        self.window.title("Audio Browser")
        self.window.geometry("600x400")
        self.window.configure(bg="#2d2d2d")
        
        # Center window
        self.window.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - 300
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - 200
        self.window.geometry(f"+{x}+{y}")
        
        self._build_ui()
        
    def _build_ui(self):
        """Build the browser UI."""
        # Header
        header = ttk.Frame(self.window, style="Sidebar.TFrame")
        header.pack(fill="x", padx=12, pady=12)
        
        ttk.Label(
            header, text="📁 Audio Files",
            style="Sidebar.TLabel",
            font=("Segoe UI", 12, "bold")
        ).pack(side="left")
        
        ttk.Button(
            header, text="Browse...",
            command=self._browse_folder,
            style="Tool.TButton"
        ).pack(side="right")
        
        # Path display
        self.path_var = tk.StringVar(value=os.path.expanduser("~"))
        path_frame = ttk.Frame(self.window, style="Sidebar.TFrame")
        path_frame.pack(fill="x", padx=12, pady=(0, 8))
        
        ttk.Label(
            path_frame, text="Path:",
            style="Sidebar.TLabel"
        ).pack(side="left", padx=(0, 8))
        
        path_entry = ttk.Entry(
            path_frame, textvariable=self.path_var,
            state="readonly"
        )
        path_entry.pack(side="left", fill="x", expand=True)
        
        # File list
        list_frame = ttk.Frame(self.window, style="Sidebar.TFrame")
        list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Listbox with audio files
        self.file_list = tk.Listbox(
            list_frame,
            bg="#1a1a1a", fg="#f5f5f5",
            selectmode="single",
            font=("Segoe UI", 10),
            yscrollcommand=scrollbar.set
        )
        self.file_list.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.file_list.yview)
        
        # Double-click to select
        self.file_list.bind('<Double-Button-1>', self._on_file_double_click)
        
        # Preview section
        preview_frame = ttk.Frame(self.window, style="Sidebar.TFrame")
        preview_frame.pack(fill="x", padx=12, pady=(0, 12))
        
        ttk.Label(
            preview_frame, text="Preview:",
            style="Sidebar.TLabel",
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")
        
        self.preview_text = tk.Text(
            preview_frame, height=4,
            bg="#1a1a1a", fg="#f5f5f5",
            font=("Consolas", 9),
            state="disabled"
        )
        self.preview_text.pack(fill="x", pady=(4, 0))
        
        # File selection change
        self.file_list.bind('<<ListboxSelect>>', self._on_file_select)
        
        # Buttons
        btn_frame = ttk.Frame(self.window, style="Sidebar.TFrame")
        btn_frame.pack(fill="x", padx=12, pady=(0, 12))
        
        ttk.Button(
            btn_frame, text="Cancel",
            command=self.window.destroy,
            style="Tool.TButton"
        ).pack(side="right", padx=(8, 0))
        
        ttk.Button(
            btn_frame, text="Import",
            command=self._on_import,
            style="Tool.TButton"
        ).pack(side="right")
        
        # Load current directory
        self._load_directory(self.path_var.get())
        
    def _browse_folder(self):
        """Browse for a folder."""
        from tkinter import filedialog
        
        folder = filedialog.askdirectory(
            title="Select Audio Folder",
            initialdir=self.path_var.get()
        )
        
        if folder:
            self.path_var.set(folder)
            self._load_directory(folder)
    
    def _load_directory(self, path: str):
        """Load audio files from directory."""
        self.file_list.delete(0, tk.END)
        
        if not os.path.exists(path):
            return
        
        # Supported extensions
        audio_exts = {'.wav', '.mp3', '.flac', '.ogg', '.aac', '.m4a'}
        
        try:
            files = []
            for filename in os.listdir(path):
                ext = os.path.splitext(filename)[1].lower()
                if ext in audio_exts:
                    files.append(filename)
            
            # Sort files
            files.sort()
            
            # Add to listbox with icons
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                icon = "🎵"
                if ext == '.wav':
                    icon = "🎼"
                elif ext == '.mp3':
                    icon = "🎧"
                elif ext in ['.flac', '.ogg']:
                    icon = "🎶"
                
                self.file_list.insert(tk.END, f"{icon} {filename}")
                
        except Exception as e:
            print(f"Error loading directory: {e}")
    
    def _on_file_select(self, event=None):
        """Handle file selection."""
        selection = self.file_list.curselection()
        if not selection:
            return
        
        # Get filename (remove icon)
        filename = self.file_list.get(selection[0]).split(" ", 1)[1]
        file_path = os.path.join(self.path_var.get(), filename)
        
        # Show preview
        self._show_preview(file_path)
    
    def _show_preview(self, file_path: str):
        """Show file preview information."""
        self.preview_text.config(state="normal")
        self.preview_text.delete("1.0", tk.END)
        
        try:
            from src.utils.audio_io import get_audio_info
            
            info = get_audio_info(file_path)
            
            preview = f"File: {os.path.basename(file_path)}\n"
            
            if 'duration' in info:
                duration = info['duration']
                mins = int(duration // 60)
                secs = duration % 60
                preview += f"Duration: {mins}:{secs:05.2f}\n"
            
            if 'sample_rate' in info:
                preview += f"Sample Rate: {info['sample_rate']} Hz\n"
            
            if 'channels' in info:
                ch = "Mono" if info['channels'] == 1 else f"{info['channels']} channels"
                preview += f"Channels: {ch}\n"
            
            if 'size' in info:
                size_mb = info['size'] / (1024 * 1024)
                preview += f"Size: {size_mb:.2f} MB\n"
            
            self.preview_text.insert("1.0", preview)
            
        except Exception as e:
            self.preview_text.insert("1.0", f"Error loading preview:\n{str(e)}")
        
        self.preview_text.config(state="disabled")
    
    def _on_file_double_click(self, event=None):
        """Handle double-click on file."""
        self._on_import()
    
    def _on_import(self):
        """Import selected file."""
        selection = self.file_list.curselection()
        if not selection:
            if messagebox:
                messagebox.showwarning("No Selection", "Please select a file to import.")
            return
        
        # Get filename (remove icon)
        filename = self.file_list.get(selection[0]).split(" ", 1)[1]
        file_path = os.path.join(self.path_var.get(), filename)
        
        # Call callback
        if self.on_file_selected:
            self.on_file_selected(file_path)
        
        self.window.destroy()


def setup_drag_drop(canvas, on_drop_callback: Callable):
    """Setup drag-and-drop support for a canvas.
    
    Args:
        canvas: tkinter Canvas widget
        on_drop_callback: Function to call with file path when file is dropped
    """
    if not DRAG_DROP_AVAILABLE:
        print("Drag-drop not available (tkinterdnd2 not installed)")
        return
    
    def on_drop(event):
        """Handle file drop event."""
        files = canvas.tk.splitlist(event.data)
        
        # Filter audio files
        audio_exts = {'.wav', '.mp3', '.flac', '.ogg', '.aac', '.m4a'}
        
        for file_path in files:
            ext = os.path.splitext(file_path)[1].lower()
            if ext in audio_exts:
                on_drop_callback(file_path)
                break  # Only import first valid file
    
    # Register drop target
    try:
        canvas.drop_target_register(DND_FILES)
        canvas.dnd_bind('<<Drop>>', on_drop)
        print("✓ Drag-drop enabled for timeline")
    except Exception as e:
        print(f"Could not enable drag-drop: {e}")
