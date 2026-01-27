from __future__ import annotations
"""Audio lines visualization style."""

import numpy as np
import math
from PySide6.QtGui import QPainter, QPen, QPainterPath, QColor
from PySide6.QtCore import Qt, QPointF
from visualizer import BaseVisualizer


class AudioLines(BaseVisualizer):
    """Abstract line art with flowing Bezier curves."""
    
    def __init__(self):
        """Initialize audio lines visualizer."""
        super().__init__("Audio Lines")
        self.num_lines = 5
        self.line_width = 3
        self.time = 0
    
    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        """Render audio lines."""
        if self.theme is None:
            return
        
        # Number of control points
        num_points = 8
        samples_per_point = len(fft_data) // num_points
        
        # Draw multiple layers of lines
        for layer in range(self.num_lines):
            # Create path
            path = QPainterPath()
            
            # Get color for this layer
            color = self.theme.get_gradient_color(layer / self.num_lines)
            
            # Vertical offset for this layer
            base_y = (layer / self.num_lines) * self.height
            
            # Calculate control points based on FFT data
            points = []
            for i in range(num_points):
                start_idx = i * samples_per_point
                end_idx = start_idx + samples_per_point
                magnitude = np.mean(fft_data[start_idx:end_idx]) if end_idx <= len(fft_data) else 0
                
                x = (i / (num_points - 1)) * self.width
                # Added self.time * 0.05 for constant flow, magnitude * 150 for audio reaction
                phase = i * 0.5 + layer + self.time * 0.05
                y = base_y + math.sin(phase) * 50 + magnitude * 150
                
                points.append(QPointF(x, y))
            
            # Create smooth curve through points using Bezier curves
            if len(points) > 0:
                path.moveTo(points[0])
                
                for i in range(1, len(points)):
                    # Calculate control points for smooth curve
                    if i < len(points) - 1:
                        # Quadratic Bezier curve
                        cp_x = (points[i].x() + points[i - 1].x()) / 2
                        cp_y = points[i].y()
                        path.quadTo(QPointF(cp_x, cp_y), points[i])
                    else:
                        path.lineTo(points[i])
            
            # Draw with transparency
            line_color = QColor(color)
            line_color.setAlpha(150)
            
            pen = QPen(line_color)
            pen.setWidth(self.line_width)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)
            
            # Draw glow
            glow_color = QColor(color)
            glow_color.setAlpha(50)
            pen.setColor(glow_color)
            pen.setWidth(self.line_width + 4)
            painter.setPen(pen)
            painter.drawPath(path)
            
        # Increment time for next frame
        self.time += 1
