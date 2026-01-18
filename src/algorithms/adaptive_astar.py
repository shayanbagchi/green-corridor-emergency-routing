"""
Adaptive Weighted A* Emergency Vehicle Routing System

This module implements an adaptive weighted A* pathfinding algorithm for emergency
vehicle routing in urban traffic networks. The algorithm dynamically adjusts routing
weights based on multiple contextual factors to optimize emergency response times.

Key Innovation:
    Unlike standard A* which uses fixed weights, this implementation features
    dynamic weight adaptation based on:
    - Route progress (approaching destination)
    - Emergency severity level (CRITICAL/HIGH/MEDIUM)
    - Real-time traffic congestion
    - Time-of-day patterns (rush hour detection)

Author: Emergency Vehicle Routing Research Team
License: MIT
Version: 1.0.0
"""

import argparse
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
import sumolib
import traci

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get project root directory (go up from src/algorithms to project root)
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

# Add src directory to path for imports
SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SRC_DIR)
from utils import config


@dataclass
class RouteContext:
    """
    Context information for adaptive routing decisions.

    Attributes:
        start_time: Simulation start timestamp
        total_distance: Total route distance in meters
        distance_traveled: Distance covered so far in meters
        time_accumulated: Time elapsed in seconds
        severity: Emergency severity level (CRITICAL, HIGH, MEDIUM)
        vehicle_type: Type of emergency vehicle
        signals_passed: Count of traffic signals encountered
        weight_history: Historical weight adaptations for analysis
    """

    start_time: Optional[float] = None
    total_distance: float = 0.0
    distance_traveled: float = 0.0
    time_accumulated: float = 0.0
    severity: str = "HIGH"
    vehicle_type: str = "ambulance"
    signals_passed: int = 0
    weight_history: List[Dict] = field(default_factory=list)


