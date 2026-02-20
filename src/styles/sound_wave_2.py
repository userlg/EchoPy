from __future__ import annotations
import numpy as np
from PySide6.QtGui import QPainter, QBrush, QColor, QLinearGradient
from PySide6.QtCore import Qt, QRectF
from visualizer import BaseVisualizer


class SoundWave2(BaseVisualizer):
    """
    Un visualizador moderno y estilizado basado en barras simétricas sólidas,
    con puntas redondeadas y un rebaje suave del centro a los bordes.
    Idóneo para fondos minimalistas y amplios.
    """

    def __init__(self):
        super().__init__("Sound Wave 2")
        self.bar_count = 120  # Número total de barras en la onda
        self.bar_gap_ratio = (
            0.4  # Proporción del ancho que toma el espacio respecto a la barra
        )
        self.smoothed_magnitudes = np.zeros(self.bar_count // 2, dtype=np.float64)

    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        if self.theme is None or fft_data is None:
            return

        painter.setRenderHint(QPainter.Antialiasing, True)

        center_x = self.width / 2
        center_y = self.height / 2

        # Expansión al 98% de la pantalla para inmersión total
        usable_width = self.width * 0.98

        # Calcular ancho individual con margen interno
        total_bar_space = usable_width / self.bar_count
        bar_width = total_bar_space * (1 - self.bar_gap_ratio)
        bar_width = max(3.0, bar_width)  # Ancho mínimo más grueso para mayor modernidad

        # Rango útil del FFT: ignorar las frecuencias de agudos inaudibles (reducimos al 30%)
        n_fft = len(fft_data)
        effective_fft = int(n_fft * 0.3)

        half_bars = self.bar_count // 2

        # Mantenemos el array suavizado en sincronía con el tamaño si eventualmente cambia
        if len(self.smoothed_magnitudes) != half_bars:
            self.smoothed_magnitudes = np.zeros(half_bars, dtype=np.float64)

        # Creamos posiciones de lectura logarítmicas para extraer graves al principio y medios-agudos al final
        log_indices = np.logspace(
            np.log10(1), np.log10(max(1, effective_fft - 1)), half_bars
        ).astype(int)

        raw_magnitudes = np.zeros(half_bars, dtype=np.float64)
        for i in range(half_bars):
            lo = log_indices[i]
            hi = max(lo + 1, min(effective_fft, log_indices[i] + 2))
            raw_magnitudes[i] = np.mean(fft_data[lo:hi]) if lo < effective_fft else 0.0

        # Suavizado asimétrico por bin (Sube rápido, baja líquido y lento)
        for i in range(half_bars):
            target = raw_magnitudes[i]
            current = self.smoothed_magnitudes[i]
            if target > current:
                self.smoothed_magnitudes[i] += (
                    target - current
                ) * 0.85  # Ataque casi instantáneo
            else:
                self.smoothed_magnitudes[i] += (
                    target - current
                ) * 0.08  # Caída muy sedosa y líquida

        # Multiplicador de escala global masivo para dominar la pantalla
        scale_factor = self.height * 1.5

        # Atenuación gaussiana forzosa desde el centro hacia los bordes
        x_lin = np.linspace(0, 1, half_bars)
        # Forma de campana muy ancha, cayendo solo levemente en las puntas extremas
        envelope = np.exp(-1.2 * (x_lin) ** 2)

        # Aplicar el multiplicador global
        magnitudes = self.smoothed_magnitudes * scale_factor * envelope

        # Super boost a las magnitudes, elevación a la potencia de 0.65 hace que las frecuencias
        # débiles resalten mucho más, dándole armonía constante al espectro vacío.
        magnitudes = np.clip(np.power(magnitudes, 0.65) * 45.0, 8.0, self.height * 0.95)

        # Construcción de la onda espejo completa
        # Lado izquierdo (frecuencias altas cayendo en el borde -> graves al medio)
        left_side = magnitudes[::-1]
        # Lado derecho (graves al medio -> frecuencias altas borde derecho)
        right_side = magnitudes

        full_wave = np.concatenate((left_side, right_side))

        # Posicionamiento inicial en X para centrar
        start_x = center_x - (usable_width / 2)

        # Determinamos el color predominante
        base_color = self.theme.get_color(1)

        # Gradiente base hiper-brillante característico
        brush_gradient = QLinearGradient(
            0, center_y - (self.height / 2.5), 0, center_y + (self.height / 2.5)
        )
        fill_c = QColor(255, 255, 255, 255)
        border_c = QColor(255, 255, 255, 120)

        brush_gradient.setColorAt(0.0, border_c)
        brush_gradient.setColorAt(0.2, fill_c)
        brush_gradient.setColorAt(0.5, QColor(255, 255, 255, 255))
        brush_gradient.setColorAt(0.8, fill_c)
        brush_gradient.setColorAt(1.0, border_c)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(brush_gradient))

        for i in range(self.bar_count):
            h = full_wave[i]

            # Dibujo de la barra
            # Se centra horizontalmente según el iterador y verticalmente (`center_y - h/2`)
            bx = (
                start_x
                + (i * total_bar_space)
                + (total_bar_space * self.bar_gap_ratio / 2)
            )
            by = center_y - (h / 2)

            # Puntas ultra redondeadas calculadas en base al ancho
            radius = bar_width / 2

            painter.drawRoundedRect(QRectF(bx, by, bar_width, h), radius, radius)

            # Sutil Glow exterior blanco detrás de las frecuencias potentes (centro)
            if h > 30:
                glow_color = QColor(base_color)
                glow_intensity = min(60, int((h / self.height) * 150))
                glow_color.setAlpha(glow_intensity)
                painter.setBrush(QBrush(glow_color))
                painter.drawRoundedRect(
                    QRectF(bx - 2, by - 2, bar_width + 4, h + 4), radius + 2, radius + 2
                )
                # Restaurar brush normal para el núcleo
                painter.setBrush(QBrush(brush_gradient))
