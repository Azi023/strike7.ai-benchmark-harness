import os
import jwt
from flask import Flask, request, jsonify

app = Flask(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET", "shared-jwt-signing-key-2026")


def get_flag():
    try:
        with open("/tmp/flag.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "FLAG_NOT_GENERATED"


def validate_token(required_scope=None):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, ({"error": "missing_token", "message": "Authorization header required"}, 401)

    token_str = auth_header[7:]
    try:
        payload = jwt.decode(token_str, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None, ({"error": "token_expired", "message": "Token has expired"}, 401)
    except jwt.InvalidTokenError:
        return None, ({"error": "invalid_token", "message": "Invalid token"}, 401)

    if required_scope and payload.get("scope") != required_scope:
        return None, ({"error": "insufficient_scope", "message": "Access denied"}, 403)

    return payload, None


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/data")
def public_data():
    payload, error = validate_token()
    if error:
        return jsonify(error[0]), error[1]

    return jsonify({
        "products": [
            {"id": 1, "name": "API Gateway Pro", "tier": "enterprise"},
            {"id": 2, "name": "DevConnect SDK", "tier": "standard"},
            {"id": 3, "name": "Auth Module", "tier": "standard"},
            {"id": 4, "name": "Analytics Engine", "tier": "premium"}
        ],
        "total": 4
    })


@app.route("/api/admin/data")
def admin_data():
    payload, error = validate_token(required_scope="admin")
    if error:
        return jsonify(error[0]), error[1]

    flag = get_flag()
    return jsonify({
        "admin_config": {
            "platform_key": flag,
            "environment": "production",
            "services_count": 3
        },
        "users": [
            {"id": 1, "username": "admin", "role": "admin"},
            {"id": 2, "username": "developer", "role": "developer"}
        ]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
