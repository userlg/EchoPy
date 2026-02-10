from __future__ import annotations
import numpy as np
from PySide6.QtGui import QPainter, QImage, QPixmap
from PySide6.QtCore import Qt
from visualizer import BaseVisualizer

class FireEffect(BaseVisualizer):
    """Fuego de alto rendimiento: Procesamiento paralelo mediante NumPy."""
    
    def __init__(self):
        super().__init__("Fire Effect")
        self.heat_map = None
        self.palette = None
        self.res_scale = 8  # Resolución optimizada para fluidez
        self.decay = 0.92
        self.vocal_boost = 60.0
        self.prev_theme_id = None

    def set_size(self, width: int, height: int):
        super().set_size(width, height)
        self.map_width = width // self.res_scale
        self.map_height = height // self.res_scale
        self.heat_map = np.zeros((self.map_height, self.map_width), dtype=np.float32)
        self._update_palette()

    def _update_palette(self):
        """Pre-calcula una paleta de 256 colores para evitar cálculos en cada frame."""
        if self.theme is None: return
        
        # Generamos 256 colores basados en el gradiente del tema
        self.palette = np.zeros((256, 4), dtype=np.uint8)
        for i in range(256):
            color = self.theme.get_gradient_color(i / 255.0)
            # Formato BGRA para QImage (Format_RGB32)
            self.palette[i] = [color.blue(), color.green(), color.red(), 255]

    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        if self.theme is None or self.heat_map is None:
            return
            
        # 1. PROPAGACIÓN ULTRA-RÁPIDA
        # Promediamos la fila de abajo y sus vecinos laterales de un solo golpe
        src = self.heat_map
        below = src[1:, :]
        # Promedio simple pero efectivo (Vectorizado)
        self.heat_map[:-1, :] = (below + np.roll(below, 1, axis=1) + np.roll(below, -1, axis=1)) / 3.01 * self.decay

        # 2. INYECCIÓN DE PODER (Voz)
        n_fft = len(fft_data)
        useful_bins = int(n_fft * 0.2)
        vocal_data = fft_data[:useful_range] if (useful_range := useful_bins) > 0 else []
        
        if len(vocal_data) > 0:
            # Redimensionamos el espectro para que coincida con el ancho del mapa de calor
            # Esto elimina el bucle 'for' de inyección
            xp = np.linspace(0, 1, len(vocal_data))
            x = np.linspace(0, 1, self.map_width)
            resampled_audio = np.interp(x, xp, vocal_data)
            
            # Inyectamos el calor en la base
            self.heat_map[-1, :] = np.clip(self.heat_map[-1, :] + resampled_audio * self.vocal_boost, 0, 1.0)

        # 3. CONVERSIÓN DE MEMORIA (El secreto de la fluidez)
        # Convertimos el mapa de calor (0-1) a índices de paleta (0-255)
        indices = (self.heat_map * 255).astype(np.uint8)
        
        # Mapeamos los índices a colores RGB usando la paleta pre-calculada
        # Esto sucede a nivel de C++, es instantáneo
        image_data = self.palette[indices]
        
        # Creamos la imagen directamente desde el buffer de memoria
        height, width, _ = image_data.shape
        image = QImage(image_data.data, width, height, QImage.Format_RGB32)
        
        # 4. RENDERIZADO FINAL
        # Escalamos con SmoothTransformation para un look orgánico y profesional
        pixmap = QPixmap.fromImage(image)
        painter.drawPixmap(0, 0, pixmap.scaled(self.width, self.height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))