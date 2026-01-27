import sounddevice as sd
import numpy as np
import time
import sys

def diagnose():
    print("Enumerating all audio devices for signal detection...")
    try:
        devices = sd.query_devices()
    except Exception as e:
        print(f"Error querying devices: {e}")
        return

    active_devices = []

    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            host_api = "Unknown"
            try:
                host_api = sd.query_hostapis(device['hostapi'])['name']
            except: pass
            
            print(f"\nTesting Device {i}: {device['name']} ({host_api})")
            try:
                # Try to capture a short burst
                samplerate = int(device['default_samplerate'])
                with sd.InputStream(device=i, channels=1, samplerate=samplerate) as stream:
                    sd.sleep(100)
                    data, overflowed = stream.read(1024)
                    
                    # Manual peak detection if numpy methods are missing
                    # data is likely a numpy array if sounddevice is working
                    try:
                        peak = float(np.max(np.abs(data)))
                    except:
                        # Fallback for corrupted numpy: iterate manually
                        # data.flatten() might work if it's a ndarray
                        vals = data.flatten()
                        peak = 0.0
                        for v in vals:
                            abs_v = abs(v)
                            if abs_v > peak: peak = abs_v
                    
                    print(f"  > Peak Level: {peak:.6f}")
                    if peak > 0.0001:
                        print("  [!!!] ACTIVE SIGNAL DETECTED!")
                        active_devices.append((i, device['name'], peak))
            except Exception as e:
                print(f"  > Error: {e}")

    print("\n--- Summary of Active Sources ---")
    if not active_devices:
        print("No active signals found on any device.")
    for idx, name, peak in active_devices:
        print(f"Index {idx}: {name} (Peak: {peak:.4f})")

if __name__ == "__main__":
    diagnose()
