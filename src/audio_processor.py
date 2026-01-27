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
                # 1. Prefer Stereo (to capture all music channels)
                {'rate': int(device_info['default_samplerate']), 'channels': min(2, device_info['max_input_channels'])},
                # 2. Fallback to Mono
                {'rate': int(device_info['default_samplerate']), 'channels': 1},
                # 3. Standard fallback rates
                {'rate': 44100, 'channels': min(2, device_info['max_input_channels'])},
                {'rate': 48000, 'channels': min(2, device_info['max_input_channels'])}
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
        try:
            # Debug callback execution (remove later)
            # print(".", end="", flush=True) 
            
            if status:
                logger.warning(f"Audio callback status: {status}")
            
            # 1. Stereo to Mono capture (average channels to ensure we miss nothing)
            if indata.shape[1] >= 2:
                audio_data = np.mean(indata, axis=1)
            else:
                audio_data = indata[:, 0]
            
            # --- DYNAMIC RANGE EXPANDER (Better than AGC) ---
            # Problem: AGC flattens dynamics (quiet = loud).
            # Solution: Subtract noise floor, then multiply.
            # This acts as a "Soft Gate" and preserves relative volume.
            
            # 1. Noise Floor Subtraction
            # Calibrated to silence the constant 0.00017 hiss observed in logs
            NOISE_FLOOR = 0.0
            
            # Using abs() to detect amplitude, then restoring sign (though for FFT we just need magnitude)
            # But we act on the raw waveform first to clean it.
            # "Soft Knee" gate:
            # If val < 0.000035 -> 0
            # If val = 0.000045 -> 0.00001
            
            abs_data = np.abs(audio_data)
            clean_gain = np.maximum(0, abs_data - NOISE_FLOOR)
            
            # 2. Massive Make-up Gain
            # Reduced from 40000 to 6000 to fix saturation (Peak ~1.0)
            GAIN_MULTIPLIER = 20000.0
            
            boosted_data = clean_gain * GAIN_MULTIPLIER
            
            # Restore sign (optional, but good for waveform visuals)
            self.audio_buffer = boosted_data * np.sign(audio_data)
            
            # 3. FFT Processing
            # Apply window to the clean, boosted data
            windowed_data = self.audio_buffer * self.window
            fft_raw = np.fft.rfft(windowed_data, n=self.fft_size)
            
            # Normalize: Scale by 2/N
            fft_magnitude = np.abs(fft_raw)[:self.fft_size // 2] * (2.0 / self.fft_size)
            
            # Filter out DC
            fft_magnitude[:2] = 0.0
            
            # Enhanced Log-scaling
            fft_magnitude = np.log1p(fft_magnitude) / 3.0
                
            # Apply User Gain (Fine tuning)
            fft_magnitude = np.clip(fft_magnitude * (self.gain / 60.0), 0.0, 1.0)
            
            # 4. Smoothing and Delivery
            # Optimized: passing numpy array directly, avoiding list conversions
            self.fft_data = self.smoother.update(fft_magnitude)
            self.audio_data_ready.emit(self.audio_buffer, self.fft_data)
        
        except Exception as e:
            print(f"CALLBACK FATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    def set_smoothing(self, smoothing: float):
        """Set smoothing factor."""
        self.smoother.set_smoothing(smoothing)

    def set_gain(self, gain: float):
        """Set gain multiplier."""
        self.gain = gain
        logger.info(f"Gain set to: {self.gain}")
    
    def get_devices(self) -> List[dict]:
        """Get list of available audio input devices."""
        try:
            devices = sd.query_devices()
            input_devices = []
            valid_keywords = ['stereo mix', 'what u hear', 'loopback', 'wave out', 'waveout', 'monitor']
            exclude_keywords = ['mic', 'microphone', 'input', 'headset', 'webcam', 'line in']
            
            for i, device in enumerate(devices):
                device_name = device['name'].lower()
                is_valid = False
                if any(kw in device_name for kw in valid_keywords):
                    is_valid = True
                if any(kw in device_name for kw in exclude_keywords):
                    if 'stereo mix' not in device_name:
                        is_valid = False
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
        """Find a Windows loopback device (Stereo Mix)."""
        try:
            devices = sd.query_devices()
            for i, device in enumerate(devices):
                device_name = device['name'].lower()
                try:
                    host_api = sd.query_hostapis(device['hostapi'])['name']
                except: continue
                if host_api == 'Windows WASAPI' and 'stereo mix' in device_name:
                    logger.info(f"Using High Quality WASAPI Stereo Mix: {device['name']} (index {i})")
                    return i
            for i, device in enumerate(devices):
                device_name = device['name'].lower()
                if 'stereo mix' in device_name and device['max_input_channels'] > 0:
                    logger.info(f"Using Legacy Stereo Mix: {device['name']} (index {i})")
                    return i
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
        """Change audio input device."""
        was_running = self.is_running
        if was_running:
            self.stop()
        if was_running:
            self.start(device_index)
