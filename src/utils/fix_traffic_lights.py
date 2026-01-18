"""
Traffic Light Configuration Diagnostic and Repair Tool

This utility identifies and fixes problematic traffic light configurations
where all signals show the same state (all green or all red simultaneously).

Usage:
    python fix_traffic_lights.py --network path/to/network.net.xml
    python fix_traffic_lights.py --network path/to/network.net.xml --junction-id 10076345214
    python fix_traffic_lights.py --network path/to/network.net.xml --fix --output fixed_network.net.xml

Author: Emergency Vehicle Routing Research Team
"""

import argparse
import logging
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


def analyze_tls_phases(network_file: str, junction_id: str = None) -> List[Dict]:
    """
    Analyze traffic light signal programs for issues.

    Args:
        network_file: Path to SUMO network file
        junction_id: Optional specific junction to check

    Returns:
        List of problematic traffic light configurations
    """
    tree = ET.parse(network_file)
    root = tree.getroot()

    issues = []

    for tlLogic in root.findall("tlLogic"):
        tls_id = tlLogic.get("id")

        # Skip if checking specific junction and this isn't it
        if junction_id and tls_id != junction_id:
            continue

        tls_type = tlLogic.get("type", "static")
        print(f"\n{'='*80}")
        print(f"Analyzing Traffic Light: {tls_id}")
        print(f"Type: {tls_type}")
        print(f"{'='*80}")

        phases = tlLogic.findall("phase")
        if not phases:
            issues.append(
                {
                    "id": tls_id,
                    "type": "NO_PHASES",
                    "description": "Traffic light has no phases defined",
                    "severity": "CRITICAL",
                }
            )
            print(f"[CRITICAL] No phases defined!")
            continue

        print(f"Total phases: {len(phases)}")

        # Analyze each phase
        for idx, phase in enumerate(phases):
            state = phase.get("state", "")
            duration = phase.get("duration", "0")

            print(f"\nPhase {idx + 1}:")
            print(f"  Duration: {duration}s")
            print(f"  State: {state}")

            # Check for all-green (all 'G' or 'g')
            if state and all(c in "Gg" for c in state):
                issues.append(
                    {
                        "id": tls_id,
                        "phase": idx,
                        "type": "ALL_GREEN",
                        "description": f"Phase {idx} has all signals green - potential collision hazard",
                        "severity": "CRITICAL",
                        "state": state,
                        "duration": duration,
                    }
                )
                print(f"  [CRITICAL] ALL SIGNALS GREEN - Collision hazard!")

            # Check for all-red (all 'r')
            elif state and all(c == "r" for c in state):
                issues.append(
                    {
                        "id": tls_id,
                        "phase": idx,
                        "type": "ALL_RED",
                        "description": f"Phase {idx} has all signals red - causes unnecessary delays",
                        "severity": "WARNING",
                        "state": state,
                        "duration": duration,
                    }
                )
                print(f"  [WARNING] ALL SIGNALS RED - Unnecessary delay")

            # Check for very short phases (< 3 seconds)
            try:
                if float(duration) < 3.0:
                    issues.append(
                        {
                            "id": tls_id,
                            "phase": idx,
                            "type": "SHORT_PHASE",
                            "description": f"Phase {idx} duration too short ({duration}s)",
                            "severity": "WARNING",
                            "state": state,
                            "duration": duration,
                        }
                    )
                    print(f"  [WARNING] Phase too short (< 3s)")
            except ValueError:
                pass

            # Count signal types
            green_count = state.count("G") + state.count("g")
            red_count = state.count("r")
            yellow_count = state.count("y")

            print(
                f"  Signals: {green_count} green, {red_count} red, {yellow_count} yellow"
            )

    return issues


def generate_fixed_phases(num_links: int) -> List[Tuple[str, str]]:
    """
    Generate proper traffic light phases for a junction.

    Creates a 4-phase cycle suitable for typical intersections:
    - Phase 1: North-South green (30s)
    - Phase 2: North-South yellow (3s)
    - Phase 3: East-West green (30s)
    - Phase 4: East-West yellow (3s)

    Args:
        num_links: Number of signal links in the junction

    Returns:
        List of (state, duration) tuples
    """
    # Default safe pattern: alternating directions
    if num_links <= 0:
        return []

    # For simplicity, assume first half = NS, second half = EW
    # This is a heuristic and may need manual adjustment
    half = num_links // 2

    phases = []

    # Phase 1: North-South green, East-West red
    state1 = "G" * half + "r" * (num_links - half)
    phases.append((state1, "30"))

    # Phase 2: North-South yellow, East-West red
    state2 = "y" * half + "r" * (num_links - half)
    phases.append((state2, "3"))

    # Phase 3: North-South red, East-West green
    state3 = "r" * half + "G" * (num_links - half)
    phases.append((state3, "30"))

    # Phase 4: North-South red, East-West yellow
    state4 = "r" * half + "y" * (num_links - half)
    phases.append((state4, "3"))

    return phases


