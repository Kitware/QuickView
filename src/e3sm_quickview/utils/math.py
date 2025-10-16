"""
Mathematical utilities for visualization calculations.

This module contains pure mathematical functions for data processing and
camera calculations that can be reused across different visualization projects.
"""

import numpy as np
from typing import List, Tuple, Optional


def calculate_weighted_average(
    data_array: np.ndarray, weights: Optional[np.ndarray] = None
) -> float:
    """
    Calculate average of data, optionally weighted.

    Args:
        data_array: The data to average
        weights: Optional weights for weighted averaging (e.g., area weights)

    Returns:
        The (weighted) average, handling NaN values
    """
    data = np.array(data_array)
    weights = np.array(weights)
    # Handle NaN values
    if np.isnan(data).any():
        mask = ~np.isnan(data)
        if not np.any(mask):
            return np.nan  # all values are NaN
        data = data[mask]
        if weights is not None:
            weights = weights[mask]

    if weights is not None:
        return float(np.average(data, weights=weights))
    else:
        return float(np.mean(data))


def calculate_data_range(bounds: List[float]) -> Tuple[float, float, float]:
    """
    Calculate the range (width, height, depth) from data bounds.

    Args:
        bounds: Data bounds [xmin, xmax, ymin, ymax, zmin, zmax]

    Returns:
        Tuple of (width, height, depth)
    """
    if not bounds or len(bounds) < 6:
        return (0, 0, 0)

    return (bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4])


def calculate_pan_offset(
    direction: int, factor: float, extents: List[float], offset_ratio: float = 0.05
) -> float:
    """
    Calculate camera pan offset based on direction and factor.

    Args:
        direction: Axis index (0=x, 1=y, 2=z)
        factor: Direction factor (positive or negative)
        extents: Data extents [xmin, xmax, ymin, ymax, zmin, zmax]
        offset_ratio: Ratio of extent to use for offset (0.05 = 5%)

    Returns:
        Offset value for the specified axis
    """
    if direction < 0 or direction > 2:
        return 0.0

    idx = direction * 2
    extent_range = extents[idx + 1] - extents[idx]
    offset = extent_range * offset_ratio

    return offset if factor > 0 else -offset


def interpolate_value(
    t: float, start_value: float, end_value: float, interpolation_type: str = "linear"
) -> float:
    """
    Interpolate between two values.

    Args:
        t: Interpolation parameter (0 to 1)
        start_value: Starting value
        end_value: Ending value
        interpolation_type: Type of interpolation ("linear", "smooth", "ease-in-out")

    Returns:
        Interpolated value
    """
    t = max(0, min(1, t))  # Clamp to [0, 1]

    if interpolation_type == "smooth":
        # Smooth step (cubic)
        t = t * t * (3 - 2 * t)
    elif interpolation_type == "ease-in-out":
        # Ease in-out (quintic)
        t = t * t * t * (t * (t * 6 - 15) + 10)
    # else: linear (no transformation)

    return start_value + t * (end_value - start_value)


def normalize_range(
    value: float,
    old_min: float,
    old_max: float,
    new_min: float = 0.0,
    new_max: float = 1.0,
) -> float:
    """
    Normalize a value from one range to another.

    Args:
        value: Value to normalize
        old_min: Minimum of the original range
        old_max: Maximum of the original range
        new_min: Minimum of the target range
        new_max: Maximum of the target range

    Returns:
        Normalized value in the target range
    """
    if old_max == old_min:
        return new_min

    normalized = (value - old_min) / (old_max - old_min)
    return new_min + normalized * (new_max - new_min)
