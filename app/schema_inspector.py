import sqlite3
from app.config import DATABASE_PATH

ALLOWED_TABLES = {"customers", "products", "orders", "order_items"}

def get_schema_text() -> str:
    conn = sqlite3.connect(f"file:{DATABASE_PATH.as_posix()}?mode=ro", uri=True)
    try:
        sections = []
        for table in sorted(ALLOWED_TABLES):
            rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
            cols = ", ".join(f"{row[1]} ({row[2]})" for row in rows)
            sections.append(f"{table}: {cols}")
        sections.append(
            "Relationships: orders.customer_id -> customers.customer_id; "
            "order_items.order_id -> orders.order_id; "
            "order_items.product_id -> products.product_id"
        )
        sections.append(
            "Revenue rule for this demo: SUM(order_items.quantity * order_items.unit_price). "
            "Exclude orders whose status is 'cancelled' when analyzing realized sales. "
            "Dates are ISO strings YYYY-MM-DD. Data covers 2025."
        )
        return "\n".join(sections)
    finally:
        conn.close()
