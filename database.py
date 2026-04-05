import sqlite3

conn = sqlite3.connect("data.db", check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        stock INTEGER,
        price INTEGER
    )
    """)
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        qty INTEGER,
        total INTEGER,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()

def add_product(name, stock, price):
    c.execute("INSERT INTO products (name, stock, price) VALUES (?, ?, ?)", (name, stock, price))
    conn.commit()

def get_products():
    return c.execute("SELECT * FROM products").fetchall()

def get_product(pid):
    return c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()

def update_stock(pid, qty):
    c.execute("UPDATE products SET stock = stock - ? WHERE id=?", (qty, pid))
    conn.commit()

def add_order(user_id, product_id, qty, total):
    c.execute("INSERT INTO orders (user_id, product_id, qty, total) VALUES (?, ?, ?, ?)",
              (user_id, product_id, qty, total))
    conn.commit()

def get_user_orders(user_id):
    return c.execute("SELECT * FROM orders WHERE user_id=?", (user_id,)).fetchall()