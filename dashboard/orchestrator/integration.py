"""
Strike7 Orchestrator Integration

This module initializes the orchestrator and registers it with the Flask app.
Import this and call `init_orchestrator(app)` in your existing app.py.

Usage in app.py:
    from orchestrator.integration import init_orchestrator
    app = Flask(__name__)
    init_orchestrator(app)

That's it. The orchestrator will:
  1. Load config from orchestrator.yaml
  2. Initialize the orchestrator service (drivers, port pool, sessions)
  3. Register the API Blueprint (both new orchestrator endpoints AND
     backward-compatible /api/benchmark/<id>/start|stop endpoints)
  4. Start background daemons (timeout, health, reconciliation)
"""

import os
import logging

from .config import OrchestratorConfig
from .service import OrchestratorService

logger = logging.getLogger("s7.orchestrator.integration")

# Global orchestrator instance (accessible from other modules)
_orchestrator: OrchestratorService = None


def get_orchestrator() -> OrchestratorService:
    """Get the global orchestrator instance."""
    return _orchestrator


def init_orchestrator(app, config_path=None):
    """
    Initialize the orchestrator and register it with the Flask app.

    Args:
        app: Flask application instance
        config_path: Optional path to orchestrator.yaml.
                     If not provided, searches common locations.
    """
    global _orchestrator

    # Setup logging
    log_format = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    logging.basicConfig(format=log_format)
    orchestrator_logger = logging.getLogger("s7.orchestrator")
    orchestrator_logger.setLevel(logging.INFO)

    # Find config file
    if not config_path:
        search_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "orchestrator.yaml"),
            "/opt/strike7.ai-benchmark-harness/orchestrator.yaml",
            os.path.join(os.path.dirname(__file__), "..", "orchestrator.yaml"),
        ]
        for p in search_paths:
            if os.path.exists(p):
                config_path = p
                break

    # Load configuration
    config = OrchestratorConfig(config_path)

    # Set log level from config
    orchestrator_logger.setLevel(getattr(logging, config.log_level.upper(), logging.INFO))

    # Ensure log directory exists
    log_dir = os.path.dirname(config._config.get("log_file", ""))
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except PermissionError:
            logger.warning(f"Cannot create log directory {log_dir}, using console only")

    # Initialize orchestrator service
    _orchestrator = OrchestratorService(config)

    # Store in Flask app config for access in request handlers
    app.config["ORCHESTRATOR"] = _orchestrator
    app.config["ORCHESTRATOR_CONFIG"] = config

    # Register the API Blueprint
    from api.orchestrator_routes import orchestrator_bp
    app.register_blueprint(orchestrator_bp)

    # Start background daemons
    _orchestrator.start()

    logger.info("=" * 60)
    logger.info("Strike7 Orchestrator initialized successfully")
    logger.info(f"  Mode:     {config.mode}")
    logger.info(f"  Workers:  {len(config.workers)}")
    logger.info(f"  Ports:    {config.port_pool_start}-{config.port_pool_end}")
    logger.info(f"  DB:       {config.db_path}")
    logger.info("=" * 60)

    return _orchestrator
