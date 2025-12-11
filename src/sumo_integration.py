"""
SUMO Integration - Traffic Simulation (No Firebase)
Simulates 4-lane intersection with AI traffic light control
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Check if SUMO_HOME is set
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please set SUMO_HOME environment variable")

import traci
import sumolib
from src.local_database import get_database, StateWatcher

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sumo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
DATA_DIR = project_root / 'data'
SUMO_CONFIG = project_root / 'sumo_simulation' / 'intersection.sumocfg'


class SUMOTrafficSimulation:
    """SUMO traffic simulation with AI control integration."""

    def __init__(self, gui=True):
        self.gui = gui
        self.db = None
        self.current_signal_state = {}
        self.state_watcher = None

        # Lane detector IDs (SUMO edge IDs) - MUST MATCH YOUR NETWORK
        self.lane_edges = {
            "Lane 1": "N1J0",  # North approach
            "Lane 2": "E1J0",  # East approach
            "Lane 3": "S1J0",  # South approach
            "Lane 4": "W1J0"   # West approach
        }

        # Traffic light ID in SUMO
        self.tls_id = "J0"

        self.initialize_database()

    def initialize_database(self):
        """Initialize local database connection."""
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            self.db = get_database(DATA_DIR)

            # Start watching for state updates
            state_file = DATA_DIR / "signal_state.json"
            self.state_watcher = StateWatcher(
                state_file,
                self.on_state_update,
                check_interval=0.1
            )
            self.state_watcher.start()

            logger.info("✓ Database initialized")

        except Exception as e:
            logger.error(f"✗ Database initialization failed: {e}")
            sys.exit(1)

    def on_state_update(self, data: dict):
        """Callback when signal state is updated."""
        try:
            self.current_signal_state = data
            logger.debug(f"State updated: {data.get('current_state')}")
        except Exception as e:
            logger.error(f"Error processing state update: {e}")

    def start_sumo(self):
        """Start SUMO simulation."""

        if not SUMO_CONFIG.exists():
            logger.error(f"SUMO config not found: {SUMO_CONFIG}")
            logger.error("Please create SUMO simulation files first")
            sys.exit(1)

        sumo_binary = "sumo-gui" if self.gui else "sumo"
        sumo_cmd = [
            sumo_binary,
            "-c", str(SUMO_CONFIG),
            "--start",
            "--quit-on-end",
            "--step-length", "0.1",
            "--no-warnings"
        ]

        try:
            traci.start(sumo_cmd)
            logger.info("✓ SUMO simulation started")
        except Exception as e:
            logger.error(f"✗ Failed to start SUMO: {e}")
            sys.exit(1)

    def count_vehicles_on_lane(self, edge_id):
        """Count vehicles on a specific edge/lane."""
        try:
            # Get all vehicles on this edge
            vehicle_ids = traci.edge.getLastStepVehicleIDs(edge_id)
            return len(vehicle_ids)
        except:
            return 0

    def update_vehicle_counts(self):
        """Count vehicles on all lanes and update database."""
        counts = {}

        for lane_name, edge_id in self.lane_edges.items():
            count = self.count_vehicles_on_lane(edge_id)
            counts[lane_name] = count

        # Update database
        try:
            self.db.write_counts(counts)
            logger.debug(f"Updated counts: {counts}")
        except Exception as e:
            logger.error(f"Database update failed: {e}")

        return counts

    def apply_signal_state(self):
        """Apply current signal state to SUMO traffic lights."""

        if not self.current_signal_state:
            return

        state = self.current_signal_state.get("current_state", "RED")
        green_index = self.current_signal_state.get("green_lane_index", -1)

        # SUMO traffic light state string for 4 connections (N, E, S, W)
        # Each character controls one approach: r=red, y=yellow, G=green

        if state == "GREEN":
            # Set green for current lane, red for others
            tl_state = ["r", "r", "r", "r"]
            if 0 <= green_index < 4:
                tl_state[green_index] = "G"
            state_str = "".join(tl_state)

        elif state == "YELLOW":
            # Yellow for current green lane
            tl_state = ["r", "r", "r", "r"]
            if 0 <= green_index < 4:
                tl_state[green_index] = "y"
            state_str = "".join(tl_state)

        else:  # ALL_RED
            state_str = "rrrr"

        try:
            traci.trafficlight.setRedYellowGreenState(self.tls_id, state_str)
        except Exception as e:
            logger.error(f"Failed to set traffic light: {e}")

    def run(self):
        """Main simulation loop."""

        self.start_sumo()

        logger.info("=" * 60)
        logger.info("🚦 SUMO TRAFFIC SIMULATION RUNNING 🚦")
        logger.info("=" * 60)

        step = 0
        last_count_update = 0
        count_interval = 1.0  # Update counts every 1 second

        try:
            while traci.simulation.getMinExpectedNumber() > 0:
                traci.simulationStep()
                step += 1

                current_time = traci.simulation.getTime()

                # Update vehicle counts periodically
                if current_time - last_count_update >= count_interval:
                    counts = self.update_vehicle_counts()
                    last_count_update = current_time

                    if step % 100 == 0:  # Log every 100 steps
                        logger.info(f"Time: {current_time:.1f}s | Counts: {counts}")

                # Apply AI controller's signal state
                self.apply_signal_state()

                time.sleep(0.01)  # Small delay for real-time visualization

        except traci.exceptions.FatalTraCIError:
            logger.info("Simulation ended")
        except KeyboardInterrupt:
            logger.info("\nStopping simulation...")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        traci.close()

        if self.state_watcher:
            self.state_watcher.stop()

        logger.info("✓ SUMO simulation stopped")


def main():
    """Entry point for SUMO simulation."""

    # Create logs directory
    os.makedirs('logs', exist_ok=True)

    # Create simulation (with GUI)
    sim = SUMOTrafficSimulation(gui=True)
    sim.run()


if __name__ == "__main__":
    main()