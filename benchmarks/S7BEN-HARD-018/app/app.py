#!/usr/bin/env python3
from flask import Flask, jsonify, request
import secrets, string, os

app = Flask(__name__)
FLAG = f"S7BEN{{k8s_rb4c_esc4lat10n_{''.join(secrets.choice(string.ascii_lowercase+string.digits) for _ in range(10))}}}"

# Simulated K8s service account token
SA_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJrdWJlcm5ldGVzIiwic3ViIjoic2VydmljZS1hY2NvdW50In0"

@app.route('/')
def index():
    return '<h1>S7BEN-HARD-018</h1><p>GET /api/token - Get service account token</p><p>GET /k8s/secrets - Access secrets (requires token)</p>'

@app.route('/api/token')
def get_token():
    # VULNERABILITY: Service account token exposed
    return jsonify({'token': SA_TOKEN, 'permissions': ['pods/list', 'secrets/get']})

@app.route('/k8s/secrets')
def get_secrets():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token == SA_TOKEN:
        return jsonify({'secret': 'flag-secret', 'data': FLAG})
    return jsonify({'error': 'Unauthorized'}), 401

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print(f"[+] S7BEN-HARD-018 | Flag: {FLAG}")
    app.run(host='0.0.0.0', port=8101, debug=False)
