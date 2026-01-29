from __future__ import annotations
"""Spectrum bars visualization style."""

import numpy as np
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QLinearGradient
from PySide6.QtCore import Qt, QPointF, QRectF
from visualizer import BaseVisualizer


class SpectrumBars(BaseVisualizer):
    """Classic spectrum analyzer with vertical bars."""
    
    def __init__(self):
        """Initialize spectrum bars visualizer."""
        super().__init__("Spectrum Bars")
        self.num_bars = 64
        self.bar_spacing = 2
    
    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        """Render spectrum bars."""
        if self.theme is None:
            return
        
        # Calculate bar width
        total_width = self.width - (self.num_bars - 1) * self.bar_spacing
        bar_width = total_width / self.num_bars
        
        # Logarithmic sampling for better harmonic distribution
        # Frequencies are distributed logarithmically (like human hearing)
        # We start from log10(2) to skip only DC and sub-hum (0-40Hz), preserving bass
        log_indices = np.logspace(np.log10(2), np.log10(len(fft_data)), self.num_bars + 1)
        indices = log_indices.astype(int)
        
        for i in range(self.num_bars):
            # Get indices for this bar's frequency range
            start_idx = indices[i]
            end_idx = indices[i+1]
            
            # Ensure at least one bin is sampled
            if end_idx <= start_idx:
                end_idx = start_idx + 1
            
            # Average magnitude in this range
            if start_idx < len(fft_data):
                magnitude = np.mean(fft_data[start_idx:end_idx])
            else:
                magnitude = 0
            
            # Scale to height with minimum baseline
            bar_height = max(5, magnitude * self.height * 60.0)  # Aggressive scaling for visual impact
            bar_height = min(bar_height, self.height - 10)
            
            # Calculate position
            x = i * (bar_width + self.bar_spacing)
            y = self.height - bar_height
            
            # Create gradient for bar
            gradient = QLinearGradient(QPointF(x, self.height), QPointF(x, y))
            
            # Get color based on frequency (lower = bass, higher = treble)
            color_pos = i / self.num_bars
            color = self.theme.get_gradient_color(color_pos)
            
            # Gradient from darker to brighter
            dark_color = QColor(color.red() // 3, color.green() // 3, color.blue() // 3)
            gradient.setColorAt(0, dark_color)
            gradient.setColorAt(0.5, color)
            gradient.setColorAt(1, color.lighter(120))
            
            # Draw bar
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawRect(QRectF(x, y, bar_width, bar_height))
