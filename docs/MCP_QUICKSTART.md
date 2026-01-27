# Strike7 MCP Server - Quick Start Guide

**Model Context Protocol (MCP)** allows AI agents like Claude to connect to Strike7 and interact with security benchmarks programmatically.

---

## What is MCP?

MCP is a protocol that lets AI models:
- Call **tools** (functions like start_benchmark, submit_flag)
- Read **resources** (data like benchmark lists, progress)
- Use **prompts** (pre-built templates for common tasks)

Think of it as an API specifically designed for AI agents.

---

## Quick Setup (5 minutes)

### Step 1: Test the MCP Server

```bash
# Make it executable
chmod +x dashboard/mcp_server_minimal.py

# Test it works
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python dashboard/mcp_server_minimal.py
```

You should see a JSON response listing available tools.

### Step 2: Configure Claude Desktop

Add to your Claude Desktop config file:

**Location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Config:**
```json
{
  "mcpServers": {
    "strike7": {
      "command": "python",
      "args": ["/home/atheeque/workspace/strike7-benchmarks/dashboard/mcp_server_minimal.py"]
    }
  }
}
```

**Important:** Use the full absolute path to `mcp_server_minimal.py`

### Step 3: Restart Claude Desktop

After saving the config, restart Claude Desktop. You should see a 🔌 icon indicating MCP servers are connected.

---

## Available Tools

### 1. strike7_start_benchmark
Start a benchmark container.

**Parameters:**
- `benchmark_id` (required): e.g., "S7BEN-EASY-001"
- `timeout_minutes` (optional): Auto-stop timeout, default 30

**Example:**
```
Can you start the CSRF benchmark S7BEN-EASY-001?
```

**Response:**
```json
{
  "status": "success",
  "benchmark_id": "S7BEN-EASY-001",
  "port": 5000,
  "container_name": "s7ben-easy-001-app-1",
  "started_at": "2026-01-23T10:00:00"
}
```

### 2. strike7_submit_flag
Submit a captured flag.

**Parameters:**
- `benchmark_id` (required)
- `flag` (required): The captured flag

**Example:**
```
Submit the flag S7BEN{csrf_att4ck_succ3ssful} for S7BEN-EASY-001
```

**Response:**
```json
{
  "status": "success",
  "correct": true,
  "attempts": 1,
  "time_to_capture": 45.2
}
```

### 3. strike7_stop_benchmark
Stop a running container.

**Parameters:**
- `benchmark_id` (required)

**Example:**
```
Stop the S7BEN-EASY-001 benchmark
```

### 4. strike7_get_status
Get status of all running containers.

**Parameters:** None

**Example:**
```
What Strike7 containers are currently running?
```

---

## Available Resources

### strike7://benchmarks
Complete list of all 64 benchmarks with metadata.

**Example:**
```
Show me all Strike7 benchmarks
```

### strike7://session/progress
Current session progress and statistics.

**Example:**
```
What's my progress on Strike7 benchmarks?
```

---

## Example Conversations

### Basic Workflow

```
User: Start the CSRF benchmark S7BEN-EASY-001

Claude: [Calls strike7_start_benchmark]
The benchmark is now running on port 5000.

User: Can you exploit it and get the flag?

Claude: [Analyzes the CSRF vulnerability]
[Crafts exploit]
[Captures flag]
[Calls strike7_submit_flag]

Success! The flag has been validated. Time to capture: 45.2 seconds.

User: Stop the benchmark

Claude: [Calls strike7_stop_benchmark]
Benchmark stopped. Runtime: 60 seconds.
```

### Discovery Workflow

```
User: Show me all HARD difficulty benchmarks

Claude: [Reads strike7://benchmarks resource]
[Filters for HARD category]

Here are the 14 HARD difficulty benchmarks:
1. S7BEN-HARD-017: Client-Side Price Manipulation
2. S7BEN-HARD-018: Kubernetes RBAC Privilege Escalation
...

User: Tell me more about the Kubernetes one

Claude: [Reads strike7://benchmark/S7BEN-HARD-018]

This benchmark tests Kubernetes RBAC privilege escalation:
- OWASP: A05 (Security Misconfiguration)
- CWE: CWE-250
- Port: 8101
- Difficulty: 8/9
...
```

---

## Testing Without Claude Desktop

You can test the MCP server directly using stdio:

```bash
# Start the server
python dashboard/mcp_server_minimal.py

# Send requests (in another terminal or via pipe)
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python dashboard/mcp_server_minimal.py

echo '{"jsonrpc":"2.0","id":2,"method":"resources/list","params":{}}' | python dashboard/mcp_server_minimal.py
```

---

## Troubleshooting

### Issue: Claude says "No MCP servers connected"
**Solution:** Check the config file path and restart Claude Desktop

### Issue: "Command not found" error
**Solution:** Use absolute path to Python and script:
```json
{
  "command": "/usr/bin/python3",
  "args": ["/full/path/to/mcp_server_minimal.py"]
}
```

### Issue: Benchmark won't start
**Solution:**
1. Make sure the dashboard API is running: `python dashboard/app.py`
2. Check Docker is running: `docker ps`
3. Look at server logs in Claude Desktop console

### Issue: Flag submission says "Benchmark not found"
**Solution:** Ensure the dashboard has loaded the benchmarks correctly. Check `dashboard/config/benchmarks.yaml` exists.

---

## Next Steps

### For Users
1. Try exploiting a simple benchmark through Claude
2. Ask Claude to show you the benchmark list
3. Have Claude track your progress

### For Developers
1. Add more tools (execute_command, get_hints)
2. Add more resources (telemetry, leaderboard)
3. Implement prompts for guided exploitation
4. Add HTTP transport for remote agents

---

## Advanced: HTTP Transport

For remote AI agents, you can expose MCP over HTTP:

```python
# dashboard/mcp_server_http.py
# TODO: Implement SSE transport
```

Then agents can connect via:
```
http://localhost:5501/mcp
```

---

## Architecture

```
┌──────────────────────────────────────────┐
│        Claude / AI Agent                 │
│  ────────────────────────────────────── │
│  "Start S7BEN-EASY-001"                  │
└──────────────┬───────────────────────────┘
               │ MCP Protocol (JSON-RPC)
               ▼
┌──────────────────────────────────────────┐
│     Strike7 MCP Server (stdio)           │
│  ────────────────────────────────────── │
│  Tools: start, stop, submit, status      │
│  Resources: benchmarks, progress         │
└──────────────┬───────────────────────────┘
               │ Python API Calls
               ▼
┌──────────────────────────────────────────┐
│    Strike7 Dashboard (Flask API)         │
│  ────────────────────────────────────── │
│  ContainerManager, FlagValidator, etc.   │
└──────────────┬───────────────────────────┘
               │ Docker Commands
               ▼
┌──────────────────────────────────────────┐
│        Docker Containers                 │
│  ────────────────────────────────────── │
│  S7BEN-EASY-001, S7BEN-HARD-018, etc.    │
└──────────────────────────────────────────┘
```

---

## Documentation

- **MCP Protocol Spec:** https://modelcontextprotocol.io/
- **Strike7 API Docs:** `dashboard/API_DOCUMENTATION.md`
- **Claude Desktop Config:** https://docs.anthropic.com/claude/docs/desktop-configuration

---

**Version:** 1.0
**Last Updated:** 2026-01-23
**Status:** Prototype - Basic functionality working
