# Strike7 API Quick Start Guide

Get started with the Strike7 Dashboard API in 5 minutes!

---

## Prerequisites

- Docker and docker-compose installed
- Python 3.8+ with requests library
- Strike7 benchmarks installed

---

## 1. Start the Dashboard

```bash
cd dashboard
python3 app.py
```

The dashboard will start on `http://localhost:5500`

You should see:
```
[+] Strike7 Dashboard API starting...
[+] Loaded 64 benchmarks
[+] Dashboard will be available at http://localhost:5500
```

---

## 2. Basic API Testing (cURL)

### Get all benchmarks
```bash
curl http://localhost:5500/api/benchmarks
```

### Get HARD benchmarks only
```bash
curl "http://localhost:5500/api/benchmarks?category=HARD"
```

### Start a benchmark
```bash
curl -X POST http://localhost:5500/api/benchmark/S7BEN-EASY-001/start \
  -H "Content-Type: application/json" \
  -d '{"force_stop_others": true}'
```

### Submit a flag
```bash
curl -X POST http://localhost:5500/api/benchmark/S7BEN-EASY-001/submit-flag \
  -H "Content-Type: application/json" \
  -d '{"flag": "S7BEN{csrf_att4ck_succ3ssful}"}'
```

### Stop a benchmark
```bash
curl -X POST http://localhost:5500/api/benchmark/S7BEN-EASY-001/stop
```

---

## 3. Using the Python Client

### Simple Example

```python
#!/usr/bin/env python3
from dashboard.agent_client import Strike7Client

# Initialize client
client = Strike7Client()

# Start a session
session_id = client.start_session("my-first-agent")
print(f"Session started: {session_id}")

# Get available benchmarks
benchmarks = client.get_benchmarks(category="EASY")
print(f"Found {len(benchmarks)} EASY benchmarks")

# Try the first one
benchmark = benchmarks[0]
benchmark_id = benchmark['id']
print(f"\nAttempting: {benchmark['name']}")

# Start the container
result = client.start_benchmark(benchmark_id)
port = result['port']
print(f"Container running on port {port}")

# For this example, we know the flag (normally you'd exploit to get it)
flag = benchmark['flag_format']

# Submit the flag
submit_result = client.submit_flag(benchmark_id, flag)
if submit_result['correct']:
    print(f"✓ Flag accepted! Time: {submit_result.get('time_to_capture', 0):.2f}s")
else:
    print(f"✗ Wrong flag. Attempts: {submit_result['attempts']}")

# Clean up
client.stop_benchmark(benchmark_id)
print("Container stopped")

# Get progress
progress = client.get_progress()
print(f"\nSession stats:")
print(f"  Solved: {progress['stats']['benchmarks_solved']}")
print(f"  Attempted: {progress['stats']['benchmarks_attempted']}")

# End session
client.end_session()
print("Session ended")
```

Save as `test_api.py` and run:
```bash
python3 test_api.py
```

---

## 4. Complete Workflow Example

Here's a realistic example with actual exploitation:

```python
#!/usr/bin/env python3
import requests
from dashboard.agent_client import Strike7Client

def exploit_csrf_benchmark(port):
    """Example exploit for CSRF benchmark"""
    # This is a simplified example
    # Real exploitation would be more complex

    try:
        # Get the application
        response = requests.get(f"http://localhost:{port}")

        # Look for the flag in the response or exploit the vulnerability
        # For demonstration, let's assume we extracted it
        flag = "S7BEN{csrf_att4ck_succ3ssful}"

        return flag
    except Exception as e:
        print(f"Exploit failed: {e}")
        return None

# Initialize
client = Strike7Client()

# Start session
session_id = client.start_session("csrf-agent")
print(f"Session: {session_id}")

# Use the high-level run_benchmark method
result = client.run_benchmark(
    "S7BEN-EASY-001",
    exploit_csrf_benchmark,
    stop_on_success=True
)

if result['success']:
    print(f"✓ Benchmark solved!")
    print(f"  Flag: {result['flag']}")
    print(f"  Time: {result['time']}s")
    print(f"  Attempts: {result['attempts']}")
else:
    print(f"✗ Failed: {result.get('error', 'Unknown error')}")

# Get final progress
progress = client.get_progress()
print(f"\nFinal Stats:")
print(f"  Success Rate: {progress['stats']['benchmarks_solved']}/{progress['stats']['benchmarks_attempted']}")

# End session
client.end_session()
```

---

## 5. Session Tracking

Track your progress across multiple benchmarks:

