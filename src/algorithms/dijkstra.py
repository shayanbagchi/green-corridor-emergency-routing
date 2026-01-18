"""
Dijkstra's Algorithm Routing System

This module uses distance-only routing (pure Dijkstra approach).
Pure distance-based optimization without time consideration.

Key Characteristics:
    - Distance-only optimization (1.0 distance + 0.0 time)
    - No heuristic acceleration
    - Guaranteed shortest path by length
    - Classical baseline algorithm

Author: Emergency Vehicle Routing Research Team
License: MIT
Version: 1.0.0
"""

import argparse
import logging
import os
import sys
import traci
import sumolib
from typing import List, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get project root directory (go up from src/algorithms to project root)
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


def create_route_dijkstra(
    net: sumolib.net.Net, start_edge: str, goal_edge: str, max_iterations: int = 1000
) -> List[str]:
    """
    Create route using distance-only routing (pure Dijkstra: 1.0 distance + 0.0 time).

    Args:
        net: SUMO network object
        start_edge: Starting edge identifier
        goal_edge: Destination edge identifier
        max_iterations: Maximum search iterations

    Returns:
        List of edge identifiers forming the route
    """
    route = []
    current_edge = start_edge
    visited: Set[str] = set()
    iterations = 0

    while current_edge != goal_edge and iterations < max_iterations:
        if current_edge in visited:
            break

        visited.add(current_edge)

        # Get outgoing edges
        try:
            edges_leaving = [
                edge.getID() for edge in net.getEdge(current_edge).getOutgoing().keys()
            ]
        except Exception:
            break

        if not edges_leaving:
            break

        # Find best next edge using distance-only
        min_cost_edge = None
        min_distance = float("inf")

        for edge in edges_leaving:
            try:
                # Distance to goal (only metric that matters for Dijkstra)
                distance = traci.simulation.getDistanceRoad(
                    edge, 0.0, goal_edge, 0.0, True
                )
                if distance < 0:
                    continue

                if distance < min_distance:
                    min_distance = distance
                    min_cost_edge = edge
            except Exception:
                continue

        if min_cost_edge is None:
            break

        route.append(current_edge)
        current_edge = min_cost_edge
        iterations += 1

    route.append(goal_edge)
    return route


