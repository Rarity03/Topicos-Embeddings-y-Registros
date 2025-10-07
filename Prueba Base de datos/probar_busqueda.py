import torch
import clip
from PIL import Image
import sys
import json


print("Cargando el modelo CLIP...", file=sys.stderr)
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)
print(f"Modelo cargado en el dispositivo: {device}", file=sys.stderr)

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
        return embedding.cpu().numpy().flatten().tolist()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python probar_busqueda.py <texto|imagen> \"<consulta|ruta>\"", file=sys.stderr)
        sys.exit(1)

    mode = sys.argv[1]
    query = sys.argv[2]
    
    query_embedding = None
    if mode == "texto":
        print(f"Generando embedding para el texto: '{query}'", file=sys.stderr)
        query_embedding = get_query_embedding(query_text=query)
    elif mode == "imagen":
        print(f"Generando embedding para la imagen: '{query}'", file=sys.stderr)
        try:
            query_embedding = get_query_embedding(image_path=query)
        except FileNotFoundError:
            print(f"Error: No se encontró la imagen en la ruta: {query}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Error: Modo '{mode}' no reconocido. Usa 'texto' o 'imagen'.", file=sys.stderr)
        sys.exit(1)

    if query_embedding is not None:
        # Imprimir el resultado como un JSON string a stdout
        # Node.js leerá esta salida.
        print(json.dumps(query_embedding))