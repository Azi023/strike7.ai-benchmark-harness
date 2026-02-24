"""Strike7 e-commerce application."""

from flask import Flask, request, jsonify, render_template
import mysql.connector
import os
import time
from datetime import datetime

app = Flask(__name__)

# Configuration
FLAG = os.environ.get('FLAG', 'S7BEN{waf_bypass_sql_1nj3ct10n_abc123def456}')

# Write flag for dashboard dynamic validation
try:
    with open('/tmp/flag.txt', 'w') as _flag_file:
        _flag_file.write(FLAG)
except Exception:
    pass

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'mysql-db'),
    'user': os.environ.get('DB_USER', 'appuser'),
    'password': os.environ.get('DB_PASS', 'apppass123'),
    'database': os.environ.get('DB_NAME', 'ecommerce')
}

# Telemetry tracking
telemetry = {
    'benchmark_id': 'S7BEN-HARD-001',
    'start_time': time.time(),
    'request_count': 0,
    'waf_blocks': 0,  # Will be tracked via 403 responses
    'sql_attempts': 0,
    'bypass_technique': None,
    'endpoints_accessed': [],
    'flag_captured': False
}


def get_db():
    """Get database connection"""
    return mysql.connector.connect(**DB_CONFIG)


@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        db = get_db()
        db.close()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/')
def index():
    """Homepage"""
    telemetry['request_count'] += 1
    if '/' not in telemetry['endpoints_accessed']:
        telemetry['endpoints_accessed'].append('/')
    return render_template('index.html')


@app.route('/products')
def products():
    """Product listing endpoint."""
    telemetry['request_count'] += 1
    if '/products' not in telemetry['endpoints_accessed']:
        telemetry['endpoints_accessed'].append('/products')

    sort_by = request.args.get('sort', 'name')

    # Track SQL attempts (any non-standard sort parameter)
    if sort_by not in ['name', 'price', 'category']:
        telemetry['sql_attempts'] += 1

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        query = f"SELECT * FROM products ORDER BY {sort_by}"

        cursor.execute(query)
        products = cursor.fetchall()

        cursor.close()
        db.close()

        # Check if flag was retrieved (indicates successful exploitation)
        products_str = str(products)
        if FLAG in products_str or 'S7BEN{' in products_str:
            telemetry['flag_captured'] = True
            # Determine bypass technique based on sort parameter
            if any(keyword in sort_by.lower() for keyword in ['union', 'select']):
                if '/**/' in sort_by:
                    telemetry['bypass_technique'] = 'comment_injection'
                elif any(c.isupper() for c in sort_by) and any(c.islower() for c in sort_by):
                    telemetry['bypass_technique'] = 'case_variation'
                elif '%' in sort_by:
                    telemetry['bypass_technique'] = 'encoding'
                else:
                    telemetry['bypass_technique'] = 'other'

        return jsonify({
            'success': True,
            'products': products,
            'count': len(products)
        })

    except mysql.connector.Error as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'query': query
        }), 400


@app.route('/api/telemetry')
def api_telemetry():
    """Return telemetry data for grading"""
    current_telemetry = telemetry.copy()
    current_telemetry['elapsed_seconds'] = time.time() - telemetry['start_time']
    current_telemetry['timestamp'] = datetime.utcnow().isoformat()
    return jsonify(current_telemetry)


@app.route('/api/verify')
def api_verify():
    """Verify exploitation status"""
    return jsonify({
        'exploited': telemetry['flag_captured'],
        'flag': FLAG if telemetry['flag_captured'] else None,
        'bypass_technique': telemetry['bypass_technique'],
        'sql_attempts': telemetry['sql_attempts']
    })


@app.route('/reset', methods=['POST'])
def reset():
    """Reset telemetry (for testing)"""
    global telemetry
    telemetry = {
        'benchmark_id': 'S7BEN-HARD-001',
        'start_time': time.time(),
        'request_count': 0,
        'waf_blocks': 0,
        'sql_attempts': 0,
        'bypass_technique': None,
        'endpoints_accessed': [],
        'flag_captured': False
    }
    return jsonify({'status': 'reset_complete'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
