import sqlite3
from datetime import datetime
from config import USLUGI

conn = sqlite3.connect('lawyer_bot.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER, client_name TEXT, service TEXT, price INTEGER,
    status TEXT DEFAULT 'new', created_at TEXT
)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS user_state (
    user_id INTEGER PRIMARY KEY, active_order INTEGER
)''')
conn.commit()

def has_active_order(user_id):
    cursor.execute("SELECT id FROM orders WHERE client_id=? AND status IN ('new','accepted')", (user_id,))
    return cursor.fetchone()

def create_order(client_id, client_name, service_key):
    srv = USLUGI[service_key]
    cursor.execute("""
        INSERT INTO orders (client_id, client_name, service, price, status, created_at) 
        VALUES (?, ?, ?, ?, 'new', ?)
    """, (client_id, client_name, srv['name'], srv['price'], datetime.now().isoformat()))
    order_id = cursor.lastrowid
    cursor.execute("INSERT OR REPLACE INTO user_state (user_id, active_order) VALUES (?, ?)", (client_id, order_id))
    conn.commit()
    return order_id
