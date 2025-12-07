import sqlite3
from contextlib import contextmanager
import aiosqlite

# Глобальное подключение для синхронного кода
conn = None


def get_connection():
    global conn
    if conn is None:
        conn = sqlite3.connect('/app/database.db', check_same_thread=False)
        conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Инициализация базы данных - СОЗДАЁТ ТАБЛИЦЫ"""
    global conn
    conn = get_connection()
    cursor = conn.cursor()

    # Таблица заказов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            service TEXT NOT NULL,
            price REAL NOT NULL,
            status TEXT DEFAULT 'new',
            lawyer_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Таблица юристов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lawyers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            status TEXT DEFAULT 'free',
            rating REAL DEFAULT 0.0
        )
    ''')

    conn.commit()
    print("✅ База данных инициализирована!")


# Асинхронные функции для бота
async def get_async_db():
    async with aiosqlite.connect('/app/database.db') as db:
        db.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
        yield db


if __name__ == "__main__":
    init_db()

