"""
Strike7 Orchestrator Configuration

Loads configuration from orchestrator.yaml or environment variables.
Supports two modes:
  - local: Docker commands run on the same machine (Phase 0)
  - remote: Docker commands run via SSH on worker nodes (Phase 1+)
"""

import os
import yaml
import logging

logger = logging.getLogger("s7.orchestrator.config")

DEFAULT_CONFIG = {
    "mode": "local",  # "local" or "remote"
    "benchmarks_dir": "/opt/strike7.ai-benchmark-harness/benchmarks",
    "docker_compose_cmd": "docker-compose",  # v1 on VPS
    "dashboard_port": 5500,

    # Port pool configuration
    "port_pool": {
        "start": 5001,
        "end": 5299,
        "reserved": [5500],  # Dashboard port - never allocate
    },

    # Session / timeout configuration
    "timeouts": {
        "EASY": 1800,      # 30 minutes
        "MED": 3600,        # 60 minutes
        "HARD": 7200,       # 120 minutes
        "VHARD": 10800,     # 180 minutes
        "CVE": 7200,        # 120 minutes
        "default": 3600,    # 60 minutes fallback
    },

    # Concurrency limits
    "limits": {
        "max_containers_per_worker": 15,
        "max_containers_global": 30,
        "max_per_agent_session": 3,
    },

    # Health monitoring
    "health": {
        "check_interval_seconds": 30,
        "unhealthy_threshold": 3,  # consecutive failures before marking unhealthy
    },

    # Workers (only used in remote mode)
    "workers": [
        {
            "id": "local",
            "host": "localhost",
            "mode": "local",
            "ssh_user": None,
            "ssh_key": None,
            "port_range": [5001, 5299],
            "max_containers": 15,
        }
    ],

    # Proxy configuration (for routing agent traffic to workers)
    "proxy": {
        "enabled": False,  # Enable when using remote workers
        "timeout_seconds": 30,
    },

    # Logging
    "log_level": "INFO",
    "log_file": "/var/log/strike7/orchestrator.log",

    # Database for session tracking
    "db_path": "data/orchestrator.db",
}


class OrchestratorConfig:
    """Configuration manager for the orchestrator."""

    def __init__(self, config_path=None):
        self._config = dict(DEFAULT_CONFIG)

        # Try loading from file
        if config_path and os.path.exists(config_path):
            self._load_from_file(config_path)
        else:
            # Auto-detect config file locations
            search_paths = [
                os.path.join(os.path.dirname(__file__), "..", "orchestrator.yaml"),
                "/opt/strike7.ai-benchmark-harness/orchestrator.yaml",
                os.path.expanduser("~/orchestrator.yaml"),
            ]
            for path in search_paths:
                if os.path.exists(path):
                    self._load_from_file(path)
                    break

        # Environment overrides (highest priority)
        self._load_from_env()

        logger.info(f"Orchestrator config loaded: mode={self.mode}, "
                     f"benchmarks_dir={self.benchmarks_dir}")

    def _load_from_file(self, path):
        """Load config from YAML file, merging with defaults."""
        try:
            with open(path, "r") as f:
                file_config = yaml.safe_load(f) or {}
            self._deep_merge(self._config, file_config)
            logger.info(f"Config loaded from {path}")
        except Exception as e:
            logger.warning(f"Failed to load config from {path}: {e}")

    def _load_from_env(self):
        """Override config from environment variables."""
        env_map = {
            "S7_ORCHESTRATOR_MODE": ("mode", str),
            "S7_BENCHMARKS_DIR": ("benchmarks_dir", str),
            "S7_DOCKER_COMPOSE_CMD": ("docker_compose_cmd", str),
            "S7_DASHBOARD_PORT": ("dashboard_port", int),
            "S7_PORT_POOL_START": ("port_pool.start", int),
            "S7_PORT_POOL_END": ("port_pool.end", int),
            "S7_MAX_CONTAINERS": ("limits.max_containers_per_worker", int),
            "S7_LOG_LEVEL": ("log_level", str),
            "S7_DB_PATH": ("db_path", str),
        }
        for env_key, (config_path, cast_fn) in env_map.items():
            val = os.environ.get(env_key)
            if val is not None:
                self._set_nested(config_path, cast_fn(val))

    def _deep_merge(self, base, override):
        """Recursively merge override dict into base dict."""
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._deep_merge(base[k], v)
            else:
                base[k] = v

    def _set_nested(self, path, value):
        """Set a nested config value using dot notation."""
        keys = path.split(".")
        d = self._config
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value

    def _get_nested(self, path, default=None):
        """Get a nested config value using dot notation."""
        keys = path.split(".")
        d = self._config
        for k in keys:
            if isinstance(d, dict):
                d = d.get(k)
            else:
                return default
            if d is None:
                return default
        return d

    # Convenience properties
    @property
    def mode(self):
        return self._config["mode"]

    @property
    def benchmarks_dir(self):
        return self._config["benchmarks_dir"]

    @property
    def docker_compose_cmd(self):
        return self._config["docker_compose_cmd"]

    @property
    def port_pool_start(self):
        return self._config["port_pool"]["start"]

    @property
    def port_pool_end(self):
        return self._config["port_pool"]["end"]

    @property
    def reserved_ports(self):
        return set(self._config["port_pool"].get("reserved", []))

    @property
    def workers(self):
        return self._config["workers"]

    @property
    def timeouts(self):
        return self._config["timeouts"]

    @property
    def limits(self):
        return self._config["limits"]

    @property
    def health_check_interval(self):
        return self._config["health"]["check_interval_seconds"]

    @property
    def db_path(self):
        return self._config["db_path"]

    @property
    def log_level(self):
        return self._config["log_level"]

    def get_timeout_for_tier(self, tier):
        """Get timeout in seconds for a benchmark difficulty tier."""
        tier_upper = tier.upper() if tier else "DEFAULT"
        return self.timeouts.get(tier_upper, self.timeouts["default"])

    def get_worker(self, worker_id="local"):
        """Get worker config by ID."""
        for w in self.workers:
            if w["id"] == worker_id:
                return w
        return None

    def to_dict(self):
        """Export config as dict (for API responses)."""
        # Sanitize sensitive fields
        safe = dict(self._config)
        for w in safe.get("workers", []):
            if w.get("ssh_key"):
                w["ssh_key"] = "***REDACTED***"
        return safe
