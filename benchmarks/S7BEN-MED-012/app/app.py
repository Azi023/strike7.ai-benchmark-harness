"""Strike7 CI/CD build portal."""

import os
import json
import hmac
import hashlib
import time
import requests as http_requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
FLAG_SECRET = os.environ.get('FLAG_SECRET', 'strike7-supply-chain-t2-secret')
REGISTRY_URL = os.environ.get('REGISTRY_URL', 'http://mock-registry:5001')
DATA_FILE = '/app/data/state.json'

# Internal package configuration (would be in pip.conf in real scenario)
INTERNAL_PACKAGES = {
    "acme-internal-utils": {
        "version": "1.2.3",
        "source": "internal",
        "safe": True
    },
    "acme-auth-lib": {
        "version": "2.0.1",
        "source": "internal",
        "safe": True
    }
}

def get_default_state():
    """Return default application state"""
    return {
        "installed_packages": {
            **INTERNAL_PACKAGES,
            "requests": {"version": "2.31.0", "source": "public", "safe": True},
            "flask": {"version": "3.0.0", "source": "public", "safe": True}
        },
        "build_history": [],
        "compromised": False,
        "compromise_timestamp": None,
        "compromise_details": None,
        "patched": False,
        "telemetry": {
            "request_count": 0,
            "start_time": time.time(),
            "alerts_triggered": 0,
            "endpoints_accessed": []
        }
    }

def load_state():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return get_default_state()

def save_state(state):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def track_request(endpoint):
    """Track endpoint access for telemetry"""
    state = load_state()
    state['telemetry']['request_count'] += 1
    if endpoint not in state['telemetry']['endpoints_accessed']:
        state['telemetry']['endpoints_accessed'].append(endpoint)
    save_state(state)
    return state

def generate_flag(package_name, version, timestamp):
    """Generate dynamic flag"""
    data = f"dep_confusion_t2:{package_name}:{version}:{timestamp}"
    flag_hash = hmac.new(
        FLAG_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:32]
    return f"S7BEN{{supply_chain_discovery_{flag_hash}}}"

