import os
import csv
import re
import unicodedata
from pathlib import Path

def limpiar_valor(valor, clave):

    # Elimina paréntesis
    valor = re.sub(r'\(.*?\)', '', valor).strip()

    if clave == 'Genero':
        v_lower = valor.lower()
        if any(g in v_lower for g in ["hombre", "masculino", "niño"]): return "Hombre"
        if any(g in v_lower for g in ["mujer", "femenino", "niña"]): return "Mujer"
        if "unisex" in v_lower: return "Unisex"

    if clave == 'Talla':
        def normalizar_talla(talla_str):
            t_lower = talla_str.lower().strip()
            
            if t_lower in ["chico", "chica", "ch", "s", "niña pequeña", "niño pequeño", "niña", "niño", "pequeña", "pequeño", "niños", "niñas"]:
                return "S"
            if t_lower in ["mediano", "mediana", "m", "regular", "jovenes", "jóvenes"]:
                return "M"
            if t_lower in ["grande", "gde", "g", "l"]:
                return "L"
            if "extra grande" in t_lower or t_lower in ["eg", "extragrande", "xl", "2xl", "3xl", "4xl"]:
                if "2" in t_lower or "xxl" in t_lower: return "XXL"
                if "3" in t_lower or "xxxl" in t_lower: return "XXXL"
                if "4" in t_lower or "xxxxl" in t_lower: return "4XL"
                return "XL"
            if "extra chico" in t_lower or t_lower in ["ech", "extrachico", "xs"]:
                return "XS"
            if "unica" in t_lower or "única" in t_lower or "unitalla" in t_lower or "one size" in t_lower:
                return "UNITALLA"
            match_num = re.match(r'^\d+(\.\d+)?', t_lower)
            if match_num and 'cm' in t_lower:
                numero = match_num.group(0)
                return f"{numero.upper()} CM"
            elif match_num:
                return match_num.group(0).upper()
            return talla_str.upper()

        items = re.split(r'[/,x,–-—,y,Y,X,]', valor)
        normalized_items = [normalizar_talla(item) for item in items if item.strip()]
        valor = ' | '.join(list(dict.fromkeys(normalized_items)))
    elif clave == 'Temporada':
        items = re.split(r'[/,x,–-—,y,Y,X,]', valor)
        cleaned_items = [item.strip().capitalize() for item in items if item.strip()]
        valor = ' | '.join(cleaned_items)
    elif clave == 'Estilo':
        items = re.split(r'[/,x,–-—,y,Y,X,]', valor)
        cleaned_items = [item.strip().capitalize() for item in items if item.strip()]
        valor = ' | '.join(cleaned_items)
    else:
        valor = re.split(r'[/,x,–-—,y,Y,X,\s]{2,}', valor)[0].strip()
    if valor.lower() in ["no especificado", "no se especifica", "genérico", "no aparece", "none", ""]:
        return ""
    
    return valor.strip()

def normalizar_clave(clave):
    nfkd_form = unicodedata.normalize('NFD', clave.lower().strip())
    clave_sin_acentos = "".join([c for c in nfkd_form if not unicodedata.combining(c)])

    if "tipo" in clave_sin_acentos: return "Tipo"
    if "talla" in clave_sin_acentos: return "Talla"
    if "color" in clave_sin_acentos: return "Color"
    if "temporada" in clave_sin_acentos: return "Temporada"
    if "genero" in clave_sin_acentos:
        return "Genero"
    if "estilo" in clave_sin_acentos:
        return "Estilo"
    if "pais" in clave_sin_acentos:
        return "Pais"
    if "marca" in clave_sin_acentos:
        return "Marca"
    if "modelo" in clave_sin_acentos:
        return "Modelo"
    return clave.capitalize()


def encontrar_imagen(ruta_txt_obj):
    directorio = ruta_txt_obj.parent
    nombre_base = ruta_txt_obj.stem 
    ruta_webp = directorio / f"{nombre_base}.webp"
    if ruta_webp.is_file():
        return str(ruta_webp)
    return "No encontrada" 

def procesar_archivos_txt(directorio_raiz, archivo_csv_salida):
    cabeceras = [
        'Tipo', 'Talla', 'Color', 'Temporada', 'Genero', 'Estilo',
        'Pais', 'Marca', 'Modelo', 'Ruta_Imagen'
    ]
    datos_ropa = []

    print(f"Iniciando")

    for ruta_actual, carpetas, archivos in os.walk(directorio_raiz):
        for archivo in archivos:
            if archivo.lower().endswith('.py'):
                continue

            if archivo.lower().endswith('.txt'):
                ruta_txt_obj = Path(ruta_actual) / archivo
                ruta_txt = str(ruta_txt_obj)

                info_prenda = {}
                
                try:
                    with open(ruta_txt, 'r', encoding='utf-8') as f:
                        for linea in f:
                            match = re.match(r'([^:,]+)\s*[:,]\s*(.*)', linea)
                            if match:
                                clave, valor = match.groups()
                                clave_normalizada = normalizar_clave(clave)
                                if clave_normalizada in cabeceras:
                                    info_prenda[clave_normalizada] = limpiar_valor(valor, clave_normalizada)
        
                    info_prenda['Ruta_Imagen'] = encontrar_imagen(ruta_txt_obj)
                    if not info_prenda.get('Genero'):
                        info_prenda['Genero'] = 'Unisex'
                    if len(info_prenda) > 1: 
                        datos_ropa.append(info_prenda)
                        print(f"Procesado: {ruta_txt}")
                except Exception as e:
                    print(f"Error al procesar el archivo '{ruta_txt}': {e}")
    if not datos_ropa:
        print("No se encontraron datos para procesar")
        return

    try:
        with open(archivo_csv_salida, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=cabeceras, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(datos_ropa)
        print(f"\nDatos guardados en '{archivo_csv_salida}'")
    except IOError as e:
        print(f"Error al escribir el archivo CSV: {e}")


if __name__ == "__main__":
    directorio_base = '.' 
    archivo_salida = 'dataset_ropa.csv'
    procesar_archivos_txt(directorio_base, archivo_salida)
