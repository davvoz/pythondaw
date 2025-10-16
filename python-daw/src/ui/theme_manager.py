"""Theme manager for applying visual styles to the application."""

try:
    from tkinter import ttk
except Exception:  # pragma: no cover
    ttk = None


class ThemeManager:
    """Manages application theming and visual styles."""
    
    def __init__(self, root):
        self.root = root

    def apply_dark_theme(self):
        """Apply the professional dark theme to the application."""
        if ttk is None:
            return
            
        try:
            style = ttk.Style(self.root)
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

            # Treeview
            style.configure("Treeview",
                            background="#1a1a1a",
                            foreground="#f5f5f5",
                            fieldbackground="#1a1a1a",
                            borderwidth=0,
                            font=("Segoe UI", 9))
            style.configure("Treeview.Heading",
                            background="#252525",
                            foreground="#a0a0a0",
                            borderwidth=0,
                            font=("Segoe UI", 8, "bold"))
            style.map("Treeview",
                     background=[("selected", "#3b82f6")],
                     foreground=[("selected", "#ffffff")])
        except Exception:
            pass
