import pymysql
from werkzeug.security import generate_password_hash, check_password_hash



class Database:
    def __init__(self):
        self.connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='sistem_informasi_perikanan',
            port=3307,
            cursorclass=pymysql.cursors.DictCursor,
            charset='utf8mb4'
        )

    def query(self, sql, params=None):
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql, params or ())
            self.connection.commit()
            return cursor
        except Exception as e:
            print(f"Database query error: {e}")
            self.connection.rollback()
            raise e

    def fetchall(self, sql, params=None):
        cursor = self.query(sql, params)
        return cursor.fetchall()

    def fetchone(self, sql, params=None):
        cursor = self.query(sql, params)
        return cursor.fetchone()

db = Database()

class KategoriIkan:
    @staticmethod
    def create(nama_kategori, habitat, deskripsi):
        if not db: raise RuntimeError("DB not connected")
        sql = "INSERT INTO kategori_ikan (nama_kategori, habitat, deskripsi) VALUES (%s, %s, %s)"
        db.query(sql, (nama_kategori, habitat, deskripsi))
        return True

    @staticmethod
    def get_all():
        if not db: return []
        sql = "SELECT * FROM kategori_ikan ORDER BY id_kategori DESC"
        return db.fetchall(sql)

    @staticmethod
    def get_by_id(id_kategori):
        if not db: return None
        sql = "SELECT * FROM kategori_ikan WHERE id_kategori = %s"
        return db.fetchone(sql, (id_kategori,))

    @staticmethod
    def update(id_kategori, nama_kategori, habitat, deskripsi):
        if not db: raise RuntimeError("DB not connected")
        sql = "UPDATE kategori_ikan SET nama_kategori = %s, habitat = %s, deskripsi = %s WHERE id_kategori = %s"
        db.query(sql, (nama_kategori, habitat, deskripsi, id_kategori))
        return True

    @staticmethod
    def delete(id_kategori):
        if not db: raise RuntimeError("DB not connected")
        sql = "DELETE FROM kategori_ikan WHERE id_kategori = %s"
        db.query(sql, (id_kategori,))
        return True

class DaftarIkan:
    @staticmethod
    def create(nama_ikan, id_kategori, harga, stok, user_id):
        if not db: raise RuntimeError("DB not connected")
        sql = """INSERT INTO daftar_ikan (nama_ikan, id_kategori, harga, stok, id_user)
                 VALUES (%s, %s, %s, %s, %s)"""
        db.query(sql, (nama_ikan, id_kategori, harga, stok, user_id))
        return True

    @staticmethod
    def get_all():
        if not db: return []
        sql = """SELECT d.*, k.nama_kategori, u.username AS created_by
                 FROM daftar_ikan d
                 JOIN kategori_ikan k ON d.id_kategori = k.id_kategori
                 JOIN users u ON d.id_user = u.id_user
                 ORDER BY d.id_ikan DESC"""
        return db.fetchall(sql)

    @staticmethod
    def get_by_id(id_ikan):
        if not db: return None
        sql = """SELECT d.*, k.nama_kategori, u.username AS created_by
                 FROM daftar_ikan d
                 JOIN kategori_ikan k ON d.id_kategori = k.id_kategori
                 JOIN users u ON d.id_user = u.id_user
                 WHERE d.id_ikan = %s"""
        return db.fetchone(sql, (id_ikan,))

    @staticmethod
    def get_by_kategori(id_kategori):
        if not db: return []
        sql = "SELECT * FROM daftar_ikan WHERE id_kategori = %s"
        return db.fetchall(sql, (id_kategori,))

    @staticmethod
    def update(id_ikan, nama_ikan, id_kategori, harga, stok):
        if not db: raise RuntimeError("DB not connected")
        sql = "UPDATE daftar_ikan SET nama_ikan = %s, id_kategori = %s, harga = %s, stok = %s WHERE id_ikan = %s"
        db.query(sql, (nama_ikan, id_kategori, harga, stok, id_ikan))
        return True

    @staticmethod
    def delete(id_ikan):
        if not db: raise RuntimeError("DB not connected")
        sql = "DELETE FROM daftar_ikan WHERE id_ikan = %s"
        db.query(sql, (id_ikan,))
        return True

    @staticmethod
    def search(q=None, id_kategori=None):
        """
        Cari ikan berdasarkan nama (LIKE) dan/atau kategori.
        Jika q None atau kosong, akan mengembalikan semua.
        """
        if not db: return []
        sql = """SELECT d.*, k.nama_kategori, u.username AS created_by
                 FROM daftar_ikan d
                 JOIN kategori_ikan k ON d.id_kategori = k.id_kategori
                 JOIN users u ON d.id_user = u.id_user
                 WHERE 1=1"""

        params = []
        if   q:
            sql += " AND d.nama_ikan LIKE %s"
            params.append(f"%{q}%")
        if id_kategori:
            sql += " AND d.id_kategori = %s"
            params.append(id_kategori)
        sql += " ORDER BY d.id_ikan DESC"


        print("DEBUG search: SQL =", sql)
        print("DEBUG search: params =", params)
        return db.fetchall(sql, params)



class User:
    @staticmethod
    def create(username, password, role='kasir'):
        hashed = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
        sql = "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)"
        db.query(sql, (username, hashed, role))
        return True

    @staticmethod
    def check_login(username, password):
        sql = "SELECT * FROM users WHERE username = %s"
        user = db.fetchone(sql, (username,))
        if not user:
            return None
        # user['password'] harus ada
        try:
            if check_password_hash(user['password'], password):
                return user
        except Exception as e:
            print("Error checking password:", e)
        return None

    @staticmethod
    def get_all():
        sql = "SELECT * FROM users ORDER BY id_user"
        return db.fetchall(sql)

    @staticmethod
    def get_by_id(id_user):
        sql = "SELECT * FROM users WHERE id_user = %s"
        return db.fetchone(sql, (id_user,))