
import re
import ollama

from app.config import OLLAMA_HOST, OLLAMA_MODEL
from app.schema_inspector import get_schema_text


SYSTEM_PROMPT = """
You are a SQLite SQL query generator.

Return exactly one SQLite SELECT query and nothing else.
Never output reasoning, explanations, or markdown code fences.

Rules:
1. Use only tables and columns in the supplied schema.
2. Generate only one read-only SQL statement.
3. Never generate INSERT, UPDATE, DELETE, DROP, ALTER,
   CREATE, ATTACH, or PRAGMA statements.
4. Use explicit JOIN conditions.
5. For sales revenue, use
   SUM(order_items.quantity * order_items.unit_price).
6. Exclude cancelled orders for realized-sales questions
   unless cancellations are explicitly requested.
7. The sample data covers 2025.
8. If the question cannot be answered from the schema,
   return exactly CANNOT_ANSWER.
9. Never invent columns or tables.
10. For detail-row queries, use LIMIT 100 unless the user
    requests a smaller limit.

Output only the SQL query.
"""


def generate_sql(question: str) -> str:
    client = ollama.Client(host=OLLAMA_HOST)

    response = client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    f"Database schema:\n{get_schema_text()}\n\n"
                    f"Question: {question}\n\n"
                    "Return only the SQL query. No explanation."
                ),
            },
        ],
        options={
            "temperature": 0,
            "num_predict": 256,
        },
        think=False,
    )

    # Read the response from Ollama.
    try:
        content = response.message.content.strip()
    except AttributeError:
        content = response["message"]["content"].strip()

    # Remove Qwen reasoning tags, if present.
    content = re.sub(
        r"<think>.*?</think>",
        "",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    ).strip()

    # Remove Markdown code fences.
    content = re.sub(
        r"^\s*```(?:sql)?\s*",
        "",
        content,
        flags=re.IGNORECASE,
    )
    content = re.sub(r"\s*```\s*$", "", content).strip()

    if content.upper() == "CANNOT_ANSWER":
        raise ValueError(
            "I cannot answer that from the available sales database schema."
        )

    # Extract a single SQL statement if the model adds commentary.
    match = re.search(
        r"\b(?:SELECT|WITH)\b.*?(?:;|$)",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not match:
        raise ValueError(
            f"The model did not return a SQL query: {content[:200]}"
        )

    content = match.group(0).strip()

    # Reject multiple statements; the SQL validator must also
    # enforce read-only execution and validate the full statement.
    if ";" in content.rstrip(";"):
        raise ValueError("Multiple SQL statements are not allowed.")

    return content
