import sqlite3
from datetime import date, timedelta
from pathlib import Path
from app.config import DATABASE_PATH

def create_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()

    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.executescript("""
    PRAGMA foreign_keys = ON;
    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY,
        customer_name TEXT NOT NULL,
        city TEXT NOT NULL,
        segment TEXT NOT NULL
    );
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT NOT NULL,
        category TEXT NOT NULL,
        list_price REAL NOT NULL
    );
    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        order_date TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
    );
    CREATE TABLE order_items (
        order_item_id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(order_id),
        FOREIGN KEY(product_id) REFERENCES products(product_id)
    );
    CREATE TABLE query_history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        sql_query TEXT,
        success INTEGER NOT NULL,
        row_count INTEGER NOT NULL DEFAULT 0,
        latency_ms REAL NOT NULL DEFAULT 0,
        error TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)

    customers = [
        (1, "Aarav Retail", "Chennai", "Retail"),
        (2, "Bluebird Stores", "Bengaluru", "SMB"),
        (3, "Cedar Market", "Hyderabad", "Retail"),
        (4, "Delta Traders", "Mumbai", "Enterprise"),
        (5, "Evergreen Shop", "Pune", "SMB"),
        (6, "Fresh Basket", "Chennai", "Enterprise"),
        (7, "Golden Mart", "Delhi", "Retail"),
        (8, "Harbor Supplies", "Kochi", "SMB"),
        (9, "Indigo Retail", "Bengaluru", "Enterprise"),
        (10, "Juniper Goods", "Coimbatore", "Retail"),
        (11, "Kite Commerce", "Hyderabad", "SMB"),
        (12, "Lotus Stores", "Mumbai", "Enterprise"),
    ]
    products = [
        (1, "Laptop Stand", "Accessories", 1499.0),
        (2, "Wireless Mouse", "Accessories", 899.0),
        (3, "Mechanical Keyboard", "Accessories", 2499.0),
        (4, "USB-C Hub", "Electronics", 3299.0),
        (5, "Webcam HD", "Electronics", 2799.0),
        (6, "Notebook Pack", "Stationery", 299.0),
        (7, "Desk Lamp", "Home Office", 1199.0),
        (8, "Monitor 24 inch", "Electronics", 10999.0),
    ]
    cur.executemany("INSERT INTO customers VALUES (?, ?, ?, ?)", customers)
    cur.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", products)

    statuses = ["completed", "completed", "completed", "shipped", "cancelled"]
    order_rows, item_rows = [], []
    item_id = 1
    # Deterministic sample data for Jan-Dec 2025.
    for order_id in range(1, 181):
        customer_id = ((order_id * 7) % len(customers)) + 1
        month = ((order_id - 1) % 12) + 1
        day = ((order_id * 3) % 27) + 1
        order_date = date(2025, month, day).isoformat()
        status = statuses[order_id % len(statuses)]
        order_rows.append((order_id, customer_id, order_date, status))
        # One or two line items per order, deterministic distribution.
        for offset in range(1 + (order_id % 2)):
            product_id = ((order_id * 3 + offset * 5) % len(products)) + 1
            quantity = ((order_id + offset) % 5) + 1
            price = products[product_id - 1][3] * (1.0 + ((order_id % 4) * 0.025))
            item_rows.append((item_id, order_id, product_id, quantity, round(price, 2)))
            item_id += 1
    cur.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", order_rows)
    cur.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?)", item_rows)
    conn.commit()
    conn.close()
    print(f"Created sample database: {DATABASE_PATH}")
    print(f"Customers: {len(customers)}, products: {len(products)}, orders: {len(order_rows)}, order items: {len(item_rows)}")

if __name__ == "__main__":
    create_database()
