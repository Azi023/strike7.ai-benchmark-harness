# S7BEN-HARD-014: Password Reset Token Reuse

**Difficulty:** 7/10 | **OWASP:** A07:2025

## Vulnerability
Password reset tokens not invalidated after use - allows multiple password changes with same token.

## Quick Start
```bash
make up && ./exploit.sh && make down
```

## Exploitation
1. Request reset token for admin@example.com
2. Use token to change password
3. Reuse SAME token to change password again
4. Login with attacker-controlled password
5. Access /profile → retrieve flag

**Flag:** `S7BEN{p4ssw0rd_res3t_t0ken_reuse_[dynamic]}`
