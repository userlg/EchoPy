from __future__ import annotations
import numpy as np
import math
from PySide6.QtGui import QPainter, QPen, QColor, QRadialGradient, QBrush
from PySide6.QtCore import Qt, QPointF
from visualizer import BaseVisualizer


class FrequencyRings(BaseVisualizer):
    """Frequency rings transformed into explosive kinetic shockwaves."""
    
    def __init__(self):
        super().__init__("Frequency Rings")
        self.num_rings = 8 # Más anillos para mayor densidad visual
        self.ring_history = []
        self.max_history = 15 # Rastro más largo para una estela persistente
        self.expansion_speed = 1.8 # Velocidad de expansión agresiva
    
    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        if self.theme is None or fft_data is None or len(fft_data) == 0:
            return
        
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        center_x = self.width / 2
        center_y = self.height / 2
        
        # 1. Análisis Vocal (Enfoque en el núcleo de la voz: 20Hz - 4000Hz)
        n_fft = len(fft_data)
        useful_range = int(n_fft * 0.22)
        log_indices = np.logspace(np.log10(2), np.log10(useful_range), self.num_rings + 1)
        indices = log_indices.astype(int)
        
        current_magnitudes = []
        for i in range(self.num_rings):
            start_idx = indices[i]
            end_idx = indices[i+1]
            # Boost dinámico: Los anillos exteriores (agudos) necesitan más sensibilidad
            boost = 1.0 + (i / self.num_rings) * 2.5
            magnitude = np.mean(fft_data[start_idx:end_idx]) if start_idx < n_fft else 0
            current_magnitudes.append(np.power(magnitude * boost, 0.6)) # Curva de potencia para reactividad
        
        # Guardar en el historial para el efecto de onda
        self.ring_history.append(current_magnitudes)
        if len(self.ring_history) > self.max_history:
            self.ring_history.pop(0)
        
        max_radius = min(self.width, self.height) / 2
        
        # 2. Renderizado de las Ondas de Impacto
        for history_idx, magnitudes in enumerate(self.ring_history):
            # El "age" determina qué tan lejos ha viajado la onda desde el centro
            age = len(self.ring_history) - history_idx - 1
            alpha_factor = 1.0 - (age / self.max_history)
            
            for ring_idx, magnitude in enumerate(magnitudes):
                # Radio base + expansión por el tiempo + reacción al audio actual
                # Esto crea el efecto de que la voz "empuja" los anillos hacia afuera
                base_radius = (ring_idx / self.num_rings) * max_radius * 0.4
                expansion = age * (max_radius / self.max_history) * self.expansion_speed
                
                # Reacción elástica: solo los anillos más jóvenes reaccionan al impacto inmediato
                pulse = (magnitude * 350 * alpha_factor)
                radius = base_radius + expansion + pulse
                
                if radius > 10 and radius < max_radius * 1.2:
                    color_pos = ring_idx / self.num_rings
                    base_color = self.theme.get_gradient_color(color_pos)
                    
                    # --- EFECTO NEÓN CINEMÁTICO ---
                    # A. El Aura (Glow expansivo)
                    glow_color = QColor(base_color)
                    glow_color.setAlpha(int(alpha_factor * 50))
                    
                    glow_pen = QPen(glow_color)
                    # El ancho del brillo aumenta con la potencia del audio
                    glow_pen.setWidthF(4 + magnitude * 30)
                    painter.setPen(glow_pen)
                    painter.drawEllipse(QPointF(center_x, center_y), radius, radius)
                    
                    # B. El Núcleo (Línea sólida de energía)
                    core_color = QColor(base_color)
                    core_color.setAlpha(int(alpha_factor * 255))
                    
                    # Si el anillo es potente, el núcleo se vuelve blanco (incandescente)
                    if magnitude > 0.4 and age < 2:
                        core_color = QColor(255, 255, 255, int(alpha_factor * 255))
                    
                    core_pen = QPen(core_color)
                    core_pen.setWidthF(1.5 + magnitude * 3)
                    painter.setPen(core_pen)
                    painter.drawEllipse(QPointF(center_x, center_y), radius, radius)

        # 3. Núcleo Central de Poder
        # Un orbe sutil en el centro que pulsa con los graves
        bass_impact = current_magnitudes[0] if current_magnitudes else 0
        core_r = 30 + (bass_impact * 50)
        
        central_glow = QRadialGradient(QPointF(center_x, center_y), core_r)
        c_color = self.theme.get_color(0)
        c_color.setAlpha(int(bass_impact * 180))
        
        central_glow.setColorAt(0, c_color)
        central_glow.setColorAt(1, Qt.transparent)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(central_glow))
        painter.drawEllipse(QPointF(center_x, center_y), core_r, core_r)