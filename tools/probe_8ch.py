
import sounddevice as sd
import sys

def diagnose():
    print("--- 8-Channel Surround Probe ---")
    i = 12
    try:
        settings = sd.WasapiSettings()
        settings._streaminfo.flags |= 256 # Loopback
        
        # Testing 8 channels (7.1 surround)
        stream = sd.InputStream(
            device=i, 
            channels=8, 
            samplerate=48000, 
            extra_settings=settings
        )
        stream.start()
        print("✅ SUCCESS: Opened SyncMaster with 8 channels!")
        stream.stop()
        stream.close()
    except Exception as e:
        print(f"❌ FAILED: 8-channel -> {e}")

if __name__ == "__main__":
    diagnose()
