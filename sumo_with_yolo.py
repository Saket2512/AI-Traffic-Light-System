"""
🚦 COMPLETE SUMO + YOLO INTEGRATION
Runs SUMO simulation with 4 camera video feeds simultaneously
Shows real-time vehicle detection and AI traffic control
"""

import os
import sys
import time
import logging
import cv2
import numpy as np
from pathlib import Path
from threading import Thread, Lock
from ultralytics import YOLO

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Check SUMO
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    print("⚠️  SUMO_HOME not set. Running without SUMO simulation.")
    print("   Only video detection will work.")
    SUMO_AVAILABLE = False

try:
    import traci

    SUMO_AVAILABLE = True
except:
    SUMO_AVAILABLE = False
    print("⚠️  SUMO not available. Running video detection only.")

from src.traffic_logic import TrafficController

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# 🎥 VIDEO CONFIGURATION - UPDATE THESE PATHS
# =============================================================================
VIDEO_PATHS = {
    "Lane 1": r"C:\Users\sskar\PycharmProjects\AI_Traffic_Project\videos\lane1.mp4",  # North
    "Lane 2": r"C:\Users\sskar\PycharmProjects\AI_Traffic_Project\videos\lane3.mp4",  # East
    "Lane 3": r"C:\Users\sskar\Downloads\2034115-hd_1920_1080_30fps.mp4",  # South
    "Lane 4": r"C:\Users\sskar\Downloads\854745-hd_1280_720_50fps.mp4"  # West
}

VEHICLE_CLASSES = [2, 3, 5, 7]  # car, motorcycle, bus, truck
# =============================================================================

SUMO_CONFIG = project_root / 'sumo_simulation' / 'intersection.sumocfg'


