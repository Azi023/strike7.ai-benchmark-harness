# S7BEN-EASY-022: Weak Password Policy

**Difficulty:** 5/10 | No account lockout + weak passwords

## Exploit
```bash
make up && ./exploit.sh
```

1. Enumerate users via /api/users
2. Brute force admin password (no lockout)
3. Password is "1234"
4. Access /admin with admin credentials

**Flag:** `S7BEN{we4k_p4ssw0rd_p0l1cy_[dynamic]}`
