"""
OSM Bounding Box Extraction Utility

Extracts a geographic bounding box from large OSM PBF files with configurable
coordinates. Useful for creating regional network datasets from larger OpenStreetMap
data files.

Author: Emergency Vehicle Routing Research Team
License: MIT
Version: 1.0.0
"""

import argparse
import logging
import os
import sys
from typing import Tuple
import osmium

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BBoxExtractor(osmium.SimpleHandler):
    """
    Extract OSM data within a specified bounding box.

    Processes nodes, ways, and relations from large OSM PBF files,
    keeping only elements within the defined geographic bounds.
    """

    def __init__(
        self,
        writer: osmium.SimpleWriter,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
    ):
        """
        Initialize the bounding box extractor.

        Args:
            writer: OSM writer for output file
            min_lon: Western boundary (longitude)
            min_lat: Southern boundary (latitude)
            max_lon: Eastern boundary (longitude)
            max_lat: Northern boundary (latitude)
        """
        super().__init__()
        self.writer = writer
        self.min_lon = min_lon
        self.min_lat = min_lat
        self.max_lon = max_lon
        self.max_lat = max_lat

        # Statistics
        self.node_count = 0
        self.way_count = 0
        self.relation_count = 0
        self.nodes_kept = 0
        self.ways_kept = 0
        self.relations_kept = 0
        self.nodes_in_bbox = set()

    def is_in_bbox(self, location: osmium.osm.Location) -> bool:
        """
        Check if a location is within the bounding box.

        Args:
            location: OSM location object with lat/lon

        Returns:
            True if location is within bounds
        """
        if not location.valid():
            return False
        return (
            self.min_lon <= location.lon <= self.max_lon
            and self.min_lat <= location.lat <= self.max_lat
        )

    def node(self, n: osmium.osm.Node) -> None:
        """
        Process OSM nodes.

        Args:
            n: OSM node object
        """
        self.node_count += 1
        if self.node_count % 50000 == 0:
            print(
                f"  Processed {self.node_count:,} nodes, " f"kept {self.nodes_kept:,}",
                end="\r",
            )

        if self.is_in_bbox(n.location):
            self.writer.add_node(n)
            self.nodes_in_bbox.add(n.id)
            self.nodes_kept += 1

    def way(self, w: osmium.osm.Way) -> None:
        """
        Process OSM ways.

        Args:
            w: OSM way object
        """
        self.way_count += 1
        if self.way_count % 10000 == 0:
            print(
                f"  Processed {self.way_count:,} ways, " f"kept {self.ways_kept:,}",
                end="\r",
            )

        # Keep way if any of its nodes are in the bounding box
        for node in w.nodes:
            if node.ref in self.nodes_in_bbox:
                self.writer.add_way(w)
                self.ways_kept += 1
                break

    def relation(self, r: osmium.osm.Relation) -> None:
        """
        Process OSM relations.

        Args:
            r: OSM relation object
        """
        self.relation_count += 1
        if self.relation_count % 1000 == 0:
            print(
                f"  Processed {self.relation_count:,} relations, "
                f"kept {self.relations_kept:,}",
                end="\r",
            )

        # Keep all relations (simplified approach)
        # In production, this would check if relation members are in bbox
        self.writer.add_relation(r)
        self.relations_kept += 1

    def print_statistics(self) -> None:
        """Print extraction statistics."""
        print(f"\n\n{'='*80}")
        print("EXTRACTION COMPLETE")
        print(f"{'='*80}")
        print(f"\nTotal processed:")
        print(f"  Nodes:     {self.node_count:>12,}")
        print(f"  Ways:      {self.way_count:>12,}")
        print(f"  Relations: {self.relation_count:>12,}")
        print(f"\nKept in output:")
        print(
            f"  Nodes:     {self.nodes_kept:>12,} ({self.nodes_kept/max(self.node_count,1)*100:.1f}%)"
        )
        print(
            f"  Ways:      {self.ways_kept:>12,} ({self.ways_kept/max(self.way_count,1)*100:.1f}%)"
        )
        print(
            f"  Relations: {self.relations_kept:>12,} ({self.relations_kept/max(self.relation_count,1)*100:.1f}%)"
        )


def validate_bbox(
    min_lon: float, min_lat: float, max_lon: float, max_lat: float
) -> bool:
    """
    Validate bounding box coordinates.

    Args:
        min_lon: Western boundary
        min_lat: Southern boundary
        max_lon: Eastern boundary
        max_lat: Northern boundary

    Returns:
        True if valid, False otherwise
    """
    if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
        print("Error: Longitude must be between -180 and 180")
        return False

    if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
        print("Error: Latitude must be between -90 and 90")
        return False

    if min_lon >= max_lon:
        print("Error: min_lon must be less than max_lon")
        return False

    if min_lat >= max_lat:
        print("Error: min_lat must be less than max_lat")
        return False

    return True


