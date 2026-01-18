"""
Batch Results Analysis Tool

Analyzes comprehensive experiment results and generates:
- Statistical summaries with confidence intervals
- Comparative performance tables
- Paper-ready LaTeX tables
- Visualization data

Author: Emergency Vehicle Routing Research Team
License: MIT
Version: 1.0.0
"""

import json
import statistics
import math
from typing import Dict, List, Tuple
from datetime import datetime
from scipy import stats
import numpy as np


class BatchResultsAnalyzer:
    """Analyzes batch experiment results."""

    def __init__(self, results_file: str):
        """
        Initialize analyzer with results file.

        Args:
            results_file: Path to batch results JSON
        """
        with open(results_file, "r") as f:
            data = json.load(f)

        self.metadata = data["metadata"]
        self.results = data["results"]

        # Filter successful runs
        self.successful_results = [r for r in self.results if r["success"]]

        print(f"✓ Loaded {len(self.results)} results")
        print(f"  Successful: {len(self.successful_results)}")
        print(f"  Failed: {len(self.results) - len(self.successful_results)}")

    def confidence_interval(
        self, data: List[float], confidence: float = 0.95
    ) -> Tuple[float, float]:
        """
        Calculate confidence interval (returns (0,0) for deterministic single-run data).

        Args:
            data: List of values
            confidence: Confidence level (default 0.95 for 95% CI)

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if len(data) < 2:
            return (0, 0)

        n = len(data)
        mean = statistics.mean(data)
        std_err = statistics.stdev(data) / math.sqrt(n)

        # t-distribution for small samples
        t_value = stats.t.ppf((1 + confidence) / 2, n - 1)
        margin = t_value * std_err

        return (mean - margin, mean + margin)

    def group_results(self) -> Dict:
        """Group results by algorithm, severity (for adaptive_astar), traffic, route."""
        grouped = {}

        for result in self.successful_results:
            # For baseline algorithms, ignore severity (set to N/A)
            severity = (
                result["severity"] if result["algorithm"] == "adaptive_astar" else "N/A"
            )

            key = (
                result["algorithm"],
                severity,
                result["traffic"],
                result["route_name"],
            )

            if key not in grouped:
                grouped[key] = {"travel_times": [], "computation_times": []}

            grouped[key]["travel_times"].append(result["travel_time_seconds"])
            grouped[key]["computation_times"].append(result["wall_clock_time_seconds"])

        return grouped

    def calculate_statistics(self, grouped: Dict) -> Dict:
        """Calculate statistics for each group."""
        stats_data = {}

        for key, data in grouped.items():
            algorithm, severity, traffic, route = key

            travel_times = data["travel_times"]
            comp_times = data["computation_times"]

            if len(travel_times) > 0:
                # For single-run deterministic data, mean = the single value
                travel_mean = (
                    statistics.mean(travel_times) if len(travel_times) > 0 else 0
                )
                stats_data[key] = {
                    "algorithm": algorithm,
                    "severity": severity,
                    "traffic": traffic,
                    "route": route,
                    "n": len(travel_times),
                    "travel_time_mean": travel_mean,
                    "travel_time_std": (
                        statistics.stdev(travel_times) if len(travel_times) > 1 else 0
                    ),
                    "travel_time_min": min(travel_times),
                    "travel_time_max": max(travel_times),
                    "travel_time_ci": self.confidence_interval(travel_times),
                    "computation_time_mean": (
                        statistics.mean(comp_times) if len(comp_times) > 0 else 0
                    ),
                    "computation_time_std": (
                        statistics.stdev(comp_times) if len(comp_times) > 1 else 0
                    ),
                }

        return stats_data

    def perform_t_tests(self, stats_data: Dict) -> Dict:
        """Compare Adaptive A* vs baselines (deterministic comparison, no t-tests for single runs)."""
        comparisons = {}

        # Group by severity, traffic, route
        for severity in self.metadata["severities"]:
            for traffic in self.metadata["traffic_levels"]:
                for route in self.metadata["routes"]:
                    route_name = route["name"]

                    # Get adaptive A* data
                    adaptive_key = ("adaptive_astar", severity, traffic, route_name)
                    if adaptive_key not in stats_data:
                        continue

                    # Find matching data from results
                    adaptive_times = [
                        r["travel_time_seconds"]
                        for r in self.successful_results
                        if r["algorithm"] == "adaptive_astar"
                        and r["severity"] == severity
                        and r["traffic"] == traffic
                        and r["route_name"] == route_name
                    ]

                    if len(adaptive_times) < 1:
                        continue

                    # Compare with each baseline
                    for algorithm in self.metadata["algorithms"]:
                        if algorithm == "adaptive_astar":
                            continue

                        # Baseline algorithms use 'N/A' for severity in grouping
                        baseline_key = (algorithm, "N/A", traffic, route_name)
                        if baseline_key not in stats_data:
                            continue

                        # Get baseline data (baselines don't filter by severity)
                        baseline_times = [
                            r["travel_time_seconds"]
                            for r in self.successful_results
                            if r["algorithm"] == algorithm
                            and r["traffic"] == traffic
                            and r["route_name"] == route_name
                        ]

                        if len(baseline_times) < 1:
                            continue

                        # For deterministic single-run data, just compare means (no statistical test)
                        adaptive_mean = statistics.mean(adaptive_times)
                        baseline_mean = statistics.mean(baseline_times)

                        # Skip t-test and Cohen's d for single values
                        if len(adaptive_times) > 1 and len(baseline_times) > 1:
                            t_statistic, p_value = stats.ttest_ind(
                                adaptive_times, baseline_times
                            )
                            pooled_std = math.sqrt(
                                (
                                    statistics.stdev(adaptive_times) ** 2
                                    + statistics.stdev(baseline_times) ** 2
                                )
                                / 2
                            )
                            cohens_d = (adaptive_mean - baseline_mean) / pooled_std
                        else:
                            # Deterministic comparison - no statistical test
                            t_statistic = 0
                            p_value = 1.0  # N/A for single values
                            cohens_d = 0

                        comparison_key = (algorithm, severity, traffic, route_name)
                        comparisons[comparison_key] = {
                            "baseline_algorithm": algorithm,
                            "severity": severity,
                            "traffic": traffic,
                            "route": route_name,
                            "adaptive_mean": adaptive_mean,
                            "baseline_mean": baseline_mean,
                            "difference": adaptive_mean - baseline_mean,
                            "improvement_pct": (
                                ((baseline_mean - adaptive_mean) / baseline_mean) * 100
                                if baseline_mean > 0
                                else 0
                            ),
                            "t_statistic": t_statistic,
                            "p_value": p_value,
                            "significant": (
                                p_value < 0.05 if len(adaptive_times) > 1 else False
                            ),
                            "cohens_d": cohens_d,
                            "effect_size": (
                                self._interpret_effect_size(abs(cohens_d))
                                if len(adaptive_times) > 1
                                else "N/A"
                            ),
                        }

        return comparisons

    def _interpret_effect_size(self, d: float) -> str:
        """Interpret Cohen's d effect size."""
        if d < 0.2:
            return "negligible"
        elif d < 0.5:
            return "small"
        elif d < 0.8:
            return "medium"
        else:
            return "large"

    def generate_markdown_report(self, output_file: str):
        """Generate comprehensive markdown report."""
        grouped = self.group_results()
        stats_data = self.calculate_statistics(grouped)
        comparisons = self.perform_t_tests(stats_data)

        with open(output_file, "w") as f:
            f.write("# Comprehensive Algorithm Comparison Analysis\n\n")
            f.write(
                f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )
            f.write(f"**Total Experiments:** {len(self.results)}\n")
            f.write(f"**Successful:** {len(self.successful_results)}\n")
            f.write(f"**Failed:** {len(self.results) - len(self.successful_results)}\n")
            f.write(
                f"**Note:** Deterministic simulations with fixed traffic patterns (single run per config)\n\n"
            )

            # Overall performance comparison
            f.write("## Overall Performance Comparison\n\n")
            f.write("### Travel Times by Algorithm (seconds)\n\n")
            f.write("| Algorithm | Time (s) | Configs |\n")
            f.write("|-----------|----------|---------|\n")

            # Calculate overall stats per algorithm
            algo_overall = {}
            for key, stat in stats_data.items():
                algo = stat["algorithm"]
                if algo not in algo_overall:
                    algo_overall[algo] = []
                algo_overall[algo].append(stat["travel_time_mean"])

            for algo in sorted(algo_overall.keys()):
                times = algo_overall[algo]
                mean = statistics.mean(times)

                f.write(f"| {algo} | {mean:.2f} | {len(times)} |\n")

            # Statistical comparison tables
            f.write("\n## Statistical Comparisons\n\n")

            # For each traffic level, compare adaptive_astar (with severities) vs baselines (without)
            for traffic in self.metadata["traffic_levels"]:
                f.write(f"\n### {traffic.upper()} Traffic Conditions\n\n")

                # Compare each severity of adaptive_astar against baseline averages
                for severity in self.metadata["severities"]:
                    f.write(f"\n#### Adaptive A* ({severity}) vs Baselines\n\n")
                    f.write(
                        "| Baseline Algorithm | Route | Adaptive (s) | Baseline (s) | Difference | Improvement % |\n"
                    )
                    f.write(
                        "|-------------------|-------|--------------|--------------|------------|---------------|\n"
                    )

                    # For each baseline algorithm
                    for baseline_algo in self.metadata["algorithms"]:
                        if baseline_algo == "adaptive_astar":
                            continue

                        # Compare across routes
                        for route in self.metadata["routes"]:
                            route_name = route["name"]

                            # Get adaptive_astar data for this severity
                            adaptive_key = (
                                "adaptive_astar",
                                severity,
                                traffic,
                                route_name,
                            )
                            baseline_key = (baseline_algo, "N/A", traffic, route_name)

                            comp_key = (baseline_algo, severity, traffic, route_name)
                            if comp_key in comparisons:
                                comp = comparisons[comp_key]
                                f.write(
                                    f"| {baseline_algo} | {route_name} | {comp['adaptive_mean']:.2f} | "
                                    f"{comp['baseline_mean']:.2f} | {comp['difference']:+.2f}s | "
                                    f"{comp['improvement_pct']:+.1f}% |\n"
                                )

                    f.write("\n")

            # Summary statistics
            f.write("\n## Summary Statistics\n\n")

            # Calculate overall improvements
            all_improvements = [c["improvement_pct"] for c in comparisons.values()]
            significant_improvements = [
                c["improvement_pct"] for c in comparisons.values() if c["significant"]
            ]

            if len(all_improvements) > 0:
                f.write(f"**Overall Performance (Deterministic Comparison):**\n")
                f.write(
                    f"- Mean improvement: {statistics.mean(all_improvements):.2f}%\n"
                )
                f.write(
                    f"- Median improvement: {statistics.median(all_improvements):.2f}%\n"
                )
                f.write(f"- Best improvement: {max(all_improvements):.2f}%\n")
                f.write(f"- Worst case: {min(all_improvements):.2f}%\n")
                f.write(f"- Comparisons: {len(all_improvements)} configurations\n\n")

            f.write("\n---\n\n")
            f.write("**Notes:**\n")
            f.write("- Positive improvement % means Adaptive A* is faster\n")
            f.write(
                "- Results are from deterministic simulations with fixed traffic patterns\n"
            )
            f.write("- Each configuration ran once (no statistical variance)\n")

        print(f"✓ Markdown report generated: {output_file}")

    def generate_latex_table(self, output_file: str):
        """Generate LaTeX tables for paper."""
        grouped = self.group_results()
        stats_data = self.calculate_statistics(grouped)

        with open(output_file, "w") as f:
            f.write("% Algorithm Comparison Table for Research Paper\n")
            f.write(
                "% Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n"
            )

            f.write("\\begin{table}[htbp]\n")
            f.write("\\centering\n")
            f.write("\\caption{Comparative Performance of Routing Algorithms}\n")
            f.write("\\label{tab:algorithm_comparison}\n")
            f.write("\\begin{tabular}{llcccc}\n")
            f.write("\\hline\n")
            f.write(
                "Algorithm & Condition & Mean (s) & Std Dev & 95\\% CI & Improvement \\\\\n"
            )
            f.write("\\hline\n")

            # Group by traffic and severity
            for traffic in self.metadata["traffic_levels"]:
                for severity in self.metadata["severities"]:
                    f.write(
                        f"\\multicolumn{{6}}{{l}}{{\\textbf{{{severity} / {traffic.upper()}}}}} \\\\\n"
                    )

                    # Get adaptive baseline
                    adaptive_key = None
                    for key in stats_data.keys():
                        if (
                            key[0] == "adaptive_astar"
                            and key[1] == severity
                            and key[2] == traffic
                        ):
                            adaptive_key = key
                            break

                    if adaptive_key:
                        adaptive_stat = stats_data[adaptive_key]
                        adaptive_mean = adaptive_stat["travel_time_mean"]
                        ci = adaptive_stat["travel_time_ci"]

                        f.write(
                            f"Adaptive A* & Baseline & {adaptive_mean:.2f} & "
                            f"{adaptive_stat['travel_time_std']:.2f} & "
                            f"[{ci[0]:.2f}, {ci[1]:.2f}] & -- \\\\\n"
                        )

                        # Other algorithms
                        for algo in self.metadata["algorithms"]:
                            if algo == "adaptive_astar":
                                continue

                            algo_key = None
                            for key in stats_data.keys():
                                if (
                                    key[0] == algo
                                    and key[1] == severity
                                    and key[2] == traffic
                                ):
                                    algo_key = key
                                    break

                            if algo_key:
                                algo_stat = stats_data[algo_key]
                                algo_mean = algo_stat["travel_time_mean"]
                                improvement = (
                                    (algo_mean - adaptive_mean) / algo_mean
                                ) * 100
                                ci = algo_stat["travel_time_ci"]

                                algo_name = algo.replace("_", " ").title()
                                f.write(
                                    f"{algo_name} & & {algo_mean:.2f} & "
                                    f"{algo_stat['travel_time_std']:.2f} & "
                                    f"[{ci[0]:.2f}, {ci[1]:.2f}] & {improvement:+.1f}\\% \\\\\n"
                                )

                    f.write("\\hline\n")

            f.write("\\end{tabular}\n")
            f.write("\\end{table}\n\n")

            f.write("% Note: Positive improvement indicates Adaptive A* is faster\n")

        print(f"✓ LaTeX table generated: {output_file}")

    def generate_csv_export(self, output_file: str):
        """Export results to CSV for further analysis."""
        import csv

        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(
                [
                    "Algorithm",
                    "Severity",
                    "Traffic",
                    "Route",
                    "Travel Time (s)",
                    "Computation Time (s)",
                    "Success",
                    "Timestamp",
                ]
            )

            # Data rows
            for result in self.results:
                writer.writerow(
                    [
                        result["algorithm"],
                        result["severity"],
                        result["traffic"],
                        result["route_name"],
                        result.get("travel_time_seconds", result.get("travel_time", 0)),
                        result.get(
                            "wall_clock_time_seconds", result.get("computation_time", 0)
                        ),
                        result["success"],
                        result["timestamp"],
                    ]
                )

        print(f"✓ CSV export generated: {output_file}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze batch experiment results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "results_file", type=str, help="Path to batch results JSON file"
    )
    parser.add_argument(
        "--markdown",
        type=str,
        default="../results/analysis_report.md",
        help="Output markdown report file",
    )
    parser.add_argument(
        "--latex",
        type=str,
        default="../results/paper_table.tex",
        help="Output LaTeX table file",
    )
    parser.add_argument(
        "--csv",
        type=str,
        default="../results/results_export.csv",
        help="Output CSV file",
    )

    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("BATCH RESULTS ANALYZER")
    print("=" * 80 + "\n")

    # Analyze results
    analyzer = BatchResultsAnalyzer(args.results_file)

    # Generate reports
    analyzer.generate_markdown_report(args.markdown)
    analyzer.generate_latex_table(args.latex)
    analyzer.generate_csv_export(args.csv)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Markdown: {args.markdown}")
    print(f"LaTeX: {args.latex}")
    print(f"CSV: {args.csv}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
