from werkzeug.security import generate_password_hash
from app import get_db_connection
import mysql.connector

# Fungsi untuk membuat database jika belum ada
def create_database_if_not_exists():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS restaurant_db")
        cursor.execute("USE restaurant_db")
        conn.commit()
        print("Database 'restaurant_db' siap digunakan!")
        conn.close()
    except Exception as e:
        print(f"Error membuat database: {e}")
        raise

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="restaurant_db"
    )



# def create_admin():
#     conn = get_db_connection()
#     admin = conn.execute(
#         "SELECT * FROM users WHERE role = 'admin'"
#     ).fetchone()

#     if not admin :
#         conn.execute(
#             'INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)',
#             ('admin', generate_password_hash('admin123'), 'admin@restaurant.com', 'admin')
#         )
#         conn.commit()
#     conn.close()
    


 # membuat akuun admin 
def create_admin():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE role = %s", ('admin',))
    admin = cursor.fetchone()

    if not admin:
        cursor.execute(
            "INSERT INTO users (username, password, email, role) VALUES (%s, %s, %s, %s)",
            (
                'admin',
                generate_password_hash('admin123'),
                'admin@restaurant.com',
                'admin'
            )
        )
        conn.commit()
        print("Admin berhasil dibuat!")
    conn.close()


# def init_db():
#     conn = get_db_connection()

#     conn.executescript('''
#         CREATE TABLE IF NOT EXISTS users (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             username TEXT UNIQUE NOT NULL,
#             password TEXT NOT NULL,
#             email TEXT,
#             role TEXT NOT NULL,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         );

#         CREATE TABLE IF NOT EXISTS menu (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             name TEXT NOT NULL,
#             category TEXT NOT NULL,
#             price INTEGER NOT NULL,
#             description TEXT,
#             image_url TEXT,
#             available INTEGER DEFAULT 1
#         );

#         CREATE TABLE IF NOT EXISTS reservations (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_id INTEGER,
#             name TEXT NOT NULL,
#             email TEXT NOT NULL,
#             phone TEXT NOT NULL,
#             date TEXT NOT NULL,
#             time TEXT NOT NULL,
#             guests INTEGER NOT NULL,
#             message TEXT,
#             status TEXT DEFAULT 'pending',
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             FOREIGN KEY (user_id) REFERENCES users (id)
#         );
#     ''')

#     conn.commit()
#     conn.close()
#     print("Database berhasil dibuat!")


# membuat tabel db
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(100),
            role ENUM('admin','staff','customer') NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(50) NOT NULL,
            price INT NOT NULL,
            description TEXT,
            image_url VARCHAR(255),
            available TINYINT(1) DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            date DATE NOT NULL,
            time TIME NOT NULL,
            guests INT NOT NULL,
            message TEXT,
            status ENUM('pending','approved','rejected') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()
    print("Database & tabel berhasil dibuat!")

# menambahkan isi sampel data
def add_sample_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS count FROM menu")
    existing = cursor.fetchone()

    if existing['count'] == 0:
        sample_menu = [
            ('Beef Bourguignon', 'Main Course', 185000, 'Daging sapi dimasak dengan red wine dan sayuran', 'https://images.unsplash.com/photo-1600891964092-4316c288032e?w=400'),
            ('Coq au Vin', 'Main Course', 165000, 'Ayam dalam saus wine merah dengan jamur', 'https://images.unsplash.com/photo-1598103442097-8b74394b95c6?w=400'),
            ('Ratatouille', 'Main Course', 125000, 'Sayuran Prancis panggang dengan herbs', 'https://images.unsplash.com/photo-1572453800999-e8d2d1589b7c?w=400'),
            ('French Onion Soup', 'Appetizer', 75000, 'Sup bawang klasik dengan keju gruyere', 'https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400'),
            ('Escargots', 'Appetizer', 95000, 'Bekicot dengan garlic butter', 'https://usa.inquirer.net/files/2022/12/Authentic-Homemade-Escargots-Easy-Recipe.jpg'),
            ('Crème Brûlée', 'Dessert', 65000, 'Custard vanilla dengan karamel renyah', 'https://images.unsplash.com/photo-1470124182917-cc6e71b22ecc?w=400'),
            ('Tarte Tatin', 'Dessert', 70000, 'Tart apel karamel terbalik', 'https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=400'),
            ('Galette de Bretagne', 'Appetizer', 85000, 'Panekuk dengan isian gurih dari Bretagne', 'https://cdn.tasteatlas.com/Images/Dishes/ba0206fa9d884c7dbbce4522a585805b.jpg?w=905&h=510'),
            ('Soufflé au Chocolat', 'Dessert', 70000, 'Kue cokelat ringan dan lembut', 'https://cdn.tasteatlas.com/images/dishes/ffe89104a97543eb80544c4e0b196bd5.jpg?w=905&h=510'),
            ('Créme Caramel', 'Dessert', 65000, 'Custard dengan krim karamel yang lembut', 'https://www.tasteatlas.com/Images/Dishes/e0fe68df68e5466e9a1d0f7580415820.jpg?mw=1300'),
            ('Confit de Canard', 'Main Course', 123000, 'Daging bebek super empuk', 'https://salsawisata.com/wp-content/uploads/2024/01/Confit-de-Canard.webp'),
            ('Langue de Bouef', 'Main Course', 130000, 'Lidah sapi dengan bumbu kuat', 'https://salsawisata.com/wp-content/uploads/2024/01/menu-makanan-khas-Perancis.webp')
        ]

        cursor.executemany(
            "INSERT INTO menu (name, category, price, description, image_url) VALUES (%s, %s, %s, %s, %s)",
            sample_menu
        )
        conn.commit()
        print("Sample menu berhasil ditambahkan!")

    conn.close()


