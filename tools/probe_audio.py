
import sounddevice as sd
import sys

def diagnose():
    print("--- Audio Device Diagnosis (Reporting Errors) ---")
    devices = sd.query_devices()
    host_apis = sd.query_hostapis()
    
    for i, d in enumerate(devices):
        api_name = host_apis[d['hostapi']]['name']
        if i == 12: # Focusing on the failed SyncMaster WASAPI device
            print(f"\n[Index {i}] {d['name']}")
            print(f"  Host API: {api_name}")
            print(f"  Max Outputs: {d['max_output_channels']}")
            print(f"  Default Sample Rate: {d['default_samplerate']}")
            
            for rate in [d['default_samplerate'], 48000, 44100]:
                for chans in [int(d['max_output_channels']), 2, 1]:
                    if chans == 0: continue
                    try:
                        settings = sd.WasapiSettings()
                        settings._streaminfo.flags |= 256 # Loopback
                        
                        stream = sd.InputStream(
                            device=i, 
                            channels=chans, 
                            samplerate=int(rate), 
                            extra_settings=settings
                        )
                        stream.start()
                        stream.stop()
                        stream.close()
                        print(f"  ✅ SUCCESS: {rate}Hz, {chans}ch")
                        return # Exit on first success
                    except Exception as e:
                        print(f"  ❌ FAILED: {rate}Hz, {chans}ch -> {e}")

if __name__ == "__main__":
    diagnose()
