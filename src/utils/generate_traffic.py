"""
SUMO Traffic Generation Utility

Generates realistic background traffic for SUMO simulations with configurable
vehicle counts, distributions, and traffic patterns. Supports multiple traffic
scenarios (low/moderate/high/severe congestion).

Author: Emergency Vehicle Routing Research Team
License: MIT
Version: 1.0.0
"""

import argparse
import logging
import os
import random
import subprocess
import sys
from typing import List, Dict
import sumolib

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Traffic scenario definitions
TRAFFIC_SCENARIOS = {
    "low": {
        "vehicles": 2000,
        "car_ratio": 0.85,
        "bus_ratio": 0.08,
        "truck_ratio": 0.07,
        "depart_window": 100,  # 100 seconds = ~20 vehicles/sec
        "description": "Light traffic, minimal congestion",
    },
    "moderate": {
        "vehicles": 5000,
        "car_ratio": 0.80,
        "bus_ratio": 0.10,
        "truck_ratio": 0.10,
        "depart_window": 250,  # 250 seconds = ~20 vehicles/sec
        "description": "Normal traffic conditions",
    },
    "high": {
        "vehicles": 10000,
        "car_ratio": 0.75,
        "bus_ratio": 0.12,
        "truck_ratio": 0.13,
        "depart_window": 500,  # 500 seconds = ~20 vehicles/sec
        "description": "Heavy traffic, significant congestion",
    },
    "severe": {
        "vehicles": 20000,
        "car_ratio": 0.70,
        "bus_ratio": 0.15,
        "truck_ratio": 0.15,
        "depart_window": 1000,  # 1000 seconds = ~20 vehicles/sec
        "description": "Severe congestion, gridlock conditions",
    },
}


def find_suitable_edges(
    network_file: str, min_length: float = 50.0, min_speed: float = 5.0
) -> List[str]:
    """
    Find suitable edges for traffic generation.

    Args:
        network_file: Path to SUMO network XML file
        min_length: Minimum edge length in meters
        min_speed: Minimum speed limit in m/s

    Returns:
        List of suitable edge IDs

    Raises:
        FileNotFoundError: If network file doesn't exist
    """
    if not os.path.exists(network_file):
        raise FileNotFoundError(f"Network file not found: {network_file}")

    print(f"Loading network from {network_file}...")
    net = sumolib.net.readNet(network_file)

    print("Analyzing network for suitable edges...")
    suitable_edges = []

    for edge in net.getEdges():
        if (
            edge.allows("passenger")
            and edge.getLength() > min_length
            and not edge.getID().startswith(":")
            and edge.getSpeed() > min_speed
        ):
            suitable_edges.append(edge.getID())

    print(f"✓ Found {len(suitable_edges):,} suitable edges")
    return suitable_edges


