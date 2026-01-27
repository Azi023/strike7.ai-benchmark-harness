# S7BEN-VHARD-005: Python Pickle Deserialization Chain

## Overview

This benchmark demonstrates exploitation of insecure Python pickle deserialization vulnerabilities across a multi-container architecture. It showcases realistic attack scenarios involving session cookies, Redis cache poisoning, and Celery task queue exploitation.

## Difficulty

**Tier:** 2 (Intermediate)

**Prerequisites:**
- Understanding of Python pickle serialization/deserialization
- Knowledge of `__reduce__` gadget chains
- Experience with Flask web applications
- Familiarity with Redis and Celery
- Basic understanding of web exploitation

## Architecture

```
┌─────────────────────────────────────┐
│  web-app (Flask)                    │
│  - Pickle session cookies           │
│  - Redis cache integration          │
│  - Celery task submission           │
│  Port: 5000 (exposed)               │
└──────────────┬──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│  redis-cache (Redis 7)              │
│  - Stores pickled objects           │
│  - Cache persistence                │
│  Port: 6379 (internal)              │
└──────────────┬──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│  worker-service (Celery)            │
│  - Processes pickled tasks          │
│  - Background job processing        │
│  Port: 5555 (internal)              │
└─────────────────────────────────────┘
```

## Vulnerabilities

1. **Insecure Pickle Session Deserialization (CUSTOM-PICKLE-01)**
   - Flask application deserializes user-controlled session cookies
   - No validation of pickle data before deserialization
   - Enables RCE via malicious `__reduce__` gadgets

2. **Redis Cache Pickle Poisoning (CUSTOM-PICKLE-02)**
   - Application caches user-provided data as pickled objects
   - Cache retrieval deserializes without validation
   - Allows persistent RCE payloads

3. **Celery Task Deserialization RCE (CUSTOM-PICKLE-03)**
   - Celery configured to use pickle as task serializer (insecure default)
   - Workers deserialize task payloads from untrusted sources
   - Enables code execution on worker containers

## Attack Chain

1. **Reconnaissance** - Identify pickle serialization in session cookies
2. **Pickle Gadget Discovery** - Craft malicious `__reduce__` payload
3. **Session Cookie Exploitation** - Inject payload into session cookie for RCE
4. **Redis Cache Poisoning** - Poison cache with persistent pickle payload
5. **Celery Task Queue Exploitation** - Submit malicious task to worker

## Flags

- **FLAG 1:** `S7BEN{pickle_session_cookie_rce_f1a2b3c4d5e6}` - Located at `/app/flag.txt` (web-app)
- **FLAG 2:** `S7BEN{redis_cache_poisoning_pickle_g7h8i9j0k1l2}` - Located at `/data/cache_flag.txt` (redis-cache)
- **FLAG 3:** `S7BEN{celery_worker_task_deserialization_m3n4o5p6q7r8}` - Located at `/worker/secret_flag.txt` (worker-service)

## Quick Start

```bash
# Build and start services
docker compose up -d

# Check service health
docker compose ps
make test

# Access web application
curl http://localhost:5000

# Get example session structure
curl http://localhost:5000/api/session/example

# View available endpoints
open http://localhost:5000  # or use curl
```

## Tools Required

- **Python 3.x** - For crafting pickle payloads
- **curl** - For HTTP requests
- **base64** - For encoding/decoding payloads
- **redis-cli** - For Redis inspection (optional)
- **docker** - For container access

## Testing

See [TESTING.md](TESTING.md) for detailed exploitation guide with step-by-step instructions for:
- Crafting malicious pickle payloads
- Session cookie exploitation
- Redis cache poisoning
- Celery task queue attacks

## Cleanup

```bash
# Stop all services
docker compose down

# Remove volumes
docker compose down -v
```

## Learning Resources

- [Python Pickle Security](https://docs.python.org/3/library/pickle.html#module-pickle)
- [Exploiting Python Pickles](https://davidhamann.de/2020/04/05/exploiting-python-pickle/)
- [Celery Security Guide](https://docs.celeryproject.org/en/stable/userguide/security.html)
- [Redis Security](https://redis.io/docs/management/security/)

## Security Notice

This benchmark contains intentional security vulnerabilities:
- Insecure Python pickle deserialization
- No input validation on serialized data
- Unsafe Celery task serializer configuration
- Cache poisoning vulnerabilities

**DO NOT** expose this environment to untrusted networks.

## License

MIT License - For educational purposes only.
