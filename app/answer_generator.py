import json
import ollama
from app.config import OLLAMA_HOST, OLLAMA_MODEL

def summarize_result(question: str, sql: str, df, max_rows: int = 12) -> str:
    preview = df.head(max_rows).to_dict(orient="records")
    if df.empty:
        return "The query ran successfully but returned no rows."
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": (
                    "Explain SQL query results in plain English. Be concise, factual, and use only the supplied result data. "
                    "Do not claim causation or invent facts. If the result is an aggregate, identify the leading value when clear."
                )},
                {"role": "user", "content": (
                    f"Question: {question}\nSQL: {sql}\nRows returned: {len(df)}\n"
                    f"Result preview JSON: {json.dumps(preview, default=str)}\n"
                    "Write a short answer based only on these results."
                )},
            ],
            options={"temperature": 0},
        )
        return response["message"]["content"].strip()
    except Exception:
        return f"Query succeeded and returned {len(df)} row(s). Review the result table below."
