from __future__ import annotations
import math
import numpy as np
from PySide6.QtGui import (
    QPainter,
    QPen,
    QColor,
    QRadialGradient,
    QBrush,
    QPolygonF,
)
from PySide6.QtCore import Qt, QPointF
from visualizer import BaseVisualizer


class Oscilloscope(BaseVisualizer):
    """Oscilloscope optimizado para máxima fluidez y rendimiento cinemático."""

    def __init__(self):
        super().__init__("Oscilloscope")
        self.line_width = 3
        self.flicker_intensity = 0.0
        self.glitch_timer = 0.0

        # Variables de suavizado
        self.smooth_scale = 1.0
        self.smooth_flicker = 0.0
        self.interpolation_factor = 0.18

        # Estado para estabilidad de frame-time
        self.phase = 0.0
        self.max_points = 360
        self.min_points = 180

    def _build_polyline(self, waveform: np.ndarray, center_x: float, center_y: float) -> QPolygonF:
        """Construye la polilínea principal minimizando costo por frame."""
        wf = np.nan_to_num(waveform, nan=0.0, posinf=0.0, neginf=0.0)

        # Puntos adaptativos según tamaño de waveform para evitar sobrecarga
        num_points = int(np.clip(len(wf) // 6, self.min_points, self.max_points))
        indices = np.linspace(0, len(wf) - 1, num_points, dtype=np.int32)

        x_vals = wf[indices]
        y_indices = (indices + len(wf) // 3) % len(wf)
        y_vals = wf[y_indices]

        # Jitter determinista (sin np.random por frame -> más estable)
        jitter_amount = 2.5 * self.smooth_flicker
        t = self.phase + np.linspace(0.0, 6.0, num_points)
        jitter_x = np.sin(t * 1.7) * jitter_amount
        jitter_y = np.cos(t * 2.1) * jitter_amount

        px = center_x + x_vals * self.smooth_scale + jitter_x
        py = center_y + y_vals * self.smooth_scale + jitter_y

        poly = QPolygonF()
        poly.reserve(num_points)
        for x, y in zip(px, py):
            poly.append(QPointF(float(x), float(y)))

        return poly

    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        if self.theme is None or len(waveform) < 2:
            return

        painter.setRenderHint(QPainter.Antialiasing, True)

        avg_energy = float(np.mean(np.abs(waveform)))

        # Flicker suave y acotado
        target_flicker = min(1.0, avg_energy * 2.4)
        self.smooth_flicker += (target_flicker - self.smooth_flicker) * self.interpolation_factor

        center_x = self.width / 2
        center_y = self.height / 2

        # Retícula ligera
        grid_color = QColor(self.theme.get_color(0))
        grid_color.setAlpha(34)
        painter.setPen(QPen(grid_color, 1))

        base_r = min(self.width, self.height)
        for r_factor in (0.22, 0.44, 0.66):
            r = base_r * r_factor
            painter.drawEllipse(QPointF(center_x, center_y), r, r)

        painter.drawLine(0, int(center_y), self.width, int(center_y))
        painter.drawLine(int(center_x), 0, int(center_x), self.height)

        # Escala dinámica con inercia
        target_scale = (base_r * 0.34) * (1.0 + avg_energy * 1.8)
        self.smooth_scale += (target_scale - self.smooth_scale) * self.interpolation_factor

        polyline = self._build_polyline(waveform, center_x, center_y)

        # Glow
        main_color = self.theme.get_color(0)
        glow_color = QColor(main_color)
        glow_color.setAlpha(int(24 + 56 * self.smooth_flicker))
        painter.setPen(QPen(glow_color, self.line_width + 8, Qt.SolidLine, Qt.RoundCap))
        painter.drawPolyline(polyline)

        # Núcleo
        core_color = QColor(main_color)
        if self.smooth_flicker > 0.65:
            core_color = core_color.lighter(135)

        painter.setPen(QPen(core_color, self.line_width, Qt.SolidLine, Qt.RoundCap))
        painter.drawPolyline(polyline)

        # Scanline más barata
        self.glitch_timer += 1.8
        scanline_y = (self.glitch_timer % 100.0) / 100.0 * self.height
        painter.setPen(QPen(QColor(255, 255, 255, 20), 2))
        painter.drawLine(0, int(scanline_y), self.width, int(scanline_y))

        # Viñeta
        vignette = QRadialGradient(QPointF(center_x, center_y), self.width * 0.72)
        vignette.setColorAt(0, Qt.transparent)
        vignette.setColorAt(1, QColor(0, 0, 0, 145))
        painter.setBrush(QBrush(vignette))
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, self.width, self.height)

        # Fase temporal para jitter determinista
        self.phase += 0.025 + (0.03 * self.smooth_flicker)
        if self.phase > math.tau:
            self.phase -= math.tau
