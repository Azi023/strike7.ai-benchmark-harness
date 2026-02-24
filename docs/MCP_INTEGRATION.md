# Strike7 MCP Integration Guide

Live MCP server: `http://139.59.80.137/mcp/sse`

---

## 1. Verify the Server is Up (Do This First)

```bash
curl -s http://139.59.80.137/mcp/health | python3 -m json.tool
```

Expected response:

```json
{
  "status": "healthy",
  "service": "strike7-mcp",
  "tools_available": 11,
  "sse_endpoint": "http://139.59.80.137/mcp/sse",
  "messages_endpoint": "http://139.59.80.137/mcp/messages/",
  "health_endpoint": "http://139.59.80.137/mcp/health"
}
```

If `status` is not `"healthy"`, stop here and check the VPS.

---

## 2. How MCP/SSE Transport Works

The MCP server uses **Server-Sent Events (SSE)** as the transport layer.
This is **bidirectional over two separate connections**:

```
Client                                    Server
  |                                          |
  |── GET /mcp/sse ──────────────────────►  |  (SSE stream, stays open)
  |◄─ event: endpoint ──────────────────────|  first event: gives messages path
  |   data: /mcp/messages/?session_id=XXX   |
  |                                          |
  |── POST /mcp/messages/?session_id=XXX ►  |  (send JSON-RPC request)
  |◄─ HTTP 202 Accepted ────────────────────|  ACK only — NOT the result
  |                                          |
  |◄─ data: {"jsonrpc":"2.0","id":1,...} ───|  result arrives on SSE stream
```

Key points:
- **POST responses are always `202 Accepted`** with body `Accepted`. The actual JSON-RPC result comes back as an `event: message` on the SSE stream.
- **SSE events use `\r\n\r\n` as separators**, not `\n\n`. Normalise line endings before parsing.
- After `initialize`, you must send `notifications/initialized` (no response expected).
- The SSE stream stays open for the entire session. Close it when done.

---

## 3. Correct Endpoints

| Purpose | URL |
|---------|-----|
| Open SSE stream | `GET http://139.59.80.137/mcp/sse` |
| Send JSON-RPC | `POST http://139.59.80.137/mcp/messages/?session_id=<id>` |
| Health check | `GET http://139.59.80.137/mcp/health` |

> **Important:** The SSE `data:` line advertises `/mcp/messages/?session_id=...` (with the `/mcp/` prefix). Use the full path from the `data:` line directly — do not prepend a base URL manually.

---

## 4. Connection Handshake (3 steps)

### Step 1 — Open SSE stream and get session ID

```bash
curl -s --max-time 5 http://139.59.80.137/mcp/sse
# Output:
# event: endpoint
# data: /mcp/messages/?session_id=<32-char-hex>
```

Parse the `session_id` from the `data:` line.

### Step 2 — Send `initialize`

```bash
curl -s -X POST "http://139.59.80.137/mcp/messages/?session_id=<id>" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "my-agent", "version": "1.0"}
    }
  }'
# Returns: 202 Accepted
# Result arrives on the SSE stream as: event: message / data: {"jsonrpc":"2.0","id":1,"result":{...}}
```

### Step 3 — Send `notifications/initialized`

```bash
curl -s -X POST "http://139.59.80.137/mcp/messages/?session_id=<id>" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "notifications/initialized"}'
# Returns: 202 Accepted  (no result event expected)
```

After these 3 steps you can call any tool.

---

## 5. Available Tools (11 total)

| Tool | Description | Key Arguments |
|------|-------------|---------------|
| `list_benchmarks` | List/filter benchmarks | `category`, `owasp` |
| `get_benchmark_details` | Full benchmark info | `benchmark_id` |
| `start_benchmark` | Start a container | `benchmark_id`, `timeout_minutes` |
| `stop_benchmark` | Stop a container | `benchmark_id` |
| `get_container_status` | List running containers | — |
| `submit_flag` | Validate a captured flag | `benchmark_id`, `flag` |
| `execute_command` | Run shell command on server | `command`, `timeout` |
| `get_statistics` | Benchmark statistics | — |
| `start_session` | Start evaluation session | `agent_id` |
| `get_metrics` | Evaluation metrics | `agent_id` (optional) |
| `health_check` | Check API connectivity | — |

### Example: call `tools/list`

```bash
curl -s -X POST "http://139.59.80.137/mcp/messages/?session_id=<id>" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
# Result arrives on SSE stream
```

### Example: call `start_benchmark`

```bash
curl -s -X POST "http://139.59.80.137/mcp/messages/?session_id=<id>" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 3,
    "method": "tools/call",
    "params": {
      "name": "start_benchmark",
      "arguments": {"benchmark_id": "S7BEN-EASY-001", "timeout_minutes": 30}
    }
  }'
```

---

## 6. Ready-Made Python Client

A minimal working client is available at `docs/mcp_client_example.py`.
It handles SSE threading, the path correction, and the full handshake
in under 100 lines. Use it as a starting point:

```bash
python3 docs/mcp_client_example.py
```

---

## 7. MCP Inspector (Interactive Exploration)

Browse all tools and test calls without writing any code:

```bash
npx @modelcontextprotocol/inspector http://139.59.80.137/mcp/sse
```

This opens a web UI where you can see all 11 tools, their schemas, and
invoke them interactively. Ideal for initial exploration before building an agent.

---

## 8. Claude Desktop Configuration (stdio mode)

For local development, run the MCP server as a subprocess (no SSE needed):

```json
{
  "mcpServers": {
    "strike7": {
      "command": "python3",
      "args": ["/path/to/strike7-benchmarks/dashboard/strike7_mcp_server.py"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "STRIKE7_API_URL": "http://localhost:5500"
      }
    }
  }
}
```

For connecting to the live VPS server from Claude Desktop:

```json
{
  "mcpServers": {
    "strike7-remote": {
      "url": "http://139.59.80.137/mcp/sse",
      "transport": "sse"
    }
  }
}
```

---

## 9. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `404` on POST to `/messages/` | Missing `/mcp/` prefix | Use `/mcp/messages/?session_id=...` |
| `202` but no SSE result | SSE stream closed early | Keep GET connection open during entire session |
| Session ID invalid | New SSE connection needed | Re-connect to `/mcp/sse` to get fresh session |
| Tools call returns `isError: true` | Wrong tool name | Check `tools/list` — names have no `strike7_` prefix |
| Container timeout on port 5001 | Benchmark not started | Call `start_benchmark` first; wait ~5-7s for healthcheck |
