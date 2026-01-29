"""Utility functions for EchoPy."""

import json
import os
import sys
import logging
from typing import Any, Dict, Optional
import numpy as np
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt


def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller bundle."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Not running in a bundle, use project root
        # This assumes utils is in src/
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    return os.path.join(base_path, relative_path)


def get_user_data_path() -> str:
    """Get absolute path to user data directory for logs and config."""
    app_name = "EchoPy"
    if os.name == 'nt':
        base_path = os.getenv('LOCALAPPDATA', os.path.expanduser('~'))
    else:
        base_path = os.path.join(os.path.expanduser('~'), '.local', 'share')
    
    data_path = os.path.join(base_path, app_name)
    os.makedirs(data_path, exist_ok=True)
    return data_path


# Configure logging
def setup_logging(level=logging.INFO):
    """Setup application logging."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(get_user_data_path(), "echopy.log"), encoding='utf-8')
        ]
    )


logger = logging.getLogger("EchoPy")


class Config:
    """Configuration manager for persistence."""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize configuration manager."""
        # Use user data path if just a filename is provided
        if not os.path.isabs(config_file):
            self.config_file = os.path.join(get_user_data_path(), config_file)
        else:
            self.config_file = config_file
            
        if not os.path.exists(self.config_file):
             self._ensure_writable()
        
        self.config: Dict[str, Any] = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        defaults = {
            "theme": "modern",
            "style": "spectrum_bars",
            "audio_device": None,
            "sample_rate": 44100,
            "fft_size": 2048,
            "smoothing": 0.5,
            "background_image": None,
            "fullscreen": False,
            "fps_limit": 60,
            "gain": 100.0,
            "opacity": 0.3,
            "sensitivity": {
                "rms_threshold_on": 0.0008,
                "rms_threshold_off": 0.0004,
                "silence_timeout": 45
            }
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                    # Merge saved config with defaults
                    defaults.update(saved_config)
                    return defaults
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        # Default configuration
        return defaults
    
    def save_config(self):
        """Save configuration to file."""
        try:
            # Ensure file is not hidden/read-only before writing
            self._ensure_writable()
            
            # Write JSON
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def _ensure_writable(self):
        """Ensure file is writable by removing Hidden attribute on Windows."""
        if os.name == 'nt' and os.path.exists(self.config_file):
            try:
                import ctypes
                # FILE_ATTRIBUTE_NORMAL = 0x80
                # Set to normal to remove Hidden (0x02) or Read-only (0x01)
                ctypes.windll.kernel32.SetFileAttributesW(self.config_file, 0x80)
            except Exception as e:
                logger.error(f"Error removing hidden attribute: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value and save."""
        self.config[key] = value
        self.save_config()


class SmoothingBuffer:
    """Exponential moving average smoother for audio data (Vectorized)."""
    
    def __init__(self, size: int, smoothing: float = 0.8):
        """
        Initialize smoothing buffer.
        
        Args:
            size: Buffer size
            smoothing: Smoothing factor (0.0 to 1.0, higher = smoother)
        """
        self.size = size
        self.smoothing = max(0.0, min(1.0, smoothing))
        self.buffer = np.zeros(size, dtype=np.float32)
    
    def update(self, values: Any) -> np.ndarray:
        """
        Update buffer with new values and return smoothed values.
        
        Args:
            values: New values to smooth (list or np.ndarray)
            
        Returns:
            Smoothed values as np.ndarray
        """
        # Ensure input is numpy array
        if isinstance(values, np.ndarray):
            new_values = values.astype(np.float32)
        else:
            new_values = np.array(values, dtype=np.float32)
        
        if len(new_values) != self.size:
            # Resize buffer if needed (resetting history)
            self.size = len(new_values)
            self.buffer = np.zeros(self.size, dtype=np.float32)
        
        # Vectorized calculation:
        # buffer = buffer * smoothing + new * (1 - smoothing)
        self.buffer = self.buffer * self.smoothing + new_values * (1.0 - self.smoothing)
        
        return self.buffer.copy()
    
    def set_smoothing(self, smoothing: float):
        """Set smoothing factor."""
        # Ensure input is float
        try:
           s = float(smoothing)
        except:
           s = 0.5
        self.smoothing = max(0.0, min(1.0, s))
    
    def reset(self):
        """Reset buffer to zeros."""
        self.buffer = np.zeros(self.size, dtype=np.float32)


class CavaFilter:
    """
    Advanced filter inspired by CAVA (Integral Filter + Fall-off).
    Provides smoother and more 'liquid' transitions than simple EMA.
    """
    
    def __init__(self, size: int, integral_weight: float = 0.7, gravity: float = 0.03):
        """
        Initialize CavaFilter.
        
        Args:
            size: Buffer size
            integral_weight: Weight of previous values in the integral (0.0 to 1.0)
            gravity: How fast the bars fall down (higher = faster)
        """
        self.size = size
        self.integral_weight = integral_weight
        self.gravity = gravity
        self.prev_values = np.zeros(size, dtype=np.float32)
        self.integral_buffer = np.zeros(size, dtype=np.float32)
        
    def update(self, values: np.ndarray) -> np.ndarray:
        """
        Apply CAVA-style filtering.
        """
        if len(values) != self.size:
            self.size = len(values)
            self.prev_values = np.zeros(self.size, dtype=np.float32)
            self.integral_buffer = np.zeros(self.size, dtype=np.float32)

        # 1. Integral filter (Smooths the 'ascent')
        # integral = (current * (1-weight)) + (prev_integral * weight)
        self.integral_buffer = (values * (1.0 - self.integral_weight)) + (self.integral_buffer * self.integral_weight)
        
        # 2. Fall-off filter (Smooths the 'descent')
        # If new value is lower than old, apply gravity
        mask = self.integral_buffer < (self.prev_values - self.gravity)
        output = np.where(mask, self.prev_values - self.gravity, self.integral_buffer)
        
        # Clip to ensure no negative values
        output = np.maximum(0.0, output)
        
        self.prev_values = output.copy()
        return output

    def set_smoothing(self, smoothing: float):
        """Map generic smoothing (0-1) to integral weight."""
        self.integral_weight = clamp(smoothing, 0.1, 0.95)
    
    def set_gravity(self, gravity: float):
        """Set gravity factor."""
        self.gravity = gravity


def load_image(path: str, width: Optional[int] = None, height: Optional[int] = None) -> Optional[QPixmap]:
    """
    Load and optionally scale an image.
    
    Args:
        path: Path to image file
        width: Target width (None to keep aspect ratio)
        height: Target height (None to keep aspect ratio)
        
    Returns:
        QPixmap or None if loading failed
    """
    if not os.path.exists(path):
        return None
    
    image = QImage(path)
    if image.isNull():
        return None
    
    pixmap = QPixmap.fromImage(image)
    
    if width or height:
        if width and height:
            pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        elif width:
            pixmap = pixmap.scaledToWidth(width, Qt.SmoothTransformation)
        elif height:
            pixmap = pixmap.scaledToHeight(height, Qt.SmoothTransformation)
    
    return pixmap


def frequency_to_bin(frequency: float, sample_rate: int, fft_size: int) -> int:
    """
    Convert frequency in Hz to FFT bin index.
    
    Args:
        frequency: Frequency in Hz
        sample_rate: Sample rate in Hz
        fft_size: FFT size
        
    Returns:
        Bin index
    """
    return int(frequency * fft_size / sample_rate)


def bin_to_frequency(bin_index: int, sample_rate: int, fft_size: int) -> float:
    """
    Convert FFT bin index to frequency in Hz.
    
    Args:
        bin_index: Bin index
        sample_rate: Sample rate in Hz
        fft_size: FFT size
        
    Returns:
        Frequency in Hz
    """
    return bin_index * sample_rate / fft_size


def map_range(value: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    """
    Map a value from one range to another.
    
    Args:
        value: Input value
        in_min: Input range minimum
        in_max: Input range maximum
        out_min: Output range minimum
        out_max: Output range maximum
        
    Returns:
        Mapped value
    """
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))
