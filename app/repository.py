import sqlite3
from app.config import DATABASE_PATH

def log_query(question, sql_query, success, row_count=0, latency_ms=0, error=None):
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        conn.execute(
            """INSERT INTO query_history
            (question, sql_query, success, row_count, latency_ms, error)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (question, sql_query, int(success), row_count, latency_ms, error),
        )
        conn.commit()
    finally:
        conn.close()

def get_history(limit=30):
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """SELECT history_id, question, sql_query, success, row_count,
                      latency_ms, error, created_at
               FROM query_history ORDER BY history_id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
