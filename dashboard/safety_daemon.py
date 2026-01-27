#!/usr/bin/env python3
"""
Strike7 Safety Daemon
Background process to enforce container safety limits and automatic cleanup
"""

import time
import logging
import yaml
import os
from datetime import datetime
from api.container_manager import ContainerManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ContainerSafetyDaemon:
    """Background process to enforce safety limits on benchmark containers"""

    def __init__(self, container_manager: ContainerManager, config: dict):
        """
        Initialize safety daemon

        Args:
            container_manager: ContainerManager instance
            config: Safety configuration dictionary
        """
        self.container_manager = container_manager
        self.config = config
        self.running = False
        self.check_interval = config.get('safety', {}).get('health_check_interval', 30)

    def start(self):
        """Start the safety daemon"""
        logger.info("Starting Strike7 Container Safety Daemon")
        logger.info(f"Check interval: {self.check_interval} seconds")
        logger.info(f"Max concurrent containers: {self.container_manager.config['max_concurrent']}")
        logger.info(f"Container timeout: {self.container_manager.config['timeout_minutes']} minutes")

        self.running = True

        # Initial cleanup if enabled
        if self.config.get('safety', {}).get('enable_auto_cleanup', True):
            self._cleanup_orphaned_containers()

        # Main monitoring loop
        try:
            while self.running:
                self._check_and_enforce()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("Safety daemon stopped by user")
            self.stop()

    def stop(self):
        """Stop the safety daemon"""
        logger.info("Stopping Strike7 Container Safety Daemon")
        self.running = False

    def _check_and_enforce(self):
        """Main safety check and enforcement logic"""
        try:
            # 1. Check for containers exceeding timeout
            if self.config.get('safety', {}).get('enable_timeout_daemon', True):
                self._enforce_timeouts()

            # 2. Check concurrent container limit
            self._enforce_concurrent_limit()

            # 3. Check system resources
            self._check_system_resources()

        except Exception as e:
            logger.error(f"Error in safety check: {e}")

    def _enforce_timeouts(self):
        """Stop containers that have exceeded their timeout"""
        stopped = self.container_manager.check_timeouts()

        if stopped:
            for benchmark_id in stopped:
                logger.warning(f"Stopped {benchmark_id} - timeout exceeded")
                if self.config.get('notifications', {}).get('on_timeout', True):
                    self._notify_timeout(benchmark_id)

    def _enforce_concurrent_limit(self):
        """Enforce maximum concurrent container limit"""
        running = self.container_manager.get_running_containers()
        max_concurrent = self.container_manager.config['max_concurrent']

        if len(running) > max_concurrent:
            logger.warning(f"Container limit exceeded: {len(running)}/{max_concurrent}")

            # Stop oldest containers
            sorted_containers = sorted(
                running,
                key=lambda x: x.get('started_at', datetime.now().isoformat())
            )

            to_stop = len(running) - max_concurrent
            for container in sorted_containers[:to_stop]:
                benchmark_id = container['benchmark_id']
                logger.warning(f"Stopping {benchmark_id} - exceeded max concurrent")
                self.container_manager.stop_container(benchmark_id)

    def _check_system_resources(self):
        """Check system resources and stop containers if resources are low"""
        system = self.container_manager.get_system_status()
        max_memory = self.config.get('safety', {}).get('max_memory_total_mb', 2048)

        available_memory = system.get('available_memory_mb', 0)

        if available_memory > 0 and available_memory < 1024:
            logger.error(f"Low memory warning: {available_memory}MB available")

            # If critically low, stop all containers
            if available_memory < 512:
                logger.error("Critical memory shortage - stopping all containers")
                stopped = self.container_manager.stop_all_containers()
                logger.info(f"Emergency stopped {len(stopped)} containers")

    def _cleanup_orphaned_containers(self):
        """Clean up any orphaned Strike7 containers on startup"""
        logger.info("Checking for orphaned containers...")

        try:
            running = self.container_manager.get_running_containers()

            if running:
                logger.info(f"Found {len(running)} running Strike7 containers")
                for container in running:
                    logger.info(f"  - {container['benchmark_id']}: {container['status']}")

                # Optionally stop all on startup (configurable)
                # Disabled by default to allow resuming work
                # Uncomment to enable:
                # self.container_manager.stop_all_containers()
                # logger.info("Cleaned up all orphaned containers")
            else:
                logger.info("No orphaned containers found")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def _notify_timeout(self, benchmark_id: str):
        """Send notification about container timeout (placeholder)"""
        # This could be extended to send email, webhook, etc.
        logger.info(f"NOTIFICATION: {benchmark_id} stopped due to timeout")


def load_config():
    """Load configuration from settings.yaml"""
    config_file = os.path.join(
        os.path.dirname(__file__),
        'config',
        'settings.yaml'
    )

    try:
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not load config: {e}. Using defaults.")
        return {
            'container_management': {
                'max_concurrent': 1,
                'timeout_minutes': 30
            },
            'safety': {
                'health_check_interval': 30,
                'enable_auto_cleanup': True,
                'enable_timeout_daemon': True
            }
        }


def load_benchmarks():
    """Load benchmarks from YAML"""
    benchmarks_file = os.path.join(
        os.path.dirname(__file__),
        'config',
        'benchmarks.yaml'
    )

    try:
        with open(benchmarks_file, 'r') as f:
            data = yaml.safe_load(f)
            return data.get('benchmarks', [])
    except Exception as e:
        logger.error(f"Error loading benchmarks: {e}")
        return []


def main():
    """Main entry point for safety daemon"""
    logger.info("=" * 60)
    logger.info("Strike7 Container Safety Daemon")
    logger.info("=" * 60)

    # Load configuration
    config = load_config()
    benchmarks = load_benchmarks()

    logger.info(f"Loaded {len(benchmarks)} benchmarks")

    # Initialize container manager
    container_manager = ContainerManager(
        benchmarks,
        config=config.get('container_management', {})
    )

    # Create and start daemon
    daemon = ContainerSafetyDaemon(container_manager, config)

    try:
        daemon.start()
    except KeyboardInterrupt:
        logger.info("Daemon stopped by user")
    finally:
        daemon.stop()


if __name__ == '__main__':
    main()
