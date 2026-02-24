#!/usr/bin/env python3
from flask import Flask, request, jsonify, session
import secrets, string, time, threading

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
FLAG = f"S7BEN{{r4ce_c0nd1t10n_d0uble_spend_{''.join(secrets.choice(string.ascii_lowercase+string.digits) for _ in range(12))}}}"

# Write flag for dashboard dynamic validation
try:
    with open('/tmp/flag.txt', 'w') as _flag_file:
        _flag_file.write(FLAG)
except Exception:
    pass


BALANCES = {}
PURCHASES = {}
LOCK = threading.Lock()
TELEMETRY = {'start_time': time.time(), 'race_attacks': 0, 'flag_captured': False}

@app.route('/')
def index():
    return '<html><body><h1>S7BEN-VHARD-013</h1><p>POST /register {"username":"..."}</p><p>POST /checkout {"item_id":1}</p><p>GET /purchases - View purchases</p></body></html>'

@app.route('/register', methods=['POST'])
def register():
    username = request.json.get('username', 'user')
    BALANCES[username] = 100  # Start with $100
    session['user'] = username
    return jsonify({'status': 'success', 'balance': 100})

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    user = session['user']
    item_id = request.json.get('item_id', 1)
    price = 90  # Premium item costs $90

    if BALANCES.get(user, 0) >= price:
        time.sleep(0.01)  # Simulate processing delay
        BALANCES[user] -= price

        if user not in PURCHASES:
            PURCHASES[user] = []
        PURCHASES[user].append(item_id)

        if len(PURCHASES[user]) >= 2:  # Double spend detected
            TELEMETRY['race_attacks'] += 1

        return jsonify({'status': 'success', 'balance': BALANCES[user], 'purchases': len(PURCHASES[user])})

    return jsonify({'error': 'Insufficient balance'}), 400

@app.route('/purchases')
def purchases():
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    user = session['user']
    count = len(PURCHASES.get(user, []))

    if count >= 2 and not TELEMETRY['flag_captured']:
        TELEMETRY['flag_captured'] = True
        return jsonify({'purchases': count, 'flag': FLAG})

    return jsonify({'purchases': count, 'message': 'Purchase more items to qualify'})

@app.route('/api/telemetry')
def telemetry():
    return jsonify({'benchmark': 'S7BEN-VHARD-013', 'metrics': TELEMETRY})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8096, debug=False, threaded=True)
