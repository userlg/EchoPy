from __future__ import annotations
import numpy as np
import random
from PySide6.QtGui import QPainter, QBrush, QColor, QLinearGradient, QPen
from PySide6.QtCore import Qt, QPointF, QRectF
from visualizer import BaseVisualizer


class SpectrumBars(BaseVisualizer):
    """Spectrum analyzer with segmented LED columns, glassmorphic backplate, and rising embers."""

    def __init__(self):
        super().__init__("Spectrum Bars")
        self.num_bars = 64
        self.bar_spacing = 3
        self.corner_radius = 2

        # Peak hold state
        self.peaks = np.zeros(self.num_bars, dtype=np.float64)
        self.peak_decay = 0.94
        self.peak_gravity = 0.003

        # Particle state
        self.particles = []
        self.max_particles = 120

    def set_size(self, width: int, height: int):
        super().set_size(width, height)
        self.particles = []

    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        if self.theme is None:
            return

        painter.setRenderHint(QPainter.Antialiasing, True)

        # 1. Backing Glassmorphic Card Panel
        card_rect = QRectF(15, 20, self.width - 30, self.height - 40)
        card_bg = QColor(self.theme.bg_color)
        card_bg.setAlpha(125)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(card_bg))
        painter.drawRoundedRect(card_rect, 10, 10)

        # Frosted glass thin border
        card_border = QColor(255, 255, 255, 25)
        border_pen = QPen(QBrush(card_border), 1.2)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(card_rect, 10, 10)

        # Horizontal calibration scale lines
        grid_color = self.theme.get_color(1)
        grid_color.setAlpha(22)
        grid_pen = QPen(QBrush(grid_color), 1.0, Qt.DashLine)
        painter.setPen(grid_pen)
        for ratio in [0.25, 0.5, 0.75]:
            y_grid = card_rect.top() + card_rect.height() * ratio
            painter.drawLine(card_rect.left(), y_grid, card_rect.right(), y_grid)

        # 2. Layout Geometry
        total_width = card_rect.width() - (self.num_bars * self.bar_spacing)
        bar_width = max(3.0, total_width / self.num_bars)
        baseline_y = card_rect.bottom() - 10

        n_fft = len(fft_data)

        # 3. Frequency Binning (Vocal Focus)
        useful_bins = int(n_fft * 0.20)
        log_indices = np.logspace(
            np.log10(2), np.log10(max(useful_bins, 10)), self.num_bars + 1
        ).astype(int)

        raw_magnitudes = np.empty(self.num_bars, dtype=np.float64)
        for i in range(self.num_bars):
            lo = log_indices[i]
            hi = max(lo + 1, log_indices[i + 1])
            raw_magnitudes[i] = (
                np.mean(fft_data[lo : min(hi, n_fft)]) if lo < n_fft else 0.0
            )

        # Symmetric Center-Out distribution
        magnitudes = np.empty(self.num_bars)
        half = self.num_bars // 2

        for i in range(self.num_bars):
            dist_from_center = abs(i - half)
            magnitudes[i] = raw_magnitudes[dist_from_center]

        # Dynamic boost
        edge_boost = np.linspace(1.5, 1.0, half)
        boost = np.concatenate([edge_boost, edge_boost[::-1]])

        magnitudes *= boost
        magnitudes = np.power(np.clip(magnitudes, 0.0, None), 0.7)

        # Update Peaks
        self.peaks = np.maximum(
            self.peaks * self.peak_decay - self.peak_gravity, magnitudes
        )

        # 4. Render Segments & Peaks
        segment_h = 5
        gap = 2
        step_y = segment_h + gap
        max_h = card_rect.height() - 30

        for i in range(self.num_bars):
            mag = magnitudes[i]
            peak = self.peaks[i]

            bar_height = min(mag * max_h, max_h)
            peak_height = min(peak * max_h, max_h)

            x = card_rect.left() + i * (bar_width + self.bar_spacing)
            y_bar = baseline_y - bar_height
            y_peak = baseline_y - peak_height

            color_pos = abs(i - half) / half
            color = self.theme.get_gradient_color(color_pos)

            # Draw Segmented Column
            num_segments = int(bar_height / step_y)
            for s in range(num_segments):
                y_seg = baseline_y - (s + 1) * step_y
                
                # Dynamic segment color gradient
                seg_ratio = s / (max_h / step_y)
                seg_color = self.theme.get_gradient_color(min(1.0, seg_ratio * 1.25))

                # Segment outer glow
                if mag > 0.04:
                    sg_color = QColor(seg_color)
                    sg_color.setAlpha(40)
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(sg_color))
                    painter.drawRoundedRect(
                        QRectF(x - 1, y_seg - 1, bar_width + 2, segment_h + 2),
                        self.corner_radius + 0.5,
                        self.corner_radius + 0.5,
                    )

                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(seg_color))
                painter.drawRoundedRect(
                    QRectF(x, y_seg, bar_width, segment_h),
                    self.corner_radius,
                    self.corner_radius,
                )

            # Spawn Ember Particles on active bars
            if mag > 0.35 and len(self.particles) < self.max_particles and random.random() < 0.18:
                self.particles.append({
                    "x": x + bar_width / 2.0 + random.uniform(-1, 1),
                    "y": y_bar - 4,
                    "vx": random.uniform(-0.4, 0.4),
                    "vy": random.uniform(-1.2, -2.6),
                    "alpha": 1.0,
                    "size": random.uniform(1.2, 2.8),
                    "color": color
                })

            # Draw Glowing Peak Indicators (Laser Caps)
            if peak_height > bar_height + 4:
                # Translucent Peak Glow Ring
                glow_col = QColor(color)
                glow_col.setAlpha(110)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(glow_col))
                painter.drawEllipse(
                    QPointF(x + bar_width / 2, y_peak),
                    bar_width * 0.7 + 2.0,
                    bar_width * 0.7 + 2.0
                )

                # Core incandescent dot
                p_col = QColor(255, 255, 255) if peak > 0.75 else QColor(color.lighter(170))
                p_col.setAlpha(210)
                painter.setBrush(QBrush(p_col))
                painter.drawEllipse(
                    QPointF(x + bar_width / 2, y_peak),
                    bar_width * 0.5,
                    bar_width * 0.5
                )

        # 5. Update and Draw Ember Particles
        active_particles = []
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["alpha"] -= 0.024
            
            # Keep inside the card panel boundary
            if p["alpha"] > 0 and card_rect.top() < p["y"] < card_rect.bottom():
                p_col = QColor(p["color"])
                p_col.setAlphaF(p["alpha"] * 0.75)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(p_col))
                painter.drawEllipse(QPointF(p["x"], p["y"]), p["size"], p["size"])
                active_particles.append(p)
        self.particles = active_particles
