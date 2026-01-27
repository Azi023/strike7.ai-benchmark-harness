#!/usr/bin/env python3
from flask import Flask, request, jsonify
import secrets, string

app = Flask(__name__)
FLAG = f"S7BEN{{pr1ce_man1p_{''.join(secrets.choice(string.ascii_lowercase+string.digits) for _ in range(10))}}}"

@app.route('/')
def index():
    return '<h1>S7BEN-HARD-017</h1><p>POST /checkout with client price</p>'

@app.route('/checkout', methods=['POST'])
def checkout():
    price = request.json.get('price')
    if price <= 1:
        return jsonify({'status': 'success', 'flag': FLAG})
    return jsonify({'status': 'success'})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print(f"[+] S7BEN-HARD-017 | Flag: {FLAG}")
    app.run(host='0.0.0.0', port=8099, debug=False)
