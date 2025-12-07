import sqlite3
import os


def init_db():
    conn = sqlite3.connect('/app/database.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            service_name TEXT NOT NULL,
            price INTEGER NOT NULL,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ База данных готова!")


def get_orders(client_id=None):
    conn = sqlite3.connect('/app/database.db')
    if client_id:
        cursor = conn.execute("SELECT * FROM orders WHERE client_id = ? ORDER BY created_at DESC", (client_id,))
    else:
        cursor = conn.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = cursor.fetchall()
    conn.close()
    return orders


def update_order_status(order_id, status):
    conn = sqlite3.connect('/app/database.db')
    cursor = conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def create_order(client_id, service_name, price):
    conn = sqlite3.connect('/app/database.db')
    cursor = conn.execute(
        "INSERT INTO orders (client_id, service_name, price) VALUES (?, ?, ?)",
        (client_id, service_name, price)
    )
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id



