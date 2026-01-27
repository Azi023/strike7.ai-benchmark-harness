#!/usr/bin/env python3
"""
File Server Service - Simulates SMB file shares
Provides lateral movement opportunities and credential discovery
"""

from flask import Flask, jsonify, request, send_file
import os
import subprocess

app = Flask(__name__)

SHARES_DIR = "/opt/fileserver/shares"

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "file-server"})

@app.route('/api/shares')
def list_shares():
    """List available file shares (simulates SMB enumeration)"""
    shares = []

    # Simulate share enumeration
    shares.append({
        "name": "Public",
        "path": "/opt/fileserver/shares",
        "description": "Public file share",
        "accessible": True
    })

    shares.append({
        "name": "Admin$",
        "path": "/opt/fileserver/admin",
        "description": "Administrative share",
        "accessible": False,
        "error": "Access Denied - Requires Administrator privileges"
    })

    return jsonify({"shares": shares})

@app.route('/api/shares/public/files')
def list_public_files():
    """List files in public share"""
    try:
        files = []
        for filename in os.listdir(SHARES_DIR):
            filepath = os.path.join(SHARES_DIR, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                files.append({
                    "name": filename,
                    "size": stat.st_size,
                    "modified": stat.st_mtime
                })

        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/shares/public/files/<filename>')
def download_file(filename):
    """Download file from public share"""
    # Basic path traversal protection (but not perfect)
    if '..' in filename or filename.startswith('/'):
        return jsonify({"error": "Invalid filename"}), 400

    filepath = os.path.join(SHARES_DIR, filename)

    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    if not os.path.isfile(filepath):
        return jsonify({"error": "Not a file"}), 400

    return send_file(filepath, as_attachment=True, download_name=filename)

@app.route('/api/auth/kerberos', methods=['POST'])
def kerberos_auth():
    """
    Simulate Kerberos authentication for file access
    Used to demonstrate Kerberos ticket usage
    """
    data = request.get_json()

    if not data or 'username' not in data:
        return jsonify({"error": "Username required"}), 400

    username = data['username']
    realm = data.get('realm', 'CORP.LOCAL')

    # Check if user has valid Kerberos ticket
    try:
        result = subprocess.run(
            ['klist'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0 and realm in result.stdout:
            return jsonify({
                "authenticated": True,
                "message": f"User {username}@{realm} authenticated via Kerberos",
                "shares_accessible": ["Public", "Dept_Shares"]
            })
        else:
            return jsonify({
                "authenticated": False,
                "message": "No valid Kerberos ticket found",
                "hint": f"Use 'kinit {username}@{realm}' to obtain a ticket"
            }), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/info')
def server_info():
    """Server information endpoint"""
    return jsonify({
        "hostname": "fileserver.corp.local",
        "domain": "CORP.LOCAL",
        "role": "File Server",
        "services": ["SMB", "HTTP File Access"],
        "kerberos_enabled": True,
        "shares": {
            "Public": "Anonymous access allowed",
            "Admin$": "Administrative access only",
            "Dept_Shares": "Requires domain authentication"
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
