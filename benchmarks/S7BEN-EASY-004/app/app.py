import os
import secrets
import sqlite3
import uuid
from flask import Flask, render_template_string, request, jsonify
from datetime import datetime

app = Flask(__name__)
FLAG = f"S7BEN{{w0rkfl0w_byp4ss_{secrets.token_hex(8)}}}"

# Write flag for dashboard dynamic validation
try:
    with open('/tmp/flag.txt', 'w') as _flag_file:
        _flag_file.write(FLAG)
except Exception:
    pass

DB_FILE = '/tmp/orders.db'

# Valid order states
STATES = {
    'CREATED': 'Order created',
    'PAYMENT_PENDING': 'Awaiting payment',
    'PAID': 'Payment received',
    'SHIPPED': 'Order shipped',
    'DELIVERED': 'Order delivered'
}

# Proper workflow (but not enforced!)
WORKFLOW = {
    'CREATED': ['PAYMENT_PENDING'],
    'PAYMENT_PENDING': ['PAID'],
    'PAID': ['SHIPPED'],
    'SHIPPED': ['DELIVERED']
}

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the orders database"""
    try:
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)

        conn = get_db()
        conn.execute('''
            CREATE TABLE orders (
                id TEXT PRIMARY KEY,
                item TEXT NOT NULL,
                price REAL NOT NULL,
                status TEXT NOT NULL,
                paid BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")

# Initialize database on startup
init_db()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Strike7 E-Commerce</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 30px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 { color: #333; }
        .order-form {
            background: #f9f9f9;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        input, select {
            width: 100%;
            padding: 10px;
            margin: 5px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            background: #4CAF50;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin: 5px;
        }
        button:hover { background: #45a049; }
        .info {
            background: #e3f2fd;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
            border-left: 4px solid #2196F3;
        }
        .workflow {
            background: #fff3cd;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
            border-left: 4px solid #ffc107;
        }
        #result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 4px;
        }
        .success { background: #d4edda; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; border: 1px solid #f5c6cb; }
        pre {
            background: #f4f4f4;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Strike7 E-Commerce Portal</h1>

        <div class="workflow">
            <strong>Expected Workflow:</strong><br>
            CREATED → PAYMENT_PENDING → PAID → SHIPPED → DELIVERED
        </div>

        <div class="info">
            <strong>API Endpoints:</strong><br>
            • POST /order - Create new order<br>
            • GET /order/{id} - Get order details<br>
            • PUT /order/{id}/status - Update order status<br>
            • POST /order/{id}/payment - Process payment
        </div>

        <div class="order-form">
            <h3>Create New Order</h3>
            <input type="text" id="item" placeholder="Item name" value="Premium Widget">
            <input type="number" id="price" placeholder="Price" value="99.99">
            <button onclick="createOrder()">Create Order</button>
        </div>

        <div id="result"></div>
    </div>

    <script>
        let currentOrderId = null;

        function createOrder() {
            const item = document.getElementById('item').value;
            const price = document.getElementById('price').value;

            fetch('/order', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({item, price: parseFloat(price)})
            })
            .then(r => r.json())
            .then(data => {
                currentOrderId = data.order_id;
                displayResult(data, 'success');
            })
            .catch(err => displayResult({error: err.message}, 'error'));
        }

        function getOrder() {
            if (!currentOrderId) {
                alert('Create an order first!');
                return;
            }
            fetch(`/order/${currentOrderId}`)
                .then(r => r.json())
                .then(data => displayResult(data, 'success'))
                .catch(err => displayResult({error: err.message}, 'error'));
        }

        function updateStatus() {
            if (!currentOrderId) {
                alert('Create an order first!');
                return;
            }
            const status = prompt('Enter new status (CREATED, PAYMENT_PENDING, PAID, SHIPPED, DELIVERED):');
            if (!status) return;

            fetch(`/order/${currentOrderId}/status`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({status: status.toUpperCase()})
            })
            .then(r => r.json())
            .then(data => displayResult(data, 'success'))
            .catch(err => displayResult({error: err.message}, 'error'));
        }

        function displayResult(data, type) {
            const div = document.getElementById('result');
            div.className = type;
            div.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';

            if (data.order_id) {
                div.innerHTML += `
                    <button onclick="getOrder()">Get Order Status</button>
                    <button onclick="updateStatus()">Update Status</button>
                `;
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/order', methods=['POST'])
def create_order():
    """Create a new order"""
    data = request.get_json()

    if not data or 'item' not in data or 'price' not in data:
        return jsonify({"error": "Missing item or price"}), 400

    order_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    conn = get_db()
    conn.execute(
        'INSERT INTO orders (id, item, price, status, paid, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (order_id, data['item'], float(data['price']), 'CREATED', False, now, now)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Order created successfully",
        "order_id": order_id,
        "item": data['item'],
        "price": data['price'],
        "status": "CREATED"
    })

@app.route('/order/<order_id>')
def get_order(order_id):
    """Get order details"""
    conn = get_db()
    cur = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
    order = cur.fetchone()
    conn.close()

    if not order:
        return jsonify({"error": "Order not found"}), 404

    return jsonify({
        "order_id": order['id'],
        "item": order['item'],
        "price": order['price'],
        "status": order['status'],
        "paid": bool(order['paid']),
        "created_at": order['created_at'],
        "updated_at": order['updated_at']
    })

@app.route('/order/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Update the status of an order."""
    data = request.get_json()

    if not data or 'status' not in data:
        return jsonify({"error": "Missing status"}), 400

    new_status = data['status'].upper()

    if new_status not in STATES:
        return jsonify({
            "error": "Invalid status",
            "valid_states": list(STATES.keys())
        }), 400

    conn = get_db()

    # Get current order
    cur = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
    order = cur.fetchone()

    if not order:
        conn.close()
        return jsonify({"error": "Order not found"}), 404

    # Update the status directly
    now = datetime.now().isoformat()
    conn.execute(
        'UPDATE orders SET status = ?, updated_at = ? WHERE id = ?',
        (new_status, now, order_id)
    )
    conn.commit()

    # Check if they bypassed payment
    cur = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
    updated_order = cur.fetchone()
    conn.close()

    response = {
        "message": f"Order status updated to {new_status}",
        "order_id": order_id,
        "previous_status": order['status'],
        "new_status": new_status,
        "paid": bool(updated_order['paid'])
    }

    # FLAG: If order reached SHIPPED without being PAID
    if new_status == 'SHIPPED' and not updated_order['paid']:
        flag = FLAG
        response['flag'] = flag
        response['exploit_success'] = True
        response['message'] = f"Order status updated to {new_status}"

    return jsonify(response)

@app.route('/order/<order_id>/payment', methods=['POST'])
def process_payment(order_id):
    """Process payment for an order (proper way)"""
    conn = get_db()

    cur = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
    order = cur.fetchone()

    if not order:
        conn.close()
        return jsonify({"error": "Order not found"}), 404

    if order['status'] != 'PAYMENT_PENDING':
        conn.close()
        return jsonify({
            "error": "Order must be in PAYMENT_PENDING state",
            "current_status": order['status']
        }), 400

    # Process payment
    now = datetime.now().isoformat()
    conn.execute(
        'UPDATE orders SET paid = 1, status = ?, updated_at = ? WHERE id = ?',
        ('PAID', now, order_id)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Payment processed successfully",
        "order_id": order_id,
        "status": "PAID"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
