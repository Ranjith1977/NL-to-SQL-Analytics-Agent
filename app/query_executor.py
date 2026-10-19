import sqlite3
import time
import pandas as pd
from app.config import DATABASE_PATH, MAX_RESULT_ROWS, QUERY_TIMEOUT_SECONDS

def execute_readonly(sql: str) -> tuple[pd.DataFrame, float]:
    uri = f"file:{DATABASE_PATH.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    started = time.perf_counter()
    deadline = time.monotonic() + QUERY_TIMEOUT_SECONDS
    conn.set_progress_handler(lambda: 1 if time.monotonic() > deadline else 0, 1000)
    try:
        cursor = conn.execute(sql)
        columns = [d[0] for d in cursor.description or []]
        rows = cursor.fetchmany(MAX_RESULT_ROWS + 1)
        if len(rows) > MAX_RESULT_ROWS:
            rows = rows[:MAX_RESULT_ROWS]
        df = pd.DataFrame(rows, columns=columns)
        elapsed_ms = (time.perf_counter() - started) * 1000
        return df, round(elapsed_ms, 2)
    finally:
        conn.close()
