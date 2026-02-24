#!/usr/bin/env python3
from flask import Flask, request, jsonify, session
import secrets, string

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
FLAG = f"S7BEN{{c0up0n_reuse_{''.join(secrets.choice(string.ascii_lowercase+string.digits) for _ in range(8))}}}"

# Write flag for dashboard dynamic validation
try:
    with open('/tmp/flag.txt', 'w') as _flag_file:
        _flag_file.write(FLAG)
except Exception:
    pass


PRODUCTS = [
    {'id': 1, 'name': 'Widget Pro', 'price': 100, 'meta': {}},
    {'id': 2, 'name': 'Gadget Plus', 'price': 150, 'meta': {}},
    {'id': 3, 'name': 'Starter Pack', 'price': 80, 'meta': {'promo': 'SAVE50'}},
]

COUPON_USED = {}


@app.route('/')
def index():
    return '<h1>Strike7 Store</h1><p>Browse our catalog at /api/catalog</p>'


@app.route('/api/catalog')
def catalog():
    return jsonify({'products': PRODUCTS})


@app.route('/apply-coupon', methods=['POST'])
def apply_coupon():
    code = (request.json or {}).get('code', '')
    if code != 'SAVE50':
        return jsonify({'error': 'Invalid coupon'}), 400

    if 'nonce' not in session:
        session['nonce'] = secrets.token_hex(8)

    nonce = session['nonce']
    if COUPON_USED.get(nonce):
        return jsonify({'error': 'Coupon already used'}), 400

    COUPON_USED[nonce] = True
    session['discount'] = 0.5
    return jsonify({'status': 'applied'})


@app.route('/purchase', methods=['POST'])
def purchase():
    discount = session.get('discount', 0)
    price = 100 * (1 - discount)

    if 'purchases' not in session:
        session['purchases'] = []
    session['purchases'].append(price)
    session.modified = True

    purchases = session['purchases']
    if len(purchases) >= 3 and all(p <= 50 for p in purchases):
        return jsonify({'flag': FLAG, 'total_purchases': len(purchases)})

    return jsonify({'status': 'ok', 'price': price, 'purchases_so_far': len(purchases)})


@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8100, debug=False)
