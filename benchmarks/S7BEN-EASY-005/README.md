# S7BEN-EASY-005: Insufficient Logging - Brute Force Undetected

## Overview
This benchmark demonstrates a critical security logging failure where authentication attempts are not properly logged, allowing attackers to perform brute force attacks without detection.

## Vulnerability
- **Type:** Insufficient Logging (OWASP A09)
- **CWE:** CWE-778 - Insufficient Logging

## Challenge
The application fails to log failed login attempts. This allows attackers to:
1. Brute force credentials without triggering alerts
2. Avoid detection by security monitoring systems
3. Bypass rate limiting that relies on log analysis

## Objective
Brute force the admin password and retrieve the flag from the admin panel.

## Quick Start
```bash
make up
```

Visit http://localhost:5000 to access the application.

## Testing
See [TESTING.md](TESTING.md) for detailed exploitation steps.
