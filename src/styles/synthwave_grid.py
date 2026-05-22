from __future__ import annotations
import numpy as np
import math
import random
from PySide6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QColor,
    QLinearGradient,
    QRadialGradient,
    QPainterPath,
)
from PySide6.QtCore import Qt, QPointF, QRectF
from visualizer import BaseVisualizer


class SynthwaveGrid(BaseVisualizer):
    """
    A 3D Retro Synthwave / Outrun visualizer style.
    Renders a scrolling perspective grid, a pulsing neon sun,
    reactive wireframe mountains, and twinkling drifting stars.
    """

    def __init__(self):
        super().__init__("Synthwave Grid")
        self.grid_time = 0.0
        self.stars = []
        self.num_stars = 80

        # Mountain properties
        self.num_mountain_points = 40
        self.mountain_base = np.zeros(self.num_mountain_points)
        self.smoothed_mountain_heights = np.zeros(self.num_mountain_points)
        self.mountain_smoothing = 0.85

        # Initialize base mountains with multi-octave noise
        center = self.num_mountain_points / 2.0
        for i in range(self.num_mountain_points):
            # Classic synthwave mountain envelope (lower in center, higher on sides)
            envelope = 1.0 - math.exp(-((i - center) ** 2) / (2 * (center * 0.5) ** 2))
            
            # Combine sine waves for fractal-like noise silhouette
            noise = (
                math.sin(i * 0.3) * 0.5 +
                math.sin(i * 0.75) * 0.25 +
                math.sin(i * 1.6) * 0.1
            )
            self.mountain_base[i] = abs(noise) * envelope

    def set_size(self, width: int, height: int):
        super().set_size(width, height)
        # Initialize or adjust starfield size
        self._init_stars()

    def _init_stars(self):
        self.stars = []
        horizon_y = self.height * 0.6
        for _ in range(self.num_stars):
            self.stars.append({
                "x": random.uniform(0, self.width),
                "y": random.uniform(0, horizon_y),
                "speed": random.uniform(0.1, 0.6),
                "size": random.uniform(1.0, 2.5),
                "twinkle_speed": random.uniform(0.02, 0.08),
                "twinkle_phase": random.uniform(0, math.pi * 2)
            })

    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        if self.theme is None:
            return

        painter.setRenderHint(QPainter.Antialiasing, True)

        # 1. Frequency Analysis & Reactivity
        n_fft = len(fft_data)
        if n_fft == 0:
            fft_data = np.zeros(512)
            n_fft = 512

        # Extract energy bands
        bass_band = fft_data[:max(1, int(n_fft * 0.05))]
        mids_band = fft_data[int(n_fft * 0.05):int(n_fft * 0.3)]
        highs_band = fft_data[int(n_fft * 0.3):int(n_fft * 0.8)]

        bass_energy = np.mean(bass_band) if len(bass_band) > 0 else 0.0
        mids_energy = np.mean(mids_band) if len(mids_band) > 0 else 0.0
        highs_energy = np.mean(highs_band) if len(highs_band) > 0 else 0.0

        # Overall volume
        volume = np.mean(fft_data) if len(fft_data) > 0 else 0.0

        # Define Layout Geometry
        horizon_y = self.height * 0.6
        center_x = self.width / 2

        # 2. Draw Sky Background Gradient
        sky_grad = QLinearGradient(0, 0, 0, horizon_y)
        # Deep space purple to magenta near horizon
        space_color = QColor(self.theme.bg_color)
        horizon_color = self.theme.get_color(1) # Accent color 1
        
        sky_grad.setColorAt(0.0, space_color.darker(150))
        sky_grad.setColorAt(0.7, space_color)
        sky_grad.setColorAt(1.0, horizon_color.darker(140))
        
        painter.fillRect(QRectF(0, 0, self.width, horizon_y), QBrush(sky_grad))

        # 3. Draw & Update Starfield
        painter.setPen(Qt.NoPen)
        for star in self.stars:
            # Update twinkle phase and positions
            star["twinkle_phase"] += star["twinkle_speed"]
            # Star speed react to mids/highs energy
            speed_mult = 1.0 + highs_energy * 8.0 + mids_energy * 4.0
            star["y"] += star["speed"] * speed_mult
            
            # Wrap around stars that hit the horizon
            if star["y"] > horizon_y:
                star["y"] = 0
                star["x"] = random.uniform(0, self.width)

            # Twinkle brightness
            alpha = int(120 + 135 * math.sin(star["twinkle_phase"]))
            alpha = max(0, min(255, alpha))
            
            star_color = QColor(255, 255, 255, alpha)
            painter.setBrush(QBrush(star_color))
            painter.drawEllipse(QPointF(star["x"], star["y"]), star["size"], star["size"])

        # 4. Draw Pulsing Neon Outrun Sun
        # Base sun size
        sun_r = min(self.width, self.height) * 0.18
        # Pulsing effect from bass
        pulsing_r = sun_r * (1.0 + bass_energy * 0.5)
        
        sun_x = center_x
        sun_y = horizon_y - pulsing_r * 0.4
        
        # Sun Gradient (Yellow to Hot Pink/Orange)
        sun_grad = QLinearGradient(sun_x, sun_y - pulsing_r, sun_x, sun_y + pulsing_r)
        col_top = self.theme.get_color(2) # Accent 2
        col_bottom = self.theme.get_color(0) # Main brand color
        sun_grad.setColorAt(0.0, col_top.lighter(130))
        sun_grad.setColorAt(0.6, col_bottom)
        sun_grad.setColorAt(1.0, col_bottom.darker(150))

        # Draw sun circle
        painter.save()
        painter.setBrush(QBrush(sun_grad))
        painter.drawEllipse(QPointF(sun_x, sun_y), pulsing_r, pulsing_r)
        
        # Sun Cutouts (Horizontal bands of increasing thickness from top-middle to bottom)
        num_cutouts = 8
        for i in range(num_cutouts):
            # Calculate height and position of cutout line
            ratio = (i + 1) / (num_cutouts + 1)
            # Center cutout to bottom bias
            line_y = sun_y + pulsing_r * (0.1 + ratio * 0.85)
            
            # Line thickness gets thicker near the bottom
            thickness = 1.5 + (ratio * 8.0) * (1.0 + bass_energy * 0.3)
            
            # Draw cutout rectangle spanning the width of the sun
            cutout_rect = QRectF(sun_x - pulsing_r - 10, line_y - thickness/2, pulsing_r * 2 + 20, thickness)
            
            # Fill with background-blend color
            bg_blend = space_color.darker(120)
            bg_blend.setAlpha(240)
            painter.fillRect(cutout_rect, QBrush(bg_blend))
            
        painter.restore()

        # 5. Draw Reactive Wireframe Mountains
        # Generate mountain peaks based on FFT frequencies
        mountain_path = QPainterPath()
        mountain_path.moveTo(0, horizon_y)
        
        half_pts = self.num_mountain_points // 2
        
        # Logarithmic indices for FFT mapping to make peaks reactive to specific frequency segments
        log_indices = np.logspace(0, np.log10(max(2, n_fft - 1)), half_pts).astype(int)

        # Populate target heights
        for i in range(self.num_mountain_points):
            # Distance from center
            dist_from_center = abs(i - half_pts)
            # Find the frequency bin index
            bin_idx = log_indices[min(dist_from_center, half_pts - 1)]
            freq_val = fft_data[min(bin_idx, n_fft - 1)]
            
            # Reactive height component (Bass for outer/mids, mids for inner)
            reactivity = freq_val * self.height * 0.45
            
            # Combine base mountain height with audio reaction
            target_h = (self.mountain_base[i] * self.height * 0.22) + reactivity
            
            # Smooth interpolation
            self.smoothed_mountain_heights[i] = (
                self.smoothed_mountain_heights[i] * self.mountain_smoothing
                + target_h * (1.0 - self.mountain_smoothing)
            )

        # Construct path points
        x_step = self.width / (self.num_mountain_points - 1)
        points = []
        for i in range(self.num_mountain_points):
            x = i * x_step
            y = horizon_y - self.smoothed_mountain_heights[i]
            # Ensure mountains don't go below the horizon line
            y = min(y, horizon_y)
            points.append(QPointF(x, y))
            mountain_path.lineTo(x, y)
            
        mountain_path.lineTo(self.width, horizon_y)
        mountain_path.closeSubpath()

        # Fill mountains with dark translucent glow
        mtn_fill = QColor(space_color)
        mtn_fill.setAlpha(210)
        painter.fillPath(mountain_path, QBrush(mtn_fill))

        # Draw Mountain Neon Outline
        mtn_stroke = self.theme.get_color(1)
        pen_mtn = QPen(mtn_stroke)
        pen_mtn.setWidthF(1.8 + bass_energy * 0.6)
        painter.setPen(pen_mtn)
        for i in range(self.num_mountain_points - 1):
            painter.drawLine(points[i], points[i+1])

        # 6. Draw 3D Perspective Grid
        grid_height = self.height - horizon_y
        
        # Render horizontal lines scrolling forward
        # grid_time increments in each frame, scaled by audio volume
        self.grid_time += 0.006 * (1.0 + volume * 4.5)
        phase = self.grid_time % 1.0

        accent_color = self.theme.get_color(0)
        
        # Grid line linear gradient for vanishing fade-out effect near horizon
        grid_pen_grad = QLinearGradient(0, horizon_y, 0, self.height)
        fade_color = QColor(accent_color)
        fade_color.setAlpha(30)
        
        grid_pen_grad.setColorAt(0.0, Qt.transparent)
        grid_pen_grad.setColorAt(0.15, fade_color)
        grid_pen_grad.setColorAt(0.6, accent_color)
        grid_pen_grad.setColorAt(1.0, accent_color.lighter(130))

        # Horizontal Lines
        num_h_lines = 14
        for i in range(num_h_lines):
            # Compute line phase
            line_phase = (phase + i / num_h_lines) % 1.0
            
            # Perspective mapping (exponential spacing)
            y = horizon_y + grid_height * (line_phase ** 2.3)
            
            # Draw line with thickness relative to perspective depth
            line_pen = QPen(QBrush(grid_pen_grad), 1.0)
            line_pen.setWidthF(0.8 + 2.2 * (line_phase ** 2.0))
            painter.setPen(line_pen)
            painter.drawLine(0, int(y), self.width, int(y))

        # Vertical Lines (converge at vanishing point at center of the horizon)
        num_v_lines = 24
        # Calculate horizontal step at the bottom
        x_bottom_step = (self.width * 1.8) / num_v_lines
        start_x_bottom = center_x - (self.width * 0.9)
        
        for i in range(num_v_lines + 1):
            x_bottom = start_x_bottom + i * x_bottom_step
            
            # Pen width fades slightly near vanishing point
            v_pen = QPen(QBrush(grid_pen_grad), 1.2)
            painter.setPen(v_pen)
            painter.drawLine(QPointF(x_bottom, self.height), QPointF(center_x, horizon_y))

        # 7. Draw Neon Horizon Bar & Glow
        horizon_pen = QPen(self.theme.get_color(1))
        horizon_pen.setWidthF(2.0 + volume * 1.5)
        painter.setPen(horizon_pen)
        painter.drawLine(0, int(horizon_y), self.width, int(horizon_y))

        # Sutil Glow on Horizon
        horizon_glow = QLinearGradient(0, horizon_y - 12, 0, horizon_y + 12)
        glow_color = self.theme.get_color(1)
        glow_color.setAlpha(int(60 + volume * 100))
        horizon_glow.setColorAt(0.5, glow_color)
        horizon_glow.setColorAt(0.0, Qt.transparent)
        horizon_glow.setColorAt(1.0, Qt.transparent)
        
        painter.fillRect(QRectF(0, horizon_y - 12, self.width, 24), QBrush(horizon_glow))
