# NL-to-SQL Analytics Agent

Local-first analytics app that turns natural-language questions into validated, read-only SQL against a sample SQLite sales database. Results are summarized in plain English through a Streamlit UI backed by FastAPI and a local Ollama model.

## Features

- Local Ollama model with schema-aware SQL generation.
- SQLGlot validation; read-only SQLite execution with allowed-table, row-count, and query-time limits.
- FastAPI endpoints and Streamlit dashboard; query history and supporting result rows.

## Project layout

```text
app/           FastAPI backend and SQL/database logic
dashboard/     Streamlit UI
data/          Local SQLite database (excluded from Git)
docs/          Architecture notes
evaluation/    Evaluation runner and questions
screenshots/   UI images shown above
tests/         Automated tests
README.md      Setup and usage
requirements.txt
```

See [docs/architecture.md](docs/architecture.md) for component details.

## Setup (Windows PowerShell)

Run from the project root. Requirements: Python 3.12, Git, and Ollama.

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
ollama pull qwen3:1.7b
```

No paid LLM API key is needed. The app uses `qwen3:1.7b` by default; see [.env.example](.env.example) for configurable environment variables.

The existing sample database is `data\sales.db`. **Do not run `python -m app.init_db` unless you intend to replace the configured database with a fresh sample.**

## Run

Open two terminals in the project root and activate `.venv` in both.

**Terminal 1 — FastAPI**
```powershell
python -m uvicorn app.main:app --reload
```
API docs: <http://127.0.0.1:8000/docs>

**Terminal 2 — Streamlit**
```powershell
python -m streamlit run dashboard\streamlit_app.py
```

## API quick reference

The FastAPI service is available at `http://127.0.0.1:8000`. Interactive
documentation is available at <http://127.0.0.1:8000/docs>.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Check service and database status. |
| `GET` | `/schema` | Inspect the database schema provided to the SQL generator. |
| `POST` | `/ask` | Generate, validate, and run a query for a natural-language question. |
| `GET` | `/history?limit=30` | Retrieve recent queries; `limit` is capped at 100. |
| `DELETE` | `/history` | Clear query history without deleting business data. |

Example request from PowerShell:

```powershell
$response = Invoke-RestMethod `
    -Uri http://127.0.0.1:8000/ask `
    -Method Post `
    -ContentType "application/json" `
    -Body (@{ question = "What were the top 5 products by revenue?" } | ConvertTo-Json)

$response.answer
$response.sql
$response.rows
```

The response includes the generated SQL, result columns and rows, row count,
latency, and a plain-English answer. Invalid or unsafe queries are rejected.

## Configuration

Copy `.env.example` to `.env` in the project root to customize these settings.
The application reads environment variables directly; if your shell does not
load `.env` files automatically, set the variables in the shell before starting
the API.

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_MODEL` | `qwen3:1.7b` | Local model used to generate SQL and summarize results. |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL. |
| `DATABASE_PATH` | `data/sales.db` | SQLite database path; relative paths resolve from the project root. |
| `MAX_RESULT_ROWS` | `200` | Maximum number of rows returned from a query. |
| `QUERY_TIMEOUT_SECONDS` | `5` | Maximum execution time for a database query. |
| `API_BASE_URL` | `http://127.0.0.1:8000` | API URL used by the Streamlit dashboard. |

## Screenshots

| Dashboard | Database explorer |
|---|---|
| <a href="screenshots/dashboard.png"><img src="screenshots/dashboard.png" alt="Sales analytics dashboard" width="520"></a> | <a href="screenshots/database-explorer.png"><img src="screenshots/database-explorer.png" alt="Database schema explorer" width="520"></a> |

| Query history | Generated SQL |
|---|---|
| <a href="screenshots/query-history.png"><img src="screenshots/query-history.png" alt="Query history view" width="520"></a> | <a href="screenshots/generated-sql-query.png"><img src="screenshots/generated-sql-query.png" alt="Generated SQL view" width="520"></a> |

| Example questions |
|---|
| <a href="screenshots/request-questions.png"><img src="screenshots/request-questions.png" alt="Example natural-language questions" width="520"></a> |

Click any image to open it at full size.

## Test

The database test recreates its configured database. Use a temporary path to protect `data\sales.db`:

```powershell
$testDatabase = Join-Path $env:TEMP ("nl-to-sql-test-" + [guid]::NewGuid().ToString("N") + ".db")
$env:DATABASE_PATH = $testDatabase
try {
    python -m pytest -q
    $testExitCode = $LASTEXITCODE
} finally {
    Remove-Item Env:DATABASE_PATH
    if (Test-Path -LiteralPath $testDatabase) { Remove-Item -LiteralPath $testDatabase }
}
if ($testExitCode -ne 0) { exit $testExitCode }
```

Optional API evaluation (requires FastAPI and Ollama running):
```powershell
python evaluation\evaluate.py
```

## Troubleshooting

- **Ollama connection errors:** Start Ollama, verify `OLLAMA_HOST`, and make
  sure the configured model is installed (for example, run `ollama pull
  qwen3:1.7b`).
- **Database not found:** Check `DATABASE_PATH`. The app expects the sample
  `data\sales.db`; only run `python -m app.init_db` if you intend to create or
  replace the sample database.
- **Port already in use:** Start Uvicorn on another port with
  `python -m uvicorn app.main:app --reload --port 8001`, then set
  `API_BASE_URL` to `http://127.0.0.1:8001` before starting Streamlit.

## Safety

This demo is not a production security boundary. Do not expose it publicly or connect it to sensitive data without authentication, a security review, and stronger infrastructure controls.
