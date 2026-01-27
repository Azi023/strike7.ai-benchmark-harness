#!/usr/bin/env python3
"""
Database Server API - Provides access to corporate database
Demonstrates credential storage and lateral movement opportunities
"""

from flask import Flask, jsonify
import psycopg2
import os

app = Flask(__name__)

DB_CONFIG = {
    'host': 'localhost',
    'database': 'corpdb',
    'user': 'postgres',
    'password': os.getenv('POSTGRES_PASSWORD', 'DBP@ssw0rd!')
}

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(**DB_CONFIG)

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({"status": "healthy", "service": "database-server"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/api/info')
def info():
    """Database server information"""
    return jsonify({
        "server": "dbserver.corp.local",
        "domain": "CORP.LOCAL",
        "database": "PostgreSQL 15",
        "kerberos_spn": "MSSQLSvc/dbserver.corp.local",
        "note": "This server is associated with svc_sql@CORP.LOCAL service account"
    })

@app.route('/api/users')
def list_users():
    """List database users (requires access from trusted hosts)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, email, department FROM users")
        users = []
        for row in cur.fetchall():
            users.append({
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "department": row[3]
            })
        cur.close()
        conn.close()
        return jsonify({"users": users})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/credentials')
def list_credentials():
    """
    List stored credentials - VULNERABLE ENDPOINT
    Should require authentication but doesn't
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT service, username, password, notes FROM credentials")
        creds = []
        for row in cur.fetchall():
            creds.append({
                "service": row[0],
                "username": row[1],
                "password": row[2],
                "notes": row[3]
            })
        cur.close()
        conn.close()
        return jsonify({
            "credentials": creds,
            "warning": "This endpoint should be restricted but is accessible"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Wait for PostgreSQL to be ready
    import time
    max_retries = 30
    for i in range(max_retries):
        try:
            conn = get_db_connection()
            conn.close()
            print("[+] Database connection established")
            break
        except Exception as e:
            if i < max_retries - 1:
                print(f"[*] Waiting for database... ({i+1}/{max_retries})")
                time.sleep(2)
            else:
                print(f"[!] Failed to connect to database: {e}")
                raise

    app.run(host='0.0.0.0', port=5000, debug=False)
