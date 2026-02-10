from __future__ import annotations
import numpy as np
import math
from PySide6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QColor,
    QRadialGradient,
    QLinearGradient,
)
from PySide6.QtCore import Qt, QPointF, QRectF
from visualizer import BaseVisualizer


class RadialBars(BaseVisualizer):
    """Radial bars with fixed orientation and high-impact vocal sensitivity."""

    def __init__(self):
        super().__init__("Radial Bars")
        self.num_rays = 120
        self.min_radius = 60  # Núcleo más sólido
        self.smoothed_bass = 0.0

    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        if self.theme is None or fft_data is None:
            return

        painter.setRenderHint(QPainter.Antialiasing, True)

        center_x = self.width / 2
        center_y = self.height / 2
        max_radius = min(self.width, self.height) / 2 - 20
        bar_len_max = max_radius - self.min_radius

        # ──────────── Frequency Binning (Vocal focus: 25%) ────────────
        n_fft = len(fft_data)
        # Concentramos las 120 barras en el rango donde la voz domina
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

        # ──────────── Sensibilidad Agresiva ────────────
        bass_end = self.num_rays // 4
        mids_end = int(self.num_rays * 0.6)

        boost = np.ones(self.num_rays, dtype=np.float64)
        boost[:bass_end] = 1.8  # Graves con autoridad
        boost[bass_end:mids_end] = 3.5  # Mids (Cuerpo de la voz)
        boost[mids_end:] = 5.0  # Highs (Claridad y aire)

        magnitudes = magnitudes * boost
        # Expansión de señales débiles para movimiento constante
        magnitudes = np.power(np.clip(magnitudes, 0.0, None), 0.5)

        # Pulso del núcleo central
        bass_energy = float(np.mean(magnitudes[: max(1, bass_end)]))
        self.smoothed_bass += (bass_energy - self.smoothed_bass) * 0.2
        pulse_r = self.min_radius + (self.smoothed_bass * 40.0)

        # ──────────── Renderizado Estático (Sin Giro) ────────────
        # Guardamos el estado central
        painter.save()
        painter.translate(center_x, center_y)

        angle_step = 360.0 / self.num_rays

        for i in range(self.num_rays):
            mag = magnitudes[i]

            # Longitud de barra con multiplicador de impacto
            bar_len = mag * bar_len_max * 1.8
            bar_len = np.clip(bar_len, 4.0, bar_len_max)

            # Color según posición radial (Armonía)
            color_pos = i / self.num_rays
            color = self.theme.get_gradient_color(color_pos)

            painter.save()
            # Rotamos cada barra a su posición fija, pero sin rotación global del sistema
            painter.rotate(i * angle_step)

            r_start = pulse_r
            r_end = pulse_r + bar_len

            # Gradiente: del núcleo hacia la punta desapareciendo
            grad = QLinearGradient(0, r_start, 0, r_end)
            c1 = QColor(color)
            c1.setAlpha(220)
            c2 = QColor(color)
            c2.setAlpha(0)
            grad.setColorAt(0.0, c1)
            grad.setColorAt(0.7, c1)  # Mantiene color la mayor parte
            grad.setColorAt(1.0, c2)

            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.NoPen)

            # Ancho dinámico para mayor agresividad visual
            w = 3 + (mag * 12)
            # Dibujamos barras con puntas redondeadas para estilo premium
            painter.drawRoundedRect(QRectF(-w / 2, r_start, w, bar_len), w / 2, w / 2)

            painter.restore()

        painter.restore()

        # ──────────── Núcleo de Poder (Halo Central) ────────────
        halo_r = pulse_r * 0.9
        halo_grad = QRadialGradient(QPointF(center_x, center_y), halo_r)

        c_inner = self.theme.get_color(0)
        c_inner.setAlpha(180)
        c_outer = QColor(c_inner)
        c_outer.setAlpha(0)

        halo_grad.setColorAt(0.0, c_inner)
        halo_grad.setColorAt(0.8, c_inner)
        halo_grad.setColorAt(1.0, c_outer)

        painter.setBrush(QBrush(halo_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(center_x, center_y), halo_r, halo_r)
