"""
🎮 PYGAME TRAFFIC SIMULATION WITH AI CONTROL
Complete interactive traffic simulation with:
- Random vehicle generation
- Visual intersection with animated vehicles
- AI traffic controller with Max Pressure algorithm
- Real-time dashboard showing decisions
"""

import pygame
import sys
import random
import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.traffic_logic import TrafficController

# Initialize Pygame
pygame.init()

# =============================================================================
# 🎨 CONFIGURATION
# =============================================================================
# Screen settings
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
FPS = 60

# Colors
COLORS = {
    'road': (50, 50, 50),
    'grass': (34, 139, 34),
    'line': (255, 255, 255),
    'green': (0, 255, 0),
    'yellow': (255, 255, 0),
    'red': (255, 0, 0),
    'white': (255, 255, 255),
    'black': (0, 0, 0),
    'blue': (0, 191, 255),
    'dark_gray': (30, 30, 30),
    'light_gray': (180, 180, 180),
    'orange': (255, 165, 0),
    'cyan': (0, 255, 255)
}

# Traffic settings
MIN_VEHICLES = 5
MAX_VEHICLES = 30
VEHICLE_SPAWN_RATE = 0.3  # Probability per second
VEHICLE_SPEED = 2

# =============================================================================
# 🚗 VEHICLE CLASS
# =============================================================================
@dataclass
class Vehicle:
    """Represents a vehicle in the simulation."""
    x: float
    y: float
    lane: str
    color: Tuple[int, int, int]
    width: int = 30
    height: int = 20

    def move(self, speed: float):
        """Move vehicle forward."""
        if self.lane == "Lane 1":  # North (moving down)
            self.y += speed
        elif self.lane == "Lane 2":  # East (moving left)
            self.x -= speed
        elif self.lane == "Lane 3":  # South (moving up)
            self.y -= speed
        elif self.lane == "Lane 4":  # West (moving right)
            self.x += speed

    def draw(self, screen):
        """Draw vehicle."""
        if self.lane in ["Lane 1", "Lane 3"]:  # Vertical
            pygame.draw.rect(screen, self.color,
                           (self.x - self.width//2, self.y - self.height//2,
                            self.width, self.height))
        else:  # Horizontal
            pygame.draw.rect(screen, self.color,
                           (self.x - self.height//2, self.y - self.width//2,
                            self.height, self.width))

        # Outline
        if self.lane in ["Lane 1", "Lane 3"]:
            pygame.draw.rect(screen, COLORS['white'],
                           (self.x - self.width//2, self.y - self.height//2,
                            self.width, self.height), 2)
        else:
            pygame.draw.rect(screen, COLORS['white'],
                           (self.x - self.height//2, self.y - self.width//2,
                            self.height, self.width), 2)


