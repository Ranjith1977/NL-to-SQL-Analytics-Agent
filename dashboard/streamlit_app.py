import os

import pandas as pd
import requests
import streamlit as st


# ---------------- CONFIGURATION ----------------

API_BASE = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

st.set_page_config(
    page_title="Sales Analytics Assistant",
    page_icon="💬",
    layout="centered",
)


# ---------------- PAGE HEADER ----------------

st.title("💬 Sales Analytics Assistant")

st.caption(
    "Ask a question in plain English. Explore your sales database "
    "and get answers from your data."
)


# ---------------- SESSION STATE ----------------

if "last_result" not in st.session_state:
    st.session_state["last_result"] = None

if "question" not in st.session_state:
    st.session_state["question"] = ""

if "database_schema" not in st.session_state:
    st.session_state["database_schema"] = None

if "schema_error" not in st.session_state:
    st.session_state["schema_error"] = None


# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.header("About")

    st.write("**AI model:** Ollama running locally")
    st.write("**Data source:** SQLite sales database")

    st.write(
        "**How it works:** English question → SQL → "
        "database results → English answer"
    )

    st.divider()

    st.subheader("Try asking")

    examples = [
        "How many customers are in the database?",
        "Which product generated the highest revenue?",
        "What were the total sales in 2025?",
        "Who are the top five customers by revenue?",
        "Which city has the most customers?",
        "Which product category made the most money?",
        "How many orders are cancelled?",
        "What is the average order value?",
    ]

    for example in examples:
        if st.button(
            example,
            key=f"example_{examples.index(example)}",
            width="stretch",
        ):
            st.session_state["question"] = example

    st.divider()

    # ---------------- DATABASE EXPLORER ----------------

    with st.expander("🔎 Database Explorer"):
        st.caption(
            "Inspect the tables and columns in your database."
        )

        if st.button(
            "Load database schema",
            width="stretch",
        ):
            try:
                schema_response = requests.get(
                    f"{API_BASE}/schema",
                    timeout=15,
                )

                if schema_response.ok:
                    st.session_state["database_schema"] = (
                        schema_response.json()
                    )
                    st.session_state["schema_error"] = None
                else:
                    st.session_state["schema_error"] = (
                        f"Schema endpoint returned HTTP "
                        f"{schema_response.status_code}."
                    )

            except requests.RequestException:
                st.session_state["schema_error"] = (
                    f"Cannot connect to the backend at {API_BASE}. "
                    "Start FastAPI and try again."
                )

        if st.session_state["schema_error"]:
            st.warning(st.session_state["schema_error"])

        schema = st.session_state["database_schema"]

        # Your FastAPI backend returns {"schema": "..."}.
        if schema:
            schema_text = schema.get("schema", "")

            if schema_text:
                st.markdown("### Database schema")

                st.caption(
                    "Tables and columns detected from your "
                    "SQLite database."
                )

                st.code(schema_text, language="sql")

            else:
                st.warning(
                    "The backend returned an empty schema. "
                    "Check the database path and schema inspector."
                )


# ---------------- ASK A QUESTION ----------------

with st.form("ask_form"):
    question = st.text_area(
        "Your question",
        key="question",
        placeholder=(
            "Example: Which product generated the highest revenue?"
        ),
        height=90,
    )

    run = st.form_submit_button(
        "Get answer",
        type="primary",
        width="stretch",
    )


if run:
    if not question.strip():
        st.warning("Type a question first.")

    else:
        try:
            with st.spinner(
                "Checking the database and preparing your answer..."
            ):
                response = requests.post(
                    f"{API_BASE}/ask",
                    json={"question": question.strip()},
                    timeout=180,
                )

            if response.ok:
                st.session_state["last_result"] = response.json()

            else:
                try:
                    detail = response.json().get(
                        "detail",
                        response.text,
                    )
                except ValueError:
                    detail = response.text

                st.error(
                    f"I couldn't answer that question: {detail}"
                )

        except requests.Timeout:
            st.error(
                "The request took too long. Check whether Ollama "
                "is running and try a simpler question."
            )

        except requests.RequestException:
            st.error(
                f"Cannot reach the backend at {API_BASE}. "
                "Start FastAPI in another terminal and try again."
            )


# ---------------- DISPLAY ANSWER ----------------

result = st.session_state.get("last_result")

if result:
    st.divider()
    st.subheader("Answer")

    st.write(result.get("answer", "No answer returned."))

    st.caption(
        f"Based on {result.get('row_count', 0)} "
        "database result row(s)."
    )

    if "latency_ms" in result:
        st.caption(
            f"Response time: {result['latency_ms']} ms"
        )

    with st.expander("View supporting data"):
        df = pd.DataFrame(
            result.get("rows", []),
            columns=result.get("columns", []),
        )

        if df.empty:
            st.write("The database returned no matching rows.")

        else:
            st.dataframe(
                df,
                width="stretch",
                hide_index=True,
            )

            st.download_button(
                "Download supporting data as CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="query_results.csv",
                mime="text/csv",
                width="stretch",
            )


# ---------------- SEARCH HISTORY ----------------

st.divider()
st.subheader("🕘 Recent Question History")

history_col, clear_col = st.columns([3, 1])

with history_col:
    st.caption("Review previous questions and answers.")

with clear_col:
    clear_history = st.button(
        "🗑️ Clear history",
        width="stretch",
    )


if clear_history:
    try:
        clear_response = requests.delete(
            f"{API_BASE}/history",
            timeout=15,
        )

        if clear_response.ok:
            st.session_state["last_result"] = None
            st.success("Search history cleared.")
            st.rerun()

        elif clear_response.status_code == 404:
            st.error(
                "The backend does not yet implement DELETE /history. "
                "Add that endpoint to FastAPI to clear server-side history."
            )

        else:
            st.error(
                f"Could not clear history. "
                f"HTTP {clear_response.status_code}: "
                f"{clear_response.text}"
            )

    except requests.RequestException:
        st.error(
            "Cannot connect to the backend to clear history."
        )


try:
    history_response = requests.get(
        f"{API_BASE}/history?limit=20",
        timeout=10,
    )

    if history_response.ok:
        items = history_response.json().get("items", [])

        if items:
            history_df = pd.DataFrame(items)

            # Hide generated SQL in the history panel.
            if "sql" in history_df.columns:
                history_df = history_df.drop(columns=["sql"])

            st.dataframe(
                history_df,
                width="stretch",
                hide_index=True,
            )

        else:
            st.caption("No questions yet.")

    else:
        st.caption(
            f"History is unavailable (HTTP "
            f"{history_response.status_code})."
        )

except requests.RequestException:
    st.caption(
        "Start the backend to view question history."
    )