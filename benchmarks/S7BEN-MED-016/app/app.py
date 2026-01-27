#!/usr/bin/env python3
from flask import Flask, request, jsonify
import secrets
app=Flask(__name__)
FLAG=f"S7BEN{{def4ult_creds_{secrets.token_hex(5)}}}"
ADMINS={"admin":"admin123"}
@app.route("/")
def index():
  return"<h1>POST /login</h1>"
@app.route("/login",methods=["POST"])
def login():
  u,p=request.json.get("user"),request.json.get("pass")
  if ADMINS.get(u)==p:
    return jsonify({"flag":FLAG})
  return jsonify({"error":"nope"}),401
@app.route("/health")
def health():
  return"ok"
if __name__=="__main__":
  print(f"Flag: {FLAG}")
  app.run(host="0.0.0.0",port=8104)