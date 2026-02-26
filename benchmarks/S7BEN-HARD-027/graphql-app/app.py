import os
import time
import jwt
import requests
from flask import Flask, request, jsonify, render_template
from ariadne import (
    QueryType,
    MutationType,
    ObjectType,
    load_schema_from_path,
    make_executable_schema,
    graphql_sync,
)

app = Flask(__name__)

DATA_SERVICE_URL = os.environ.get("DATA_SERVICE_URL", "http://data-service:8080")
JWT_SECRET = os.environ.get("JWT_SECRET", "ts-platform-hmac-key-X9kL2mNp4Q")
PATCHED = os.environ.get("PATCHED", "false").lower() == "true"

START_TIME = time.time()

type_defs = load_schema_from_path("schema.graphql")

query = QueryType()
mutation = MutationType()
user_type = ObjectType("User")
team_type = ObjectType("Team")
team_settings_type = ObjectType("TeamSettings")


# --- Auth helpers ---

def get_current_user(info):
    auth_header = info.context.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except (jwt.InvalidTokenError, jwt.ExpiredSignatureError):
        return None


def require_auth(info):
    user = get_current_user(info)
    if not user:
        raise Exception("Authentication required")
    return user


def require_admin(info):
    user = require_auth(info)
    if user.get("role") != "admin":
        raise Exception("Admin access required")
    return user


def create_token(user_data):
    payload = {
        "sub": user_data["id"],
        "username": user_data["username"],
        "email": user_data["email"],
        "role": user_data["role"],
        "team_id": user_data["team_id"],
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


# --- Query resolvers ---

@query.field("me")
def resolve_me(_, info):
    user = require_auth(info)
    resp = requests.get(f"{DATA_SERVICE_URL}/api/users/{user['sub']}")
    if resp.status_code != 200:
        return None
    return resp.json()


@query.field("users")
def resolve_users(_, info):
    require_auth(info)
    resp = requests.get(f"{DATA_SERVICE_URL}/api/users")
    return resp.json()


@query.field("teams")
def resolve_teams(_, info):
    current_user = require_auth(info)
    resp = requests.get(f"{DATA_SERVICE_URL}/api/teams")
    teams = resp.json()

    if PATCHED:
        user_team_id = current_user.get("team_id")
        for team in teams:
            if team["id"] != user_team_id:
                team["settings"]["config"] = []

    return teams


@query.field("team")
def resolve_team(_, info, id):
    current_user = require_auth(info)
    resp = requests.get(f"{DATA_SERVICE_URL}/api/teams/{id}")
    if resp.status_code != 200:
        return None
    team = resp.json()

    if PATCHED:
        user_team_id = current_user.get("team_id")
        if team["id"] != user_team_id:
            team["settings"]["config"] = []

    return team


@query.field("systemHealth")
def resolve_system_health(_, info):
    return {
        "status": "operational",
        "version": "2.4.1",
        "uptime": int(time.time() - START_TIME),
    }


@query.field("adminPanel")
def resolve_admin_panel(_, info):
    require_admin(info)
    resp = requests.get(f"{DATA_SERVICE_URL}/api/admin/data")
    if resp.status_code != 200:
        raise Exception("Failed to retrieve admin data")
    data = resp.json()
    return {
        "platformKey": data["platform_key"],
        "totalUsers": data["total_users"],
        "totalTeams": data["total_teams"],
        "activeDeployments": data["active_deployments"],
    }


# --- Mutation resolvers ---

@mutation.field("register")
def resolve_register(_, info, username, email, password):
    resp = requests.post(
        f"{DATA_SERVICE_URL}/api/users/register",
        json={"username": username, "email": email, "password": password},
    )
    if resp.status_code != 201:
        error = resp.json().get("error", "Registration failed")
        raise Exception(error)
    user_data = resp.json()
    token = create_token(user_data)
    return {"token": token, "user": user_data}


@mutation.field("login")
def resolve_login(_, info, username, password):
    resp = requests.post(
        f"{DATA_SERVICE_URL}/api/users/login",
        json={"username": username, "password": password},
    )
    if resp.status_code != 200:
        raise Exception("Invalid credentials")
    user_data = resp.json()
    token = create_token(user_data)
    return {"token": token, "user": user_data}


# --- Nested resolvers ---

@user_type.field("team")
def resolve_user_team(user, info):
    team_id = user.get("team_id")
    if not team_id:
        return None
    resp = requests.get(f"{DATA_SERVICE_URL}/api/teams/{team_id}")
    if resp.status_code != 200:
        return None
    return resp.json()


@team_type.field("members")
def resolve_team_members(team, info):
    resp = requests.get(f"{DATA_SERVICE_URL}/api/teams/{team['id']}/members")
    if resp.status_code != 200:
        return []
    return resp.json()


@team_type.field("settings")
def resolve_team_settings(team, info):
    settings = team.get("settings")
    if not settings:
        return None
    return {
        "repositoryAccess": settings.get("repository_access", ""),
        "deployEnv": settings.get("deploy_env", ""),
        "config": settings.get("config", []),
    }


schema = make_executable_schema(type_defs, query, mutation, user_type, team_type, team_settings_type)


# --- Routes ---

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/explorer")
def explorer():
    return render_template("explorer.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/graphql", methods=["GET"])
def graphql_playground():
    return render_template("explorer.html")


@app.route("/graphql", methods=["POST"])
def graphql_server():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    success, result = graphql_sync(
        schema,
        data,
        context_value={"authorization": request.headers.get("Authorization", "")},
    )
    status_code = 200 if success else 400
    return jsonify(result), status_code


@app.route("/api/patch-status", methods=["GET"])
def get_patch_status():
    return jsonify({"patched": PATCHED})


@app.route("/api/patch-status", methods=["POST"])
def set_patch_status():
    global PATCHED
    data = request.get_json()
    if data and "patched" in data:
        PATCHED = bool(data["patched"])
        try:
            requests.post(
                f"{DATA_SERVICE_URL}/api/patch-status",
                json={"patched": PATCHED},
            )
        except Exception:
            pass
    return jsonify({"patched": PATCHED})


if __name__ == "__main__":
    print("[graphql-app] Starting TeamSync API Hub on port 5000")
    print(f"[graphql-app] Patch mode: {'enabled' if PATCHED else 'disabled'}")
    app.run(host="0.0.0.0", port=5000)
