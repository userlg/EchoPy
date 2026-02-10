from __future__ import annotations
import numpy as np
import math
from PySide6.QtGui import QPainter, QPen, QPainterPath, QColor, QLinearGradient, QBrush
from PySide6.QtCore import Qt, QPointF
from visualizer import BaseVisualizer


class AudioLines(BaseVisualizer):
    """Energy ribbons with high-impact flow and vocal-driven turbulence."""
    
    def __init__(self):
        super().__init__("Audio Lines")
        self.num_layers = 8  # Más capas para mayor profundidad visual
        self.line_width = 2
        self.time = 0.0
        self.smoothing = 0.2  # Suavizado para una fluidez cinematográfica
        self.prev_magnitudes = None
    
    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        if self.theme is None or fft_data is None:
            return
        
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # 1. Análisis de Poder Vocal (Foco en la autoridad de la voz)
        n_fft = len(fft_data)
        num_points = 12  # Puntos de control para la curva
        samples_per_point = max(1, int(n_fft * 0.25) // num_points)
        
        current_mags = np.zeros(num_points)
        for i in range(num_points):
            start = i * samples_per_point
            end = start + samples_per_point
            current_mags[i] = np.mean(fft_data[start:end]) if start < n_fft else 0

        # Suavizado temporal para evitar saltos nerviosos
        if self.prev_magnitudes is None:
            self.prev_magnitudes = current_mags
        else:
            self.prev_magnitudes = (current_mags * self.smoothing) + (self.prev_magnitudes * (1.0 - self.smoothing))

        # 2. Renderizado de Capas de Energía (Ribbons)
        for layer in range(self.num_layers):
            path = QPainterPath()
            
            # Color y degradado de la capa
            color_pos = layer / self.num_layers
            base_color = self.theme.get_gradient_color(color_pos)
            
            # El listón se sitúa en el centro con un ligero offset por capa
            center_y = self.height * 0.5
            layer_offset = (layer - (self.num_layers / 2)) * 15
            
            points = []
            for i in range(num_points):
                x = (i / (num_points - 1)) * self.width
                
                # Dinámica de movimiento:
                # - Sinusoidal constante para el "flow"
                # - Reacción al audio multiplicada por el peso de la capa
                phase = i * 0.8 + layer * 0.5 + self.time
                wave = math.sin(phase) * (20 + layer * 5)
                audio_react = self.prev_magnitudes[i] * (200 + layer * 50)
                
                y = center_y + layer_offset + wave + audio_react
                points.append(QPointF(x, y))

            # 3. Construcción de la Curva (Cubic Bezier para suavidad extrema)
            path.moveTo(points[0])
            for i in range(len(points) - 1):
                p1 = points[i]
                p2 = points[i+1]
                # Puntos de control para suavizado
                control_x = (p1.x() + p2.x()) / 2
                path.cubicTo(QPointF(control_x, p1.y()), QPointF(control_x, p2.y()), p2)

            # 4. Estética de Alto Impacto
            # Relleno sutil entre la línea y el horizonte para dar volumen
            fill_path = QPainterPath(path)
            fill_path.lineTo(self.width, center_y)
            fill_path.lineTo(0, center_y)
            fill_path.closeSubpath()
            
            fill_grad = QLinearGradient(0, center_y - 100, 0, center_y + 100)
            c_fill = QColor(base_color)
            c_fill.setAlpha(30)
            fill_grad.setColorAt(0, Qt.transparent)
            fill_grad.setColorAt(0.5, c_fill)
            fill_grad.setColorAt(1, Qt.transparent)
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(fill_grad))
            painter.drawPath(fill_path)

            # Dibujo de la línea principal con resplandor
            glow_color = QColor(base_color)
            glow_color.setAlpha(60)
            painter.setPen(QPen(glow_color, self.line_width + 6, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

            core_pen = QPen(base_color, self.line_width)
            if layer % 2 == 0: core_pen.setColor(base_color.lighter(150)) # Brillo extra en capas alternas
            painter.setPen(core_pen)
            painter.drawPath(path)

        self.time += 0.04 # Velocidad del flujo