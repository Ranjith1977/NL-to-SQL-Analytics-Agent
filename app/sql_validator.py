import re
import sqlglot
from sqlglot import exp
from app.schema_inspector import ALLOWED_TABLES

class UnsafeQueryError(ValueError):
    pass

def validate_sql(sql: str) -> str:
    if not sql or not sql.strip():
        raise UnsafeQueryError("The model did not return a SQL query.")
    cleaned = sql.strip()
    # Allow one optional trailing semicolon, reject statement chaining.
    if ";" in cleaned.rstrip(";"):
        raise UnsafeQueryError("Only one SQL statement is allowed.")
    cleaned = cleaned.rstrip(";").strip()

    try:
        statements = sqlglot.parse(cleaned, read="sqlite")
    except Exception as exc:
        raise UnsafeQueryError(f"SQL could not be parsed: {exc}") from exc
    if len(statements) != 1 or statements[0] is None:
        raise UnsafeQueryError("Only one SQL statement is allowed.")

    tree = statements[0]
    if not isinstance(tree, (exp.Select, exp.Subquery)):
        raise UnsafeQueryError("Only read-only SELECT queries are allowed.")
    if tree.find(exp.Select) is None:
        raise UnsafeQueryError("A SELECT query is required.")
    if tree.find(exp.Into) is not None:
        raise UnsafeQueryError("SELECT INTO is not allowed.")

    # Reject table-valued/unknown table references; CTE aliases are not physical tables.
    cte_names = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
    referenced_tables = set()
    for table in tree.find_all(exp.Table):
        name = table.name.lower()
        if name and name not in cte_names:
            referenced_tables.add(name)
    invalid = referenced_tables - ALLOWED_TABLES
    if invalid:
        raise UnsafeQueryError("Query references unsupported table(s): " + ", ".join(sorted(invalid)))

    # Disallow risky constructs and common file/network extensions.
    forbidden_nodes = (exp.Command, exp.Pragma, exp.Into)
    if any(tree.find(node) is not None for node in forbidden_nodes):
        raise UnsafeQueryError("This SQL construct is not allowed.")
    lowered = cleaned.lower()
    if re.search(r"\b(load_extension|readfile|writefile)\s*\(", lowered):
        raise UnsafeQueryError("Potentially unsafe SQLite function detected.")
    return cleaned
