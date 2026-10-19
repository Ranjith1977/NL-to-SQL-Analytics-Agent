
from contextlib import asynccontextmanager
import sqlite3
import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import DATABASE_PATH, OLLAMA_HOST, OLLAMA_MODEL
from app.schema_inspector import get_schema_text
from app.sql_generator import generate_sql
from app.sql_validator import validate_sql, UnsafeQueryError
from app.query_executor import execute_readonly
from app.answer_generator import summarize_result
from app.repository import log_query, get_history


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not DATABASE_PATH.exists():
        raise RuntimeError(
            f"Database not found at {DATABASE_PATH}. "
            "Run: python -m app.init_db"
        )
    yield


app = FastAPI(
    title="NL-to-SQL Analytics Agent",
    description=(
        "Local-first natural language analytics "
        "with read-only SQL guardrails."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class AskResponse(BaseModel):
    question: str
    sql: str
    columns: list[str]
    rows: list[dict]
    row_count: int
    latency_ms: float
    answer: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "database_exists": DATABASE_PATH.exists(),
        "model": OLLAMA_MODEL,
        "ollama_host": OLLAMA_HOST,
    }


@app.get("/schema")
def schema():
    return {"schema": get_schema_text()}


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    question = payload.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be blank.",
        )

    started = time.perf_counter()
    generated = None

    try:
        generated = generate_sql(question)
        safe_sql = validate_sql(generated)
        df, query_ms = execute_readonly(safe_sql)
        answer = summarize_result(question, safe_sql, df)

        total_ms = round(
            (time.perf_counter() - started) * 1000,
            2,
        )

        log_query(
            question,
            safe_sql,
            True,
            len(df),
            total_ms,
        )

        return AskResponse(
            question=question,
            sql=safe_sql,
            columns=list(df.columns),
            rows=df.to_dict(orient="records"),
            row_count=len(df),
            latency_ms=total_ms,
            answer=answer,
        )

    except (UnsafeQueryError, ValueError) as exc:
        log_query(
            question,
            generated,
            False,
            error=str(exc),
        )
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        message = str(exc)

        log_query(
            question,
            generated,
            False,
            error=message[:500],
        )

        if (
            "Connection refused" in message
            or "Failed to connect" in message
        ):
            message = (
                "Cannot connect to Ollama. Start Ollama "
                "and verify the model is installed."
            )

        raise HTTPException(
            status_code=500,
            detail=message[:500],
        ) from exc


@app.get("/history")
def history(limit: int = 30):
    return {
        "items": get_history(max(1, min(limit, 100)))
    }


@app.delete("/history")
def clear_history():
    """Clear query history without deleting business data."""

    try:
        with sqlite3.connect(
            str(DATABASE_PATH),
            timeout=10,
        ) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                """
            )

            tables = {
                row[0] for row in cursor.fetchall()
            }

            candidates = (
                "query_history",
                "query_logs",
                "history",
            )

            history_table = next(
                (
                    name
                    for name in candidates
                    if name in tables
                ),
                None,
            )

            if history_table is None:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "History table not found. "
                        "Check app/repository.py for "
                        "the actual table name."
                    ),
                )

            cursor.execute(
                f'DELETE FROM "{history_table}"'
            )
            deleted_count = cursor.rowcount

        return {
            "status": "success",
            "message": "Query history cleared successfully.",
            "deleted_count": deleted_count,
        }

    except HTTPException:
        raise

    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not clear history: {exc}",
        ) from exc
