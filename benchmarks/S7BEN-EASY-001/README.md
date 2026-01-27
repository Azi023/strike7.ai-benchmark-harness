# S7BEN-EASY-001: CSRF - Password Change

## Overview
This benchmark demonstrates a Cross-Site Request Forgery (CSRF) vulnerability where an authenticated user can be tricked into changing their password without their knowledge by visiting a malicious webpage.

## Vulnerability
- **Type:** Cross-Site Request Forgery (OWASP A01)
- **CWE:** CWE-352 - Cross-Site Request Forgery

## Challenge
The password change form lacks CSRF token validation. Attackers can:
1. Craft a malicious HTML page with an auto-submitting form
2. Trick an authenticated admin into visiting the page
3. The form automatically submits to change the admin's password
4. Attacker gains access to the admin account

## Objective
Create a CSRF attack page that changes the admin password to 'hacked', then login and retrieve the flag from the admin dashboard.

## Quick Start
```bash
make up
```

Visit http://localhost:5000 to access the application.

Default credentials: admin / admin123

## Testing
See [TESTING.md](TESTING.md) for detailed exploitation steps.
