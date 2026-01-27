from __future__ import annotations
import sys
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
        # Signal processing state
        self.gain = 60.0
        self.smoother = smoother or SmoothingBuffer(fft_size // 2, 0.4)
        
        # Audio stream state
        self.stream: Optional[sd.InputStream] = None
        self.is_running = False
        self.device_index: Optional[int] = None
        self.window = np.hanning(buffer_size)
        
        # AGC State
        self.running_peak = 0.01
        
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
        
        # Auto-match sample rate to hardware if possible
        try:
            device_info = sd.query_devices(device_index)
            host_api = sd.query_hostapis(device_info['hostapi'])['name']
            
            # Try different configurations in order of preference
            configs = [
                # 1. Hardware default (usually works)
                {'rate': int(device_info['default_samplerate']), 'channels': 1},
                # 2. Hardware default with stereo channels (some WASAPI devices require this)
                {'rate': int(device_info['default_samplerate']), 'channels': min(2, device_info['max_input_channels'])},
                # 3. Standard fallback rates
                {'rate': 44100, 'channels': 1},
                {'rate': 48000, 'channels': 1}
            ]
            
            last_error = None
            for config in configs:
                try:
                    self.sample_rate = config['rate']
                    chans = config['channels']
                    
                    logger.info(f"Attempting capture: {host_api} | {self.sample_rate}Hz | {chans}ch")
                    
                    self.stream = sd.InputStream(
                        device=device_index,
                        channels=chans,
                        samplerate=self.sample_rate,
                        blocksize=self.buffer_size,
                        callback=self._audio_callback
                    )
                    self.stream.start()
                    self.is_running = True
                    logger.info(f"Audio capture SUCCESSFUL (device: {device_index})")
                    return # Exit on success
                except Exception as e:
                    last_error = e
                    continue
            
            # If all configs failed for this device, and it was WASAPI, try finding MME version
            if host_api == 'Windows WASAPI':
                logger.warning("WASAPI failed, searching for MME fallback...")
                mme_device = self._find_mme_version(device_info['name'])
                if mme_device is not None:
                    return self.start(device_index=mme_device, use_loopback=False)
            
            raise last_error or Exception("All configurations failed")
            
        except Exception as e:
            logger.error(f"FATAL: All capture attempts failed for device {device_index}: {e}")
            self.is_running = False

    def _find_mme_version(self, target_name: str) -> Optional[int]:
        """Find the MME version of a WASAPI device name for fallback."""
        try:
            devices = sd.query_devices()
            mme_idx = [i for i, h in enumerate(sd.query_hostapis()) if h['name'] == 'MME'][0]
            for i, d in enumerate(devices):
                if d['hostapi'] == mme_idx and target_name.split('(')[0].strip() in d['name']:
                    logger.info(f"Found MME fallback device: {d['name']} (index {i})")
                    return i
        except: pass
        return None
    
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
        """Audio stream callback."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        # 1. Mono capture
        audio_data = indata[:, 0]
        
        # 2. Precision Pre-AGC Gate
        # The user's music RMS is ~0.00005. We assume noise is < 0.00003.
        # We must gate BEFORE boosting, otherwise we just boost noise.
        raw_rms = np.sqrt(np.mean(audio_data**2))
        
        # Precision Threshold: Raised to 0.00005 (5e-5) to cut off higher noise floor
        if raw_rms < 0.00005:
            # SILENCE DETECTED
            self.audio_buffer = np.zeros_like(audio_data)
            self.fft_data = np.zeros(self.fft_size // 2, dtype=np.float32)
            self.audio_data_ready.emit(self.audio_buffer, self.fft_data)
            return 

        # --- AUTOMATIC GAIN CONTROL (AGC) ---
        # If we passed the gate, this is valid signal. Boost it.
        
        # Track peak with decay
        current_peak = np.max(np.abs(audio_data))
        if current_peak > self.running_peak:
            self.running_peak = current_peak
        else:
            self.running_peak *= 0.995 
            
        # Floor raised to 0.00008: Limit max boost to avoid amplifying noise floor
        search_floor = 0.00008 
        effective_peak = max(self.running_peak, search_floor)
        
        # Target level is 0.5 (half scale)
        norm_factor = 0.5 / effective_peak
        
        # Apply normalization
        normalized_data = audio_data * norm_factor
        self.audio_buffer = normalized_data.copy()
        
        # 3. FFT Processing
        windowed_data = normalized_data * self.window
        fft_raw = np.fft.rfft(windowed_data, n=self.fft_size)
        
        # Normalize FFT magnitude:
        # Scale by 2/N to get actual amplitude (0..1)
        # This prevents the AGC-boosted signal from resulting in massive (>100) values
        fft_magnitude = np.abs(fft_raw)[:self.fft_size // 2] * (2.0 / self.fft_size)
        
        # Filter out DC
        fft_magnitude[:2] = 0.0
        
        # Enhanced Log-scaling
        fft_magnitude = np.log1p(fft_magnitude) / 3.0
            
        # Apply User Gain (Fine tuning)
        fft_magnitude = np.clip(fft_magnitude * (self.gain / 60.0), 0.0, 1.0)
        
        # 4. Smoothing and Delivery
        self.fft_data = np.array(self.smoother.update(fft_magnitude.tolist()), dtype=np.float32)
        self.audio_data_ready.emit(self.audio_buffer, self.fft_data)
    
    def set_smoothing(self, smoothing: float):
        """
        Set smoothing factor.
        
        Args:
            smoothing: Smoothing factor (0.0 to 1.0)
        """
        self.smoother.set_smoothing(smoothing)

    def set_gain(self, gain: float):
        """
        Set gain multiplier.
        
        Args:
            gain: Gain factor (e.g. 60.0 for normal, 120.0 for high)
        """
        self.gain = gain
        logger.info(f"Gain set to: {self.gain}")
    
    def get_devices(self) -> List[dict]:
        """
        Get list of available audio input devices.
        
        Returns:
            List of device info dictionaries
        """
        try:
            devices = sd.query_devices()
            input_devices = []
            
            # Strict filtering: Only allow System Audio / Loopback devices
            # Keywords that indicate a system loopback device
            valid_keywords = ['stereo mix', 'what u hear', 'loopback', 'wave out', 'waveout', 'monitor']
            
            # Keywords to strictly exclude (microphones, etc)
            exclude_keywords = ['mic', 'microphone', 'input', 'headset', 'webcam', 'line in']
            
            for i, device in enumerate(devices):
                device_name = device['name'].lower()
                
                # Check if it's a valid loopback device
                is_valid = False
                
                # 1. Must contain a valid keyword
                if any(kw in device_name for kw in valid_keywords):
                    is_valid = True
                
                # 2. Must NOT contain an exclude keyword (unless it strictly claims to be a mix)
                if any(kw in device_name for kw in exclude_keywords):
                    # If it has a bad keyword, it's false unless it SPECIFICALLY says "stereo mix"
                    if 'stereo mix' not in device_name:
                        is_valid = False
                
                # 3. Must have input channels
                if device['max_input_channels'] <= 0:
                    is_valid = False
                    
                if is_valid:
                    input_devices.append({
                        'index': i,
                        'name': f"🔊 {device['name']} (System Audio)",
                        'channels': device['max_input_channels'],
                        'sample_rate': device['default_samplerate'],
                        'is_loopback': True
                    })
            
            if not input_devices:
                logger.warning("No specific System Audio devices found. Listing all non-microphone input devices as fallback.")
                # Fallback: List everything satisfying basic exclusion rules if nothing else found
                for i, device in enumerate(devices):
                    device_name = device['name'].lower()
                    if device['max_input_channels'] > 0 and not any(kw in device_name for kw in exclude_keywords):
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
        Find a Windows loopback device (Stereo Mix) for capturing system audio.
        Heavily prioritizes 'Stereo Mix' as the most stable way to capture system audio
        in this environment.
        """
        try:
            devices = sd.query_devices()
            
            # 1. Look for 'Stereo Mix' under Windows WASAPI (Highest Quality)
            for i, device in enumerate(devices):
                device_name = device['name'].lower()
                try:
                    host_api = sd.query_hostapis(device['hostapi'])['name']
                except: continue
                
                if host_api == 'Windows WASAPI' and 'stereo mix' in device_name:
                    logger.info(f"Using High Quality WASAPI Stereo Mix: {device['name']} (index {i})")
                    return i

            # 2. Look for 'Stereo Mix' under MME/DirectSound (High Compatibility)
            for i, device in enumerate(devices):
                device_name = device['name'].lower()
                if 'stereo mix' in device_name and device['max_input_channels'] > 0:
                    logger.info(f"Using Legacy Stereo Mix: {device['name']} (index {i})")
                    return i
            
            # 3. Last resort: ANY device with 'mix' or 'loopback' in name
            for i, device in enumerate(devices):
                device_name = device['name'].lower()
                if any(kw in device_name for kw in ['mix', 'loopback']) and device['max_input_channels'] > 0:
                    return i
                    
            logger.info("No Stereo Mix or loopback device found automatically.")
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
