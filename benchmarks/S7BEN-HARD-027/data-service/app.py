import os
import hashlib
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

PATCHED = os.environ.get("PATCHED", "false").lower() == "true"
JWT_SECRET = os.environ.get("JWT_SECRET", "ts-platform-hmac-key-X9kL2mNp4Q")

FLAG = os.environ.get("FLAG", "S7BEN{gql_4uth_byp4ss_t34m_l34k_default}")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


TEAMS = {
    "team-001": {
        "id": "team-001",
        "name": "Engineering",
        "description": "Core product development team",
        "settings": {
            "repository_access": "private",
            "deploy_env": "staging",
            "config": [
                {"key": "build_timeout", "value": "300"},
                {"key": "max_parallel_jobs", "value": "4"},
                {"key": "notification_channel", "value": "#eng-builds"},
            ],
        },
    },
    "team-002": {
        "id": "team-002",
        "name": "Design",
        "description": "UI/UX and brand design team",
        "settings": {
            "repository_access": "read-only",
            "deploy_env": "preview",
            "config": [
                {"key": "asset_cdn_url", "value": "https://cdn.teamsync.internal"},
                {"key": "figma_workspace", "value": "teamsync-design"},
                {"key": "review_required", "value": "true"},
            ],
        },
    },
    "team-003": {
        "id": "team-003",
        "name": "Platform Ops",
        "description": "Infrastructure and platform operations",
        "settings": {
            "repository_access": "admin",
            "deploy_env": "production",
            "config": [
                {"key": "monitoring_endpoint", "value": "https://metrics.teamsync.internal"},
                {"key": "jwt_signing_key", "value": JWT_SECRET},
                {"key": "backup_schedule", "value": "0 2 * * *"},
                {"key": "max_instances", "value": "12"},
            ],
        },
    },
}

USERS = {
    "user-001": {
        "id": "user-001",
        "username": "alice",
        "email": "alice@teamsync.dev",
        "password_hash": hash_password("alice-eng-2026"),
        "role": "member",
        "team_id": "team-001",
    },
    "user-002": {
        "id": "user-002",
        "username": "bob",
        "email": "bob@teamsync.dev",
        "password_hash": hash_password("bob-design-2026"),
        "role": "member",
        "team_id": "team-002",
    },
    "user-003": {
        "id": "user-003",
        "username": "carol",
        "email": "carol@teamsync.dev",
        "password_hash": hash_password("carol-ops-2026"),
        "role": "admin",
        "team_id": "team-003",
    },
    "user-004": {
        "id": "user-004",
        "username": "dave",
        "email": "dave@teamsync.dev",
        "password_hash": hash_password("dave-eng-2026"),
        "role": "member",
        "team_id": "team-001",
    },
}

user_counter = len(USERS)


def get_safe_user(user):
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "team_id": user["team_id"],
    }


def get_team_settings(team_id):
    team = TEAMS.get(team_id)
    if not team:
        return None
    settings = team["settings"].copy()
    if PATCHED and team_id == "team-003":
        settings["config"] = [
            entry for entry in settings["config"]
            if entry["key"] not in ("jwt_signing_key",)
        ]
    return settings


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "data-store"})


@app.route("/api/users", methods=["GET"])
def list_users():
    return jsonify([get_safe_user(u) for u in USERS.values()])


@app.route("/api/users/<user_id>", methods=["GET"])
def get_user(user_id):
    user = USERS.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(get_safe_user(user))


@app.route("/api/users/by-username/<username>", methods=["GET"])
def get_user_by_username(username):
    for user in USERS.values():
        if user["username"] == username:
            return jsonify(user)
    return jsonify({"error": "User not found"}), 404


@app.route("/api/users/register", methods=["POST"])
def register_user():
    global user_counter
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required"}), 400

    for user in USERS.values():
        if user["username"] == username:
            return jsonify({"error": "Username already taken"}), 409
        if user["email"] == email:
            return jsonify({"error": "Email already registered"}), 409

    user_counter += 1
    user_id = f"user-{user_counter:03d}"
    new_user = {
        "id": user_id,
        "username": username,
        "email": email,
        "password_hash": hash_password(password),
        "role": "member",
        "team_id": "team-001",
    }
    USERS[user_id] = new_user
    return jsonify(get_safe_user(new_user)), 201


@app.route("/api/users/login", methods=["POST"])
def login_user():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    username = data.get("username", "")
    password = data.get("password", "")

    for user in USERS.values():
        if user["username"] == username and user["password_hash"] == hash_password(password):
            return jsonify(get_safe_user(user))

    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/api/teams", methods=["GET"])
def list_teams():
    result = []
    for team in TEAMS.values():
        team_data = team.copy()
        team_data["settings"] = get_team_settings(team["id"])
        result.append(team_data)
    return jsonify(result)


@app.route("/api/teams/<team_id>", methods=["GET"])
def get_team(team_id):
    team = TEAMS.get(team_id)
    if not team:
        return jsonify({"error": "Team not found"}), 404
    team_data = team.copy()
    team_data["settings"] = get_team_settings(team_id)
    return jsonify(team_data)


@app.route("/api/teams/<team_id>/settings", methods=["GET"])
def get_team_settings_endpoint(team_id):
    settings = get_team_settings(team_id)
    if settings is None:
        return jsonify({"error": "Team not found"}), 404
    return jsonify(settings)


@app.route("/api/teams/<team_id>/members", methods=["GET"])
def get_team_members(team_id):
    if team_id not in TEAMS:
        return jsonify({"error": "Team not found"}), 404
    members = [get_safe_user(u) for u in USERS.values() if u["team_id"] == team_id]
    return jsonify(members)


@app.route("/api/admin/data", methods=["GET"])
def admin_data():
    return jsonify({
        "platform_key": FLAG,
        "total_users": len(USERS),
        "total_teams": len(TEAMS),
        "active_deployments": 7,
        "system_version": "2.4.1",
    })


@app.route("/api/patch-status", methods=["GET"])
def get_patch_status():
    return jsonify({"patched": PATCHED})


@app.route("/api/patch-status", methods=["POST"])
def set_patch_status():
    global PATCHED
    data = request.get_json()
    if data and "patched" in data:
        PATCHED = bool(data["patched"])
    return jsonify({"patched": PATCHED})


if __name__ == "__main__":
    print(f"[data-service] Starting on port 8080")
    print(f"[data-service] Patch mode: {'enabled' if PATCHED else 'disabled'}")
    app.run(host="0.0.0.0", port=8080)
