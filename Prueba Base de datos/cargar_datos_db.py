import pandas as pd
import numpy as np
import psycopg
from pgvector.psycopg import register_vector

DB_CONFIG = {
    "dbname": "ropa_db",
    "user": "postgres", 
    "password": "12345",
    "host": "localhost",
    "port": "5434" 
}

def cargar_datos():
    try:
        df_metadata = pd.read_csv('metadata_ropa.csv')
        embeddings = np.load('embeddings_ropa.npy')

        if len(df_metadata) != len(embeddings):
            print("Error: El número de filas en metadata y el número de embeddings no coinciden.")
            return

    except FileNotFoundError as e:
        print(f"No se encontró el archivo {e.filename}")
        return

    with psycopg.connect(**DB_CONFIG) as conn:
        print("Conexión a la base de datos exitosa.")
        register_vector(conn)

        with conn.cursor() as cur:
            for index, row in df_metadata.iterrows():
                embedding = embeddings[index]
                cleaned_row = row.where(pd.notna(row), None)

                try:
                    with conn.transaction():
                        cur.execute(
                            """
                            INSERT INTO Products (name, tipo, size, model, color, season, style, brand, genre, origin_country, image_url, price, stock)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING product_id;
                            """,
                            (
                                cleaned_row['Tipo'], cleaned_row['Tipo'], cleaned_row['Talla'], cleaned_row['Modelo'], cleaned_row['Color'],
                                cleaned_row['Temporada'], cleaned_row['Estilo'], cleaned_row['Marca'], cleaned_row['Genero'],
                                cleaned_row['Pais'], cleaned_row['Ruta_Imagen'], 0.00, 0 
                            )
                        )
                        product_id = cur.fetchone()[0]
                        cur.execute(
                            "INSERT INTO ProductVectors (product_id, embedding) VALUES (%s, %s);",
                            (product_id, embedding)
                        )
                    
                    print(f"Insertado producto ID: {product_id} - {cleaned_row['Tipo']}")

                except Exception as e:
                    print(f"Error al insertar la fila {index}: {e}")

    print("\nCarga completada")

if __name__ == "__main__":
    cargar_datos()

