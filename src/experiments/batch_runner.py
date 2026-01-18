"""
Batch Experiment Runner for All Algorithm Comparisons

Runs comprehensive experiments across all combinations of:
- Algorithms: 6 (Adaptive A*, Standard A*, Dijkstra, CH, CHWrapper, ALT)
- Traffic Levels: 4 (low, moderate, high, severe)
- Routes: 3 different origin-destination pairs

Note: Severity parameter (CRITICAL, HIGH, MEDIUM) only applies to Adaptive A*

Experiment Matrix:
- Adaptive A*: 3 severities × 4 traffic × 3 routes = 36 configs
- Other algorithms: 4 traffic × 3 routes = 12 configs each × 5 = 60 configs
- Total: 96 experiments (deterministic, single run per configuration)

Note: Uses deterministic simulations with fixed traffic patterns.
Each configuration produces consistent, reproducible results.

Author: Emergency Vehicle Routing Research Team
License: MIT
Version: 1.0.0
"""

import sys
import json
import time
import subprocess
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


# Setup logging with UTF-8 encoding for Windows compatibility
import io

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.StreamHandler(
            io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        ),
    ],
)
logger = logging.getLogger(__name__)


class BatchExperimentRunner:
    """Runs all algorithm combinations and collects results."""

    def __init__(
        self,
        algorithms: Optional[List[str]] = None,
        traffic_levels: Optional[List[str]] = None,
        severities: Optional[List[str]] = None,
        routes: Optional[List[Dict]] = None,
        gui: bool = True,
        max_workers: int = 1,
        cooldown: int = 30,
    ):
        """
        Initialize batch runner.

        Args:
            algorithms: List of algorithm names to run (default: all)
            traffic_levels: List of traffic levels (default: all)
            severities: List of severities for adaptive_astar (default: all)
            routes: List of route dicts with start/goal (default: predefined 3)
            gui: Whether to show SUMO GUI (default: True)
            max_workers: Number of parallel workers (default: 1, sequential)
            cooldown: Seconds to wait between experiments (default: 30)
        """
        self.results = []
        self.gui = gui
        self.max_workers = max_workers
        self.cooldown = cooldown

        # Algorithm scripts mapping (in algorithms/ directory)
        all_algorithms = {
            "adaptive_astar": "../algorithms/adaptive_astar.py",
            "standard_astar": "../algorithms/standard_astar.py",
            "dijkstra": "../algorithms/dijkstra.py",
            "ch": "../algorithms/ch.py",
            "chwrapper": "../algorithms/chwrapper.py",
            "alt": "../algorithms/alt.py",
        }

        # Filter algorithms if specified
        if algorithms:
            self.algorithms = {
                k: v for k, v in all_algorithms.items() if k in algorithms
            }
        else:
            self.algorithms = all_algorithms

        # Experiment parameters
        self.severities = severities if severities else ["CRITICAL", "HIGH", "MEDIUM"]
        self.traffic_levels = (
            traffic_levels if traffic_levels else ["low", "moderate", "high", "severe"]
        )

        # Route pairs (use provided or default to 3 routes)
        if routes:
            self.routes = routes
        else:
            self.routes = [
                {"name": "Route 1", "start": "290640275#1", "goal": "40692890#6"},
                {"name": "Route 2", "start": "-1213264717", "goal": "23542229#4"},
                {"name": "Route 3", "start": "-1213264717", "goal": "40692890#6"},
            ]

    def run_single_experiment(
        self, algorithm: str, severity: str, traffic: str, route: Dict
    ) -> Dict:
        """
        Run a single experiment configuration.

        Args:
            algorithm: Algorithm name
            severity: Emergency severity (only used for adaptive_astar)
            traffic: Traffic level
            route: Route dictionary with start/goal

        Returns:
            Result dictionary with comprehensive metrics
        """
        script_relative_path = self.algorithms[algorithm]

        # Display info
        if algorithm == "adaptive_astar":
            logger.info(f"{'='*80}")
            logger.info(
                f"{algorithm.upper()} | {severity} | {traffic.upper()} | {route['name']}"
            )
            logger.info(f"{'='*80}")
        else:
            logger.info(f"{'='*80}")
            logger.info(f"{algorithm.upper()} | {traffic.upper()} | {route['name']}")
            logger.info(f"{'='*80}")

        # Build command (severity only for adaptive_astar)
        # Get absolute path to script
        script_dir = Path(__file__).resolve().parent
        script_absolute_path = (script_dir / script_relative_path).resolve()
        script_working_directory = script_absolute_path.parent

        command = [
            sys.executable,
            str(script_absolute_path),
            "--start",
            route["start"],
            "--goal",
            route["goal"],
            "--traffic",
            traffic,
        ]

        # Add severity only for adaptive_astar
        if algorithm == "adaptive_astar":
            command.extend(["--severity", severity])

        # Add no-gui flag if specified
        if not self.gui:
            command.append("--no-gui")

        # Initialize metrics to capture
        wall_clock_start = time.time()
        success = False
        travel_time_seconds = None
        total_distance_km = None
        average_speed_kmh = None
        traffic_lights_count = None
        route_edges_count = None
        arrival_reason = None
        error_message = None

        try:
            # Run subprocess with real-time output streaming
            logger.info(f"Running command: {' '.join(command)}")
            logger.info(f"Working directory: {script_working_directory}")

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(script_working_directory),
                bufsize=1,
                universal_newlines=True,
            )

            # Capture output in real-time and parse metrics
            output_lines = []

            # Read stdout line by line
            for line in process.stdout:
                line = line.rstrip()
                if line:
                    logger.info(f"  {line}")
                    output_lines.append(line)

                    # Parse travel time
                    if "Travel time:" in line:
                        try:
                            travel_time_seconds = float(
                                line.split("Travel time:")[1].split("s")[0].strip()
                            )
                            success = True
                        except:
                            pass

                    # Parse total distance
                    if "Total distance:" in line or "distance:" in line.lower():
                        try:
                            if "Total distance:" in line:
                                total_distance_km = float(
                                    line.split("Total distance:")[1]
                                    .split("km")[0]
                                    .strip()
                                )
                            elif "Distance:" in line and "km" in line:
                                # Handle progress updates like "Distance: 2.34km"
                                parts = line.split("Distance:")
                                if len(parts) > 1:
                                    dist_str = parts[1].split("km")[0].strip()
                                    if dist_str.replace(".", "").isdigit():
                                        total_distance_km = float(dist_str)
                        except:
                            pass

                    # Parse average speed
                    if "Average speed:" in line or "average speed:" in line.lower():
                        try:
                            avg_speed_str = (
                                line.split("speed:")[1].split("km/h")[0].strip()
                            )
                            average_speed_kmh = float(avg_speed_str)
                        except:
                            pass

                    # Parse traffic lights (different phrasing for adaptive vs baselines)
                    if "Traffic lights" in line:
                        try:
                            if "preempted:" in line:
                                traffic_lights_count = int(
                                    line.split("preempted:")[1].strip()
                                )
                            elif "crossed:" in line:
                                traffic_lights_count = int(
                                    line.split("crossed:")[1].strip()
                                )
                        except:
                            pass

                    # Parse route edges count
                    if "SUMO computed route:" in line and "edges" in line:
                        try:
                            route_edges_count = int(
                                line.split("route:")[1].split("edges")[0].strip()
                            )
                        except:
                            pass

                    # Parse arrival reason
                    if "Arrival reason:" in line:
                        try:
                            arrival_reason = line.split("Arrival reason:")[1].strip()
                        except:
                            pass

            # Wait for process to complete
            process.wait()

            # Get any stderr output
            stderr_output = process.stderr.read()
            if stderr_output:
                logger.error(f"STDERR: {stderr_output}")

            wall_clock_time_seconds = time.time() - wall_clock_start

            if not success and process.returncode != 0:
                error_message = (
                    stderr_output[:200]
                    if stderr_output
                    else "Process failed with non-zero exit code"
                )
                logger.error(f"ERROR: {error_message}")
            elif not success:
                error_message = "Could not parse travel time from output"
                logger.warning(f"WARNING: {error_message}")

        except Exception as e:
            wall_clock_time_seconds = time.time() - wall_clock_start
            error_message = f"Exception: {str(e)}"
            logger.exception(f"ERROR running experiment: {e}")

        # Return comprehensive results
        result = {
            "algorithm": algorithm,
            "severity": severity,
            "traffic": traffic,
            "route_name": route["name"],
            "route_start": route["start"],
            "route_goal": route["goal"],
            "success": success,
            "travel_time_seconds": travel_time_seconds,
            "travel_time_minutes": (
                round(travel_time_seconds / 60, 2) if travel_time_seconds else None
            ),
            "total_distance_km": total_distance_km,
            "average_speed_kmh": average_speed_kmh,
            "traffic_lights_count": traffic_lights_count,
            "route_edges_count": route_edges_count,
            "arrival_reason": arrival_reason,
            "wall_clock_time_seconds": wall_clock_time_seconds,
            "error": error_message,
            "timestamp": datetime.now().isoformat(),
        }

        return result

    def run_all_experiments(self):
        """Run all experiment combinations."""
        # Calculate total experiments
        adaptive_configs = (
            len(self.severities) * len(self.traffic_levels) * len(self.routes)
        )
        baseline_configs = (
            len(self.traffic_levels) * len(self.routes) * (len(self.algorithms) - 1)
        )
        total_configs = (
            adaptive_configs + baseline_configs
            if "adaptive_astar" in self.algorithms
            else baseline_configs
        )

        logger.info("#" * 80)
        logger.info("BATCH EXPERIMENT RUNNER")
        logger.info("#" * 80)
        logger.info(
            f"Algorithms: {len(self.algorithms)} - {', '.join(self.algorithms.keys())}"
        )
        logger.info(
            f"Traffic Levels: {len(self.traffic_levels)} - {', '.join(self.traffic_levels)}"
        )
        logger.info(f"Routes: {len(self.routes)}")
        logger.info(f"GUI Mode: {'Enabled' if self.gui else 'Disabled (no-gui)'}")
        logger.info(f"Parallel Workers: {self.max_workers}")
        logger.info(f"Cooldown: {self.cooldown}s between experiments")
        logger.info(f"Total experiments: {total_configs}")
        logger.info("#" * 80)

        start_time = time.time()
        completed = 0

        # Run all combinations
        for algorithm in self.algorithms.keys():
            # Adaptive A* tests all severities
            if algorithm == "adaptive_astar":
                for severity in self.severities:
                    for traffic in self.traffic_levels:
                        for route in self.routes:
                            completed += 1
                            logger.info(
                                f"[{completed}/{total_configs}] Running: {algorithm} | {severity} | {traffic} | {route['name']}"
                            )

                            result = self.run_single_experiment(
                                algorithm=algorithm,
                                severity=severity,
                                traffic=traffic,
                                route=route,
                            )
                            self.results.append(result)

                            # Progress update
                            elapsed = time.time() - start_time
                            avg_time = elapsed / completed

                            status = "[OK]" if result["success"] else "[FAIL]"
                            logger.info(
                                f"{status} Completed {completed}/{total_configs} | "
                                f"Elapsed: {elapsed/60:.1f}min | "
                                f"Avg: {avg_time:.1f}s/config"
                            )

                            # Cooldown period between experiments
                            if completed < total_configs and self.cooldown > 0:
                                logger.info(
                                    f"   Cooling down for {self.cooldown} seconds before next run..."
                                )
                                time.sleep(self.cooldown)

            # Other algorithms: no severity parameter
            else:
                for traffic in self.traffic_levels:
                    for route in self.routes:
                        completed += 1
                        logger.info(
                            f"[{completed}/{total_configs}] Running: {algorithm} | {traffic} | {route['name']}"
                        )

                        result = self.run_single_experiment(
                            algorithm=algorithm,
                            severity="N/A",  # Not applicable
                            traffic=traffic,
                            route=route,
                        )
                        self.results.append(result)

                        # Progress update
                        elapsed = time.time() - start_time
                        avg_time = elapsed / completed

                        status = "[OK]" if result["success"] else "[FAIL]"
                        logger.info(
                            f"{status} Completed {completed}/{total_configs} | "
                            f"Elapsed: {elapsed/60:.1f}min | "
                            f"Avg: {avg_time:.1f}s/config"
                        )

                        # Cooldown period between experiments
                        if completed < total_configs and self.cooldown > 0:
                            logger.info(
                                f"   Cooling down for {self.cooldown} seconds before next run..."
                            )
                            time.sleep(self.cooldown)

        total_time = time.time() - start_time
        successful = sum(1 for r in self.results if r["success"])

        logger.info(f"{'='*80}")
        logger.info(f"ALL EXPERIMENTS COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(
            f"Total time: {total_time/60:.1f} minutes ({total_time/3600:.2f} hours)"
        )
        logger.info(f"Successful: {successful}/{total_configs}")
        logger.info(f"Failed: {total_configs - successful}/{total_configs}")
        logger.info(f"{'='*80}")

    def save_results(self, output_file: str):
        """Save results to JSON file."""
        output_path = Path(output_file)

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_experiments": len(self.results),
                "algorithms": list(self.algorithms.keys()),
                "severities": self.severities,
                "traffic_levels": self.traffic_levels,
                "routes": self.routes,
                "gui_mode": self.gui,
                "max_workers": self.max_workers,
            },
            "results": self.results,
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"[OK] Results saved to: {output_path}")