# =============================================================================
# 🎮 MAIN SIMULATION CLASS
# =============================================================================
class TrafficSimulation:
    """Main traffic simulation with Pygame visualization."""

    def __init__(self):
        # Pygame setup
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AI Traffic Control - Pygame Simulation")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 28)

        # Traffic controller
        self.controller = TrafficController(
            ticks_per_second=10,
            lane_names=["Lane 1", "Lane 2", "Lane 3", "Lane 4"]
        )

        # Simulation state
        self.vehicles = {
            "Lane 1": [],
            "Lane 2": [],
            "Lane 3": [],
            "Lane 4": []
        }

        self.target_counts = {
            "Lane 1": random.randint(MIN_VEHICLES, MAX_VEHICLES),
            "Lane 2": random.randint(MIN_VEHICLES, MAX_VEHICLES),
            "Lane 3": random.randint(MIN_VEHICLES, MAX_VEHICLES),
            "Lane 4": random.randint(MIN_VEHICLES, MAX_VEHICLES)
        }

        # Timing
        self.last_tick = time.time()
        self.last_spawn = time.time()
        self.last_target_update = time.time()

        # Statistics
        self.vehicles_passed = {lane: 0 for lane in self.controller.lanes}

        # Intersection center
        self.center_x = 500
        self.center_y = SCREEN_HEIGHT // 2
        self.road_width = 200

        print("🚀 Pygame Traffic Simulation Started")
        print("Controls: SPACE=Pause, R=Reset, ESC=Quit")

    def spawn_vehicles(self):
        """Spawn vehicles to reach target counts."""
        current_time = time.time()

        # Update target counts periodically (every 10 seconds)
        if current_time - self.last_target_update > 10:
            for lane in self.controller.lanes:
                self.target_counts[lane] = random.randint(MIN_VEHICLES, MAX_VEHICLES)
            self.last_target_update = current_time

        # Spawn vehicles
        if current_time - self.last_spawn > (1.0 / (VEHICLE_SPAWN_RATE * 4)):
            for lane in self.controller.lanes:
                current_count = len(self.vehicles[lane])

                # Spawn if below target
                if current_count < self.target_counts[lane]:
                    if random.random() < 0.5:  # 50% chance to spawn
                        self.spawn_vehicle(lane)

            self.last_spawn = current_time

    def spawn_vehicle(self, lane: str):
        """Spawn a single vehicle in specified lane."""
        # Random vehicle color
        colors = [COLORS['cyan'], COLORS['orange'], (255, 100, 100),
                 (100, 255, 100), (255, 255, 100)]
        color = random.choice(colors)

        # Starting positions
        if lane == "Lane 1":  # North (top, moving down)
            x = self.center_x - self.road_width // 4
            y = 50
        elif lane == "Lane 2":  # East (right, moving left)
            x = SCREEN_WIDTH - 50
            y = self.center_y - self.road_width // 4
        elif lane == "Lane 3":  # South (bottom, moving up)
            x = self.center_x + self.road_width // 4
            y = SCREEN_HEIGHT - 50
        elif lane == "Lane 4":  # West (left, moving right)
            x = 50
            y = self.center_y + self.road_width // 4
        else:
            return

        vehicle = Vehicle(x, y, lane, color)
        self.vehicles[lane].append(vehicle)

    def update_vehicles(self):
        """Update vehicle positions."""
        state_info = self.controller.get_current_state_info()
        current_green = state_info['lane_names'][state_info['green_lane_index']]
        is_green = state_info['current_state'] == "GREEN"

        for lane, vehicle_list in self.vehicles.items():
            can_move = (lane == current_green and is_green)

            for vehicle in vehicle_list[:]:
                # Check if at intersection
                at_intersection = self.is_at_intersection(vehicle)

                if at_intersection and not can_move:
                    # Stop at intersection
                    continue

                # Move vehicle
                vehicle.move(VEHICLE_SPEED)

                # Remove if off screen
                if self.is_off_screen(vehicle):
                    vehicle_list.remove(vehicle)
                    self.vehicles_passed[lane] += 1

    def is_at_intersection(self, vehicle: Vehicle) -> bool:
        """Check if vehicle is at intersection."""
        if vehicle.lane == "Lane 1":  # Moving down
            return (self.center_y - 100 < vehicle.y < self.center_y + 50)
        elif vehicle.lane == "Lane 2":  # Moving left
            return (self.center_x - 100 < vehicle.x < self.center_x + 50)
        elif vehicle.lane == "Lane 3":  # Moving up
            return (self.center_y - 50 < vehicle.y < self.center_y + 100)
        elif vehicle.lane == "Lane 4":  # Moving right
            return (self.center_x - 50 < vehicle.x < self.center_x + 100)
        return False

    def is_off_screen(self, vehicle: Vehicle) -> bool:
        """Check if vehicle is off screen."""
        margin = 100
        return (vehicle.x < -margin or vehicle.x > SCREEN_WIDTH + margin or
                vehicle.y < -margin or vehicle.y > SCREEN_HEIGHT + margin)

    def draw_intersection(self):
        """Draw the intersection and roads."""
        # Grass background
        self.screen.fill(COLORS['grass'])

        # Vertical road
        pygame.draw.rect(self.screen, COLORS['road'],
                        (self.center_x - self.road_width//2, 0,
                         self.road_width, SCREEN_HEIGHT))

        # Horizontal road
        pygame.draw.rect(self.screen, COLORS['road'],
                        (0, self.center_y - self.road_width//2,
                         SCREEN_WIDTH, self.road_width))

        # Lane dividers
        dash_length = 20
        gap_length = 20

        # Vertical center line
        y = 0
        while y < SCREEN_HEIGHT:
            pygame.draw.rect(self.screen, COLORS['line'],
                           (self.center_x - 2, y, 4, dash_length))
            y += dash_length + gap_length

        # Horizontal center line
        x = 0
        while x < SCREEN_WIDTH:
            pygame.draw.rect(self.screen, COLORS['line'],
                           (x, self.center_y - 2, dash_length, 4))
            x += dash_length + gap_length

        # Stop lines
        line_width = 4
        offset = 80

        # North stop line
        pygame.draw.line(self.screen, COLORS['white'],
                        (self.center_x - self.road_width//2, self.center_y - offset),
                        (self.center_x, self.center_y - offset), line_width)

        # East stop line
        pygame.draw.line(self.screen, COLORS['white'],
                        (self.center_x + offset, self.center_y - self.road_width//2),
                        (self.center_x + offset, self.center_y), line_width)

        # South stop line
        pygame.draw.line(self.screen, COLORS['white'],
                        (self.center_x, self.center_y + offset),
                        (self.center_x + self.road_width//2, self.center_y + offset), line_width)

        # West stop line
        pygame.draw.line(self.screen, COLORS['white'],
                        (self.center_x - offset, self.center_y),
                        (self.center_x - offset, self.center_y + self.road_width//2), line_width)

    def draw_traffic_lights(self):
        """Draw traffic lights at intersection."""
        state_info = self.controller.get_current_state_info()
        green_index = state_info['green_lane_index']
        current_state = state_info['current_state']

        # Light positions
        positions = [
            (self.center_x - 50, self.center_y - 120),  # North
            (self.center_x + 120, self.center_y - 50),  # East
            (self.center_x + 50, self.center_y + 120),  # South
            (self.center_x - 120, self.center_y + 50)   # West
        ]

        for i, (x, y) in enumerate(positions):
            # Determine color
            if i == green_index:
                if current_state == "GREEN":
                    color = COLORS['green']
                elif current_state == "YELLOW":
                    color = COLORS['yellow']
                else:
                    color = COLORS['red']
            else:
                color = COLORS['red']

            # Draw light
            pygame.draw.circle(self.screen, COLORS['black'], (x, y), 25)
            pygame.draw.circle(self.screen, color, (x, y), 20)
            pygame.draw.circle(self.screen, COLORS['white'], (x, y), 20, 3)

    def draw_dashboard(self):
        """Draw comprehensive dashboard."""
        # Dashboard background
        dashboard_x = 1000
        pygame.draw.rect(self.screen, COLORS['dark_gray'],
                        (dashboard_x, 0, SCREEN_WIDTH - dashboard_x, SCREEN_HEIGHT))

        y = 20

        # Title
        title = self.font_large.render("AI CONTROLLER", True, COLORS['cyan'])
        self.screen.blit(title, (dashboard_x + 20, y))
        y += 60

        # Current state
        state_info = self.controller.get_current_state_info()
        current_lane = state_info['lane_names'][state_info['green_lane_index']]
        state = state_info['current_state']
        timer = state_info['timer_sec']

        # State color
        if state == "GREEN":
            state_color = COLORS['green']
        elif state == "YELLOW":
            state_color = COLORS['yellow']
        else:
            state_color = COLORS['red']

        # Active lane
        text = self.font_medium.render("ACTIVE LANE:", True, COLORS['light_gray'])
        self.screen.blit(text, (dashboard_x + 20, y))
        y += 40

        text = self.font_large.render(current_lane, True, state_color)
        self.screen.blit(text, (dashboard_x + 20, y))
        y += 50

        # Signal state
        text = self.font_medium.render(f"Signal: {state}", True, state_color)
        self.screen.blit(text, (dashboard_x + 20, y))
        y += 40

        # Timer
        text = self.font_medium.render(f"Time: {timer:.1f}s", True, COLORS['white'])
        self.screen.blit(text, (dashboard_x + 20, y))
        y += 60

        # Separator
        pygame.draw.line(self.screen, COLORS['light_gray'],
                        (dashboard_x + 20, y), (SCREEN_WIDTH - 20, y), 2)
        y += 20

        # Vehicle counts
        text = self.font_medium.render("VEHICLE COUNTS:", True, COLORS['cyan'])
        self.screen.blit(text, (dashboard_x + 20, y))
        y += 40

        vehicle_counts = {lane: len(vehicles) for lane, vehicles in self.vehicles.items()}

        for i, lane in enumerate(self.controller.lanes):
            count = vehicle_counts[lane]
            is_active = (lane == current_lane)

            # Lane name
            color = COLORS['cyan'] if is_active else COLORS['white']
            text = self.font_small.render(f"{lane}:", True, color)
            self.screen.blit(text, (dashboard_x + 30, y))

            # Count
            text = self.font_medium.render(f"{count}", True, COLORS['white'])
            self.screen.blit(text, (dashboard_x + 200, y))

            # Bar
            bar_width = min(count * 5, 150)
            bar_color = COLORS['green'] if is_active else COLORS['light_gray']
            pygame.draw.rect(self.screen, bar_color,
                           (dashboard_x + 250, y + 5, bar_width, 20))

            y += 35

        y += 20

        # AI Logic explanation
        pygame.draw.line(self.screen, COLORS['light_gray'],
                        (dashboard_x + 20, y), (SCREEN_WIDTH - 20, y), 2)
        y += 20

        text = self.font_medium.render("AI LOGIC:", True, COLORS['cyan'])
        self.screen.blit(text, (dashboard_x + 20, y))
        y += 40

        # Formula
        if state == "GREEN":
            count = vehicle_counts[current_lane]
            calc_time = min(10 + (count * 0.5), 45)

            text = self.font_small.render("Formula:", True, COLORS['light_gray'])
            self.screen.blit(text, (dashboard_x + 30, y))
            y += 30

            formula = f"10 + ({count} × 0.5) = {calc_time:.1f}s"
            text = self.font_small.render(formula, True, COLORS['orange'])
            self.screen.blit(text, (dashboard_x + 30, y))
            y += 35

            text = self.font_small.render("Dynamic Time Allocation Algorithm", True, COLORS['light_gray'])
            self.screen.blit(text, (dashboard_x + 30, y))
            y += 30

            text = self.font_small.render("Selects most congested", True, COLORS['light_gray'])
            self.screen.blit(text, (dashboard_x + 30, y))

        y += 50

        # Statistics
        pygame.draw.line(self.screen, COLORS['light_gray'],
                        (dashboard_x + 20, y), (SCREEN_WIDTH - 20, y), 2)
        y += 20

        text = self.font_medium.render("STATISTICS:", True, COLORS['cyan'])
        self.screen.blit(text, (dashboard_x + 20, y))
        y += 40

        stats = self.controller.get_statistics()

        stats_data = [
            ("Cycles:", str(stats['total_cycles'])),
            ("Runtime:", f"{stats['runtime_seconds']:.0f}s"),
            ("Served:", str(sum(self.vehicles_passed.values())))
        ]

        for label, value in stats_data:
            text = self.font_small.render(label, True, COLORS['light_gray'])
            self.screen.blit(text, (dashboard_x + 30, y))

            text = self.font_small.render(value, True, COLORS['white'])
            self.screen.blit(text, (dashboard_x + 200, y))

            y += 30

    def draw_lane_labels(self):
        """Draw lane labels on the roads."""
        labels = [
            ("LANE 1 (N)", self.center_x - 80, 100),
            ("LANE 2 (E)", SCREEN_WIDTH - 200, self.center_y - 80),
            ("LANE 3 (S)", self.center_x + 80, SCREEN_HEIGHT - 100),
            ("LANE 4 (W)", 100, self.center_y + 80)
        ]

        for label, x, y in labels:
            text = self.font_small.render(label, True, COLORS['white'])
            # Shadow
            shadow = self.font_small.render(label, True, COLORS['black'])
            self.screen.blit(shadow, (x + 2, y + 2))
            self.screen.blit(text, (x, y))

    def run(self):
        """Main game loop."""
        running = True
        paused = False

        while running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        paused = not paused
                    elif event.key == pygame.K_r:
                        self.__init__()  # Reset

            if not paused:
                # Spawn vehicles
                self.spawn_vehicles()

                # Update vehicles
                self.update_vehicles()

                # Update controller
                current_time = time.time()
                if current_time - self.last_tick >= 0.1:
                    vehicle_counts = {lane: len(vehicles)
                                    for lane, vehicles in self.vehicles.items()}
                    counts_list = [vehicle_counts[lane] for lane in self.controller.lanes]
                    self.controller.update_vehicle_counts(counts_list)
                    self.controller.update_tick()
                    self.last_tick = current_time

            # Drawing
            self.draw_intersection()

            # Draw all vehicles
            for vehicle_list in self.vehicles.values():
                for vehicle in vehicle_list:
                    vehicle.draw(self.screen)

            self.draw_traffic_lights()
            self.draw_lane_labels()
            self.draw_dashboard()

            # Pause indicator
            if paused:
                text = self.font_large.render("PAUSED", True, COLORS['yellow'])
                rect = text.get_rect(center=(self.center_x, self.center_y))
                pygame.draw.rect(self.screen, COLORS['black'],
                               rect.inflate(40, 20))
                self.screen.blit(text, rect)

            # Update display
            pygame.display.flip()
            self.clock.tick(FPS)

        # Cleanup
        pygame.quit()

        # Print final stats
        print("\n" + "="*60)
        print("📊 FINAL STATISTICS")
        print("="*60)
        stats = self.controller.get_statistics()
        print(f"Total Cycles: {stats['total_cycles']}")
        print(f"Runtime: {stats['runtime_seconds']:.1f}s")
        print(f"\nVehicles Passed:")
        for lane, count in self.vehicles_passed.items():
            print(f"  {lane}: {count}")
        print("="*60)


# =============================================================================
# 🚀 MAIN ENTRY POINT
# =============================================================================
def main():
    """Entry point for Pygame simulation."""

    print("\n" + "="*60)
    print("🎮 AI TRAFFIC CONTROL - PYGAME SIMULATION")
    print("="*60)
    print("\nFeatures:")
    print("  • Random vehicle generation")
    print("  • AI traffic control with Max Pressure")
    print("  • Visual intersection with animated vehicles")
    print("  • Real-time dashboard")
    print("\nControls:")
    print("  SPACE - Pause/Resume")
    print("  R     - Reset simulation")
    print("  ESC   - Quit")
    print("="*60 + "\n")

    # Run simulation
    sim = TrafficSimulation()
    sim.run()


if __name__ == "__main__":
    main()