from typing import Optional

import numpy as np


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


def extract_avgs(vtk_data, array_names):
    results = {}
    area_array = vtk_data.GetCellData().GetArray("area")
    for name in array_names:
        vtk_array = vtk_data.GetCellData().GetArray(name)
        if vtk_array is None:
            results[name] = np.nan
            continue
        if area_array:
            avg_value = calculate_weighted_average(vtk_array, area_array)
        else:
            avg_value = float(np.nanmean(np.array(vtk_array)))
        results[name] = avg_value
    return results
