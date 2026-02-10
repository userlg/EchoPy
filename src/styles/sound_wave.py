from __future__ import annotations
import numpy as np
import random
from collections import deque
from PySide6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QColor,
    QLinearGradient,
    QRadialGradient,
)
from PySide6.QtCore import Qt, QPointF, QRectF
from visualizer import BaseVisualizer


class SoundWave(BaseVisualizer):
    """Onda de sonido estilo 'Bar-Wave' con impacto de plasma y rastro de energía."""

    def __init__(self):
        super().__init__("Sound Wave")
        self.history_size = 80  # Número de barras visibles
        self.points = deque([0.0] * self.history_size, maxlen=self.history_size)
        self.particles = []
        self.bar_spacing = 2
        self.smoothing = 0.3

    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        if self.theme is None or len(waveform) == 0:
            return

        painter.setRenderHint(QPainter.Antialiasing, True)

        # 1. CAPTURA DE IMPACTO (La fuerza de la palabra)
        # Usamos el valor pico pero con un "piso" mínimo para que la onda respire siempre
        peak = np.max(np.abs(waveform))
        # Suavizamos la entrada para evitar saltos nerviosos
        current_val = peak if peak > 0.05 else 0.02
        self.points.append(current_val)

        center_y = self.height / 2
        max_bar_h = self.height * 0.45
        total_bars = len(self.points)

        # Calculamos el ancho de cada barra para llenar la pantalla
        bar_w = (self.width - (total_bars * self.bar_spacing)) / total_bars

        # 2. RENDERIZADO DE BARRAS (Arquitectura de Poder)
        main_color = self.theme.get_color(0)

        for i, val in enumerate(self.points):
            # Posición X (Fluye de derecha a izquierda)
            x = i * (bar_w + self.bar_spacing)

            # Altura de la barra con curva de potencia para resaltar picos
            h = np.power(val, 0.5) * max_bar_h

            # Efecto de desvanecimiento a la izquierda (Sabiduría que deja rastro)
            fade_factor = i / total_bars
            alpha = int(255 * fade_factor)

            # Rectángulo de la barra (Simetría superior e inferior)
            rect_top = QRectF(x, center_y - h, bar_w, h)
            rect_bottom = QRectF(x, center_y, bar_w, h)

            # Gradiente de impacto (De centro brillante a puntas oscuras)
            grad = QLinearGradient(x, center_y - h, x, center_y + h)
            c_light = QColor(main_color.lighter(160))
            c_light.setAlpha(alpha)
            c_dark = QColor(main_color)
            c_dark.setAlpha(int(alpha * 0.3))

            grad.setColorAt(0.5, c_light)
            grad.setColorAt(0.0, c_dark)
            grad.setColorAt(1.0, c_dark)

            # Dibujamos las barras con bordes redondeados (Estética Premium)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(rect_top, bar_w / 2, bar_w / 2)
            painter.drawRoundedRect(rect_bottom, bar_w / 2, bar_w / 2)

            # 3. BRILLO DE NÚCLEO (Solo para la barra más reciente)
            if i == total_bars - 1:
                glow = QRadialGradient(QPointF(x + bar_w / 2, center_y), h * 1.5)
                glow_col = QColor(main_color.lighter(180))
                glow_col.setAlpha(100)
                glow.setColorAt(0, glow_col)
                glow.setColorAt(1, Qt.transparent)
                painter.setBrush(QBrush(glow))
                painter.drawEllipse(QPointF(x + bar_w / 2, center_y), h * 1.2, h * 1.2)

        # 4. SISTEMA DE CHISPAS (Energía en expansión)
        if peak > 0.4:
            for _ in range(2):
                self.particles.append(
                    {
                        "x": self.width - 20,
                        "y": center_y + random.uniform(-h, h),
                        "vx": -random.uniform(5, 15),
                        "vy": random.uniform(-3, 3),
                        "life": 1.0,
                        "size": random.uniform(2, 5),
                    }
                )

        new_particles = []
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 0.03
            if p["life"] > 0:
                p_col = QColor(main_color.lighter(200))
                p_col.setAlpha(int(p["life"] * 255))
                painter.setBrush(QBrush(p_col))
                painter.drawEllipse(QPointF(p["x"], p["y"]), p["size"], p["size"])
                new_particles.append(p)
        self.particles = new_particles

        # 5. LÍNEA DE HORIZONTE (Estabilidad estoica)
        horizon_color = QColor(main_color)
        horizon_color.setAlpha(60)
        horizon_pen = QPen(horizon_color)
        painter.setPen(horizon_pen)
        painter.drawLine(0, int(center_y), self.width, int(center_y))
