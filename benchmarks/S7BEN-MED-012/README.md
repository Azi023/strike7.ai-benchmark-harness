# S7BEN-MED-012: Dependency Confusion - Evaluation

## Overview

A realistic CI/CD build portal for ACME Corporation.

**Tier:** Evaluation (T2)  
**Difficulty:** Medium  
**OWASP 2025:** A03 - Software Supply Chain Failures

---

## Quick Start

```bash
cd benchmarks/S7BEN-MED-012
make build
make up
```

Access the portal: http://localhost:5000

---

## Architecture

This benchmark runs two services:
- **App** (port 5000): DevOps build portal
- **Registry** (port 5001): Package registry

---

## Cleanup

```bash
make down
make clean
```