def parse_algorithms(args_algorithms: Optional[List[str]]) -> Optional[List[str]]:
    """Parse algorithm arguments with special keywords."""
    if not args_algorithms:
        return None

    all_algorithms = [
        "adaptive_astar",
        "standard_astar",
        "dijkstra",
        "ch",
        "chwrapper",
        "alt",
    ]
    baselines = ["standard_astar", "dijkstra", "ch", "chwrapper", "alt"]

    # Handle special keywords
    if "all" in args_algorithms:
        return all_algorithms
    if "baselines" in args_algorithms:
        return baselines

    return args_algorithms


def parse_traffic(args_traffic: Optional[List[str]]) -> Optional[List[str]]:
    """Parse traffic arguments with special keywords."""
    if not args_traffic:
        return None

    # Handle special keywords
    if "all" in args_traffic:
        return ["low", "moderate", "high", "severe"]
    if "light" in args_traffic:
        return ["low", "moderate"]
    if "heavy" in args_traffic:
        return ["high", "severe"]

    return args_traffic


def parse_severities(args_severities: Optional[List[str]]) -> Optional[List[str]]:
    """Parse severity arguments with special keywords."""
    if not args_severities:
        return None

    # Handle special keywords
    if "all" in args_severities:
        return ["CRITICAL", "HIGH", "MEDIUM"]

    return args_severities


