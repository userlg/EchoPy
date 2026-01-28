
import sounddevice as sd
import sys

def diagnose():
    print("--- RawInputStream Probe ---")
    i = 12
    d = sd.query_devices(i)
    
    try:
        settings = sd.WasapiSettings()
        settings._streaminfo.flags |= 256 # Loopback
        
        # Using RawInputStream to see if it bypasses validation
        stream = sd.RawInputStream(
            device=i, 
            channels=2, 
            samplerate=48000, 
            dtype='int16',
            extra_settings=settings
        )
        stream.start()
        print("✅ SUCCESS: RawInputStream started on SyncMaster Loopback!")
        stream.stop()
        stream.close()
    except Exception as e:
        print(f"❌ FAILED: RawInputStream -> {e}")

if __name__ == "__main__":
    diagnose()
