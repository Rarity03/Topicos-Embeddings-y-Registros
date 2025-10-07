import os
from pathlib import Path
from PIL import Image

def convertir_imagenes_a_webp(directorio_raiz, borrar_originales=False):

    extensiones_soportadas = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.avif')
    
    print(f"Iniciando conversión")
    
    imagenes_convertidas = 0
    errores = 0
    
    for ruta_actual, _, archivos in os.walk(directorio_raiz):
        for archivo in archivos:
            if not archivo.lower().endswith(extensiones_soportadas):
                continue

            ruta_original_obj = Path(ruta_actual) / archivo
            nombre_base = ruta_original_obj.stem
            ruta_webp_obj = ruta_original_obj.with_name(nombre_base + '.webp')

            if ruta_webp_obj.exists():
                print(f"Ya existe una versión .webp")
                if borrar_originales:
                    try:
                        os.remove(ruta_original_obj)
                    except OSError as e:
                        print(f"Error al borrar")
                continue

            try:
                with Image.open(ruta_original_obj) as img:
                    if img.mode not in ('RGB', 'RGBA'):
                        img = img.convert('RGB')
                    img.save(ruta_webp_obj, 'webp', quality=85, optimize=True)
                    imagenes_convertidas += 1
                if borrar_originales:
                    os.remove(ruta_original_obj)

            except Exception as e:
                print(f"Error al convertir")
                errores += 1
    
    print(f"\nImágenes convertidas: {imagenes_convertidas}")
    print(f"\nErrores durante la conversión: {errores}")


if __name__ == "__main__":
    directorio_base = '.'
    
    confirmacion = input("¿Deseas borrar los archivos de imagen originales después de la conversión? (s/n): ").lower()
    eliminar = confirmacion == 's'
    
    convertir_imagenes_a_webp(directorio_base, borrar_originales=eliminar)