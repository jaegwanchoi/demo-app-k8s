from flask import Flask, request, jsonify
import jwt, os, time, sqlite3

app = Flask(__name__)
SECRET = os.environ["JWT_SECRET"]
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
DB_PATH = os.environ.get("DB_PATH", "/data/users.db")

print(f"[auth] starting LOG_LEVEL={LOG_LEVEL} DB_PATH={DB_PATH}", flush=True)

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY)")
    return conn

@app.route("/register", methods=["POST"])
def register():
    user = (request.get_json(silent=True) or {}).get("user", "")
    if not user:
        return jsonify({"error": "user required"}), 400
    try:
        with db() as conn:
            conn.execute("INSERT INTO users(name) VALUES (?)", (user,))
        return jsonify({"registered": user})
    except sqlite3.IntegrityError:
        return jsonify({"error": "already registered"}), 409

@app.route("/users")
def users():
    with db() as conn:
        rows = conn.execute("SELECT name FROM users ORDER BY name").fetchall()
    return jsonify({"users": [r[0] for r in rows]})

@app.route("/login", methods=["POST"])
def login():
    user = (request.get_json(silent=True) or {}).get("user", "")
    with db() as conn:
        row = conn.execute("SELECT 1 FROM users WHERE name=?", (user,)).fetchone()
    if not row:
        return jsonify({"error": "not registered"}), 404
    token = jwt.encode(
        {"user": user, "exp": int(time.time()) + 3600},
        SECRET,
        algorithm="HS256",
    )
    return jsonify({"token": token})

@app.route("/verify")
def verify():
    token = request.args.get("token", "")
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        return jsonify({"valid": True, "user": payload["user"]})
    except Exception as e:
        return jsonify({"valid": False, "error": str(e)}), 401

@app.route("/health")
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
