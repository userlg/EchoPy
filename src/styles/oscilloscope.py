from __future__ import annotations
import numpy as np
from PySide6.QtGui import QPainter, QPen, QPainterPath, QColor, QRadialGradient, QBrush
from PySide6.QtCore import Qt, QPointF
from visualizer import BaseVisualizer

class Oscilloscope(BaseVisualizer):
    """Oscilloscope optimizado para máxima fluidez y rendimiento cinemático."""
    
    def __init__(self):
        super().__init__("Oscilloscope")
        self.line_width = 3
        self.flicker_intensity = 0.0
        self.glitch_timer = 0
        
        # Variables de suavizado (Smoothing)
        self.smooth_scale = 1.0
        self.smooth_flicker = 0.0
        self.interpolation_factor = 0.15 # Determina la inercia del movimiento

    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        if self.theme is None or len(waveform) < 2:
            return
            
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # 1. Procesamiento de Energía con Suavizado
        avg_energy = np.mean(np.abs(waveform))
        
        # Suavizado de la intensidad del parpadeo (flicker)
        target_flicker = min(1.0, self.flicker_intensity + 0.2) if avg_energy > 0.4 else self.flicker_intensity * 0.8
        self.smooth_flicker += (target_flicker - self.smooth_flicker) * self.interpolation_factor
        
        center_x = self.width / 2
        center_y = self.height / 2

        # 2. Retícula de Enfoque
        grid_color = QColor(self.theme.get_color(0))
        grid_color.setAlpha(40)
        painter.setPen(QPen(grid_color, 1))
        
        base_r = min(self.width, self.height)
        for r_factor in [0.2, 0.4, 0.6]:
            r = base_r * r_factor
            painter.drawEllipse(QPointF(center_x, center_y), r, r)

        painter.drawLine(0, int(center_y), self.width, int(center_y))
        painter.drawLine(int(center_x), 0, int(center_x), self.height)

        # 3. Construcción del Núcleo (Optimización NumPy)
        num_points = 500 # Un poco menos de puntos para mayor fluidez
        
        # Suavizado de la escala dinámica para evitar saltos
        target_scale = (base_r * 0.4) * (1.0 + avg_energy * 2.0)
        self.smooth_scale += (target_scale - self.smooth_scale) * self.interpolation_factor

        # Vectorización: Calculamos todos los índices y posiciones de una vez con NumPy
        indices = np.linspace(0, len(waveform) - 1, num_points).astype(int)
        x_vals = waveform[indices]
        
        y_indices = (indices + len(waveform) // 3) % len(waveform)
        y_vals = waveform[y_indices]
        
        # Generamos el Jitter (temblor) de forma masiva
        jitter_amount = 5 * self.smooth_flicker
        jitters = np.random.uniform(-jitter_amount, jitter_amount, (num_points, 2)) if jitter_amount > 0.1 else np.zeros((num_points, 2))

        # Coordenadas finales calculadas por NumPy (mucho más rápido que un bucle for)
        px = center_x + x_vals * self.smooth_scale + jitters[:, 0]
        py = center_y + y_vals * self.smooth_scale + jitters[:, 1]

        # Creación del Path (Aún requiere un bucle, pero sin cálculos matemáticos dentro)
        path = QPainterPath()
        path.moveTo(px[0], py[0])
        for i in range(1, num_points):
            path.lineTo(px[i], py[i])

        # 4. Renderizado de "Rastro de Gloria"
        main_color = self.theme.get_color(0)
        
        # Glow
        glow_color = QColor(main_color)
        glow_color.setAlpha(int(60 * self.smooth_flicker + 20))
        painter.setPen(QPen(glow_color, self.line_width + 10, Qt.SolidLine, Qt.RoundCap))
        painter.drawPath(path)
        
        # Núcleo
        core_color = QColor(main_color)
        if self.smooth_flicker > 0.6:
            core_color = core_color.lighter(140)
            
        painter.setPen(QPen(core_color, self.line_width, Qt.SolidLine, Qt.RoundCap))
        painter.drawPath(path)

        # 5. Efectos Finales (Scanline y Viñeta)
        self.glitch_timer += 2
        scanline_y = (self.glitch_timer % 100) / 100.0 * self.height
        
        scan_color = QColor(255, 255, 255, 25)
        painter.setPen(QPen(scan_color, 2))
        painter.drawLine(0, int(scanline_y), self.width, int(scanline_y))
        
        vignette = QRadialGradient(QPointF(center_x, center_y), self.width * 0.7)
        vignette.setColorAt(0, Qt.transparent)
        vignette.setColorAt(1, QColor(0, 0, 0, 160))
        painter.setBrush(QBrush(vignette))
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, self.width, self.height)