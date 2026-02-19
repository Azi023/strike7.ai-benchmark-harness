"""Strike7 e-commerce service."""

import os
import json
import hmac
import hashlib
import time
import base64
from datetime import datetime
from flask import Flask, render_template, request, jsonify, make_response

app = Flask(__name__)
FLAG_SECRET = os.environ.get('FLAG_SECRET', 'strike7-error-t2-secret-key')
SESSION_SECRET = os.environ.get('SESSION_SECRET', 'UltraS3cur3K3y_F0rS3ss10ns!')
DATA_FILE = '/app/data/state.json'

# Product catalog
PRODUCTS = {
    1: {"id": 1, "name": "Wireless Headphones", "price": 79.99, "stock": 15},
    2: {"id": 2, "name": "USB-C Hub", "price": 49.99, "stock": 8},
    3: {"id": 3, "name": "Mechanical Keyboard", "price": 129.99, "stock": 3},
    4: {"id": 4, "name": "4K Monitor", "price": 399.99, "stock": 0},
    5: {"id": 5, "name": "Laptop Stand", "price": 34.99, "stock": 25}
}

# Users
USERS = {
    "customer1": {"role": "user", "email": "customer@shop.com"},
    "admin": {"role": "admin", "email": "admin@shop.com"}
}

def get_default_state():
    return {
        "cart": {},
        "orders": [],
        "key_extracted": False,
        "session_forged": False,
        "flag_retrieved": False,
        "patched": False,
        "telemetry": {
            "request_count": 0,
            "start_time": time.time(),
            "endpoints_accessed": [],
            "errors_triggered": 0
        }
    }

def load_state():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return get_default_state()

def save_state(state):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def track_request(endpoint):
    state = load_state()
    state['telemetry']['request_count'] += 1
    if endpoint not in state['telemetry']['endpoints_accessed']:
        state['telemetry']['endpoints_accessed'].append(endpoint)
    save_state(state)
    return state

def generate_flag(key_used, timestamp):
    data = f"error_t2:{key_used[:10]}:{timestamp}"
    flag_hash = hmac.new(
        FLAG_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:32]
    return f"S7BEN{{error_chain_exploit_{flag_hash}}}"