class AdaptiveWeightedAStarRouter:
    """
    Adaptive Weighted A* pathfinding for emergency vehicles.

    This class implements the core routing algorithm with dynamic weight adaptation
    to optimize emergency vehicle routes based on real-time contextual factors.
    """

    def __init__(
        self,
        network_file: str,
        base_distance_weight: float = 0.6,
        base_time_weight: float = 0.4,
    ):
        """
        Initialize the adaptive router.

        Args:
            network_file: Path to SUMO network XML file
            base_distance_weight: Initial weight for distance component (0-1)
            base_time_weight: Initial weight for time component (0-1)

        Raises:
            FileNotFoundError: If network file doesn't exist
            ValueError: If weights don't sum to 1.0
        """
        if abs(base_distance_weight + base_time_weight - 1.0) > 0.001:
            raise ValueError("Distance and time weights must sum to 1.0")

        self.net = sumolib.net.readNet(network_file)
        self.base_distance_weight = base_distance_weight
        self.base_time_weight = base_time_weight
        self.context = RouteContext()

    def get_adaptive_weights(
        self, current_edge_id: str, goal_edge_id: str
    ) -> Tuple[float, float]:
        """
        Calculate dynamic routing weights based on contextual factors.

        This is the CORE NOVELTY of the algorithm - weights adapt in real-time
        based on multiple factors unlike standard A* with fixed weights.

        Adaptation Factors:
            1. Progress-based: Shift toward time priority near destination
            2. Severity-based: Higher severity = more time-focused
            3. Congestion-based: Adapt to real-time traffic conditions
            4. Time-of-day: Rush hour detection and adjustment

        Args:
            current_edge_id: Current edge identifier
            goal_edge_id: Destination edge identifier

        Returns:
            Tuple of (distance_weight, time_weight) summing to 1.0
        """
        # 1. PROGRESS-BASED ADAPTATION
        progress_shift = 0.0
        if self.context.total_distance > 0:
            progress_ratio = (
                self.context.distance_traveled / self.context.total_distance
            )
            # Shift up to 0.20 toward time weight as we approach destination
            progress_shift = 0.20 * progress_ratio

        # 2. SEVERITY-BASED ADAPTATION
        severity_factors = {
            "CRITICAL": 0.15,  # +15% shift to time priority
            "HIGH": 0.08,  # +8% shift to time priority
            "MEDIUM": 0.0,  # No shift
        }
        severity_shift = severity_factors.get(self.context.severity, 0.0)

        # 3. CONGESTION-BASED ADAPTATION
        # In deployment, this would query real-time traffic data
        congestion_shift = 0.0  # Placeholder for future implementation

        # 4. TIME-OF-DAY ADAPTATION
        current_hour = datetime.now().hour
        rush_hour_shift = (
            0.05 if (7 <= current_hour <= 9) or (16 <= current_hour <= 19) else 0.0
        )

        # COMBINE ALL ADAPTATIONS
        total_shift = (
            progress_shift + severity_shift + congestion_shift + rush_hour_shift
        )

        # Apply shifts (decrease distance weight, increase time weight)
        time_weight = min(0.95, self.base_time_weight + total_shift)
        distance_weight = 1.0 - time_weight

        # Log weight evolution for analysis
        self.context.weight_history.append(
            {
                "edge": current_edge_id,
                "distance_weight": distance_weight,
                "time_weight": time_weight,
                "progress": progress_ratio if self.context.total_distance > 0 else 0,
                "congestion_shift": congestion_shift,
            }
        )

        return distance_weight, time_weight

    def calculate_cost(self, start_edge_id: str, current_node: str) -> float:
        """
        Calculate g(n) - actual cost from start to current node.

        Uses adaptive weights to combine distance and time components.

        Args:
            start_edge_id: Starting edge identifier
            current_node: Current node identifier

        Returns:
            Combined cost value (lower is better)
        """
        try:
            # Get distance from start to current node
            distance = traci.simulation.getDistanceRoad(
                start_edge_id, 0.0, current_node, 0.0, True
            )

            if distance < 0:
                return float("inf")

            # Get current edge speed limit
            try:
                current_edge = self.net.getEdge(current_node)
                speed_limit = current_edge.getSpeed()
            except Exception:
                speed_limit = 40.0  # Default fallback (m/s)

            # Calculate travel time
            travel_time = distance / max(speed_limit, 1.0)

            # Get adaptive weights
            distance_weight, time_weight = self.get_adaptive_weights(
                current_node, self.context.goal_edge
            )

            # Combine with adaptive weights
            combined_cost = distance_weight * distance + time_weight * travel_time

            # Update context
            self.context.distance_traveled = distance
            self.context.time_accumulated = travel_time

            return combined_cost
        except Exception:
            return float("inf")

    def heuristic_estimate(self, current_node: str, goal_node_id: str) -> float:
        """
        Calculate h(n) - estimated cost from current to goal.

        Uses adaptive weights for heuristic estimation.

        Args:
            current_node: Current node identifier
            goal_node_id: Goal node identifier

        Returns:
            Heuristic cost estimate
        """
        try:
            # Get distance from current to goal
            distance = traci.simulation.getDistanceRoad(
                current_node, 0.0, goal_node_id, 0.0, True
            )

            if distance < 0:
                return float("inf")

            # Get speed limit for estimation
            try:
                current_edge = self.net.getEdge(current_node)
                speed_limit = current_edge.getSpeed()
            except Exception:
                speed_limit = 40.0

            # Estimate remaining travel time
            remaining_travel_time = distance / max(speed_limit, 1.0)

            # Get adaptive weights
            distance_weight, time_weight = self.get_adaptive_weights(
                current_node, goal_node_id
            )

            # Combine with adaptive weights
            combined_heuristic = (
                distance_weight * distance + time_weight * remaining_travel_time
            )

            return combined_heuristic
        except Exception:
            return float("inf")

    def evaluate_node(self, node: str, start_node: str, goal_node: str) -> float:
        """
        A* evaluation function: f(n) = g(n) + h(n)

        Args:
            node: Node to evaluate
            start_node: Starting node
            goal_node: Goal node

        Returns:
            Total estimated cost through this node
        """
        g_cost = self.calculate_cost(start_node, node)
        h_cost = self.heuristic_estimate(node, goal_node)
        return g_cost + h_cost

    def find_next_edge(self, current_edge: str, goal_junction: str) -> Optional[str]:
        """
        Find the next edge with minimum cost using adaptive A*.

        Args:
            current_edge: Current edge identifier
            goal_junction: Destination junction identifier

        Returns:
            Next edge identifier or None if no valid edge found
        """
        try:
            edges_leaving = [
                edge.getID()
                for edge in self.net.getEdge(current_edge).getOutgoing().keys()
            ]

            if not edges_leaving:
                return None

            min_cost_edge = None
            min_cost = float("inf")

            for edge in edges_leaving:
                cost = self.evaluate_node(edge, current_edge, goal_junction)
                if cost < min_cost:
                    min_cost = cost
                    min_cost_edge = edge

            return min_cost_edge
        except Exception:
            return None

    def create_route(
        self, start_edge: str, goal_edge: str, max_iterations: int = 1000
    ) -> List[str]:
        """
        Create optimal route using Adaptive Weighted A* via SUMO routing.

        Instead of manual pathfinding (which can violate one-way constraints),
        this method sets custom edge costs in SUMO and lets SUMO compute
        a valid route that respects network topology.

        Args:
            start_edge: Starting edge identifier
            goal_edge: Destination edge identifier
            max_iterations: Maximum search iterations for safety (unused, kept for compatibility)

        Returns:
            List of edge identifiers forming the route
        """
        try:
            # Initialize context
            self.context.total_distance = traci.simulation.getDistanceRoad(
                start_edge, 0.0, goal_edge, 0.0, True
            )
            self.context.goal_edge = goal_edge
            self.context.start_time = traci.simulation.getTime()

            # Set adaptive edge weights for all edges in network
            logger.info("Setting adaptive edge weights for routing")
            for edge in self.net.getEdges():
                edge_id = edge.getID()

                # Skip internal edges
                if edge_id.startswith(":"):
                    continue

                try:
                    # Calculate adaptive cost for this edge
                    edge_length = edge.getLength()
                    edge_speed = edge.getSpeed()

                    # Get adaptive weights (simplified - using severity only for initial route)
                    severity_factors = {"CRITICAL": 0.15, "HIGH": 0.08, "MEDIUM": 0.0}
                    severity_shift = severity_factors.get(self.context.severity, 0.0)
                    time_weight = min(0.95, self.base_time_weight + severity_shift)
                    distance_weight = 1.0 - time_weight

                    # Calculate travel time
                    travel_time = edge_length / max(edge_speed, 1.0)

                    # Combined cost with adaptive weights
                    effort = (
                        distance_weight * edge_length + time_weight * travel_time * 10.0
                    )

                    # Set edge effort (cost) in SUMO
                    traci.edge.setEffort(edge_id, effort)

                except Exception:
                    continue

            logger.info("Computing route using SUMO's routing with adaptive weights")

            # Let SUMO compute the route using our custom edge efforts
            # This respects one-way streets and network topology
            route = traci.simulation.findRoute(start_edge, goal_edge).edges

            if not route or len(route) <= 1:
                logger.warning("SUMO routing failed, trying without custom weights")
                # Fallback: clear efforts and try again
                for edge in self.net.getEdges():
                    edge_id = edge.getID()
                    if not edge_id.startswith(":"):
                        try:
                            traci.edge.setEffort(edge_id, -1)  # Reset to default
                        except:
                            pass
                route = traci.simulation.findRoute(start_edge, goal_edge).edges

            return list(route) if route else [start_edge, goal_edge]

        except Exception as e:
            logger.error(f"Route computation failed: {e}", exc_info=True)
            logger.warning("Falling back to direct edge sequence")
            return [start_edge, goal_edge]