class VideoDetector:
    """Processes video with YOLO detection in separate thread."""

    def __init__(self, lane_name: str, video_path: str, model: YOLO):
        self.lane_name = lane_name
        self.video_path = video_path
        self.model = model
        self.lock = Lock()

        # State
        self.current_frame = None
        self.annotated_frame = None
        self.vehicle_count = 0
        self.running = False
        self.thread = None
        self.cap = None

    def start(self) -> bool:
        """Start video processing thread."""
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            logger.error(f"Failed to open video: {self.video_path}")
            return False

        self.running = True
        self.thread = Thread(target=self._process_loop, daemon=True)
        self.thread.start()
        logger.info(f"✅ Started {self.lane_name}")
        return True

    def stop(self):
        """Stop processing thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        if self.cap:
            self.cap.release()

    def get_data(self):
        """Get current frame and count (thread-safe)."""
        with self.lock:
            return self.annotated_frame, self.vehicle_count

    def _process_loop(self):
        """Main processing loop."""
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            # Detect vehicles
            results = self.model.predict(
                frame,
                conf=0.4,
                verbose=False,
                classes=VEHICLE_CLASSES
            )

            # Get annotated frame and count
            annotated = results[0].plot()
            boxes = results[0].boxes
            count = len(boxes)

            # Update (thread-safe)
            with self.lock:
                self.annotated_frame = annotated
                self.vehicle_count = count

            time.sleep(0.03)  # ~30 FPS


class SUMOTrafficSystem:
    """Complete system with SUMO simulation and video detection."""

    def __init__(self, use_sumo=True):
        self.use_sumo = use_sumo and SUMO_AVAILABLE

        logger.info("🚀 Initializing AI Traffic Control System...")

        # Initialize YOLO
        logger.info("Loading YOLO model...")
        self.model = YOLO('yolov8n.pt')

        # Initialize traffic controller
        logger.info("Initializing traffic controller...")
        self.controller = TrafficController(
            ticks_per_second=10,
            lane_names=["Lane 1", "Lane 2", "Lane 3", "Lane 4"]
        )

        # SUMO configuration
        self.lane_edges = {
            "Lane 1": "N1J0",  # North
            "Lane 2": "E1J0",  # East
            "Lane 3": "S1J0",  # South
            "Lane 4": "W1J0"  # West
        }
        self.tls_id = "J0"

        # Initialize video detectors
        self.detectors = {}
        for lane_name, video_path in VIDEO_PATHS.items():
            if Path(video_path).exists():
                detector = VideoDetector(lane_name, video_path, self.model)
                if detector.start():
                    self.detectors[lane_name] = detector
            else:
                logger.warning(f"Video not found: {video_path}")

        if not self.detectors:
            logger.error("❌ No video detectors initialized!")
            sys.exit(1)

        logger.info("✅ Initialization complete!")

    def start_sumo(self):
        """Start SUMO simulation."""
        if not self.use_sumo:
            logger.info("Running without SUMO simulation")
            return

        if not SUMO_CONFIG.exists():
            logger.error(f"SUMO config not found: {SUMO_CONFIG}")
            self.use_sumo = False
            return

        sumo_cmd = [
            "sumo-gui",
            "-c", str(SUMO_CONFIG),
            "--start",
            "--quit-on-end",
            "--step-length", "0.1",
            "--no-warnings",
            "--time-to-teleport", "-1"
        ]

        try:
            traci.start(sumo_cmd)
            logger.info("✅ SUMO simulation started")
        except Exception as e:
            logger.error(f"Failed to start SUMO: {e}")
            self.use_sumo = False

    def get_vehicle_counts(self):
        """Get vehicle counts from video detectors."""
        counts = {}
        for lane_name in self.controller.lanes:
            if lane_name in self.detectors:
                _, count = self.detectors[lane_name].get_data()
                counts[lane_name] = count
            else:
                counts[lane_name] = 0
        return counts

    def apply_signal_to_sumo(self, state_info):
        """Apply traffic signal state to SUMO."""
        if not self.use_sumo:
            return

        state = state_info['current_state']
        green_index = state_info['green_lane_index']

        # SUMO traffic light state string (N, E, S, W)
        tl_state = ['r', 'r', 'r', 'r']

        if state == "GREEN" and 0 <= green_index < 4:
            tl_state[green_index] = 'G'
        elif state == "YELLOW" and 0 <= green_index < 4:
            tl_state[green_index] = 'y'

        state_str = ''.join(tl_state)

        try:
            traci.trafficlight.setRedYellowGreenState(self.tls_id, state_str)
        except Exception as e:
            logger.error(f"Failed to set traffic light: {e}")

    def create_display(self, vehicle_counts, state_info):
        """Create combined display with 4 videos and info panel."""

        # Get frames from detectors
        frames = []
        for lane_name in self.controller.lanes:
            if lane_name in self.detectors:
                frame, count = self.detectors[lane_name].get_data()
                if frame is not None:
                    # Resize
                    resized = cv2.resize(frame, (640, 360))

                    # Add overlay
                    overlay = resized.copy()
                    cv2.rectangle(overlay, (0, 0), (640, 80), (0, 0, 0), -1)
                    cv2.addWeighted(overlay, 0.7, resized, 0.3, 0, resized)

                    # Signal color
                    current_lane = state_info['lane_names'][state_info['green_lane_index']]
                    if lane_name == current_lane:
                        if state_info['current_state'] == "GREEN":
                            color = (0, 255, 0)
                            signal_text = "🟢 GREEN"
                        elif state_info['current_state'] == "YELLOW":
                            color = (0, 255, 255)
                            signal_text = "🟡 YELLOW"
                        else:
                            color = (0, 0, 255)
                            signal_text = "🔴 RED"
                    else:
                        color = (0, 0, 255)
                        signal_text = "🔴 RED"

                    # Draw info
                    cv2.putText(resized, lane_name, (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                    cv2.putText(resized, signal_text, (10, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    cv2.putText(resized, f"Vehicles: {count}", (450, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                    # Border
                    cv2.rectangle(resized, (0, 0), (639, 359), color, 4)

                    frames.append(resized)

        # Ensure we have 4 frames
        while len(frames) < 4:
            blank = np.zeros((360, 640, 3), dtype=np.uint8)
            frames.append(blank)

        # Arrange 2x2 grid
        top_row = np.hstack([frames[0], frames[1]])
        bottom_row = np.hstack([frames[2], frames[3]])
        video_grid = np.vstack([top_row, bottom_row])

        # Create info panel
        panel_height = 200
        panel = np.zeros((panel_height, video_grid.shape[1], 3), dtype=np.uint8)
        panel[:] = (30, 30, 30)

        # Title
        cv2.putText(panel, "AI TRAFFIC CONTROLLER", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)

        # Current state
        current_lane = state_info['lane_names'][state_info['green_lane_index']]
        state = state_info['current_state']
        timer = state_info['timer_sec']

        cv2.putText(panel, f"Active: {current_lane} - {state}", (20, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        cv2.putText(panel, f"Time: {timer:.1f}s", (20, 130),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

        # Vehicle counts
        x = 500
        cv2.putText(panel, "Vehicle Counts:", (x, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        y = 80
        for lane, count in vehicle_counts.items():
            indicator = "→" if lane == current_lane else " "
            cv2.putText(panel, f"{indicator} {lane}: {count}", (x, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            y += 30

        # Stats
        stats = self.controller.get_statistics()
        cv2.putText(panel, f"Cycles: {stats['total_cycles']}", (x + 300, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(panel, f"Served: {stats['total_vehicles_served']}", (x + 300, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # AI Logic explanation
        if state == "GREEN":
            count = vehicle_counts[current_lane]
            calc_time = min(10 + (count * 0.5), 45)
            cv2.putText(panel, f"Formula: 10 + ({count} × 0.5) = {calc_time:.1f}s",
                        (20, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 200, 255), 2)

        # Combine
        display = np.vstack([video_grid, panel])

        # Add header
        header = np.zeros((60, display.shape[1], 3), dtype=np.uint8)
        cv2.putText(header, "AI-POWERED TRAFFIC CONTROL - REAL-TIME DEMONSTRATION",
                    (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

        display = np.vstack([header, display])

        return display

    def print_decision_info(self, vehicle_counts, state_info):
        """Print detailed decision information."""
        print("\n" + "=" * 80)
        print("🧠 AI TRAFFIC CONTROLLER - DECISION ANALYSIS")
        print("=" * 80)

        current_lane = state_info['lane_names'][state_info['green_lane_index']]
        state = state_info['current_state']
        timer = state_info['timer_sec']

        print(f"\n📍 CURRENT STATE:")
        print(f"   Lane: {current_lane}")
        print(f"   Signal: {state}")
        print(f"   Time: {timer:.1f}s")

        print(f"\n🚗 VEHICLE COUNTS:")
        for lane, count in vehicle_counts.items():
            indicator = "🟢" if lane == current_lane else "  "
            print(f"   {indicator} {lane}: {count} vehicles")

        if state == "GREEN":
            count = vehicle_counts[current_lane]
            calc_time = min(10 + (count * 0.5), 45)
            print(f"\n📊 GREEN TIME CALCULATION:")
            print(f"   Formula: 10 + ({count} × 0.5) = {calc_time:.1f}s")

        stats = self.controller.get_statistics()
        print(f"\n📈 STATISTICS:")
        print(f"   Cycles: {stats['total_cycles']}")
        print(f"   Vehicles Served: {stats['total_vehicles_served']}")
        print(f"   Runtime: {stats['runtime_seconds']:.1f}s")
        print("=" * 80)

    def run(self):
        """Main loop."""
        self.start_sumo()

        print("\n" + "=" * 80)
        print("🚦 AI TRAFFIC CONTROL SYSTEM - RUNNING")
        print("=" * 80)
        print(f"Mode: {'SUMO + Video Detection' if self.use_sumo else 'Video Detection Only'}")
        print("\nControls:")
        print("  'q' - Quit")
        print("  's' - Save screenshot")
        print("  'p' - Print detailed info")
        print("=" * 80 + "\n")

        last_tick = time.time()
        last_info_print = time.time()
        screenshot_count = 0

        try:
            running = True
            while running:
                current_time = time.time()

                # Update controller
                if current_time - last_tick >= 0.1:
                    # Get counts
                    vehicle_counts = self.get_vehicle_counts()
                    counts_list = [vehicle_counts[lane] for lane in self.controller.lanes]

                    # Update controller
                    self.controller.update_vehicle_counts(counts_list)
                    self.controller.update_tick()

                    # Get state
                    state_info = self.controller.get_current_state_info()

                    # Apply to SUMO
                    if self.use_sumo:
                        self.apply_signal_to_sumo(state_info)

                        # Check if SUMO is still running
                        try:
                            if traci.simulation.getMinExpectedNumber() <= 0:
                                print("\n⚠️  SUMO simulation ended")
                                running = False
                        except:
                            pass

                    # Print info periodically
                    if current_time - last_info_print >= 10.0:
                        self.print_decision_info(vehicle_counts, state_info)
                        last_info_print = current_time

                    last_tick = current_time

                # SUMO simulation step
                if self.use_sumo:
                    try:
                        traci.simulationStep()
                    except:
                        pass

                # Create and show display
                state_info = self.controller.get_current_state_info()
                vehicle_counts = self.get_vehicle_counts()
                display = self.create_display(vehicle_counts, state_info)

                cv2.imshow("AI Traffic Control System", display)

                # Handle keyboard
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\n⏹  Stopping...")
                    break
                elif key == ord('s'):
                    screenshot_count += 1
                    filename = f"traffic_system_{screenshot_count}_{int(time.time())}.png"
                    cv2.imwrite(filename, display)
                    print(f"📸 Screenshot saved: {filename}")
                elif key == ord('p'):
                    self.print_decision_info(vehicle_counts, state_info)

                time.sleep(0.01)

        except KeyboardInterrupt:
            print("\n⏹  Interrupted by user")

        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        print("\n🧹 Cleaning up...")

        # Stop detectors
        for detector in self.detectors.values():
            detector.stop()

        # Close SUMO
        if self.use_sumo:
            try:
                traci.close()
                print("✅ SUMO closed")
            except:
                pass

        cv2.destroyAllWindows()

        # Print final stats
        print("\n" + "=" * 80)
        print("📊 FINAL STATISTICS")
        print("=" * 80)
        stats = self.controller.get_statistics()
        print(f"Total Cycles: {stats['total_cycles']}")
        print(f"Vehicles Served: {stats['total_vehicles_served']}")
        print(f"Runtime: {stats['runtime_seconds']:.1f}s")
        print("\nGreen Time Distribution:")
        for lane, time_sec in stats['lane_green_times'].items():
            print(f"  {lane}: {time_sec:.1f}s")
        print("=" * 80)
        print("\n✅ System stopped successfully!")


def main():
    """Entry point."""

    print("\n" + "=" * 80)
    print("🚦 AI TRAFFIC CONTROL SYSTEM")
    print("   SUMO Simulation + Real-Time Video Detection")
    print("=" * 80)
    print("\nThis system will:")
    print("  1. Show 4 video feeds with YOLO vehicle detection")
    print("  2. Run AI traffic controller with Max Pressure algorithm")
    if SUMO_AVAILABLE:
        print("  3. Control SUMO traffic simulation in real-time")
    else:
        print("  3. Run without SUMO (video detection only)")
    print("\n" + "=" * 80)

    # Check videos
    missing = []
    for lane, path in VIDEO_PATHS.items():
        if not Path(path).exists():
            missing.append(f"  {lane}: {path}")

    if missing:
        print("\n⚠️  WARNING: Some videos not found:")
        for msg in missing:
            print(msg)
        print("\n💡 Update VIDEO_PATHS in this file (line 34)")

        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            return

    # Ask about SUMO
    use_sumo = SUMO_AVAILABLE
    if SUMO_AVAILABLE:
        response = input("\nRun with SUMO simulation? (y/n, default=y): ")
        use_sumo = response.lower() != 'n'

    # Run system
    system = SUMOTrafficSystem(use_sumo=use_sumo)
    system.run()


if __name__ == "__main__":
    main()