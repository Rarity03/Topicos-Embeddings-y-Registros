import torch
import clip
import psycopg
from pgvector.psycopg import register_vector
from PIL import Image
import numpy as np
import sys
import json

DB_CONFIG = {
    "dbname": "ropa_db",
    "user": "postgres", 
    "password": "12345",
    "host": "localhost",
    "port": "5434" 
}

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

def get_query_embedding(query_text=None, image_path=None):
    with torch.no_grad():
        if image_path:
            image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
            embedding = model.encode_image(image)
        elif query_text:
            text = clip.tokenize([query_text], truncate=True).to(device)
            embedding = model.encode_text(text)
        else:
            return None

        embedding /= embedding.norm(dim=-1, keepdim=True)
        return embedding.cpu().numpy().flatten()
        return embedding.cpu().numpy().flatten().tolist()

def find_similar_products(query_embedding, threshold=0.5, limit=20):
    with psycopg.connect(**DB_CONFIG) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    p.name, 
                    p.image_url, 
                    1 - (pv.embedding <=> %s) AS similarity
                FROM Products p
                JOIN ProductVectors pv ON p.product_id = pv.product_id
                WHERE 1 - (pv.embedding <=> %s) > %s
                ORDER BY similarity DESC
                LIMIT %s;
                """,
                (query_embedding, query_embedding, threshold, limit)
            )
            results = cur.fetchall()
            return results

if __name__ == "__main__":
    args = [arg for arg in sys.argv if not arg.startswith('--')]
    
    threshold = 0.5 
    if "--threshold" in sys.argv:
        try:
            threshold_index = sys.argv.index("--threshold") + 1
            threshold = float(sys.argv[threshold_index])
        except (IndexError, ValueError):
            print("Error: El valor de --threshold debe ser un número (ej: 0.6). Usando el valor por defecto 0.5.")

    if len(args) < 3:
        print("\nUso incorrecto. Elige un modo y proporciona una consulta.")
        print("Búsqueda por texto: python probar_busqueda.py texto \"tu consulta aquí\"")
        print("Búsqueda por imagen: python probar_busqueda.py imagen \"ruta/a/tu/imagen.webp\"")
        print("Para usar un umbral: python probar_busqueda.py texto \"Falda\" --threshold 0.6")
    if len(sys.argv) != 3:
        print("Uso: python probar_busqueda.py <texto|imagen> \"<consulta|ruta>\"", file=sys.stderr)
        sys.exit(1)

    mode = args[1]
    query = args[2]
    mode = sys.argv[1]
    query = sys.argv[2]
    
    query_embedding = None
    if mode == "texto":
        print(f"\nBuscando productos similares a: '{query}'")
        print(f"Generando embedding para el texto: '{query}'", file=sys.stderr)
        query_embedding = get_query_embedding(query_text=query)
    elif mode == "imagen":
        print(f"\nBuscando productos similares a la imagen: '{query}'")
        print(f"Generando embedding para la imagen: '{query}'", file=sys.stderr)
        try:
            query_embedding = get_query_embedding(image_path=query)
        except FileNotFoundError:
            print(f"Error: No se encontró la imagen en la ruta: {query}")
            print(f"Error: No se encontró la imagen en la ruta: {query}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Error: Modo '{mode}' no reconocido. Usa 'texto' o 'imagen'.")
        print(f"Error: Modo '{mode}' no reconocido. Usa 'texto' o 'imagen'.", file=sys.stderr)
        sys.exit(1)

    if query_embedding is not None:
        similar_products = find_similar_products(query_embedding, threshold=threshold)
        
        print("\nResultados de la Búsqueda")
        if not similar_products:
            print("No se encontraron productos similares.")
        else:
            for i, (name, image_url, similarity) in enumerate(similar_products):
                print(f"{i+1}. Nombre: {name} (Similitud: {similarity:.4f})")
                print(f"   Imagen: {image_url}\n")
        print(json.dumps(query_embedding))