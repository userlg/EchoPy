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
        
        # 1. Suavizado Temporal (Inter-frame smoothing)
        if self.prev_waveform is None or len(self.prev_waveform) != len(waveform):
            self.prev_waveform = waveform
        else:
            waveform = (waveform * self.smoothing) + (self.prev_waveform * (1.0 - self.smoothing))
            self.prev_waveform = waveform

        # 2. Procesamiento de Puntos (Downsampling Inteligente)
        num_points = 250  # Suficiente para que se vea fluido pero no pesado
        step = max(1, len(waveform) // num_points)
        center_y = self.height / 2
        amplitude = self.height * 0.4  # Usar el 40% de la altura para cada lado
        
        # Creamos los paths para la parte superior e inferior (Efecto Espejo)
        path_top = QPainterPath()
        path_bottom = QPainterPath()
        
        first = True
        for i in range(0, len(waveform), step):
            sample = waveform[i]
            # Limitador y ganancia dinámica
            val = np.clip(sample * 0.4, -1.0, 1.0)
            
            x = (i / len(waveform)) * self.width
            y_offset = val * amplitude
            
            if first:
                path_top.moveTo(x, center_y - y_offset)
                path_bottom.moveTo(x, center_y + y_offset)
                first = False
            else:
                path_top.lineTo(x, center_y - y_offset)
                path_bottom.lineTo(x, center_y + y_offset)

        # 3. Renderizado de "Aura" (Relleno con gradiente)
        # Cerramos los paths para poder rellenarlos
        fill_path = QPainterPath(path_top)
        # Conectamos con el path inferior de forma invertida para cerrar la forma
        fill_path.connectPath(path_bottom.toReversed())
        fill_path.closeSubpath()

        # Gradiente de poder (del centro hacia los bordes)
        grad = QLinearGradient(0, center_y - amplitude, 0, center_y + amplitude)
        main_color = self.theme.get_color(0)
        
        c_glow = QColor(main_color)
        c_glow.setAlpha(120)
        c_fade = QColor(main_color)
        c_fade.setAlpha(0)

        grad.setColorAt(0.0, c_fade)
        grad.setColorAt(0.5, c_glow)
        grad.setColorAt(1.0, c_fade)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawPath(fill_path)

        # 4. Líneas de Contorno (Los "nervios" de la onda)
        # Brillo exterior
        glow_pen = QPen(QColor(main_color.red(), main_color.green(), main_color.blue(), 60))
        glow_pen.setWidth(8)
        painter.setPen(glow_pen)
        painter.drawPath(path_top)
        painter.drawPath(path_bottom)

        # Línea principal sólida
        core_pen = QPen(main_color)
        core_pen.setWidth(2)
        painter.setPen(core_pen)
        painter.drawPath(path_top)
        painter.drawPath(path_bottom)

        # 5. Núcleo Central (Línea de horizonte)
        # En lugar de una línea punteada simple, una línea con gradiente de opacidad
        center_grad = QLinearGradient(0, 0, self.width, 0)
        center_grad.setColorAt(0.0, Qt.transparent)
        center_grad.setColorAt(0.5, QColor(255, 255, 255, 100))
        center_grad.setColorAt(1.0, Qt.transparent)
        
        painter.setPen(QPen(QBrush(center_grad), 1))
        painter.drawLine(0, int(center_y), self.width, int(center_y))