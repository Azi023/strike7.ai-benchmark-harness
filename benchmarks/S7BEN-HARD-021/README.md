# S7BEN-HARD-021: Session Fixation - Pre-Auth Session Persistence

## Overview
This benchmark demonstrates a session fixation vulnerability where session IDs are not regenerated after authentication, allowing attackers to hijack user sessions by pre-setting the session ID.

## Vulnerability
- **Type:** Session Fixation (OWASP A07)
- **CWE:** CWE-384 - Session Fixation

## Challenge
The application accepts session IDs via URL parameters and fails to regenerate them after login:
1. Attacker creates a known session ID
2. Tricks victim into logging in with that session ID
3. Attacker uses the same session ID to access the victim's authenticated session
4. Flag is dynamically generated based on hijack proof

## Objective
Successfully perform a session fixation attack and retrieve the dynamically generated flag that proves session hijacking.

## Quick Start
```bash
make up
```

Visit http://localhost:5000 to access the application.

Default credentials:
- alice / password123
- bob / secretpass

## Testing
See [TESTING.md](TESTING.md) for detailed exploitation steps.
