from __future__ import annotations
import numpy as np
import math
import random
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QRadialGradient, QPainterPath
from PySide6.QtCore import Qt, QPointF
from visualizer import BaseVisualizer


class CircularSpectrum(BaseVisualizer):
    """Circular spectrum with high impact, rotating grids, glassmorphism, and erupting sparks."""

    def __init__(self):
        """Initialize the visualizer with physics and particle states."""
        super().__init__("Circular Spectrum")
        self.num_bands = 64
        self.min_radius = 80
        self.bar_width = 3
        self.smoothed_bass = 0.0
        self.smoothed_bars = np.zeros(self.num_bands, dtype=np.float64)
        self.smoothing_factor = 0.75  # Smooth interpolation (75% prev, 25% new)

        self.idle_phase = 0.0
        self.top_bars_count = 10

        # Effects State
        self.shockwaves = []
        self.rotation_angle = 0.0  # Slow environment rotation
        self.particles = []
        self.max_particles = 120

    def set_size(self, width: int, height: int):
        super().set_size(width, height)
        self.particles = []

    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        if self.theme is None:
            return

        painter.setRenderHint(QPainter.Antialiasing, True)

        self.idle_phase += 0.04
        self.rotation_angle += 0.05

        # Layout
        center_x = self.width / 2
        center_y = self.height / 2
        max_radius = min(self.width, self.height) / 2 - 20
        bar_zone = max_radius - self.min_radius

        # ──────────────── Frequency Analysis ────────────────
        n_fft = len(fft_data)
        effective_n = int(n_fft * 0.25)

        log_indices = np.logspace(
            np.log10(2), np.log10(max(effective_n, 10)), self.num_bands + 1
        ).astype(int)

        magnitudes = np.empty(self.num_bands, dtype=np.float64)
        for i in range(self.num_bands):
            lo = log_indices[i]
            hi = max(lo + 1, log_indices[i + 1])
            if lo < n_fft:
                magnitudes[i] = np.mean(fft_data[lo : min(hi, n_fft)])
            else:
                magnitudes[i] = 0.0

        # ──────────────── Boost and Power Curve ────────────────
        bass_end = self.num_bands // 4
        mids_end = int(self.num_bands * 0.6)

        boost = np.ones(self.num_bands, dtype=np.float64)
        boost[:bass_end] = 1.8
        boost[bass_end:mids_end] = 3.5
        boost[mids_end:] = 5.5

        magnitudes = magnitudes * boost
        magnitudes[:bass_end] = np.power(np.clip(magnitudes[:bass_end], 0.0, None), 0.45)
        magnitudes[bass_end:] = np.power(np.clip(magnitudes[bass_end:], 0.0, None), 0.5)

        # ──────────────── Idle Micro-Dynamics ────────────────
        for i in range(self.top_bars_count):
            oscillation = (math.sin(self.idle_phase + i * 0.5) * 0.5) + 0.5
            idle_magnitude = oscillation * 0.15
            threshold = 0.25
            if magnitudes[i] < threshold:
                blend_factor = 1.0 - (magnitudes[i] / threshold)
                magnitudes[i] += idle_magnitude * blend_factor

        # ──────────────── Smoothing & Scale ────────────────
        target_lengths = magnitudes * bar_zone * 1.8
        self.smoothed_bars = (self.smoothed_bars * self.smoothing_factor) + (
            target_lengths * (1.0 - self.smoothing_factor)
        )
        current_bar_lengths = self.smoothed_bars
        bar_lengths = np.clip(current_bar_lengths, 3.0, bar_zone)

        # ──────────────── Bass energy & Inner radius pulse ────────────────
        bass_energy = float(np.mean(magnitudes[: max(1, bass_end)]))

        if bass_energy > 0.3 and (bass_energy - self.smoothed_bass) > 0.05:
            if not self.shockwaves or self.shockwaves[-1][0] > self.min_radius + 30:
                self.shockwaves.append([self.min_radius, 1.0])

        self.smoothed_bass += (bass_energy - self.smoothed_bass) * 0.2
        pulse_offset = min(self.smoothed_bass * 50.0, 22.0)
        current_inner_r = self.min_radius + pulse_offset
        center_r = current_inner_r - 8

        # ──────────────── Particle Spark System (Spawn & Update) ────────────────
        # Spawn particles on bass hits
        if bass_energy > 0.25 and len(self.particles) < self.max_particles:
            num_spawn = int(4 * bass_energy)
            for _ in range(num_spawn):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(1.5, 4.5) * (1.0 + bass_energy)
                self.particles.append({
                    "x": center_x + math.cos(angle) * current_inner_r,
                    "y": center_y + math.sin(angle) * current_inner_r,
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed,
                    "alpha": 1.0,
                    "size": random.uniform(1.2, 3.2),
                    "color_pos": random.uniform(0.0, 1.0)
                })

        # Update and render particles
        active_particles = []
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["alpha"] -= 0.018
            if p["alpha"] > 0:
                col = self.theme.get_gradient_color(p["color_pos"])
                p_col = QColor(col)
                p_col.setAlphaF(p["alpha"] * 0.7)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(p_col))
                painter.drawEllipse(QPointF(p["x"], p["y"]), p["size"], p["size"])
                active_particles.append(p)
        self.particles = active_particles

        # ──────────────── Render Shockwaves ────────────────
        painter.setBrush(Qt.NoBrush)
        new_shockwaves = []
        for r, opacity in self.shockwaves:
            r += 2.0 + (self.smoothed_bass * 4.0)
            opacity -= 0.016

            if opacity > 0.0 and r < max_radius:
                color = self.theme.get_gradient_color(0.2)
                wave_color = QColor(color)
                wave_color.setAlphaF(opacity * 0.35)
                pen = QPen(wave_color)
                pen.setWidthF(3.5)
                painter.setPen(pen)
                painter.drawEllipse(QPointF(center_x, center_y), r, r)
                new_shockwaves.append([r, opacity])
        self.shockwaves = new_shockwaves

        # ──────────────── Render Spectrogram Circular Bars ────────────────
        half_sweep = 180.0
        angle_step = half_sweep / self.num_bands

        for i in range(self.num_bands):
            mag = bar_lengths[i]
            color_pos = i / self.num_bands
            color = self.theme.get_gradient_color(color_pos)

            w = max(2.0, self.bar_width + (1.0 - color_pos) * 2.5)

            angle_right = i * angle_step
            angle_left = 360.0 - angle_right

            for angle_deg in (angle_right, angle_left):
                angle_rad = math.radians(angle_deg - 90 + self.rotation_angle)
                cos_a = math.cos(angle_rad)
                sin_a = math.sin(angle_rad)

                sx = center_x + cos_a * current_inner_r
                sy = center_y + sin_a * current_inner_r
                ex = center_x + cos_a * (current_inner_r + mag)
                ey = center_y + sin_a * (current_inner_r + mag)

                start_pt = QPointF(sx, sy)
                end_pt = QPointF(ex, ey)

                # Translucent Outer Glow
                glow_color = QColor(color)
                glow_intensity = min(200, max(25, int(mag * 2.2)))
                glow_color.setAlpha(glow_intensity)
                glow_pen = QPen(QBrush(glow_color), w * 3.8)
                glow_pen.setCapStyle(Qt.RoundCap)
                painter.setPen(glow_pen)
                painter.drawLine(start_pt, end_pt)

                # Bright Core Line
                core_color = color.lighter(125) if mag > 12 else color
                pen = QPen(QBrush(core_color), w)
                pen.setCapStyle(Qt.RoundCap)
                painter.setPen(pen)
                painter.drawLine(start_pt, end_pt)

                # High intensity neon tip dot
                if mag > 8:
                    dot_color = color.lighter(180)
                    dot_color.setAlpha(220)
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(dot_color))
                    painter.drawEllipse(end_pt, w * 0.75, w * 0.75)

        # ──────────────── Central Dial Grid Overlay ────────────────
        painter.save()
        clip_path = QPainterPath()
        clip_path.addEllipse(QPointF(center_x, center_y), center_r, center_r)
        painter.setClipPath(clip_path)

        grid_color = self.theme.get_color(0)
        grid_color.setAlpha(35)
        # In PySide6, Qt.DashLine can be set on a QPen
        grid_pen = QPen(QBrush(grid_color), 1.0, Qt.DashLine)
        painter.setPen(grid_pen)

        painter.translate(center_x, center_y)
        painter.save()
        painter.rotate(self.rotation_angle * 12.0)
        for _ in range(0, 360, 30):
            painter.drawLine(0, 0, int(center_r), 0)
            painter.rotate(30)
        painter.restore()

        # Concentric tech rings
        painter.drawEllipse(QPointF(0, 0), center_r * 0.4, center_r * 0.4)
        painter.drawEllipse(QPointF(0, 0), center_r * 0.7, center_r * 0.7)
        painter.restore()

        # ──────────────── Frosted Glass Dial ────────────────
        dial_gradient = QRadialGradient(QPointF(center_x, center_y), center_r)
        bg_color = QColor(self.theme.bg_color)
        bg_color.setAlpha(170)
        glow_brand = self.theme.get_color(0)
        glow_brand.setAlpha(70)

        dial_gradient.setColorAt(0.0, glow_brand)
        dial_gradient.setColorAt(0.82, bg_color)
        dial_gradient.setColorAt(1.0, bg_color.darker(115))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(dial_gradient))
        painter.drawEllipse(QPointF(center_x, center_y), center_r, center_r)

        # Frosted glass ring border
        glass_border = QColor(255, 255, 255, 55)
        border_pen = QPen(QBrush(glass_border), 1.6)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(center_x, center_y), center_r, center_r)
