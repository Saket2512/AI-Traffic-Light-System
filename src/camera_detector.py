"""
Camera Detector - Vehicle Detection and Counting
Uses YOLOv8 for real-time vehicle detection and Firebase for communication
"""

import cv2
import time
import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import firebase_admin
from firebase_admin import credentials, firestore
from ultralytics import YOLO

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# ⚠️ CONFIGURATION - EDIT THIS FOR EACH CAMERA INSTANCE ⚠️
# =============================================================================
MY_LANE_NAME = "Lane 1"  # Change to: "Lane 1", "Lane 2", "Lane 3", or "Lane 4"
VIDEO_SOURCE = str(project_root / "videos" / "lane1.mp4")  # Path to video file
# For webcam, use: VIDEO_SOURCE = 0
# =============================================================================

# Paths
SERVICE_ACCOUNT_PATH = project_root / 'config' / 'serviceAccountKey.json'
MODEL_PATH = project_root / 'models' / 'yolov8n.pt'


class CameraDetector:
    """Vehicle detection and counting system for one lane."""

    def __init__(self, lane_name: str, video_source: str):
        self.lane_name = lane_name
        self.video_source = video_source
        self.db = None
        self.model = None
        self.current_signal_state = {}
        self.state_watch = None

        self.initialize_firebase()
        self.initialize_model()

    def initialize_firebase(self):
        """Initialize Firebase connection."""
        try:
            if not SERVICE_ACCOUNT_PATH.exists():
                raise FileNotFoundError(
                    f"Firebase key not found at {SERVICE_ACCOUNT_PATH}"
                )

            cred = credentials.Certificate(str(SERVICE_ACCOUNT_PATH))

            # Initialize only if not already initialized
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)

            self.db = firestore.client()

            # Document references
            self.counts_doc_ref = self.db.collection('traffic-data').document('lane-counts')
            self.state_doc_ref = self.db.collection('traffic-data').document('signal-state')

            # Start listener for signal state
            self.state_watch = self.state_doc_ref.on_snapshot(self.on_state_snapshot)

            logger.info(f"✓ Firebase initialized for {self.lane_name}")

        except Exception as e:
            logger.error(f"✗ Firebase initialization failed: {e}")
            sys.exit(1)

    def initialize_model(self):
        """Initialize YOLO model."""
        try:
            # Download model if not exists
            if not MODEL_PATH.exists():
                os.makedirs(MODEL_PATH.parent, exist_ok=True)
                logger.info("Downloading YOLOv8 model...")

            self.model = YOLO(str(MODEL_PATH))
            logger.info(f"✓ YOLO model loaded for {self.lane_name}")

        except Exception as e:
            logger.error(f"✗ Model loading failed: {e}")
            sys.exit(1)

    def on_state_snapshot(self, doc_snapshot, changes, read_time):
        """Listener callback for signal state updates."""
        try:
            if doc_snapshot:
                self.current_signal_state = doc_snapshot[0].to_dict()
                logger.debug(f"State updated: {self.current_signal_state.get('current_state')}")
        except Exception as e:
            logger.error(f"Error in state listener: {e}")

    def get_signal_info(self):
        """Get current signal information for this lane."""

        # Find my lane index
        my_lane_index = -1
        if "lane_names" in self.current_signal_state:
            if self.lane_name in self.current_signal_state["lane_names"]:
                my_lane_index = self.current_signal_state["lane_names"].index(self.lane_name)

        # Determine signal color and timer
        color = (0, 0, 255)  # Default: Red (BGR format)
        timer = 0
        state_text = "RED"

        if self.current_signal_state:
            state = self.current_signal_state.get("current_state", "RED")
            green_index = self.current_signal_state.get("green_lane_index", -1)
            timer = self.current_signal_state.get("timer_sec", 0)

            if my_lane_index == green_index:
                if state == "GREEN":
                    color = (0, 255, 0)  # Green
                    state_text = "GREEN"
                elif state == "YELLOW":
                    color = (0, 255, 255)  # Yellow
                    state_text = "YELLOW"
            else:
                state_text = "RED"

        return color, timer, state_text

    def draw_ui(self, frame, vehicle_count):
        """Draw UI elements on the frame."""

        h, w = frame.shape[:2]
        color, timer, state_text = self.get_signal_info()

        # Draw semi-transparent background for signal
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (180, 130), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Draw signal light
        cv2.circle(frame, (90, 60), 45, color, -1)
        cv2.circle(frame, (90, 60), 45, (255, 255, 255), 3)

        # Draw signal label
        cv2.putText(frame, state_text, (50, 115),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Draw timer
        timer_text = f"{timer:.1f}s"
        cv2.putText(frame, timer_text, (200, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255, 255, 255), 4)
        cv2.putText(frame, timer_text, (200, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.8, color, 2)

        # Draw lane info at bottom
        info_text = f"{self.lane_name}: {vehicle_count} vehicles"
        (text_w, text_h), _ = cv2.getTextSize(info_text,
                                              cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)

        # Draw background for text
        cv2.rectangle(frame, (10, h - text_h - 30),
                      (20 + text_w, h - 10), (0, 0, 0), -1)

        # Draw text
        cv2.putText(frame, info_text, (15, h - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

        # Draw FPS
        fps_text = f"FPS: {cv2.getTickFrequency() / (cv2.getTickCount()):.1f}"
        cv2.putText(frame, fps_text, (w - 200, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    def run(self):
        """Main detection loop."""

        # Open video source
        cap = cv2.VideoCapture(self.video_source)

        if not cap.isOpened():
            logger.error(f"✗ Could not open video source: {self.video_source}")
            return

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        logger.info(f"✓ Video opened: {self.video_source}")
        logger.info(f"  Resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
        logger.info(f"  FPS: {fps}")

        logger.info("=" * 60)
        logger.info(f"🎥 {self.lane_name} DETECTOR RUNNING 🎥")
        logger.info(f"Press 'q' to quit")
        logger.info("=" * 60)

        last_update_time = 0
        update_interval = 1.0  # Update Firestore every 1 second
        frame_count = 0

        try:
            while cap.isOpened():
                success, frame = cap.read()

                if not success:
                    logger.info("Video ended. Looping...")
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue

                frame_count += 1

                # Run YOLO detection
                # Classes: 2=car, 5=bus, 7=truck
                results = self.model.predict(
                    frame,
                    classes=[2, 5, 7],
                    verbose=False,
                    conf=0.3  # Confidence threshold
                )

                # Get vehicle count
                vehicle_count = len(results[0].boxes)

                # Get annotated frame
                annotated_frame = results[0].plot()

                # Draw custom UI
                self.draw_ui(annotated_frame, vehicle_count)

                # Display frame
                cv2.imshow(f"Traffic Detector - {self.lane_name}", annotated_frame)

                # Update Firestore periodically
                current_time = time.time()
                if (current_time - last_update_time) >= update_interval:
                    try:
                        self.counts_doc_ref.update({self.lane_name: vehicle_count})
                        logger.debug(f"Sent count to Firestore: {vehicle_count}")
                        last_update_time = current_time
                    except Exception as e:
                        logger.error(f"Firestore update failed: {e}")

                # Check for quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except KeyboardInterrupt:
            logger.info("\nStopping detector...")

        finally:
            self.cleanup(cap)

    def cleanup(self, cap):
        """Clean up resources."""
        cap.release()
        cv2.destroyAllWindows()

        if self.state_watch:
            self.state_watch.unsubscribe()

        logger.info(f"✓ {self.lane_name} detector stopped")


def main():
    """Entry point for camera detector."""

    # Validate configuration
    if MY_LANE_NAME not in ["Lane 1", "Lane 2", "Lane 3", "Lane 4"]:
        logger.error(f"Invalid lane name: {MY_LANE_NAME}")
        logger.error("Must be one of: Lane 1, Lane 2, Lane 3, Lane 4")
        sys.exit(1)

    # Check video file exists
    if isinstance(VIDEO_SOURCE, str) and not Path(VIDEO_SOURCE).exists():
        logger.error(f"Video file not found: {VIDEO_SOURCE}")
        logger.error(f"Please place video in: {project_root / 'videos'}")
        sys.exit(1)

    # Create and run detector
    detector = CameraDetector(MY_LANE_NAME, VIDEO_SOURCE)
    detector.run()


if __name__ == "__main__":
    main()