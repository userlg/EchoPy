from __future__ import annotations
"""Matrix rain visualization style."""

import numpy as np
import random
import string
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtCore import Qt
from visualizer import BaseVisualizer


class MatrixColumn:
    """Single column of falling characters."""
    
    def __init__(self, x, height, speed):
        self.x = x
        self.y = random.randint(-height, 0)
        self.height = height
        self.speed = speed
        self.chars = []
        self. length = random.randint(10, 30)
        self._generate_chars()
    
    def _generate_chars(self):
        """Generate random characters."""
        chars = string.ascii_letters + string.digits + "!@#$%^&*()"
        self.chars = [random.choice(chars) for _ in range(self.length)]
    
    def update(self, speed_multiplier=1.0):
        """Update column position."""
        self.y += self.speed * speed_multiplier
        
        if self.y > self.height:
            self.y = random.randint(-self.height // 2, -10)
            self._generate_chars()


class MatrixRain(BaseVisualizer):
    """Matrix-style falling characters."""
    
    def __init__(self):
        """Initialize matrix rain visualizer."""
        super().__init__("Matrix Rain")
        self.columns = []
        self.char_size = 16
        self.font = QFont("Courier New", self.char_size)
    
    def set_size(self, width: int, height: int):
        """Set canvas size and initialize columns."""
        super().set_size(width, height)
        
        # Create columns
        num_columns = width // self.char_size
        self.columns = []
        
        for i in range(num_columns):
            x = i * self.char_size
            speed = random.uniform(2, 10)
            self.columns.append(MatrixColumn(x, height, speed))
    
    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        """Render matrix rain."""
        if self.theme is None or not self.columns:
            return
        
        # Calculate speed multiplier from audio
        avg_magnitude = np.mean(fft_data) if len(fft_data) > 0 else 0
        speed_multiplier = 1.0 + avg_magnitude * 5.0
        
        # Update and draw columns
        painter.setFont(self.font)
        
        for column in self.columns:
            column.update(speed_multiplier)
            
            # Draw characters in column
            for i, char in enumerate(column.chars):
                y = int(column.y + i * self.char_size)
                
                if 0 <= y <= self.height:
                    # Fade from bright to dark
                    fade = 1.0 - (i / len(column.chars))
                    
                    color = self.theme.get_color(0)
                    char_color = QColor(color)
                    char_color.setAlpha(int(255 * fade))
                    
                    # First character is brightest (white)
                    if i == 0:
                        char_color = QColor(255, 255, 255)
                    
                    painter.setPen(QPen(char_color))
                    painter.drawText(int(column.x), y, char)
