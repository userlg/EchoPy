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
        
        # Sample FFT data to match number of bars
        samples_per_bar = len(fft_data) // self.num_bars
        
        for i in range(self.num_bars):
            # Get average magnitude for this bar
            start_idx = i * samples_per_bar
            end_idx = start_idx + samples_per_bar
            magnitude = np.mean(fft_data[start_idx:end_idx]) if end_idx <= len(fft_data) else 0
            
            # Scale to height with minimum baseline
            bar_height = max(5, magnitude * self.height * 2.5)  # Minimum 5px height
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