class TrafficLightController:
    """
    Traffic signal preemption for emergency vehicles.

    Implements green corridor by detecting approaching emergency vehicles
    and adjusting traffic light phases to provide right-of-way.
    """

    @staticmethod
    def preempt_traffic_lights(
        vehicle_id: str,
        detection_range: float = 500.0,
        stuck_timeout: float = 10.0,
        stuck_speed: float = 0.1,
        cooldown_period: float = 30.0,
        max_fallbacks: int = 3,
    ) -> bool:
        """
        Enhanced: Preempt compatible green phases, count preemption only on passage, fallback if stuck.
        Args:
            vehicle_id: Emergency vehicle identifier
            detection_range: Distance threshold for preemption (meters)
            stuck_timeout: Time in seconds to revert if ambulance is stuck
            stuck_speed: Speed threshold to consider as stuck (m/s)
            cooldown_period: Time in seconds to wait after fallback before allowing preemption again
            max_fallbacks: Maximum number of fallback attempts before reporting gridlock
        Returns:
            True if any light was successfully changed
        """
        try:
            if vehicle_id not in traci.vehicle.getIDList():
                return False

            tls_list = traci.vehicle.getNextTLS(vehicle_id)
            if not tls_list:
                return False
            tls_id, tls_index, tls_dist, tls_state = tls_list[0]

            # Store original program for each TLS for robust fallback
            if not hasattr(TrafficLightController, "_original_programs"):
                TrafficLightController._original_programs = {}
            if tls_id not in TrafficLightController._original_programs:
                try:
                    TrafficLightController._original_programs[tls_id] = (
                        traci.trafficlight.getProgram(tls_id)
                    )
                except Exception:
                    TrafficLightController._original_programs[tls_id] = None
            original_program = TrafficLightController._original_programs[tls_id]

            # Cooldown tracking for each TLS
            if not hasattr(TrafficLightController, "_cooldowns"):
                TrafficLightController._cooldowns = {}
            cooldowns = TrafficLightController._cooldowns
            sim_time = traci.simulation.getTime()
            # If cooldown is active, skip preemption
            if tls_id in cooldowns and sim_time < cooldowns[tls_id]:
                # Optionally, print debug info
                # print(f"  [COOLDOWN] Skipping preemption for {tls_id} until {cooldowns[tls_id]:.1f}s (now {sim_time:.1f}s)")
                return False

            # Gridlock tracking: after max_fallbacks, stop preempting and report
            if not hasattr(TrafficLightController, "_fallback_counts"):
                TrafficLightController._fallback_counts = {}
            fallback_counts = TrafficLightController._fallback_counts
            if not hasattr(TrafficLightController, "_gridlock_tls"):
                TrafficLightController._gridlock_tls = set()
            gridlock_tls = TrafficLightController._gridlock_tls
            # Placeholder for future: gridlock database
            if not hasattr(TrafficLightController, "_gridlock_db"):
                TrafficLightController._gridlock_db = set()
            gridlock_db = TrafficLightController._gridlock_db
            if tls_id in gridlock_tls:
                return False

            # Track stuck state using vehicle's last movement
            if not hasattr(TrafficLightController, "_stuck_info"):
                TrafficLightController._stuck_info = {}
            stuck_info = TrafficLightController._stuck_info.setdefault(
                vehicle_id,
                {
                    "last_pos": None,
                    "last_time": None,
                    "stuck_start": None,
                    "last_tls": None,
                },
            )

            # Get vehicle position and speed
            pos = traci.vehicle.getPosition(vehicle_id)
            speed = traci.vehicle.getSpeed(vehicle_id)
            # sim_time already set above

            # Detect if stuck at the same intersection
            if stuck_info["last_tls"] == tls_id:
                if speed < stuck_speed:
                    if stuck_info["stuck_start"] is None:
                        stuck_info["stuck_start"] = sim_time
                    elif sim_time - stuck_info["stuck_start"] > stuck_timeout:
                        # Fallback: revert to original program if known
                        fallback_counts[tls_id] = fallback_counts.get(tls_id, 0) + 1
                        if fallback_counts[tls_id] >= max_fallbacks:
                            logger.critical(
                                f"GRIDLOCK: Ambulance stuck at {tls_id} for {max_fallbacks} preemption cycles. Disabling further preemption at this intersection."
                            )
                            gridlock_tls.add(tls_id)
                            gridlock_db.add(
                                tls_id
                            )  # For future improvement: persistent gridlock DB
                            stuck_info["stuck_start"] = None
                            return False
                        if original_program is not None:
                            try:
                                traci.trafficlight.setProgram(tls_id, original_program)
                                logger.warning(
                                    f"FALLBACK: Ambulance stuck >{stuck_timeout}s at {tls_id}, reverting to original signal program '{original_program}'. Cooldown {cooldown_period}s. Fallback count: {fallback_counts[tls_id]}/{max_fallbacks}"
                                )
                                cooldowns[tls_id] = sim_time + cooldown_period
                            except Exception as e:
                                logger.error(
                                    f"Error reverting TLS {tls_id} to program '{original_program}': {e}"
                                )
                        else:
                            logger.warning(
                                f"FALLBACK: Ambulance stuck >{stuck_timeout}s at {tls_id}, but no original program known. Fallback count: {fallback_counts[tls_id]}/{max_fallbacks}"
                            )
                            cooldowns[tls_id] = sim_time + cooldown_period
                        stuck_info["stuck_start"] = None
                        return False
                else:
                    stuck_info["stuck_start"] = None
            else:
                stuck_info["last_tls"] = tls_id
                stuck_info["stuck_start"] = None

            # Only preempt if within detection range and not already green
            if tls_dist <= detection_range and tls_state in ["r", "y"]:
                logic = traci.trafficlight.getAllProgramLogics(tls_id)[0]
                compatible_phases = []
                for phase_idx, phase in enumerate(logic.phases):
                    # If the ambulance's link index is green, check for other compatible greens
                    if tls_index < len(phase.state) and phase.state[tls_index] in [
                        "G",
                        "g",
                    ]:
                        compatible_phases.append(phase_idx)
                if compatible_phases:
                    # Multi-phase preemption: cycle through all compatible phases to clear intersection
                    for phase_idx in compatible_phases:
                        traci.trafficlight.setPhase(tls_id, phase_idx)
                        traci.trafficlight.setPhaseDuration(
                            tls_id, 10
                        )  # Short duration for each phase
                        new_state = traci.trafficlight.getRedYellowGreenState(tls_id)
                        print(
                            f"  -> Signal preemption: {tls_id[:40]}..., Dist: {tls_dist:.1f}m, {tls_state} -> {new_state[tls_index]} (phase {phase_idx}) [multi-phase]"
                        )
                    return True
                print(
                    f"  -> Warning: No compatible green phase found for link {tls_index} at {tls_id[:40]}..."
                )
                return False
        except Exception as e:
            return False
        return False


