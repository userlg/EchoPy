from __future__ import annotations
import numpy as np
import math
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QRadialGradient
from PySide6.QtCore import Qt, QPointF
from visualizer import BaseVisualizer


class CircularSpectrum(BaseVisualizer):
    """Circular spectrum with mirrored bars, glow effects, and reactive center."""

    def __init__(self):
        """Initialize circular spectrum visualizer."""
        super().__init__("Circular Spectrum")
        self.num_bands = 64  # Half-circle bands (mirrored → 128 visual)
        self.min_radius = 80  # Inner circle radius
        self.bar_width = 3  # Base bar width in px
        self.smoothed_bass = 0.0  # For center pulse smoothing

        # Effects State
        self.rotation_angle = 0.0
        self.shockwaves = []  # List of (radius, opacity) tuples

    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        """Render enhanced circular spectrum with optimized vocal sensitivity."""
        if self.theme is None:
            return

        painter.setRenderHint(QPainter.Antialiasing, True)

        # Layout
        center_x = self.width / 2
        center_y = self.height / 2
        max_radius = min(self.width, self.height) / 2 - 20
        bar_zone = max_radius - self.min_radius

        # ──────────────── Frequency Binning (Optimized for Voice) ────────────────
        n_fft = len(fft_data)
        # Focus analysis on the lower 25% of the spectrum where the voice carries power
        effective_n = int(n_fft * 0.25)

        log_indices = np.logspace(
            np.log10(2), np.log10(effective_n), self.num_bands + 1
        ).astype(int)

        # Pre-compute magnitudes for each band
        magnitudes = np.empty(self.num_bands, dtype=np.float64)
        for i in range(self.num_bands):
            lo = log_indices[i]
            hi = max(lo + 1, log_indices[i + 1])
            if lo < n_fft:
                magnitudes[i] = np.mean(fft_data[lo : min(hi, n_fft)])
            else:
                magnitudes[i] = 0.0

        # ──────────────── Aggressive Boost & Power Curve ────────────────
        bass_end = self.num_bands // 4
        mids_end = int(self.num_bands * 0.6)

        boost = np.ones(self.num_bands, dtype=np.float64)
        boost[:bass_end] = 1.5  # Deep punch
        boost[bass_end:mids_end] = 3.0  # Vocal core clarity
        boost[mids_end:] = 5.5  # High-frequency presence (breathing/clarity)

        magnitudes = magnitudes * boost
        # Expanded power curve to make subtle sounds more visible
        magnitudes = np.power(np.clip(magnitudes, 0.0, None), 0.5)

        # Scale to bar zone with high impact multiplier
        bar_lengths = magnitudes * bar_zone * 45.0
        bar_lengths = np.clip(bar_lengths, 3.0, bar_zone)

        # ──────────────── Bass energy → center pulse & shockwaves ────────────────
        bass_energy = float(np.mean(magnitudes[: max(1, bass_end)]))

        if bass_energy > 0.3 and (bass_energy - self.smoothed_bass) > 0.05:
            if not self.shockwaves or self.shockwaves[-1][0] > self.min_radius + 30:
                self.shockwaves.append([self.min_radius, 1.0])

        self.smoothed_bass += (bass_energy - self.smoothed_bass) * 0.25
        pulse_offset = min(self.smoothed_bass * 60.0, 25.0)

        current_inner_r = self.min_radius + pulse_offset

        # Update Rotation
        rotation_speed = 0.2 + (self.smoothed_bass * 1.5)
        self.rotation_angle = (self.rotation_angle + rotation_speed) % 360.0

        # ──────────────── Render Shockwaves ────────────────
        painter.setBrush(Qt.NoBrush)
        new_shockwaves = []
        for r, opacity in self.shockwaves:
            r += 2.0 + (self.smoothed_bass * 5.0)
            opacity -= 0.015

            if opacity > 0.0 and r < max_radius:
                color = self.theme.get_color(0.2)
                wave_color = QColor(color)
                wave_color.setAlphaF(opacity * 0.4)
                pen = QPen(wave_color)
                pen.setWidthF(4.0)
                painter.setPen(pen)
                painter.drawEllipse(QPointF(center_x, center_y), r, r)
                new_shockwaves.append([r, opacity])

        self.shockwaves = new_shockwaves

        # ──────────────── Render bars (mirrored + rotated) ────────────────
        half_sweep = 180.0
        angle_step = half_sweep / self.num_bands

        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.rotation_angle)
        painter.translate(-center_x, -center_y)

        for i in range(self.num_bands):
            mag = bar_lengths[i]
            color_pos = i / self.num_bands
            color = self.theme.get_gradient_color(color_pos)

            w = max(2, int(self.bar_width + (1.0 - color_pos) * 3))

            angle_right = i * angle_step
            angle_left = 360.0 - angle_right

            for angle_deg in (angle_right, angle_left):
                angle_rad = math.radians(angle_deg - 90)
                cos_a = math.cos(angle_rad)
                sin_a = math.sin(angle_rad)

                sx = center_x + cos_a * current_inner_r
                sy = center_y + sin_a * current_inner_r
                ex = center_x + cos_a * (current_inner_r + mag)
                ey = center_y + sin_a * (current_inner_r + mag)

                start_pt = QPointF(sx, sy)
                end_pt = QPointF(ex, ey)

                # Glow halo
                glow_color = QColor(color)
                glow_color.setAlpha(50)
                glow_pen = QPen(glow_color)
                glow_pen.setWidthF(w * 3.0)
                glow_pen.setCapStyle(Qt.RoundCap)
                painter.setPen(glow_pen)
                painter.drawLine(start_pt, end_pt)

                # Core bar
                pen = QPen(color)
                pen.setWidthF(w)
                pen.setCapStyle(Qt.RoundCap)
                painter.setPen(pen)
                painter.drawLine(start_pt, end_pt)

        painter.restore()

        # ──────────────── Reactive center core ────────────────
        center_r = current_inner_r - 8
        core_color = self.theme.get_color(0)

        gradient = QRadialGradient(QPointF(center_x, center_y), center_r)
        inner_color = QColor(core_color)
        inner_color.setAlpha(140)
        gradient.setColorAt(0.0, inner_color)

        mid_color = QColor(core_color)
        mid_color.setAlpha(70)
        gradient.setColorAt(0.6, mid_color)

        edge_color = QColor(core_color)
        edge_color.setAlpha(0)
        gradient.setColorAt(1.0, edge_color)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(center_x, center_y), center_r, center_r)

        ring_color = QColor(core_color)
        ring_color.setAlpha(100)
        ring_pen = QPen(ring_color)
        ring_pen.setWidthF(1.5)
        painter.setPen(ring_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(
            QPointF(center_x, center_y), current_inner_r, current_inner_r
        )
