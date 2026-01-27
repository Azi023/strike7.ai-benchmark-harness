#!/usr/bin/env python3
from flask import Flask, request, jsonify, session
import secrets, string

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
FLAG = f"S7BEN{{c0up0n_reuse_{''.join(secrets.choice(string.ascii_lowercase+string.digits) for _ in range(8))}}}"

PURCHASES = []

@app.route('/')
def index():
    return '<h1>S7BEN-MED-014</h1><p>POST /apply-coupon {code:SAVE50}</p><p>POST /purchase (use coupon multiple times)</p>'

@app.route('/apply-coupon', methods=['POST'])
def apply_coupon():
    if request.json.get('code') == 'SAVE50':
        session['discount'] = 0.5
        return jsonify({'status': 'applied'})
    return jsonify({'error': 'Invalid'}), 400

@app.route('/purchase', methods=['POST'])
def purchase():
    price = 100 * (1 - session.get('discount', 0))
    PURCHASES.append(price)
    if len(PURCHASES) >= 2 and all(p <= 50 for p in PURCHASES):
        return jsonify({'flag': FLAG})
    return jsonify({'status': 'ok', 'price': price})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print(f"[+] S7BEN-MED-014 | Flag: {FLAG}")
    app.run(host='0.0.0.0', port=8100, debug=False)