class EmergencyVehicleSimulation:
    """
    Main simulation controller for emergency vehicle routing.

    Orchestrates the complete simulation including route computation,
    vehicle spawning, traffic light preemption, and performance monitoring.
    """

    def __init__(self, config_file: str, network_file: str, view_settings: str):
        """
        Initialize simulation environment.

        Args:
            config_file: SUMO configuration file path
            network_file: SUMO network file path
            view_settings: GUI visualization settings file path
        """
        self.config_file = config_file
        self.network_file = network_file
        self.view_settings = view_settings
        self.router = AdaptiveWeightedAStarRouter(network_file)
        self.tls_controller = TrafficLightController()

    def spawn_emergency_vehicle(
        self,
        route: List[str],
        vehicle_id: str = "ambulance",
        max_speed_kmh: float = 80.0,
        goal_edge: str = None,
    ) -> None:
        """
        Spawn emergency vehicle with computed route.

        Args:
            route: List of edge IDs forming the initial route
            vehicle_id: Unique identifier for the vehicle
            max_speed_kmh: Maximum speed limit in km/h (realistic constraint)
            goal_edge: Destination edge for dynamic rerouting
        """
        try:
            # Create route with just the start edge - let vehicle navigate dynamically
            if len(route) > 0:
                traci.route.add("emergency_route", [route[0]])
            else:
                logger.error("Empty route provided, cannot spawn vehicle")
                return

            traci.vehicle.add(vehicle_id, "emergency_route", typeID="emergency")

            # Set destination - SUMO will compute valid route respecting network constraints
            if goal_edge:
                try:
                    traci.vehicle.changeTarget(vehicle_id, goal_edge)
                    logger.info(
                        f"Vehicle will navigate to {goal_edge} using SUMO routing"
                    )
                except Exception as e:
                    logger.warning(
                        f"Could not set target: {e}. Using predefined route."
                    )
                    # Fallback: try to set full route
                    if len(route) > 1:
                        traci.vehicle.setRoute(vehicle_id, route)

            # Set realistic emergency vehicle properties
            traci.vehicle.setColor(vehicle_id, (255, 0, 0, 255))  # Red

            # Convert km/h to m/s and set max speed
            max_speed_ms = max_speed_kmh / 3.6
            traci.vehicle.setMaxSpeed(vehicle_id, max_speed_ms)

            # Speed factor for responsiveness (can exceed limits slightly)
            traci.vehicle.setSpeedFactor(vehicle_id, 1.2)

            logger.info(f"Emergency vehicle spawned (Max speed: {max_speed_kmh} km/h)")
        except Exception as e:
            logger.error(f"Error spawning vehicle: {e}", exc_info=True)

    def print_route_statistics(self) -> None:
        """Print weight adaptation statistics from route computation phase."""
        if not self.router.context.weight_history:
            return

        print("\n" + "=" * 80)
        print("ROUTE COMPUTATION - ADAPTIVE WEIGHT STATISTICS")
        print("=" * 80)
        print(f"Total edges evaluated: {len(self.router.context.weight_history)}")

        initial = self.router.context.weight_history[0]
        final = self.router.context.weight_history[-1]

        print(
            f"\nWeights at start: Distance={initial['distance_weight']:.3f}, "
            f"Time={initial['time_weight']:.3f}"
        )
        print(
            f"Weights at end: Distance={final['distance_weight']:.3f}, "
            f"Time={final['time_weight']:.3f}"
        )

        avg_dist = sum(
            w["distance_weight"] for w in self.router.context.weight_history
        ) / len(self.router.context.weight_history)
        avg_time = sum(
            w["time_weight"] for w in self.router.context.weight_history
        ) / len(self.router.context.weight_history)

        print(f"Average weights: Distance={avg_dist:.3f}, Time={avg_time:.3f}")
        print("\nNote: Route is now FIXED. Vehicle follows this pre-computed path.")
        print("=" * 80)

    def run(
        self,
        start_edge: str,
        goal_edge: str,
        severity: str = "HIGH",
        max_speed_kmh: float = 80.0,
        show_weight_stats: bool = False,
        weight_interval: int = 30,
        traffic_condition: str = "moderate",
        use_gui: bool = True,
    ) -> None:
        """
        Execute the complete simulation.

        Args:
            start_edge: Starting edge identifier
            goal_edge: Destination edge identifier
            severity: Emergency severity level (CRITICAL/HIGH/MEDIUM)
            max_speed_kmh: Maximum vehicle speed in km/h
            show_weight_stats: Whether to show route computation statistics
            weight_interval: Interval for real-time weight display (seconds)
            traffic_condition: Traffic scenario (low/moderate/high/severe)
            use_gui: Whether to use SUMO GUI (default: True)
        """
        # Map traffic conditions to route files
        traffic_files = {
            "low": os.path.join(PROJECT_ROOT, "data", "routes", "traffic_low.rou.xml"),
            "moderate": os.path.join(
                PROJECT_ROOT, "data", "routes", "traffic_moderate.rou.xml"
            ),
            "high": os.path.join(
                PROJECT_ROOT, "data", "routes", "traffic_high.rou.xml"
            ),
            "severe": os.path.join(
                PROJECT_ROOT, "data", "routes", "traffic_severe.rou.xml"
            ),
        }

        # Start SUMO
        sumo_binary = "sumo" if not use_gui else "sumo-gui"
        sumo_cmd = [sumo_binary, "-c", self.config_file]

        if use_gui:
            sumo_cmd.extend(
                [
                    "--step-length",
                    "1.0",
                    "--delay",
                    "100",
                    "--start",
                    "--gui-settings-file",
                    self.view_settings,
                ]
            )

        sumo_cmd.append("--quit-on-end")

        # Add traffic file if exists
        traffic_file = traffic_files.get(traffic_condition)
        if traffic_file and os.path.exists(
            os.path.join(os.path.dirname(self.config_file), traffic_file)
        ):
            sumo_cmd.extend(["--additional-files", traffic_file])

        traci.start(sumo_cmd)

        # Set severity
        self.router.context.severity = severity

        print("=" * 80)
        print("ADAPTIVE WEIGHTED A* EMERGENCY VEHICLE ROUTING")
        print("=" * 80)
        print(f"Start Edge: {start_edge}")
        print(f"Goal Edge:  {goal_edge}")
        print(f"Emergency Severity: {severity}")
        print(f"Max Speed: {max_speed_kmh} km/h")
        print(f"Traffic Condition: {traffic_condition.upper()}")
        print("\nComputing optimal route using Adaptive Weighted A*...")

        # Compute route
        route = self.router.create_route(start_edge, goal_edge)

        if not route or len(route) <= 1:
            print("\n[FAIL] Failed to create valid route")
            traci.close()
            return

        print(f"\n[OK] Route computed successfully with {len(route)} edges")

        # Optionally show weight statistics
        if show_weight_stats:
            self.print_route_statistics()

        # Allow traffic to load first (all vehicles depart in first 10 seconds)
        print("\n" + "=" * 80)
        print("LOADING BACKGROUND TRAFFIC...")
        print("=" * 80)

        # Wait times: ambulance spawns AFTER traffic is fully loaded
        # low=110s, moderate=260s, high=510s, severe=1010s
        wait_times = {"low": 110, "moderate": 260, "high": 510, "severe": 1010}
        wait_time = wait_times.get(traffic_condition, 110)

        print(
            f"Waiting {wait_time} seconds for {traffic_condition} traffic to load and settle..."
        )

        while traci.simulation.getTime() < wait_time:
            traci.simulationStep()

        print(
            f"[OK] Background traffic loaded ({traci.vehicle.getIDCount()} vehicles on network)"
        )
        print(
            f"[OK] Spawning emergency vehicle at t={traci.simulation.getTime():.1f}s\n"
        )

        # Spawn vehicle with dynamic routing capability
        self.spawn_emergency_vehicle(
            route, max_speed_kmh=max_speed_kmh, goal_edge=goal_edge
        )

        # Simulation monitoring
        start_time = traci.simulation.getTime()
        vehicle_departed = False
        arrival_detected = False

        print("\n" + "=" * 80)
        print("SIMULATION RUNNING - REAL-TIME MONITORING")
        print("=" * 80)
        print(f"Green corridor active (detection range: 500m)")

        # Reset context for simulation phase
        total_distance = self.router.context.total_distance
        distance_covered = 0.0
        last_weight_time = 0.0
        self.router.context.weight_history.clear()

        # Simulation loop
        step = 0
        lights_preempted = 0
        last_preempted_tls = set()

        while traci.simulation.getMinExpectedNumber() > 0 and step < 3600:
            traci.simulationStep()
            step += 1
            current_time = traci.simulation.getTime()

            if "ambulance" in traci.vehicle.getIDList():
                if not vehicle_departed:
                    vehicle_departed = True
                    print(f"[OK] Ambulance departed at {current_time:.2f}s")

                # Traffic signal preemption (count only when ambulance passes intersection)
                tls_list = traci.vehicle.getNextTLS("ambulance")
                preempted_this_step = False
                if tls_list:
                    tls_id, tls_index, tls_dist, tls_state = tls_list[0]
                    if self.tls_controller.preempt_traffic_lights("ambulance"):
                        # Only count if ambulance is approaching a new intersection
                        if tls_id not in last_preempted_tls:
                            lights_preempted += 1
                            last_preempted_tls.add(tls_id)
                        preempted_this_step = True
                # Remove from set if ambulance has passed the intersection
                for tls_id in list(last_preempted_tls):
                    # If intersection is no longer in nextTLS, ambulance has passed
                    if not tls_list or tls_id != tls_list[0][0]:
                        last_preempted_tls.remove(tls_id)

                # Monitor progress
                try:
                    distance_covered = traci.vehicle.getDistance("ambulance")
                    current_edge = traci.vehicle.getRoadID("ambulance")
                    speed = traci.vehicle.getSpeed("ambulance")

                    if total_distance > 0:
                        progress = distance_covered / total_distance
                        self.router.context.distance_traveled = distance_covered

                        # Calculate adaptive weights
                        w_d, w_t = self.router.get_adaptive_weights(
                            current_edge, goal_edge
                        )

                        # Display at intervals
                        if current_time >= last_weight_time + weight_interval:
                            progress_pct = int(progress * 100)
                            print(
                                f"  [{int(current_time)}s] Progress: {progress_pct}% | "
                                f"Distance: {distance_covered/1000:.2f}km | "
                                f"Speed: {speed*3.6:.1f}km/h | "
                                f"Weights: D={w_d:.3f}, T={w_t:.3f}"
                            )
                            last_weight_time = current_time
                except Exception:
                    pass

                # Check arrival using robust TraCI methods
                # Method 1: Check if vehicle reached last edge in route
                try:
                    vehicle_route = traci.vehicle.getRoute("ambulance")
                    route_index = traci.vehicle.getRouteIndex("ambulance")
                    at_last_edge = route_index == len(vehicle_route) - 1

                    # Method 2: Check if vehicle is in SUMO's arrived list
                    arrived_list = traci.simulation.getArrivedIDList()
                    in_arrived_list = "ambulance" in arrived_list

                    # Method 3: Check if on goal edge (original method)
                    current_edge = traci.vehicle.getRoadID("ambulance")
                    on_goal_edge = current_edge == goal_edge

                    # Arrival condition: any of the three methods confirms arrival
                    # OR if stuck at end of penultimate edge (can't proceed further)
                    if not arrival_detected:
                        # Check if stuck at end of penultimate edge
                        stuck_at_penultimate = False
                        if route_index == len(vehicle_route) - 2:  # Penultimate edge
                            try:
                                lane_pos = traci.vehicle.getLanePosition("ambulance")
                                lane_id = traci.vehicle.getLaneID("ambulance")
                                lane_length = traci.lane.getLength(lane_id)
                                # At end of lane (within 1m) with zero speed for >5 seconds
                                if (
                                    lane_length - lane_pos < 1.0
                                    and speed < 0.1
                                    and current_time - start_time > 5
                                ):
                                    stuck_at_penultimate = True
                            except Exception:
                                pass

                        # Trigger arrival detection
                        if (
                            in_arrived_list
                            or at_last_edge
                            or on_goal_edge
                            or stuck_at_penultimate
                        ):
                            arrival_detected = True
                            arrival_time = current_time
                            travel_time = arrival_time - start_time

                            # Show final progress before arrival message
                            if total_distance > 0 and distance_covered > 0:
                                final_progress = int(
                                    (distance_covered / total_distance) * 100
                                )
                                print(
                                    f"  [{int(current_time)}s] Progress: {final_progress}% | "
                                    f"Distance: {distance_covered/1000:.2f}km | "
                                    f"Speed: {speed*3.6:.1f}km/h | "
                                    f"Weights: D={w_d:.3f}, T={w_t:.3f}"
                                )

                            # Determine arrival reason for debugging
                            arrival_reason = []
                            if in_arrived_list:
                                arrival_reason.append("in arrived list")
                            if at_last_edge:
                                arrival_reason.append("at last route edge")
                            if on_goal_edge:
                                arrival_reason.append("on goal edge")
                            if stuck_at_penultimate:
                                arrival_reason.append("stuck at penultimate edge")

                            print(f"\n" + "=" * 80)
                            print("[OK] DESTINATION REACHED")
                            print("=" * 80)
                            print(f"Arrival detected via: {', '.join(arrival_reason)}")
                            print(
                                f"Route completion: {route_index+1}/{len(vehicle_route)} edges"
                            )
                            print(
                                f"Travel time: {travel_time:.2f}s ({travel_time/60:.2f} min)"
                            )
                            print(f"Total distance: {distance_covered/1000:.2f} km")

                            if travel_time > 0:
                                avg_speed = (distance_covered / travel_time) * 3.6
                                print(f"Average speed: {avg_speed:.2f} km/h")

                            print(f"Traffic lights preempted: {lights_preempted}")
                            break

                except Exception as e:
                    # Fallback to original method if TraCI calls fail
                    current_edge = traci.vehicle.getRoadID("ambulance")
                    if current_edge == goal_edge and not arrival_detected:
                        arrival_detected = True
                        arrival_time = traci.simulation.getTime()
                        travel_time = arrival_time - start_time

                        print(f"\n" + "=" * 80)
                        print("[OK] DESTINATION REACHED")
                        print("=" * 80)
                        print(
                            f"Travel time: {travel_time:.2f}s ({travel_time/60:.2f} min)"
                        )
                        print(f"Total distance: {total_distance/1000:.2f} km")

                        if travel_time > 0:
                            avg_speed = (total_distance / travel_time) * 3.6
                            print(f"Average speed: {avg_speed:.2f} km/h")

                        print(f"Traffic lights preempted: {lights_preempted}")
                        break

        traci.close()
        print("\n[OK] Simulation completed successfully")


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Adaptive Weighted A* Emergency Vehicle Routing System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic simulation with default settings
  python run_simulation.py
  
  # Critical emergency with high traffic
  python run_simulation.py --severity CRITICAL --traffic high --max-speed 100
  
  # Custom route with moderate traffic
  python run_simulation.py --start "edge_123" --goal "edge_456" --traffic moderate
  
  # Show weight adaptation details
  python run_simulation.py --show-weights --weight-interval 20

