"""Menu bar manager for the main window."""

try:
    import tkinter as tk
    from tkinter import messagebox
except Exception:  # pragma: no cover
    tk = None
    messagebox = None


class MenuManager:
    """Manages the application menu bar."""

    def __init__(self, root, callbacks=None):
        self.root = root
        self.callbacks = callbacks or {}
        self.menubar = None

    def build_menu(self):
        """Build and attach the menu bar."""
        if self.root is None or tk is None:
            return
            
        self.menubar = tk.Menu(
            self.root, bg="#252525", fg="#f5f5f5",
            activebackground="#3b82f6", activeforeground="#ffffff",
            borderwidth=0
        )
        
        self._build_file_menu()
        self._build_edit_menu()
        self._build_view_menu()
        self._build_transport_menu()
        self._build_help_menu()
        
        self.root.config(menu=self.menubar)

    def _build_file_menu(self):
        """Build File menu."""
        file_menu = tk.Menu(
            self.menubar, tearoff=0, bg="#2d2d2d", fg="#f5f5f5",
            activebackground="#3b82f6", activeforeground="#ffffff"
        )
        
        file_menu.add_command(
            label="New Project",
            command=lambda: None,
            accelerator="Ctrl+N"
        )
        file_menu.add_command(
            label="Open Project...",
            command=lambda: None,
            accelerator="Ctrl+O"
        )
        file_menu.add_command(
            label="Save Project",
            command=lambda: None,
            accelerator="Ctrl+S"
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Import Audio...",
            command=self.callbacks.get('import_audio', lambda: None),
            accelerator="Ctrl+I"
        )
        file_menu.add_command(
            label="Browse Audio Files...",
            command=self.callbacks.get('browse_audio', lambda: None),
            accelerator="Ctrl+B"
        )
        file_menu.add_separator()
        
        # Recent files submenu
        recent_menu = tk.Menu(
            file_menu, tearoff=0, bg="#2d2d2d", fg="#f5f5f5",
            activebackground="#3b82f6", activeforeground="#ffffff"
        )
        
        # Get recent files from callback if available
        recent_files = self.callbacks.get('get_recent_files', lambda: [])()
        
        if recent_files:
            for i, file_path in enumerate(recent_files[:10]):  # Max 10 recent files
                import os
                filename = os.path.basename(file_path)
                recent_menu.add_command(
                    label=f"{i+1}. {filename}",
                    command=lambda fp=file_path: self.callbacks.get('import_recent', lambda x: None)(fp)
                )
        else:
            recent_menu.add_command(label="(No recent files)", state="disabled")
        
        file_menu.add_cascade(label="Recent Files", menu=recent_menu)
        
        file_menu.add_separator()
        file_menu.add_command(
            label="Exit",
            command=self.callbacks.get('exit', lambda: None),
            accelerator="Alt+F4"
        )
        
        self.menubar.add_cascade(label="File", menu=file_menu)

    def _build_edit_menu(self):
        """Build Edit menu."""
        edit_menu = tk.Menu(
            self.menubar, tearoff=0, bg="#2d2d2d", fg="#f5f5f5",
            activebackground="#3b82f6", activeforeground="#ffffff"
        )
        
        edit_menu.add_command(
            label="🔁 Duplicate Loop",
            command=self.callbacks.get('duplicate_loop', lambda: None),
            accelerator="Ctrl+D"
        )
        edit_menu.add_separator()
        edit_menu.add_command(
            label="Delete Selected",
            command=self.callbacks.get('delete_clip', lambda: None),
            accelerator="Del"
        )
        
        self.menubar.add_cascade(label="Edit", menu=edit_menu)

    def _build_view_menu(self):
        """Build View menu."""
        view_menu = tk.Menu(
            self.menubar, tearoff=0, bg="#2d2d2d", fg="#f5f5f5",
            activebackground="#3b82f6", activeforeground="#ffffff"
        )
        
        view_menu.add_command(
            label="Zoom In",
            command=self.callbacks.get('zoom_in', lambda: None),
            accelerator="+"
        )
        view_menu.add_command(
            label="Zoom Out",
            command=self.callbacks.get('zoom_out', lambda: None),
            accelerator="-"
        )
        view_menu.add_command(
            label="Fit to Window",
            command=self.callbacks.get('zoom_reset', lambda: None),
            accelerator="0"
        )
        
        self.menubar.add_cascade(label="View", menu=view_menu)

    def _build_transport_menu(self):
        """Build Transport menu."""
        transport_menu = tk.Menu(
            self.menubar, tearoff=0, bg="#2d2d2d", fg="#f5f5f5",
            activebackground="#3b82f6", activeforeground="#ffffff"
        )
        
        transport_menu.add_command(
            label="▶ Play",
            command=self.callbacks.get('play', lambda: None),
            accelerator="Space"
        )
        transport_menu.add_command(
            label="■ Stop",
            command=self.callbacks.get('stop', lambda: None)
        )
        
        self.menubar.add_cascade(label="Transport", menu=transport_menu)

    def _build_help_menu(self):
        """Build Help menu."""
        help_menu = tk.Menu(
            self.menubar, tearoff=0, bg="#2d2d2d", fg="#f5f5f5",
            activebackground="#3b82f6", activeforeground="#ffffff"
        )
        
        help_menu.add_command(
            label="About",
            command=self._show_about
        )
        
        self.menubar.add_cascade(label="Help", menu=help_menu)

    def _show_about(self):
        """Show about dialog."""
        if messagebox is not None:
            messagebox.showinfo(
                "About",
                "Python DAW\nProfessional Digital Audio Workstation\nVersion 1.0"
            )