def extract_bbox(
    input_file: str,
    output_file: str,
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
) -> None:
    """
    Extract geographic bounding box from OSM PBF file.

    Args:
        input_file: Path to input OSM PBF file
        output_file: Path to output OSM file
        min_lon: Western boundary (longitude)
        min_lat: Southern boundary (latitude)
        max_lon: Eastern boundary (longitude)
        max_lat: Northern boundary (latitude)

    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If bounding box coordinates are invalid
    """
    # Validate inputs
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    if not validate_bbox(min_lon, min_lat, max_lon, max_lat):
        raise ValueError("Invalid bounding box coordinates")

    print("=" * 80)
    print("OSM BOUNDING BOX EXTRACTION")
    print("=" * 80)
    print(f"\nInput:  {input_file}")
    print(f"Output: {output_file}")
    print(f"\nBounding Box:")
    print(f"  West  (min_lon): {min_lon:>10.6f}°")
    print(f"  South (min_lat): {min_lat:>10.6f}°")
    print(f"  East  (max_lon): {max_lon:>10.6f}°")
    print(f"  North (max_lat): {max_lat:>10.6f}°")
    print(f"\nThis may take several minutes for large files...\n")

    # Create writer and handler
    writer = osmium.SimpleWriter(output_file)
    handler = BBoxExtractor(writer, min_lon, min_lat, max_lon, max_lat)

    try:
        print("Processing OSM data...")
        handler.apply_file(input_file, locations=True)

        handler.print_statistics()
        print(f"\n✓ Output saved to: {output_file}")
        print("=" * 80)

    finally:
        writer.close()


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Extract a geographic bounding box from OSM PBF files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract Bangalore area
  python extract_bbox.py -i india.osm.pbf -o bangalore.osm \\
    --min-lon 77.4440 --min-lat 12.8305 --max-lon 77.7242 --max-lat 13.0715
  
  # Extract custom region
  python extract_bbox.py -i world.osm.pbf -o region.osm \\
    --min-lon -122.5 --min-lat 37.7 --max-lon -122.3 --max-lat 37.8

Coordinate System:
  Longitude: East-West position (-180 to 180, negative = West)
  Latitude:  North-South position (-90 to 90, negative = South)
  
  Example cities:
    - Bangalore: ~77.59° E, ~12.97° N
    - San Francisco: ~-122.42° E, ~37.77° N
    - London: ~-0.12° E, ~51.50° N

Input File Format:
  Supports OSM PBF (Protocol Buffer Format) files from:
  - https://download.geofabrik.de/
  - https://planet.openstreetmap.org/
        """,
    )

    # Required arguments
    parser.add_argument(
        "-i", "--input", type=str, required=True, help="Input OSM PBF file path"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Output OSM file path (will be created/overwritten)",
    )

    # Bounding box coordinates
    bbox_group = parser.add_argument_group("Bounding Box Coordinates")
    bbox_group.add_argument(
        "--min-lon",
        type=float,
        required=True,
        help="Western boundary (minimum longitude, -180 to 180)",
    )
    bbox_group.add_argument(
        "--min-lat",
        type=float,
        required=True,
        help="Southern boundary (minimum latitude, -90 to 90)",
    )
    bbox_group.add_argument(
        "--max-lon",
        type=float,
        required=True,
        help="Eastern boundary (maximum longitude, -180 to 180)",
    )
    bbox_group.add_argument(
        "--max-lat",
        type=float,
        required=True,
        help="Northern boundary (maximum latitude, -90 to 90)",
    )

    # Preset locations (optional feature for future)
    parser.add_argument(
        "--preset",
        type=str,
        choices=["bangalore"],
        help="Use preset coordinates for known cities (overrides bbox args)",
    )

    args = parser.parse_args()

    # Apply preset if specified
    if args.preset == "bangalore":
        print("Using Bangalore preset coordinates...")
        args.min_lon = 77.4440
        args.min_lat = 12.8305
        args.max_lon = 77.7242
        args.max_lat = 13.0715

    # Execute extraction
    try:
        extract_bbox(
            args.input,
            args.output,
            args.min_lon,
            args.min_lat,
            args.max_lon,
            args.max_lat,
        )
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
