#!/usr/bin/env python3
"""Strike7 Internal Configuration Portal - Development Build"""

from flask import Flask, request, jsonify
import os
import secrets

app = Flask(__name__)

FLAG = os.environ.get('FLAG', f"S7BEN{{debug_m0de_{secrets.token_hex(6)}}}")
app.config['FLAG'] = FLAG
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))

# Simulated internal service config store (intentionally incomplete)
SERVICE_CONFIG = {
    "db_host": "db.internal",
    "db_port": "5432",
    "cache_ttl": "3600",
    "log_level": "INFO",
    "max_connections": "100",
}


@app.route("/")
def index():
    return (
        "<!DOCTYPE html><html><head><title>Strike7 Internal Portal</title></head>"
        "<body><h1>Strike7 Internal Configuration Portal</h1>"
        "<p>Configuration management for internal microservices.</p>"
        "<ul>"
        "<li><a href='/api/config?key=log_level'>View: log_level</a></li>"
        "<li><a href='/api/config?key=cache_ttl'>View: cache_ttl</a></li>"
        "<li><a href='/api/config?key=db_port'>View: db_port</a></li>"
        "<li><a href='/health'>Health check</a></li>"
        "</ul></body></html>"
    )


@app.route("/api/config")
def api_config():
    """Returns a service configuration value by key.

    Raises KeyError (→ 500) when 'key' param is absent or not in SERVICE_CONFIG.
    In debug mode, this exposes the Werkzeug interactive debugger.
    """
    key = request.args.get("key")
    value = SERVICE_CONFIG[key]   # KeyError triggers Werkzeug debugger when debug=True
    return jsonify({"key": key, "value": value})


@app.route("/health")
def health():
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8103, debug=True)
