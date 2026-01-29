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
            
        # Optimization: Downsample aggressively. 
        # Drawing 2000 points is slow. Drawing 200 is fast.
        # We take 1 point every 4 samples or based on width.
        step = max(1, len(waveform) // 300) 
        
        points = []
        center_y = self.height / 2
        amplitude = self.height / 2
        
        # Build Point List
        for i in range(0, len(waveform), step):
            sample = waveform[i]
            # Reduce gain massively. Peak is ~5.0. 
            # We want that to be nearly full screen, so 5.0 * 0.2 = 1.0
            val = max(-1.0, min(1.0, sample * 0.2))
            
            x = (i / len(waveform)) * self.width
            y = center_y - (val * amplitude)
            points.append(QPointF(x, y))
            
        if not points:
            return

        # Create Polygon
        from PySide6.QtGui import QPolygonF
        polygon = QPolygonF(points)
        

        
        # 1. Optimized Glow (Single fast pass)
        color = self.theme.get_color(0)
        glow_color = QColor(color)
        glow_color.setAlpha(50) # Transparent
        
        glow_pen = QPen(glow_color)
        glow_pen.setWidth(8) # Thicker for glow
        glow_pen.setCosmetic(True) # Hardware accelerated
        
        painter.setPen(glow_pen)
        painter.drawPolyline(polygon)
        
        # 2. Main Line (Sharp center)
        pen = QPen(color)
        pen.setWidth(2)
        pen.setCosmetic(True)
        
        painter.setPen(pen)
        painter.drawPolyline(polygon)
        
        # Draw center line
        center_color = QColor(color)
        center_color.setAlpha(50)
        painter.setPen(QPen(center_color, 1, Qt.DashLine))
        painter.drawLine(0, int(center_y), self.width, int(center_y))
