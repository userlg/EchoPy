from __future__ import annotations
"""Particle system visualization style."""

import numpy as np
import random
import math
from PySide6.QtGui import QPainter, QPen, QBrush, QColor
from PySide6.QtCore import Qt, QPointF
from visualizer import BaseVisualizer


class Particle:
    """Single particle in the system."""
    
    def __init__(self, x, y, vx, vy, size, color):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.color = color
        self.life = 1.0
    
    def update(self, dt=0.016):
        """Update particle position and life."""
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.vy += 200 * dt  # Gravity
        self.life -= dt * 0.5
    
    def is_alive(self):
        """Check if particle is still alive."""
        return self.life > 0


class Particles(BaseVisualizer):
    """Particle system visualization."""
    
    def __init__(self):
        """Initialize particle visualizer."""
        super().__init__("Particles")
        self.particles = []
        self.max_particles = 500
        self.spawn_rate = 5
    
    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        """Render particles."""
        if self.theme is None:
            return
        
        # Update existing particles
        self.particles = [p for p in self.particles if p.is_alive() and 0 <= p.y <= self.height]
        for particle in self.particles:
            particle.update()
        
        # Spawn new particles based on audio
        num_bands = 8
        samples_per_band = len(fft_data) // num_bands
        
        for band in range(num_bands):
            start_idx = band * samples_per_band
            end_idx = start_idx + samples_per_band
            magnitude = np.mean(fft_data[start_idx:end_idx]) if end_idx <= len(fft_data) else 0
            
            # Spawn particles based on magnitude
            num_spawn = int(magnitude * self.spawn_rate * 10)
            
            for _ in range(num_spawn):
                if len(self.particles) >= self.max_particles:
                    break
                
                # Spawn position
                x = (band / num_bands) * self.width + random.uniform(0, self.width / num_bands)
                y = self.height - 10
                
                # Velocity
                vx = random.uniform(-50, 50)
                vy = -magnitude * random.uniform(200, 400)
                
                # Size and color
                size = random.uniform(2, 6) * (1 + magnitude)
                color = self.theme.get_gradient_color(band / num_bands)
                
                self.particles.append(Particle(x, y, vx, vy, size, color))
        
        # Draw particles
        for particle in self.particles:
            color = QColor(particle.color)
            color.setAlpha(int(particle.life * 255))
            
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(particle.x, particle.y), particle.size, particle.size)
