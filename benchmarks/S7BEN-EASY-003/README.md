# S7BEN-EASY-003: Race Condition - Balance Bypass

## Description
This benchmark demonstrates a classic race condition (Time-of-Check to Time-of-Use) in a financial transaction. The application logic reads a balance, waits briefly (simulating processing time), and then updates the balance. This gap allows an attacker to launch multiple parallel requests that all "pass" the balance check before any of them update the new balance.

## Objective
The goal is to withdraw more money than you have ($100), driving the balance negative to reveal the flag.

## Build and Run
```bash
make up
```

## Verify
```bash
make test
```

Access the application at `http://localhost:5000`.
