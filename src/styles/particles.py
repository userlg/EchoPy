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
        self.vy += 30 * dt  # Reduced Gravity (was 200) - floatier
        self.life -= dt * 0.3 # Extended life (was 0.5)
    
    def is_alive(self):
        """Check if particle is still alive."""
        return self.life > 0


class Particles(BaseVisualizer):
    """Particle system visualization."""
    
    def __init__(self):
        """Initialize particle visualizer."""
        super().__init__("Particles")
        self.particles = []
        self.max_particles = 3000 # Increased from 500
        self.spawn_rate = 100      # Increased from 5
    
    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        """Render particles."""
        if self.theme is None:
            return
        
        # Update existing particles
        # Fix: Allow particles reasonably below screen (processing entry) and above (processing exit)
        self.particles = [p for p in self.particles if p.is_alive() and -500 <= p.y <= self.height + 200]
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
            # Use probabilistic spawning for low magnitudes
            spawn_amount = magnitude * self.spawn_rate * 50
            num_spawn = int(spawn_amount)
            if random.random() < (spawn_amount - num_spawn):
                num_spawn += 1
            
            for _ in range(num_spawn):
                if len(self.particles) >= self.max_particles:
                    break
                
                # Spawn position
                # Modernization: Spawn randomly across screen instead of tied to band index
                x = random.uniform(0, self.width)
                y = self.height + random.uniform(0, 50) # Start slightly below screen for smoother entry
                
                # Velocity (Add base minimal velocity so they always show up)
                vx = random.uniform(-50, 50)
                base_upwards = random.uniform(600, 900) # Increased Base Jump (was 300-500)
                mag_upwards = magnitude * random.uniform(2000, 4000) # Increased Mag Jump
                vy = -(base_upwards + mag_upwards)
                
                # Size and color
                size = random.uniform(4, 12) * (1 + magnitude)
                color = self.theme.get_gradient_color(band / num_bands)
                
                self.particles.append(Particle(x, y, vx, vy, size, color))
        
        # Draw particles
        for particle in self.particles:
            color = QColor(particle.color)
            color.setAlpha(int(particle.life * 255))
            
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(particle.x, particle.y), particle.size, particle.size)
