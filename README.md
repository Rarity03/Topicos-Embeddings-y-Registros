# Cosas a corregir y faltantes

## Embeddings:
- [ ] Añadir las imágenes de las personas faltantes (imágenes de DRIVE), formatear y agregar sus metdatos a los existentes.
- [ ] Crear los nuevos embeddings con las nuevas imágenes.
- [ ] A los metadatos resultantes de la creación de los embeddings agregarles su precio y stock en dos columnas al final.

---

## Creación de registros:
- [ ] Modificar el apartado de creación de comentarios para crear comentarios coherentes (en su mayoría y en inglés, pues los nombres y las direcciones se están generando en inglés, así se mantendrá la coherencia).
- [ ] Modificar la salida del archivo para que en lugar de ingresar los datos a la base, nos genere los datos para cargarlos directamente desde un `.txt` con queries.

---

# Proceso de obtención de Embeddings

## 1. Elaboración de Embeddings

Para la elaboración de los embeddings se utilizaron imágenes de ropa reales. Estas imágenes, junto con su descripción (incluyendo tipo, talla, color, temporada, género, estilo, país, marca y modelo), fueron obtenidas de distintas tiendas en línea. Una vez recopilados, todos los archivos se agruparon en un directorio principal para su tratamiento.

El proceso se dividió en los siguientes pasos:

### 1.1. Conversión de Imágenes a formato .webp (`convertir_imagenes.py`)

Para optimizar el almacenamiento y la velocidad de carga, se estandarizaron todas las imágenes al formato `.webp`. Para ello se utilizó el script `convertir_imagenes.py`.

**Funcionamiento del script:**  
El script recorre de manera recursiva todos los directorios y subdirectorios a partir de su ubicación. Busca archivos de imagen con extensiones comunes (`.jpg`, `.png`, `.gif`, etc.) y los convierte a formato `.webp` con una calidad optimizada. 

### 1.2. Estandarización de Nombres de Archivos (`renombrar_archivos.py`)

Para mantener una consistencia y evitar errores en el tratamiento posterior, se formateó el nombre de cada imagen y su archivo de texto descriptivo. Esta tarea se realizó con `renombrar_archivos.py`.  
La estructura esperada es una carpeta por cada producto, conteniendo una imagen y un archivo `.txt`.

**Funcionamiento del script:**  
Este script recorre cada subdirectorio en la carpeta donde se ejecuta. Dentro de cada uno, identifica el archivo de imagen y el archivo de texto. Luego, renombra ambos archivos utilizando el nombre de la carpeta contenedora como nombre base.  
Por ejemplo, si una carpeta se llama `sudadera_roja_nike`, la imagen y el texto dentro se renombrarán a `sudadera_roja_nike.webp` y `sudadera_roja_nike.txt` respectivamente.

### 1.3. Procesamiento y Estandarización de Datos (`procesar_datos.py`)

El script `procesar_datos.py` se encarga de leer todos los archivos `.txt`, limpiar y estandarizar la información, y consolidar todo en un único archivo CSV para su uso posterior.

**Funcionamiento del script:**  
1. **Recorre y lee:** El script busca todos los archivos `.txt` en el directorio y sus subcarpetas.  
2. **Extrae y normaliza:** Para cada archivo, extrae la información clave-valor (ej: `Talla: Mediana`). Aplica funciones de limpieza para normalizar tanto las claves (ej: `genero` o `Género` se convierten en `Genero`) como los valores (ej: `chico`, `ch`, `pequeño` se estandarizan a `S`). También maneja múltiples valores para un mismo atributo, separándolos con `|`.  
3. **Asocia la imagen:** Identifica la ruta de la imagen `.webp` correspondiente al archivo de texto.  
4. **Genera un CSV:** Toda la información limpia y estructurada de todas las prendas se guarda en un único archivo llamado `dataset_ropa.csv`, donde cada fila corresponde a un producto y cada columna a un atributo.

### 1.4. Generación de Embeddings con CLIP (`crear_embeddings.py`)

Para la obtención de los embeddings se utilizó el modelo multimodal **CLIP** (Contrastive Language-Image Pre-Training) de OpenAI, que es capaz de entender tanto texto como imágenes.

**Funcionamiento del script:**  

#### 1. Carga del modelo

```python
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)
```

- `clip.load(...)`: Carga un modelo pre-entrenado de CLIP.  
- `"ViT-B/32"`: Especifica la versión del modelo (Vision Transformer base).  
- `model`: Contiene la red neuronal con sus codificadores de imagen y texto.  
- `preprocess`: Función auxiliar que transforma las imágenes al formato que el modelo espera.

#### 2. Funciones para la construcción de descripciones

**`expandir_tallas(talla_str)`**  
Convierte tallas abreviadas (ej. `"S | M"`) a descripciones completas (ej. `"chica y mediana"`). Usa un diccionario que mapea abreviaturas a nombres completos.

