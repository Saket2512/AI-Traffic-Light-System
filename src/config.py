"""
🔧 Configuration File - All project settings in one place
Edit this file to customize the system behavior
"""

from pathlib import Path

# =============================================================================
# 📁 PROJECT PATHS
# =============================================================================
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
MODELS_DIR = PROJECT_ROOT / "models"
VIDEOS_DIR = PROJECT_ROOT / "videos"
SUMO_DIR = PROJECT_ROOT / "sumo_simulation"

# =============================================================================
# 🎥 VIDEO SOURCES
# =============================================================================
# Option 1: Use same video for all lanes (for demo)
DEFAULT_VIDEO = r"C:\Users\sskar\Downloads\Lane 1.mp4"

VIDEO_SOURCES = {
    "Lane 1": r"C:\Users\sskar\PycharmProjects\AI_Traffic_Project\videos\lane1.mp4",  # North
    "Lane 2": r"C:\Users\sskar\PycharmProjects\AI_Traffic_Project\videos\lane3.mp4",  # East
    "Lane 3": r"C:\Users\sskar\Downloads\2034115-hd_1920_1080_30fps.mp4",  # South
    "Lane 4": r"C:\Users\sskar\Downloads\854745-hd_1280_720_50fps.mp4"  # West
}


# Option 2: Use webcams (set to 0, 1, 2, 3 for different cameras)
# VIDEO_SOURCES = {
#     "Lane 1": 0,
#     "Lane 2": 1,
#     "Lane 3": 2,
#     "Lane 4": 3
# }

# =============================================================================
# 🚦 TRAFFIC CONTROL PARAMETERS
# =============================================================================
class TrafficConfig:
    """Traffic light timing configuration."""

    # Lane names
    LANE_NAMES = ["Lane 1", "Lane 2", "Lane 3", "Lane 4"]

    # Timing parameters (in seconds)
    BASE_GREEN_TIME = 10  # Minimum green light duration
    MAX_GREEN_TIME = 45  # Maximum green light duration
    TIME_PER_VEHICLE = 0.5  # Additional seconds per vehicle
    DENSITY_THRESHOLD = 5  # Minimum vehicles to trigger dynamic timing

    YELLOW_TIME = 3  # Yellow light duration
    ALL_RED_TIME = 2  # All-red clearance time

    # Controller update rate
    TICKS_PER_SECOND = 10  # How fast the controller runs

    # Explanation for presentation
    @staticmethod
    def get_explanation():
        return {
            "Algorithm": "Max Pressure (Priority to Most Congested Lane)",
            "Base Green": f"{TrafficConfig.BASE_GREEN_TIME}s minimum",
            "Dynamic Formula": f"{TrafficConfig.BASE_GREEN_TIME}s + (vehicles × {TrafficConfig.TIME_PER_VEHICLE}s)",
            "Max Green": f"{TrafficConfig.MAX_GREEN_TIME}s maximum",
            "Yellow": f"{TrafficConfig.YELLOW_TIME}s transition",
            "All Red": f"{TrafficConfig.ALL_RED_TIME}s safety clearance"
        }


# =============================================================================
# 🤖 YOLO DETECTION PARAMETERS
# =============================================================================
class DetectionConfig:
    """YOLO model configuration."""

    MODEL_NAME = 'yolov8n.pt'  # Can use: yolov8n, yolov8s, yolov8m, yolov8l
    MODEL_PATH = MODELS_DIR / MODEL_NAME

    # COCO dataset vehicle class IDs
    VEHICLE_CLASSES = [2, 3, 5, 7]  # car, motorcycle, bus, truck
    VEHICLE_NAMES = {
        2: "car",
        3: "motorcycle",
        5: "bus",
        7: "truck"
    }

    # Detection parameters
    CONFIDENCE_THRESHOLD = 0.4  # Minimum confidence to count detection
    UPDATE_INTERVAL = 1.0  # Seconds between database updates

    # Display settings
    DISPLAY_ANNOTATED = True  # Show bounding boxes
    DISPLAY_FPS = True  # Show FPS counter