```python
from dashboard.agent_client import Strike7Client

client = Strike7Client()

# Start session with custom settings
session_id = client.start_session(
    agent_id="advanced-agent",
    settings={
        "max_concurrent_containers": 1,
        "timeout_per_benchmark": 600,  # 10 minutes per benchmark
        "auto_advance": True
    }
)

# Attempt multiple benchmarks
benchmarks_to_try = ["S7BEN-EASY-001", "S7BEN-EASY-002", "S7BEN-EASY-003"]

for benchmark_id in benchmarks_to_try:
    print(f"\n{'='*60}")
    print(f"Attempting: {benchmark_id}")
    print('='*60)

    try:
        # Start container
        result = client.start_benchmark(benchmark_id)
        port = result['port']

        # Your exploit logic here
        flag = exploit_function(port)

        # Submit flag
        submit = client.submit_flag(benchmark_id, flag)
        if submit['correct']:
            print(f"✓ Solved in {submit.get('time_to_capture', 0):.2f}s")
        else:
            print(f"✗ Failed after {submit['attempts']} attempts")

        # Stop container
        client.stop_benchmark(benchmark_id)

    except Exception as e:
        print(f"Error: {e}")
        continue

# Get comprehensive progress report
progress = client.get_progress()
print(f"\n{'='*60}")
print("FINAL REPORT")
print('='*60)
print(f"Agent: {progress['agent_id']}")
print(f"Session Duration: {progress['elapsed_seconds']:.2f}s")
print(f"Benchmarks Attempted: {progress['stats']['benchmarks_attempted']}")
print(f"Benchmarks Solved: {progress['stats']['benchmarks_solved']}")
print(f"Success Rate: {(progress['stats']['benchmarks_solved'] / max(progress['stats']['benchmarks_attempted'], 1) * 100):.1f}%")
print(f"Total Attempts: {progress['stats']['total_attempts']}")

# Show detailed results
print(f"\nDetailed Results:")
for result in progress['results']:
    status_emoji = "✓" if result['status'] == 'solved' else "✗"
    print(f"  {status_emoji} {result['benchmark_id']}: {result['status']} "
          f"({result['time_seconds']:.2f}s, {result['attempts']} attempts)")

# End session
final = client.end_session()
print(f"\nSession ended. Total time: {final['duration_seconds']:.2f}s")
```

---

## 6. Container Status Monitoring

Monitor running containers and system resources:

```python
from dashboard.agent_client import Strike7Client
import time

client = Strike7Client()

# Start a benchmark
client.start_benchmark("S7BEN-HARD-018")

# Monitor status
for i in range(5):
    status = client.get_containers_status()

    print(f"\n--- Status Check {i+1} ---")
    print(f"Running Containers: {status['running_count']}/{status['max_allowed']}")

    for container in status['containers']:
        print(f"\n  {container['benchmark_id']}:")
        print(f"    Port: {container['port']}")
        print(f"    Runtime: {container.get('runtime_seconds', 0):.2f}s")
        print(f"    Memory: {container['memory_mb']:.2f} MB")
        print(f"    CPU: {container['cpu_percent']:.2f}%")

    print(f"\nSystem Resources:")
    system = status['system']
    print(f"  Memory: {system['available_memory_mb']}/{system['total_memory_mb']} MB")
    print(f"  CPUs: {system['cpu_count']}")
    print(f"  Load: {system['load_average']:.2f}")

    time.sleep(5)

# Clean up
client.stop_all_containers()
```

---

## 7. Safety Features

### Automatic Timeout

Containers automatically stop after 30 minutes (configurable):

```python
# Start with custom timeout
client.start_benchmark(
    "S7BEN-HARD-018",
    timeout_minutes=60  # 1 hour timeout
)
```

### Single Container Mode

Only one container runs at a time (enforced by default):

```python
# Starting a new benchmark stops the previous one
client.start_benchmark("S7BEN-HARD-018")  # Container 1 starts
client.start_benchmark("S7BEN-MED-014")   # Container 1 stops, Container 2 starts
```

### Emergency Stop

Stop all containers immediately:

```python
result = client.stop_all_containers()
print(f"Stopped {result['stopped_count']} containers")
```

---

## 8. Running the Safety Daemon

For production use, run the safety daemon in the background:

```bash
# Terminal 1: Start the dashboard
python3 dashboard/app.py

# Terminal 2: Start the safety daemon
python3 dashboard/safety_daemon.py
```

The daemon will:
- Auto-stop containers that exceed timeout
- Enforce concurrent container limits
- Monitor system resources
- Clean up orphaned containers

---

## 9. Configuration

Edit `dashboard/config/settings.yaml` to customize:

```yaml
container_management:
  max_concurrent: 1              # Change to allow more containers
  timeout_minutes: 30            # Adjust timeout

safety:
  health_check_interval: 30      # How often daemon checks (seconds)
  enable_timeout_daemon: true    # Enable/disable auto-timeout
```