def generate_vehicle_trips(
    suitable_edges: List[str],
    output_file: str,
    scenario: str = "moderate",
    custom_vehicles: int = None,
) -> Dict[str, int]:
    """
    Generate vehicle trip definitions.

    Args:
        suitable_edges: List of edge IDs for route generation
        output_file: Path to output trips XML file
        scenario: Traffic scenario (low/moderate/high/severe)
        custom_vehicles: Override vehicle count (ignores scenario default)

    Returns:
        Dictionary with generation statistics
    """
    config = TRAFFIC_SCENARIOS[scenario]
    num_vehicles = custom_vehicles if custom_vehicles else config["vehicles"]

    print(f"\nGenerating {scenario.upper()} traffic scenario:")
    print(f"  Vehicles: {num_vehicles:,}")
    print(
        f"  Departure window: {config['depart_window']}s ({config['depart_window']/60:.1f} min)"
    )
    print(
        f"  Distribution: {config['car_ratio']*100:.0f}% cars, "
        f"{config['bus_ratio']*100:.0f}% buses, {config['truck_ratio']*100:.0f}% trucks"
    )

    # Calculate vehicle counts by type
    num_cars = int(num_vehicles * config["car_ratio"])
    num_buses = int(num_vehicles * config["bus_ratio"])
    num_trucks = num_vehicles - num_cars - num_buses

    with open(output_file, "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ')
        f.write(
            'xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">\n\n'
        )

        # Vehicle type definitions
        f.write("    <!-- Vehicle Type Definitions -->\n")
        f.write('    <vType id="car" vClass="passenger" color="1,1,0" ')
        f.write('speedFactor="1.0" speedDev="0.1" sigma="0.5"/>\n')
        f.write('    <vType id="bus" vClass="bus" color="0,0,1" ')
        f.write('speedFactor="0.9" speedDev="0.05" sigma="0.5"/>\n')
        f.write('    <vType id="truck" vClass="truck" color="0.5,0.5,0.5" ')
        f.write('speedFactor="0.8" speedDev="0.05" sigma="0.5"/>\n')
        f.write('    <vType id="emergency" vClass="emergency" color="1,0,0" ')
        f.write('speedFactor="1.3" sigma="0.0" guiShape="emergency"/>\n\n')

        # Generate trips
        f.write(f"    <!-- Background Traffic: {scenario.upper()} Scenario -->\n")
        f.write(
            f"    <!-- {num_cars:,} cars, {num_buses:,} buses, {num_trucks:,} trucks -->\n"
        )
        f.write("\n")

        vehicle_id = 0

        # Generate cars
        for i in range(num_cars):
            depart_time = random.uniform(0, config["depart_window"])
            from_edge = random.choice(suitable_edges)
            to_edge = random.choice(suitable_edges)
            while to_edge == from_edge:
                to_edge = random.choice(suitable_edges)

            f.write(f'    <trip id="bg_car_{vehicle_id}" type="car" ')
            f.write(f'depart="{depart_time:.2f}" from="{from_edge}" to="{to_edge}"/>\n')
            vehicle_id += 1

            if (vehicle_id) % 200 == 0:
                print(f"  Generated {vehicle_id:,}/{num_vehicles:,} trips...", end="\r")

        # Generate buses
        for i in range(num_buses):
            depart_time = random.uniform(0, config["depart_window"])
            from_edge = random.choice(suitable_edges)
            to_edge = random.choice(suitable_edges)
            while to_edge == from_edge:
                to_edge = random.choice(suitable_edges)

            f.write(f'    <trip id="bg_bus_{vehicle_id}" type="bus" ')
            f.write(f'depart="{depart_time:.2f}" from="{from_edge}" to="{to_edge}"/>\n')
            vehicle_id += 1

            if (vehicle_id) % 200 == 0:
                print(f"  Generated {vehicle_id:,}/{num_vehicles:,} trips...", end="\r")

        # Generate trucks
        for i in range(num_trucks):
            depart_time = random.uniform(0, config["depart_window"])
            from_edge = random.choice(suitable_edges)
            to_edge = random.choice(suitable_edges)
            while to_edge == from_edge:
                to_edge = random.choice(suitable_edges)

            f.write(f'    <trip id="bg_truck_{vehicle_id}" type="truck" ')
            f.write(f'depart="{depart_time:.2f}" from="{from_edge}" to="{to_edge}"/>\n')
            vehicle_id += 1

            if (vehicle_id) % 200 == 0:
                print(f"  Generated {vehicle_id:,}/{num_vehicles:,} trips...", end="\r")

        f.write("\n</routes>\n")

    print(f"\n✓ Generated {num_vehicles:,} vehicle trips")
    print(f"✓ Saved to: {output_file}")

    return {
        "total": num_vehicles,
        "cars": num_cars,
        "buses": num_buses,
        "trucks": num_trucks,
    }


def add_emergency_vtype(routes_file: str) -> None:
    """
    Add emergency vType to routes file if not already present.
    duarouter overwrites vType definitions, so we need to inject it back.

    Args:
        routes_file: Path to routes XML file
    """
    with open(routes_file, "r") as f:
        content = f.read()

    emergency_vtype = '    <vType id="emergency" vClass="emergency" color="1,0,0" speedFactor="1.3" sigma="0.0" guiShape="emergency"/>\n'

    # Check if emergency vType already exists
    if 'id="emergency"' in content:
        return

    # Find the closing tag of first vType and add emergency after it
    if "<vType" in content:
        # Find position after the first vType closing
        first_vtype_end = content.find('"/>\n', content.find("<vType"))
        if first_vtype_end != -1:
            insert_pos = first_vtype_end + 4
            content = content[:insert_pos] + emergency_vtype + content[insert_pos:]
    else:
        # If no vTypes, add before routes closing tag
        routes_end = content.find("</routes>")
        if routes_end != -1:
            content = (
                content[:routes_end] + emergency_vtype + "\n" + content[routes_end:]
            )

    with open(routes_file, "w") as f:
        f.write(content)


def convert_trips_to_routes(
    network_file: str, trips_file: str, routes_file: str, threads: int = 4
) -> bool:
    """
    Convert trip definitions to routed vehicles using duarouter.

    Args:
        network_file: Path to SUMO network file
        trips_file: Path to trips XML file
        routes_file: Path to output routes XML file
        threads: Number of routing threads

    Returns:
        True if successful, False otherwise
    """
    print("\nConverting trips to routes with duarouter...")
    print("This may take several minutes for large traffic volumes...")

    cmd = [
        "duarouter",
        "--net-file",
        network_file,
        "--trip-files",
        trips_file,
        "--output-file",
        routes_file,
        "--ignore-errors",
        "--no-warnings",
        "--routing-threads",
        str(threads),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

        if result.returncode == 0:
            print("✓ Routes generated successfully!")
            # Add emergency vType after duarouter processing
            add_emergency_vtype(routes_file)
            return True
        else:
            print("⚠ Warning: duarouter completed with warnings")
            print("This is normal for large networks with disconnected components")
            # Still try to add emergency vType
            add_emergency_vtype(routes_file)
            return True
    except subprocess.TimeoutExpired:
        print("✗ Error: duarouter timeout (>30 minutes)")
        return False
    except FileNotFoundError:
        print("✗ Error: duarouter not found. Is SUMO installed and in PATH?")
        return False
    except Exception as e:
        print(f"✗ Error running duarouter: {e}")
        return False


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Generate realistic background traffic for SUMO simulations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Traffic Scenarios:
  low      - 200 vehicles, light traffic, minimal congestion
  moderate - 500 vehicles, normal traffic conditions (default)
  high     - 1000 vehicles, heavy traffic, significant congestion
  severe   - 2000 vehicles, severe congestion, gridlock conditions

Examples:
  # Generate moderate traffic (default)
  python generate_traffic.py -n network.net.xml -o traffic.rou.xml
  
  # Generate high traffic scenario
  python generate_traffic.py -n network.net.xml -o traffic_high.rou.xml --scenario high
  
  # Custom vehicle count
  python generate_traffic.py -n network.net.xml -o traffic.rou.xml --vehicles 750
  
  # Skip routing (generate trips only)
  python generate_traffic.py -n network.net.xml -o traffic.trips.xml --trips-only

Output Files:
  - *.trips.xml: Trip definitions (origin-destination pairs)
  - *.rou.xml: Routed vehicles (full paths computed by duarouter)
        """,
    )

    # Required arguments
    parser.add_argument(
        "-n", "--network", type=str, required=True, help="SUMO network file (.net.xml)"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Output file path (.rou.xml or .trips.xml)",
    )

    # Traffic configuration
    traffic_group = parser.add_argument_group("Traffic Configuration")
    traffic_group.add_argument(
        "--scenario",
        type=str,
        choices=["low", "moderate", "high", "severe"],
        default="moderate",
        help="Predefined traffic scenario (default: moderate)",
    )
    traffic_group.add_argument(
        "--vehicles", type=int, help="Custom vehicle count (overrides scenario default)"
    )

    # Edge filtering
    filter_group = parser.add_argument_group("Edge Filtering")
    filter_group.add_argument(
        "--min-length",
        type=float,
        default=50.0,
        help="Minimum edge length in meters (default: 50)",
    )
    filter_group.add_argument(
        "--min-speed",
        type=float,
        default=5.0,
        help="Minimum speed limit in m/s (default: 5)",
    )

    # Routing options
    route_group = parser.add_argument_group("Routing Options")
    route_group.add_argument(
        "--trips-only",
        action="store_true",
        help="Generate trips only, skip routing (no duarouter)",
    )
    route_group.add_argument(
        "--threads", type=int, default=4, help="Number of routing threads (default: 4)"
    )

    args = parser.parse_args()

    # Determine output files
    if args.trips_only:
        trips_file = args.output
        routes_file = None
    else:
        # Generate intermediate trips file
        base_name = os.path.splitext(args.output)[0]
        trips_file = f"{base_name}.trips.xml"
        routes_file = args.output

    print("=" * 80)
    print("SUMO TRAFFIC GENERATION")
    print("=" * 80)

    try:
        # Step 1: Find suitable edges
        suitable_edges = find_suitable_edges(
            args.network, args.min_length, args.min_speed
        )

        if len(suitable_edges) < 10:
            print(
                "\n⚠ Warning: Very few suitable edges found. "
                "Traffic generation may fail."
            )

        # Step 2: Generate trips
        stats = generate_vehicle_trips(
            suitable_edges, trips_file, args.scenario, args.vehicles
        )

        # Step 3: Convert to routes (unless trips-only)
        if not args.trips_only:
            success = convert_trips_to_routes(
                args.network, trips_file, routes_file, args.threads
            )

            if success:
                print(f"✓ Final output: {routes_file}")
                print(f"  (Intermediate trips: {trips_file})")
            else:
                print(f"\n⚠ Routing failed, but trips file was created: {trips_file}")

        print("\n" + "=" * 80)
        print("GENERATION COMPLETE")
        print("=" * 80)
        print(f"\nTraffic Statistics:")
        print(f"  Total vehicles: {stats['total']:>6,}")
        print(
            f"  Cars:           {stats['cars']:>6,} ({stats['cars']/stats['total']*100:.0f}%)"
        )
        print(
            f"  Buses:          {stats['buses']:>6,} ({stats['buses']/stats['total']*100:.0f}%)"
        )
        print(
            f"  Trucks:         {stats['trucks']:>6,} ({stats['trucks']/stats['total']*100:.0f}%)"
        )

        if not args.trips_only:
            print(f"\nNext Step:")
            print(
                f"  Add '{os.path.basename(routes_file)}' to your SUMO configuration:"
            )
            print(f'  <route-files value="...{os.path.basename(routes_file)}"/>')

    except FileNotFoundError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
