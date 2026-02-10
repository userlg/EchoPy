from __future__ import annotations
import numpy as np
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QLinearGradient
from PySide6.QtCore import Qt, QPointF, QRectF
from visualizer import BaseVisualizer

class SpectrumBars(BaseVisualizer):
    """Spectrum analyzer with centered-out harmonious bars for high-impact visuals."""

    def __init__(self):
        super().__init__("Spectrum Bars")
        self.num_bars = 64
        self.bar_spacing = 3
        self.corner_radius = 4  # Estética moderna: bordes redondeados
        
        # Estado para suavizado (Smoothing)
        self.prev_magnitudes = np.zeros(self.num_bars)
        self.smoothing_factor = 0.25  # Menos es más fluido, más es más reactivo

        # Peak hold state
        self.peaks = np.zeros(self.num_bars, dtype=np.float64)
        self.peak_decay = 0.92
        self.peak_gravity = 0.005

    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        if self.theme is None:
            return

        painter.setRenderHint(QPainter.Antialiasing, True)

        # Layout
        total_width = self.width - (self.num_bars * self.bar_spacing)
        bar_width = total_width / self.num_bars
        baseline_y = self.height * 0.82  # Elevamos un poco para la reflexión

        n_fft = len(fft_data)

        # ──────────── Frequency Binning (Vocal Focus) ────────────
        # Nos enfocamos en el rango de 20Hz a ~5000Hz para máxima respuesta
        useful_bins = int(n_fft * 0.20) 
        log_indices = np.logspace(
            np.log10(2), np.log10(useful_bins), self.num_bars + 1
        ).astype(int)

        raw_magnitudes = np.empty(self.num_bars, dtype=np.float64)
        for i in range(self.num_bars):
            lo = log_indices[i]
            hi = max(lo + 1, log_indices[i + 1])
            raw_magnitudes[i] = np.mean(fft_data[lo : min(hi, n_fft)]) if lo < n_fft else 0.0

        # ──────────── Distribución Simétrica (Center-Out) ────────────
        # Mapeamos los graves al centro y los agudos a los extremos
        magnitudes = np.empty(self.num_bars)
        half = self.num_bars // 2
        
        for i in range(self.num_bars):
            # Calcula la distancia al centro para traer los graves al medio
            dist_from_center = abs(i - half)
            # Invertimos: el centro (dist 0) toma el índice 0 de raw_magnitudes (graves)
            magnitudes[i] = raw_magnitudes[dist_from_center]

        # ──────────── Procesamiento Estético ────────────
        # Boost dinámico: Agudos (ahora en los bordes) necesitan más ganancia visual
        edge_boost = np.linspace(2.5, 1.0, half)
        boost = np.concatenate([edge_boost, edge_boost[::-1]])
        
        magnitudes *= boost
        # Curva de potencia agresiva para que "floten"
        magnitudes = np.power(np.clip(magnitudes, 0.0, None), 0.5)
        
        # Suavizado temporal (Interpolación)
        magnitudes = (magnitudes * self.smoothing_factor) + (self.prev_magnitudes * (1.0 - self.smoothing_factor))
        self.prev_magnitudes = magnitudes

        # Actualizar Picos
        self.peaks = np.maximum(self.peaks * self.peak_decay - self.peak_gravity, magnitudes)

        # ──────────── Renderizado de Barras ────────────
        for i in range(self.num_bars):
            mag = magnitudes[i]
            peak = self.peaks[i]

            # Altura con piso estético (mínimo 5px)
            bar_height = max(5, mag * self.height * 0.9)
            bar_height = min(bar_height, self.height * 0.75)
            
            peak_height = max(bar_height, peak * self.height * 0.9)
            peak_height = min(peak_height, self.height * 0.75)

            x = i * (bar_width + self.bar_spacing)
            y_bar = baseline_y - bar_height
            y_peak = baseline_y - peak_height

            # Color dinámico basado en la posición (Armonía visual)
            color_pos = abs(i - half) / half # 0 en el centro, 1 en los bordes
            color = self.theme.get_gradient_color(color_pos)

            # 1. Reflexión Elegante
            reflection_h = bar_height * 0.35
            ref_grad = QLinearGradient(QPointF(x, baseline_y), QPointF(x, baseline_y + reflection_h))
            ref_col = QColor(color)
            ref_col.setAlpha(60)
            ref_grad.setColorAt(0.0, ref_col)
            ref_grad.setColorAt(1.0, Qt.transparent)
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(ref_grad))
            painter.drawRoundedRect(QRectF(x, baseline_y + 2, bar_width, reflection_h), self.corner_radius, self.corner_radius)

            # 2. Barra Principal con Degradado de Potencia
            bar_grad = QLinearGradient(QPointF(x, baseline_y), QPointF(x, y_bar))
            bar_grad.setColorAt(0.0, color.darker(150))
            bar_grad.setColorAt(0.4, color)
            bar_grad.setColorAt(1.0, color.lighter(140))

            painter.setBrush(QBrush(bar_grad))
            painter.drawRoundedRect(QRectF(x, y_bar, bar_width, bar_height), self.corner_radius, self.corner_radius)

            # 3. Glow Cap (Brillo en la punta)
            if mag > 0.1:
                glow_col = QColor(color.lighter(160))
                glow_col.setAlpha(120)
                painter.setBrush(QBrush(glow_col))
                painter.drawRoundedRect(QRectF(x, y_bar, bar_width, 6), self.corner_radius, self.corner_radius)

            # 4. Peak Dot (Puntos flotantes)
            if peak_height > bar_height + 4:
                p_col = QColor(color.lighter(180))
                p_col.setAlpha(int(255 * (peak_height / self.height)))
                painter.setBrush(QBrush(p_col))
                painter.drawRoundedRect(QRectF(x, y_peak - 3, bar_width, 3), 1, 1)