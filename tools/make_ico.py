import struct
import os

def create_ico_from_png(png_path, ico_path):
    if not os.path.exists(png_path):
        print(f"Error: {png_path} no existe.")
        return

    with open(png_path, 'rb') as f:
        png_data = f.read()

    # ICO Header: 0, 1 (icon), 1 (number of images)
    header = struct.pack('<HHH', 0, 1, 1)
    
    # Entry: width (0 for 256), height (0 for 256), colors (0), reserved (0), planes (1), bpp (32), size, offset
    width = 0 # 256
    height = 0 # 256
    ico_entry = struct.pack('<BBBBHHII', width, height, 0, 0, 1, 32, len(png_data), 6 + 16)

    with open(ico_path, 'wb') as f:
        f.write(header)
        f.write(ico_entry)
        f.write(png_data)
    
    print(f"Icono generado: {ico_path}")

create_ico_from_png("resources/favicon.png", "resources/favicon.ico")
