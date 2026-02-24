#!/usr/bin/env python3
"""
Strike7 MCP/SSE Client — Minimal Example
~90 lines. No dependencies beyond the standard library + requests.

Usage:
    python3 docs/mcp_client_example.py

What it does:
    1. Opens the SSE stream and extracts the session ID
    2. Starts a background thread to receive JSON-RPC responses from the stream
    3. Sends initialize + notifications/initialized
    4. Calls tools/list and prints available tools

Extend it by calling mcp("tools/call", {...}) for any tool in the list.
"""

import socket
import threading
import queue
import json
import re
import time
import requests

# ── Configuration ─────────────────────────────────────────────────
MCP_HOST  = "139.59.80.137"
MCP_SSE   = f"http://{MCP_HOST}/mcp/sse"    # SSE stream endpoint
MCP_BASE  = f"http://{MCP_HOST}"            # base for messages URL


# ── Step 1: Open SSE connection and read first event ──────────────
def connect_sse(host: str) -> tuple[str, socket.socket]:
    """
    Open a raw socket to the SSE endpoint.
    Returns (messages_url, open_socket).
    The socket must stay open for the duration of the session.
    """
    sock = socket.create_connection((host, 80), timeout=12)
    sock.sendall(
        b"GET /mcp/sse HTTP/1.1\r\n"
        b"Host: " + host.encode() + b"\r\n"
        b"Accept: text/event-stream\r\n"
        b"Cache-Control: no-cache\r\n"
        b"Connection: keep-alive\r\n\r\n"
    )
    sock.settimeout(8)
    buf = b""
    while b"data:" not in buf:
        buf += sock.recv(4096)

    m = re.search(rb"data:\s*(/[^\r\n]+)", buf)
    if not m:
        raise RuntimeError("No endpoint event in SSE response")
    messages_path = m.group(1).decode().strip()  # e.g. /mcp/messages/?session_id=xxx
    messages_url  = f"{MCP_BASE}{messages_path}"
    return messages_url, sock


# ── Step 2: Background thread reads JSON-RPC responses from SSE ───
def start_sse_reader(sock: socket.socket, response_queue: queue.Queue) -> None:
    """Continuously parse SSE events and enqueue JSON-RPC response objects."""
    accumulator = b""

    def reader():
        nonlocal accumulator
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                accumulator += chunk
            except socket.timeout:
                pass
            except Exception:
                break

            # Normalise \r\n → \n so we can split on \n\n
            norm   = accumulator.replace(b"\r\n", b"\n")
            events = norm.split(b"\n\n")
            accumulator = events[-1].replace(b"\n", b"\r\n")  # keep partial

            for event in events[:-1]:
                for line in event.split(b"\n"):
                    if not line.startswith(b"data:"):
                        continue
                    payload = line[5:].strip()
                    if not payload:
                        continue
                    try:
                        obj = json.loads(payload)
                        if isinstance(obj, dict) and ("id" in obj or "error" in obj):
                            response_queue.put(obj)
                    except json.JSONDecodeError:
                        pass

    t = threading.Thread(target=reader, daemon=True)
    t.start()


# ── Step 3: JSON-RPC call helper ──────────────────────────────────
_req_id = 0

def mcp(messages_url: str, resp_queue: queue.Queue,
        method: str, params: dict = None, wait: float = 12.0):
    """Send a JSON-RPC request and wait for the response on the SSE stream."""
    global _req_id
    _req_id += 1
    rid = _req_id
    payload = {"jsonrpc": "2.0", "id": rid, "method": method}
    if params:
        payload["params"] = params

    requests.post(messages_url, json=payload, timeout=10)  # always 202

    deadline = time.time() + wait
    while time.time() < deadline:
        try:
            resp = resp_queue.get(timeout=0.3)
            if resp.get("id") == rid:
                return resp
            resp_queue.put(resp)  # not ours — put back
        except queue.Empty:
            pass
    return None


# ── Main ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[+] Connecting to {MCP_SSE}")
    messages_url, sock = connect_sse(MCP_HOST)
    session_id = messages_url.split("session_id=")[-1]
    print(f"[+] Session ID  : {session_id}")
    print(f"[+] Messages URL: {messages_url}")

    resp_q = queue.Queue()
    start_sse_reader(sock, resp_q)
    time.sleep(0.2)  # let thread warm up

    # initialize
    resp = mcp(messages_url, resp_q, "initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "strike7-example-client", "version": "1.0"},
    })
    server_info = resp["result"].get("serverInfo", {}) if resp else {}
    print(f"[+] Server      : {server_info}")

    # notifications/initialized (required by MCP spec — no response)
    requests.post(messages_url,
                  json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                  timeout=5)

    # tools/list
    resp = mcp(messages_url, resp_q, "tools/list")
    tools = resp["result"].get("tools", []) if resp else []
    print(f"\n[+] {len(tools)} tools available:")
    for t in tools:
        print(f"    • {t['name']}")

    print("\n[+] Ready. Call mcp(messages_url, resp_q, 'tools/call', {...}) to use any tool.")
    sock.close()
