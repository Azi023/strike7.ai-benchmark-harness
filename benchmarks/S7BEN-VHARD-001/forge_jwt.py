#!/usr/bin/env python3
import base64, json, hmac, hashlib, time

def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")

# Read public key PEM and normalize trailing newlines to match container
with open("public_key.pem", "r") as f:
    public_key = f.read().rstrip() + '\n'  # Ensure exactly one trailing newline

header = {"alg": "HS256", "typ": "JWT"}
payload = {
    "username": "admin",
    "role": "admin",
    "email": "admin@example.com",
    "iat": int(time.time()),
}

header_b64 = b64url(json.dumps(header, separators=(",", ":")).encode())
payload_b64 = b64url(json.dumps(payload, separators=(",", ":")).encode())

signing_input = f"{header_b64}.{payload_b64}".encode()

sig = hmac.new(public_key.encode(), signing_input, hashlib.sha256).digest()
sig_b64 = b64url(sig)

token = f"{header_b64}.{payload_b64}.{sig_b64}"
print(token)

with open("admin_token.txt", "w") as f:
    f.write(token)

print("\nSaved to admin_token.txt")
