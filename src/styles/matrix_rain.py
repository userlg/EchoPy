from __future__ import annotations
import numpy as np
import random
import string
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QStaticText
from PySide6.QtCore import Qt
from visualizer import BaseVisualizer


class MatrixColumn:
    """Columna de caracteres con rastro dinámico y reactividad al impacto."""
    
    def __init__(self, x, height, speed):
        self.x = x
        self.y = random.randint(-height, 0)
        self.height = height
        self.speed = speed
        self.length = random.randint(15, 40) # Columnas más largas para más presencia
        self.chars = []
        self.glow_indices = [] # Caracteres que parpadean con "energía"
        self._generate_chars()
    
    def _generate_chars(self):
        """Genera caracteres crípticos (Mezcla de latín, símbolos y números)."""
        # Usamos caracteres que se ven más agresivos y menos 'tecnológicos'
        source = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789$#@&§ΔΩΨΣ"
        self.chars = [random.choice(source) for _ in range(self.length)]
        self.glow_indices = [random.randint(0, self.length-1) for _ in range(3)]
    
    def update(self, speed_multiplier=1.0, magnitude=0.0):
        """Actualiza posición y muta caracteres según la energía."""
        self.y += self.speed * speed_multiplier
        
        # Mutación aleatoria: la realidad es inestable ante una mente fuerte
        if random.random() < 0.1 * (1 + magnitude):
            idx = random.randint(0, self.length - 1)
            source = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789$#@&§ΔΩΨΣ"
            self.chars[idx] = random.choice(source)
            
        if self.y > self.height:
            self.y = random.randint(-self.height // 2, -10)
            self._generate_chars()


class MatrixRain(BaseVisualizer):
    """Lluvia de sabiduría con impacto cinético y resplandor vocal."""
    
    def __init__(self):
        super().__init__("Matrix Rain")
        self.columns = []
        self.char_size = 20 # Caracteres más grandes para mayor autoridad
        self.font = QFont("Consolas", self.char_size)
        self.font.setBold(True)
    
    def set_size(self, width: int, height: int):
        super().set_size(width, height)
        num_columns = width // (self.char_size - 4) # Mayor densidad
        self.columns = []
        for i in range(num_columns):
            x = i * (self.char_size - 4)
            speed = random.uniform(3, 12)
            self.columns.append(MatrixColumn(x, height, speed))
    
    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        if self.theme is None or not self.columns:
            return
        
        # 1. Análisis de Poder (Frecuencias de Autoridad)
        # Nos enfocamos en el rango medio-bajo donde la voz tiene más peso
        n_fft = len(fft_data)
        avg_magnitude = np.mean(fft_data[:int(n_fft * 0.2)]) if n_fft > 0 else 0
        
        # Efecto de sacudida: si la voz es muy fuerte, la lluvia se acelera drásticamente
        speed_multiplier = 1.0 + (avg_magnitude * 15.0)
        
        painter.setFont(self.font)
        
        for column in self.columns:
            column.update(speed_multiplier, avg_magnitude)
            
            for i, char in enumerate(column.chars):
                char_y = int(column.y + i * self.char_size)
                
                # Solo dibujamos si está en pantalla
                if -20 <= char_y <= self.height + 20:
                    # 2. Lógica de Color e Intensidad
                    dist_factor = 1.0 - (i / column.length) # 1.0 en la cabeza, 0.0 en la cola
                    
                    base_color = self.theme.get_color(0)
                    final_color = QColor(base_color)
                    
                    # El color se intensifica con la magnitud de la voz
                    if i == 0:
                        # La "cabeza" de la columna es blanca y cegadora
                        final_color = QColor(255, 255, 255)
                        if avg_magnitude > 0.3:
                            # Efecto Glow en la cabeza
                            final_color = final_color.lighter(200)
                    else:
                        # El rastro se desvanece
                        alpha = int(255 * dist_factor)
                        final_color.setAlpha(alpha)
                        
                        # Caracteres especiales que brillan aleatoriamente (Glitches de poder)
                        if i in column.glow_indices and avg_magnitude > 0.2:
                            final_color = QColor(255, 255, 255, 200)

                    # 3. Renderizado con Profundidad
                    # Si el carácter está "lejos" en el rastro, lo hacemos un poco más pequeño
                    if i > 5:
                        f = painter.font()
                        f.setPointSize(self.char_size - 2)
                        painter.setFont(f)
                    
                    painter.setPen(QPen(final_color))
                    painter.drawText(int(column.x), char_y, char)
                    
                    # Reset font size
                    painter.setFont(self.font)

        # 4. Flash de Impacto
        # Si hay un pico de voz, un destello cubre sutilmente la pantalla
        if avg_magnitude > 0.5:
            flash_color = QColor(255, 255, 255, int(avg_magnitude * 80))
            painter.fillRect(0, 0, self.width, self.height, flash_color)