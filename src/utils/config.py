"""
Configuration module for Adaptive Weighted A* Emergency Vehicle Routing.

This module contains configuration constants and default values used throughout
the routing system.
"""

import logging
from typing import Dict

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# ROUTING ALGORITHM PARAMETERS
# ============================================================================

# Base weights for distance vs time trade-off
BASE_DISTANCE_WEIGHT: float = 0.6
BASE_TIME_WEIGHT: float = 0.4

# Maximum weight shift boundaries
MAX_TIME_WEIGHT: float = 0.95
MIN_TIME_WEIGHT: float = 0.05

# Adaptation factors
PROGRESS_SHIFT_MAX: float = 0.20  # Maximum shift based on route progress
RUSH_HOUR_SHIFT: float = 0.05  # Shift during rush hours

# Severity-based weight shifts
SEVERITY_SHIFTS: Dict[str, float] = {
    "CRITICAL": 0.15,  # +15% toward time priority
    "HIGH": 0.08,  # +8% toward time priority
    "MEDIUM": 0.0,  # No shift
}

# Rush hour time windows (24-hour format)
MORNING_RUSH_START: int = 7
MORNING_RUSH_END: int = 9
EVENING_RUSH_START: int = 16
EVENING_RUSH_END: int = 19

# ============================================================================
# VEHICLE PARAMETERS
# ============================================================================

# Speed limits (km/h)
DEFAULT_MAX_SPEED_KMH: float = 80.0
REALISTIC_SPEED_RANGE: tuple = (40.0, 120.0)

# Vehicle behavior
SPEED_FACTOR: float = 1.2  # Multiplier for speed responsiveness
VEHICLE_COLOR_RGB: tuple = (255, 0, 0, 255)  # Red for emergency vehicles

# ============================================================================
# TRAFFIC LIGHT CONTROL
# ============================================================================

# Signal preemption parameters
DETECTION_RANGE_METERS: float = 500.0  # Distance to start preemption
GREEN_PHASE_DURATION_SEC: float = 30.0  # Hold green for emergency vehicle

# Signal states
RED_STATES: set = {"r", "y"}  # States that require preemption
GREEN_STATES: set = {"G", "g"}  # Valid green states

# ============================================================================
# SIMULATION PARAMETERS
# ============================================================================

# Search algorithm constraints
MAX_ROUTE_ITERATIONS: int = 1000  # Safety limit for A* search
PROGRESS_REPORT_INTERVAL: int = 100  # Route computation progress

# Simulation timing
DEFAULT_STEP_LENGTH: float = 1.0  # Simulation step in seconds
GUI_DELAY_MS: int = 500  # Visualization delay
MAX_SIMULATION_TIME: int = 3600  # Maximum simulation duration (1 hour)

# Monitoring intervals
DEFAULT_WEIGHT_INTERVAL_SEC: int = 30  # Real-time weight display interval

# ============================================================================
# FILE PATHS (defaults)
# ============================================================================

# Paths relative to project root
DEFAULT_NETWORK_FILE: str = "data/network/bangalore.net.xml"
DEFAULT_CONFIG_FILE: str = "data/network/bangalore.sumocfg"
DEFAULT_VIEW_FILE: str = "data/network/bangalore.view.xml"

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================


def validate_weights(distance_weight: float, time_weight: float) -> bool:
    """
    Validate that weights are proper probabilities summing to 1.0.

    Args:
        distance_weight: Weight for distance component
        time_weight: Weight for time component

    Returns:
        True if valid, False otherwise
    """
    if distance_weight < 0 or time_weight < 0:
        return False
    if distance_weight > 1 or time_weight > 1:
        return False
    return abs(distance_weight + time_weight - 1.0) < 0.001


def validate_severity(severity: str) -> bool:
    """
    Validate emergency severity level.

    Args:
        severity: Severity level string

    Returns:
        True if valid severity level
    """
    return severity in SEVERITY_SHIFTS


def validate_speed(speed_kmh: float) -> bool:
    """
    Validate vehicle speed is within realistic range.

    Args:
        speed_kmh: Speed in kilometers per hour

    Returns:
        True if within realistic range
    """
    min_speed, max_speed = REALISTIC_SPEED_RANGE
    return min_speed <= speed_kmh <= max_speed