# =============================================================================
# 🎮 SUMO SIMULATION PARAMETERS
# =============================================================================
class SUMOConfig:
    """SUMO simulation configuration."""

    CONFIG_FILE = SUMO_DIR / "intersection.sumocfg"

    # SUMO edge IDs corresponding to lane names
    LANE_EDGES = {
        "Lane 1": "N1J0",  # North approach
        "Lane 2": "E1J0",  # East approach
        "Lane 3": "S1J0",  # South approach
        "Lane 4": "W1J0"  # West approach
    }

    TRAFFIC_LIGHT_ID = "J0"

    # Simulation settings
    USE_GUI = True  # Show SUMO GUI
    STEP_LENGTH = 0.1  # Simulation step in seconds

    # Data collection
    COLLECT_STATISTICS = True  # Collect performance metrics
    STATS_INTERVAL = 10.0  # Seconds between statistics updates


# =============================================================================
# 📊 VISUALIZATION PARAMETERS
# =============================================================================
class VisualizationConfig:
    """Display and visualization settings."""

    # Window sizes
    LANE_VIEW_WIDTH = 640
    LANE_VIEW_HEIGHT = 360

    # Colors (BGR format)
    COLOR_GREEN = (0, 255, 0)
    COLOR_YELLOW = (0, 255, 255)
    COLOR_RED = (0, 0, 255)
    COLOR_WHITE = (255, 255, 255)
    COLOR_BLACK = (0, 0, 0)
    COLOR_GRAY = (100, 100, 100)

    # UI settings
    FONT = 0  # cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE = 0.7
    FONT_THICKNESS = 2

    # Signal light size
    SIGNAL_RADIUS = 45

    # Update rates
    DISPLAY_FPS = 30
    INFO_UPDATE_INTERVAL = 5.0  # Seconds between info prints


# =============================================================================
# 🗄️ DATABASE PARAMETERS
# =============================================================================
class DatabaseConfig:
    """Local database configuration."""

    COUNTS_FILE = "lane_counts.json"
    STATE_FILE = "signal_state.json"

    # File watch settings
    WATCH_INTERVAL = 0.1  # Seconds between file checks

    # Backup settings
    ENABLE_BACKUP = True
    BACKUP_INTERVAL = 300  # Seconds between backups


# =============================================================================
# 📝 LOGGING PARAMETERS
# =============================================================================
class LoggingConfig:
    """Logging configuration."""

    LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    # Log file names
    CONTROLLER_LOG = "controller.log"
    DETECTOR_LOG = "detector.log"
    SUMO_LOG = "sumo.log"

    # Log format
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    # Console output
    CONSOLE_OUTPUT = True
    COLORIZED_OUTPUT = True


# =============================================================================
# 🎯 PRESENTATION MODE
# =============================================================================
class PresentationConfig:
    """Settings for presentation/demo mode."""

    # Enable enhanced visualization
    SHOW_STATISTICS = True
    SHOW_AI_DECISIONS = True
    SHOW_INTERSECTION_VIEW = True

    # Auto-screenshot for reports
    AUTO_SCREENSHOT = False
    SCREENSHOT_INTERVAL = 30.0  # Seconds

    # Performance metrics
    TRACK_WAIT_TIME = True
    TRACK_THROUGHPUT = True
    TRACK_CYCLE_TIME = True

    # Explanation mode
    VERBOSE_DECISIONS = True  # Print detailed decision explanations


# =============================================================================
# 🔍 VALIDATION
# =============================================================================
def validate_config():
    """Validate configuration and create necessary directories."""
    import os

    # Create directories
    for directory in [DATA_DIR, LOGS_DIR, MODELS_DIR, VIDEOS_DIR]:
        os.makedirs(directory, exist_ok=True)

    # Check SUMO config
    if not SUMOConfig.CONFIG_FILE.exists():
        print(f"⚠️  SUMO config not found: {SUMOConfig.CONFIG_FILE}")

    # Check video files
    missing_videos = []
    for lane, path in VIDEO_SOURCES.items():
        if isinstance(path, str) and not Path(path).exists():
            missing_videos.append(f"{lane}: {path}")

    if missing_videos:
        print("⚠️  WARNING: Some video files not found:")
        for msg in missing_videos:
            print(f"  - {msg}")
        print("  You can still run with SUMO-only mode")

    return True


# Run validation on import
if __name__ != "__main__":
    validate_config()