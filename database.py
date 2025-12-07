import sqlite3

# Глобальное подключение
conn = sqlite3.connect('/app/database.db', check_same_thread=False)
conn.row_factory = sqlite3.Row


def init_db():
    """Создаёт таблицы"""
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service TEXT,
            price REAL,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lawyers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            status TEXT DEFAULT 'free'
        )
    ''')

    conn.commit()
    print("✅ База данных готова!")


if __name__ == "__main__":
    init_db()


