"""
Quick setup script to create all missing files
Run this once: python setup_files.py
"""

import os
from pathlib import Path

# Get project root
project_root = Path(__file__).parent

print("🔧 Setting up project files...")
print(f"Project root: {project_root}")

# Create directories
directories = [
    "src",
    "utils",
    "data",
    "logs",
    "models",
    "videos"
]

for dir_name in directories:
    dir_path = project_root / dir_name
    dir_path.mkdir(exist_ok=True)
    print(f"✓ Directory: {dir_name}")

# Create __init__.py files
init_files = [
    "src/__init__.py",
    "utils/__init__.py"
]

for init_file in init_files:
    file_path = project_root / init_file
    file_path.touch(exist_ok=True)
    print(f"✓ Created: {init_file}")

# Check for required files
required_files = {
    "src/config.py": "Configuration file",
    "utils/visualizer.py": "Visualization utilities",
    "presentation_mode.py": "Main presentation demo",
    "src/traffic_logic.py": "Traffic controller logic",
    "src/local_database.py": "Local database",
}

print("\n📋 Checking required files:")
missing = []

for file_path, description in required_files.items():
    full_path = project_root / file_path
    if full_path.exists():
        print(f"✓ {file_path} - {description}")
    else:
        print(f"✗ {file_path} - MISSING! ({description})")
        missing.append(file_path)

if missing:
    print("\n⚠️  Missing files detected!")
    print("\nYou need to create these files manually:")
    for file in missing:
        print(f"  - {file}")
    print("\nI can create template files for you.")

    response = input("\nCreate template files? (y/n): ")
    if response.lower() == 'y':
        # Create templates
        if "src/config.py" in missing:
            config_template = '''"""
Configuration file - Edit paths and settings here
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
MODELS_DIR = PROJECT_ROOT / "models"
VIDEOS_DIR = PROJECT_ROOT / "videos"

# UPDATE THIS PATH
DEFAULT_VIDEO = r"C:\\Users\\sskar\\Downloads\\5927708-hd_1080_1920_30fps.mp4"

VIDEO_SOURCES = {
    "Lane 1": DEFAULT_VIDEO,
    "Lane 2": DEFAULT_VIDEO,
    "Lane 3": DEFAULT_VIDEO,
    "Lane 4": DEFAULT_VIDEO
}

class TrafficConfig:
    LANE_NAMES = ["Lane 1", "Lane 2", "Lane 3", "Lane 4"]
    BASE_GREEN_TIME = 10
    MAX_GREEN_TIME = 45
    TIME_PER_VEHICLE = 0.5
    DENSITY_THRESHOLD = 5
    YELLOW_TIME = 3
    ALL_RED_TIME = 2
    TICKS_PER_SECOND = 10

    @staticmethod
    def get_explanation():
        return {
            "Algorithm": "Max Pressure",
            "Base Green": f"{TrafficConfig.BASE_GREEN_TIME}s",
            "Dynamic Formula": f"{TrafficConfig.BASE_GREEN_TIME}s + (vehicles × {TrafficConfig.TIME_PER_VEHICLE}s)",
            "Max Green": f"{TrafficConfig.MAX_GREEN_TIME}s",
        }

class DetectionConfig:
    MODEL_NAME = 'yolov8n.pt'
    MODEL_PATH = MODELS_DIR / MODEL_NAME
    VEHICLE_CLASSES = [2, 3, 5, 7]
    CONFIDENCE_THRESHOLD = 0.4
    UPDATE_INTERVAL = 1.0
    DISPLAY_ANNOTATED = True
    DISPLAY_FPS = True

class VisualizationConfig:
    LANE_VIEW_WIDTH = 640
    LANE_VIEW_HEIGHT = 360
    COLOR_GREEN = (0, 255, 0)
    COLOR_YELLOW = (0, 255, 255)
    COLOR_RED = (0, 0, 255)
    COLOR_WHITE = (255, 255, 255)
    COLOR_BLACK = (0, 0, 0)
    DISPLAY_FPS = 30
    INFO_UPDATE_INTERVAL = 5.0

class SUMOConfig:
    CONFIG_FILE = PROJECT_ROOT / "sumo_simulation" / "intersection.sumocfg"
    LANE_EDGES = {
        "Lane 1": "N1J0",
        "Lane 2": "E1J0",
        "Lane 3": "S1J0",
        "Lane 4": "W1J0"
    }
    TRAFFIC_LIGHT_ID = "J0"
    USE_GUI = True

class PresentationConfig:
    SHOW_STATISTICS = True
    SHOW_AI_DECISIONS = True
    VERBOSE_DECISIONS = True
'''
            with open(project_root / "src/config.py", 'w') as f:
                f.write(config_template)
            print("✓ Created src/config.py")

        print("\n✅ Template files created!")
        print("⚠️  You still need to copy the full code from the artifacts above")
else:
    print("\n✅ All required files present!")

print("\n" + "=" * 60)
print("📁 Project Structure:")
print("=" * 60)


def print_tree(directory, prefix="", max_depth=2, current_depth=0):
    """Print directory tree."""
    if current_depth >= max_depth:
        return

    try:
        items = sorted(directory.iterdir())
        for i, item in enumerate(items):
            if item.name.startswith('.') or item.name == '__pycache__':
                continue

            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            print(f"{prefix}{current_prefix}{item.name}")

            if item.is_dir() and current_depth < max_depth - 1:
                extension = "    " if is_last else "│   "
                print_tree(item, prefix + extension, max_depth, current_depth + 1)
    except PermissionError:
        pass


print_tree(project_root)

print("\n" + "=" * 60)
print("🚀 Next Steps:")
print("=" * 60)
print("1. Update video path in src/config.py")
print("2. Copy full code for missing files from the artifacts")
print("3. Run: python presentation_mode.py")
print("=" * 60)