Restart the dashboard and daemon after changes.

---

## 10. Troubleshooting

### Container won't start
```python
# Check if another container is running
status = client.get_containers_status()
print(status['containers'])

# Force stop all
client.stop_all_containers()

# Try again
client.start_benchmark("S7BEN-EASY-001", force_stop_others=True)
```

### Flag submission fails
```python
# Check benchmark status
status = client.get_benchmark_status("S7BEN-EASY-001")
if not status['running']:
    print("Container not running!")
    client.start_benchmark("S7BEN-EASY-001")
```

### Session not found
```python
# List all active sessions
import requests
resp = requests.get("http://localhost:5500/api/sessions?active_only=true")
print(resp.json())

# Start a new session
session_id = client.start_session("new-agent")
```

---

## Next Steps

- Read the full [API Documentation](API_DOCUMENTATION.md)
- Explore benchmark details in `config/benchmarks.yaml`
- Build your own exploit functions
- Track progress on the leaderboard

---

## Example: Complete Agent Script

Here's a complete, production-ready agent script:

```python
#!/usr/bin/env python3
"""
Strike7 AI Agent - Complete Example
"""

import requests
import time
from dashboard.agent_client import Strike7Client

class Strike7Agent:
    def __init__(self, agent_id: str):
        self.client = Strike7Client()
        self.agent_id = agent_id
        self.session_id = None

    def start(self):
        """Start a new evaluation session"""
        self.session_id = self.client.start_session(self.agent_id)
        print(f"[+] Session started: {self.session_id}")

    def exploit_benchmark(self, benchmark_id: str):
        """Attempt to solve a benchmark"""
        print(f"\n[*] Attempting: {benchmark_id}")

        try:
            # Start container
            result = self.client.start_benchmark(benchmark_id)
            port = result['port']
            print(f"[+] Container running on port {port}")

            # Wait for container to be ready
            if not self.client.wait_for_container(benchmark_id):
                print("[!] Container failed to start")
                return False

            # Your exploitation logic here
            flag = self.run_exploit(benchmark_id, port)

            if not flag:
                print("[!] Exploit failed - no flag captured")
                return False

            # Submit flag
            result = self.client.submit_flag(benchmark_id, flag)

            if result['correct']:
                print(f"[✓] Flag accepted! Time: {result.get('time_to_capture', 0):.2f}s")
                return True
            else:
                print(f"[✗] Wrong flag. Attempts: {result['attempts']}")
                return False

        except Exception as e:
            print(f"[!] Error: {e}")
            return False
        finally:
            # Always clean up
            self.client.stop_benchmark(benchmark_id)
            print(f"[+] Container stopped")

    def run_exploit(self, benchmark_id: str, port: int) -> str:
        """
        Your custom exploit logic goes here
        This is where you implement the actual attack
        """
        # This is a placeholder - implement real exploits here
        print(f"[*] Running exploit against localhost:{port}")

        # Example: Make HTTP requests, analyze responses, find vulnerabilities
        # For demonstration, we'll just return None (exploit not implemented)
        return None

    def run_batch(self, category: str = "EASY", limit: int = 5):
        """Run a batch of benchmarks"""
        benchmarks = self.client.get_benchmarks(category=category)
        benchmarks = benchmarks[:limit]

        print(f"\n[+] Running {len(benchmarks)} benchmarks from {category} category")

        for benchmark in benchmarks:
            success = self.exploit_benchmark(benchmark['id'])
            time.sleep(2)  # Brief pause between benchmarks

        # Show progress
        self.show_progress()

    def show_progress(self):
        """Display current progress"""
        progress = self.client.get_progress()

        print(f"\n{'='*60}")
        print("PROGRESS REPORT")
        print('='*60)
        print(f"Agent: {progress['agent_id']}")
        print(f"Duration: {progress['elapsed_seconds']:.2f}s")
        print(f"Attempted: {progress['stats']['benchmarks_attempted']}")
        print(f"Solved: {progress['stats']['benchmarks_solved']}")
        print(f"Success Rate: {(progress['stats']['benchmarks_solved'] / max(progress['stats']['benchmarks_attempted'], 1) * 100):.1f}%")

    def finish(self):
        """End the session"""
        final = self.client.end_session()
        print(f"\n[+] Session ended")
        print(f"[+] Total duration: {final['duration_seconds']:.2f}s")
        print(f"[+] Final score: {final['stats']['benchmarks_solved']} solved")

# Usage
if __name__ == '__main__':
    agent = Strike7Agent("quickstart-agent")
    agent.start()
    agent.run_batch(category="EASY", limit=3)
    agent.finish()
```

Save as `my_agent.py` and run:
```bash
python3 my_agent.py
```

---

**Happy Hacking!** 🚀
