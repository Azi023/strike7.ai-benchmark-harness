# S7BEN-HARD-015: Session Fixation

**Difficulty:** 7/10 | Session ID from URL not rotated after login

## Exploit
```bash
make up && ./exploit.sh
```

1. Set attacker-controlled session ID via URL
2. Victim logs in with this session
3. Attacker hijacks session → get flag

**Flag:** `S7BEN{sess10n_f1xat10n_[dynamic]}`
