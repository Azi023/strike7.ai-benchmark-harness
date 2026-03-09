"""Tail nginx benchmark access log and record steps to runs."""
import time
import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.run_tracker import RunTracker

LOG_FILE = "/var/log/strike7/benchmark_steps.log"
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "model_benchmarks.db",
)


def parse_line(line):
    """Parse: 2026-03-09T17:38:12+00:00|GET|/benchmark/5002/login|200|0.045|0.043|1234|..."""
    parts = line.strip().split("|")
    if len(parts) < 7:
        return None

    timestamp, method, uri, status, req_time, upstream_time, body_size = parts[:7]

    # Extract port from URI: /benchmark/5002/login -> port=5002, path=/login
    match = re.match(r"/benchmark/(\d+)(.*)", uri)
    if not match:
        return None

    port = int(match.group(1))
    path = match.group(2) or "/"
    duration_ms = float(req_time) * 1000 if req_time != "-" else None

    return {
        "port": port,
        "method": method,
        "path": path,
        "status_code": int(status) if status != "-" else None,
        "duration_ms": duration_ms,
        "response_size": int(body_size) if body_size != "-" else None,
        "source_ip": parts[7] if len(parts) > 7 else None,
    }


def tail_and_log():
    tracker = RunTracker(DB_PATH)

    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "w").close()

    with open(LOG_FILE, "r") as f:
        f.seek(0, 2)  # Seek to end
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue

            parsed = parse_line(line)
            if not parsed:
                continue

            # Find active run for this port
            run = tracker.get_active_run_by_port(parsed["port"])
            if run and run.get("run_id"):
                tracker.add_step(
                    run_id=run["run_id"],
                    method=parsed["method"],
                    path=parsed["path"],
                    status_code=parsed["status_code"],
                    duration_ms=parsed["duration_ms"],
                    response_size=parsed["response_size"],
                    source_ip=parsed["source_ip"],
                )


if __name__ == "__main__":
    print("Step logger started, tailing", LOG_FILE)
    tail_and_log()
