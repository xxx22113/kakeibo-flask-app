from flask import Flask,request,jsonify,render_template,session,redirect,url_for,flash
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path
import sqlite3

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "kakeibo.db"
SCHEMA_PATH = APP_DIR / "schema.sql"

app = Flask(__name__)
app.secret_key = "change-me-very-secret"  # 本番は環境変数推奨


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    if not DB_PATH.exists():
        DB_PATH.touch()
    with get_conn() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def login_required():
    return "user_id" in session


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if not username or not password:
            flash("ユーザー名とパスワードを入力してください")
            return redirect(url_for("register"))

        pw_hash = generate_password_hash(password)

        try:
            with get_conn() as conn:
                conn.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, pw_hash),
                )
            flash("登録しました。ログインしてください。")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("そのユーザー名はすでに使われています")
            return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        with get_conn() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,),
            ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))

        flash("ユーザー名またはパスワードが違います")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/", methods=["GET", "POST"])
def index():
    if not login_required():
        return redirect(url_for("login"))

    user_id = session["user_id"]

    if request.method == "POST":
        # 家計簿の追加（user_id は session から）
        spent_date = request.form["spent_date"].strip()
        category = request.form["category"].strip()
        amount = int(request.form["amount"])
        memo = request.form.get("memo", "").strip()

        with get_conn() as conn:
            conn.execute(
                "INSERT INTO expenses (user_id, spent_date, category, amount, memo) VALUES (?, ?, ?, ?, ?)",
                (user_id, spent_date, category, amount, memo),
            )
        return redirect(url_for("index"))

    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM expenses WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()

    return render_template("index.html", rows=rows, username=session.get("username"))


"""@app.post("/api/expenses")
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
        return (
            jsonify(
                {"error": "spent_date/category/amount は必須（amountは0以上の整数）"}
            ),
            400,
        )

    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO expenses(spent_date, category, amount, memo) VALUES(?,?,?,?)",
            (spent_date, category, amount, memo),
        )
        new_id = cur.lastrowid

    return jsonify({"id": new_id}), 201
"""

@app.delete("/api/expenses/<int:expense_id>")
def delete_expense(expense_id: int):
    if not login_required():
        return jsonify({"error": "unauthorized"}), 401

    user_id = session["user_id"]

    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM expenses WHERE id = ? AND user_id = ?",
            (expense_id, user_id),
        )

    if cur.rowcount == 0:
        return jsonify({"ok": False, "error": "not_found"}), 404

    return jsonify({"ok": True})



if __name__ == "__main__":
    init_db()
    app.run(debug=True)
