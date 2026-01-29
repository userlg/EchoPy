import sounddevice as sd
import numpy as np
import time
import sys

# Answers for the user
print("1. BUSCANDO DISPOSITIVOS 'LOOPBACK' POR NOMBRE...")
devices = sd.query_devices()
loopback_names = [f"[{i}] {d['name']}" for i, d in enumerate(devices) if "loopback" in d['name'].lower()]
if loopback_names:
    for name in loopback_names: print(f"   ENCONTRADO: {name}")
else:
    print("   NO se encontraron dispositivos con 'loopback' en el nombre.")

print("\n2. PROBANDO CAPTURA RMS (Buscando señal activa)...")

def test_idx(idx, desc, is_wasapi=False):
    print(f"\nProbando [{idx}] {desc}...")
    try:
        extra = None
        if is_wasapi:
            # Intentar inyectar flag de loopback manualmente
            class Settings: pass
            extra = Settings()
            extra._streaminfo = sd._ffi.new('PaWasapiStreamInfo*', {
                'size': 24, # PaWasapiStreamInfo size
                'hostApiType': 13, # paWASAPI
                'version': 1,
                'flags': 256 # paWinWasapiLoopback
            })
        
        # Intentar 2 canales
        with sd.InputStream(device=idx, channels=2, samplerate=48000, extra_settings=extra) as s:
            print("   Stream abierto. Midiendo...")
            time.sleep(1.0) # Estabilizar
            data, _ = s.read(1024)
            rms = np.sqrt(np.mean(data**2))
            print(f"   RMS DETECTADO: {rms:.8f}")
            if rms > 0.0001:
                print("   >>> SEÑAL ACTIVA <<<")
                return True
    except Exception as e:
        print(f"   ERROR: {e}")
    return False

# Probar SyncMaster (sus dos versiones: MME index 4 con inputs, WASAPI index 12 render)
found_active = False
if test_idx(12, "SyncMaster WASAPI (Loopback Flag 256)", is_wasapi=True): found_active = True
if not found_active and test_idx(4, "SyncMaster MME (Native Input)"): found_active = True
if not found_active and test_idx(2, "Stereo Mix MME"): found_active = True

print("\n3. TARJETA DE SONIDO DETECTADA:")
# Identificar la tarjeta por el dispositivo por defecto o el nombre recurrente
try:
    default_out = sd.query_devices(sd.default.device[1])['name']
    print(f"   Salida por defecto: {default_out}")
except:
    print("   No se pudo identificar la tarjeta.")

print("\n--- TEST FINALIZADO ---")
