from __future__ import annotations
import numpy as np
from PySide6.QtGui import QPainter, QPen, QColor, QRadialGradient, QBrush, QPolygonF
from PySide6.QtCore import Qt, QPointF
from visualizer import BaseVisualizer


class Oscilloscope(BaseVisualizer):
    """Oscilloscope optimizado para máxima fluidez y rendimiento cinemático."""

    def __init__(self):
        super().__init__("Oscilloscope")
        self.smooth_scale = 1.0
        self.interpolation_factor = 0.25  # Más rápido para mayor respuesta
        self.scan_y = 0.0

    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        if self.theme is None or len(waveform) < 2:
            return

        painter.setRenderHint(QPainter.Antialiasing, True)

        # 1. Procesamiento de Energía
        avg_energy = float(np.mean(np.abs(waveform)))

        center_x = self.width / 2
        center_y = self.height / 2

        # 2. Retícula del Osciloscopio (Grid)
        grid_color = QColor(self.theme.get_color(0))
        grid_color.setAlpha(25)
        painter.setPen(QPen(grid_color, 1))

        # Dibujar cuadrícula
        grid_spacing = 50
        for x in range(int(center_x) % grid_spacing, int(self.width), grid_spacing):
            painter.drawLine(x, 0, x, int(self.height))
        for y in range(int(center_y) % grid_spacing, int(self.height), grid_spacing):
            painter.drawLine(0, y, int(self.width), y)

        # Regla central
        grid_color.setAlpha(60)
        painter.setPen(QPen(grid_color, 2))
        painter.drawLine(0, int(center_y), int(self.width), int(center_y))
        painter.drawLine(int(center_x), 0, int(center_x), int(self.height))

        # 3. Construcción del Lissajous ultra fluido
        num_points = min(1024, len(waveform))

        # Escala dinámica suave
        base_r = min(self.width, self.height)
        target_scale = (base_r * 0.45) * (1.0 + avg_energy * 2.0)
        self.smooth_scale += (
            target_scale - self.smooth_scale
        ) * self.interpolation_factor

        # Mapeo de Lissajous (X = señal, Y = señal desfasada)
        shift = num_points // 4  # Desfase para formar curvas cerradas
        x_vals = waveform[:num_points]
        y_vals = np.roll(waveform, shift)[:num_points]

        px = center_x + x_vals * self.smooth_scale
        py = center_y + y_vals * self.smooth_scale

        # Combinar en un QPolygonF para dibujado Vectorizado (Ultra Rápido)
        points = [QPointF(float(x), float(y)) for x, y in zip(px, py)]
        poly = QPolygonF(points)

        # 4. Renderizado con efecto CRT Glow Múltiple
        main_color = self.theme.get_color(0)

        # Glow exterior ancho
        glow1 = QColor(main_color)
        glow1.setAlpha(15)
        painter.setPen(QPen(glow1, 18, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPolyline(poly)

        # Glow interior intenso
        glow2 = QColor(main_color)
        glow2.setAlpha(60)
        painter.setPen(QPen(glow2, 6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPolyline(poly)

        # Núcleo brillante
        core = QColor(main_color.lighter(150))
        core.setAlpha(200)
        painter.setPen(QPen(core, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPolyline(poly)

        # Filamento central super blanco
        white_core = QColor(255, 255, 255, 255)
        painter.setPen(QPen(white_core, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPolyline(poly)

        # 5. Efecto Scanline constante (ciclo continuo, sin tirones)
        self.scan_y += 1.5
        if self.scan_y > self.height:
            self.scan_y = 0.0

        scan_color = QColor(255, 255, 255, 12)
        painter.setPen(QPen(scan_color, 4))
        painter.drawLine(0, int(self.scan_y), int(self.width), int(self.scan_y))

        # Viñeta (bordes oscuros)
        vignette = QRadialGradient(QPointF(center_x, center_y), self.width * 0.7)
        vignette.setColorAt(0, Qt.transparent)
        vignette.setColorAt(1, QColor(0, 0, 0, 180))
        painter.setBrush(QBrush(vignette))
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, int(self.width), int(self.height))
