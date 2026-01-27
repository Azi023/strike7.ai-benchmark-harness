# S7BEN-VHARD-013: Race Condition Double Spend

**Difficulty:** 9/10 | TOCTOU in checkout process

## Exploit
Register user with $100 balance, send concurrent checkout requests for $90 item.
Race condition allows multiple purchases with insufficient funds.

```bash
make up && ./exploit.sh
```

**Flag:** `S7BEN{r4ce_c0nd1t10n_d0uble_spend_[dynamic]}`
