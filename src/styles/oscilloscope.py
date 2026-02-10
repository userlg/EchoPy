from __future__ import annotations
import numpy as np
import random
from PySide6.QtGui import QPainter, QPen, QPainterPath, QColor, QRadialGradient, QBrush
from PySide6.QtCore import Qt, QPointF
from visualizer import BaseVisualizer

class Oscilloscope(BaseVisualizer):
    """Oscilloscope with high-impact kinetic energy and cinematic glow."""
    
    def __init__(self):
        super().__init__("Oscilloscope")
        self.line_width = 3
        self.flicker_intensity = 0.0
        self.glitch_timer = 0
    
    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        if self.theme is None or len(waveform) < 2:
            return
            
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # 1. Análisis de Impacto (Energía de la Voz)
        avg_energy = np.mean(np.abs(waveform))
        # Detectamos picos para generar un "parpadeo" de poder
        if avg_energy > 0.4:
            self.flicker_intensity = min(1.0, self.flicker_intensity + 0.2)
        else:
            self.flicker_intensity *= 0.8

        center_x = self.width / 2
        center_y = self.height / 2

        # 2. Retícula de Enfoque (Sutil y Cinematográfica)
        # En lugar de una cuadrícula de laboratorio, usamos una cruz de precisión
        grid_color = QColor(self.theme.get_color(0))
        grid_color.setAlpha(40)
        painter.setPen(QPen(grid_color, 1))
        
        # Círculos de enfoque concéntricos
        for r_factor in [0.2, 0.4, 0.6]:
            r = min(self.width, self.height) * r_factor
            painter.drawEllipse(QPointF(center_x, center_y), r, r)

        painter.drawLine(0, int(center_y), self.width, int(center_y))
        painter.drawLine(int(center_x), 0, int(center_x), self.height)

        # 3. Construcción del Núcleo de Energía (Lissajous Dinámico)
        num_points = 600 # Menos puntos pero más gruesos para impacto visual
        step = max(1, len(waveform) // num_points)
        
        path = QPainterPath()
        
        # El tamaño del trazado aumenta con la fuerza de la voz
        dynamic_scale = (min(self.width, self.height) * 0.4) * (1.0 + avg_energy * 2.0)
        
        for i in range(num_points):
            idx = i * step
            if idx >= len(waveform): break
            
            # X: Forma de onda original
            x_val = waveform[idx]
            # Y: Desfase dinámico (crea esa forma de "nudo" o "energía sagrada")
            y_idx = (idx + len(waveform) // 3) % len(waveform)
            y_val = waveform[y_idx]
            
            # Añadir un ligero "jitter" o temblor si la energía es alta
            jitter = (random.uniform(-5, 5) * self.flicker_intensity) if self.flicker_intensity > 0.5 else 0
            
            x = center_x + x_val * dynamic_scale + jitter
            y = center_y + y_val * dynamic_scale + jitter
            
            if i == 0: path.moveTo(x, y)
            else: path.lineTo(x, y)

        # 4. Renderizado de "Rastro de Gloria" (Glow y Trace)
        main_color = self.theme.get_color(0)
        
        # Efecto de resplandor expansivo (Halo)
        glow_color = QColor(main_color)
        glow_color.setAlpha(int(60 * self.flicker_intensity + 20))
        painter.setPen(QPen(glow_color, self.line_width + 12, Qt.SolidLine, Qt.RoundCap))
        painter.drawPath(path)
        
        # Trazado principal (Núcleo sólido)
        core_color = QColor(main_color)
        if self.flicker_intensity > 0.7:
            core_color = core_color.lighter(150) # El núcleo se vuelve blanco con la intensidad
            
        painter.setPen(QPen(core_color, self.line_width, Qt.SolidLine, Qt.RoundCap))
        painter.drawPath(path)

        # 5. Efecto de Escaneo de "Sabiduría Antigua"
        # Un barrido vertical sutil que recuerda a los monitores CRT clásicos
        scanline_y = (self.glitch_timer % 100) / 100.0 * self.height
        self.glitch_timer += 2
        
        scan_color = QColor(255, 255, 255, 30)
        painter.setPen(QPen(scan_color, 2))
        painter.drawLine(0, int(scanline_y), self.width, int(scanline_y))
        
        # Viñeta para centrar la atención
        vignette = QRadialGradient(QPointF(center_x, center_y), self.width * 0.7)
        vignette.setColorAt(0, Qt.transparent)
        vignette.setColorAt(1, QColor(0, 0, 0, 150))
        painter.setBrush(QBrush(vignette))
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, self.width, self.height)