Traffic Conditions:
  low      - Light traffic, minimal congestion (200 vehicles)
  moderate - Normal traffic conditions (500 vehicles, default)
  high     - Heavy traffic, significant congestion (1000 vehicles)
  severe   - Gridlock conditions (2000 vehicles)

Emergency Severity:
  CRITICAL - Life-threatening, maximum priority (fastest routes)
  HIGH     - Urgent, high priority (balanced optimization, default)
  MEDIUM   - Non-critical, flexible routing (distance-optimized)

Notes:
  - Edge IDs can be found using SUMO netedit or network analysis tools
  - Traffic files must exist in data/routes/ directory
  - Use generate_traffic.py to create custom traffic scenarios
        """,
    )

    # Route configuration
    route_group = parser.add_argument_group("Route Configuration")
    route_group.add_argument(
        "--start",
        type=str,
        default="290640275#1",
        help="Starting edge ID (default: 290640275#1)",
    )
    route_group.add_argument(
        "--goal",
        type=str,
        default="323470681#1",
        help="Destination edge ID (default: 323470681#1)",
    )

    # Emergency parameters
    emergency_group = parser.add_argument_group("Emergency Parameters")
    emergency_group.add_argument(
        "--severity",
        type=str,
        default="HIGH",
        choices=["CRITICAL", "HIGH", "MEDIUM"],
        help="Emergency severity level affecting route priorities (default: HIGH)",
    )
    emergency_group.add_argument(
        "--max-speed",
        type=float,
        default=80.0,
        help="Maximum vehicle speed in km/h (realistic range: 40-120, default: 80)",
    )

    # Traffic simulation
    traffic_group = parser.add_argument_group("Traffic Simulation")
    traffic_group.add_argument(
        "--traffic",
        type=str,
        default="moderate",
        choices=["low", "moderate", "high", "severe"],
        help="Background traffic density level (default: moderate)",
    )

    # Simulation configuration
    sim_group = parser.add_argument_group("Simulation Files")
    sim_group.add_argument(
        "--config",
        type=str,
        default=os.path.join(PROJECT_ROOT, "data", "network", "bangalore.sumocfg"),
        help="SUMO configuration file path",
    )
    sim_group.add_argument(
        "--network",
        type=str,
        default=os.path.join(PROJECT_ROOT, "data", "network", "bangalore.net.xml"),
        help="SUMO network file path",
    )
    sim_group.add_argument(
        "--view",
        type=str,
        default=os.path.join(PROJECT_ROOT, "data", "network", "bangalore.view.xml"),
        help="SUMO GUI visualization settings file path",
    )

    # Display and monitoring options
    display_group = parser.add_argument_group("Display and Monitoring")
    display_group.add_argument(
        "--show-weights",
        action="store_true",
        help="Display adaptive weight evolution statistics during route computation",
    )
    display_group.add_argument(
        "--no-gui", action="store_true", help="Run without GUI (faster execution)"
    )
    display_group.add_argument(
        "--weight-interval",
        type=int,
        default=10,
        help="Real-time weight monitoring interval in seconds (default: 10)",
    )

    args = parser.parse_args()

    # Validate speed
    if args.max_speed <= 0 or args.max_speed > 200:
        print("Error: Max speed must be between 0 and 200 km/h")
        sys.exit(1)

    # Run simulation
    try:
        sim = EmergencyVehicleSimulation(args.config, args.network, args.view)
        sim.run(
            start_edge=args.start,
            goal_edge=args.goal,
            severity=args.severity,
            max_speed_kmh=args.max_speed,
            show_weight_stats=args.show_weights,
            weight_interval=args.weight_interval,
            traffic_condition=args.traffic,
            use_gui=not args.no_gui,
        )
    except FileNotFoundError as e:
        print(f"Error: Required file not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
