import sounddevice as sd
import numpy as np

def test_device(idx):
    try:
        info = sd.query_devices(idx)
        print(f"\nTesting Device {idx}: {info['name']}")
        print(f"HostAPI: {sd.query_hostapis(info['hostapi'])['name']}")
        print(f"Max Inputs: {info['max_input_channels']}")
        print(f"Max Outputs: {info['max_output_channels']}")
        
        # Try loopback settings
        try:
            settings = sd.WasapiSettings(loopback=True)
            print("WasapiSettings(loopback=True) is available.")
        except Exception as e:
            settings = None
            print(f"WasapiSettings(loopback=True) NOT available: {e}")

        # Try opening stream with different channel counts
        for chans in [2, 1, info['max_output_channels']]:
            if chans <= 0: continue
            try:
                with sd.InputStream(device=idx, channels=chans, samplerate=info['default_samplerate'], extra_settings=settings):
                    print(f"  SUCCESS with channels={chans}")
                    return True
            except Exception as e:
                print(f"  FAILED with channels={chans}: {e}")
        return False
    except Exception as e:
        print(f"Error querying device {idx}: {e}")
        return False

# Test index 12 (SyncMaster)
test_device(12)
# Test index 4 (Fallback)
test_device(4)
