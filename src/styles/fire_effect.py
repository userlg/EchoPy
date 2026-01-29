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
        # Use much lower resolution for performance (Python loops are slow)
        # This gives a nice retro "pixel fire" look too.
        self.map_width = width // 10
        self.map_height = height // 10
        self.heat_map = np.zeros((self.map_height, self.map_width), dtype=np.float32)
    
    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        """Render fire effect."""
        if self.theme is None or self.heat_map is None:
            return
            
        # 1. VECTORIZED PROPAGATION (Fixes FPS)
        # Shift everything up
        # We want heat[y, x] to be average of below pixels
        # Create views for vectorized operations
        src = self.heat_map
        
        # Calculate horizontal spread (blur)
        # roll(-1) shifts left (so pixel gets value from right), roll(1) shifts right
        # We average center, left, and right from the row BELOW
        # Actually, standard fire algo: new[y, x] = (old[y+1, x-1] + old[y+1, x] + old[y+1, x+1]) / 3
        
        # Prepare the source source (rows 1 to end)
        src_below = src[1:, :]
        
        # Horizontal neighbors in the row below
        left = np.roll(src_below, -1, axis=1) # Value from right neighbor? No, roll(-1) moves [0, 1, 2] to [1, 2, 0]. Index 0 gets Index 1. 
        # So at x, we want x-1. roll(1) moves [0, 1, 2] to [2, 0, 1]. Index 1 gets Index 0.
        
        r_right = np.roll(src_below, -1, axis=1) # Pixels shift left, so at [x] we get [x+1]
        r_left = np.roll(src_below, 1, axis=1)   # Pixels shift right, so at [x] we get [x-1]
        
        # Average and decay
        decay = 0.985
        avg_heat = (src_below + r_left + r_right) / 3.0 * decay
        
        # Apply to current rows (0 to end-1)
        self.heat_map[:-1, :] = avg_heat

        # 2. LOGARITHMIC FREQUENCY MAPPING (Fixes Left-Side Only)
        # Map frequencies logarithmically to screen width
        log_indices = np.logspace(np.log10(2), np.log10(len(fft_data)), self.map_width + 1).astype(int)
        
        # Inject heat at bottom row
        for i in range(self.map_width):
            start = log_indices[i]
            end = log_indices[i+1]
            if end <= start: end = start + 1
            
            if start < len(fft_data):
                mag = np.mean(fft_data[start:end])
            else:
                mag = 0
                
            # Boost heat
            heat = mag * 30.0 
            self.heat_map[-1, i] = min(1.0, self.heat_map[-1, i] + heat) # Additive mixing
            
            # Spark logic (random flare-ups)
            if heat > 0.5 and np.random.random() < 0.1:
                 self.heat_map[-2:-1, i] = 1.0
        
        # Create image from heat map
        image = QImage(self.map_width, self.map_height, QImage.Format_RGB32)
        
        for y in range(self.map_height):
            for x in range(self.map_width):
                heat = self.heat_map[y, x]
                
                # Dynamic Theme Coloring
                # 1. Get base color from theme gradient
                # We map heat (0.0-1.0) directly to the gradient position
                base_color = self.theme.get_gradient_color(heat)
                
                # 2. Apply intensity scaling (black out low heat)
                # If heat is very low, we want it to fade to black/transparent
                if heat < 0.1:
                    # Fade to black rapidly
                    alpha = int(heat * 10 * 255)
                    r = base_color.red() * heat * 10
                    g = base_color.green() * heat * 10
                    b = base_color.blue() * heat * 10
                    color = QColor(int(r), int(g), int(b), 255) # Keep alpha 255 but darken RGB
                else:
                    color = base_color
                
                image.setPixelColor(x, y, color)
        
        # Draw scaled image
        
        # Scale and draw
        from PySide6.QtGui import QPixmap
        pixmap = QPixmap.fromImage(image)
        scaled = pixmap.scaled(self.width, self.height, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        painter.drawPixmap(0, 0, scaled)
