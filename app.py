from flask import Flask, request, jsonify, render_template
import sqlite3
from pathlib import Path

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "kakeibo.db"
SCHEMA_PATH = APP_DIR / "schema.sql"

app = Flask(__name__)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not DB_PATH.exists():
        DB_PATH.touch()
    with get_conn() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/expenses")
def list_expenses():
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, spent_date, category, amount, memo, created_at
            FROM expenses
            ORDER BY spent_date DESC, id DESC
            """
        ).fetchall()

        total = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses"
        ).fetchone()["total"]

    return jsonify({"items": [dict(r) for r in rows], "total": total})


@app.post("/api/expenses")
def create_expense():
    data = request.get_json(force=True)

    spent_date = (data.get("spent_date") or "").strip()
    category = (data.get("category") or "").strip()
    memo = (data.get("memo") or "").strip()

    try:
        amount = int(data.get("amount"))
    except Exception:
        amount = None

    if not spent_date or not category or amount is None or amount < 0:
        return jsonify({"error": "spent_date/category/amount は必須（amountは0以上の整数）"}), 400

    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO expenses(spent_date, category, amount, memo) VALUES(?,?,?,?)",
            (spent_date, category, amount, memo),
        )
        new_id = cur.lastrowid

    return jsonify({"id": new_id}), 201


@app.delete("/api/expenses/<int:expense_id>")
def delete_expense(expense_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    return jsonify({"ok": True})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
