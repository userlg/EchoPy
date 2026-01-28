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
from ui.overlay import DebugOverlay


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
    """Widget that renders visualizations with dynamic behavior."""
    
    # --- Smart State Manager Configuration ---
    # Now using RMS Activity Level (post-noise floor) for absolute stability
    # Sensitivity calibrated for low-volume system audio (e.g. YouTube at 30%)
    RAW_THRESHOLD_ON = 0.0008  # RMS Wake up (8e-4) - CLEAN SIGNAL
    RAW_THRESHOLD_OFF = 0.0004 # RMS Sleep floor
    SILENCE_TIMEOUT = 45       # ~0.75s of silence before sleeping
    
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
        
        # Audio analysis state
        self.current_max_peak = 0.0
        self.activity_level = 0.0 # Smoothed activity level (post-RMS)
        self.is_silent = True
        self._silence_frame_counter = 0 # For hysteresis
        
        # Theme
        self.current_theme = get_theme("modern")
        
        # Background image
        self.background_image: Optional[QPixmap] = None
        self.background_opacity = 0.3
        
        # Debug / Overlay
        self.debug_overlay = DebugOverlay(self)
        
        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update)
        self.animation_timer.start(16)  # 60 FPS
        
    def set_visualizer(self, visualizer: BaseVisualizer):
        """Set the active visualizer."""
        self.visualizer = visualizer
        if self.visualizer:
            self.visualizer.set_theme(self.current_theme)
            self.visualizer.set_theme(self.current_theme)
            self.visualizer.set_size(self.width(), self.height())
            logger.debug(f"Visualizer configured: {self.visualizer.name}")
        self.update()
    
    def set_theme(self, theme: ColorTheme):
        self.current_theme = theme
        if self.visualizer:
            self.visualizer.set_theme(theme)
    
    def set_background_image(self, pixmap: Optional[QPixmap]):
        self.background_image = pixmap
    
    def set_background_opacity(self, opacity: float):
        self.background_opacity = max(0.0, min(1.0, opacity))
    
    def set_show_fps(self, show: bool):
        self.debug_overlay.visible = show
        self.update()
    
    def update_audio_data(self, waveform: np.ndarray, fft_data: np.ndarray, activity_signal: float):
        """
        Update audio data with RMS Temporal Hysteresis.
        activity_signal is the RMS of the 'cleaned' audio.
        """
        self._update_activity_metrics(activity_signal, waveform)
        self._update_state_machine()
        self._update_internal_buffers(waveform, fft_data)
        self._handle_debug_logging(waveform)

    def _update_activity_metrics(self, activity_signal: float, waveform: np.ndarray):
        """Calculate and smooth activity metrics."""
        alpha = 0.15 # Sensitivity factor
        self.activity_level = ((1.0 - alpha) * self.activity_level) + (alpha * activity_signal)
        self.current_max_peak = np.max(np.abs(waveform)) if len(waveform) > 0 else 0.0

    def _update_state_machine(self):
        """Update the visualizer's active/silent state."""
        if self.is_silent:
            if self.activity_level > self.RAW_THRESHOLD_ON:
                self.is_silent = False
                self._silence_frame_counter = 0
                if not self.animation_timer.isActive():
                    self.animation_timer.start(16)
                    logger.debug(f"Visualizer WAKING UP (Activity: {self.activity_level:.6f})")
        else:
            if self.activity_level < self.RAW_THRESHOLD_OFF:
                self._silence_frame_counter += 1
                if self._silence_frame_counter > self.SILENCE_TIMEOUT:
                    self.is_silent = True
                    self.animation_timer.stop()
                    logger.debug("Visualizer SLEEPING (Dynamic Idling)")
                    self.update() # Clear screen
            else:
                self._silence_frame_counter = 0

    def _update_internal_buffers(self, waveform: np.ndarray, fft_data: np.ndarray):
        """Update data buffers based on current state."""
        if not self.is_silent:
            self.waveform = waveform
            self.fft_data = fft_data
        else:
            self.waveform.fill(0.0)
            self.fft_data.fill(0.0)

    def _handle_debug_logging(self, waveform: np.ndarray):
        """Log diagnostic information periodically."""
        if not hasattr(self, '_debug_print_counter'):
            self._debug_print_counter = 0
            
        self._debug_print_counter += 1
        if self._debug_print_counter >= 60:
            self._debug_print_counter = 0
            status = "SILENCE" if self.is_silent else "ACTIVE"
            logger.debug(f"DIAG | Status: {status} | Peak: {self.current_max_peak:.3f} | Activity(RMS): {self.activity_level:.6f}")

        
    def paintEvent(self, event):
        """Paint event handler."""
        painter = QPainter(self)
        # Disable Antialiasing for performance (Waveform line is too complex)
        # painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 1. Draw Background
        self._draw_background(painter)
        
        # 2. Draw Visualization
        if self.visualizer:
            # If silent, we are passing zeroed arrays (set in update_audio_data)
            # so the visualizer will naturally render "stopped" state.
            self.visualizer.render(painter, self.waveform, self.fft_data)
        else:
            self._draw_no_visualizer_message(painter)
        
        # 3. Draw Overlays (via DebugOverlay class - Refactoring step)
        self.debug_overlay.render(
            painter, 
            self.width(), 
            self.height(), 
            self.visualizer,
            self.current_max_peak,
            self.is_silent
        )
        
        # Update frame count in overlay
        self.debug_overlay.increment_frame()
    
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

    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        if self.visualizer:
            self.visualizer.set_size(self.width(), self.height())
    
    def get_fps(self) -> int:
        """Get current FPS."""
        return self.debug_overlay.fps