**`construir_descripcion(row)`**  
Por cada prenda (cada row del archivo CSV), construye una oración completa y coherente uniendo sus atributos. Inicia con una base como "Una prenda de ropa" o "Una prenda de tipo Sudadera" y de forma condicional, va añadiendo fragmentos si la información existe: "...en talla mediana", "...de color rojo", "...para hombre". Al final, une todas las partes para formar una descripción completa
Ejemplo de salida:  
> "Una prenda de tipo Sudadera, en talla mediana y grande, de color rojo, para hombre, con estilo casual, de la marca Nike, modelo Air, originaria de Vietnam."

#### 3. Generación de los embeddings

```python
def generar_embeddings(df):
    embeddings_list = []
    valid_indices = [] 
    
    for index, row in df.iterrows(): # 1. Iteración
        # ...
        try:
            # 2. Preprocesamiento
            imagen = preprocess(Image.open(ruta_imagen)).unsqueeze(0).to(device)
            texto = clip.tokenize([descripcion_texto], truncate=True).to(device)

            with torch.no_grad(): # 3. Inferencia
                # 4. Obtención de embeddings separados
                image_features = model.encode_image(imagen)
                text_features = model.encode_text(texto)
                
                # 5. Normalización
                image_features /= image_features.norm(dim=-1, keepdim=True)
                text_features /= text_features.norm(dim=-1, keepdim=True)
                
                # 6. Combinación
                combined_embedding = (image_features + text_features) / 2
                
                # 7. Almacenamiento
                embeddings_list.append(combined_embedding.cpu().numpy().flatten())
                valid_indices.append(index)
        # ...
    return np.array(embeddings_list), valid_indices
```
 
- **Iteración:** Recorre cada fila del DataFrame.  
- **Preprocesamiento:** Para cada prenda, prepara la imagen (usando la función preprocess) y el texto (usando clip.tokenize para convertirlo en números que el modelo entienda).
- **Inferencia:** Calcula los embeddings sin entrenar el modelo (`torch.no_grad()`).  
- **model.encode_image(imagen):** Pasa la imagen preprocesada por el codificador visual de CLIP para obtener el embedding de la imagen (image_features).
- **model.encode_text(texto):** Pasa el texto "tokenizado" por el codificador de lenguaje para obtener el embedding del texto (text_features).
- **Normalización:** Ajusta los vectores a una magnitud unitaria.  
- **Combinación:** Promedia los embeddings de imagen y texto.  
- **Almacenamiento:** Convierte el resultado en un arreglo NumPy para su exportación.

---

## Descripción de CLIP

CLIP es un modelo de red neuronal de código abierto desarrollado por OpenAi. Su caracteriztica principal a diferencia de otros modelos es que no asocia estrictamente imagenes con un concepto en especifico (ejem. Imagen de perro con el concepto "perro"), sino que asocia las imagenes con el texto que las describe y el contexto de dicho texto e imagen, es decir, no se centra en el "perro", sino en la relación que tendra esa imagen del perro con una posible descripción que lo distinga (ejem. Imagen de un perro en un sofa, descripción: "El mejor amigo del hombre hechando una siesta").

### Aprendizaje Contrastivo

CLIP utiliza **aprendizaje contrastivo**: Aprende a determinar qué texto describe mejor una imagen, maximizando la similitud de pares correctos (imagen-texto) y minimizando la de pares incorrectos. En lugar de aprender a etiquetar una imagen con una categoría fija (ej. "gato" o "perro"), aprende a determinar qué texto, de un conjunto de opciones, es el que mejor describe a una imagen.

Fue entrenado con **400 millones de pares imagen-texto** obtenidos de internet.

### Componentes del modelo

1. **Codificador de Imágenes:** Es una red neuronal que toma una imagen como entrada y la convierte en una representación numérica vectorial. Este vector captura las características de la imagen.
2. **Codificador de Texto:** Es un transformador de lenguaje que toma una descripción textual como entrada y también la convierte en un embedding vectorial de la misma dimensión que el de la imagen.

Durante el entrenamiento:  
- Se procesan N pares (imagen, texto).  
- Por ejemplo, los 32 textos y las 32 imágenes son procesados por sus respectivos codificadores para obtener 32 embeddings de texto y 32 embeddings de imagen.
- Posteriormente el modelo calcula la similitud (usando la similitud del coseno) entre cada embedding de imagen y todos los embeddings de texto del lote, creando una matriz de N x N (en este caso, 32x32) con todas las posibles puntuaciones de similitud.
- El objetivo del entrenamiento es maximizar la similitud de los pares correctos (la imagen i con el texto i) y, al mismo tiempo, minimizar la similitud de los pares incorrectos (la imagen i con cualquier otro texto j).

### Aprendizaje Zero-Shot

CLIP puede usarse para tareas no vistas durante su entrenamiento (*zero-shot*).  
- Se definen descripciónes textuales para cada posible categoria de objetos que se introduciran al modelo.
- El modelo CLIP recibe la imagen que se clasificara y todos sus posibles textos descriptivos.
- El modelo convierte tanto el texto como la imagen en embeddings y luego calcula la similitud del coseno entre el mebeddings de la imagen y cada uno de los embeddings de texto.
- La descripción textual que obtenga la puntuación de similitud mas alta es la predicción del modelo para esa imagen.

---
