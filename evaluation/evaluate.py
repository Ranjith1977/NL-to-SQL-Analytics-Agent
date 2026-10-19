"""Small manual evaluation runner. Requires the FastAPI server and Ollama to be running."""
import json
import requests

API = "http://127.0.0.1:8000"
with open("evaluation/questions.json", encoding="utf-8") as f:
    cases = json.load(f)

passed = 0
for case in cases:
    print(f"\nQuestion: {case['question']}")
    try:
        response = requests.post(API + "/ask", json={"question": case["question"]}, timeout=180)
        if not response.ok:
            print("FAIL:", response.text)
            continue
        result = response.json()
        cols = {c.lower() for c in result["columns"]}
        expected = {c.lower() for c in case["expected_columns"]}
        matched = expected.issubset(cols)
        passed += int(matched)
        print("PASS" if matched else "CHECK", "| expected columns:", expected, "| actual:", cols)
        print("SQL:", result["sql"])
    except requests.RequestException as exc:
        print("ERROR:", exc)
print(f"\nExpected-column checks passed: {passed}/{len(cases)}")
print("This is a lightweight smoke test, not a full semantic-accuracy benchmark.")