def fix_traffic_lights(
    network_file: str, output_file: str, junction_id: str = None
) -> int:
    """
    Fix problematic traffic light configurations.

    Args:
        network_file: Input network file
        output_file: Output network file
        junction_id: Optional specific junction to fix

    Returns:
        Number of traffic lights fixed
    """
    tree = ET.parse(network_file)
    root = tree.getroot()

    fixed_count = 0

    for tlLogic in root.findall("tlLogic"):
        tls_id = tlLogic.get("id")

        # Skip if checking specific junction and this isn't it
        if junction_id and tls_id != junction_id:
            continue

        phases = tlLogic.findall("phase")

        if not phases:
            print(f"[FIX] {tls_id}: No phases - skipping (needs manual configuration)")
            continue

        # Check for problematic phases
        needs_fix = False
        num_links = 0

        for phase in phases:
            state = phase.get("state", "")
            if state:
                num_links = len(state)
                # All green or all red
                if (all(c in "Gg" for c in state)) or (all(c == "r" for c in state)):
                    needs_fix = True
                    break

        if needs_fix and num_links > 0:
            print(f"[FIX] {tls_id}: Regenerating {num_links}-link traffic light phases")

            # Remove old phases
            for phase in phases:
                tlLogic.remove(phase)

            # Add new phases
            new_phases = generate_fixed_phases(num_links)
            for state, duration in new_phases:
                new_phase = ET.SubElement(tlLogic, "phase")
                new_phase.set("duration", duration)
                new_phase.set("state", state)

            fixed_count += 1
            print(f"      Generated {len(new_phases)} phases with proper alternation")

    # Write output
    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"\n[OK] Fixed network written to: {output_file}")
    print(f"[OK] Total traffic lights fixed: {fixed_count}")

    return fixed_count


def main():
    parser = argparse.ArgumentParser(
        description="Traffic Light Configuration Diagnostic and Repair Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze all traffic lights
  python fix_traffic_lights.py --network ../../data/network/bangalore.net.xml
  
  # Analyze specific junction
  python fix_traffic_lights.py --network ../../data/network/bangalore.net.xml --junction-id 10076345214
  
  # Fix issues and save to new file
  python fix_traffic_lights.py --network ../../data/network/bangalore.net.xml --fix --output fixed_network.net.xml
  
  # Fix specific junction only
  python fix_traffic_lights.py --network ../../data/network/bangalore.net.xml --junction-id 10076345214 --fix --output fixed_network.net.xml

Notes:
  - Always backup your network file before applying fixes
  - Fixed phases use a simple 4-phase cycle (NS green, NS yellow, EW green, EW yellow)
  - Complex intersections may require manual adjustment after automated fix
  - Use SUMO's netedit tool for fine-tuning: netedit -s fixed_network.net.xml
        """,
    )

    parser.add_argument(
        "--network",
        type=str,
        default=os.path.join(PROJECT_ROOT, "data", "network", "bangalore.net.xml"),
        help="Path to SUMO network file",
    )

    parser.add_argument(
        "--junction-id",
        type=str,
        help="Specific junction/traffic light ID to analyze (e.g., 10076345214)",
    )

    parser.add_argument(
        "--fix", action="store_true", help="Apply fixes to problematic traffic lights"
    )

    parser.add_argument(
        "--output",
        type=str,
        default=os.path.join(
            PROJECT_ROOT, "data", "network", "bangalore_fixed.net.xml"
        ),
        help="Output file for fixed network (only used with --fix)",
    )

    args = parser.parse_args()

    if not os.path.exists(args.network):
        print(f"[ERROR] Network file not found: {args.network}")
        sys.exit(1)

    print("=" * 80)
    print("TRAFFIC LIGHT CONFIGURATION ANALYSIS")
    print("=" * 80)
    print(f"Network: {args.network}")
    if args.junction_id:
        print(f"Junction ID: {args.junction_id}")
    print("=" * 80)

    # Analyze
    issues = analyze_tls_phases(args.network, args.junction_id)

    # Summary
    print("\n" + "=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)

    if not issues:
        print("[OK] No issues found - all traffic lights appear properly configured")
    else:
        critical = [i for i in issues if i["severity"] == "CRITICAL"]
        warnings = [i for i in issues if i["severity"] == "WARNING"]

        print(f"Total issues: {len(issues)}")
        print(f"  Critical: {len(critical)}")
        print(f"  Warnings: {len(warnings)}")

        print("\nIssue Details:")
        for issue in issues:
            print(f"\n[{issue['severity']}] {issue['id']}")
            print(f"  {issue['description']}")
            if "state" in issue:
                print(f"  State: {issue['state']}")
                print(f"  Duration: {issue['duration']}s")

    # Apply fixes if requested
    if args.fix:
        print("\n" + "=" * 80)
        print("APPLYING FIXES")
        print("=" * 80)

        # Backup warning
        print(f"[WARNING] Creating fixed network file")
        print(f"[WARNING] Original file unchanged: {args.network}")
        print(f"[WARNING] Fixed file will be: {args.output}")

        fixed_count = fix_traffic_lights(args.network, args.output, args.junction_id)

        if fixed_count > 0:
            print("\n[OK] Fixes applied successfully!")
            print("\nNext steps:")
            print(f"1. Review the fixed network: netedit -s {args.output}")
            print(f"2. Test the network with your simulations")
            print(f"3. If satisfied, replace original: cp {args.output} {args.network}")
        else:
            print("\n[INFO] No fixes needed or applied")
    else:
        if issues:
            print("\nTo fix these issues, run with --fix flag:")
            print(f"python {os.path.basename(__file__)} --network {args.network} --fix")


if __name__ == "__main__":
    main()
