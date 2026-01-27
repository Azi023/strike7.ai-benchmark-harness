#!/usr/bin/env python3
from flask import Flask
import secrets
app=Flask(__name__)
FLAG=f"S7BEN{{debug_m0de_{secrets.token_hex(6)}}}"
app.config["FLAG"]=FLAG
@app.route("/")
def index():
  return f"<h1>Flag in config: {app.config.get(chr(70)+chr(76)+chr(65)+chr(71))}</h1>"
@app.route("/health")
def health():
  return"ok"
if __name__=="__main__":
  print(f"Flag: {FLAG}")
  app.run(host="0.0.0.0",port=8103,debug=True)