
import sounddevice as sd
import sys

def diagnose():
    print("--- WASAPI Exclusive Mode Probe ---")
    i = 12
    try:
        settings = sd.WasapiSettings(exclusive=True)
        # settings._streaminfo.flags |= 256 # Loopback (Exclusive usually doesn't need loopback flag, it takes the device)
        
        stream = sd.InputStream(
            device=i, 
            channels=2, 
            samplerate=48000, 
            extra_settings=settings
        )
        stream.start()
        print("✅ SUCCESS: Opened SyncMaster in Exclusive Mode!")
        stream.stop()
        stream.close()
    except Exception as e:
        print(f"❌ FAILED: Exclusive -> {e}")

if __name__ == "__main__":
    diagnose()
