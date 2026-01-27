from __future__ import annotations
import numpy as np
import sounddevice as sd
from PySide6.QtCore import QObject, Signal, QTimer
from typing import Optional, List, Dict, TYPE_CHECKING
if TYPE_CHECKING:
    from numpy import ndarray
from utils import SmoothingBuffer, logger


class AudioProcessor(QObject):
    """Handles real-time audio capture and FFT processing."""
    
    # Signal emitted when new audio data is available
    # Using strings for types in Signal to avoid runtime evaluation issues
    audio_data_ready = Signal(object, object)  # (waveform, fft_data)
    
    def __init__(self, 
                 sample_rate: int = 44100,
                 buffer_size: int = 2048,
                 fft_size: int = 2048,
                 smoother: Optional[SmoothingBuffer] = None):
        """
        Initialize audio processor.
        
        Args:
            sample_rate: Audio sample rate in Hz
            buffer_size: Audio buffer size
            fft_size: FFT size (must be power of 2)
            smoother: Optional SmoothingBuffer instance (Dependency Inversion)
        """
        super().__init__()
        
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.fft_size = fft_size
        
        # Audio data buffers
        self.audio_buffer = np.zeros(buffer_size, dtype=np.float32)
        self.fft_data = np.zeros(fft_size // 2, dtype=np.float32)
        
        # Windowing function
        self.window = np.hanning(buffer_size)
        
        # Smoothing (DIP: Inject if provided, otherwise create default)
        self.smoother = smoother or SmoothingBuffer(fft_size // 2, 0.8)
        
        # Audio stream
        self.stream: Optional[sd.InputStream] = None
        self.is_running = False
        
        # Device info
        self.device_index: Optional[int] = None
        
    def start(self, device_index: Optional[int] = None, use_loopback: bool = True):
        """
        Start audio capture.
        
        Args:
            device_index: Audio device index (None for auto-detect)
            use_loopback: If True, try to find and use loopback device for system audio
        """
        if self.is_running:
            return
        
        # If no device specified and use_loopback is True, try to find loopback device
        if device_index is None and use_loopback:
            loopback_device = self.find_loopback_device()
            if loopback_device is not None:
                device_index = loopback_device
                logger.info(f"Using loopback device for system audio capture: {device_index}")
            else:
                logger.warning("No loopback device found. Using default microphone.")
                logger.info("To capture system audio on Windows:")
                logger.info("  1. Ensure 'Stereo Mix' is enabled OR")
                logger.info("  2. Use a WASAPI loopback device if available.")
        
        self.device_index = device_index
        
        try:
            self.stream = sd.InputStream(
                device=device_index,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.buffer_size,
                callback=self._audio_callback
            )
            self.stream.start()
            self.is_running = True
            logger.info(f"Audio capture started (device: {device_index or 'default'})")
        except Exception as e:
            logger.error(f"Error starting audio capture: {e}", exc_info=True)
            self.is_running = False
    
    def stop(self):
        """Stop audio capture."""
        if not self.is_running:
            return
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        self.is_running = False
        logger.info("Audio capture stopped")
    
    def _audio_callback(self, indata, frames, time, status):
        """
        Audio stream callback.
        
        Args:
            indata: Input audio data
            frames: Number of frames
            time: Time info
            status: Status flags
        """
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        # Prepare data for FFT (Mono + Windowing)
        audio_data = indata[:, 0].copy()
        windowed_data = audio_data * self.window
        
        # Update audio buffer (raw for waveform visualization)
        self.audio_buffer = audio_data
        
        # Perform FFT
        fft_raw = np.fft.rfft(windowed_data, n=self.fft_size)
        fft_magnitude = np.abs(fft_raw)[:self.fft_size // 2]
        
        # Normalize
        fft_magnitude = fft_magnitude / (self.fft_size / 2)
        
        # Apply Gain (Boost the signal for better visualization)
        fft_magnitude = fft_magnitude * 20.0  # Slightly increased gain
        
        # Apply smoothing
        self.fft_data = np.array(self.smoother.update(fft_magnitude.tolist()), dtype=np.float32)
        
        # Emit signal with new data
        self.audio_data_ready.emit(self.audio_buffer.copy(), self.fft_data.copy())
    
    def set_smoothing(self, smoothing: float):
        """
        Set smoothing factor.
        
        Args:
            smoothing: Smoothing factor (0.0 to 1.0)
        """
        self.smoother.set_smoothing(smoothing)
    
    def get_devices(self) -> List[dict]:
        """
        Get list of available audio input devices.
        
        Returns:
            List of device info dictionaries
        """
        try:
            devices = sd.query_devices()
            input_devices = []
            
            # First, check for Windows loopback devices
            for i, device in enumerate(devices):
                device_name = device['name'].lower()
                
                # Check if it's a loopback/output device that we can use for recording
                # In Windows, we look for output devices that support loopback
                if device['max_output_channels'] > 0:
                    # Check for common loopback device names
                    is_loopback = any(keyword in device_name for keyword in [
                        'stereo mix', 
                        'wave out mix',
                        'what u hear',
                        'loopback'
                    ])
                    
                    if is_loopback or 'mix' in device_name:
                        input_devices.append({
                            'index': i,
                            'name': f"🔊 {device['name']} (System Audio)",
                            'channels': device['max_output_channels'],
                            'sample_rate': device['default_samplerate'],
                            'is_loopback': True
                        })
            
            # Then add regular input devices
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    input_devices.append({
                        'index': i,
                        'name': device['name'],
                        'channels': device['max_input_channels'],
                        'sample_rate': device['default_samplerate'],
                        'is_loopback': False
                    })
            
            return input_devices
        except Exception as e:
            logger.error(f"Error querying devices: {e}")
            return []
    
    def find_loopback_device(self) -> Optional[int]:
        """
        Find a Windows loopback device (Stereo Mix, etc.) for capturing system audio.
        
        Returns:
            Device index of loopback device, or None if not found
        """
        try:
            devices = sd.query_devices()
            
            # Look for common loopback device names
            loopback_keywords = [
                'stereo mix',
                'wave out mix', 
                'what u hear',
                'what you hear',
                'loopback',
                'mix'
            ]
            
            for i, device in enumerate(devices):
                device_name = device['name'].lower()
                host_api = sd.query_hostapis(device['hostapi'])['name']
                
                # Check for WASAPI loopback (modern Windows method)
                if host_api == 'Windows WASAPI' and device['max_output_channels'] > 0:
                    # In sounddevice, WASAPI loopback is often hidden or needs special handling,
                    # but sometimes it shows up as an input device with 'loopback' in name.
                    if 'loopback' in device_name:
                        logger.info(f"Found WASAPI loopback device: {device['name']} (index {i})")
                        return i
                
                # Check for common loopback device names (Stereo Mix, etc.)
                for keyword in loopback_keywords:
                    if keyword in device_name and device['max_input_channels'] > 0:
                        logger.info(f"Found loopback device: {device['name']} (index {i})")
                        return i
            
            logger.info("No loopback device found automatically.")
            return None
            
        except Exception as e:
            logger.error(f"Error finding loopback device: {e}")
            return None
    
    def set_device(self, device_index: Optional[int]):
        """
        Change audio input device.
        
        Args:
            device_index: Device index
        """
        was_running = self.is_running
        
        if was_running:
            self.stop()
        
        if was_running:
            self.start(device_index)
