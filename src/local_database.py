"""
Local Database - File-based communication system
Replaces Firebase with simple JSON file storage
"""

import json
import time
import threading
from pathlib import Path
from typing import Dict, Callable, Optional
import logging

logger = logging.getLogger(__name__)


class LocalDatabase:
    """
    Simple file-based database using JSON for inter-process communication.
    Thread-safe with file locking.
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.lock = threading.Lock()

        # File paths
        self.counts_file = self.data_dir / "lane_counts.json"
        self.state_file = self.data_dir / "signal_state.json"

        # Initialize files if they don't exist
        self._initialize_files()

    def _initialize_files(self):
        """Create initial data files."""
        if not self.counts_file.exists():
            self.write_counts({
                "Lane 1": 0,
                "Lane 2": 0,
                "Lane 3": 0,
                "Lane 4": 0
            })

        if not self.state_file.exists():
            self.write_state({
                "green_lane_index": 0,
                "current_state": "GREEN",
                "timer_sec": 10.0,
                "lane_names": ["Lane 1", "Lane 2", "Lane 3", "Lane 4"],
                "vehicle_counts": [0, 0, 0, 0],
                "total_cycles": 0,
                "timestamp": time.time()
            })

    def write_counts(self, counts: Dict[str, int]) -> bool:
        """Write vehicle counts to file."""
        try:
            with self.lock:
                data = counts.copy()
                data["timestamp"] = time.time()

                with open(self.counts_file, 'w') as f:
                    json.dump(data, f, indent=2)
                return True
        except Exception as e:
            logger.error(f"Failed to write counts: {e}")
            return False

    def read_counts(self) -> Optional[Dict[str, int]]:
        """Read vehicle counts from file."""
        try:
            with self.lock:
                if not self.counts_file.exists():
                    return None

                with open(self.counts_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read counts: {e}")
            return None

    def update_lane_count(self, lane_name: str, count: int) -> bool:
        """Update count for a specific lane."""
        try:
            with self.lock:
                # Read current data
                if self.counts_file.exists():
                    with open(self.counts_file, 'r') as f:
                        data = json.load(f)
                else:
                    data = {}

                # Update specific lane
                data[lane_name] = count
                data["timestamp"] = time.time()

                # Write back
                with open(self.counts_file, 'w') as f:
                    json.dump(data, f, indent=2)
                return True
        except Exception as e:
            logger.error(f"Failed to update lane count: {e}")
            return False

    def write_state(self, state: Dict) -> bool:
        """Write signal state to file."""
        try:
            with self.lock:
                state["timestamp"] = time.time()

                with open(self.state_file, 'w') as f:
                    json.dump(state, f, indent=2)
                return True
        except Exception as e:
            logger.error(f"Failed to write state: {e}")
            return False

    def read_state(self) -> Optional[Dict]:
        """Read signal state from file."""
        try:
            with self.lock:
                if not self.state_file.exists():
                    return None

                with open(self.state_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read state: {e}")
            return None


class StateWatcher:
    """
    Watches for changes in state file and triggers callbacks.
    Simulates Firebase's on_snapshot functionality.
    """

    def __init__(self, file_path: Path, callback: Callable, check_interval: float = 0.1):
        self.file_path = file_path
        self.callback = callback
        self.check_interval = check_interval
        self.last_modified = 0
        self.running = False
        self.thread = None

    def start(self):
        """Start watching the file."""
        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop watching the file."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def _watch_loop(self):
        """Internal loop that checks for file changes."""
        while self.running:
            try:
                if self.file_path.exists():
                    current_modified = self.file_path.stat().st_mtime

                    if current_modified != self.last_modified:
                        self.last_modified = current_modified

                        # Read file and trigger callback
                        with open(self.file_path, 'r') as f:
                            data = json.load(f)

                        # Call the callback with the data
                        self.callback(data)

                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error in watch loop: {e}")
                time.sleep(1.0)


# Singleton instance
_db_instance = None
_db_lock = threading.Lock()


def get_database(data_dir: str = "data") -> LocalDatabase:
    """Get or create the database instance."""
    global _db_instance

    if _db_instance is None:
        with _db_lock:
            if _db_instance is None:
                _db_instance = LocalDatabase(Path(data_dir))

    return _db_instance