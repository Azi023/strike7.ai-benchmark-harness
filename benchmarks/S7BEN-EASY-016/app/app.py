#!/usr/bin/env python3
from flask import Flask, request, jsonify, session
import secrets, string

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
FLAG = f"S7BEN{{bus1ness_l0g1c_negat1ve_{''.join(secrets.choice(string.ascii_lowercase+string.digits) for _ in range(10))}}}"

# Write flag for dashboard dynamic validation
try:
    with open('/tmp/flag.txt', 'w') as _flag_file:
        _flag_file.write(FLAG)
except Exception:
    pass


BALANCES = {}
ITEMS = {'premium_flag': 1000}

@app.route('/')
def index():
    return '<h1>S7BEN-EASY-016</h1><p>POST /register</p><p>POST /cart/add {"item":"...","quantity":...}</p><p>GET /purchase?item=...</p>'

@app.route('/register', methods=['POST'])
def register():
    user = request.json.get('username', 'user')
    BALANCES[user] = 0
    session['user'] = user
    return jsonify({'balance': 0})

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user = session['user']
    item = request.json.get('item')
    qty = request.json.get('quantity', 1)
    
    price = 10
    BALANCES[user] -= price * qty
    
    return jsonify({'balance': BALANCES[user], 'message': f'Added {qty} items'})

@app.route('/purchase', methods=['GET'])
def purchase():
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user = session['user']
    item = request.args.get('item')
    
    if BALANCES[user] >= ITEMS[item]:
        return jsonify({'status': 'success', 'flag': FLAG})
    return jsonify({'error': 'Insufficient balance'}), 400

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8097, debug=False)
