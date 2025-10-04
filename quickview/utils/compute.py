from paraview import servermanager
import numpy as np
from typing import Optional


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


def extract_avgs(pv_data, array_names):
    results = {}
    vtk_data = servermanager.Fetch(pv_data)
    area_array = vtk_data.GetCellData().GetArray("area")
    for name in array_names:
        vtk_array = vtk_data.GetCellData().GetArray(name)
        avg_value = calculate_weighted_average(vtk_array, area_array)
        results[name] = avg_value

    return results
