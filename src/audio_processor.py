import numpy as np
import time
import sounddevice as sd
try:
    import pyaudiowpatch as pyaudio
    HAS_PYAUDIOWPATCH = True
except ImportError:
    HAS_PYAUDIOWPATCH = False
from PySide6.QtCore import QObject, Signal, QTimer
from typing import Optional, List, Dict, TYPE_CHECKING
if TYPE_CHECKING:
    from numpy import ndarray
from utils import SmoothingBuffer, CavaFilter, logger


class AudioProcessor(QObject):
    """Handles real-time audio capture and FFT processing."""
    
    # Signal emitted when new audio data is available
    audio_data_ready = Signal(object, object, float)  # (waveform, fft_data, activity_level)
    
    def __init__(self, 
                 sample_rate: int = 44100,
                 buffer_size: int = 2048,
                 fft_size: int = 2048,
                 smoother: Optional[CavaFilter] = None):
        """Initialize audio processor."""
        super().__init__()
        
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.fft_size = fft_size
        
        # Audio data buffers
        self.audio_buffer = np.zeros(buffer_size, dtype=np.float32)
        self.fft_data = np.zeros(fft_size // 2, dtype=np.float32)
        
        # Signal processing state
        self.gain = 60.0
        self.smoother = smoother or CavaFilter(fft_size // 2, 0.7, 0.03)
        
        # Audio stream state
        self.stream: Optional[Any] = None # Can be sd.InputStream or pyaudio.Stream
        self.pa_instance: Optional[pyaudio.PyAudio] = None
        self.is_running = False
        self.device_index: Optional[int] = None
        self.window = np.hanning(buffer_size)
        
        # AGC State
        self.running_peak = 0.01
        
    def start(self, device_index: Optional[int] = None, use_loopback: bool = True):
        """
        Start audio capture with enhanced multi-device fallback and PyAudioWPatch support.
        """
        if self.is_running:
            return

        # 1. Try PyAudioWPatch first if available (Most reliable for WASAPI Loopback)
        if HAS_PYAUDIOWPATCH and use_loopback and device_index is None:
            try:
                if self._start_pyaudiowpatch():
                    return
            except Exception as e:
                logger.error(f"PyAudioWPatch failed: {e}. Falling back to sounddevice.")

        # 2. Fallback to sounddevice
        self._start_sounddevice(device_index, use_loopback)

    def _start_pyaudiowpatch(self) -> bool:
        """Attempt to start capture using PyAudioWPatch."""
        try:
            self.pa_instance = pyaudio.PyAudio()
            
            # Find WASAPI API
            wasapi_api_idx = -1
            for i in range(self.pa_instance.get_host_api_count()):
                if self.pa_instance.get_host_api_info_by_index(i)['type'] == pyaudio.paWASAPI:
                    wasapi_api_idx = i
                    break
            
            if wasapi_api_idx == -1:
                self.pa_instance.terminate()
                return False

            # Get default loopback device
            try:
                default_speakers = self.pa_instance.get_default_output_device_info()
                loopback = self.pa_instance.get_wasapi_loopback_analogue_by_dict(default_speakers)
            except (IOError, RuntimeError):
                # Fallback: specific search for SyncMaster if default fails
                loopback = None
                for i in range(self.pa_instance.get_device_count()):
                    dev = self.pa_instance.get_device_info_by_index(i)
                    if dev['hostApi'] == wasapi_api_idx and "SyncMaster" in dev['name'] and dev['maxInputChannels'] > 0:
                        loopback = dev
                        break
                if not loopback:
                    self.pa_instance.terminate()
                    return False

            logger.info(f"PyAudioWPatch: Initializing capture on {loopback['name']}")
            
            # Open stream
            self.stream = self.pa_instance.open(
                format=pyaudio.paFloat32,
                channels=loopback['maxInputChannels'],
                rate=int(loopback['defaultSampleRate']),
                input=True,
                frames_per_buffer=self.buffer_size,
                input_device_index=loopback['index'],
                stream_callback=self._pyaudio_callback
            )
            
            self.sample_rate = int(loopback['defaultSampleRate'])
            self.device_index = loopback['index']
            self.is_running = True
            logger.info(f"PYAUDIO ENGINE ONLINE: {loopback['name']} ({loopback['maxInputChannels']}ch @ {self.sample_rate}Hz)")
            return True
            
        except Exception as e:
            logger.debug(f"PyAudioWPatch start failed: {e}")
            if self.pa_instance:
                self.pa_instance.terminate()
                self.pa_instance = None
            return False

    def _pyaudio_callback(self, in_data, frame_count, time_info, status):
        """Bridge between PyAudio and the existing processor logic."""
        # Convert bytes string to numpy array (pyaudio format=paFloat32)
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        # Reshape to (frames, channels) to match sounddevice's callback 'indata' format
        # but wait, existing logic expects (frames, channels).
        # PyAudioWPatch with float32 will give a flat array of interleaved channels.
        channels = self.pa_instance.get_device_info_by_index(self.device_index)['maxInputChannels']
        audio_data = audio_data.reshape(-1, channels)
        
        # Call the shared processing logic
        self._audio_callback(audio_data, frame_count, None, status)
        return (None, pyaudio.paContinue)

    def _start_sounddevice(self, device_index: Optional[int], use_loopback: bool):
        """Standard sounddevice capture with robust matching."""
        device_list = []
        if device_index is not None:
            device_list = [device_index]
        elif use_loopback:
            device_list = self.find_loopback_candidates()
            if not device_list:
                logger.warning("No loopback candidates found. Using default input.")
        
        if not device_list:
            device_list = [None] 

        last_error = None
        for current_idx in device_list:
            try:
                device_info = sd.query_devices(current_idx)
                host_api = sd.query_hostapis(device_info['hostapi'])['name']
                
                # Check hardware capabilities
                hw_input_chans = device_info['max_input_channels']
                hw_output_chans = device_info['max_output_channels']
                
                # WASAPI Loopback check
                is_wasapi_loopback = (host_api == 'Windows WASAPI' and hw_input_chans == 0)
                
                # SPECIAL FIX: If it's a render device (0 inputs), we MUST use the loopback flag
                # but sounddevice might block non-input devices. 
                # We prioritize devices with ACTUAL input channels if they exist.
                
                chan_candidates = [hw_output_chans if is_wasapi_loopback else hw_input_chans, 2, 1]
                chan_candidates = sorted(list(set(c for c in chan_candidates if c > 0)), reverse=True)
                
                for chans in chan_candidates:
                    sample_rates = [int(device_info['default_samplerate']), 48000, 44100]
                    sample_rates = sorted(list(set(sample_rates)), reverse=True)
                    
                    for rate in sample_rates:
                        try:
                            extra_settings = self._get_wasapi_settings() if is_wasapi_loopback else None
                            
                            logger.info(f"Attempting: {device_info['name']} | {rate}Hz | {chans}ch")
                            
                            self.stream = sd.InputStream(
                                device=current_idx,
                                channels=chans,
                                samplerate=rate,
                                blocksize=self.buffer_size,
                                callback=self._audio_callback,
                                extra_settings=extra_settings
                            )
                            self.stream.start()
                            
                            self.sample_rate = rate
                            self.device_index = current_idx
                            self.is_running = True
                            logger.info(f"AUDIO ENGINE ONLINE: {device_info['name']} ({chans}ch @ {rate}Hz)")
                            return
                        except Exception as e:
                            last_error = e
                            continue
            except Exception as e:
                last_error = e
                continue
        
        logger.error(f"FATAL: All capture attempts failed. last error: {last_error}")
        self.is_running = False

    def _get_wasapi_settings(self):
        """Helper to create WASAPI loopback settings with CFFI fallback."""
        try:
            settings = sd.WasapiSettings()
            settings._streaminfo.flags |= 256 # paWinWasapiLoopback
            return settings
        except Exception:
            # Manual construction for older/minimal sounddevice installations
            class WASAPILoopbackSettings:
                def __init__(self):
                    self._streaminfo = sd._ffi.new('PaWasapiStreamInfo*', {
                        'size': sd._ffi.sizeof('PaWasapiStreamInfo'),
                        'hostApiType': sd._lib.paWASAPI,
                        'version': 1,
                        'flags': 256
                    })
            return WASAPILoopbackSettings()

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
            try:
                if hasattr(self.stream, 'stop'):
                    self.stream.stop()
                if hasattr(self.stream, 'close'):
                    self.stream.close()
            except: pass
            self.stream = None
        
        if self.pa_instance:
            try:
                self.pa_instance.terminate()
            except: pass
            self.pa_instance = None
        
        self.is_running = False
        logger.info("Audio capture stopped")
    
    def _audio_callback(self, indata, frames, time, status):
        """Optimized audio stream callback."""
        try:
            if status:
                # Log status but don't stop processing unless fatal
                if status.input_overflow:
                    # Input overflow is usually transient in MME/DirectSound
                    return # Skip this frame to catch up
                logger.warning(f"Audio callback status: {status}")
            
            # --- FASTER MULTICHANNEL DOWNMIXING ---
            channels = indata.shape[1]
            if channels == 2:
                # Optimized stereo-to-mono
                audio_data = (indata[:, 0] + indata[:, 1]) * 0.5
            elif channels == 1:
                audio_data = indata.ravel()
            else:
                # Vectorized weighted downmix for surround
                weights = np.ones(channels, dtype=np.float32)
                if channels >= 3: weights[2] = 0.7 # Center
                if channels >= 6: weights[4:6] = 0.7 # Surround
                weights /= (np.sum(weights) / 2.0)
                audio_data = np.dot(indata, weights)
            
            # --- ULTRA-FAST NOISE FLOOR & ENERGY ---
            NOISE_FLOOR = 0.00020
            # RMS calculation (Vectorized)
            activity_level = np.sqrt(np.mean(np.square(np.maximum(0.0, np.abs(audio_data) - NOISE_FLOOR))))
            
            # Apply Gain for visualizer (using the already cleaned data)
            # Scaling here avoids double-processing later
            # Use user-configurable gain
            # Base gain is 60.0, so we normalize relative to that
            user_gain_factor = self.gain / 60.0 
            GAIN_MULTIPLIER = 15000.0 * user_gain_factor
            self.audio_buffer = np.clip(audio_data * GAIN_MULTIPLIER, -1.0, 1.0)
            
            # 3. FFT Processing (Power-of-2 size is fast)
            windowed_data = audio_data * self.window
            fft_raw = np.fft.rfft(windowed_data, n=self.fft_size)
            
            # Normalize and scale
            fft_magnitude = np.abs(fft_raw)[:self.fft_size // 2] * (2.0 / self.fft_size)
            fft_magnitude[:2] = 0.0 # Remove DC
            
            # Log-perception scaling
            fft_magnitude = np.log1p(fft_magnitude) * 0.33
                
            # Apply User Gain and Clip
            fft_magnitude = np.clip(fft_magnitude * (self.gain / 60.0), 0.0, 1.0)
            
            # 4. Smoothing and Delivery
            self.fft_data = self.smoother.update(fft_magnitude)
            self.audio_data_ready.emit(self.audio_buffer, self.fft_data, activity_level)
        
        except Exception as e:
            logger.error(f"CALLBACK FATAL ERROR: {e}")
    
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
    
    def find_loopback_candidates(self) -> List[int]:
        """Find potential loopback devices in order of preference."""
        candidates = []
        try:
            # 1. Native WASAPI Loopback of the default output
            try:
                default_data = sd.query_devices(sd.default.device[1])
                default_out_name = default_data['name']
                
                for i, d in enumerate(sd.query_devices()):
                    is_wasapi = 'Windows WASAPI' in sd.query_hostapis(d['hostapi'])['name']
                    # Primary target: WASAPI version of the default output or SyncMaster
                    if is_wasapi and (default_out_name in d['name'] or "syncmaster" in d['name'].lower()):
                        if i not in candidates: candidates.append(i)
            except: pass

            # 2. Hardware Stereo Mix (MME)
            for i, d in enumerate(sd.query_devices()):
                if 'stereo mix' in d['name'].lower() and 'MME' in sd.query_hostapis(d['hostapi'])['name']:
                    if i not in candidates: candidates.append(i)
            
            # 3. Hardware Stereo Mix (Any other API)
            for i, d in enumerate(sd.query_devices()):
                if 'stereo mix' in d['name'].lower():
                    if i not in candidates: candidates.append(i)

            # 4. Keyword search (Broad)
            keywords = ['mix', 'loopback', 'reverb', 'monitor', 'what u hear']
            for i, d in enumerate(sd.query_devices()):
                if any(kw in d['name'].lower() for kw in keywords):
                    if i not in candidates: candidates.append(i)
                    
            return candidates
        except Exception as e:
            logger.error(f"Error finding loopback candidates: {e}")
            return []

    
    def set_device(self, device_index: Optional[int]):
        """Change audio input device safely."""
        # Map -1 (Auto) to None
        if device_index == -1:
            device_index = None

        # Safeguard: Don't restart if device is the same
        if device_index == self.device_index and self.is_running:
            logger.info(f"Device change ignored: Already on device index {device_index}")
            return
            
        was_running = self.is_running
        if was_running:
            self.stop()
            # Allow driver resources to release (critical for WASAPI Loopback)
            time.sleep(0.2)
            
        # Try to restart with new device
        if was_running:
            self.start(device_index)
            
            # Robustness check: If failed, try fallback to auto-detection
            if not self.is_running:
                logger.warning("Device switch failed, attempting fallback restart...")
                time.sleep(0.2)
                self.start() # Try default/auto strategy
