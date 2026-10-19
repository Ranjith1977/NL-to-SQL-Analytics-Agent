import pytest
from app.sql_validator import validate_sql, UnsafeQueryError

def test_accepts_simple_select():
    assert "SELECT" in validate_sql("SELECT customer_name FROM customers")

def test_accepts_join_select():
    sql = """SELECT p.product_name, SUM(oi.quantity * oi.unit_price) AS revenue
             FROM order_items oi
             JOIN products p ON p.product_id = oi.product_id
             GROUP BY p.product_name"""
    assert validate_sql(sql).startswith("SELECT")

@pytest.mark.parametrize("sql", [
    "DELETE FROM customers",
    "DROP TABLE customers",
    "UPDATE customers SET city='X'",
    "SELECT * FROM sqlite_master",
    "SELECT * FROM customers; DELETE FROM customers",
    "PRAGMA table_info(customers)",
])
def test_rejects_unsafe_or_unapproved_sql(sql):
    with pytest.raises(UnsafeQueryError):
        validate_sql(sql)
