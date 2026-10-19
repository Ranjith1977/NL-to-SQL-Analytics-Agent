import sqlite3
from app.config import DATABASE_PATH
from app.init_db import create_database

def test_database_has_expected_tables():
    create_database()
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        assert {"customers", "products", "orders", "order_items", "query_history"} <= tables
    finally:
        conn.close()
