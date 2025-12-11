"""
🎯 PROFESSIONAL PRESENTATION MODE
Complete AI Traffic Control System Demonstration
Perfect for project presentations and demonstrations
"""

import cv2
import numpy as np
import sys
import time
import logging
from pathlib import Path
from threading import Thread, Lock
from ultralytics import YOLO

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import project modules
from src.traffic_logic import TrafficController
from src.config import (TrafficConfig, DetectionConfig, VisualizationConfig,
                        VIDEO_SOURCES, PresentationConfig)
from utils.visualizer import TrafficVisualizer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoProcessor:
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
        logger.info(f"✅ Started processing {self.lane_name}")
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
                conf=DetectionConfig.CONFIDENCE_THRESHOLD,
                verbose=False,
                classes=DetectionConfig.VEHICLE_CLASSES
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


class PresentationDemo:
    """Complete presentation demo with all features."""

    def __init__(self):
        logger.info("🚀 Initializing Presentation Demo...")

        # Initialize YOLO
        logger.info("Loading YOLO model...")
        self.model = YOLO(str(DetectionConfig.MODEL_PATH))

        # Initialize traffic controller
        logger.info("Initializing traffic controller...")
        self.controller = TrafficController(
            base_green_sec=TrafficConfig.BASE_GREEN_TIME,
            max_green_sec=TrafficConfig.MAX_GREEN_TIME,
            per_vehicle_time=TrafficConfig.TIME_PER_VEHICLE,
            density_threshold=TrafficConfig.DENSITY_THRESHOLD,
            yellow_sec=TrafficConfig.YELLOW_TIME,
            all_red_sec=TrafficConfig.ALL_RED_TIME,
            ticks_per_second=TrafficConfig.TICKS_PER_SECOND,
            lane_names=TrafficConfig.LANE_NAMES
        )

        # Initialize visualizer
        self.visualizer = TrafficVisualizer()

        # Initialize video processors
        self.processors = {}
        for lane_name, video_path in VIDEO_SOURCES.items():
            if isinstance(video_path, str) and Path(video_path).exists():
                processor = VideoProcessor(lane_name, video_path, self.model)
                if processor.start():
                    self.processors[lane_name] = processor
            else:
                logger.warning(f"Video not found for {lane_name}: {video_path}")

        if not self.processors:
            logger.error("❌ No video processors initialized!")
            sys.exit(1)

        # Timing
        self.last_tick = time.time()
        self.last_info_print = time.time()
        self.screenshot_counter = 0

        logger.info("✅ Initialization complete!")

    def get_vehicle_counts(self) -> dict:
        """Get current vehicle counts from all lanes."""
        counts = {}
        for lane_name in TrafficConfig.LANE_NAMES:
            if lane_name in self.processors:
                _, count = self.processors[lane_name].get_data()
                counts[lane_name] = count
            else:
                counts[lane_name] = 0
        return counts

    def get_signal_info(self, lane_name: str, state_info: dict):
        """Get signal color and state for a specific lane."""
        lane_index = TrafficConfig.LANE_NAMES.index(lane_name)
        green_index = state_info['green_lane_index']
        state = state_info['current_state']
        timer = state_info['timer_sec']

        if lane_index == green_index:
            if state == "GREEN":
                return self.visualizer.COLORS['green'], "GREEN", timer
            elif state == "YELLOW":
                return self.visualizer.COLORS['yellow'], "YELLOW", timer

        return self.visualizer.COLORS['red'], "RED", timer

    def create_main_display(self, vehicle_counts: dict, state_info: dict) -> np.ndarray:
        """Create the main display with all lanes and info panels."""

        # Get lane views
        lane_views = []
        for lane_name in TrafficConfig.LANE_NAMES:
            if lane_name in self.processors:
                frame, count = self.processors[lane_name].get_data()
                if frame is not None:
                    color, state_text, timer = self.get_signal_info(lane_name, state_info)

                    lane_view = self.visualizer.create_lane_view(
                        frame, lane_name, count, color, state_text, timer,
                        (VisualizationConfig.LANE_VIEW_WIDTH,
                         VisualizationConfig.LANE_VIEW_HEIGHT)
                    )
                    lane_views.append(lane_view)

        if len(lane_views) < 4:
            # Fill missing lanes with blank
            blank = np.zeros((VisualizationConfig.LANE_VIEW_HEIGHT,
                              VisualizationConfig.LANE_VIEW_WIDTH, 3), dtype=np.uint8)
            while len(lane_views) < 4:
                lane_views.append(blank)

        # Arrange lanes in 2x2 grid
        top_row = np.hstack([lane_views[0], lane_views[1]])
        bottom_row = np.hstack([lane_views[2], lane_views[3]])
        lanes_grid = np.vstack([top_row, bottom_row])

        grid_width = lanes_grid.shape[1]

        # Create info panels
        # Left: AI Logic panel
        ai_info = {
            "Algorithm": "Max Pressure",
            "Base Green": f"{TrafficConfig.BASE_GREEN_TIME}s",
            "Max Green": f"{TrafficConfig.MAX_GREEN_TIME}s",
            "Time/Vehicle": f"{TrafficConfig.TIME_PER_VEHICLE}s",
            "Yellow": f"{TrafficConfig.YELLOW_TIME}s",
            "All Red": f"{TrafficConfig.ALL_RED_TIME}s"
        }
        ai_panel = self.visualizer.create_info_panel(
            grid_width // 2, 250, "AI TRAFFIC LOGIC", ai_info
        )

        # Right: Current state panel
        current_lane = state_info['lane_names'][state_info['green_lane_index']]
        state_info_dict = {
            "Active Lane": current_lane,
            "Signal State": state_info['current_state'],
            "Time Remaining": f"{state_info['timer_sec']:.1f}s",
            "Total Cycles": state_info['total_cycles']
        }
        state_panel = self.visualizer.create_info_panel(
            grid_width // 2, 250, "CURRENT STATE", state_info_dict,
            highlight_keys=["Active Lane", "Signal State"]
        )

        info_row1 = np.hstack([ai_panel, state_panel])

        # Bottom panels
        # Left: Intersection diagram
        intersection = self.visualizer.create_intersection_diagram(
            400,
            vehicle_counts,
            TrafficConfig.LANE_NAMES,
            state_info['green_lane_index'],
            state_info['current_state']
        )
        intersection = cv2.resize(intersection, (grid_width // 2, 250))

        # Right: Statistics
        stats = self.controller.get_statistics()
        stats_panel = self.visualizer.create_statistics_panel(
            grid_width // 2, 250, stats
        )

        info_row2 = np.hstack([intersection, stats_panel])

        # Combine all
        display = np.vstack([lanes_grid, info_row1, info_row2])

        # Add title bar
        title_bar = np.zeros((70, display.shape[1], 3), dtype=np.uint8)
        title_bar[:] = (0, 0, 0)

        cv2.putText(title_bar,
                    "AI-POWERED REAL-TIME TRAFFIC LIGHT CONTROL SYSTEM",
                    (30, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 255), 3)

        display = np.vstack([title_bar, display])

        return display

    def print_decision_info(self, vehicle_counts: dict, state_info: dict):
        """Print detailed decision information to console."""
        if not PresentationConfig.VERBOSE_DECISIONS:
            return

        print("\n" + "=" * 80)
        print("🧠 AI TRAFFIC CONTROLLER - DECISION ANALYSIS")
        print("=" * 80)

        current_lane = state_info['lane_names'][state_info['green_lane_index']]

        print(f"\n📍 CURRENT STATE:")
        print(f"   Lane: {current_lane}")
        print(f"   Signal: {state_info['current_state']}")
        print(f"   Time: {state_info['timer_sec']:.1f}s remaining")
        print(f"   Cycle: #{state_info['total_cycles']}")

        print(f"\n🚗 VEHICLE COUNTS:")
        for lane, count in vehicle_counts.items():
            indicator = "🟢" if lane == current_lane else "  "
            print(f"   {indicator} {lane}: {count:2d} vehicles")

        print(f"\n🤖 AI LOGIC EXPLANATION:")
        explanation = TrafficConfig.get_explanation()
        for key, value in explanation.items():
            print(f"   {key}: {value}")

        if state_info['current_state'] == "GREEN":
            count = vehicle_counts[current_lane]
            if count < TrafficConfig.DENSITY_THRESHOLD:
                calc_time = TrafficConfig.BASE_GREEN_TIME
                formula = f"Low density, using base time"
            else:
                calc_time = min(
                    TrafficConfig.BASE_GREEN_TIME + (count * TrafficConfig.TIME_PER_VEHICLE),
                    TrafficConfig.MAX_GREEN_TIME
                )
                formula = f"{TrafficConfig.BASE_GREEN_TIME} + ({count} × {TrafficConfig.TIME_PER_VEHICLE}) = {calc_time:.1f}s"

            print(f"\n📊 GREEN TIME CALCULATION:")
            print(f"   Formula: {formula}")
            print(f"   Result: {calc_time:.1f}s")

        stats = self.controller.get_statistics()
        print(f"\n📈 PERFORMANCE:")
        print(f"   Runtime: {stats['runtime_seconds']:.1f}s")
        print(f"   Vehicles Served: {stats['total_vehicles_served']}")
        print(f"   Avg per Cycle: {stats['avg_vehicles_per_cycle']:.1f}")

        print("=" * 80)

    def run(self):
        """Main presentation loop."""
        print("\n" + "=" * 80)
        print("🎯 AI TRAFFIC CONTROL SYSTEM - PRESENTATION MODE")
        print("=" * 80)
        print("\n🎮 CONTROLS:")
        print("   'q' - Quit")
        print("   's' - Save screenshot")
        print("   'p' - Print detailed status")
        print("   'i' - Toggle info printing")
        print("\n" + "=" * 80)

        show_info = True

        try:
            while True:
                current_time = time.time()

                # Update controller
                if current_time - self.last_tick >= (1.0 / TrafficConfig.TICKS_PER_SECOND):
                    # Get counts
                    vehicle_counts = self.get_vehicle_counts()
                    counts_list = [vehicle_counts[lane] for lane in TrafficConfig.LANE_NAMES]

                    # Update controller
                    self.controller.update_vehicle_counts(counts_list)
                    state_changed = self.controller.update_tick()

                    # Print info periodically
                    if show_info and current_time - self.last_info_print >= VisualizationConfig.INFO_UPDATE_INTERVAL:
                        state_info = self.controller.get_current_state_info()
                        self.print_decision_info(vehicle_counts, state_info)
                        self.last_info_print = current_time

                    self.last_tick = current_time

                # Get current state
                state_info = self.controller.get_current_state_info()
                vehicle_counts = self.get_vehicle_counts()

                # Create display
                display = self.create_main_display(vehicle_counts, state_info)

                # Show display
                cv2.imshow("AI Traffic Control - Presentation Mode", display)

                # Handle input
                key = cv2.waitKey(1) & 0xFF

                if key == ord('q'):
                    print("\n⏹  Stopping presentation...")
                    break
                elif key == ord('s'):
                    self.screenshot_counter += 1
                    filename = f"traffic_screenshot_{self.screenshot_counter}_{int(time.time())}.png"
                    cv2.imwrite(filename, display)
                    print(f"📸 Screenshot saved: {filename}")
                elif key == ord('p'):
                    self.controller.print_detailed_status()
                elif key == ord('i'):
                    show_info = not show_info
                    status = "enabled" if show_info else "disabled"
                    print(f"ℹ️  Info printing {status}")

        except KeyboardInterrupt:
            print("\n⏹  Interrupted by user")

        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up...")

        # Stop video processors
        for processor in self.processors.values():
            processor.stop()

        cv2.destroyAllWindows()

        # Print final statistics
        print("\n" + "=" * 80)
        print("📊 FINAL PRESENTATION STATISTICS")
        print("=" * 80)
        self.controller.print_detailed_status()
        print("\n✅ Presentation demo ended successfully!")


def main():
    """Entry point for presentation mode."""

    print("\n" + "=" * 80)
    print("🎯 AI TRAFFIC CONTROL SYSTEM")
    print("   Professional Presentation Mode")
    print("=" * 80)

    # Check video availability
    missing = []
    for lane, path in VIDEO_SOURCES.items():
        if isinstance(path, str) and not Path(path).exists():
            missing.append(f"{lane}: {path}")

    if missing:
        print("\n⚠️  WARNING: Some video files not found:")
        for msg in missing:
            print(f"  - {msg}")
        print("\nPlease update VIDEO_SOURCES in src/config.py")

        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            return

    # Run demo
    demo = PresentationDemo()
    demo.run()


if __name__ == "__main__":
    main()