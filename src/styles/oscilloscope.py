from __future__ import annotations
"""Oscilloscope visualization style."""

import numpy as np
from PySide6.QtGui import QPainter, QPen, QPainterPath, QColor
from PySide6.QtCore import Qt
from visualizer import BaseVisualizer


class Oscilloscope(BaseVisualizer):
    """Oscilloscope display with Lissajous curves."""
    
    def __init__(self):
        """Initialize oscilloscope visualizer."""
        super().__init__("Oscilloscope")
        self.line_width = 2
        self.grid_color = QColor(0, 255, 0, 30)
        self.phase_offset = 0
    
    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        """Render oscilloscope."""
        if self.theme is None or len(waveform) < 2:
            return
        
        # Draw grid (retro CRT style)
        painter.setPen(QPen(self.grid_color, 1))
        
        # Vertical lines
        for x in range(0, self.width, self.width // 10):
            painter.drawLine(x, 0, x, self.height)
        
        # Horizontal lines
        for y in range(0, self.height, self.height // 10):
            painter.drawLine(0, y, self.width, y)
        
        # Draw center crosshair
        center_x = self.width / 2
        center_y = self.height / 2
        
        brighter_grid = QColor(0, 255, 0, 100)
        painter.setPen(QPen(brighter_grid, 2))
        painter.drawLine(0, int(center_y), self.width, int(center_y))
        painter.drawLine(int(center_x), 0, int(center_x), self.height)
        
        # Create Lissajous curve (XY plot)
        # Use waveform for X and phase-shifted waveform for Y
        num_points = min(len(waveform), 1000)
        step = len(waveform) // num_points
        
        path = QPainterPath()
        
        # Scale factor
        scale = min(self.width, self.height) * 0.4
        
        for i in range(num_points):
            idx = i * step
            if idx >= len(waveform):
                break
            
            # X coordinate from waveform
            x_val = waveform[idx]
            
            # Y coordinate from phase-shifted waveform
            y_idx = (idx + len(waveform) // 4) % len(waveform)
            y_val = waveform[y_idx]
            
            # Map to screen coordinates
            x = center_x + x_val * scale
            y = center_y + y_val * scale
            
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        
        # Draw trace with glow
        color = self.theme.get_color(0)
        
        # Glow effect
        glow_color = QColor(color)
        glow_color.setAlpha(30)
        painter.setPen(QPen(glow_color, self.line_width + 6))
        painter.drawPath(path)
        
        # Main trace
        painter.setPen(QPen(color, self.line_width))
        painter.drawPath(path)
        
        # Add scanline effect
        scanline_color = QColor(0, 0, 0, 20)
        painter.setPen(QPen(scanline_color, 1))
        for y in range(0, self.height, 4):
            painter.drawLine(0, y, self.width, y)
