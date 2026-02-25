#\!/usr/bin/env python3
from flask import Flask, jsonify
import secrets, string, os
app=Flask(__name__)
FLAG=f"S7BEN{{d0cker_s0cket_{secrets.token_hex(6)}}}"

# Write flag for dashboard dynamic validation
try:
    with open('/tmp/flag.txt', 'w') as _flag_file:
        _flag_file.write(FLAG)
except Exception:
    pass

@app.route("/")
def index():
  return"<h1>S7BEN-HARD-019</h1>"
@app.route("/api/flag")
def flag():
  return jsonify({"flag":FLAG})
@app.route("/health")
def health():
  return jsonify({"status":"healthy"})
if __name__=="__main__":
  app.run(host="0.0.0.0",port=8102)