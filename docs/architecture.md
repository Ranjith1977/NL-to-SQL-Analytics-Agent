# Architecture

## Request flow

1. The Streamlit UI sends the user's question to FastAPI at `/ask`.
2. The backend obtains the SQLite schema and asks the configured local Ollama model to generate a query.
3. SQLGlot validates the query against the read-only query policy and allowed tables.
4. The query executor opens the configured SQLite database in read-only mode, enforces a result cap and timeout, and returns rows.
5. The answer generator turns the returned data into a concise plain-English response. The backend records the request in `query_history`.

The flow is:

```text
Streamlit -> FastAPI -> Ollama SQL generation -> SQL validation
          -> read-only SQLite execution -> answer generation -> Streamlit
```

## Components

- `app/main.py`: FastAPI application and `/health`, `/schema`, `/ask`, and `/history` endpoints.
- `app/config.py`: environment-backed database and model settings.
- `app/sql_generator.py` and `app/sql_validator.py`: SQL creation and safety validation.
- `app/query_executor.py`, `app/schema_inspector.py`, and `app/repository.py`: SQLite access, schema discovery, and query history.
- `app/answer_generator.py`: plain-English result summaries.
- `dashboard/streamlit_app.py`: Streamlit UI.
- `data/sales.db`: local sample database; it is intentionally excluded from Git.
- `tests/`: unit tests; `evaluation/`: the manual API evaluation runner and its question set.

## Configuration and data safety

`DATABASE_PATH` defaults to `data/sales.db` and may be overridden with an environment variable. Relative paths are resolved from the project root. The `.env.example` file documents supported values, but this project does not load `.env` files automatically; set environment variables in the shell or your process manager.

The database initializer (`python -m app.init_db`) replaces the configured database if it already exists. Do not run it when preserving existing data. Query execution itself uses SQLite read-only mode.
