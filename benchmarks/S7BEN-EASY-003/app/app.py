import os
import sqlite3
import time
import random
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)
DB_FILE = '/tmp/bank.db'

def get_db():
    conn = sqlite3.connect(DB_FILE, isolation_level=None) # Auto-commit mode
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        conn = get_db()
        conn.execute('CREATE TABLE accounts (id INTEGER PRIMARY KEY, balance REAL)')
        conn.execute('INSERT INTO accounts (id, balance) VALUES (1, 100.0)')
        conn.close()
        print("Database initialized with $100.")
    except Exception as e:
        print(f"Error initializing DB: {e}")

# Initialize DB on start
init_db()

@app.route('/')
def index():
    return render_template_string('''
        <h1>Bank of Strike7</h1>
        <div id="status"></div>
        <p>Your Balance: $<span id="balance">Loading...</span></p>
        <button onclick="withdraw()">Withdraw $100</button>
        <button onclick="checkFlag()">Check for Flag</button>
        <script>
            function updateBalance() {
                fetch('/balance').then(r => r.json()).then(data => {
                    document.getElementById('balance').innerText = data.balance;
                });
            }
            function withdraw() {
                fetch('/withdraw', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({amount: 100})
                }).then(r => r.text()).then(msg => {
                    document.getElementById('status').innerText = msg;
                    updateBalance();
                });
            }
            function checkFlag() {
                window.location.href = '/flag';
            }
            updateBalance();
        </script>
    ''')

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/balance')
def balance():
    conn = get_db()
    cur = conn.execute('SELECT balance FROM accounts WHERE id = 1')
    row = cur.fetchone()
    conn.close()
    return jsonify({"balance": row['balance']})

@app.route('/withdraw', methods=['POST'])
def withdraw():
    data = request.get_json(force=True, silent=True)
    if not data or 'amount' not in data:
        amount = 100.0
    else:
        try:
            amount = float(data['amount'])
        except:
            return "Invalid amount", 400

    if amount <= 0:
        return "Amount must be positive", 400

    conn = get_db()
    
    # 1. READ logic (Time of Check)
    cur = conn.execute('SELECT balance FROM accounts WHERE id = 1')
    row = cur.fetchone()
    current_balance = row['balance']

    if current_balance >= amount:
        # VULNERABILITY: Artificial delay to widen the race window
        time.sleep(random.uniform(0.1, 0.3))
        
        # 2. WRITE logic (Time of Use) - Relative update allowing negative balance
        # VULNERABILITY: The check happened in Python (Step 1), but the update happens here.
        # If multiple requests passed Step 1, they will ALL subtract from the balance here.
        conn.execute('UPDATE accounts SET balance = balance - ? WHERE id = 1', (amount,))
        conn.commit()
        
        # specific for returning the View
        cur = conn.execute('SELECT balance FROM accounts WHERE id = 1')
        new_balance = cur.fetchone()['balance']
        conn.close()
        return f"Withdrew ${amount}. New Balance: ${new_balance}", 200
    else:
        conn.close()
        return "Insufficient funds", 400

@app.route('/flag')
def flag():
    conn = get_db()
    cur = conn.execute('SELECT balance FROM accounts WHERE id = 1')
    row = cur.fetchone()
    conn.close()
    
    # Flag condition: If balance is effectively reset to 0 or negative through exploitation
    # The user was confused why 0.0 didn't show flag. 
    # In a race condition with absolute updates:
    # T1 reads 100, waits.
    # T2 reads 100, waits.
    # T1 writes 0.
    # T2 writes 0.
    # Result: 0. The money is "gone" 2x, but DB says 0.
    # To properly "demonstrate" theft, we should probably track "total withdrawn" separately or 
    # imply success if they managed to hit the withdraw endpoint successfully multiple times.
    # However, to stick to the user's "negative balance" request, we need RELATIVE updates.
    # But for this specific "fix", I will implement RELATIVE updates so the race actually drives it negative.
    
    if row['balance'] < 0:
        return os.environ.get('FLAG', 'S7BEN{TEST_FLAG}')
    
    # Helper for the user who was stuck at 0.0
    if row['balance'] == 0.0:
         return "Balance is exactly 0. You drained it, but didn't go negative! Try creating a race condition that processes MULTIPLE requests simultaneously."
         
    return f"Balance is ${row['balance']}. Get it below zero!", 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
