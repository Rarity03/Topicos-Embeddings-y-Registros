import os
from pathlib import Path

def renombrar_archivos_en_carpeta(directorio, nombre_base):
    extensiones_imagen = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp')
    archivos_en_dir = [f for f in os.listdir(directorio) if os.path.isfile(os.path.join(directorio, f)) and f != "renombrar_archivos.py"]
    
    archivo_txt = next((f for f in archivos_en_dir if f.lower().endswith('.txt')), None)
    archivo_imagen = next((f for f in archivos_en_dir if f.lower().endswith(extensiones_imagen)), None)
    
    if not archivo_txt or not archivo_imagen:
        return

    extension_img = os.path.splitext(archivo_imagen)[1]
    nuevo_nombre_txt = f"{nombre_base}.txt"
    nuevo_nombre_img = f"{nombre_base}{extension_img}"

    if archivo_txt == nuevo_nombre_txt and archivo_imagen == nuevo_nombre_img:
        print(f"Archivos en '{directorio}' ya están correctamente nombrados.\n")
        return

    ruta_original_txt = os.path.join(directorio, archivo_txt)
    ruta_nueva_txt = os.path.join(directorio, nuevo_nombre_txt)
    ruta_original_img = os.path.join(directorio, archivo_imagen)
    ruta_nueva_img = os.path.join(directorio, nuevo_nombre_img)

    try:
        temp_txt_path = ruta_original_txt + ".tmp"
        temp_img_path = ruta_original_img + ".tmp"
        os.rename(ruta_original_txt, temp_txt_path)
        os.rename(ruta_original_img, temp_img_path)

        os.rename(temp_txt_path, ruta_nueva_txt)
        os.rename(temp_img_path, ruta_nueva_img)
        print(f"Archivos renombrados en '{directorio}'.\n")
    except OSError as e:
        print(f"Error al renombrar en '{directorio}': {e}\n")


if __name__ == "__main__":
    directorio_actual = os.getcwd()
    print(f"Iniciando proceso de renombrado\n")
    
    for nombre_item in os.listdir(directorio_actual):
        ruta_item = os.path.join(directorio_actual, nombre_item)
        
        if os.path.isdir(ruta_item):
            nombre_base = Path(ruta_item).name
            renombrar_archivos_en_carpeta(ruta_item, nombre_base)

    print("Proceso de renombrado completado")
