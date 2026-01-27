"""Debug and info overlay for the visualizer."""

from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtCore import QTimer, Qt
import numpy as np
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..visualizer import BaseVisualizer

class DebugOverlay:
    """Handles rendering of FPS and debug information."""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.fps = 0
        self.frame_count = 0
        self.visible = True
        
        # FPS Timer
        self._fps_timer = QTimer()
        self._fps_timer.timeout.connect(self._update_fps)
        self._fps_timer.start(1000)
        
        # Font settings
        self.font = QFont("Monospace", 9)
        self.font.setStyleHint(QFont.TypeWriter)
        
    def _update_fps(self):
        """Update FPS counter once per second."""
        self.fps = self.frame_count
        self.frame_count = 0
        
    def increment_frame(self):
        """Call this every repaint."""
        self.frame_count += 1
        
    def render(self, painter: QPainter, width: int, height: int, 
               visualizer: Optional['BaseVisualizer'], 
               audio_peak: float, is_silent: bool = False):
        """Render the debug overlay."""
        if not self.visible:
            return
            
        painter.save()
        painter.setFont(self.font)
        painter.setPen(QPen(QColor(255, 255, 255, 180)))  # Semi-transparent white
        
        # Draw background for text to ensure readability
        bg_height = 80 if visualizer else 60
        painter.fillRect(5, 5, 200, bg_height, QColor(0, 0, 0, 100))
        
        y_offset = 25
        painter.drawText(15, y_offset, f"FPS: {self.fps}")
        
        if visualizer:
            y_offset += 20
            painter.drawText(15, y_offset, f"Mode: {visualizer.name}")
            
        y_offset += 20
        status = "SILENCE" if is_silent else "ACTIVE"
        painter.drawText(15, y_offset, f"Peak: {audio_peak:.4f} [{status}]")
        
        painter.restore()
