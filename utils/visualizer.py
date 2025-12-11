"""
🎨 Enhanced Visualization Utilities
Beautiful graphics for presentation and demonstration
"""

import cv2
import numpy as np
from typing import Dict, Tuple, List
from datetime import datetime


class TrafficVisualizer:
    """Creates professional visualizations for traffic control system."""

    # Color scheme (BGR format)
    COLORS = {
        'green': (0, 255, 0),
        'yellow': (0, 255, 255),
        'red': (0, 0, 255),
        'white': (255, 255, 255),
        'black': (0, 0, 0),
        'gray': (60, 60, 60),
        'dark_gray': (30, 30, 30),
        'light_gray': (150, 150, 150),
        'cyan': (255, 255, 0),
        'orange': (0, 165, 255),
        'blue': (255, 0, 0)
    }

    def __init__(self):
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def draw_signal_light(self,
                          frame: np.ndarray,
                          x: int,
                          y: int,
                          color: Tuple[int, int, int],
                          state_text: str,
                          timer: float,
                          size: int = 50) -> None:
        """Draw an animated traffic signal light."""

        # Background box with shadow
        shadow_offset = 5
        cv2.rectangle(frame,
                      (x - size - shadow_offset, y - size - shadow_offset),
                      (x + size + shadow_offset, y + size + shadow_offset),
                      (20, 20, 20), -1)

        cv2.rectangle(frame, (x - size, y - size), (x + size, y + size),
                      self.COLORS['black'], -1)

        # Main signal circle with glow effect
        if state_text != "RED":
            cv2.circle(frame, (x, y), size - 5, color, -1)
            cv2.circle(frame, (x, y), size - 10, self.COLORS['white'], 2)
        else:
            cv2.circle(frame, (x, y), size - 10, color, -1)

        # Outer ring
        cv2.circle(frame, (x, y), size - 5, self.COLORS['white'], 3)

        # State text below
        text_size = cv2.getTextSize(state_text, self.font, 0.6, 2)[0]
        text_x = x - text_size[0] // 2
        cv2.putText(frame, state_text, (text_x, y + size + 20),
                    self.font, 0.6, self.COLORS['white'], 2)

        # Timer inside circle
        timer_text = f"{timer:.1f}s"
        timer_size = cv2.getTextSize(timer_text, self.font, 0.7, 2)[0]
        timer_x = x - timer_size[0] // 2
        timer_y = y + timer_size[1] // 2
        cv2.putText(frame, timer_text, (timer_x, timer_y),
                    self.font, 0.7, self.COLORS['black'], 2)

    def create_info_panel(self,
                          width: int,
                          height: int,
                          title: str,
                          info_dict: Dict[str, str],
                          highlight_keys: List[str] = None) -> np.ndarray:
        """Create an information panel with title and key-value pairs."""

        panel = np.zeros((height, width, 3), dtype=np.uint8)
        panel[:] = self.COLORS['dark_gray']

        # Title bar
        cv2.rectangle(panel, (0, 0), (width, 50), self.COLORS['black'], -1)
        cv2.putText(panel, title, (15, 32),
                    self.font, 1.0, self.COLORS['cyan'], 2)

        # Content
        y_offset = 80
        for key, value in info_dict.items():
            color = self.COLORS['orange'] if highlight_keys and key in highlight_keys else self.COLORS['white']

            # Key
            cv2.putText(panel, f"{key}:", (15, y_offset),
                        self.font, 0.6, self.COLORS['light_gray'], 1)

            # Value
            cv2.putText(panel, str(value), (200, y_offset),
                        self.font, 0.7, color, 2)

            y_offset += 35

        return panel

    def create_lane_view(self,
                         frame: np.ndarray,
                         lane_name: str,
                         vehicle_count: int,
                         signal_color: Tuple[int, int, int],
                         signal_state: str,
                         timer: float,
                         target_size: Tuple[int, int] = (640, 360)) -> np.ndarray:
        """Create enhanced lane view with overlays."""

        # Resize frame
        resized = cv2.resize(frame, target_size)
        h, w = resized.shape[:2]

        # Draw signal light (top-left)
        self.draw_signal_light(resized, 80, 80, signal_color, signal_state, timer, size=45)

        # Create bottom info bar with gradient
        bar_height = 80
        for i in range(bar_height):
            alpha = i / bar_height
            color_val = int(30 * alpha)
            cv2.line(resized, (0, h - bar_height + i), (w, h - bar_height + i),
                     (color_val, color_val, color_val), 1)

        # Lane name
        cv2.putText(resized, lane_name, (15, h - 45),
                    self.font, 1.2, self.COLORS['cyan'], 3)

        # Vehicle count with icon
        count_text = f"{vehicle_count} vehicles"
        cv2.putText(resized, count_text, (15, h - 15),
                    self.font, 0.9, self.COLORS['white'], 2)

        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(resized, timestamp, (w - 120, h - 15),
                    self.font, 0.6, self.COLORS['light_gray'], 1)

        # Border
        cv2.rectangle(resized, (0, 0), (w - 1, h - 1), signal_color, 3)

        return resized

    def create_intersection_diagram(self,
                                    size: int,
                                    vehicle_counts: Dict[str, int],
                                    lane_names: List[str],
                                    green_index: int,
                                    state: str) -> np.ndarray:
        """Create a top-down intersection view with signal states."""

        intersection = np.zeros((size, size, 3), dtype=np.uint8)
        intersection[:] = self.COLORS['dark_gray']

        center = size // 2
        road_width = 100

        # Draw roads with lane markings
        # Vertical road
        cv2.rectangle(intersection,
                      (center - road_width // 2, 0),
                      (center + road_width // 2, size),
                      self.COLORS['gray'], -1)

        # Lane dividers
        for i in range(0, size, 20):
            cv2.line(intersection, (center, i), (center, i + 10),
                     self.COLORS['white'], 2)

        # Horizontal road
        cv2.rectangle(intersection,
                      (0, center - road_width // 2),
                      (size, center + road_width // 2),
                      self.COLORS['gray'], -1)

        for i in range(0, size, 20):
            cv2.line(intersection, (i, center), (i + 10, center),
                     self.COLORS['white'], 2)

        # Center junction
        cv2.rectangle(intersection,
                      (center - road_width // 2, center - road_width // 2),
                      (center + road_width // 2, center + road_width // 2),
                      self.COLORS['black'], -1)

        # Traffic signals at each approach
        positions = [
            (center, 70, "N", 0),  # North
            (size - 70, center, "E", 1),  # East
            (center, size - 70, "S", 2),  # South
            (70, center, "W", 3)  # West
        ]

        for x, y, direction, idx in positions:
            # Determine signal color
            if idx == green_index:
                if state == "GREEN":
                    color = self.COLORS['green']
                elif state == "YELLOW":
                    color = self.COLORS['yellow']
                else:
                    color = self.COLORS['red']
            else:
                color = self.COLORS['red']

            # Draw signal
            cv2.circle(intersection, (x, y), 25, color, -1)
            cv2.circle(intersection, (x, y), 25, self.COLORS['white'], 3)

            # Direction label
            cv2.putText(intersection, direction, (x - 12, y + 8),
                        self.font, 0.8, self.COLORS['black'], 2)

            # Vehicle count
            lane_name = lane_names[idx]
            count = vehicle_counts.get(lane_name, 0)

            # Position for count display
            if direction == "N":
                count_pos = (x - 20, y - 40)
            elif direction == "E":
                count_pos = (x + 35, y + 5)
            elif direction == "S":
                count_pos = (x - 20, y + 55)
            else:  # W
                count_pos = (x - 65, y + 5)

            # Draw count with background
            count_text = f"{count}"
            text_size = cv2.getTextSize(count_text, self.font, 0.8, 2)[0]
            cv2.rectangle(intersection,
                          (count_pos[0] - 5, count_pos[1] - text_size[1] - 5),
                          (count_pos[0] + text_size[0] + 5, count_pos[1] + 5),
                          self.COLORS['black'], -1)
            cv2.putText(intersection, count_text, count_pos,
                        self.font, 0.8, self.COLORS['yellow'], 2)

        return intersection

    def create_statistics_panel(self,
                                width: int,
                                height: int,
                                stats: Dict) -> np.ndarray:
        """Create a statistics visualization panel."""

        panel = np.zeros((height, width, 3), dtype=np.uint8)
        panel[:] = self.COLORS['dark_gray']

        # Title
        cv2.rectangle(panel, (0, 0), (width, 50), self.COLORS['black'], -1)
        cv2.putText(panel, "PERFORMANCE STATISTICS", (15, 32),
                    self.font, 0.9, self.COLORS['cyan'], 2)

        # Statistics
        y = 80
        metrics = [
            ("Runtime", f"{stats.get('runtime_seconds', 0):.1f}s"),
            ("Cycles", str(stats.get('total_cycles', 0))),
            ("Vehicles Served", str(stats.get('total_vehicles_served', 0))),
            ("Avg/Cycle", f"{stats.get('avg_vehicles_per_cycle', 0):.1f}"),
            ("Cycles/Min", f"{stats.get('cycles_per_minute', 0):.1f}")
        ]

        for label, value in metrics:
            cv2.putText(panel, f"{label}:", (15, y),
                        self.font, 0.6, self.COLORS['light_gray'], 1)
            cv2.putText(panel, value, (200, y),
                        self.font, 0.7, self.COLORS['white'], 2)
            y += 35

        # Green time distribution (bar chart)
        if 'lane_green_times' in stats:
            y += 20
            cv2.putText(panel, "Green Time Distribution:", (15, y),
                        self.font, 0.7, self.COLORS['white'], 2)
            y += 30

            total_time = sum(stats['lane_green_times'].values())
            if total_time > 0:
                max_bar_width = width - 150
                for lane, time in stats['lane_green_times'].items():
                    percentage = (time / total_time) * 100
                    bar_width = int((time / total_time) * max_bar_width)

                    # Lane name
                    cv2.putText(panel, lane[:7], (15, y),
                                self.font, 0.5, self.COLORS['light_gray'], 1)

                    # Bar
                    cv2.rectangle(panel, (100, y - 12), (100 + bar_width, y + 2),
                                  self.COLORS['green'], -1)

                    # Percentage
                    cv2.putText(panel, f"{percentage:.1f}%", (100 + bar_width + 10, y),
                                self.font, 0.5, self.COLORS['white'], 1)

                    y += 25

        return panel