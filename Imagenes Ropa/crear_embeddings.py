import torch
import clip
import pandas as pd
from PIL import Image
import numpy as np
from pathlib import Path
import os

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)
print(f"Modelo cargado en el dispositivo: {device}")

def expandir_tallas(talla_str):
    if not isinstance(talla_str, str):
        return ""

    mapeo_tallas = {
        'XS': 'extra chica', 'S': 'chica', 'M': 'mediana', 'L': 'grande',
        'XL': 'extra grande', 'XXL': 'doble extra grande', 'XXXL': 'triple extra grande',
        'UNITALLA': 'unitalla'
    }
    
    tallas = [t.strip() for t in talla_str.split('|')]
    tallas_expandidas = [mapeo_tallas.get(t.upper(), t) for t in tallas]
    
    if len(tallas_expandidas) > 1:
        return ", ".join(tallas_expandidas[:-1]) + f" y {tallas_expandidas[-1]}"
    elif tallas_expandidas:
        return tallas_expandidas[0]
    return ""

def construir_descripcion(row):
    descripcion = []
    
    if pd.notna(row.get('Tipo')) and row['Tipo']:
        descripcion.append(f"Una prenda de tipo {row['Tipo']}")
    else:
        descripcion.append("Una prenda de ropa")
        
    if pd.notna(row.get('Talla')) and row['Talla']:
        tallas_desc = expandir_tallas(row['Talla'])
        if tallas_desc:
            descripcion.append(f"en talla {tallas_desc}")

    if pd.notna(row.get('Color')) and row['Color']:
        descripcion.append(f"de color {row['Color']}")

    if pd.notna(row.get('Genero')) and row['Genero'] and row['Genero'].lower() != 'unisex':
        descripcion.append(f"para {row['Genero'].lower()}")

    if pd.notna(row.get('Estilo')) and row['Estilo']:
        estilos = [e.strip() for e in str(row['Estilo']).split('|')]
        if len(estilos) > 1:
            estilos_str = ", ".join(estilos[:-1]) + f" y {estilos[-1]}"
            descripcion.append(f"con un estilo {estilos_str}")
        else:
            descripcion.append(f"con un estilo {estilos[0]}")

    if pd.notna(row.get('Marca')) and row['Marca']:
        marca_desc = f"de la marca {row['Marca']}"
        if pd.notna(row.get('Modelo')) and row['Modelo'] and "no especificado" not in row['Modelo'].lower():
            marca_desc += f", modelo {row['Modelo']}"
        if pd.notna(row.get('Pais')) and row['Pais']:
            marca_desc += f", originaria de {row['Pais']}"
        descripcion.append(marca_desc)
    
    return ". ".join(descripcion) + "."

def asignar_precio_realista(row):
    tipo_prenda = str(row.get('Tipo', '')).lower()
    
    precios_por_tipo = {
        'playera': [150, 600], 'camiseta': [150, 600], 'polo': [250, 800],
        'top': [120, 550], 'crop': [150, 600],

        'blusa': [250, 1200], 'camisa': [300, 1300], 'camisola': [200, 700],
        
        'sudadera': [400, 1800], 'hoodie': [450, 2000],
        'suéter': [350, 1700], 'sweater': [350, 1700], 'jersey': [350, 1700], 'cardigan': [400, 1800],

        'pantalón': [450, 2200], 'pantalon': [450, 2200], 'pants': [400, 1500], 'jean': [500, 2500],
        'short': [250, 800], 'bermuda': [300, 900],
        'legging': [200, 750],

        'falda': [300, 1500],
        'vestido': [500, 3500],

        'abrigo': [1200, 5000], 'chamarra': [800, 4500], 'chaqueta': [800, 4500], 'cazadora': [900, 4000],
        'gabardina': [1000, 4800], 'impermeable': [600, 2500], 'chubasquero': [500, 2000],
        'saco': [900, 4500], 'blazer': [850, 4200], 'tweed': [1000, 5000],
        'chaleco': [350, 1800], 'capa': [400, 2000],
        
        'conjunto': [700, 4000], 'chándal': [800, 3500], 'traje': [1500, 6000],
        'pijama': [300, 1200], 'mameluco': [300, 900], 'trusa': [100, 400],
        'mono': [400, 1600], 'corset': [300, 1200], 'kimono': [450, 1800],

        'zapato': [600, 3000], 'tenis': [700, 4000], 'bota': [800, 4500], 'sandalia': [300, 1500],

        'bolsa': [400, 3500], 'cinturón': [200, 1000], 'lentes': [250, 2000],
        'gorro': [150, 700], 'gorra': [200, 800],
        'bufanda': [180, 900], 'pashmina': [200, 1000],
        'guantes': [150, 600], 'calcetines': [80, 300], 'calceta': [80, 300], 'medias': [100, 400],
        'corbata': [250, 1200], 'moño': [150, 500],
    }
    
    for tipo_base, rango in precios_por_tipo.items():
        if tipo_base in tipo_prenda:
            return round(np.random.uniform(rango[0], rango[1]), 2)

    return round(np.random.uniform(300, 1500), 2)

def generar_embeddings(df):

    embeddings_list = []
    valid_indices = [] 

    for index, row in df.iterrows():
        ruta_imagen = row['Ruta_Imagen']
        descripcion_texto = construir_descripcion(row)
        
        try:
            if not os.path.exists(ruta_imagen):
                print(f"La imagen no existe en la ruta: {ruta_imagen}. Omitiendo fila {index}.")
                continue

            #Preprocesdo
            imagen = preprocess(Image.open(ruta_imagen)).unsqueeze(0).to(device)
            texto = clip.tokenize([descripcion_texto], truncate=True).to(device)

            with torch.no_grad():
                
                # Obtener embeddings del modelo
                image_features = model.encode_image(imagen)
                text_features = model.encode_text(texto)
                
                # Normalizar
                image_features /= image_features.norm(dim=-1, keepdim=True)
                text_features /= text_features.norm(dim=-1, keepdim=True)
                
                #Combinar promedio
                combined_embedding = (image_features + text_features) / 2
                
                # Añadir el embedding a la lista 
                embeddings_list.append(combined_embedding.cpu().numpy().flatten())
                valid_indices.append(index) 
                
                print(f"Procesada fila {index}: {row['Tipo']}")

        except Exception as e:
            print(f"ERROR al procesar la fila {index} ({ruta_imagen}): {e}")

    return np.array(embeddings_list), valid_indices


if __name__ == "__main__":
    df = pd.read_csv('dataset1.csv')
    embeddings, indices_validos = generar_embeddings(df)
    
    if embeddings.size > 0:
        np.save('embeddings_ropa.npy', embeddings)
        df_validos = df.loc[indices_validos].reset_index(drop=True)

        df_validos['price'] = df_validos.apply(asignar_precio_realista, axis=1)
        df_validos['stock'] = np.random.randint(0, 150, size=len(df_validos))

        df_validos.to_csv('metadata_ropa.csv', index_label='embedding_id')
        
        print(f"Se generaron y guardaron {len(embeddings)} embeddings.")
    else:
        print(f"\nNo se generaron embedding")