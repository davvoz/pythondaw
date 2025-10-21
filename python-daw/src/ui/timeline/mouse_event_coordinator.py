"""Mouse event coordinator for timeline interactions.

This module routes mouse events to appropriate controllers and handlers,
keeping event handling logic organized and testable.
"""

from typing import Optional, Callable, Any


class MouseEventCoordinator:
    """Coordinates mouse events and routes them to appropriate handlers.
    
    This class acts as a central dispatcher for mouse interactions, delegating
    to specialized controllers for drag, resize, selection, etc.
    
    Separates event routing logic from business logic for better maintainability.
    """
    
    def __init__(self, geometry, canvas_manager):
        """Initialize mouse event coordinator.
        
        Args:
            geometry: TimelineGeometry instance
            canvas_manager: CanvasManager instance
        """
        self.geometry = geometry
        self.canvas_manager = canvas_manager
        
        # Controllers (to be injected)
        self.drag_controller = None
        self.resize_controller = None
        self.box_select_controller = None
        self.loop_marker_controller = None
        self.track_controls_controller = None
        
        # Callbacks for specific event types (to be set by TimelineCanvas)
        self.on_clip_click = None
        self.on_empty_click = None
        self.on_control_click = None
        self.on_loop_selection = None
        self.on_track_selection = None
        
        # State for loop region selection
        self.loop_selection_start = None
    
    def handle_mouse_wheel(self, event, mixer=None):
        """Handle mouse wheel scrolling with proper direction detection.
        
        Args:
            event: Tkinter mouse wheel event
            mixer: Mixer object for track count (optional)
        """
        canvas = self.canvas_manager.canvas
        controls_canvas = self.canvas_manager.controls_canvas
        
        if not canvas:
            return
        
        try:
            # Determine scroll direction and whether scrolling is needed
            bbox = canvas.bbox('all') or (0, 0, 0, 0)
            content_w = max(0, bbox[2] - bbox[0])
            content_h = max(0, bbox[3] - bbox[1])
            viewport_w = max(1, canvas.winfo_width())
            viewport_h = max(1, canvas.winfo_height())
            
            need_h = content_w > viewport_w + 1
            need_v = content_h > viewport_h + 1
            
            # Calculate scroll delta
            delta = (event.delta or -event.num) / 120.0
            
            # Shift key = horizontal scroll
            if event.state & 0x0001:
                if need_h:
                    canvas.xview_scroll(int(-delta * 3), 'units')
            else:
                # Normal wheel = vertical scroll (sync both canvases)
                if need_v:
                    canvas.yview_scroll(int(-delta), 'units')
                    if controls_canvas:
                        controls_canvas.yview_scroll(int(-delta), 'units')
        except Exception:
            pass
    
    def handle_click(self, event, mixer=None, timeline=None, player=None,
                    clip_finder: Optional[Callable] = None,
                    control_finder: Optional[Callable] = None) -> dict:
        """Handle mouse click and route to appropriate handler.
        
        Args:
            event: Tkinter click event
            mixer: Mixer object (optional)
            timeline: Timeline object (optional)
            player: Player object (optional)
            clip_finder: Function to find clip at coordinates
            control_finder: Function to find control at coordinates
            
        Returns:
            Dict with click result info: {'type': ..., 'data': ...}
        """
        widget = event.widget
        canvas = self.canvas_manager.canvas
        controls_canvas = self.canvas_manager.controls_canvas
        ruler_canvas = self.canvas_manager.ruler_canvas
        
        # Handle controls canvas click
        if widget == controls_canvas and controls_canvas:
            x = controls_canvas.canvasx(event.x)
            y = controls_canvas.canvasy(event.y)
            
            if control_finder:
                control = control_finder(x, y)
                if control:
                    if self.on_control_click:
                        self.on_control_click(control, x, y)
                    return {'type': 'control', 'data': control}
            
            # Plain click on controls selects track
            track_idx = self.geometry.y_to_track(y)
            if track_idx is not None and self.on_track_selection:
                self.on_track_selection(track_idx)
                return {'type': 'track_select', 'data': track_idx}
            
            return {'type': 'none'}
        
        # Handle ruler canvas click (loop markers)
        if widget == ruler_canvas and ruler_canvas:
            x = ruler_canvas.canvasx(event.x)
            y = event.y
            
            if self.loop_marker_controller and player:
                marker = self.loop_marker_controller.check_loop_marker_hit(x, y, player)
                if marker:
                    self.loop_marker_controller.start_drag(marker)
                    return {'type': 'loop_marker', 'data': marker}
            
            return {'type': 'none'}
        
        # Handle main canvas click
        if not canvas:
            return {'type': 'none'}
        
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)
        
        # Check modifiers
        ctrl_pressed = event.state & 0x0004
        shift_pressed = event.state & 0x0001
        
        # Check for loop region selection (Shift in ruler)
        if shift_pressed and y <= self.geometry.ruler_height:
            time = self.geometry.x_to_time(x)
            self.loop_selection_start = max(0, time)
            return {'type': 'loop_selection_start', 'data': time}
        
        # Check for box selection (Shift in track area)
        if shift_pressed and y > self.geometry.ruler_height:
            if self.box_select_controller:
                self.box_select_controller.start_selection(x, y)
                return {'type': 'box_selection_start', 'data': (x, y)}
        
        # Check for clip click
        if clip_finder:
            clicked_clip = clip_finder(x, y)
            if clicked_clip:
                track_idx, clip = clicked_clip
                
                # Check for resize edge
                if self.resize_controller:
                    edge = self.resize_controller.check_resize_edge(x, clip, track_idx)
                    if edge and not ctrl_pressed:
                        self.resize_controller.start_resize(clip, track_idx, edge)
                        if canvas:
                            canvas.config(cursor="sb_h_double_arrow")
                        if self.on_clip_click:
                            self.on_clip_click(track_idx, clip, multi=False)
                        return {'type': 'resize_start', 'data': {'clip': clip, 'edge': edge}}
                
                # Regular clip click
                if self.drag_controller and not ctrl_pressed:
                    self.drag_controller.start_drag(clip, track_idx, x)
                
                if self.on_clip_click:
                    self.on_clip_click(track_idx, clip, multi=ctrl_pressed)
                
                return {'type': 'clip_click', 'data': {'track': track_idx, 'clip': clip, 
                                                      'ctrl': ctrl_pressed}}
        
        # Empty area click
        if self.on_empty_click:
            self.on_empty_click(x, y, ctrl_pressed)
        
        return {'type': 'empty_click', 'data': {'x': x, 'y': y, 'ctrl': ctrl_pressed}}
    
    def handle_drag(self, event, mixer=None, player=None) -> dict:
        """Handle mouse drag and route to active controller.
        
        Args:
            event: Tkinter drag event
            mixer: Mixer object (optional)
            player: Player object (optional)
            
        Returns:
            Dict with drag result info
        """
        widget = event.widget
        canvas = self.canvas_manager.canvas
        ruler_canvas = self.canvas_manager.ruler_canvas
        
        # Handle ruler canvas drag (loop markers)
        if widget == ruler_canvas and ruler_canvas:
            x = ruler_canvas.canvasx(event.x)
            if self.loop_marker_controller and self.loop_marker_controller.is_dragging():
                self.loop_marker_controller.update_drag(x, player)
                return {'type': 'loop_marker_drag'}
            return {'type': 'none'}
        
        if not canvas:
            return {'type': 'none'}
        
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)
        
        # Check active operations in priority order
        
        # Loop marker drag
        if self.loop_marker_controller and self.loop_marker_controller.is_dragging():
            self.loop_marker_controller.update_drag(x, player)
            return {'type': 'loop_marker_drag'}
        
        # Volume/pan slider drag
        if self.track_controls_controller:
            if self.track_controls_controller.dragging_volume is not None:
                self.track_controls_controller.update_volume_drag(x, mixer)
                return {'type': 'volume_drag'}
            
            if self.track_controls_controller.dragging_pan is not None:
                self.track_controls_controller.update_pan_drag(x, mixer)
                return {'type': 'pan_drag'}
        
        # Loop region selection
        if self.loop_selection_start is not None:
            end_time = self.geometry.x_to_time(x)
            end_time = max(0, end_time)
            
            # Draw preview
            canvas.delete("loop_preview")
            loop_x_start = self.geometry.time_to_x(
                min(self.loop_selection_start, end_time)
            )
            loop_x_end = self.geometry.time_to_x(
                max(self.loop_selection_start, end_time)
            )
            
            # Calculate height
            height = canvas.winfo_reqheight() or 400
            try:
                bbox = canvas.bbox('all')
                if bbox:
                    height = max(height, bbox[3])
            except Exception:
                pass
            
            canvas.create_rectangle(
                loop_x_start, self.geometry.ruler_height,
                loop_x_end, height,
                fill="#10b981", stipple="gray25", outline="#10b981",
                width=2, tags="loop_preview"
            )
            return {'type': 'loop_selection_drag', 'data': end_time}
        
        # Box selection
        if self.box_select_controller and self.box_select_controller.is_selecting():
            self.box_select_controller.update_selection(canvas, x, y)
            return {'type': 'box_selection_drag'}
        
        # Clip resize
        if self.resize_controller and self.resize_controller.is_resizing():
            self.resize_controller.update_resize(x)
            return {'type': 'resize_drag'}
        
        # Clip drag
        if self.drag_controller and self.drag_controller.is_dragging():
            self.drag_controller.update_drag(x, y, mixer)
            return {'type': 'clip_drag'}
        
        return {'type': 'none'}
    
    def handle_release(self, event, timeline=None, player=None, 
                      snap_func: Optional[Callable] = None) -> dict:
        """Handle mouse release and finalize operations.
        
        Args:
            event: Tkinter release event
            timeline: Timeline object (optional)
            player: Player object (optional)
            snap_func: Function to snap time to grid (optional)
            
        Returns:
            Dict with release result info
        """
        canvas = self.canvas_manager.canvas
        
        # Loop marker release
        if self.loop_marker_controller and self.loop_marker_controller.is_dragging():
            self.loop_marker_controller.end_drag()
            if canvas:
                canvas.config(cursor="")
            if self.canvas_manager.ruler_canvas:
                self.canvas_manager.ruler_canvas.config(cursor="")
            return {'type': 'loop_marker_release'}
        
        # Resize release
        if self.resize_controller and self.resize_controller.is_resizing():
            resize_data = self.resize_controller.end_resize()
            if canvas:
                canvas.config(cursor="")
            return {'type': 'resize_release', 'data': resize_data}
        
        # Volume/pan release
        if self.track_controls_controller:
            if self.track_controls_controller.dragging_volume is not None:
                vol_data = self.track_controls_controller.end_volume_drag()
                return {'type': 'volume_release', 'data': vol_data}
            
            if self.track_controls_controller.dragging_pan is not None:
                pan_data = self.track_controls_controller.end_pan_drag()
                return {'type': 'pan_release', 'data': pan_data}
        
        # Loop region selection release
        if self.loop_selection_start is not None and canvas:
            canvas.delete("loop_preview")
            
            x = canvas.canvasx(event.x)
            end_time = self.geometry.x_to_time(x)
            end_time = max(0, end_time)
            
            start = self.loop_selection_start
            end = end_time
            
            # Apply snapping if provided
            if snap_func:
                start = snap_func(start)
                end = snap_func(end)
            
            # Ensure correct order
            start, end = min(start, end), max(start, end)
            
            self.loop_selection_start = None
            
            # Set loop if valid duration
            if abs(end - start) > 0.1 and player and self.on_loop_selection:
                self.on_loop_selection(start, end, player)
                return {'type': 'loop_selection_complete', 
                       'data': {'start': start, 'end': end}}
            
            return {'type': 'loop_selection_cancel'}
        
        # Box selection release
        if self.box_select_controller and self.box_select_controller.is_selecting() and canvas:
            x = canvas.canvasx(event.x)
            y = canvas.canvasy(event.y)
            selected = self.box_select_controller.complete_selection(canvas, timeline, x, y)
            return {'type': 'box_selection_complete', 'data': selected}
        
        # Drag release
        if self.drag_controller and self.drag_controller.is_dragging():
            drag_data = self.drag_controller.end_drag()
            return {'type': 'drag_release', 'data': drag_data}
        
        return {'type': 'none'}
    
    def handle_motion(self, event, player=None, clip_finder: Optional[Callable] = None,
                     control_finder: Optional[Callable] = None) -> dict:
        """Handle mouse motion for cursor changes.
        
        Args:
            event: Tkinter motion event
            player: Player object (optional)
            clip_finder: Function to find clip at coordinates
            control_finder: Function to find control at coordinates
            
        Returns:
            Dict with motion result info and suggested cursor
        """
        widget = event.widget
        canvas = self.canvas_manager.canvas
        ruler_canvas = self.canvas_manager.ruler_canvas
        
        # Don't change cursor while dragging
        if self._is_any_drag_active():
            return {'type': 'dragging', 'cursor': None}
        
        # Handle ruler canvas motion
        if widget == ruler_canvas and ruler_canvas:
            x = ruler_canvas.canvasx(event.x)
            y = event.y
            
            if self.loop_marker_controller and player:
                marker = self.loop_marker_controller.check_loop_marker_hit(x, y, player)
                if marker:
                    ruler_canvas.config(cursor="sb_h_double_arrow")
                    return {'type': 'loop_marker_hover', 'cursor': 'sb_h_double_arrow'}
                else:
                    ruler_canvas.config(cursor="")
                    return {'type': 'ruler', 'cursor': ''}
        
        if not canvas:
            return {'type': 'none', 'cursor': ''}
        
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)
        
        # Check for control hover
        if control_finder:
            control = control_finder(x, y)
            if control:
                cursor = "hand2" if control.get('type') == 'button' else "sb_h_double_arrow"
                canvas.config(cursor=cursor)
                return {'type': 'control_hover', 'cursor': cursor, 'data': control}
        
        # Check for loop marker hover
        if self.loop_marker_controller and player:
            marker = self.loop_marker_controller.check_loop_marker_hit(x, y, player)
            if marker:
                canvas.config(cursor="sb_h_double_arrow")
                return {'type': 'loop_marker_hover', 'cursor': 'sb_h_double_arrow'}
        
        # Check for clip hover
        if clip_finder:
            clicked_clip = clip_finder(x, y)
            if clicked_clip:
                track_idx, clip = clicked_clip
                
                # Check resize edge
                if self.resize_controller:
                    edge = self.resize_controller.check_resize_edge(x, clip, track_idx)
                    if edge:
                        canvas.config(cursor="sb_h_double_arrow")
                        return {'type': 'resize_hover', 'cursor': 'sb_h_double_arrow'}
                
                canvas.config(cursor="hand2")
                return {'type': 'clip_hover', 'cursor': 'hand2'}
        
        # No special hover
        canvas.config(cursor="")
        return {'type': 'none', 'cursor': ''}
    
    def _is_any_drag_active(self) -> bool:
        """Check if any drag operation is currently active.
        
        Returns:
            True if any controller is dragging
        """
        if self.drag_controller and self.drag_controller.is_dragging():
            return True
        if self.resize_controller and self.resize_controller.is_resizing():
            return True
        if self.loop_marker_controller and self.loop_marker_controller.is_dragging():
            return True
        if self.box_select_controller and self.box_select_controller.is_selecting():
            return True
        if self.track_controls_controller:
            if (self.track_controls_controller.dragging_volume is not None or
                self.track_controls_controller.dragging_pan is not None):
                return True
        if self.loop_selection_start is not None:
            return True
        return False