def run_simulation(
    start_edge: str,
    goal_edge: str,
    config_file: str,
    network_file: str,
    view_settings: str,
    traffic_condition: str = "moderate",
    use_gui: bool = True,
):
    """Run simulation with Dijkstra routing."""

    # Traffic file mapping
    traffic_files = {
        "low": os.path.join(PROJECT_ROOT, "data", "routes", "traffic_low.rou.xml"),
        "moderate": os.path.join(
            PROJECT_ROOT, "data", "routes", "traffic_moderate.rou.xml"
        ),
        "high": os.path.join(PROJECT_ROOT, "data", "routes", "traffic_high.rou.xml"),
        "severe": os.path.join(
            PROJECT_ROOT, "data", "routes", "traffic_severe.rou.xml"
        ),
    }

    # Build SUMO command with Dijkstra routing
    sumo_binary = "sumo" if not use_gui else "sumo-gui"
    sumo_cmd = [sumo_binary, "-c", config_file]

    if use_gui:
        sumo_cmd.extend(
            [
                "--step-length",
                "1.0",
                "--delay",
                "100",
                "--start",
                "--gui-settings-file",
                view_settings,
            ]
        )

    sumo_cmd.extend(
        ["--quit-on-end", "--routing-algorithm", "dijkstra"]  # Dijkstra algorithm
    )

    # Add traffic file
    traffic_file = traffic_files.get(traffic_condition)
    if traffic_file and os.path.exists(traffic_file):
        sumo_cmd.extend(["--additional-files", traffic_file])

    traci.start(sumo_cmd)

    try:
        print("=" * 80)
        print("DIJKSTRA'S ALGORITHM ROUTING")
        print("=" * 80)
        print(f"Algorithm: Dijkstra (SUMO built-in)")
        print(f"Start Edge: {start_edge}")
        print(f"Goal Edge:  {goal_edge}")
        print(f"Traffic: {traffic_condition.upper()}")

        # Load network FIRST (before traffic spawns)
        print("\nLoading network...")
        net = sumolib.net.readNet(network_file)

        # Wait minimal time (spawn ambulance BEFORE most traffic)
        wait_times = {"low": 110, "moderate": 260, "high": 510, "severe": 1010}
        wait_time = wait_times.get(traffic_condition, 10)
        print(f"\nWaiting {wait_time}s before spawning ambulance...")
        while traci.simulation.getTime() < wait_time:
            traci.simulationStep()
        print(f"[OK] Ready to spawn ({traci.vehicle.getIDCount()} vehicles on network)")

        # Spawn vehicle and let SUMO compute route with built-in Dijkstra
        vehicle_id = "ambulance"
        print(f"\nValidating edge reachability...")

        try:
            # Create route with just start edge
            traci.route.add("dijkstra_route", [start_edge])
            traci.vehicle.add(
                vehicle_id, "dijkstra_route", typeID="emergency", depart="now"
            )
            traci.vehicle.setColor(vehicle_id, (0, 255, 0, 255))  # Green

            # Set max speed to 80 km/h (realistic emergency vehicle speed)
            traci.vehicle.setMaxSpeed(vehicle_id, 80.0 / 3.6)  # Convert km/h to m/s
            traci.vehicle.setSpeedFactor(
                vehicle_id, 1.2
            )  # Allow slight speed limit exceeding

            # Try to set target - this will fail if unreachable
            try:
                traci.vehicle.changeTarget(vehicle_id, goal_edge)
                print(f"[OK] Goal edge is reachable")

                # Get the route SUMO computed
                route_edges = traci.vehicle.getRoute(vehicle_id)
                print(f"[OK] Vehicle spawned")
                print(f"[OK] SUMO computed route: {len(route_edges)} edges")

            except traci.exceptions.TraCIException as e:
                # Unreachable - remove vehicle and exit
                traci.vehicle.remove(vehicle_id)
                print(f"[FAIL] Goal edge '{goal_edge}' is UNREACHABLE")
                print(f"\nError: {e}")
                print(f"\nPlease try using a different goal edge.")
                traci.close()
                return None

        except Exception as e:
            print(f"[FAIL] Validation failed: {e}")
            traci.close()
            return None

        # Run simulation
        start_time = None
        vehicle_departed = False
        arrival_detected = False
        arrival_reason = None
        step = 0
        stuck_counter = 0
        traffic_lights_crossed = 0
        seen_tls = set()
        total_distance = 0.0
        route_edges = []

        while step < 10000:
            traci.simulationStep()
            step += 1

            if vehicle_id in traci.vehicle.getIDList():
                if not vehicle_departed:
                    vehicle_departed = True
                    start_time = traci.simulation.getTime()
                    route_edges = traci.vehicle.getRoute(vehicle_id)
                    print(f"[OK] Vehicle departed at {start_time:.2f}s")

                # Track distance
                try:
                    total_distance = traci.vehicle.getDistance(vehicle_id)
                except Exception:
                    pass

                # Track traffic lights/intersections crossed
                try:
                    next_tls = traci.vehicle.getNextTLS(vehicle_id)
                    if next_tls:
                        for tls_data in next_tls:
                            tls_id = tls_data[0]
                            distance_to_tls = tls_data[2]
                            # Count when we're very close and haven't seen this light yet
                            if distance_to_tls < 5.0 and tls_id not in seen_tls:
                                traffic_lights_crossed += 1
                                seen_tls.add(tls_id)
                except Exception:
                    pass

                # Robust multi-method arrival detection (same as adaptive_astar)
                try:
                    vehicle_route = traci.vehicle.getRoute(vehicle_id)
                    route_index = traci.vehicle.getRouteIndex(vehicle_id)
                    current_edge = traci.vehicle.getRoadID(vehicle_id)
                    current_time = traci.simulation.getTime()
                    speed = traci.vehicle.getSpeed(vehicle_id)

                    at_last_edge = route_index == len(vehicle_route) - 1
                    in_arrived_list = vehicle_id in traci.simulation.getArrivedIDList()
                    on_goal_edge = current_edge == goal_edge

                    # Check if stuck at penultimate edge
                    stuck_at_penultimate = False
                    if route_index == len(vehicle_route) - 2:
                        try:
                            lane_pos = traci.vehicle.getLanePosition(vehicle_id)
                            lane_id = traci.vehicle.getLaneID(vehicle_id)
                            lane_length = traci.lane.getLength(lane_id)

                            if lane_length - lane_pos < 1.0 and speed < 0.1:
                                stuck_counter += 1
                                if stuck_counter > 5:  # Stuck for >5 seconds
                                    stuck_at_penultimate = True
                            else:
                                stuck_counter = 0
                        except Exception:
                            pass

                    # Trigger arrival if any condition met
                    if (
                        in_arrived_list
                        or at_last_edge
                        or on_goal_edge
                        or stuck_at_penultimate
                    ):
                        arrival_detected = True
                        arrival_reason = []
                        if in_arrived_list:
                            arrival_reason.append("in arrived list")
                        if at_last_edge:
                            arrival_reason.append("at last route edge")
                        if on_goal_edge:
                            arrival_reason.append("on goal edge")
                        if stuck_at_penultimate:
                            arrival_reason.append("stuck at penultimate edge")
                        arrival_reason = ", ".join(arrival_reason)
                        break

                except Exception as e:
                    # Fallback: simple edge check
                    try:
                        current_edge = traci.vehicle.getRoadID(vehicle_id)
                        if current_edge == goal_edge:
                            arrival_detected = True
                            arrival_reason = "on goal edge (fallback)"
                            break
                    except:
                        pass
            elif vehicle_departed:
                # Vehicle disappeared after departing
                arrival_detected = True
                arrival_reason = "removed from simulation"
                break

        if not start_time:
            print("[FAIL] Error: Vehicle never departed")
            traci.close()
            return None

        end_time = traci.simulation.getTime()
        travel_time = end_time - start_time

        print("\n" + "=" * 80)
        print("[OK] DESTINATION REACHED (Dijkstra)")
        print("=" * 80)
        print(f"Arrival detected via: {arrival_reason}")
        if len(route_edges) > 0:
            try:
                route_index = (
                    traci.vehicle.getRouteIndex(vehicle_id)
                    if vehicle_id in traci.vehicle.getIDList()
                    else len(route_edges)
                )
                print(f"Route completion: {route_index}/{len(route_edges)} edges")
            except:
                print(f"Route completion: {len(route_edges)}/{len(route_edges)} edges")
        print(f"Travel time: {travel_time:.2f}s ({travel_time/60:.2f} min)")
        if total_distance > 0:
            print(f"Total distance: {total_distance/1000:.2f} km")
            if travel_time > 0:
                avg_speed = (total_distance / travel_time) * 3.6
                print(f"Average speed: {avg_speed:.2f} km/h")
        print(f"Traffic lights/intersections crossed: {traffic_lights_crossed}")
        print(f"Algorithm: SUMO Dijkstra")
        print("=" * 80)

        traci.close()
        return travel_time

    except Exception as e:
        print(f"Error during simulation: {e}")
        traci.close()
        return None


def main():
    """Main entry point with CLI."""
    parser = argparse.ArgumentParser(
        description="Dijkstra's Algorithm Routing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--start", type=str, default="290640275#1")
    parser.add_argument("--goal", type=str, default="323470681#1")
    parser.add_argument(
        "--traffic",
        type=str,
        default="moderate",
        choices=["low", "moderate", "high", "severe"],
    )
    parser.add_argument(
        "--config",
        type=str,
        default=os.path.join(PROJECT_ROOT, "data", "network", "bangalore.sumocfg"),
    )
    parser.add_argument(
        "--network",
        type=str,
        default=os.path.join(PROJECT_ROOT, "data", "network", "bangalore.net.xml"),
    )
    parser.add_argument(
        "--view",
        type=str,
        default=os.path.join(PROJECT_ROOT, "data", "network", "bangalore.view.xml"),
    )

    parser.add_argument(
        "--no-gui", action="store_true", help="Run without GUI (faster execution)"
    )

    args = parser.parse_args()

    run_simulation(
        args.start,
        args.goal,
        args.config,
        args.network,
        args.view,
        args.traffic,
        not args.no_gui,
    )


if __name__ == "__main__":
    main()
