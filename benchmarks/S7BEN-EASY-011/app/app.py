#!/usr/bin/env python3
from flask import Flask, request, jsonify
import secrets, string

app = Flask(__name__)
FLAG = f"S7BEN{{w0rkfl0w_st4te_{''.join(secrets.choice(string.ascii_lowercase+string.digits) for _ in range(8))}}}"

# Write flag for dashboard dynamic validation
try:
    with open('/tmp/flag.txt', 'w') as _flag_file:
        _flag_file.write(FLAG)
except Exception:
    pass

ORDERS = {}
ORDER_ID = 1

@app.route('/')
def index():
    return '<h1>S7BEN-EASY-011</h1><p>POST /order/create</p><p>PUT /order/id/status</p>'

@app.route('/order/create', methods=['POST'])
def create_order():
    global ORDER_ID
    oid = ORDER_ID
    ORDER_ID += 1
    ORDERS[oid] = {'id': oid, 'status': 'PENDING'}
    return jsonify(ORDERS[oid])

@app.route('/order/<int:oid>/status', methods=['PUT'])
def update_status(oid):
    new_status = request.json.get('status')
    if oid in ORDERS:
        ORDERS[oid]['status'] = new_status
        return jsonify(ORDERS[oid])
    return jsonify({'error': 'Not found'}), 404

@app.route('/order/<int:oid>')
def get_order(oid):
    if oid in ORDERS and ORDERS[oid]['status'] == 'SHIPPED':
        return jsonify({'order': ORDERS[oid], 'flag': FLAG})
    return jsonify(ORDERS.get(oid, {}))

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8098, debug=False)
