import os
import time
import uuid
import hashlib
import jwt
from flask import Flask, request, jsonify, redirect, render_template_string

app = Flask(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET", "shared-jwt-signing-key-2026")
CLIENT_ID = os.environ.get("CLIENT_ID", "devconnect-portal")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "dcp-s3cr3t-k3y-2026-xT9mK4")

USERS = {
    "developer": {
        "password": "d3v2026!",
        "role": "developer",
        "scope": "read",
        "name": "Dev User"
    }
}

auth_codes = {}

PATCHED = False

LOGIN_TEMPLATE = """<!DOCTYPE html>
<html>
<head><title>Sign In</title>
<style>
  body { font-family: sans-serif; background: #f5f5f5; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
  .card { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); width: 320px; }
  h2 { margin-top: 0; color: #333; }
  input { width: 100%; padding: 8px; margin: 6px 0 12px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
  button { width: 100%; padding: 10px; background: #2563eb; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
  button:hover { background: #1d4ed8; }
  .error { color: #dc2626; font-size: 13px; }
  .info { color: #666; font-size: 12px; margin-top: 12px; }
</style>
</head>
<body>
<div class="card">
  <h2>Sign In</h2>
  {% if error %}<p class="error">{{ error }}</p>{% endif %}
  <form method="POST" action="/oauth/authorize">
    <input type="hidden" name="client_id" value="{{ client_id }}">
    <input type="hidden" name="redirect_uri" value="{{ redirect_uri }}">
    <input type="hidden" name="scope" value="{{ scope }}">
    <input type="hidden" name="state" value="{{ state }}">
    <input type="hidden" name="response_type" value="code">
    <label>Username</label>
    <input type="text" name="username" required>
    <label>Password</label>
    <input type="password" name="password" required>
    <button type="submit">Authorize</button>
  </form>
  <p class="info">Sign in to authorize application access.</p>
</div>
</body>
</html>"""


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/.well-known/openid-configuration")
def openid_config():
    return jsonify({
        "issuer": "http://auth-server:8080",
        "authorization_endpoint": "http://auth-server:8080/oauth/authorize",
        "token_endpoint": "http://auth-server:8080/oauth/token",
        "userinfo_endpoint": "http://auth-server:8080/oauth/userinfo",
        "grant_types_supported": ["authorization_code", "client_credentials"],
        "response_types_supported": ["code"],
        "scopes_supported": ["read", "write", "admin"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"]
    })


@app.route("/oauth/authorize", methods=["GET"])
def authorize_get():
    client_id = request.args.get("client_id", "")
    redirect_uri = request.args.get("redirect_uri", "")
    scope = request.args.get("scope", "read")
    state = request.args.get("state", "")

    return render_template_string(
        LOGIN_TEMPLATE,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state,
        error=None
    )


@app.route("/oauth/authorize", methods=["POST"])
def authorize_post():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    client_id = request.form.get("client_id", "")
    redirect_uri = request.form.get("redirect_uri", "")
    scope = request.form.get("scope", "read")
    state = request.form.get("state", "")

    user = USERS.get(username)
    if not user or user["password"] != password:
        return render_template_string(
            LOGIN_TEMPLATE,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            state=state,
            error="Invalid credentials"
        ), 401

    code = hashlib.sha256(f"{username}{time.time()}{uuid.uuid4()}".encode()).hexdigest()[:32]
    auth_codes[code] = {
        "username": username,
        "scope": user["scope"],
        "role": user["role"],
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "created_at": time.time()
    }

    if redirect_uri:
        sep = "&" if "?" in redirect_uri else "?"
        return redirect(f"{redirect_uri}{sep}code={code}&state={state}")

    return jsonify({"code": code, "state": state})


@app.route("/oauth/token", methods=["POST"])
def token():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    grant_type = data.get("grant_type")
    provided_client_id = data.get("client_id", "")
    provided_client_secret = data.get("client_secret", "")

    if provided_client_id != CLIENT_ID or provided_client_secret != CLIENT_SECRET:
        return jsonify({"error": "invalid_client", "error_description": "Client authentication failed"}), 401

    if grant_type == "authorization_code":
        code = data.get("code", "")
        code_data = auth_codes.pop(code, None)

        if not code_data:
            return jsonify({"error": "invalid_grant", "error_description": "Invalid or expired authorization code"}), 400

        if time.time() - code_data["created_at"] > 600:
            return jsonify({"error": "invalid_grant", "error_description": "Authorization code expired"}), 400

        payload = {
            "sub": code_data["username"],
            "role": code_data["role"],
            "scope": code_data["scope"],
            "iss": "auth-server",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600
        }
        access_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

        return jsonify({
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": code_data["scope"]
        })

    elif grant_type == "client_credentials":
        requested_scope = data.get("scope", "read")

        if PATCHED:
            allowed_scopes = ["read"]
            if requested_scope not in allowed_scopes:
                return jsonify({
                    "error": "invalid_scope",
                    "error_description": "Requested scope is not allowed for this grant type"
                }), 400
            scope = "read"
            role = "service"
        else:
            # VULNERABILITY: No scope validation for client_credentials grant
            # Any requested scope is blindly accepted
            scope = requested_scope
            role = "admin" if "admin" in requested_scope else "service"

        payload = {
            "sub": "service-account",
            "role": role,
            "scope": scope,
            "iss": "auth-server",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600
        }
        access_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

        return jsonify({
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": scope
        })

    return jsonify({"error": "unsupported_grant_type"}), 400


@app.route("/oauth/userinfo")
def userinfo():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "invalid_token"}), 401

    token_str = auth_header[7:]
    try:
        payload = jwt.decode(token_str, JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return jsonify({"error": "invalid_token"}), 401

    return jsonify({
        "sub": payload.get("sub"),
        "role": payload.get("role"),
        "scope": payload.get("scope")
    })


@app.route("/api/patch-status", methods=["GET", "POST"])
def patch_status():
    global PATCHED
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        PATCHED = data.get("patched", True)
        return jsonify({"patched": PATCHED})
    return jsonify({"patched": PATCHED})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