def parse_routes(route_strings: List[str]) -> List[Dict]:
    """
    Parse route strings into route dictionaries.

    Args:
        route_strings: List of "start:goal:name" strings

    Returns:
        List of route dictionaries
    """
    routes = []
    for i, route_str in enumerate(route_strings):
        parts = route_str.split(":")
        if len(parts) == 2:
            routes.append({"name": f"Route {i+1}", "start": parts[0], "goal": parts[1]})
        elif len(parts) == 3:
            routes.append({"name": parts[2], "start": parts[0], "goal": parts[1]})
        else:
            logger.warning(
                f"Invalid route format: {route_str}. Use 'start:goal' or 'start:goal:name'"
            )

    return routes


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run comprehensive batch experiments for all routing algorithms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all algorithms with all configs (GUI mode)
  python batch_runner.py
  
  # Run only adaptive_astar with light traffic, no GUI
  python batch_runner.py --algorithms adaptive_astar --traffic light --no-gui
  
  # Run baselines (all except adaptive_astar) with heavy traffic
  python batch_runner.py --algorithms baselines --traffic heavy
  
  # Run specific algorithms
  python batch_runner.py --algorithms adaptive_astar dijkstra ch
  
  # All traffic levels, specific algorithms
  python batch_runner.py --algorithms all --traffic all
  
  # Custom route, single traffic level
  python batch_runner.py --routes "290640275#1:40692890#6:Hospital" --traffic low
  
  # Fast run: no GUI, short cooldown
  python batch_runner.py --no-gui --cooldown 5
  
