#!/usr/bin/env python3
from flask import Flask, request
import secrets, subprocess
app=Flask(__name__)
FLAG=f"S7BEN{{pan0s_cmd_inj_{secrets.token_hex(6)}}}"

# Write flag for dashboard dynamic validation
try:
    with open('/tmp/flag.txt', 'w') as _flag_file:
        _flag_file.write(FLAG)
except Exception:
    pass

@app.route("/")
def index():
  return"<h1>S7BEN-CVE-008</h1>"
@app.route("/api/telemetry")
def telemetry():
  cmd=request.args.get("cmd","")
  if cmd:
    return{"output":f"Executed: {cmd}","flag":FLAG}
  return{"error":"no cmd"}
@app.route("/health")
def health():
  return"ok"
if __name__=="__main__":
  app.run(host="0.0.0.0",port=8107)