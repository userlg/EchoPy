from __future__ import annotations
"""Waveform visualization style."""

import numpy as np
from PySide6.QtGui import QPainter, QPen, QPainterPath, QColor
from PySide6.QtCore import Qt, QPointF
from visualizer import BaseVisualizer


class Waveform(BaseVisualizer):
    """Time-domain waveform display."""
    
    def __init__(self):
        """Initialize waveform visualizer."""
        super().__init__("Waveform")
        self.line_width = 3
        self.glow_passes = 3
    
    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        """Render waveform."""
        if self.theme is None or len(waveform) == 0:
            return
        
        # Sample waveform to fit width
        num_points = min(len(waveform), self.width)
        step = len(waveform) // num_points
        
        center_y = self.height / 2
        
        # Create path for waveform
        path = QPainterPath()
        
        # Calculate first point
        first_sample = waveform[0]
        first_y = center_y - (first_sample * self.height * 0.4)
        path.moveTo(0, first_y)
        
        # Add points
        for i in range(1, num_points):
            idx = i * step
            if idx >= len(waveform):
                break
            
            sample = waveform[idx]
            x = (i / num_points) * self.width
            y = center_y - (sample * self.height * 0.4)
            
            path.lineTo(x, y)
        
        # Draw glow effect (multiple passes with increasing thickness and transparency)
        for pass_num in range(self.glow_passes, 0, -1):
            color = self.theme.get_color(0)
            glow_color = QColor(color)
            glow_color.setAlpha(40 * pass_num)
            
            pen = QPen(glow_color)
            pen.setWidth(self.line_width + pass_num * 4)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            
            painter.setPen(pen)
            painter.drawPath(path)
        
        # Draw main waveform
        color = self.theme.get_color(0)
        pen = QPen(color)
        pen.setWidth(self.line_width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        
        painter.setPen(pen)
        painter.drawPath(path)
        
        # Draw center line
        center_color = QColor(color)
        center_color.setAlpha(50)
        painter.setPen(QPen(center_color, 1, Qt.DashLine))
        painter.drawLine(0, int(center_y), self.width, int(center_y))
