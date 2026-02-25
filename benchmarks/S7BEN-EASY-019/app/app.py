#!/usr/bin/env python3
"""
Atlassian Confluence Data Center Simulation
Simulates CVE-2023-22515: Broken access control allowing unauthenticated
admin account creation via the initial setup endpoints that remain
accessible after installation.
"""
import os
import secrets
import hashlib
import time
from flask import Flask, request, jsonify, Response, redirect, session, make_response

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Dynamic flag
FLAG = f"S7BEN{{confluence_cve_{secrets.token_hex(5)}}}"

with open("/app/flag.txt", "w") as f:
    f.write(FLAG)
try:
    with open("/tmp/flag.txt", "w") as f:
        f.write(FLAG)
except Exception:
    pass

# ─── Data Store ────────────────────────────────────────────────────────────────

CONFLUENCE_VERSION = "8.5.0"
BUILD_NUMBER = "9012"

USERS = {
    "admin": {
        "password": hashlib.sha256(secrets.token_hex(16).encode()).hexdigest(),
        "fullName": "System Administrator",
        "email": "admin@corp.local",
        "role": "admin",
    },
    "jdoe": {
        "password": hashlib.sha256("Welcome2026!".encode()).hexdigest(),
        "fullName": "Jane Doe",
        "email": "jdoe@corp.local",
        "role": "user",
    },
    "bsmith": {
        "password": hashlib.sha256("TeamCollab#1".encode()).hexdigest(),
        "fullName": "Bob Smith",
        "email": "bsmith@corp.local",
        "role": "user",
    },
}

SESSIONS = {}

SPACES = {
    "ENG": {
        "key": "ENG",
        "name": "Engineering",
        "description": "Engineering team documentation and technical specs",
        "type": "global",
    },
    "HR": {
        "key": "HR",
        "name": "Human Resources",
        "description": "HR policies, onboarding guides, and benefits information",
        "type": "global",
    },
    "IT": {
        "key": "IT",
        "name": "IT Operations",
        "description": "Infrastructure documentation and runbooks",
        "type": "global",
    },
    "PROD": {
        "key": "PROD",
        "name": "Product Management",
        "description": "Product roadmaps, feature specs, and release notes",
        "type": "global",
    },
}

PAGES = [
    {
        "id": 65537,
        "title": "Welcome to Confluence",
        "spaceKey": "ENG",
        "body": "This is the engineering team's collaboration space. Use this wiki to document technical designs, architecture decisions, and operational runbooks.",
        "creator": "admin",
        "lastModified": "2026-02-20T09:15:00Z",
        "version": 3,
    },
    {
        "id": 65538,
        "title": "Q1 2026 Sprint Planning",
        "spaceKey": "ENG",
        "body": "Sprint goals for Q1 include migration to microservices architecture, Kubernetes deployment automation, and observability stack improvements.",
        "creator": "jdoe",
        "lastModified": "2026-02-22T14:30:00Z",
        "version": 5,
    },
    {
        "id": 65539,
        "title": "Database Migration Runbook",
        "spaceKey": "ENG",
        "body": "Step-by-step guide for PostgreSQL 15 to 16 migration. Includes backup procedures, schema validation, and rollback plan.",
        "creator": "bsmith",
        "lastModified": "2026-02-24T11:45:00Z",
        "version": 2,
    },
    {
        "id": 65540,
        "title": "Employee Onboarding Guide",
        "spaceKey": "HR",
        "body": "Welcome to the team! This guide covers your first 30 days including system access requests, benefits enrollment, and team introductions.",
        "creator": "admin",
        "lastModified": "2026-01-15T08:00:00Z",
        "version": 7,
    },
    {
        "id": 65541,
        "title": "VPN and Remote Access Setup",
        "spaceKey": "IT",
        "body": "Instructions for configuring GlobalProtect VPN client, SSH key generation, and accessing internal services from remote locations.",
        "creator": "bsmith",
        "lastModified": "2026-02-18T16:20:00Z",
        "version": 4,
    },
    {
        "id": 65542,
        "title": "2026 Product Roadmap",
        "spaceKey": "PROD",
        "body": "High-level product roadmap for 2026. Key initiatives: AI-powered search, real-time collaboration, and enterprise SSO integration.",
        "creator": "jdoe",
        "lastModified": "2026-02-10T10:00:00Z",
        "version": 6,
    },
    {
        "id": 65543,
        "title": "Incident Response Procedures",
        "spaceKey": "IT",
        "body": "Severity classification, escalation matrix, and communication templates for production incidents. On-call rotation schedule included.",
        "creator": "admin",
        "lastModified": "2026-02-23T13:10:00Z",
        "version": 3,
    },
]


