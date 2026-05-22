from __future__ import annotations
import numpy as np
import math
import random
from PySide6.QtGui import (
    QPainter,
    QBrush,
    QColor,
    QRadialGradient,
    QLinearGradient,
    QPen,
)
from PySide6.QtCore import Qt, QPointF, QRectF
from visualizer import BaseVisualizer


class RadialBars(BaseVisualizer):
    """Radial bars with outrun central core, concentric dashed rings, and radial sparks."""

    def __init__(self):
        super().__init__("Radial Bars")
        self.num_rays = 120
        self.smoothed_bass = 0.0
        self.particles = []
        self.max_particles = 120

    def set_size(self, width: int, height: int):
        super().set_size(width, height)
        self.particles = []

    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        if self.theme is None or fft_data is None:
            return

        painter.setRenderHint(QPainter.Antialiasing, True)

        center_x = self.width / 2
        center_y = self.height / 2

        min_radius = min(self.width, self.height) * 0.18
        max_radius = min(self.width, self.height) / 2 - 20
        bar_len_max = max_radius - min_radius

        # 1. Frequency Binning (Vocal Focus)
        n_fft = len(fft_data)
        effective_n = int(n_fft * 0.25)

        log_indices = np.logspace(
            np.log10(2), np.log10(max(effective_n, 10)), self.num_rays + 1
        ).astype(int)

        magnitudes = np.empty(self.num_rays, dtype=np.float64)
        for i in range(self.num_rays):
            lo = log_indices[i]
            hi = max(lo + 1, log_indices[i + 1])
            magnitudes[i] = (
                np.mean(fft_data[lo : min(hi, n_fft)]) if lo < n_fft else 0.0
            )

        # Sensitivity Boost
        bass_end = self.num_rays // 4
        mids_end = int(self.num_rays * 0.6)

        boost = np.ones(self.num_rays, dtype=np.float64)
        boost[:bass_end] = 1.8
        boost[bass_end:mids_end] = 3.5
        boost[mids_end:] = 5.0

        magnitudes = magnitudes * boost
        magnitudes = np.power(np.clip(magnitudes, 0.0, None), 0.5)

        # Pulse calculations
        bass_energy = float(np.mean(magnitudes[: max(1, bass_end)]))
        self.smoothed_bass += (bass_energy - self.smoothed_bass) * 0.2
        pulse_r = min_radius + (self.smoothed_bass * 70.0)

        # 2. Draw Concentric Dashed Neon Rings (Background layer)
        ring_color = self.theme.get_color(1)
        ring_color.setAlpha(65)
        # Dash pattern on QPen: Custom or Qt.DashLine
        ring_pen = QPen(QBrush(ring_color), 1.4, Qt.DashLine)
        painter.setPen(ring_pen)
        painter.setBrush(Qt.NoBrush)

        for offset in [45, 90, 135]:
            r_ring = pulse_r + offset
            if r_ring < max_radius:
                painter.drawEllipse(QPointF(center_x, center_y), r_ring, r_ring)

        # 3. Particle Spark Spawn (Spawn on bass transients)
        if bass_energy > 0.28 and len(self.particles) < self.max_particles:
            num_spawn = int(3 * bass_energy)
            for _ in range(num_spawn):
                angle_deg = random.uniform(0, 360)
                angle_rad = math.radians(angle_deg)
                start_r = pulse_r + random.uniform(10, 40)
                speed = random.uniform(2.0, 4.8) * (1.0 + bass_energy)
                self.particles.append({
                    "angle": angle_rad,
                    "r": start_r,
                    "speed": speed,
                    "alpha": 1.0,
                    "size": random.uniform(1.2, 3.2),
                    "color_pos": angle_deg / 360.0
                })

        # Update and Render Particles
        active_particles = []
        for p in self.particles:
            p["r"] += p["speed"]
            p["alpha"] -= 0.019
            if p["alpha"] > 0 and p["r"] < max_radius:
                x = center_x + math.cos(p["angle"]) * p["r"]
                y = center_y + math.sin(p["angle"]) * p["r"]
                col = self.theme.get_gradient_color(p["color_pos"])
                p_col = QColor(col)
                p_col.setAlphaF(p["alpha"] * 0.8)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(p_col))
                painter.drawEllipse(QPointF(x, y), p["size"], p["size"])
                active_particles.append(p)
        self.particles = active_particles

        # 4. Render Radial Bars (Fixed Orientation)
        painter.save()
        painter.translate(center_x, center_y)

        angle_step = 360.0 / self.num_rays

        for i in range(self.num_rays):
            mag = magnitudes[i]
            bar_len = mag * bar_len_max * 2.5
            bar_len = np.clip(bar_len, 6.0, bar_len_max)

            color_pos = i / self.num_rays
            color = self.theme.get_gradient_color(color_pos)

            painter.save()
            painter.rotate(i * angle_step)

            r_start = pulse_r
            r_end = pulse_r + bar_len

            # Gradient fading towards outer tip
            grad = QLinearGradient(0, r_start, 0, r_end)
            c1 = QColor(color)
            c1.setAlpha(225)
            c2 = QColor(color)
            c2.setAlpha(0)
            grad.setColorAt(0.0, c1)
            grad.setColorAt(0.72, c1)
            grad.setColorAt(1.0, c2)

            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.NoPen)

            w = 2.8 + (mag * 11)
            painter.drawRoundedRect(QRectF(-w / 2, r_start, w, bar_len), w / 2, w / 2)

            # Bright tip indicator
            if mag > 0.15:
                dot_col = color.lighter(180)
                dot_col.setAlpha(200)
                painter.setBrush(QBrush(dot_col))
                painter.drawEllipse(QPointF(0, r_end - 4), w * 0.4, w * 0.4)

            painter.restore()

        painter.restore()

        # 5. Outrun Central Dial Core (Radial Gradient with Horizontal Cutouts)
        halo_r = pulse_r * 0.88
        halo_grad = QRadialGradient(QPointF(center_x, center_y), halo_r)

        c_inner = self.theme.get_color(0)
        c_inner.setAlpha(190)
        c_outer = QColor(c_inner)
        c_outer.setAlpha(0)

        halo_grad.setColorAt(0.0, c_inner)
        halo_grad.setColorAt(0.85, c_inner)
        halo_grad.setColorAt(1.0, c_outer)

        painter.setBrush(QBrush(halo_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(center_x, center_y), halo_r, halo_r)

        # Synthwave/Outrun Sun horizontal cutouts overlay
        num_cuts = 6
        bg_color = QColor(self.theme.bg_color)
        bg_color.setAlpha(220)
        for i in range(num_cuts):
            ratio = (i + 1) / (num_cuts + 1)
            # Position cutoff lines from middle to bottom
            cut_y = center_y - halo_r + (halo_r * 2) * (0.3 + ratio * 0.6)
            thickness = 1.0 + (ratio * 4.0) * (1.0 + self.smoothed_bass * 0.3)

            cut_rect = QRectF(center_x - halo_r - 2, cut_y - thickness / 2, halo_r * 2 + 4, thickness)
            painter.fillRect(cut_rect, QBrush(bg_color))