def create_session_cookie(user, role):
    """Create a signed session cookie"""
    data = {"user": user, "role": role, "exp": int(time.time()) + 3600}
    payload = base64.b64encode(json.dumps(data).encode()).decode()
    signature = hmac.new(
        SESSION_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()[:16]
    return f"{payload}.{signature}"

def verify_session_cookie(cookie):
    """Verify and decode session cookie"""
    try:
        if not cookie or '.' not in cookie:
            return None
        payload, signature = cookie.rsplit('.', 1)
        expected_sig = hmac.new(
            SESSION_SECRET.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()[:16]
        if signature != expected_sig:
            return None
        data = json.loads(base64.b64decode(payload))
        if data.get('exp', 0) < time.time():
            return None
        return data
    except Exception as e:
        raise ValueError(f"Session decode failed: {e}. Key hint: {SESSION_SECRET[:8]}...")

def get_current_user():
    """Get current user from session cookie"""
    cookie = request.cookies.get('session')
    if not cookie:
        return None
    try:
        return verify_session_cookie(cookie)
    except:
        return None

# =============================================================================
# ROUTES - REALISTIC E-COMMERCE UI (No hints!)
# =============================================================================

@app.route('/')
def index():
    state = track_request('/')
    return render_template('index.html', products=PRODUCTS)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/api/products')
def api_products():
    state = track_request('/api/products')
    return jsonify({"products": list(PRODUCTS.values())})

@app.route('/api/products/<product_id>')
def api_product_detail(product_id):
    state = track_request(f'/api/products/{product_id}')
    
    try:
        pid = int(product_id)
        product = PRODUCTS.get(pid)
        if not product:
            return jsonify({"error": "Product not found"}), 404
        return jsonify({"product": product})
    except ValueError as e:
        state['telemetry']['errors_triggered'] += 1
        save_state(state)
        
        if state.get('patched'):
            return jsonify({"error": "Invalid product ID"}), 400
        
        return jsonify({
            "error": f"Invalid product ID format: {product_id}",
            "expected": "integer",
            "debug": {
                "app_config": {
                    "session_algo": "HMAC-SHA256",
                    "sig_length": 16
                }
            }
        }), 400

@app.route('/api/cart', methods=['GET', 'POST'])
def api_cart():
    state = track_request('/api/cart')
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            product_id = int(data.get('product_id', 0))
            quantity = int(data.get('quantity', 1))
            
            if product_id not in PRODUCTS:
                return jsonify({"error": "Product not found"}), 404
            
            if quantity > PRODUCTS[product_id]['stock']:
                if not state.get('patched'):
                    state['telemetry']['errors_triggered'] += 1
                    save_state(state)
                    return jsonify({
                        "error": f"Insufficient stock for product {product_id}",
                        "available": PRODUCTS[product_id]['stock'],
                        "requested": quantity,
                        "session_debug": {
                            "cookie_format": "base64(payload).signature",
                            "signature_key_prefix": SESSION_SECRET[:4] + "..."
                        }
                    }), 400
                return jsonify({"error": "Insufficient stock"}), 400
            
            state['cart'][str(product_id)] = quantity
            save_state(state)
            return jsonify({"status": "success", "cart": state['cart']})
        
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    
    return jsonify({"cart": state['cart']})

@app.route('/api/checkout', methods=['POST'])
def api_checkout():
    """
    Checkout with session validation
    """
    state = track_request('/api/checkout')
    
    try:
        session = get_current_user()
        
        if not session:
            return jsonify({"error": "Please login to checkout"}), 401
        
        if not state['cart']:
            return jsonify({"error": "Cart is empty"}), 400
        
        # Process order
        order = {
            "id": f"ORD-{int(time.time())}",
            "user": session.get('user'),
            "items": state['cart'],
            "timestamp": datetime.now().isoformat()
        }
        state['orders'].append(order)
        state['cart'] = {}
        save_state(state)
        
        return jsonify({"status": "success", "order": order})
    
    except ValueError as e:
        state['telemetry']['errors_triggered'] += 1
        save_state(state)
        
        if state.get('patched'):
            return jsonify({"error": "Session error"}), 400
        
        return jsonify({
            "error": "Session validation failed",
            "details": str(e)
        }), 400

@app.route('/api/session/validate', methods=['POST'])
def validate_session():
    """Session validation endpoint."""
    state = track_request('/api/session/validate')
    
    cookie = request.json.get('cookie', '') if request.json else ''
    
    try:
        if not cookie:
            return jsonify({"valid": False, "error": "No cookie provided"})
        
        session = verify_session_cookie(cookie)
        if session:
            return jsonify({"valid": True, "session": session})
        return jsonify({"valid": False})
    
    except ValueError as e:
        state['telemetry']['errors_triggered'] += 1
        save_state(state)
        
        if state.get('patched'):
            return jsonify({"valid": False, "error": "Invalid session"})
        
        return jsonify({
            "valid": False,
            "error": str(e),
            "debug_info": {
                "key_length": len(SESSION_SECRET),
                "key_preview": SESSION_SECRET[:12] + "...",
                "algo": "HMAC-SHA256-truncated"
            }
        })

@app.route('/api/session/debug')
def session_debug():
    """Debug endpoint."""
    state = track_request('/api/session/debug')
    
    test_input = request.args.get('test', '')
    
    try:
        # Try to decode as base64
        if test_input:
            decoded = base64.b64decode(test_input)
            return jsonify({"status": "decoded", "length": len(decoded)})
        return jsonify({"status": "no input"})
    
    except Exception as e:
        state['telemetry']['errors_triggered'] += 1
        save_state(state)
        
        if state.get('patched'):
            return jsonify({"error": "Invalid input"})
        
        return jsonify({
            "error": "Base64 decode failed",
            "input": test_input[:20],
            "crypto_config": {
                "session_secret": SESSION_SECRET,
                "algorithm": "HMAC-SHA256",
                "truncate_to": 16
            }
        })

# =============================================================================
# ADMIN ENDPOINT (Requires forged session)
# =============================================================================

@app.route('/internal/admin/flag')
def admin_flag():
    """Admin-only flag endpoint."""
    state = track_request('/internal/admin/flag')
    
    session = get_current_user()
    
    if not session:
        return jsonify({"error": "Authentication required"}), 401
    
    if session.get('role') != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    
    # Success! Generate flag
    state['key_extracted'] = True
    state['session_forged'] = True
    state['flag_retrieved'] = True
    save_state(state)
    
    flag = generate_flag(SESSION_SECRET, datetime.now().isoformat())
    
    return jsonify({
        "status": "success",
        "message": "Welcome, admin!",
        "flag": flag,
        "proof": "Admin access confirmed"
    })

# =============================================================================
# PHASE 3 QUALITY ENDPOINTS
# =============================================================================

@app.route('/api/oracle')
def oracle():
    state = track_request('/api/oracle')
    return jsonify({
        "expected_vulnerability": "error_based_information_disclosure",
        "current_state": "exploited" if state.get('flag_retrieved') else 
                        ("patched" if state.get('patched') else "vulnerable"),
        "chain_required": True
    })

@app.route('/api/verify')
def verify():
    state = track_request('/api/verify')
    
    if state.get('flag_retrieved'):
        flag = generate_flag(SESSION_SECRET, datetime.now().isoformat())
        return jsonify({
            "exploitation_successful": True,
            "proof": {
                "key_extracted": state['key_extracted'],
                "session_forged": state['session_forged'],
                "errors_triggered": state['telemetry']['errors_triggered']
            },
            "flag": flag
        })
    
    return jsonify({
        "exploitation_successful": False,
        "errors_triggered": state['telemetry'].get('errors_triggered', 0)
    })

@app.route('/api/patch-status', methods=['GET', 'POST'])
def patch_status():
    state = load_state()
    if request.method == 'POST':
        data = request.get_json() or {}
        state['patched'] = data.get('patched', not state['patched'])
        save_state(state)
    return jsonify({
        "patched": state['patched'],
        "mode": "patched" if state['patched'] else "vulnerable"
    })

@app.route('/api/telemetry')
def telemetry():
    state = load_state()
    elapsed = time.time() - state['telemetry'].get('start_time', time.time())
    return jsonify({
        "request_count": state['telemetry']['request_count'],
        "time_elapsed_seconds": round(elapsed, 2),
        "endpoints_discovered": len(state['telemetry']['endpoints_accessed']),
        "errors_triggered": state['telemetry']['errors_triggered'],
        "stealth_score": 100,
        "tier": 2
    })

@app.route('/reset', methods=['POST'])
def reset():
    state = get_default_state()
    save_state(state)
    return jsonify({"status": "success", "message": "Reset complete"})

if __name__ == '__main__':
    if not os.path.exists(DATA_FILE):
        save_state(get_default_state())
    app.run(host='0.0.0.0', port=5000, debug=False)
