from __future__ import annotations
import numpy as np
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QLinearGradient, QPainterPath
from PySide6.QtCore import Qt, QPointF
from visualizer import BaseVisualizer


class Waveform(BaseVisualizer):
    """Enhanced cinematic waveform with energy aura and mirrored pulse."""

    def __init__(self):
        super().__init__("Waveform")
        self.line_width = 3
        self.prev_waveform = None
        self.smoothing = 0.3  # Suavizado para evitar el parpadeo errático

    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        if self.theme is None or len(waveform) == 0:
            return

        painter.setRenderHint(QPainter.Antialiasing, True)

        # 1. Preparación de la Onda Real y Limpieza
        # Removido el if/else de prev_waveform agresivo. El AudioProcessor global
        # ya administra muy bien la señal amortiguada si se desea suavizado.

        # Ocasionalmente el waveform literal es un poco nervioso visualmente,
        # optaremos por un smoothing muy sutil sólo para no dañar las curvas ricas.
        # Pero nos aseguraremos que siempre dibuje.

        if self.prev_waveform is None or len(self.prev_waveform) != len(waveform):
            self.prev_waveform = np.array(waveform)
        else:
            # Smoothing hiper bajo enfocado a mantener el diseño líquido (0.1 frente al viejo 0.3)
            # Esto ayuda a que el trazado Bezier no se rompa visualmente.
            smoothing = 0.05
            self.prev_waveform = (waveform * (1.0 - smoothing)) + (
                self.prev_waveform * smoothing
            )

        # 2. Submuestreo para Cubic Bezier (Curvas suaves reales)
        # Menos puntos = ondas más redondeadas y líquidas
        num_points = 80
        step = max(1, len(self.prev_waveform) // num_points)

        center_y = self.height / 2
        amplitude = self.height * 0.45  # Alto impacto

        path_top = QPainterPath()
        path_bottom = QPainterPath()

        # Puntos de control para la interpolación
        points = []
        for i in range(0, len(self.prev_waveform), step):
            sample = self.prev_waveform[i]
            # La waveform puede explotar, limitamos suavemente
            val = np.tanh(sample * 1.5)  # Soft clipping elegante
            x = (i / len(self.prev_waveform)) * self.width
            y_offset = val * amplitude
            points.append((x, y_offset))

        # Aseguramos inicio y fin en el horizonte
        if not points:
            return
        points[0] = (0, 0)
        points[-1] = (self.width, 0)

        # 3. Trazado de Curva Cúbica (Bezieres en lugar de Líneas Rectas)
        path_top.moveTo(points[0][0], center_y - points[0][1])
        path_bottom.moveTo(points[0][0], center_y + points[0][1])

        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]

            # Puntos de control en X (mitad del camino entre los puntos) para curvatura perfecta
            cp_x = (x1 + x2) / 2

            # Curva Superior
            path_top.cubicTo(
                QPointF(cp_x, center_y - y1),
                QPointF(cp_x, center_y - y2),
                QPointF(x2, center_y - y2),
            )
            # Curva Inferior (Espejo)
            path_bottom.cubicTo(
                QPointF(cp_x, center_y + y1),
                QPointF(cp_x, center_y + y2),
                QPointF(x2, center_y + y2),
            )

        # 4. Renderizado del Aura Eléctrica (Glow central a bordes)
        fill_path = QPainterPath(path_top)
        fill_path.connectPath(path_bottom.toReversed())
        fill_path.closeSubpath()

        main_color = self.theme.get_color(0)
        alt_color = self.theme.get_color(1)

        grad_fill = QLinearGradient(0, center_y - amplitude, 0, center_y + amplitude)
        c_core = QColor(main_color)
        c_core.setAlpha(160)
        c_fade = QColor(alt_color)
        c_fade.setAlpha(0)

        grad_fill.setColorAt(0.0, c_fade)
        grad_fill.setColorAt(0.5, c_core)
        grad_fill.setColorAt(1.0, c_fade)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(grad_fill))
        painter.drawPath(fill_path)

        # 5. Capas de Líneas Estilizadas (Nebulosa exterior a Láser interior)
        # Capa Glow Ancha
        glow_pen_wide = QPen(
            QColor(main_color.red(), main_color.green(), main_color.blue(), 30)
        )
        glow_pen_wide.setWidth(12)
        glow_pen_wide.setCapStyle(Qt.RoundCap)
        painter.setPen(glow_pen_wide)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path_top)
        painter.drawPath(path_bottom)

        # Capa Glow Media
        glow_pen_mid = QPen(
            QColor(alt_color.red(), alt_color.green(), alt_color.blue(), 80)
        )
        glow_pen_mid.setWidth(5)
        painter.setPen(glow_pen_mid)
        painter.drawPath(path_top)
        painter.drawPath(path_bottom)

        # Capa Láser Central (Pura y Brillante)
        core_pen = QPen(main_color.lighter(150))
        core_pen.setWidth(2)
        painter.setPen(core_pen)
        painter.drawPath(path_top)
        painter.drawPath(path_bottom)

        # 6. Eje de Gravedad (Línea central pulsante)
        horizon_intensity = max(100, int(np.mean(np.abs(self.prev_waveform)) * 1500))
        horizon_intensity = min(255, horizon_intensity)

        center_grad = QLinearGradient(0, 0, self.width, 0)
        center_grad.setColorAt(0.0, Qt.transparent)
        center_grad.setColorAt(0.5, QColor(255, 255, 255, horizon_intensity))
        center_grad.setColorAt(1.0, Qt.transparent)

        painter.setPen(QPen(QBrush(center_grad), 1))
        painter.drawLine(0, int(center_y), self.width, int(center_y))
