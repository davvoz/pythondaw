"""Canvas manager for timeline - handles canvas creation, layout, and scrolling.

This module encapsulates all canvas widget management to separate UI construction
from business logic.
"""

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover
    tk = None
    ttk = None


class CanvasManager:
    """Manages canvas widgets, layout, and scrolling for timeline.
    
    This class is responsible for:
    - Creating and configuring all canvas widgets (main, controls, rulers)
    - Setting up scrollbars and scroll synchronization
    - Managing canvas dimensions and scroll regions
    - Handling mouse wheel scrolling
    
    Separates UI widget management from timeline logic for better testability.
    """
    
    def __init__(self, geometry):
        """Initialize canvas manager.
        
        Args:
            geometry: TimelineGeometry instance for dimension calculations
        """
        self.geometry = geometry
        
        # Canvas widgets - will be initialized in build()
        self.canvas = None  # Main timeline canvas (scrollable)
        self.controls_canvas = None  # Fixed controls canvas (left side)
        self.ruler_canvas = None  # Fixed ruler canvas (top - scrolls horizontally only)
        self.controls_ruler_canvas = None  # Fixed top-left corner canvas
        
        # Scrollbars
        self.hscroll = None
        self.vscroll = None
        self._hscroll_visible = False
        self._vscroll_visible = False
        
        # Mouse event callbacks - to be set by TimelineCanvas
        self.on_mouse_wheel = None
        self.on_mouse_click = None
        self.on_mouse_drag = None
        self.on_mouse_release = None
        self.on_mouse_motion = None
        self.on_mouse_right_click = None
    
    def build(self, parent):
        """Build all canvas widgets and layout.
        
        Args:
            parent: Parent Tkinter widget
            
        Returns:
            Dict with all created canvas widgets for easy access
        """
        if parent is None or tk is None:
            return {}
        
        # Main container
        container = tk.Frame(parent, bg="#0d0d0d")
        container.pack(fill="both", expand=True)
        
        # Build header row (rulers)
        self._build_header_row(container)
        
        # Build content row (controls + timeline)
        self._build_content_row(container)
        
        # Bind events
        self._bind_events()
        
        return {
            'canvas': self.canvas,
            'controls_canvas': self.controls_canvas,
            'ruler_canvas': self.ruler_canvas,
            'controls_ruler_canvas': self.controls_ruler_canvas,
            'hscroll': self.hscroll,
            'vscroll': self.vscroll
        }
    
    def _build_header_row(self, container):
        """Build header row with ruler canvases.
        
        Args:
            container: Parent container widget
        """
        header_frame = tk.Frame(container, bg="#0d0d0d", height=self.geometry.ruler_height)
        header_frame.pack(side="top", fill="x")
        header_frame.pack_propagate(False)
        
        # Left part of header (above controls) - static corner
        self.controls_ruler_canvas = tk.Canvas(
            header_frame,
            bg="#1a1a1a",
            highlightthickness=0,
            borderwidth=0,
            width=self.geometry.left_margin,
            height=self.geometry.ruler_height
        )
        self.controls_ruler_canvas.pack(side="left", fill="y")
        
        # Right part of header (timeline ruler - scrolls horizontally)
        self.ruler_canvas = tk.Canvas(
            header_frame,
            bg="#1a1a1a",
            highlightthickness=0,
            borderwidth=0,
            height=self.geometry.ruler_height
        )
        self.ruler_canvas.pack(side="left", fill="both", expand=True)
    
    def _build_content_row(self, container):
        """Build content row with controls and timeline canvases.
        
        Args:
            container: Parent container widget
        """
        content_frame = tk.Frame(container, bg="#0d0d0d")
        content_frame.pack(side="top", fill="both", expand=True)
        
        # LEFT: Fixed controls canvas (scrolls vertically only)
        self.controls_canvas = tk.Canvas(
            content_frame,
            bg="#1a1a1a",
            highlightthickness=0,
            borderwidth=0,
            width=self.geometry.left_margin
        )
        self.controls_canvas.pack(side="left", fill="y")
        
        # RIGHT: Scrollable timeline canvas with scrollbars
        timeline_frame = tk.Frame(content_frame, bg="#0d0d0d")
        timeline_frame.pack(side="left", fill="both", expand=True)
        
        self.canvas = tk.Canvas(
            timeline_frame,
            bg="#0d0d0d",
            highlightthickness=0,
            borderwidth=0
        )
        
        # Create scrollbars
        try:
            self.hscroll = ttk.Scrollbar(timeline_frame, orient="horizontal", 
                                        command=self._on_xscroll)
            self.vscroll = ttk.Scrollbar(content_frame, orient="vertical", 
                                        command=self._on_vscroll)
        except Exception:
            self.hscroll = tk.Scrollbar(timeline_frame, orient="horizontal", 
                                       command=self._on_xscroll)
            self.vscroll = tk.Scrollbar(content_frame, orient="vertical", 
                                       command=self._on_vscroll)
        
        # Configure canvas scrolling
        self.canvas.configure(
            xscrollcommand=self._on_xscroll_change,
            yscrollcommand=self._on_yscroll_change
        )
        
        # Layout timeline canvas
        self.canvas.grid(row=0, column=0, sticky="nsew")
        timeline_frame.grid_rowconfigure(0, weight=1)
        timeline_frame.grid_columnconfigure(0, weight=1)
    
    def _bind_events(self):
        """Bind mouse events to all canvases."""
        if self.canvas is None:
            return
        
        # Bind mouse wheel to both main canvas and controls
        for canvas in [self.canvas, self.controls_canvas]:
            if canvas:
                canvas.bind('<MouseWheel>', self._handle_mouse_wheel)
                canvas.bind('<Button-1>', self._handle_click)
                canvas.bind('<B1-Motion>', self._handle_drag)
                canvas.bind('<ButtonRelease-1>', self._handle_release)
                canvas.bind('<Button-3>', self._handle_right_click)
                canvas.bind('<Motion>', self._handle_motion)
        
        # Bind ruler canvas events
        if self.ruler_canvas:
            self.ruler_canvas.bind('<Button-1>', self._handle_click)
            self.ruler_canvas.bind('<B1-Motion>', self._handle_drag)
            self.ruler_canvas.bind('<ButtonRelease-1>', self._handle_release)
            self.ruler_canvas.bind('<Motion>', self._handle_motion)
        
        # Bind resize events
        if self.canvas:
            self.canvas.bind('<Configure>', lambda e: self.update_scrollbars())
        if self.controls_canvas:
            self.controls_canvas.bind('<Configure>', lambda e: self.sync_controls_height())
    
    def _handle_mouse_wheel(self, event):
        """Route mouse wheel events to callback."""
        if self.on_mouse_wheel:
            self.on_mouse_wheel(event)
    
    def _handle_click(self, event):
        """Route click events to callback."""
        if self.on_mouse_click:
            self.on_mouse_click(event)
    
    def _handle_drag(self, event):
        """Route drag events to callback."""
        if self.on_mouse_drag:
            self.on_mouse_drag(event)
    
    def _handle_release(self, event):
        """Route release events to callback."""
        if self.on_mouse_release:
            self.on_mouse_release(event)
    
    def _handle_motion(self, event):
        """Route motion events to callback."""
        if self.on_mouse_motion:
            self.on_mouse_motion(event)
    
    def _handle_right_click(self, event):
        """Route right-click events to callback."""
        if self.on_mouse_right_click:
            self.on_mouse_right_click(event)
    
    def _on_xscroll(self, *args):
        """Handle horizontal scroll - sync timeline and ruler canvases."""
        if self.canvas:
            self.canvas.xview(*args)
        if self.ruler_canvas:
            self.ruler_canvas.xview(*args)
    
    def _on_vscroll(self, *args):
        """Handle vertical scroll - sync timeline and controls canvases."""
        if self.canvas:
            self.canvas.yview(*args)
        if self.controls_canvas:
            self.controls_canvas.yview(*args)
    
    def _on_xscroll_change(self, first, last):
        """Update horizontal scrollbar position."""
        if self.hscroll:
            try:
                self.hscroll.set(first, last)
            except Exception:
                pass
        # Sync ruler canvas
        if self.ruler_canvas:
            try:
                self.ruler_canvas.xview_moveto(float(first))
            except Exception:
                pass
    
    def _on_yscroll_change(self, first, last):
        """Update vertical scrollbar position."""
        if self.vscroll:
            try:
                self.vscroll.set(first, last)
            except Exception:
                pass
    
    def sync_controls_height(self):
        """Synchronize controls canvas scroll region with main canvas height."""
        if self.controls_canvas and self.canvas:
            try:
                bbox = self.canvas.bbox('all')
                if bbox:
                    height = max(0, bbox[3] - bbox[1])
                    self.controls_canvas.config(
                        scrollregion=(0, 0, self.geometry.left_margin, height)
                    )
            except Exception:
                pass
    
    def update_scroll_regions(self, width: int, height: int):
        """Update scroll regions for all canvases.
        
        Args:
            width: Content width in pixels
            height: Content height in pixels
        """
        # Main canvas scrolls both directions
        if self.canvas:
            self.canvas.config(scrollregion=(0, 0, width, height))
        
        # Controls canvas scrolls vertically only
        if self.controls_canvas:
            self.controls_canvas.config(
                scrollregion=(0, 0, self.geometry.left_margin, height)
            )
        
        # Ruler canvas scrolls horizontally only
        if self.ruler_canvas:
            self.ruler_canvas.config(
                scrollregion=(0, 0, width, self.geometry.ruler_height)
            )
    
    def update_scrollbars(self):
        """Show or hide scrollbars based on content size vs viewport size.
        
        This prevents unnecessary scrollbars when content fits in view.
        """
        if self.canvas is None:
            return
        
        try:
            # Get content and viewport dimensions
            bbox = self.canvas.bbox('all')
            if not bbox:
                return
            
            content_w = max(0, bbox[2] - bbox[0])
            content_h = max(0, bbox[3] - bbox[1])
            viewport_w = max(1, self.canvas.winfo_width())
            viewport_h = max(1, self.canvas.winfo_height())
            
            # Determine if scrollbars are needed (with small tolerance)
            need_h = content_w > viewport_w + 1
            need_v = content_h > viewport_h + 1
            
            # Show/hide horizontal scrollbar
            if need_h and not self._hscroll_visible:
                if self.hscroll:
                    self.hscroll.grid(row=1, column=0, sticky='ew')
                    self._hscroll_visible = True
            elif not need_h and self._hscroll_visible:
                if self.hscroll:
                    self.hscroll.grid_remove()
                    self._hscroll_visible = False
                    self.canvas.xview_moveto(0)  # Reset scroll position
            
            # Show/hide vertical scrollbar
            if need_v and not self._vscroll_visible:
                if self.vscroll:
                    self.vscroll.grid(row=0, column=1, sticky='ns')
                    self._vscroll_visible = True
            elif not need_v and self._vscroll_visible:
                if self.vscroll:
                    self.vscroll.grid_remove()
                    self._vscroll_visible = False
                    self.canvas.yview_moveto(0)  # Reset scroll position
        except Exception:
            pass
    
    def clear_all(self):
        """Clear all canvas widgets."""
        for canvas in [self.canvas, self.controls_canvas, self.ruler_canvas, 
                      self.controls_ruler_canvas]:
            if canvas:
                canvas.delete("all")
    
    def reset_view_if_fits(self, width: int, height: int):
        """Reset view to top-left if content fits in viewport.
        
        Args:
            width: Content width
            height: Content height
        """
        if not self.canvas:
            return
        
        try:
            viewport_w = max(1, self.canvas.winfo_width())
            viewport_h = max(1, self.canvas.winfo_height())
            
            # Reset horizontal scroll if content fits
            if width <= viewport_w:
                self.canvas.xview_moveto(0)
                if self.ruler_canvas:
                    self.ruler_canvas.xview_moveto(0)
            
            # Reset vertical scroll if content fits
            if height <= viewport_h:
                self.canvas.yview_moveto(0)
                if self.controls_canvas:
                    self.controls_canvas.yview_moveto(0)
        except Exception:
            pass
