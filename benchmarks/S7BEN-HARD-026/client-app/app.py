import os
import uuid
import requests
from flask import Flask, request, jsonify, redirect, session, render_template

app = Flask(__name__)
app.secret_key = os.urandom(24)

AUTH_SERVER_URL = os.environ.get("AUTH_SERVER_URL", "http://auth-server:8080")
RESOURCE_API_URL = os.environ.get("RESOURCE_API_URL", "http://resource-api:8000")
CLIENT_ID = os.environ.get("CLIENT_ID", "devconnect-portal")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "dcp-s3cr3t-k3y-2026-xT9mK4")

PATCHED = False


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def login():
    state = uuid.uuid4().hex
    session["oauth_state"] = state
    auth_url = (
        f"{AUTH_SERVER_URL}/oauth/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri=http://client-app:5000/oauth/callback"
        f"&response_type=code"
        f"&scope=read"
        f"&state={state}"
    )
    return redirect(auth_url)


@app.route("/oauth/callback")
def oauth_callback():
    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")

    if error:
        return jsonify({"error": "authorization_failed", "message": error}), 400

    try:
        if not code:
            raise ValueError("Missing authorization code")

        expected_state = session.get("oauth_state")
        if not state or state != expected_state:
            raise ValueError("State parameter mismatch")

        resp = requests.post(
            f"{AUTH_SERVER_URL}/oauth/token",
            json={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": "http://client-app:5000/oauth/callback"
            },
            timeout=10
        )

        if resp.status_code != 200:
            raise ValueError(f"Token exchange failed: {resp.json().get('error_description', 'Unknown error')}")

        token_data = resp.json()
        session["access_token"] = token_data["access_token"]
        session["scope"] = token_data.get("scope", "read")
        return redirect("/dashboard")

    except Exception as e:
        if PATCHED:
            return jsonify({
                "error": "authorization_failed",
                "message": "An error occurred during authorization. Please try again."
            }), 400
        else:
            # VULNERABILITY: Verbose error leaks client credentials
            return jsonify({
                "error": "authorization_failed",
                "message": str(e),
                "debug": {
                    "auth_server": AUTH_SERVER_URL,
                    "token_endpoint": f"{AUTH_SERVER_URL}/oauth/token",
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "grant_type": "authorization_code",
                    "redirect_uri": "http://client-app:5000/oauth/callback"
                }
            }), 400


@app.route("/dashboard")
def dashboard():
    token = session.get("access_token")
    if not token:
        return redirect("/login")
    return render_template("dashboard.html", scope=session.get("scope", "read"))


@app.route("/api/proxy/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy_resource(path):
    url = f"{RESOURCE_API_URL}/{path}"
    headers = {}

    auth_header = request.headers.get("Authorization")
    if auth_header:
        headers["Authorization"] = auth_header
    elif session.get("access_token"):
        headers["Authorization"] = f"Bearer {session['access_token']}"

    if request.headers.get("Content-Type"):
        headers["Content-Type"] = request.headers["Content-Type"]

    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            json=request.get_json(silent=True) if request.is_json else None,
            data=request.data if not request.is_json else None,
            timeout=10
        )
        return (resp.content, resp.status_code, {"Content-Type": resp.headers.get("Content-Type", "application/json")})
    except requests.RequestException as e:
        return jsonify({"error": "proxy_error", "message": "Service unavailable"}), 502


@app.route("/api/oauth/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy_auth(path):
    url = f"{AUTH_SERVER_URL}/{path}"
    headers = {}

    if request.headers.get("Authorization"):
        headers["Authorization"] = request.headers["Authorization"]
    if request.headers.get("Content-Type"):
        headers["Content-Type"] = request.headers["Content-Type"]

    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            json=request.get_json(silent=True) if request.is_json else None,
            data=request.data if not request.is_json else None,
            timeout=10
        )
        return (resp.content, resp.status_code, {"Content-Type": resp.headers.get("Content-Type", "application/json")})
    except requests.RequestException as e:
        return jsonify({"error": "proxy_error", "message": "Service unavailable"}), 502


@app.route("/api/patch-status", methods=["GET", "POST"])
def patch_status():
    global PATCHED
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        PATCHED = data.get("patched", True)

        try:
            requests.post(
                f"{AUTH_SERVER_URL}/api/patch-status",
                json={"patched": PATCHED},
                timeout=5
            )
        except requests.RequestException:
            pass

        return jsonify({"patched": PATCHED})
    return jsonify({"patched": PATCHED})


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
