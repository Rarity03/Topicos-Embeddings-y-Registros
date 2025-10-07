import os
contenido_txt = """Tipo:
Talla:
Color:
Temporada:
Genero:
Estilo:
Pais:
Marca:
Modelo:"""

directorio_base = "."

numero_de_carpetas = 15

for i in range(1, numero_de_carpetas + 1):
    nombre_carpeta = f"Imagen {i}"
    ruta_carpeta = os.path.join(directorio_base, nombre_carpeta)

    try:
        os.makedirs(ruta_carpeta, exist_ok=True)
        nombre_archivo = f"{nombre_carpeta}.txt"
        ruta_archivo = os.path.join(ruta_carpeta, nombre_archivo)
        with open(ruta_archivo, 'w', encoding='utf-8') as archivo:
            archivo.write(contenido_txt)
    except OSError as e:
        print(f"Error al procesar '{nombre_carpeta}': {e}")

print("\n¡Proceso completado")
