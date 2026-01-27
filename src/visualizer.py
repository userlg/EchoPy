from __future__ import annotations
import numpy as np
from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from numpy import ndarray
from abc import ABC, abstractmethod
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPixmap, QPen, QBrush, QColor
from PySide6.QtCore import Qt, QTimer, QPointF
from typing import Optional
from themes import ColorTheme, get_theme
from utils import logger


class BaseVisualizer(ABC):
    """Abstract base class for all visualization styles."""
    
    def __init__(self, name: str):
        """
        Initialize visualizer.
        
        Args:
            name: Visualizer name
        """
        self.name = name
        self.theme: Optional[ColorTheme] = None
        self.width = 800
        self.height = 600
    
    def set_theme(self, theme: ColorTheme):
        """Set color theme."""
        self.theme = theme
    
    def set_size(self, width: int, height: int):
        """Set canvas size."""
        self.width = width
        self.height = height
    
    @abstractmethod
    def render(self, painter: QPainter, waveform: np.ndarray, fft_data: np.ndarray):
        """
        Render visualization.
        
        Args:
            painter: QPainter instance
            waveform: Time-domain waveform data
            fft_data: Frequency-domain FFT data
        """
        pass


class VisualizerWidget(QWidget):
    """Widget that renders visualizations."""
    
    def __init__(self, parent=None):
        """Initialize visualizer widget."""
        super().__init__(parent)
        
        # Set widget properties
        self.setMinimumSize(800, 600)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        
        # Current visualizer
        self.visualizer: Optional[BaseVisualizer] = None
        
        # Audio data
        self.waveform = np.zeros(2048, dtype=np.float32)
        self.fft_data = np.zeros(1024, dtype=np.float32)
        
        # Theme
        self.current_theme = get_theme("modern")
        
        # Background image
        self.background_image: Optional[QPixmap] = None
        self.background_opacity = 0.3
        
        # UI Options
        self.show_fps = True
        
        # FPS tracking
        self.fps = 0
        self.frame_count = 0
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self._update_fps)
        self.fps_timer.start(1000)
        
        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update)
        self.animation_timer.start(16)  # ~60 FPS
    
    def set_visualizer(self, visualizer: BaseVisualizer):
        """Set the active visualizer."""
        self.visualizer = visualizer
        if self.visualizer:
            self.visualizer.set_theme(self.current_theme)
            self.visualizer.set_size(self.width(), self.height())
            logger.debug(f"Visualizer configured: {self.visualizer.name}")
        # Force immediate update
        self.update()
    
    def set_theme(self, theme: ColorTheme):
        """Set color theme."""
        self.current_theme = theme
        if self.visualizer:
            self.visualizer.set_theme(theme)
    
    def set_background_image(self, pixmap: Optional[QPixmap]):
        """Set background image."""
        self.background_image = pixmap
    
    def set_background_opacity(self, opacity: float):
        """Set background image opacity (0.0 to 1.0)."""
        self.background_opacity = max(0.0, min(1.0, opacity))
    
    def set_show_fps(self, show: bool):
        """Toggle FPS counter visibility."""
        self.show_fps = show
        self.update()
    
    def update_audio_data(self, waveform: np.ndarray, fft_data: np.ndarray):
        """Update audio data from processor."""
        self.waveform = waveform
        self.fft_data = fft_data
        # Debug: Show when we receive data (only occasionally to avoid spam)
        if hasattr(self, '_debug_counter'):
            self._debug_counter += 1
        else:
            self._debug_counter = 0
        
        if self._debug_counter % 300 == 0:  # Print every 300 frames (~5 seconds)
            max_fft = np.max(fft_data) if len(fft_data) > 0 else 0
            logger.debug(f"Audio data received - FFT max: {max_fft:.4f}")
    
    def paintEvent(self, event):
        """Paint event handler."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 1. Draw Background
        self._draw_background(painter)
        
        # 2. Draw Visualization
        if self.visualizer:
            self.visualizer.render(painter, self.waveform, self.fft_data)
        else:
            self._draw_no_visualizer_message(painter)
        
        # 3. Draw Overlays (FPS, Stats)
        if self.show_fps:
            self._draw_debug_info(painter)
        
        # Update frame count
        self.frame_count += 1
    
    def _draw_background(self, painter: QPainter):
        """Draw widget background and image."""
        painter.fillRect(self.rect(), self.current_theme.bg_color)
        
        if self.background_image:
            painter.save()
            painter.setOpacity(self.background_opacity)
            
            scaled = self.background_image.scaled(
                self.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            painter.restore()

    def _draw_no_visualizer_message(self, painter: QPainter):
        """Draw message when no visualizer is active."""
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.drawText(self.rect(), Qt.AlignCenter, "No visualizer set")

    def _draw_debug_info(self, painter: QPainter):
        """Draw FPS and other debug information."""
        painter.setPen(QPen(self.current_theme.text_color))
        
        y_offset = 20
        painter.drawText(10, y_offset, f"FPS: {self.fps}")
        
        if self.visualizer:
            y_offset += 20
            painter.drawText(10, y_offset, f"Visualizer: {self.visualizer.name}")
        
        max_fft = np.max(self.fft_data) if len(self.fft_data) > 0 else 0
        y_offset += 20
        painter.drawText(10, y_offset, f"Audio Peak: {max_fft:.4f}")
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        if self.visualizer:
            self.visualizer.set_size(self.width(), self.height())
    
    def _update_fps(self):
        """Update FPS counter."""
        self.fps = self.frame_count
        self.frame_count = 0
    
    def get_fps(self) -> int:
        """Get current FPS."""
        return self.fps
