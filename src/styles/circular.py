from __future__ import annotations
"""Circular spectrum visualization style."""

import numpy as np
import math
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QLinearGradient
from PySide6.QtCore import Qt, QPointF, QLineF
from visualizer import BaseVisualizer


class CircularSpectrum(BaseVisualizer):
    """Circular spectrum with bars radiating from center."""
    
    def __init__(self):
        """Initialize circular spectrum visualizer."""
        super().__init__("Circular Spectrum")
        self.num_bars = 120
        self.min_radius = 80
        self.bar_width = 3
    
    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        """Render circular spectrum."""
        if self.theme is None:
            return
        
        # Center of the circle
        center_x = self.width / 2
        center_y = self.height / 2
        
        # Maximum radius
        max_radius = min(self.width, self.height) / 2 - 20
        
        # Logarithmic sampling for better harmonic distribution
        # Frequencies are distributed logarithmically (like human hearing)
        log_indices = np.logspace(np.log10(2), np.log10(len(fft_data)), self.num_bars + 1)
        indices = log_indices.astype(int)
        
        # Angle step for circular layout
        angle_step = 360 / self.num_bars
        
        for i in range(self.num_bars):
            # Get indices for this bar
            start_idx = indices[i]
            end_idx = indices[i+1]
            
            # Ensure at least one bin is sampled
            if end_idx <= start_idx:
                end_idx = start_idx + 1
            
            # Average magnitude
            if start_idx < len(fft_data):
                magnitude = np.mean(fft_data[start_idx:end_idx])
            else:
                magnitude = 0
            
            # Calculate bar length
            bar_length = magnitude * (max_radius - self.min_radius) * 80.0
            bar_length = min(bar_length, max_radius - self.min_radius)
            
            # Calculate angle
            angle = i * angle_step
            angle_rad = math.radians(angle - 90)  # -90 to start at top
            
            # Calculate start and end points
            start_x = center_x + math.cos(angle_rad) * self.min_radius
            start_y = center_y + math.sin(angle_rad) * self.min_radius
            
            end_x = center_x + math.cos(angle_rad) * (self.min_radius + bar_length)
            end_y = center_y + math.sin(angle_rad) * (self.min_radius + bar_length)
            
            # Get color
            color_pos = i / self.num_bars
            color = self.theme.get_gradient_color(color_pos)
            
            # Draw bar
            pen = QPen(color)
            pen.setWidth(self.bar_width)
            pen.setCapStyle(Qt.RoundCap)
            
            painter.setPen(pen)
            painter.drawLine(QPointF(start_x, start_y), QPointF(end_x, end_y))
        
        # Draw center circle
        center_color = self.theme.get_color(0)
        center_color.setAlpha(100)
        painter.setBrush(QBrush(center_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(center_x, center_y), self.min_radius - 10, self.min_radius - 10)
