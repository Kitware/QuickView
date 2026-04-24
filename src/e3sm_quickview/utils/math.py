"""
Mathematical utilities for visualization calculations.

This module contains pure mathematical functions for data processing and
camera calculations that can be reused across different visualization projects.
"""

import numpy as np
from typing import List, Tuple, Optional


def calculate_linthresh(data):
    """Calculate the linear threshold for symlog scaling.

    Excludes machine-error zeros (values within ±sqrt(eps) of the data dtype),
    then returns min(abs(valid)).

    Operates on the original array without copies.

    Args:
        data: numpy array of data values

    Returns:
        linthresh value (float), clamped to at least 1.0
    """
    eps = np.finfo(data.dtype).eps
    threshold = np.sqrt(eps)

    # Find min |x| > threshold without allocating a copy.
    # Using where= runs as a tight vectorized C loop, roughly 2-3 orders
    # of magnitude faster than a Python for loop.
    min_pos = np.nanmin(data, where=data > threshold, initial=np.inf)
    # For negatives: max(data) where data < -threshold gives closest to zero
    max_neg = np.nanmax(data, where=data < -threshold, initial=-np.inf)
    min_abs = min(min_pos, -max_neg)

    if min_abs == np.inf:
        linthresh = 1.0
    else:
        linthresh = max(float(min_abs), 1.0)

    return linthresh


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


def get_nice_ticks(vmin, vmax, n, scale="linear", linthresh=None):
    """Compute nicely spaced tick values for a given range and scale.

    Args:
        vmin: Minimum data value
        vmax: Maximum data value
        n: Desired number of ticks
        scale: One of 'linear', 'log', or 'symlog'

    Returns:
        Sorted array of unique, snapped tick values.
    """

    def snap(val):
        if np.isclose(val, 0, atol=1e-12):
            return 0.0
        sign = np.sign(val)
        val_abs = abs(val)
        mag = 10 ** np.floor(np.log10(val_abs))
        residual = val_abs / mag
        nice_steps = np.array([1.0, 2.0, 5.0, 10.0])
        best_step = nice_steps[np.abs(nice_steps - residual).argmin()]
        return sign * best_step * mag

    if scale == "linear":
        raw_ticks = np.linspace(vmin, vmax, n)
    elif scale == "log":
        # Use integer powers of 10 that fall strictly inside [vmin, vmax]
        log_floor = linthresh if linthresh is not None else 1e-15
        safe_vmin = max(vmin, log_floor)
        safe_vmax = max(vmax, log_floor)
        start_exp = int(np.floor(np.log10(safe_vmin)))
        stop_exp = int(np.ceil(np.log10(safe_vmax)))
        powers = [
            10.0**e
            for e in range(start_exp, stop_exp + 1)
            if safe_vmin <= 10.0**e <= safe_vmax
        ]
        # Fall back to log-spaced ticks when no powers of 10 are interior
        if len(powers) < 2:
            raw_ticks = np.geomspace(safe_vmin, safe_vmax, n)
        else:
            raw_ticks = np.array(powers)
    elif scale == "symlog":
        if linthresh is None:
            linthresh = 1.0
        # Use powers of 10 as tick values, matching the LUT breakpoints
        ticks_set = set()
        if vmin < 0:
            lo = max(linthresh, 1e-30)
            for e in range(
                int(np.floor(np.log10(lo))), int(np.floor(np.log10(abs(vmin)))) + 1
            ):
                val = -(10.0**e)
                if vmin <= val < 0:
                    ticks_set.add(val)
        if vmax > 0:
            lo = max(linthresh, 1e-30)
            for e in range(
                int(np.floor(np.log10(lo))), int(np.floor(np.log10(vmax))) + 1
            ):
                val = 10.0**e
                if 0 < val <= vmax:
                    ticks_set.add(val)
        if vmin <= 0 <= vmax:
            ticks_set.add(0.0)
        ticks_set.add(vmin)
        ticks_set.add(vmax)
        raw_ticks = np.array(sorted(ticks_set))
        # Skip snap — powers of 10 are already nice
        return raw_ticks
    else:
        raw_ticks = np.linspace(vmin, vmax, n)

    nice_ticks = np.array([snap(t) for t in raw_ticks])

    # Force 0 for non-log scales if it's within range
    if vmin <= 0 <= vmax and scale != "log":
        idx = np.abs(nice_ticks).argmin()
        nice_ticks[idx] = 0.0

    return np.unique(np.sort(nice_ticks))


