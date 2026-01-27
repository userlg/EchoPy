from __future__ import annotations
"""Fire effect visualization style."""

import numpy as np
from PySide6.QtGui import QPainter, QBrush, QColor, QImage
from PySide6.QtCore import Qt
from visualizer import BaseVisualizer


class FireEffect(BaseVisualizer):
    """Fire simulation driven by audio."""
    
    def __init__(self):
        """Initialize fire effect visualizer."""
        super().__init__("Fire Effect")
        self.heat_map = None
        self.cooling = 0.02
    
    def set_size(self, width: int, height: int):
        """Set canvas size and initialize heat map."""
        super().set_size(width, height)
        # Use lower resolution for performance
        self.map_width = width // 4
        self.map_height = height // 4
        self.heat_map = np.zeros((self.map_height, self.map_width), dtype=np.float32)
    
    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        """Render fire effect."""
        if self.theme is None or self.heat_map is None:
            return
        
        # Cool down heat map
        self.heat_map *= (1 - self.cooling)
        
        # Add heat from audio at bottom
        num_segments = self.map_width
        samples_per_segment = len(fft_data) // num_segments
        
        for i in range(num_segments):
            start_idx = i * samples_per_segment
            end_idx = start_idx + samples_per_segment
            magnitude = np.mean(fft_data[start_idx:end_idx]) if end_idx <= len(fft_data) else 0
            
            # Add heat to bottom rows
            heat = magnitude * 2.0
            if i < self.map_width:
                self.heat_map[-1, i] = min(1.0, heat)
                if self.map_height > 1:
                    self.heat_map[-2, i] = min(1.0, heat * 0.8)
        
        # Propagate heat upward with blur
        for y in range(self.map_height - 2, 0, -1):
            for x in range(self.map_width):
                # Average with neighbors
                total = self.heat_map[y + 1, x]
                count = 1
                
                if x > 0:
                    total += self.heat_map[y + 1, x - 1]
                    count += 1
                if x < self.map_width - 1:
                    total += self.heat_map[y + 1, x + 1]
                    count += 1
                
                self.heat_map[y, x] = (total / count) * 0.97
        
        # Create image from heat map
        image = QImage(self.map_width, self.map_height, QImage.Format_RGB32)
        
        for y in range(self.map_height):
            for x in range(self.map_width):
                heat = self.heat_map[y, x]
                
                # Map heat to color (black -> red -> orange -> yellow -> white)
                if heat < 0.33:
                    # Black to red
                    t = heat / 0.33
                    color = QColor(int(255 * t), 0, 0)
                elif heat < 0.66:
                    # Red to orange/yellow
                    t = (heat - 0.33) / 0.33
                    color = QColor(255, int(255 * t), 0)
                else:
                    # Orange to yellow/white
                    t = (heat - 0.66) / 0.34
                    color = QColor(255, 255, int(255 * t))
                
                image.setPixelColor(x, y, color)
        
        # Draw scaled image
        painter.drawImage(self.width, self.height, image)
        
        # Scale and draw
        from PySide6.QtGui import QPixmap
        pixmap = QPixmap.fromImage(image)
        scaled = pixmap.scaled(self.width, self.height, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        painter.drawPixmap(0, 0, scaled)
