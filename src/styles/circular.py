from __future__ import annotations
import numpy as np
import math
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QRadialGradient
from PySide6.QtCore import Qt, QPointF
from visualizer import BaseVisualizer


class CircularSpectrum(BaseVisualizer):
    """Espectro circular de alto impacto con barras superiores dinámicas."""

    def __init__(self):
        """Inicializa el visualizador con inercia de movimiento."""
        super().__init__("Circular Spectrum")
        self.num_bands = 64
        self.min_radius = 80
        self.bar_width = 3
        self.smoothed_bass = 0.0
        
        # Estado para la fluidez (Smoothing)
        self.prev_bar_lengths = np.zeros(self.num_bands)
        self.smoothing_factor = 0.2
        
        # --- NUEVO: Estado para la animación de reposo de las barras superiores ---
        self.idle_phase = 0.0
        # Definimos cuántas barras cerca de la cima (índice 0) se verán afectadas
        self.top_bars_count = 10 
        
        # Effects State
        self.shockwaves = []

    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        """Renderizado con fluidez de acero y rotación eliminada."""
        if self.theme is None:
            return

        painter.setRenderHint(QPainter.Antialiasing, True)

        # --- NUEVO: Actualizar fase de animación de reposo ---
        # Esto crea un movimiento ondulatorio lento y constante
        self.idle_phase += 0.04

        # Layout
        center_x = self.width / 2
        center_y = self.height / 2
        max_radius = min(self.width, self.height) / 2 - 20
        bar_zone = max_radius - self.min_radius

        # ──────────────── Análisis de Frecuencias (Voz) ────────────────
        n_fft = len(fft_data)
        effective_n = int(n_fft * 0.25)

        log_indices = np.logspace(
            np.log10(2), np.log10(effective_n), self.num_bands + 1
        ).astype(int)

        magnitudes = np.empty(self.num_bands, dtype=np.float64)
        for i in range(self.num_bands):
            lo = log_indices[i]
            hi = max(lo + 1, log_indices[i + 1])
            if lo < n_fft:
                magnitudes[i] = np.mean(fft_data[lo : min(hi, n_fft)])
            else:
                magnitudes[i] = 0.0

        # ──────────────── Boost y Curva de Poder ────────────────
        bass_end = self.num_bands // 4
        mids_end = int(self.num_bands * 0.6)

        boost = np.ones(self.num_bands, dtype=np.float64)
        # Aumentamos ligeramente el boost inicial de los graves
        boost[:bass_end] = 1.8 
        boost[bass_end:mids_end] = 3.5
        boost[mids_end:] = 5.5

        magnitudes = magnitudes * boost
        # Usamos una curva de potencia ligeramente más agresiva para los graves
        magnitudes[:bass_end] = np.power(np.clip(magnitudes[:bass_end], 0.0, None), 0.45)
        magnitudes[bass_end:] = np.power(np.clip(magnitudes[bass_end:], 0.0, None), 0.5)

        # ──────────────── NUEVO: Micro-Dinámica para Barras Superiores ────────────────
        # Inyectamos vida artificial solo si el audio real es muy bajo en esa zona.
        for i in range(self.top_bars_count):
            # 1. Crear una oscilación suave basada en el tiempo y el índice (para que no se muevan igual)
            # El seno genera un valor entre -1 y 1, lo ajustamos a 0.0 - 1.0
            oscillation = (math.sin(self.idle_phase + i * 0.5) * 0.5) + 0.5
            
            # 2. Definir la "magnitud de reposo" que queremos añadir (aprox. 15% del tamaño máximo)
            idle_magnitude = oscillation * 0.15
            
            # 3. Mezcla inteligente: Si la magnitud real es baja (< 0.25), aplicamos la oscilación.
            # Si el audio real sube, la oscilación desaparece para no ensuciar la señal real.
            threshold = 0.25
            if magnitudes[i] < threshold:
                # Factor de mezcla: 1.0 si magnitud es 0, disminuye a 0.0 si magnitud llega al umbral
                blend_factor = 1.0 - (magnitudes[i] / threshold)
                magnitudes[i] += idle_magnitude * blend_factor

        # ──────────────── Suavizado de Barras (Fluidity) ────────────────
        target_lengths = magnitudes * bar_zone * 45.0
        # El suavizado se aplica DESPUÉS de la micro-dinámica para que el movimiento sea elegante
        current_bar_lengths = (target_lengths * self.smoothing_factor) + (self.prev_bar_lengths * (1.0 - self.smoothing_factor))
        self.prev_bar_lengths = current_bar_lengths
        
        bar_lengths = np.clip(current_bar_lengths, 3.0, bar_zone)

        # ──────────────── Energía de Impacto (Shockwaves) ────────────────
        bass_energy = float(np.mean(magnitudes[: max(1, bass_end)]))

        if bass_energy > 0.3 and (bass_energy - self.smoothed_bass) > 0.05:
            if not self.shockwaves or self.shockwaves[-1][0] > self.min_radius + 30:
                self.shockwaves.append([self.min_radius, 1.0])

        self.smoothed_bass += (bass_energy - self.smoothed_bass) * 0.25
        pulse_offset = min(self.smoothed_bass * 60.0, 25.0)
        current_inner_r = self.min_radius + pulse_offset

        # ──────────────── Renderizado de Ondas de Choque ────────────────
        painter.setBrush(Qt.NoBrush)
        new_shockwaves = []
        for r, opacity in self.shockwaves:
            r += 2.0 + (self.smoothed_bass * 5.0)
            opacity -= 0.015

            if opacity > 0.0 and r < max_radius:
                color = self.theme.get_color(0.2)
                wave_color = QColor(color)
                wave_color.setAlphaF(opacity * 0.4)
                pen = QPen(wave_color)
                pen.setWidthF(4.0)
                painter.setPen(pen)
                painter.drawEllipse(QPointF(center_x, center_y), r, r)
                new_shockwaves.append([r, opacity])
        self.shockwaves = new_shockwaves

        # ──────────────── Renderizado de Barras (Estáticas) ────────────────
        half_sweep = 180.0
        angle_step = half_sweep / self.num_bands

        for i in range(self.num_bands):
            mag = bar_lengths[i]
            color_pos = i / self.num_bands
            color = self.theme.get_gradient_color(color_pos)

            w = max(2, int(self.bar_width + (1.0 - color_pos) * 3))

            angle_right = i * angle_step
            angle_left = 360.0 - angle_right

            for angle_deg in (angle_right, angle_left):
                angle_rad = math.radians(angle_deg - 90) # 0° es la parte superior
                cos_a = math.cos(angle_rad)
                sin_a = math.sin(angle_rad)

                sx = center_x + cos_a * current_inner_r
                sy = center_y + sin_a * current_inner_r
                ex = center_x + cos_a * (current_inner_r + mag)
                ey = center_y + sin_a * (current_inner_r + mag)

                start_pt = QPointF(sx, sy)
                end_pt = QPointF(ex, ey)

                # Glow halo
                glow_color = QColor(color)
                glow_color.setAlpha(50)
                glow_pen = QPen(glow_color)
                glow_pen.setWidthF(w * 3.0)
                glow_pen.setCapStyle(Qt.RoundCap)
                painter.setPen(glow_pen)
                painter.drawLine(start_pt, end_pt)

                # Core bar
                pen = QPen(color)
                pen.setWidthF(w)
                pen.setCapStyle(Qt.RoundCap)
                painter.setPen(pen)
                painter.drawLine(start_pt, end_pt)

        # ──────────────── Centro Reactivo ────────────────
        center_r = current_inner_r - 8
        core_color = self.theme.get_color(0)

        gradient = QRadialGradient(QPointF(center_x, center_y), center_r)
        inner_color = QColor(core_color)
        inner_color.setAlpha(140)
        gradient.setColorAt(0.0, inner_color)

        mid_color = QColor(core_color)
        mid_color.setAlpha(70)
        gradient.setColorAt(0.6, mid_color)

        edge_color = QColor(core_color)
        edge_color.setAlpha(0)
        gradient.setColorAt(1.0, edge_color)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(center_x, center_y), center_r, center_r)

        ring_color = QColor(core_color)
        ring_color.setAlpha(100)
        ring_pen = QPen(ring_color)
        ring_pen.setWidthF(1.5)
        painter.setPen(ring_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(
            QPointF(center_x, center_y), current_inner_r, current_inner_r
        )