def format_tick(val):
    """Format a tick value as a concise human-readable string.

    Returns a string suitable for display on a colorbar. Powers of 10 are
    shown as '10^N', very large/small values use scientific notation, and
    intermediate values use fixed-point.
    """
    if np.isclose(val, 0, atol=1e-12):
        return "0"

    val_abs = abs(val)
    log10 = np.log10(val_abs)

    if np.isclose(log10, np.round(log10), atol=1e-12):
        exponent = int(np.round(log10))
        sign = "-" if val < 0 else ""
        if exponent == 0:
            return f"{sign}1"
        if exponent == 1:
            return f"{sign}10"
        return f"{sign}10^{exponent}"

    if val_abs >= 1000 or val_abs <= 0.01:
        return f"{val:.1e}"
    return f"{int(val) if val == int(val) else val:.1f}"


def tick_contrast_color(r, g, b):
    """Return '#fff' or '#000' for best contrast against the given RGB color.

    Uses the W3C relative luminance formula to decide. RGB values are
    expected in [0, 1] range.
    """
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#000" if luminance > 0.45 else "#fff"


def compute_color_ticks(
    vmin, vmax, scale="linear", n=5, min_gap=7, edge_margin=3, linthresh=None
):
    """Compute tick marks for a colorbar.

    Tick positions are computed in the space matching the scale:
    - linear: position = (val - vmin) / (vmax - vmin) * 100
    - symlog: position = (symlog(val) - symlog(vmin)) / (symlog(vmax) - symlog(vmin)) * 100

    The colorbar image is always the linear preset, so symlog ticks
    appear at different positions than linear ticks for the same values.

    Args:
        vmin: Minimum color range value
        vmax: Maximum color range value
        scale: One of 'linear', 'log', or 'symlog'
        n: Desired number of ticks
        min_gap: Minimum gap between ticks in percentage points
        edge_margin: Minimum distance from edges (0% and 100%) in percentage points

    Returns:
        List of dicts with 'position' (0-100 percentage) and 'label' keys.
    """
    if vmin >= vmax:
        return []

    raw_n = n if scale == "linear" else n * 2
    ticks = get_nice_ticks(vmin, vmax, raw_n, scale, linthresh=linthresh)
    data_range = vmax - vmin

    # Build mapping functions for non-linear tick positions
    _symlog_fn = None
    _log_min = _log_max = _log_range = None

    if scale == "symlog":
        if linthresh is None:
            linthresh = 1.0

        def _symlog_fn(v):
            v = np.asarray(v, dtype=float)
            return np.sign(v) * np.log10(1.0 + np.abs(v) / linthresh)

        s_min = float(_symlog_fn(vmin))
        s_max = float(_symlog_fn(vmax))
        s_range = s_max - s_min

    elif scale == "log":
        log_floor = linthresh if linthresh is not None else 1e-30
        safe_vmin = max(vmin, log_floor)
        safe_vmax = max(vmax, log_floor)
        _log_min = np.log10(safe_vmin)
        _log_max = np.log10(safe_vmax)
        _log_range = _log_max - _log_min

    # Build candidate list with position in the appropriate space
    candidates = []
    has_zero = False
    for t in ticks:
        val = float(t)
        if scale == "symlog" and s_range != 0:
            pos = (float(_symlog_fn(val)) - s_min) / s_range * 100
        elif scale == "log" and _log_range and _log_range != 0 and val > 0:
            pos = (np.log10(val) - _log_min) / _log_range * 100
        else:
            pos = (val - vmin) / data_range * 100
        if edge_margin <= pos <= (100 - edge_margin):
            is_zero = np.isclose(val, 0, atol=1e-12)
            if is_zero:
                has_zero = True
            candidates.append(
                {
                    "position": round(pos, 2),
                    "label": format_tick(val),
                    "priority": is_zero,
                }
            )

    # Always include 0 when it falls within the range (for any scale)
    if not has_zero and scale != "log":
        if scale == "symlog" and s_range != 0:
            zero_pos = (float(_symlog_fn(0.0)) - s_min) / s_range * 100
        else:
            zero_pos = (0.0 - vmin) / data_range * 100
        if 0 <= zero_pos <= 100:
            tick = {"position": round(zero_pos, 2), "label": "0", "priority": True}
            # Insert in sorted order
            inserted = False
            for i, c in enumerate(candidates):
                if tick["position"] <= c["position"]:
                    candidates.insert(i, tick)
                    inserted = True
                    break
            if not inserted:
                candidates.append(tick)

    # Filter out ticks that are too close together, but never remove priority ticks
    result = []
    for tick in candidates:
        is_priority = tick.get("priority", False)
        if is_priority:
            if result and (tick["position"] - result[-1]["position"]) < min_gap:
                if not result[-1].get("priority", False):
                    result.pop()
            result.append(tick)
        elif not result or (tick["position"] - result[-1]["position"]) >= min_gap:
            # Also check distance to next priority tick (look-ahead)
            result.append(tick)

    # Clean up internal flags before returning
    for tick in result:
        tick.pop("priority", None)
    return result
