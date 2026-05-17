from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)
AUTH_URL = os.environ.get("AUTH_URL", "http://auth")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

print(f"[api] starting with AUTH_URL={AUTH_URL} LOG_LEVEL={LOG_LEVEL}", flush=True)

@app.route("/data")
def data():
    token = request.args.get("token", "")
    r = requests.get(f"{AUTH_URL}/verify", params={"token": token})
    if r.status_code != 200:
        return jsonify({"error": "auth call failed"}), 502
    user_info = r.json()
    if not user_info.get("valid"):
        return jsonify({"error": "invalid token"}), 401
    return jsonify({
        "data": "secret-data",
        "for_user": user_info["user"],
        "log_level": LOG_LEVEL,
    })

@app.route("/health")
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

