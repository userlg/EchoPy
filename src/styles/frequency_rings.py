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
        self.num_rings = 6 # Reduced to 6 for minimalism and performance
        self.ring_history = []
        self.max_history = 12 # Reduced to 12 for smoother FPS
    
    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        """Render frequency rings."""
        if self.theme is None:
            return
        
        center_x = self.width / 2
        center_y = self.height / 2
        
        # Logarithmic sampling
        log_indices = np.logspace(np.log10(2), np.log10(len(fft_data)), self.num_rings + 1)
        indices = log_indices.astype(int)
        
        current_magnitudes = []
        for i in range(self.num_rings):
            start_idx = indices[i]
            end_idx = indices[i+1]
            if end_idx <= start_idx: end_idx = start_idx + 1
            magnitude = np.mean(fft_data[start_idx:end_idx]) if start_idx < len(fft_data) else 0
            current_magnitudes.append(magnitude)
        
        # Add to history
        self.ring_history.append(current_magnitudes)
        if len(self.ring_history) > self.max_history:
            self.ring_history.pop(0)
        
        # Draw rings
        max_radius = min(self.width, self.height) / 2 - 20
        
        # Enable high quality antialiasing for modern look
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        for history_idx, magnitudes in enumerate(self.ring_history):
            age = len(self.ring_history) - history_idx - 1
            expansion = (age / self.max_history) * max_radius * 1.2 # Slightly slower expansion
            alpha_factor = 1.0 - (age / self.max_history)
            
            for ring_idx, magnitude in enumerate(magnitudes):
                # Reduced base size (0.6 instead of 0.9)
                base_radius = (ring_idx / self.num_rings) * max_radius * 0.6
                
                # Dynamic scaling
                radius = base_radius + magnitude * 400 + expansion
                
                if radius > 0 and radius < max_radius * 1.5:
                    color_pos = ring_idx / self.num_rings
                    base_color = self.theme.get_gradient_color(color_pos)
                    
                    # MODERN NEON EFFECT
                    # 1. Draw Glow (Thick, transparent)
                    glow_color = QColor(base_color)
                    glow_color.setAlpha(int(alpha_factor * 60)) # Low opacity
                    glow_pen = QPen(glow_color)
                    glow_pen.setWidth(10 + int(magnitude * 20)) # Dynamic glow width
                    painter.setPen(glow_pen)
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(QPointF(center_x, center_y), radius, radius)
                    
                    # 2. Draw Core (Thin, bright)
                    core_color = QColor(base_color)
                    core_color.setAlpha(int(alpha_factor * 255))
                    core_pen = QPen(core_color)
                    core_pen.setWidth(2) # Crisp thin line
                    painter.setPen(core_pen)
                    painter.drawEllipse(QPointF(center_x, center_y), radius, radius)
