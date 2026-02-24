#!/usr/bin/env python3
from flask import Flask, request
import secrets
app=Flask(__name__)
FLAG=f"S7BEN{{activemq_deser_{secrets.token_hex(6)}}}"

# Write flag for dashboard dynamic validation
try:
    with open('/tmp/flag.txt', 'w') as _flag_file:
        _flag_file.write(FLAG)
except Exception:
    pass

@app.route("/")
def index():
  return"<h1>S7BEN-CVE-011</h1>"
@app.route("/broker",methods=["POST"])
def broker():
  payload=request.data
  if b"exploit" in payload:
    return{"status":"deserialized","flag":FLAG}
  return{"status":"ok"}
@app.route("/health")
def health():
  return"ok"
if __name__=="__main__":
  app.run(host="0.0.0.0",port=8110)