# def add_sample_data():
#     conn = get_db_connection()

#     existing = conn.execute('SELECT COUNT(*) as count FROM menu').fetchone()
#     if existing['count'] == 0:
#         sample_menu = [
#             ('Beef Bourguignon', 'Main Course', 185000, 'Daging sapi dimasak dengan red wine dan sayuran', 'https://images.unsplash.com/photo-1600891964092-4316c288032e?w=400'),
#             ('Coq au Vin', 'Main Course', 165000, 'Ayam dalam saus wine merah dengan jamur', 'https://images.unsplash.com/photo-1598103442097-8b74394b95c6?w=400'),
#             ('Ratatouille', 'Main Course', 125000, 'Sayuran Prancis panggang dengan herbs', 'https://images.unsplash.com/photo-1572453800999-e8d2d1589b7c?w=400'),
#             ('French Onion Soup', 'Appetizer', 75000, 'Sup bawang klasik dengan keju gruyere', 'https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400'),
#             ('Escargots', 'Appetizer', 95000, 'Bekicot dengan garlic butter', 'https://usa.inquirer.net/files/2022/12/Authentic-Homemade-Escargots-Easy-Recipe.jpg'),
#             ('Crème Brûlée', 'Dessert', 65000, 'Custard vanilla dengan karamel renyah', 'https://images.unsplash.com/photo-1470124182917-cc6e71b22ecc?w=400'),
#             ('Tarte Tatin', 'Dessert', 70000, 'Tart apel karamel terbalik', 'https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=400'),
#             ('Galette de Bretagne', 'Appetizer', 85000,'Panekuk dengan isian gurih dari Bretagne', 'https://cdn.tasteatlas.com//Images/Dishes/ba0206fa9d884c7dbbce4522a585805b.jpg?w=905&h=510'),
#             ('Soufflé au Chocolat', 'Dessert', 70000, 'Kue cokelat ringan dan lembut','https://cdn.tasteatlas.com//images/dishes/ffe89104a97543eb80544c4e0b196bd5.jpg?w=905&h=510'),
#             ('Créme Caramel', 'Dessert', 65000, 'Custard dengan krim karamel yang lembut','https://www.tasteatlas.com/Images/Dishes/e0fe68df68e5466e9a1d0f7580415820.jpg?mw=1300'),
#             ('Confit de Canard', 'Main Course', 123000, 'Berbahan utama daging bebek yang super empuk.','https://salsawisata.com/wp-content/uploads/2024/01/Confit-de-Canard.webp'),
#             ('Langue de Bouef', 'Main Course', 130000, 'Menggunakan lidah sapi sebagai bahan utamanya, yang kemudian dimasak dengan bumbu yang cukup kuat.','https://salsawisata.com/wp-content/uploads/2024/01/menu-makanan-khas-Perancis.webp')
#         ]

#         conn.executemany(
#             'INSERT INTO menu (name, category, price, description, image_url) VALUES (?, ?, ?, ?, ?)',
#             sample_menu
#         )
#         conn.commit()

#     conn.close()
#     print("Sample data berhasil ditambahkan!")

if __name__ == "__main__":
    create_database_if_not_exists()  # Buat database dulu
    init_db()
    add_sample_data()
    create_admin()
