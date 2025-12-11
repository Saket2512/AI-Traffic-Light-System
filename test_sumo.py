"""
Test the traffic control system without videos
Simulates vehicle counts to test the logic
"""

import sys
import time
import random
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.local_database import get_database

def simulate_traffic():
    """Simulate random vehicle counts for testing."""

    db = get_database("data")

    print("=" * 60)
    print("🚗 TRAFFIC SIMULATION TEST 🚗")
    print("=" * 60)
    print("Simulating random vehicle counts...")
    print("Press Ctrl+C to stop\n")

    lanes = ["Lane 1", "Lane 2", "Lane 3", "Lane 4"]

    try:
        while True:
            # Generate random counts (simulating real traffic)
            counts = {
                "Lane 1": random.randint(5, 25),   # Heavy traffic
                "Lane 2": random.randint(3, 15),   # Medium traffic
                "Lane 3": random.randint(1, 10),   # Light traffic
                "Lane 4": random.randint(2, 18)    # Variable traffic
            }

            # Write to database
            db.write_counts(counts)

            # Read back state
            state = db.read_state()

            if state:
                green_lane = state.get('lane_names', lanes)[state.get('green_lane_index', 0)]
                print(f"Counts: {counts}")
                print(f"Signal: {green_lane} - {state.get('current_state')} ({state.get('timer_sec', 0):.1f}s)")
                print("-" * 60)
            else:
                print("Waiting for controller to start...")

            time.sleep(2)  # Update every 2 seconds

    except KeyboardInterrupt:
        print("\n✓ Test stopped")


if __name__ == "__main__":
    print("Make sure central_controller.py is running in another terminal!")
    input("Press Enter to start simulation...")
    simulate_traffic()