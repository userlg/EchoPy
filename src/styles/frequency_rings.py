from __future__ import annotations
"""Frequency rings visualization style."""

import numpy as np
import math
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtCore import Qt, QPointF
from visualizer import BaseVisualizer


class FrequencyRings(BaseVisualizer):
    """Concentric frequency rings with ripple effect."""
    
    def __init__(self):
        """Initialize frequency rings visualizer."""
        super().__init__("Frequency Rings")
        self.num_rings = 12
        self.ring_history = []
        self.max_history = 30
    
    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        """Render frequency rings."""
        if self.theme is None:
            return
        
        center_x = self.width / 2
        center_y = self.height / 2
        
        # Sample FFT into frequency bands
        samples_per_ring = len(fft_data) // self.num_rings
        
        current_magnitudes = []
        for i in range(self.num_rings):
            start_idx = i * samples_per_ring
            end_idx = start_idx + samples_per_ring
            magnitude = np.mean(fft_data[start_idx:end_idx]) if end_idx <= len(fft_data) else 0
            current_magnitudes.append(magnitude)
        
        # Add to history
        self.ring_history.append(current_magnitudes)
        if len(self.ring_history) > self.max_history:
            self.ring_history.pop(0)
        
        # Draw rings from history (ripple effect)
        max_radius = min(self.width, self.height) / 2 - 20
        
        for history_idx, magnitudes in enumerate(self.ring_history):
            # Calculate expansion factor
            age = len(self.ring_history) - history_idx - 1
            expansion = (age / self.max_history) * max_radius
            
            # Fade based on age
            alpha = 1.0 - (age / self.max_history)
            
            for ring_idx, magnitude in enumerate(magnitudes):
                # Base radius for this ring
                base_radius = (ring_idx / self.num_rings) * max_radius * 0.3
                
                # Radius based on magnitude and expansion
                radius = base_radius + magnitude * 50 + expansion
                
                if radius > 0 and radius < max_radius * 1.5:
                    # Get color
                    color_pos = ring_idx / self.num_rings
                    color = self.theme.get_gradient_color(color_pos)
                    
                    ring_color = QColor(color)
                    ring_color.setAlpha(int(alpha * 200 * magnitude))
                    
                    # Draw ring
                    pen = QPen(ring_color)
                    pen.setWidth(2)
                    painter.setPen(pen)
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(QPointF(center_x, center_y), radius, radius)
