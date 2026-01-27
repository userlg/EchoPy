from __future__ import annotations
"""Radial bars visualization style."""

import numpy as np
import math
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QRadialGradient
from PySide6.QtCore import Qt, QPointF, QRectF
from visualizer import BaseVisualizer


class RadialBars(BaseVisualizer):
    """Radial bars emanating from center like sunrays."""
    
    def __init__(self):
        """Initialize radial bars visualizer."""
        super().__init__("Radial Bars")
        self.num_rays = 36
        self.rotation = 0
    
    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        """Render radial bars."""
        if self.theme is None:
            return
        
        # Center point
        center_x = self.width / 2
        center_y = self.height / 2
        
        # Maximum radius
        max_radius = min(self.width, self.height) / 2 - 10
        
        # Sample FFT data
        samples_per_ray = len(fft_data) // self.num_rays
        
        # Angle step
        angle_step = 360 / self.num_rays
        
        # Update rotation based on beat (average of low frequencies)
        beat_magnitude = np.mean(fft_data[:len(fft_data) // 8])
        self.rotation += beat_magnitude * 2
        
        for i in range(self.num_rays):
            # Get magnitude
            start_idx = i * samples_per_ray
            end_idx = start_idx + samples_per_ray
            magnitude = np.mean(fft_data[start_idx:end_idx]) if end_idx <= len(fft_data) else 0
            
            # Calculate bar dimensions
            bar_length = magnitude * max_radius * 2.0
            bar_length = min(bar_length, max_radius)
            bar_width = 15
            
            # Calculate angle with rotation
            angle = i * angle_step + self.rotation
            angle_rad = math.radians(angle - 90)
            
            # Save painter state
            painter.save()
            
            # Translate to center and rotate
            painter.translate(center_x, center_y)
            painter.rotate(angle)
            
            # Get color
            color_pos = i / self.num_rays
            color = self.theme.get_gradient_color(color_pos)
            
            # Create radial gradient for glow effect
            gradient = QRadialGradient(QPointF(0, -bar_length / 2), bar_length / 2)
            gradient.setColorAt(0, color)
            
            glow_color = QColor(color)
            glow_color.setAlpha(0)
            gradient.setColorAt(1, glow_color)
            
            # Draw bar
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawRect(QRectF(-bar_width / 2, -bar_length, bar_width, bar_length))
            
            # Restore painter state
            painter.restore()
        
        # Draw center glow
        gradient = QRadialGradient(QPointF(center_x, center_y), 50)
        color = self.theme.get_color(0)
        gradient.setColorAt(0, color)
        glow = QColor(color)
        glow.setAlpha(0)
        gradient.setColorAt(1, glow)
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(center_x, center_y), 50, 50)