Keywords:
  --algorithms:  all, baselines, or specific names
  --traffic:     all, light (low+moderate), heavy (high+severe), or specific levels
  --severities:  all, or CRITICAL, HIGH, MEDIUM
  
Route Format:
  start_edge:goal_edge:route_name  or  start_edge:goal_edge
        """,
    )

    parser.add_argument(
        "--output",
        type=str,
        default="../../results/batch_results.json",
        help="Output JSON file for results",
    )

    parser.add_argument(
        "--algorithms",
        nargs="+",
        metavar="ALG",
        help="Algorithms to run. Options: adaptive_astar, standard_astar, dijkstra, ch, chwrapper, alt, "
        "all (all 6), baselines (all except adaptive_astar). Space-separated.",
    )

    parser.add_argument(
        "--traffic",
        nargs="+",
        metavar="LEVEL",
        help="Traffic levels. Options: low, moderate, high, severe, "
        "all (all 4), light (low+moderate), heavy (high+severe). Space-separated.",
    )

    parser.add_argument(
        "--severities",
        nargs="+",
        metavar="SEV",
        help="Severities for adaptive_astar. Options: CRITICAL, HIGH, MEDIUM, all (all 3). Space-separated.",
    )

    parser.add_argument(
        "--routes",
        nargs="+",
        metavar="ROUTE",
        help='Routes in format "start:goal" or "start:goal:name". Space-separated.',
    )

    parser.add_argument(
        "--no-gui", action="store_true", help="Run without SUMO GUI (faster execution)"
    )

    parser.add_argument(
        "--cooldown",
        type=int,
        default=30,
        help="Seconds to wait between experiments (default: 30)",
    )

    args = parser.parse_args()

    # Parse arguments with special keyword support
    parsed_algorithms = parse_algorithms(args.algorithms)
    parsed_traffic = parse_traffic(args.traffic)
    parsed_severities = parse_severities(args.severities)

    # Parse custom routes if provided
    custom_routes = None
    if args.routes:
        custom_routes = parse_routes(args.routes)
        logger.info(f"Using {len(custom_routes)} custom routes")

    # Log configuration
    if parsed_algorithms:
        logger.info(f"Running algorithms: {', '.join(parsed_algorithms)}")
    if parsed_traffic:
        logger.info(f"Traffic levels: {', '.join(parsed_traffic)}")
    if parsed_severities:
        logger.info(f"Severities: {', '.join(parsed_severities)}")

    # Run experiments
    runner = BatchExperimentRunner(
        algorithms=parsed_algorithms,
        traffic_levels=parsed_traffic,
        severities=parsed_severities,
        routes=custom_routes,
        gui=not args.no_gui,
        max_workers=1,  # Sequential execution only
        cooldown=args.cooldown,
    )
    runner.run_all_experiments()

    # Save results
    runner.save_results(args.output)

    logger.info("=" * 80)
    logger.info(f"Results saved to: {args.output}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
