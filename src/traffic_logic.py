"""
🧠 Enhanced Traffic Logic Controller
Implements adaptive traffic signal control with detailed decision logging
"""

import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Decision:
    """Records a traffic light decision for analysis."""
    timestamp: datetime
    selected_lane: str
    lane_counts: Dict[str, int]
    calculated_time: float
    reason: str


class TrafficController:
    """
    Enhanced Rule-Based AI Controller for 4-lane intersection.

    Algorithm: Max Pressure with Dynamic Green Time Allocation

    Key Features:
    - Dynamic timing based on vehicle density
    - Max pressure lane selection
    - Detailed decision logging
    - Performance tracking
    """

    def __init__(self,
                 base_green_sec: float = 10,
                 max_green_sec: float = 45,
                 per_vehicle_time: float = 0.5,
                 density_threshold: int = 5,
                 yellow_sec: float = 3,
                 all_red_sec: float = 2,
                 ticks_per_second: int = 10,
                 lane_names: List[str] = None):

        if lane_names is None:
            lane_names = ["Lane 1", "Lane 2", "Lane 3", "Lane 4"]

        # --- AI Logic Parameters ---
        self.BASE_GREEN_SEC = base_green_sec
        self.MAX_GREEN_SEC = max_green_sec
        self.PER_VEHICLE_TIME_SEC = per_vehicle_time
        self.DENSITY_THRESHOLD = density_threshold

        # --- State Machine Parameters ---
        self.YELLOW_SEC = yellow_sec
        self.ALL_RED_SEC = all_red_sec

        # --- System Configuration ---
        self.lanes = lane_names
        self.num_lanes = len(self.lanes)
        self.ticks_per_second = ticks_per_second

        # Convert time to ticks
        self.yellow_ticks = int(self.YELLOW_SEC * self.ticks_per_second)
        self.all_red_ticks = int(self.ALL_RED_SEC * self.ticks_per_second)

        # --- State Variables ---
        self.current_green_lane_index = 0
        self.current_state = "GREEN"
        self.state_timer_ticks = int(self.BASE_GREEN_SEC * self.ticks_per_second)
        self.vehicle_counts = [0] * self.num_lanes

        # --- Statistics & History ---
        self.total_cycles = 0
        self.lane_green_times = {lane: 0.0 for lane in self.lanes}
        self.lane_service_count = {lane: 0 for lane in self.lanes}
        self.decision_history: List[Decision] = []
        self.total_vehicles_served = 0

        # --- Performance Metrics ---
        self.avg_wait_times = []
        self.cycle_times = []
        self.start_time = datetime.now()

        logger.info(f"🚦 TrafficController Initialized")
        logger.info(f"   Lanes: {', '.join(self.lanes)}")
        logger.info(f"   Base Green: {self.BASE_GREEN_SEC}s")
        logger.info(f"   Max Green: {self.MAX_GREEN_SEC}s")
        logger.info(f"   Time per Vehicle: {self.PER_VEHICLE_TIME_SEC}s")
        logger.info(f"   Starting: {self.lanes[0]} GREEN")

    def _calculate_green_time_sec(self, vehicle_count: int) -> Tuple[float, str]:
        """
        Calculate optimal green time with explanation.

        Args:
            vehicle_count: Number of vehicles in the lane

        Returns:
            Tuple of (calculated_time, explanation_string)
        """
        if vehicle_count < self.DENSITY_THRESHOLD:
            reason = f"Low density ({vehicle_count} < {self.DENSITY_THRESHOLD}), using base time"
            return self.BASE_GREEN_SEC, reason

        # Dynamic calculation
        raw_time = self.BASE_GREEN_SEC + (vehicle_count * self.PER_VEHICLE_TIME_SEC)

        if raw_time > self.MAX_GREEN_SEC:
            clamped_time = self.MAX_GREEN_SEC
            reason = f"High demand: {raw_time:.1f}s clamped to max {self.MAX_GREEN_SEC}s"
        else:
            clamped_time = raw_time
            reason = f"Dynamic: {self.BASE_GREEN_SEC} + ({vehicle_count} × {self.PER_VEHICLE_TIME_SEC}) = {clamped_time:.1f}s"

        return clamped_time, reason

    def _decide_next_green_lane_index(self) -> Tuple[int, str]:
        """
        Decide next lane using Max Pressure algorithm with explanation.

        Returns:
            Tuple of (lane_index, decision_explanation)
        """
        max_density = -1
        best_lane_index = (self.current_green_lane_index + 1) % self.num_lanes

        logger.info("🔍 MAX PRESSURE DECISION PROCESS:")

        candidates = []
        for i in range(self.num_lanes):
            if i == self.current_green_lane_index:
                logger.info(f"   ↷ {self.lanes[i]}: CURRENTLY GREEN (skipped)")
                continue

            count = self.vehicle_counts[i]
            candidates.append((i, count))
            logger.info(f"   → {self.lanes[i]}: {count} vehicles")

            if count > max_density:
                max_density = count
                best_lane_index = i

        # Create explanation
        if max_density == 0:
            reason = "All lanes empty, round-robin to next lane"
        elif len(candidates) > 1:
            sorted_candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
            top3 = sorted_candidates[:3]
            top_names = [f"{self.lanes[i]} ({c})" for i, c in top3]
            reason = f"Max pressure: {self.lanes[best_lane_index]} has {max_density} vehicles. Others: {', '.join(top_names[1:])}"
        else:
            reason = f"Selected {self.lanes[best_lane_index]} with {max_density} vehicles"

        logger.info(f"   ✓ SELECTED: {self.lanes[best_lane_index]} ({max_density} vehicles)")

        return best_lane_index, reason

    def update_vehicle_counts(self, counts_list: List[int]) -> None:
        """
        Update vehicle counts with validation.

        Args:
            counts_list: List of vehicle counts for each lane
        """
        if len(counts_list) != self.num_lanes:
            logger.error(f"❌ Count mismatch! Expected {self.num_lanes}, got {len(counts_list)}")
            return

        # Validate counts are non-negative
        validated_counts = [max(0, c) for c in counts_list]

        if validated_counts != counts_list:
            logger.warning("⚠️  Negative counts detected and corrected to 0")

        self.vehicle_counts = validated_counts
        logger.debug(f"📊 Updated counts: {dict(zip(self.lanes, validated_counts))}")

    def _transition_state(self) -> None:
        """Handle state machine transitions with logging."""

        if self.current_state == "GREEN":
            # GREEN → YELLOW
            self.current_state = "YELLOW"
            self.state_timer_ticks = self.yellow_ticks
            logger.info(f"🟡 {self.lanes[self.current_green_lane_index]} → YELLOW ({self.YELLOW_SEC}s)")

        elif self.current_state == "YELLOW":
            # YELLOW → ALL RED
            self.current_state = "ALL_RED"
            self.state_timer_ticks = self.all_red_ticks
            logger.info(f"🔴 ALL LANES → RED (Safety clearance: {self.ALL_RED_SEC}s)")

        elif self.current_state == "ALL_RED":
            # ALL RED → NEW GREEN (Decision Point)
            logger.info("="*70)
            logger.info("🧠 AI DECISION MAKING CYCLE")
            logger.info("="*70)

            # 1. Select next lane with reasoning
            next_index, lane_reason = self._decide_next_green_lane_index()
            self.current_green_lane_index = next_index

            # 2. Get vehicle count
            vehicle_count = self.vehicle_counts[self.current_green_lane_index]

            # 3. Calculate green time with explanation
            new_green_time_sec, time_reason = self._calculate_green_time_sec(vehicle_count)

            # 4. Update state
            self.current_state = "GREEN"
            self.state_timer_ticks = int(new_green_time_sec * self.ticks_per_second)

            # 5. Update statistics
            self.total_cycles += 1
            self.lane_green_times[self.lanes[self.current_green_lane_index]] += new_green_time_sec
            self.lane_service_count[self.lanes[self.current_green_lane_index]] += 1
            self.total_vehicles_served += vehicle_count

            # 6. Record decision
            decision = Decision(
                timestamp=datetime.now(),
                selected_lane=self.lanes[self.current_green_lane_index],
                lane_counts=dict(zip(self.lanes, self.vehicle_counts)),
                calculated_time=new_green_time_sec,
                reason=f"{lane_reason}. {time_reason}"
            )
            self.decision_history.append(decision)

            # Keep only last 100 decisions
            if len(self.decision_history) > 100:
                self.decision_history.pop(0)

            logger.info(f"🟢 {self.lanes[self.current_green_lane_index]} → GREEN")
            logger.info(f"   Duration: {new_green_time_sec:.1f}s")
            logger.info(f"   Vehicles: {vehicle_count}")
            logger.info(f"   Reasoning: {lane_reason}")
            logger.info(f"   Timing: {time_reason}")
            logger.info("="*70)

    def update_tick(self) -> bool:
        """
        Main tick function with enhanced tracking.

        Returns:
            True if state changed, False otherwise
        """
        self.state_timer_ticks -= 1

        if self.state_timer_ticks <= 0:
            self._transition_state()
            return True

        return False

    def get_current_state_info(self) -> Dict:
        """Get comprehensive current state information."""
        return {
            "green_lane_index": self.current_green_lane_index,
            "current_state": self.current_state,
            "timer_sec": round(self.state_timer_ticks / self.ticks_per_second, 1),
            "lane_names": self.lanes,
            "vehicle_counts": self.vehicle_counts,
            "total_cycles": self.total_cycles,
            "timestamp": datetime.now().isoformat()
        }

    def get_statistics(self) -> Dict:
        """Get comprehensive performance statistics."""
        runtime = (datetime.now() - self.start_time).total_seconds()

        return {
            "total_cycles": self.total_cycles,
            "runtime_seconds": runtime,
            "lane_green_times": self.lane_green_times,
            "lane_service_count": self.lane_service_count,
            "current_counts": dict(zip(self.lanes, self.vehicle_counts)),
            "total_vehicles_served": self.total_vehicles_served,
            "avg_vehicles_per_cycle": self.total_vehicles_served / max(1, self.total_cycles),
            "cycles_per_minute": (self.total_cycles / runtime) * 60 if runtime > 0 else 0
        }

    def get_decision_summary(self) -> str:
        """Get human-readable summary of recent decisions."""
        if not self.decision_history:
            return "No decisions recorded yet"

        recent = self.decision_history[-5:]  # Last 5 decisions
        summary = "\n📋 RECENT DECISIONS:\n"

        for i, decision in enumerate(recent, 1):
            summary += f"\n{i}. {decision.timestamp.strftime('%H:%M:%S')} - {decision.selected_lane}\n"
            summary += f"   Counts: {decision.lane_counts}\n"
            summary += f"   Time: {decision.calculated_time:.1f}s\n"
            summary += f"   Reason: {decision.reason}\n"

        return summary

    def print_detailed_status(self) -> None:
        """Print detailed system status for presentation."""
        stats = self.get_statistics()

        print("\n" + "="*70)
        print("📊 TRAFFIC CONTROL SYSTEM STATUS")
        print("="*70)
        print(f"\n⏱️  Runtime: {stats['runtime_seconds']:.1f}s")
        print(f"🔄 Total Cycles: {stats['total_cycles']}")
        print(f"🚗 Vehicles Served: {stats['total_vehicles_served']}")
        print(f"📈 Avg per Cycle: {stats['avg_vehicles_per_cycle']:.1f}")

        print(f"\n🚦 Current State:")
        print(f"   Active: {self.lanes[self.current_green_lane_index]} - {self.current_state}")
        print(f"   Timer: {self.state_timer_ticks / self.ticks_per_second:.1f}s")

        print(f"\n🚗 Live Counts:")
        for lane, count in zip(self.lanes, self.vehicle_counts):
            indicator = "🟢" if lane == self.lanes[self.current_green_lane_index] else "  "
            print(f"   {indicator} {lane}: {count} vehicles")

        print(f"\n⏲️  Green Time Distribution:")
        for lane, time_sec in stats['lane_green_times'].items():
            percentage = (time_sec / sum(stats['lane_green_times'].values()) * 100) if sum(stats['lane_green_times'].values()) > 0 else 0
            print(f"   {lane}: {time_sec:.1f}s ({percentage:.1f}%)")

        print("="*70)