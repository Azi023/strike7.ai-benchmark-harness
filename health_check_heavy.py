import requests
import time
import json
import subprocess

API_URL = "http://localhost:5500"

# Only the ones that timed out
TIMEOUT_IDS = [
    "S7BEN-VHARD-001", "S7BEN-VHARD-003", "S7BEN-VHARD-004", 
    "S7BEN-VHARD-007", "S7BEN-VHARD-008", "S7BEN-CVE-003", 
    "S7BEN-CVE-004"
]

results = []

def check_health(bid):
    print(f"Starting {bid}...")
    try:
        # Increase timeout to 350s for heavy benchmarks
        start_res = requests.post(f"{API_URL}/api/benchmark/{bid}/start", 
                                 json={"force_stop_others": True}, 
                                 timeout=350)
        
        if start_res.status_code != 200:
            return {"id": bid, "status": "ERROR", "message": f"Start failed: {start_res.text}"}
        
        data = start_res.json()
        port = data.get("port")
        if not port:
            return {"id": bid, "status": "ERROR", "message": "No port in response"}
        
        print(f"Waiting 30s for {bid} on port {port}...")
        time.sleep(30)
        
        try:
            # Check reachability
            curl_res = subprocess.run(f'curl -s -o /dev/null -w "%{{http_code}}" http://localhost:{port}/', 
                                    shell=True, capture_output=True, text=True, timeout=10)
            code = curl_res.stdout.strip()
            if code == "000":
                # Try nmap to be sure
                nmap_res = subprocess.run(f"nmap -p {port} localhost", shell=True, capture_output=True, text=True)
                if f"{port}/tcp open" in nmap_res.stdout:
                    return {"id": bid, "status": "STARTED_OK", "port": port, "code": "OPEN_BUT_NO_HTTP"}
                else:
                    # Get docker logs
                    cmd = "docker ps -a --filter name=" + bid + " --format '{{.ID}}'"
                    logs_proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    cid_list = logs_proc.stdout.strip().split("\n")
                    if cid_list and cid_list[0]:
                        cid = cid_list[0]
                        docker_logs = subprocess.run(f"docker logs {cid} --tail 20", shell=True, capture_output=True, text=True)
                        return {"id": bid, "status": "TIMEOUT", "port": port, "logs": docker_logs.stdout.strip()}
                    return {"id": bid, "status": "TIMEOUT", "port": port}
            else:
                return {"id": bid, "status": "STARTED_OK", "port": port, "code": code}
        except Exception as e:
            return {"id": bid, "status": "ERROR", "message": str(e)}
            
    except Exception as e:
        return {"id": bid, "status": "ERROR", "message": str(e)}

print("Starting heavy benchmark health checks...")
for bid in TIMEOUT_IDS:
    results.append(check_health(bid))

with open("health_results_heavy.json", "w") as f:
    json.dump(results, f, indent=2)

print("Health checks completed. Results saved to health_results_heavy.json")
