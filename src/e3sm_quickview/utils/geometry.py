"""
Geographic and geometric operations for visualization.

This module contains functions for map projections, coordinate transformations,
and graticule generation for geographic visualizations.
"""

import math
import numpy as np
from typing import List, Tuple, Optional, Callable
from functools import partial
from pyproj import Proj, Transformer
from paraview.simple import Text


def apply_projection(
    projection: Optional[Transformer], point: List[float]
) -> List[float]:
    """
    Apply map projection to a point.

    Args:
        projection: Transformer object for projection, or None for no projection
        point: [longitude, latitude, z] coordinate

    Returns:
        Projected [x, y, z] coordinate
    """
    if projection is None:
        return point
    else:
        new = projection.transform(point[0] - 180, point[1])
        return [new[0], new[1], 1.0]


def create_projection_transformer(
    projection_type: str, center: float = 0
) -> Optional[Callable]:
    """
    Create a projection transformer function for the specified projection type.

    Args:
        projection_type: Type of projection ("Robinson", "Mollweide", "Cyl. Equidistant")
        center: Center longitude for the projection

    Returns:
        Projection transformer function or None for cylindrical equidistant
    """
    # For now, center is reserved for future use when we implement centered projections
    # The actual centering is handled in generate_annotations by adjusting coordinates
    _ = center  # Mark as intentionally unused

    proj_func = partial(apply_projection, None)

    if projection_type != "Cyl. Equidistant":
        latlon = Proj("epsg:4326")

        if projection_type == "Robinson":
            proj = Proj(proj="robin")
        elif projection_type == "Mollweide":
            proj = Proj(proj="moll")
        else:
            return proj_func

        xformer = Transformer.from_proj(latlon, proj)
        proj_func = partial(apply_projection, xformer)

    return proj_func


def calculate_graticule_bounds(
    longitude_range: Tuple[float, float],
    latitude_range: Tuple[float, float],
    interval: float = 30,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate graticule line positions based on longitude/latitude ranges.

    Args:
        longitude_range: (min, max) longitude
        latitude_range: (min, max) latitude
        interval: Spacing between grid lines in degrees

    Returns:
        Tuple of (longitude_positions, latitude_positions) as numpy arrays
    """
    llon, hlon = longitude_range
    llat, hlat = latitude_range

    # Round to interval boundaries
    llon = math.floor(llon / interval) * interval
    hlon = math.ceil(hlon / interval) * interval
    llat = math.floor(llat / interval) * interval
    hlat = math.ceil(hlat / interval) * interval

    lonx = np.arange(llon, hlon + interval, interval)
    laty = np.arange(llat, hlat + interval, interval)

    return lonx, laty


def generate_annotations(
    long: Tuple[float, float],
    lat: Tuple[float, float],
    projection: str,
    center: float,
    interval: float = 30,
    label_offset_factor: float = 0.075,
) -> List[Tuple[object, List[float]]]:
    """
    Generate text annotations for map graticule (grid lines).

    Args:
        long: (min, max) longitude range
        lat: (min, max) latitude range
        projection: Map projection type
        center: Center longitude for projection
        interval: Spacing between grid lines in degrees
        label_offset_factor: Factor for offsetting labels from map edge

    Returns:
        List of (text_object, position) tuples for annotation placement
    """
    texts = []

    # Calculate graticule bounds
    lonx, laty = calculate_graticule_bounds(long, lat, interval)

    # Create projection transformer
    proj_func = create_projection_transformer(projection, center)

    # Generate longitude labels
    for x in lonx:
        lon = x - center
        pos = lon

        # Wrap longitude to [-180, 180]
        if lon > 180:
            pos = -180 + (lon % 180)
        elif lon < -180:
            pos = 180 - (abs(lon) % 180)

        if pos == 180:
            continue

        txt = str(x)
        text = Text(registrationName=f"text{x}")
        text.Text = txt

        # Position at top of map
        position = proj_func([pos, lat[1], 1.0])
        texts.append((text, position))

    # Generate latitude labels
    for y in laty:
        text = Text(registrationName=f"text{y}")
        text.Text = str(y)

        # Position at right edge of map
        position = proj_func([long[1], y, 1.0])
        # Offset slightly to the right
        position[0] += position[0] * label_offset_factor
        texts.append((text, position))

    return texts


def normalize_longitude(lon: float, center: float = 0) -> float:
    """
    Normalize longitude to be within [-180, 180] relative to center.

    Args:
        lon: Longitude value
        center: Center longitude for normalization

    Returns:
        Normalized longitude value
    """
    lon_shifted = lon - center

    if lon_shifted > 180:
        return -180 + (lon_shifted % 180)
    elif lon_shifted < -180:
        return 180 - (abs(lon_shifted) % 180)
    else:
        return lon_shifted
