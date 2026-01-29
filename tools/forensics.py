import sounddevice as sd
import numpy as np
import time

class CustomWasapiSettings:
    def __init__(self):
        # 0x00000100 is the flag for loopback in PortAudio WASAPI
        self._streaminfo = sd._ffi.new('PaWasapiStreamInfo*', {
            'size': sd._ffi.sizeof('PaWasapiStreamInfo'),
            'hostApiType': sd._lib.paWASAPI,
            'version': 1,
            'flags': 256
        })

def test_device(idx, name, is_wasapi=False):
    print(f"\n--- Testing Device {idx}: {name} ---")
    
    settings = CustomWasapiSettings() if is_wasapi else None
    
    # Try common configurations
    configs = [
        (48000, 2),
        (44100, 2),
        (48000, 1),
        (44100, 1)
    ]
    
    for rate, chans in configs:
        try:
            print(f"  Attempting {rate}Hz, {chans}ch...")
            with sd.InputStream(device=idx, channels=chans, samplerate=rate, extra_settings=settings) as stream:
                print("  SUCCESS! Monitoring signal for 3 seconds...")
                start_time = time.time()
                peaks = []
                while time.time() - start_time < 3:
                    data, overflowed = stream.read(1024)
                    rms = np.sqrt(np.mean(data**2))
                    peaks.append(rms)
                    time.sleep(0.1)
                
                max_rms = max(peaks) if peaks else 0
                print(f"  MAX RMS observed: {max_rms:.6f}")
                if max_rms > 0.0001:
                    print("  >> ACTIVE SIGNAL DETECTED! <<")
                    return True
                else:
                    print("  >> Silence detected. <<")
        except Exception as e:
            print(f"  FAILED: {e}")
    return False

print("System Audio Forensics starting...")
print("Please ensure audio (YouTube/Spotify) is playing.")

# Candidates from previous queries:
# 12 is SyncMaster (WASAPI)
# 4 is SyncMaster (MME)
# 2 is Stereo Mix (MME)
# 8 is Stereo Mix (DirectSound)

test_device(12, "SyncMaster WASAPI", is_wasapi=True)
test_device(4, "SyncMaster MME", is_wasapi=False)
test_device(2, "Stereo Mix MME", is_wasapi=False)

print("\nForensics complete.")
