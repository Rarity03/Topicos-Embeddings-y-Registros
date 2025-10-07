from faker import Faker
import psycopg2
from psycopg2.extras import execute_values
from tqdm import tqdm
import random

DB_CONFIG = {
    "dbname": "ropa_db",
    "user": "postgres",
    "password": "12345",
    "host": "localhost",
    "port": "5434"
}

NUM_USERS_TO_GENERATE = 733_000
BATCH_SIZE = 10_000
NUM_FAVORITES_PER_USER = 5
NUM_ORDERS_PER_USER = 3
MAX_ITEMS_PER_ORDER = 5
PERCENT_USERS_COMMENTING = 0.1
NUM_COMMENTS_PER_USER = 4

fake = Faker()

def generate_users(conn, num_users, batch_size):
    print("Generando usuarios y credenciales...")
    with conn.cursor() as cur:
        cur.execute("SET session_replication_role = replica;")
        conn.commit()

        for _ in tqdm(range(0, num_users, batch_size), desc="Users"):
            users_batch = []
            for _ in range(batch_size):
                first_name = fake.first_name()
                second_name = fake.first_name() if random.random() < 0.5 else None
                first_lastname = fake.last_name()
                second_lastname = fake.last_name() if random.random() < 0.5 else None
                dob = fake.date_of_birth(minimum_age=18, maximum_age=70)
                created_at = fake.date_time_between(start_date='-2y', end_date='now')
                users_batch.append((first_name, second_name, first_lastname, second_lastname, dob, created_at))

            # Insertar usuarios y obtener sus IDs
            user_ids = execute_values(
                cur,
                "INSERT INTO Users (first_name, second_name, first_lastname, second_lastname, date_of_birth, created_at) VALUES %s RETURNING user_id",
                users_batch,
                fetch=True
            )
            user_ids = [row[0] for row in user_ids]

            # Generar credenciales asociadas
            creds_batch = []
            for uid in user_ids:
                try:
                    email = fake.unique.email()
                    password = fake.sha256(raw_output=False)
                    creds_batch.append((uid, email, password))
                except Exception: 
                    continue

            execute_values(
                cur,
                "INSERT INTO User_Credentials (user_id, email, password_hash) VALUES %s",
                creds_batch
            )
            conn.commit()
        
        fake.unique.clear() # Limpiar el historial de emails únicos

        cur.execute("SET session_replication_role = DEFAULT;")
        conn.commit()
    print("Usuarios generados correctamente")

def generate_addresses(conn, user_ids):
    print("Generando direcciones para los usuarios...")
    with conn.cursor() as cur:
        # Obtener usuarios que ya tienen dirección
        cur.execute("SELECT DISTINCT user_id FROM Addresses")
        users_with_address = {row[0] for row in cur.fetchall()}

        users_needing_address = [uid for uid in user_ids if uid not in users_with_address]
        
        if not users_needing_address:
            print("Todos los usuarios ya tienen una dirección")
            return

        addresses_batch = []
        for user_id in tqdm(users_needing_address, desc="Addresses"):
            addresses_batch.append((user_id, fake.street_name(), fake.building_number(), fake.city(), fake.state(), fake.country(), fake.postcode()))
        
        execute_values(cur, "INSERT INTO Addresses (user_id, street_name, number, city, state, country, postal_code) VALUES %s", addresses_batch)
        conn.commit()
    print(f"Se generaron {len(addresses_batch)} direcciones")