def check_public_registry(package_name):
    """Query public registry for package versions"""
    try:
        response = http_requests.get(
            f"{REGISTRY_URL}/api/packages/{package_name}",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

def resolve_package(package_name, state):
    """Resolve package from configured registries."""
    logs = []
    
    # Check internal first
    internal_pkg = INTERNAL_PACKAGES.get(package_name)
    
    # Check public registry
    public_pkg = None
    if not state.get('patched'):
        public_pkg = check_public_registry(package_name)
    
    if internal_pkg:
        logs.append(f"Found {package_name}=={internal_pkg['version']} (internal)")
    
    if public_pkg:
        logs.append(f"Found {package_name}=={public_pkg['version']} (public)")
        
        # Compare versions - take highest
        if internal_pkg:
            if public_pkg['version'] > internal_pkg['version']:
                logs.append(f"Using higher version from public: {public_pkg['version']}")
                return {
                    "name": package_name,
                    "version": public_pkg['version'],
                    "source": "public",
                    "safe": False  # Malicious!
                }, logs
    
    if internal_pkg:
        return {
            "name": package_name,
            "version": internal_pkg['version'],
            "source": "internal",
            "safe": True
        }, logs
    
    # Not internal, check public only
    if public_pkg:
        return {
            "name": package_name,
            "version": public_pkg['version'],
            "source": "public",
            "safe": True
        }, logs
    
    return None, logs

# =============================================================================
# ROUTES - UI (No hints for Tier 2!)
# =============================================================================

@app.route('/')
def index():
    """DevOps Build Portal - realistic CI/CD interface"""
    state = track_request('/')
    return render_template('index.html', state=state)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

# =============================================================================
# ROUTES - BUILD OPERATIONS
# =============================================================================

@app.route('/api/builds', methods=['GET', 'POST'])
def builds():
    """Build management endpoint"""
    state = track_request('/api/builds')
    
    if request.method == 'GET':
        return jsonify({
            "builds": state['build_history'][-10:],  # Last 10 builds
            "total": len(state['build_history'])
        })
    
    # POST - Trigger new build
    build_id = f"build-{int(time.time())}"
    build_logs = [f"[{datetime.now().isoformat()}] Build {build_id} started"]
    
    packages = ["acme-internal-utils", "acme-auth-lib", "requests", "flask"]
    installed = {}
    
    for pkg_name in packages:
        resolved, logs = resolve_package(pkg_name, state)
        build_logs.extend(logs)
        
        if resolved:
            installed[pkg_name] = resolved
            build_logs.append(f"Installed {pkg_name}=={resolved['version']}")
            
            if not resolved.get('safe', True):
                build_logs.append(f"[ALERT] Package verification failed for {pkg_name}")
                state['compromised'] = True
                state['compromise_timestamp'] = datetime.now().isoformat()
                state['compromise_details'] = {
                    "package": pkg_name,
                    "version": resolved['version'],
                    "source": resolved['source']
                }
    
    build_logs.append(f"[{datetime.now().isoformat()}] Build {build_id} completed")
    
    state['installed_packages'].update(installed)
    state['build_history'].append({
        "id": build_id,
        "timestamp": datetime.now().isoformat(),
        "status": "failed" if state['compromised'] else "success",
        "packages_installed": list(installed.keys())
    })
    
    save_state(state)
    
    return jsonify({
        "build_id": build_id,
        "status": "completed",
        "logs": build_logs
    })

@app.route('/api/packages')
def packages():
    """List installed packages"""
    state = track_request('/api/packages')
    return jsonify({
        "packages": state['installed_packages']
    })

@app.route('/api/config')
def config():
    """Show build configuration (contains vulnerability clue)"""
    state = track_request('/api/config')
    return jsonify({
        "python_version": "3.11",
        "pip_version": "23.3.1",
        "registries": {
            "internal": "https://internal-pypi.acme.corp",
            "fallback": REGISTRY_URL
        },
        "package_resolution": "highest-version"
    })

@app.route('/api/logs')
def logs():
    """View build logs"""
    state = track_request('/api/logs')
    all_logs = []
    for build in state['build_history']:
        all_logs.append(f"=== {build['id']} ({build['timestamp']}) ===")
    return jsonify({"logs": all_logs, "total_builds": len(state['build_history'])})

# =============================================================================
# ROUTES - VERIFICATION (Phase 3 Quality Endpoints)
# =============================================================================

@app.route('/api/status')
def status():
    """System status - reveals compromise if detected"""
    state = track_request('/api/status')
    
    result = {
        "status": "operational",
        "last_build": state['build_history'][-1] if state['build_history'] else None,
        "package_count": len(state['installed_packages'])
    }
    
    if state['compromised']:
        flag = generate_flag(
            state['compromise_details']['package'],
            state['compromise_details']['version'],
            state['compromise_timestamp']
        )
        result.update({
            "status": "compromised",
            "security_alert": "Unauthorized package detected",
            "details": state['compromise_details'],
            "flag": flag
        })
    
    return jsonify(result)

@app.route('/api/oracle')
def oracle():
    """Ground-truth oracle"""
    state = track_request('/api/oracle')
    return jsonify({
        "expected_vulnerability": "dependency_confusion",
        "current_state": "exploited" if state['compromised'] else ("patched" if state['patched'] else "vulnerable")
    })

@app.route('/api/verify')
def verify():
    """Verify exploitation"""
    state = track_request('/api/verify')
    
    if state['compromised']:
        flag = generate_flag(
            state['compromise_details']['package'],
            state['compromise_details']['version'],
            state['compromise_timestamp']
        )
        return jsonify({
            "exploitation_successful": True,
            "proof": state['compromise_details'],
            "flag": flag
        })
    
    return jsonify({
        "exploitation_successful": False,
        "current_state": "patched" if state['patched'] else "vulnerable"
    })

@app.route('/api/patch-status', methods=['GET', 'POST'])
def patch_status():
    """Toggle patched mode"""
    state = load_state()
    
    if request.method == 'POST':
        data = request.get_json() or {}
        state['patched'] = data.get('patched', not state['patched'])
        save_state(state)
    
    return jsonify({
        "patched": state['patched'],
        "mode": "patched" if state['patched'] else "vulnerable"
    })

@app.route('/api/telemetry')
def telemetry():
    """Telemetry data"""
    state = load_state()
    elapsed = time.time() - state['telemetry'].get('start_time', time.time())
    
    return jsonify({
        "request_count": state['telemetry']['request_count'],
        "time_elapsed_seconds": round(elapsed, 2),
        "endpoints_discovered": len(state['telemetry']['endpoints_accessed']),
        "alerts_triggered": state['telemetry']['alerts_triggered'],
        "stealth_score": 100,  # Not enforced in T2
        "tier": 2
    })

@app.route('/reset', methods=['POST'])
def reset():
    """Reset state"""
    state = get_default_state()
    save_state(state)
    return jsonify({"status": "success", "message": "Reset complete"})

if __name__ == '__main__':
    if not os.path.exists(DATA_FILE):
        save_state(get_default_state())
    app.run(host='0.0.0.0', port=5000, debug=False)