# ─── Helpers ───────────────────────────────────────────────────────────────────

def get_session_user():
    sid = request.cookies.get("JSESSIONID", "")
    if sid and sid in SESSIONS:
        return SESSIONS[sid]
    return None


def is_admin():
    user = get_session_user()
    if not user:
        return False
    udata = USERS.get(user)
    return udata and udata.get("role") == "admin"


# ─── Shared CSS ────────────────────────────────────────────────────────────────

CONFLUENCE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, sans-serif;
  background: #f4f5f7; color: #172b4d; }
a { color: #0052cc; text-decoration: none; }
a:hover { text-decoration: underline; }
.topbar { background: #0052cc; color: #fff; padding: 0 24px; height: 56px;
  display: flex; align-items: center; justify-content: space-between; }
.topbar .logo { font-size: 18px; font-weight: 600; letter-spacing: -0.5px; }
.topbar .logo span { opacity: 0.7; font-weight: 400; font-size: 13px; margin-left: 8px; }
.topbar nav a { color: rgba(255,255,255,0.85); margin-left: 24px; font-size: 14px; }
.topbar nav a:hover { color: #fff; text-decoration: none; }
.topbar .user-menu { font-size: 13px; color: rgba(255,255,255,0.8); }
.container { max-width: 1100px; margin: 0 auto; padding: 24px; }
.breadcrumb { font-size: 13px; color: #6b778c; margin-bottom: 16px; }
.breadcrumb a { color: #6b778c; }
.card { background: #fff; border-radius: 3px; box-shadow: 0 1px 3px rgba(23,43,77,0.12);
  padding: 24px; margin-bottom: 16px; }
.card h2 { font-size: 16px; color: #172b4d; margin-bottom: 12px; }
.card h3 { font-size: 14px; color: #172b4d; margin-bottom: 8px; }
.page-list { list-style: none; }
.page-list li { padding: 10px 0; border-bottom: 1px solid #ebecf0; }
.page-list li:last-child { border-bottom: none; }
.page-list .title { font-size: 14px; font-weight: 500; }
.page-list .meta { font-size: 12px; color: #6b778c; margin-top: 2px; }
.space-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }
.space-card { background: #fff; border-radius: 3px; padding: 20px;
  box-shadow: 0 1px 3px rgba(23,43,77,0.12); border-left: 4px solid #0052cc; }
.space-card h3 { font-size: 15px; margin-bottom: 6px; }
.space-card p { font-size: 13px; color: #6b778c; line-height: 1.5; }
.btn { display: inline-block; padding: 8px 16px; border-radius: 3px;
  font-size: 14px; cursor: pointer; border: none; }
.btn-primary { background: #0052cc; color: #fff; }
.btn-primary:hover { background: #0747a6; text-decoration: none; }
.sidebar { width: 240px; float: left; margin-right: 24px; }
.sidebar ul { list-style: none; }
.sidebar li { padding: 8px 12px; font-size: 14px; border-radius: 3px; }
.sidebar li:hover { background: #ebecf0; }
.sidebar li.active { background: #deebff; color: #0052cc; font-weight: 500; }
.main-content { overflow: hidden; }
.wiki-body { font-size: 14px; line-height: 1.7; color: #172b4d; }
.wiki-body p { margin-bottom: 12px; }
table.info-table { width: 100%; border-collapse: collapse; font-size: 13px; }
table.info-table th { text-align: left; padding: 8px 12px; background: #f4f5f7;
  color: #6b778c; border-bottom: 2px solid #dfe1e6; font-weight: 600; }
table.info-table td { padding: 8px 12px; border-bottom: 1px solid #ebecf0; }
.login-container { max-width: 400px; margin: 80px auto; }
.login-box { background: #fff; border-radius: 3px; padding: 32px;
  box-shadow: 0 2px 8px rgba(23,43,77,0.16); }
.login-box h1 { font-size: 20px; text-align: center; margin-bottom: 24px; color: #172b4d; }
.login-box .logo-area { text-align: center; margin-bottom: 24px; }
.login-box .logo-area .product { font-size: 24px; color: #0052cc; font-weight: 700; }
.login-box .logo-area .subtitle { font-size: 12px; color: #6b778c; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 13px; font-weight: 600;
  color: #172b4d; margin-bottom: 6px; }
.form-group input { width: 100%; padding: 8px 12px; border: 2px solid #dfe1e6;
  border-radius: 3px; font-size: 14px; }
.form-group input:focus { border-color: #0052cc; outline: none; }
.alert { padding: 12px 16px; border-radius: 3px; font-size: 13px; margin-bottom: 16px; }
.alert-error { background: #ffebe6; color: #bf2600; }
.alert-success { background: #e3fcef; color: #006644; }
.admin-layout { display: flex; min-height: calc(100vh - 56px); }
.admin-sidebar { width: 240px; background: #fff; border-right: 1px solid #dfe1e6;
  padding: 20px 0; }
.admin-sidebar h3 { font-size: 11px; text-transform: uppercase; letter-spacing: 1px;
  color: #6b778c; padding: 0 20px; margin-bottom: 8px; }
.admin-sidebar ul { list-style: none; margin-bottom: 20px; }
.admin-sidebar li a { display: block; padding: 8px 20px; font-size: 14px;
  color: #172b4d; }
.admin-sidebar li a:hover { background: #f4f5f7; text-decoration: none; }
.admin-sidebar li.active a { background: #deebff; color: #0052cc; }
.admin-main { flex: 1; padding: 24px 32px; }
.footer { text-align: center; padding: 24px; font-size: 11px; color: #97a0af; }
"""


# ─── Page Templates ────────────────────────────────────────────────────────────

def render_topbar(user=None):
    user_section = ""
    if user:
        udata = USERS.get(user, {})
        user_section = f"""<div class="user-menu">{udata.get('fullName', user)}
          | <a href="/logout.action" style="color:rgba(255,255,255,0.8)">Log out</a></div>"""
    else:
        user_section = '<a href="/login.action" class="btn" style="background:rgba(255,255,255,0.15);color:#fff;font-size:13px">Log in</a>'

    return f"""<div class="topbar">
  <div style="display:flex;align-items:center">
    <div class="logo">Confluence<span>Data Center</span></div>
    <nav>
      <a href="/dashboard.action">Dashboard</a>
      <a href="/spacedirectory/view.action">Spaces</a>
      <a href="/rest/api/content">API</a>
    </nav>
  </div>
  {user_section}
</div>"""


def page_wrapper(title, body, user=None):
    return f"""<!DOCTYPE html>
<html><head><title>{title} - Confluence</title>
<style>{CONFLUENCE_CSS}</style></head>
<body>{render_topbar(user)}{body}
<div class="footer">Atlassian Confluence {CONFLUENCE_VERSION} |
  Powered by <a href="#">Atlassian</a></div>
</body></html>"""


# ─── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/")
def root():
    return redirect("/dashboard.action")


@app.route("/dashboard.action")
def dashboard():
    user = get_session_user()

    recent_html = ""
    for p in sorted(PAGES, key=lambda x: x["lastModified"], reverse=True)[:5]:
        space = SPACES.get(p["spaceKey"], {})
        recent_html += f"""<li>
          <div class="title"><a href="/pages/viewpage.action?pageId={p['id']}">{p['title']}</a></div>
          <div class="meta">{space.get('name','')} &middot; Updated {p['lastModified'][:10]}
            by {USERS.get(p['creator'],{}).get('fullName', p['creator'])}</div>
        </li>"""

    spaces_html = ""
    for s in SPACES.values():
        spaces_html += f"""<div class="space-card">
          <h3><a href="/display/{s['key']}">{s['name']}</a></h3>
          <p>{s['description']}</p>
        </div>"""

    body = f"""<div class="container">
  <h1 style="font-size:24px;margin-bottom:24px">Dashboard</h1>
  <div style="display:grid;grid-template-columns:1fr 340px;gap:24px">
    <div>
      <div class="card">
        <h2>Recent Updates</h2>
        <ul class="page-list">{recent_html}</ul>
      </div>
    </div>
    <div>
      <div class="card">
        <h2>Your Spaces</h2>
        <div class="space-grid" style="grid-template-columns:1fr">{spaces_html}</div>
      </div>
    </div>
  </div>
</div>"""
    return page_wrapper("Dashboard", body, user)


# ─── Login / Logout ───────────────────────────────────────────────────────────

@app.route("/login.action", methods=["GET"])
def login_get():
    body = """<div class="login-container">
  <div class="login-box">
    <div class="logo-area">
      <div class="product">Confluence</div>
      <div class="subtitle">Log in to your account</div>
    </div>
    <form method="POST" action="/dologin.action">
      <div class="form-group">
        <label for="username">Username</label>
        <input type="text" id="username" name="os_username" autocomplete="off">
      </div>
      <div class="form-group">
        <label for="password">Password</label>
        <input type="password" id="password" name="os_password">
      </div>
      <button type="submit" class="btn btn-primary" style="width:100%;padding:10px">Log in</button>
    </form>
  </div>
</div>"""
    return page_wrapper("Log In", body)


@app.route("/dologin.action", methods=["POST"])
def do_login():
    username = request.form.get("os_username", "")
    password = request.form.get("os_password", "")
    pw_hash = hashlib.sha256(password.encode()).hexdigest()

    udata = USERS.get(username)
    if udata and udata["password"] == pw_hash:
        sid = secrets.token_hex(24)
        SESSIONS[sid] = username
        resp = make_response(redirect("/dashboard.action"))
        resp.set_cookie("JSESSIONID", sid, httponly=True, path="/")
        return resp

    body = """<div class="login-container">
  <div class="login-box">
    <div class="logo-area">
      <div class="product">Confluence</div>
      <div class="subtitle">Log in to your account</div>
    </div>
    <div class="alert alert-error">Incorrect username or password. Please try again.</div>
    <form method="POST" action="/dologin.action">
      <div class="form-group">
        <label for="username">Username</label>
        <input type="text" id="username" name="os_username" autocomplete="off">
      </div>
      <div class="form-group">
        <label for="password">Password</label>
        <input type="password" id="password" name="os_password">
      </div>
      <button type="submit" class="btn btn-primary" style="width:100%;padding:10px">Log in</button>
    </form>
  </div>
</div>"""
    return page_wrapper("Log In", body), 401


@app.route("/logout.action")
def logout():
    sid = request.cookies.get("JSESSIONID", "")
    if sid in SESSIONS:
        del SESSIONS[sid]
    resp = make_response(redirect("/login.action"))
    resp.set_cookie("JSESSIONID", "", expires=0, path="/")
    return resp


# ─── Space / Page Views ──────────────────────────────────────────────────────

@app.route("/display/<space_key>")
def display_space(space_key):
    user = get_session_user()
    space = SPACES.get(space_key)
    if not space:
        return page_wrapper("Not Found", '<div class="container"><div class="card"><h2>Space not found</h2></div></div>', user), 404

    space_pages = [p for p in PAGES if p["spaceKey"] == space_key]
    pages_html = ""
    for p in space_pages:
        pages_html += f"""<li>
          <div class="title"><a href="/pages/viewpage.action?pageId={p['id']}">{p['title']}</a></div>
          <div class="meta">Version {p['version']} &middot; Last modified {p['lastModified'][:10]}
            by {USERS.get(p['creator'],{}).get('fullName', p['creator'])}</div>
        </li>"""

    body = f"""<div class="container">
  <div class="breadcrumb"><a href="/dashboard.action">Dashboard</a> / {space['name']}</div>
  <div class="card">
    <h2>{space['name']}</h2>
    <p style="color:#6b778c;font-size:13px;margin-bottom:16px">{space['description']}</p>
    <h3>Pages</h3>
    <ul class="page-list">{pages_html if pages_html else '<li style="color:#6b778c">No pages in this space.</li>'}</ul>
  </div>
</div>"""
    return page_wrapper(space["name"], body, user)


@app.route("/pages/viewpage.action")
def view_page():
    user = get_session_user()
    page_id = request.args.get("pageId", type=int)
    page = next((p for p in PAGES if p["id"] == page_id), None)
    if not page:
        return page_wrapper("Not Found", '<div class="container"><div class="card"><h2>Page not found</h2></div></div>', user), 404

    space = SPACES.get(page["spaceKey"], {})
    body = f"""<div class="container">
  <div class="breadcrumb">
    <a href="/dashboard.action">Dashboard</a> /
    <a href="/display/{page['spaceKey']}">{space.get('name','')}</a> / {page['title']}
  </div>
  <div class="card">
    <h1 style="font-size:24px;margin-bottom:4px">{page['title']}</h1>
    <div style="font-size:12px;color:#6b778c;margin-bottom:20px">
      Created by {USERS.get(page['creator'],{}).get('fullName', page['creator'])}
      &middot; Version {page['version']} &middot; Last modified {page['lastModified']}
    </div>
    <div class="wiki-body"><p>{page['body']}</p></div>
  </div>
</div>"""
    return page_wrapper(page["title"], body, user)


@app.route("/spacedirectory/view.action")
def space_directory():
    user = get_session_user()
    spaces_html = ""
    for s in SPACES.values():
        page_count = len([p for p in PAGES if p["spaceKey"] == s["key"]])
        spaces_html += f"""<tr>
          <td><a href="/display/{s['key']}">{s['key']}</a></td>
          <td><a href="/display/{s['key']}">{s['name']}</a></td>
          <td>{s['description']}</td>
          <td>{page_count}</td>
        </tr>"""

    body = f"""<div class="container">
  <div class="breadcrumb"><a href="/dashboard.action">Dashboard</a> / Space Directory</div>
  <div class="card">
    <h2>Space Directory</h2>
    <table class="info-table">
      <tr><th>Key</th><th>Name</th><th>Description</th><th>Pages</th></tr>
      {spaces_html}
    </table>
  </div>
</div>"""
    return page_wrapper("Space Directory", body, user)


# ─── REST API (Noise Endpoints) ──────────────────────────────────────────────

@app.route("/rest/api/content")
def api_content():
    results = []
    for p in PAGES:
        results.append({
            "id": str(p["id"]),
            "type": "page",
            "title": p["title"],
            "space": {"key": p["spaceKey"]},
            "_links": {"webui": f"/pages/viewpage.action?pageId={p['id']}"},
        })
    return jsonify({
        "results": results,
        "start": 0,
        "limit": 25,
        "size": len(results),
        "_links": {"base": f"http://localhost:8108", "context": "/wiki"},
    })


@app.route("/rest/api/content/<int:content_id>")
def api_content_by_id(content_id):
    page = next((p for p in PAGES if p["id"] == content_id), None)
    if not page:
        return jsonify({"statusCode": 404, "message": "No content found with id: " + str(content_id)}), 404
    return jsonify({
        "id": str(page["id"]),
        "type": "page",
        "title": page["title"],
        "space": {"key": page["spaceKey"], "name": SPACES.get(page["spaceKey"], {}).get("name", "")},
        "version": {"number": page["version"]},
        "body": {"storage": {"value": page["body"]}},
        "history": {
            "createdBy": {"username": page["creator"]},
            "lastUpdated": {"when": page["lastModified"]},
        },
    })


@app.route("/rest/api/space")
def api_spaces():
    results = []
    for s in SPACES.values():
        results.append({
            "key": s["key"],
            "name": s["name"],
            "type": s["type"],
            "description": {"plain": {"value": s["description"]}},
            "_links": {"webui": f"/display/{s['key']}"},
        })
    return jsonify({
        "results": results,
        "start": 0,
        "limit": 25,
        "size": len(results),
    })


@app.route("/rest/api/user")
def api_user():
    user = get_session_user()
    if not user:
        return jsonify({"statusCode": 401, "message": "User is not logged in."}), 401
    udata = USERS[user]
    return jsonify({
        "username": user,
        "displayName": udata["fullName"],
        "email": udata["email"],
        "type": "known",
    })


# ─── Server Info (Recon Endpoint) ─────────────────────────────────────────────

@app.route("/server-info.action")
def server_info():
    user = get_session_user()
    body = f"""<div class="container">
  <div class="breadcrumb"><a href="/dashboard.action">Dashboard</a> / Server Info</div>
  <div class="card">
    <h2>Confluence Server Information</h2>
    <table class="info-table">
      <tr><td style="font-weight:600;width:200px">Version</td><td>{CONFLUENCE_VERSION}</td></tr>
      <tr><td style="font-weight:600">Build Number</td><td>{BUILD_NUMBER}</td></tr>
      <tr><td style="font-weight:600">Deployment Type</td><td>Data Center</td></tr>
      <tr><td style="font-weight:600">Java Version</td><td>11.0.21</td></tr>
      <tr><td style="font-weight:600">Operating System</td><td>Linux amd64</td></tr>
      <tr><td style="font-weight:600">Database</td><td>PostgreSQL 14.10</td></tr>
      <tr><td style="font-weight:600">Setup Complete</td><td>true</td></tr>
      <tr><td style="font-weight:600">Cluster Node</td><td>node-01</td></tr>
    </table>
  </div>
</div>"""
    return page_wrapper("Server Information", body, user)


# ─── CVE-2023-22515: Setup Endpoint (THE VULNERABILITY) ─────────────────────

@app.route("/setup/setupadministrator.action", methods=["GET"])
def setup_admin_get():
    return f"""<!DOCTYPE html>
<html><head><title>Confluence Setup - Create Administrator</title>
<style>{CONFLUENCE_CSS}</style></head>
<body>
<div style="background:#0052cc;padding:20px 24px;color:#fff">
  <div style="font-size:18px;font-weight:600">Confluence Setup Wizard</div>
  <div style="font-size:12px;opacity:0.7">Step 3 of 4 — Create Administrator Account</div>
</div>
<div class="login-container" style="margin-top:40px">
  <div class="login-box">
    <h1 style="font-size:18px">Create Administrator Account</h1>
    <form method="POST" action="/setup/setupadministrator.action">
      <input type="hidden" name="setupType" value="CUSTOM">
      <div class="form-group">
        <label>Username</label>
        <input type="text" name="username" required>
      </div>
      <div class="form-group">
        <label>Full Name</label>
        <input type="text" name="fullName" value="Administrator">
      </div>
      <div class="form-group">
        <label>Email</label>
        <input type="email" name="email" value="admin@localhost">
      </div>
      <div class="form-group">
        <label>Password</label>
        <input type="password" name="password" required>
      </div>
      <button type="submit" class="btn btn-primary" style="width:100%;padding:10px">Create Admin &amp; Continue</button>
    </form>
  </div>
</div>
</body></html>"""


@app.route("/setup/setupadministrator.action", methods=["POST"])
def setup_admin_post():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    full_name = request.form.get("fullName", "Administrator")
    email = request.form.get("email", "admin@localhost")

    if not username or not password:
        return jsonify({"status": "error", "message": "Username and password are required."}), 400

    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    USERS[username] = {
        "password": pw_hash,
        "fullName": full_name,
        "email": email,
        "role": "admin",
    }

    sid = secrets.token_hex(24)
    SESSIONS[sid] = username

    resp = make_response(redirect("/admin/configuration"))
    resp.set_cookie("JSESSIONID", sid, httponly=True, path="/")
    return resp


# ─── Admin Panel ──────────────────────────────────────────────────────────────

def admin_sidebar(active="general"):
    items = [
        ("general", "General Configuration", "/admin/configuration"),
        ("system", "System Information", "/admin/system-info"),
        ("users", "User Management", "/admin/users"),
        ("spaces", "Space Management", "/admin/spaces"),
        ("backup", "Backup & Restore", "/admin/backup"),
        ("license", "License Details", "/admin/license"),
    ]
    html = '<div class="admin-sidebar"><h3>Administration</h3><ul>'
    for key, label, href in items:
        cls = ' class="active"' if key == active else ""
        html += f"<li{cls}><a href=\"{href}\">{label}</a></li>"
    html += "</ul></div>"
    return html


@app.route("/admin/configuration")
def admin_config():
    if not is_admin():
        return redirect("/login.action")

    user = get_session_user()
    body = f"""<div class="admin-layout">
  {admin_sidebar("general")}
  <div class="admin-main">
    <h1 style="font-size:24px;margin-bottom:20px">General Configuration</h1>
    <div class="card">
      <h2>Site Configuration</h2>
      <table class="info-table">
        <tr><td style="font-weight:600;width:200px">Site Title</td><td>Corporate Wiki</td></tr>
        <tr><td style="font-weight:600">Base URL</td><td>https://confluence.corp.local</td></tr>
        <tr><td style="font-weight:600">Default Space</td><td>ENG</td></tr>
        <tr><td style="font-weight:600">Global Default Language</td><td>English (US)</td></tr>
      </table>
    </div>
    <div class="card">
      <h2>Collaborative Editing</h2>
      <table class="info-table">
        <tr><td style="font-weight:600;width:200px">Mode</td><td>Synchrony (Managed)</td></tr>
        <tr><td style="font-weight:600">Status</td><td style="color:#006644">Running</td></tr>
      </table>
    </div>
  </div>
</div>"""
    return page_wrapper("General Configuration", body, user)


@app.route("/admin/system-info")
def admin_system_info():
    if not is_admin():
        return redirect("/login.action")

    user = get_session_user()
    body = f"""<div class="admin-layout">
  {admin_sidebar("system")}
  <div class="admin-main">
    <h1 style="font-size:24px;margin-bottom:20px">System Information</h1>
    <div class="card">
      <h2>Application</h2>
      <table class="info-table">
        <tr><td style="font-weight:600;width:200px">Confluence Version</td><td>{CONFLUENCE_VERSION}</td></tr>
        <tr><td style="font-weight:600">Build Number</td><td>{BUILD_NUMBER}</td></tr>
        <tr><td style="font-weight:600">Deployment</td><td>Data Center (Clustered)</td></tr>
        <tr><td style="font-weight:600">Server ID</td><td>BXYZ-4F7G-H8J9-KL0M</td></tr>
        <tr><td style="font-weight:600">Support Entitlement</td><td>SEN-12345678</td></tr>
        <tr><td style="font-weight:600">Internal Key</td><td>{FLAG}</td></tr>
      </table>
    </div>
    <div class="card">
      <h2>Runtime</h2>
      <table class="info-table">
        <tr><td style="font-weight:600;width:200px">Java Version</td><td>11.0.21+9-LTS</td></tr>
        <tr><td style="font-weight:600">JVM</td><td>OpenJDK 64-Bit Server VM</td></tr>
        <tr><td style="font-weight:600">Max Memory</td><td>4096 MB</td></tr>
        <tr><td style="font-weight:600">Free Memory</td><td>1847 MB</td></tr>
        <tr><td style="font-weight:600">Total Memory</td><td>3072 MB</td></tr>
        <tr><td style="font-weight:600">Processors</td><td>4</td></tr>
      </table>
    </div>
    <div class="card">
      <h2>Database</h2>
      <table class="info-table">
        <tr><td style="font-weight:600;width:200px">Type</td><td>PostgreSQL</td></tr>
        <tr><td style="font-weight:600">Version</td><td>14.10</td></tr>
        <tr><td style="font-weight:600">Driver</td><td>PostgreSQL JDBC Driver 42.6.0</td></tr>
        <tr><td style="font-weight:600">URL</td><td>jdbc:postgresql://db:5432/confluence</td></tr>
      </table>
    </div>
  </div>
</div>"""
    return page_wrapper("System Information", body, user)


@app.route("/admin/users")
def admin_users():
    if not is_admin():
        return redirect("/login.action")

    user = get_session_user()
    rows = ""
    for uname, udata in USERS.items():
        rows += f"""<tr>
          <td>{uname}</td><td>{udata['fullName']}</td>
          <td>{udata['email']}</td><td>{udata['role']}</td>
        </tr>"""

    body = f"""<div class="admin-layout">
  {admin_sidebar("users")}
  <div class="admin-main">
    <h1 style="font-size:24px;margin-bottom:20px">User Management</h1>
    <div class="card">
      <h2>All Users</h2>
      <table class="info-table">
        <tr><th>Username</th><th>Full Name</th><th>Email</th><th>Role</th></tr>
        {rows}
      </table>
    </div>
  </div>
</div>"""
    return page_wrapper("User Management", body, user)


@app.route("/admin/spaces")
def admin_spaces():
    if not is_admin():
        return redirect("/login.action")
    return redirect("/spacedirectory/view.action")


@app.route("/admin/backup")
def admin_backup():
    if not is_admin():
        return redirect("/login.action")

    user = get_session_user()
    body = f"""<div class="admin-layout">
  {admin_sidebar("backup")}
  <div class="admin-main">
    <h1 style="font-size:24px;margin-bottom:20px">Backup &amp; Restore</h1>
    <div class="card">
      <h2>Latest Backup</h2>
      <table class="info-table">
        <tr><td style="font-weight:600;width:200px">Last Backup</td><td>2026-02-24 02:00:00 UTC</td></tr>
        <tr><td style="font-weight:600">Status</td><td style="color:#006644">Completed</td></tr>
        <tr><td style="font-weight:600">Size</td><td>2.4 GB</td></tr>
        <tr><td style="font-weight:600">Location</td><td>/var/atlassian/application-data/confluence/backups</td></tr>
      </table>
    </div>
  </div>
</div>"""
    return page_wrapper("Backup & Restore", body, user)


@app.route("/admin/license")
def admin_license():
    if not is_admin():
        return redirect("/login.action")

    user = get_session_user()
    body = f"""<div class="admin-layout">
  {admin_sidebar("license")}
  <div class="admin-main">
    <h1 style="font-size:24px;margin-bottom:20px">License Details</h1>
    <div class="card">
      <h2>Current License</h2>
      <table class="info-table">
        <tr><td style="font-weight:600;width:200px">Type</td><td>Confluence Data Center</td></tr>
        <tr><td style="font-weight:600">Organization</td><td>Corp Industries Inc.</td></tr>
        <tr><td style="font-weight:600">User Limit</td><td>500</td></tr>
        <tr><td style="font-weight:600">Expiry Date</td><td>2027-03-15</td></tr>
        <tr><td style="font-weight:600">Support Status</td><td style="color:#006644">Active</td></tr>
      </table>
    </div>
  </div>
</div>"""
    return page_wrapper("License Details", body, user)


# ─── Health ───────────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8108)
