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
    # Calibrated for NOISE_FLOOR 0.00018
    THRESHOLD_ON = 0.01     # 1% volume to wake up (Sensible for soft intros)
    THRESHOLD_OFF = 0.005   # 0.5% volume to sleep
    SILENCE_TIMEOUT = 10    # Frames of silence before sleeping
    
    def __init__(self, parent=None):
        """Initialize visualizer widget."""
        super().__init__(parent)
        
        # ... (keep existing init code, but add silence counter)
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
        
    # ... (Keep setters as they are - no changes there)
    
    def set_visualizer(self, visualizer: BaseVisualizer):
        """Set the active visualizer."""
        self.visualizer = visualizer
        if self.visualizer:
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
    
    def update_audio_data(self, waveform: np.ndarray, fft_data: np.ndarray):
        """
        Update audio data with Smart State Detection (Hysteresis).
        """
        # 1. Measure Peak
        peak = 0.0
        if len(waveform) > 0:
            peak = np.max(np.abs(waveform))
        self.current_max_peak = peak
        
        # 2. State Machine Logic
        if self.is_silent:
            # WAKE UP LOGIC
            if peak > self.THRESHOLD_ON:
                self.is_silent = False
                self._silence_frame_counter = 0
        else:
            # SLEEP LOGIC
            if peak < self.THRESHOLD_OFF:
                self._silence_frame_counter += 1
                if self._silence_frame_counter > self.SILENCE_TIMEOUT:
                    self.is_silent = True
            else:
                self._silence_frame_counter = 0 # Reset if we see signal
        
        # 3. Data Processing
        if not self.is_silent:
            self.waveform = waveform
            self.fft_data = fft_data
        else:
            # Visual silence
            self.waveform.fill(0)
            self.fft_data.fill(0)

        # DEBUG: Print stats to console for analysis
        if not hasattr(self, '_debug_print_counter'):
            self._debug_print_counter = 0
        
        self._debug_print_counter += 1
        # Print every ~60 updates (approx 1 sec if running at 60fps)
        if self._debug_print_counter >= 60:
            self._debug_print_counter = 0
            mode_name = self.visualizer.name if self.visualizer else "None"
            fps_count = self.debug_overlay.fps
            print(f"STATS | FPS: {fps_count} | Mode: {mode_name} | Peak: {self.current_max_peak:.4f}", flush=True)
        
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
