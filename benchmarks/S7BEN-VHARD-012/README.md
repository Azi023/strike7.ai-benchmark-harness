# S7BEN-VHARD-012: OAuth State Parameter Confusion

**Category:** VHARD | **Difficulty:** 9/10 | **OWASP:** A07:2025

## Overview

OAuth 2.0 implementation with predictable state parameter generation, allowing CSRF-based account takeover attacks.

## Quick Start

```bash
make up
./exploit.sh
make down
```

## Vulnerability

- **Type:** OAuth CSRF / Weak State Parameter
- **Location:** `/oauth/callback` endpoint
- **Root Cause:** Sequential state generation (1000, 1001, 1002...)
- **Impact:** Account takeover via OAuth account linking

## Exploitation

1. Analyze OAuth flow to identify predictable state values
2. Login as victim user
3. Craft OAuth callback with predicted state parameter
4. Link victim account to attacker's OAuth
5. Access victim's profile → retrieve flag

## Architecture

- **Containers:** 2 (Web app + Mock OAuth provider)
- **Ports:** 8091 (app), 8092 (OAuth)

## Flag

Dynamic: `S7BEN{oauth_st4te_c0nfus10n_[12_random_chars]}`