def generate_related_data(conn, user_ids, product_ids):
    if not user_ids or not product_ids:
        return

    with conn.cursor() as cur:
        # Generar Favoritos
        print("Generando favoritos...")
        favorites_batch = []
        for user_id in tqdm(user_ids, desc="Favorites"):
            products_for_user = set(random.choices(product_ids, k=NUM_FAVORITES_PER_USER))
            for product_id in products_for_user:
                favorites_batch.append((user_id, product_id))
                if len(favorites_batch) >= BATCH_SIZE:
                    execute_values(cur, "INSERT INTO Favorites (user_id, product_id) VALUES %s ON CONFLICT DO NOTHING", favorites_batch)
                    conn.commit()
                    favorites_batch = []
        if favorites_batch:
            execute_values(cur, "INSERT INTO Favorites (user_id, product_id) VALUES %s ON CONFLICT DO NOTHING", favorites_batch)
            conn.commit()
        print("Favoritos generados")

        #Generar Comentarios
        print("Generando comentarios...")
        users_who_comment = random.sample(user_ids, k=int(len(user_ids) * PERCENT_USERS_COMMENTING))
        comments_batch = []
        for user_id in tqdm(users_who_comment, desc="Comments"):
            products_to_comment = random.choices(product_ids, k=NUM_COMMENTS_PER_USER)
            for product_id in products_to_comment:
                text = fake.paragraph(nb_sentences=3)
                commented_at = fake.date_time_between(start_date='-1y', end_date='now')
                comments_batch.append((user_id, product_id, text, commented_at))
                if len(comments_batch) >= BATCH_SIZE:
                    execute_values(cur, "INSERT INTO Comments (user_id, product_id, text, commented_at) VALUES %s", comments_batch)
                    conn.commit()
                    comments_batch = []
        if comments_batch:
            execute_values(cur, "INSERT INTO Comments (user_id, product_id, text, commented_at) VALUES %s", comments_batch)
            conn.commit()
        print("Comentarios generados")

        #Generar Órdenes y sus Artículos
        print("Generando órdenes y artículos...")
        # Precios de productos
        cur.execute("SELECT product_id, price FROM Products")
        product_prices = {row[0]: row[1] for row in cur.fetchall()}
        
        #Direcciones de los usuarios 
        cur.execute("SELECT user_id, address_id FROM Addresses")
        user_addresses = {row[0]: row[1] for row in cur.fetchall()}

        for user_id in tqdm(user_ids, desc="Orders"):
            # Solo crear órdenes para usuarios que tienen una dirección
            address_id = user_addresses.get(user_id)
            if not address_id:
                continue

            for _ in range(random.randint(1, NUM_ORDERS_PER_USER)):
                num_items = random.randint(1, MAX_ITEMS_PER_ORDER)
                
                # Seleccionar productos para la orden
                products_in_order = random.choices(list(product_prices.keys()), k=num_items)
                
                # Insertar la orden
                order_date = fake.date_time_between(start_date='-1y', end_date='now')
                cur.execute(
                    "INSERT INTO Orders (user_id, address_id, status, order_date, total_price) VALUES (%s, %s, %s, %s, %s) RETURNING order_id",
                    (user_id, address_id, random.choice(['completed', 'shipped', 'pending']), order_date, 0)
                )
                order_id = cur.fetchone()[0]

                # Crear los artículos de la orden
                order_items_batch = []
                for product_id in products_in_order:
                    quantity = random.randint(1, 3)
                    price_at_purchase = product_prices.get(product_id, 0)
                    order_items_batch.append((order_id, product_id, quantity, price_at_purchase))
                
                # Insertar los artículos de la orden
                if order_items_batch:
                    execute_values(cur, "INSERT INTO OrderItems (order_id, product_id, quantity, price_at_purchase) VALUES %s", order_items_batch)
            
            # El trigger 'trigger_update_order_total' debería actualizar el total_price automáticamente.
            conn.commit()
        print("Órdenes generadas")

def main():
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            print("Conexión a la base de datos exitosa.")
            
            # Generar Usuarios
            generate_users(conn, NUM_USERS_TO_GENERATE, BATCH_SIZE)

            #Crear relaciones
            print("Obteniendo IDs de usuarios y productos existentes...")
            with conn.cursor() as cur:
                cur.execute("SELECT user_id FROM Users;")
                all_user_ids = [row[0] for row in cur.fetchall()]
                generate_addresses(conn, all_user_ids)

                cur.execute("SELECT user_id FROM Users;")
                user_ids = [row[0] for row in cur.fetchall()]
                
                cur.execute("SELECT product_id FROM Products;")
                product_ids = [row[0] for row in cur.fetchall()]
            
            print(f"Encontrados {len(user_ids)} usuarios y {len(product_ids)} productos.")

            # Generar datos relacionados
            generate_related_data(conn, user_ids, product_ids)

        print("\nGeneración de datos masivos completada")

    except psycopg2.OperationalError as e:
        print(f"Error de conexión a la base de datos: {e}")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    main()
