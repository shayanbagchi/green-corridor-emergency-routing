"""
Network Statistics and Scenario Documentation

Extracts detailed statistics about the SUMO network to address reviewer concerns
about scenario details: number of intersections, edges, traffic lights, etc.

This provides the missing context for reproducible research.

Author: Emergency Vehicle Routing Research Team
License: MIT
Version: 1.0.0
"""

import argparse
import logging
import os
import sys
from typing import Dict, List
import sumolib

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NetworkAnalyzer:
    """Analyzes SUMO network and generates detailed statistics."""

    def __init__(self, network_file: str):
        """
        Initialize network analyzer.

        Args:
            network_file: Path to SUMO network XML file
        """
        self.net = sumolib.net.readNet(network_file)
        self.network_file = network_file

    def get_basic_statistics(self) -> Dict:
        """
        Extract basic network statistics.

        Returns:
            Dictionary with network counts
        """
        edges = list(self.net.getEdges())
        nodes = list(self.net.getNodes())
        tls = list(self.net.getTrafficLights())

        # Filter for actual road edges (exclude internal/connector edges)
        road_edges = [
            e
            for e in edges
            if not e.is_fringe(self.net)
            and not e.getFunction() in ["internal", "connector"]
        ]

        # Count junctions by type
        junction_types = {}
        for node in nodes:
            node_type = node.getType()
            junction_types[node_type] = junction_types.get(node_type, 0) + 1

        stats = {
            "total_edges": len(edges),
            "road_edges": len(road_edges),
            "total_nodes": len(nodes),
            "junction_types": junction_types,
            "traffic_lights": len(tls),
            "network_bounds": self.net.getBoundary(),
        }

        return stats

    def get_edge_statistics(self) -> Dict:
        """
        Analyze edge characteristics.

        Returns:
            Dictionary with edge statistics
        """
        edges = list(self.net.getEdges())
        road_edges = [
            e
            for e in edges
            if not e.is_fringe(self.net)
            and not e.getFunction() in ["internal", "connector"]
        ]

        lengths = [e.getLength() for e in road_edges]
        speeds = [e.getSpeed() for e in road_edges]
        lanes = [e.getLaneNumber() for e in road_edges]

        # Calculate total network length
        total_length = sum(lengths)

        stats = {
            "total_network_length_km": total_length / 1000,
            "average_edge_length_m": sum(lengths) / len(lengths) if lengths else 0,
            "min_edge_length_m": min(lengths) if lengths else 0,
            "max_edge_length_m": max(lengths) if lengths else 0,
            "average_speed_limit_kmh": (
                (sum(speeds) / len(speeds)) * 3.6 if speeds else 0
            ),
            "min_speed_limit_kmh": min(speeds) * 3.6 if speeds else 0,
            "max_speed_limit_kmh": max(speeds) * 3.6 if speeds else 0,
            "average_lanes": sum(lanes) / len(lanes) if lanes else 0,
            "max_lanes": max(lanes) if lanes else 0,
        }

        return stats

    def get_traffic_light_statistics(self) -> Dict:
        """
        Analyze traffic light distribution.

        Returns:
            Dictionary with TLS statistics
        """
        tls_list = list(self.net.getTrafficLights())

        # Count controlled links per TLS
        links_per_tls = []
        phases_per_tls = []

        for tls in tls_list:
            # Count connections
            connections = tls.getConnections()
            links_per_tls.append(len(connections))

            # Get programs and count phases
            programs = tls.getPrograms()
            if programs:
                for program in programs.values():
                    phases_per_tls.append(len(program._phases))

        stats = {
            "total_traffic_lights": len(tls_list),
            "average_links_per_tls": (
                sum(links_per_tls) / len(links_per_tls) if links_per_tls else 0
            ),
            "average_phases_per_tls": (
                sum(phases_per_tls) / len(phases_per_tls) if phases_per_tls else 0
            ),
            "max_links_per_tls": max(links_per_tls) if links_per_tls else 0,
            "max_phases_per_tls": max(phases_per_tls) if phases_per_tls else 0,
        }

        return stats

    def calculate_route_statistics(self, start_edge: str, goal_edge: str) -> Dict:
        """
        Calculate statistics for a specific route.

        Args:
            start_edge: Starting edge ID
            goal_edge: Goal edge ID

        Returns:
            Dictionary with route-specific statistics
        """
        try:
            # Get edge objects
            start = self.net.getEdge(start_edge)
            goal = self.net.getEdge(goal_edge)

            # Get coordinates
            start_pos = start.getFromNode().getCoord()
            goal_pos = goal.getToNode().getCoord()

            # Calculate straight-line distance
            straight_distance = (
                (goal_pos[0] - start_pos[0]) ** 2 + (goal_pos[1] - start_pos[1]) ** 2
            ) ** 0.5

            stats = {
                "start_edge": start_edge,
                "goal_edge": goal_edge,
                "start_coordinates": start_pos,
                "goal_coordinates": goal_pos,
                "straight_line_distance_m": straight_distance,
                "straight_line_distance_km": straight_distance / 1000,
                "start_speed_limit_kmh": start.getSpeed() * 3.6,
                "goal_speed_limit_kmh": goal.getSpeed() * 3.6,
            }

            return stats
        except Exception as e:
            return {"error": str(e)}

    def generate_report(
        self, output_file: str, start_edge: str = None, goal_edge: str = None
    ):
        """
        Generate comprehensive markdown report.

        Args:
            output_file: Output markdown file path
            start_edge: Optional start edge for route analysis
            goal_edge: Optional goal edge for route analysis
        """
        basic_stats = self.get_basic_statistics()
        edge_stats = self.get_edge_statistics()
        tls_stats = self.get_traffic_light_statistics()

        with open(output_file, "w") as f:
            f.write("# SUMO Network Statistics Report\n\n")
            f.write("## Network Overview\n\n")
            f.write(f"**Network File:** `{os.path.basename(self.network_file)}`\n\n")

            f.write("### Basic Statistics\n\n")
            f.write(f"- **Total Edges:** {basic_stats['total_edges']:,}\n")
            f.write(f"- **Road Edges:** {basic_stats['road_edges']:,}\n")
            f.write(f"- **Total Nodes (Junctions):** {basic_stats['total_nodes']:,}\n")
            f.write(
                f"- **Traffic Light Intersections:** {basic_stats['traffic_lights']:,}\n"
            )
            f.write(f"- **Network Bounds:** {basic_stats['network_bounds']}\n\n")

            f.write("### Junction Types\n\n")
            f.write("| Type | Count |\n")
            f.write("|------|-------|\n")
            for jtype, count in sorted(basic_stats["junction_types"].items()):
                f.write(f"| {jtype} | {count:,} |\n")
            f.write("\n")

            f.write("## Edge Characteristics\n\n")
            f.write(
                f"- **Total Network Length:** {edge_stats['total_network_length_km']:.2f} km\n"
            )
            f.write(
                f"- **Average Edge Length:** {edge_stats['average_edge_length_m']:.1f} m\n"
            )
            f.write(
                f"- **Edge Length Range:** {edge_stats['min_edge_length_m']:.1f} - {edge_stats['max_edge_length_m']:.1f} m\n"
            )
            f.write(
                f"- **Average Speed Limit:** {edge_stats['average_speed_limit_kmh']:.1f} km/h\n"
            )
            f.write(
                f"- **Speed Limit Range:** {edge_stats['min_speed_limit_kmh']:.1f} - {edge_stats['max_speed_limit_kmh']:.1f} km/h\n"
            )
            f.write(
                f"- **Average Lanes per Edge:** {edge_stats['average_lanes']:.2f}\n"
            )
            f.write(f"- **Maximum Lanes:** {edge_stats['max_lanes']}\n\n")

            f.write("## Traffic Light Statistics\n\n")
            f.write(
                f"- **Total Traffic Lights:** {tls_stats['total_traffic_lights']:,}\n"
            )
            f.write(
                f"- **Average Links per TLS:** {tls_stats['average_links_per_tls']:.1f}\n"
            )
            f.write(
                f"- **Average Phases per TLS:** {tls_stats['average_phases_per_tls']:.1f}\n"
            )
            f.write(f"- **Max Links per TLS:** {tls_stats['max_links_per_tls']}\n")
            f.write(f"- **Max Phases per TLS:** {tls_stats['max_phases_per_tls']}\n\n")

            if start_edge and goal_edge:
                route_stats = self.calculate_route_statistics(start_edge, goal_edge)
                if "error" not in route_stats:
                    f.write("## Experimental Route Details\n\n")
                    f.write(f"- **Start Edge:** `{route_stats['start_edge']}`\n")
                    f.write(f"- **Goal Edge:** `{route_stats['goal_edge']}`\n")
                    f.write(
                        f"- **Start Coordinates:** ({route_stats['start_coordinates'][0]:.2f}, {route_stats['start_coordinates'][1]:.2f})\n"
                    )
                    f.write(
                        f"- **Goal Coordinates:** ({route_stats['goal_coordinates'][0]:.2f}, {route_stats['goal_coordinates'][1]:.2f})\n"
                    )
                    f.write(
                        f"- **Straight-Line Distance:** {route_stats['straight_line_distance_km']:.2f} km ({route_stats['straight_line_distance_m']:.0f} m)\n"
                    )
                    f.write(
                        f"- **Start Speed Limit:** {route_stats['start_speed_limit_kmh']:.1f} km/h\n"
                    )
                    f.write(
                        f"- **Goal Speed Limit:** {route_stats['goal_speed_limit_kmh']:.1f} km/h\n\n"
                    )

            f.write("## Traffic Scenarios\n\n")
            f.write("| Scenario | Vehicles | Car % | Bus % | Truck % | Description |\n")
            f.write("|----------|----------|-------|-------|---------|-------------|\n")
            f.write(
                "| Low | 200 | 85% | 8% | 7% | Light traffic, minimal congestion |\n"
            )
            f.write(
                "| Moderate | 500 | 80% | 10% | 10% | Normal conditions (baseline) |\n"
            )
            f.write(
                "| High | 1000 | 75% | 12% | 13% | Heavy traffic, significant congestion |\n"
            )
            f.write(
                "| Severe | 2000 | 70% | 15% | 15% | Gridlock conditions, extreme congestion |\n\n"
            )

            f.write("## Emergency Severity Levels\n\n")
            f.write("| Level | Weight Shift | Max Speed | Description |\n")
            f.write("|-------|--------------|-----------|-------------|\n")
            f.write(
                "| CRITICAL | +15% time priority | 100-120 km/h | Life-threatening, maximum urgency |\n"
            )
            f.write(
                "| HIGH | +8% time priority | 80-100 km/h | Urgent response, high priority (default) |\n"
            )
            f.write(
                "| MEDIUM | 0% shift | 60-80 km/h | Non-critical, standard priority |\n\n"
            )

            f.write("## Reproducibility Information\n\n")
            f.write("- **SUMO Version:** 1.25.0\n")
            f.write("- **Simulation Step Length:** 1.0 second\n")
            f.write("- **Random Seeds:** Configurable per experiment\n")
            f.write("- **Speed Factor:** 1.2 (allows 20% over speed limit)\n")
            f.write(
                "- **Detection Range:** 500 meters (for traffic light preemption)\n\n"
            )

            f.write("---\n\n")
            f.write(
                "*This report provides the detailed scenario information required for reproducible research.*\n"
            )

        print(f"✓ Network statistics report generated: {output_file}")

    def print_summary(self):
        """Print summary statistics to console."""
        basic_stats = self.get_basic_statistics()
        edge_stats = self.get_edge_statistics()
        tls_stats = self.get_traffic_light_statistics()

        print("=" * 80)
        print("NETWORK STATISTICS SUMMARY")
        print("=" * 80)
        print(f"\nBasic Counts:")
        print(f"  Edges: {basic_stats['road_edges']:,}")
        print(f"  Nodes: {basic_stats['total_nodes']:,}")
        print(f"  Traffic Lights: {basic_stats['traffic_lights']:,}")
        print(f"\nNetwork Size:")
        print(f"  Total Length: {edge_stats['total_network_length_km']:.2f} km")
        print(f"  Average Edge: {edge_stats['average_edge_length_m']:.0f} m")
        print(
            f"  Average Speed Limit: {edge_stats['average_speed_limit_kmh']:.1f} km/h"
        )
        print(f"\nTraffic Control:")
        print(f"  Traffic Lights: {tls_stats['total_traffic_lights']:,}")
        print(f"  Avg Links per TLS: {tls_stats['average_links_per_tls']:.1f}")
        print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract and document SUMO network statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic statistics
  python network_statistics.py
  
  # Generate detailed report
  python network_statistics.py --report network_stats.md
  
  # Include route analysis
  python network_statistics.py --report network_stats.md --start 449595758 --goal 663480498#3
        """,
    )

    parser.add_argument(
        "--network",
        type=str,
        default="../data/network/bangalore.net.xml",
        help="Path to SUMO network file",
    )
    parser.add_argument("--report", type=str, help="Generate markdown report")
    parser.add_argument("--start", type=str, help="Start edge for route analysis")
    parser.add_argument("--goal", type=str, help="Goal edge for route analysis")

    args = parser.parse_args()

    # Resolve network path
    if not os.path.isabs(args.network):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        args.network = os.path.join(script_dir, args.network)

    if not os.path.exists(args.network):
        print(f"Error: Network file not found: {args.network}")
        return 1

    # Analyze network
    analyzer = NetworkAnalyzer(args.network)

    # Print summary
    analyzer.print_summary()

    # Generate report if requested
    if args.report:
        analyzer.generate_report(args.report, args.start, args.goal)

    return 0


if __name__ == "__main__":
    sys.exit(main())
