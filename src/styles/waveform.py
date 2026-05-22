from __future__ import annotations
import numpy as np
import random
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QLinearGradient, QPainterPath
from PySide6.QtCore import Qt, QPointF, QRectF
from visualizer import BaseVisualizer


class Waveform(BaseVisualizer):
    """Enhanced oscilloscope waveform with gridlines, scanning laser, and peak sparks."""

    def __init__(self):
        super().__init__("Waveform")
        self.line_width = 3
        self.prev_waveform = None
        self.smoothing = 0.05
        self.scanline_y = 0.0
        self.particles = []
        self.max_particles = 120

    def set_size(self, width: int, height: int):
        super().set_size(width, height)
        self.particles = []

    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        if self.theme is None or len(waveform) == 0:
            return

        painter.setRenderHint(QPainter.Antialiasing, True)

        center_y = self.height / 2
        amplitude = self.height * 0.45

        # 1. Draw Oscilloscope Coordinates Grid (Background)
        grid_color = self.theme.get_color(1)
        grid_color.setAlpha(18)
        grid_pen = QPen(QBrush(grid_color), 0.9)
        painter.setPen(grid_pen)
        painter.setBrush(Qt.NoBrush)

        grid_cols = 16
        col_w = self.width / grid_cols
        for col in range(1, grid_cols):
            x = col * col_w
            painter.drawLine(int(x), 0, int(x), self.height)

        grid_rows = 12
        row_h = self.height / grid_rows
        for row in range(1, grid_rows):
            y = row * row_h
            painter.drawLine(0, int(y), self.width, int(y))

        # 2. Moving Laser Scanline Overlay
        self.scanline_y += 1.6
        if self.scanline_y > self.height:
            self.scanline_y = 0.0
        
        scan_col = self.theme.get_color(0)
        scan_col.setAlpha(25)
        painter.fillRect(QRectF(0, self.scanline_y - 2, self.width, 4), QBrush(scan_col))

        # 3. Waveform Smoothing
        if self.prev_waveform is None or len(self.prev_waveform) != len(waveform):
            self.prev_waveform = np.array(waveform)
        else:
            self.prev_waveform = (waveform * (1.0 - self.smoothing)) + (
                self.prev_waveform * self.smoothing
            )

        # Subsampling for Bezier Curve points
        num_points = 80
        step = max(1, len(self.prev_waveform) // num_points)

        path_top = QPainterPath()
        path_bottom = QPainterPath()

        main_color = self.theme.get_color(0)
        alt_color = self.theme.get_color(1)

        points = []
        for i in range(0, len(self.prev_waveform), step):
            sample = self.prev_waveform[i]
            val = np.tanh(sample * 1.5)  # Soft clipping
            x = (i / len(self.prev_waveform)) * self.width
            y_offset = val * amplitude
            points.append((x, y_offset))

            # Spawn reactive electron sparks on high amplitude peaks
            if abs(val) > 0.38 and len(self.particles) < self.max_particles and random.random() < 0.16:
                py = center_y - y_offset if val > 0 else center_y + y_offset
                self.particles.append({
                    "x": x,
                    "y": py,
                    "vx": random.uniform(-0.5, 0.5),
                    "vy": random.uniform(-1.5, -3.2) if val > 0 else random.uniform(1.5, 3.2),
                    "alpha": 1.0,
                    "size": random.uniform(1.2, 2.8),
                    "color": main_color if val > 0 else alt_color
                })

        if not points:
            return
        points[0] = (0, 0)
        points[-1] = (self.width, 0)

        # 4. Construct Bezier Paths
        path_top.moveTo(points[0][0], center_y - points[0][1])
        path_bottom.moveTo(points[0][0], center_y + points[0][1])

        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            cp_x = (x1 + x2) / 2

            path_top.cubicTo(
                QPointF(cp_x, center_y - y1),
                QPointF(cp_x, center_y - y2),
                QPointF(x2, center_y - y2),
            )
            path_bottom.cubicTo(
                QPointF(cp_x, center_y + y1),
                QPointF(cp_x, center_y + y2),
                QPointF(x2, center_y + y2),
            )

        # 5. Render Glowing Energy Aura Fill
        fill_path = QPainterPath(path_top)
        fill_path.connectPath(path_bottom.toReversed())
        fill_path.closeSubpath()

        grad_fill = QLinearGradient(0, center_y - amplitude, 0, center_y + amplitude)
        c_core = QColor(main_color)
        c_core.setAlpha(150)
        c_fade = QColor(alt_color)
        c_fade.setAlpha(0)

        grad_fill.setColorAt(0.0, c_fade)
        grad_fill.setColorAt(0.5, c_core)
        grad_fill.setColorAt(1.0, c_fade)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(grad_fill))
        painter.drawPath(fill_path)

        # 6. Laser Glow Layers (Coherent neon design)
        # Capa Wide Glow
        glow_pen_wide = QPen(
            QBrush(QColor(main_color.red(), main_color.green(), main_color.blue(), 25)), 12.0
        )
        glow_pen_wide.setCapStyle(Qt.RoundCap)
        painter.setPen(glow_pen_wide)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path_top)
        painter.drawPath(path_bottom)

        # Capa Mid Glow
        glow_pen_mid = QPen(
            QBrush(QColor(alt_color.red(), alt_color.green(), alt_color.blue(), 75)), 5.0
        )
        painter.setPen(glow_pen_mid)
        painter.drawPath(path_top)
        painter.drawPath(path_bottom)

        # Capa Laser Core
        core_pen = QPen(QBrush(main_color.lighter(140)), 1.8)
        painter.setPen(core_pen)
        painter.drawPath(path_top)
        painter.drawPath(path_bottom)

        # 7. Axis Line (Pulsing Center Line)
        horizon_intensity = max(100, int(np.mean(np.abs(self.prev_waveform)) * 1400))
        horizon_intensity = min(235, horizon_intensity)

        center_grad = QLinearGradient(0, 0, self.width, 0)
        center_grad.setColorAt(0.0, Qt.transparent)
        center_grad.setColorAt(0.5, QColor(255, 255, 255, horizon_intensity))
        center_grad.setColorAt(1.0, Qt.transparent)

        painter.setPen(QPen(QBrush(center_grad), 1.0))
        painter.drawLine(0, int(center_y), self.width, int(center_y))

        # 8. Update and Draw Sparks
        active_particles = []
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["alpha"] -= 0.022
            if p["alpha"] > 0 and 0 < p["y"] < self.height:
                p_col = QColor(p["color"])
                p_col.setAlphaF(p["alpha"] * 0.8)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(p_col))
                painter.drawEllipse(QPointF(p["x"], p["y"]), p["size"], p["size"])
                active_particles.append(p)
        self.particles = active_particles
