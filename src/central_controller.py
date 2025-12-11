"""
Central Controller - Main Coordinator (No Firebase)
Uses local file-based communication instead of Firebase
"""

import time
import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.traffic_logic import TrafficController
from src.local_database import get_database, StateWatcher

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/controller.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Configuration ---
LANE_NAMES = ["Lane 1", "Lane 2", "Lane 3", "Lane 4"]
TICKS_PER_SECOND = 10
TICK_RATE_SEC = 1.0 / TICKS_PER_SECOND
DATA_DIR = project_root / "data"


class CentralController:
    """Main controller coordinating all system components."""

    def __init__(self):
        self.db = None
        self.controller = None
        self.counts_watcher = None
        self.initialize_database()
        self.initialize_controller()

    def initialize_database(self):
        """Initialize local database."""
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            self.db = get_database(DATA_DIR)
            logger.info("✓ Local database initialized")

        except Exception as e:
            logger.error(f"✗ Database initialization failed: {e}")
            sys.exit(1)

    def initialize_controller(self):
        """Initialize the traffic logic controller."""
        self.controller = TrafficController(
            ticks_per_second=TICKS_PER_SECOND,
            lane_names=LANE_NAMES
        )
        logger.info("✓ Traffic Controller initialized")

    def on_counts_update(self, data: dict):
        """
        Callback when vehicle counts are updated.

        Args:
            data: Dictionary containing lane counts
        """
        try:
            # Extract counts in correct order
            counts = [
                data.get(LANE_NAMES[0], 0),
                data.get(LANE_NAMES[1], 0),
                data.get(LANE_NAMES[2], 0),
                data.get(LANE_NAMES[3], 0)
            ]

            # Update controller
            self.controller.update_vehicle_counts(counts)

            logger.debug(f"Received counts: {dict(zip(LANE_NAMES, counts))}")

        except Exception as e:
            logger.error(f"Error processing count update: {e}")

    def run(self):
        """Main control loop."""

        # Start watching for count updates
        counts_file = DATA_DIR / "lane_counts.json"
        self.counts_watcher = StateWatcher(
            counts_file,
            self.on_counts_update,
            check_interval=0.1
        )
        self.counts_watcher.start()

        logger.info("=" * 60)
        logger.info("🚦 CENTRAL TRAFFIC CONTROLLER STARTED 🚦")
        logger.info("=" * 60)
        logger.info(f"Monitoring {len(LANE_NAMES)} lanes")
        logger.info(f"Tick rate: {TICKS_PER_SECOND} ticks/second")
        logger.info(f"Data directory: {DATA_DIR}")
        logger.info(f"Press Ctrl+C to stop")
        logger.info("=" * 60)

        # Write initial state
        initial_state = self.controller.get_current_state_info()
        self.db.write_state(initial_state)

        try:
            tick_count = 0
            last_stats_time = time.time()

            while True:
                # Run one controller tick
                state_changed = self.controller.update_tick()

                # Update database if state changed
                if state_changed:
                    current_state = self.controller.get_current_state_info()
                    self.db.write_state(current_state)
                    logger.debug(f"Updated state: {current_state['current_state']}")

                # Print statistics every 30 seconds
                tick_count += 1
                current_time = time.time()
                if current_time - last_stats_time >= 30:
                    stats = self.controller.get_statistics()
                    logger.info("--- Statistics ---")
                    logger.info(f"Total cycles: {stats['total_cycles']}")
                    logger.info(f"Current counts: {stats['current_counts']}")
                    last_stats_time = current_time

                # Sleep until next tick
                time.sleep(TICK_RATE_SEC)

        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        """Gracefully shutdown the controller."""
        logger.info("\n" + "=" * 60)
        logger.info("🛑 Shutting down controller...")

        if self.counts_watcher:
            self.counts_watcher.stop()
            logger.info("✓ Stopped count watcher")

        # Print final statistics
        stats = self.controller.get_statistics()
        logger.info("\n--- Final Statistics ---")
        logger.info(f"Total cycles completed: {stats['total_cycles']}")
        logger.info("Green time per lane:")
        for lane, time_sec in stats['lane_green_times'].items():
            logger.info(f"  {lane}: {time_sec:.1f}s")

        logger.info("=" * 60)
        logger.info("Controller stopped successfully")


def main():
    """Entry point for the central controller."""

    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    # Initialize and run controller
    controller = CentralController()
    controller.run()


if __name__ == "__main__":
    main()