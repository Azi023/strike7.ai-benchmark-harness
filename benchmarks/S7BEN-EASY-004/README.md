# S7BEN-EASY-004: Workflow Bypass - Order Status Manipulation

## Overview
This benchmark demonstrates an insecure workflow design where order status can be directly manipulated, allowing attackers to skip critical steps like payment verification.

## Vulnerability
- **Type:** Workflow Bypass (OWASP A04)
- **CWE:** CWE-840 - Business Logic Errors

## Challenge
The e-commerce system has a defined order workflow but fails to enforce proper state transitions. Attackers can:
1. Create an order in CREATED state
2. Skip PAYMENT_PENDING and PAID states
3. Directly set status to SHIPPED
4. Receive goods without payment

## Objective
Manipulate the order status to reach SHIPPED without going through the PAID state, then retrieve the flag.

## Quick Start
```bash
make up
```

Visit http://localhost:5000 to access the application.

## Testing
See [TESTING.md](TESTING.md) for detailed exploitation steps.
