import sqlite3
import logging


logging.basicConfig(level=logging.INFO)


def get_db_connection():
    try:
        conn = sqlite3.connect("users.db")
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logging.error(f"Ошибка подключения к базе данных: {e}")
        raise


conn = get_db_connection()
cursor = conn.cursor()
try:
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS site_name_password (
        user_id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    conn.commit()
    logging.info("Таблица site_name_password создана или уже существует.")
except sqlite3.Error as e:
    logging.error(f"Ошибка при создании таблицы site_name_password: {e}")