from PIL import Image
import os

png_path = "resources/favicon.png"
ico_path = "resources/favicon.ico"

if os.path.exists(png_path):
    img = Image.open(png_path)
    img.save(ico_path, format='ICO', sizes=[(256, 256)])
    print(f"Búsqueda implacable: {ico_path} generado.")
else:
    print("Error: No se encontró el png.")
