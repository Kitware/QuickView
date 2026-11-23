"""State file export/import round-trip tests.

The app is started headless once per module on a small synthetic simulation
file that matches the connectivity file shipped with the package. A scenario
then exports, scrambles and re-imports state while recording what it observes,
and the individual tests assert on those observations.
"""

import asyncio
import copy
import json
import sys
from pathlib import Path

import netCDF4
import numpy as np
import pytest

import e3sm_quickview

CONNECTIVITY = Path(e3sm_quickview.__file__).parent / "data" / "connectivity.nc"
N_LEV = 8
SCENARIO_TIMEOUT = 300


def write_simulation(path):
    """Write a 1-timestep, N_LEV-level file on the bundled ne30pg2 grid."""
    with netCDF4.Dataset(CONNECTIVITY) as conn:
        n_col = len(conn.dimensions["ncol"])

    rng = np.random.default_rng(0)
    with netCDF4.Dataset(path, "w") as ds:
        ds.createDimension("time", None)
        ds.createDimension("lev", N_LEV)
        ds.createDimension("ncol", n_col)

        time = ds.createVariable("time", "f8", ("time",))
        time.units = "days since 2000-01-01 00:00:00"
        time[:] = [0.0]

        lev = ds.createVariable("lev", "f8", ("lev",))
        lev.units = "hPa"
        lev[:] = np.linspace(10, 1000, N_LEV)

        for name, units, offset in (("T", "K", 250.0), ("U", "m/s", 0.0)):
            var = ds.createVariable(name, "f4", ("time", "lev", "ncol"))
            var.units = units
            var.long_name = name
            var[:] = offset + 20 * rng.standard_normal((1, N_LEV, n_col))


def strip(state_json):
    """Drop the fields that legitimately differ between two exports."""
    content = json.loads(state_json)
    content.pop("origin")
    content["layout"].pop("camera", None)
    return content


def differences(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        return [
            d
            for k in sorted(set(a) | set(b))
            for d in differences(
                a.get(k, "<missing>"), b.get(k, "<missing>"), f"{path}.{k}"
            )
        ]
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [
            d
            for i, (x, y) in enumerate(zip(a, b))
            for d in differences(x, y, f"{path}[{i}]")
        ]
    return [] if a == b else [f"{path}: {a!r} -> {b!r}"]


async def run_scenario(app, simulation):
    s = app.state
    results = {}

    async def settle(views=()):
        for view in views:
            await view.colormap.completion()
        await app.server.network_completion
        await asyncio.sleep(0.5)

    # Load data and two 3D variables
    app.file_browser.set_data_simulation(str(simulation))
    app.file_browser.set_data_connectivity(str(CONNECTIVITY))
    await app.data_loading_open(str(simulation), str(CONNECTIVITY))
    s.variables_selected = ["T", "U"]
    await app._data_load_variables()
    await settle()
    results["animation_track"] = s.animation_track
    views = [
        app.view_manager.get_view(name, dims)
        for dims, names in app.selected_variables.items()
        for name in names
    ]
    cmap_t, cmap_u = (v.colormap for v in views)

    # Apply non-default settings everywhere the state file covers
    with s:
        s.continent_level = -1
        s.grid_interval = 10
        s.spherical_center_lon = 40
        s.spherical_center_lat = 15
        s.animation_step = 3
    cmap_t.update(
        n_ticks=7,
        cut_outside_range=True,
        nan_color=[1.0, 0.0, 1.0, 1.0],
        selected_categories="diverging",
    )
    await settle(views)
    cmap_t.update(diverging=True)
    await settle(views)
    cmap_t.update(abs_max="42", epsilon="0.5")
    cmap_u.update(
        enable_independent_bands=True,
        independent_bands="both",
        independent_band_top_color=[1.0, 0.0, 0.0, 1.0],
    )
    await settle(views)
    saved = strip(app.download_state())
    results["saved"] = saved

    # Move the session away from the saved state and turn probing on
    with s:
        s.continent_level = 2
        s.grid_interval = 30
        s.spherical_center_lon = 0
        s.spherical_center_lat = 0
        s.animation_step = 0
        s.picking_mode = "hover"
    cmap_t.update(diverging=False, n_ticks=5, nan_color=[0.0, 0.0, 0.0, 0.0])
    await settle(views)

    # Import the saved state and export again
    await app._import_state(copy.deepcopy(saved))
    await settle(views)
    results["reloaded"] = strip(app.download_state())
    results["picking_mode"] = s.picking_mode
    results["animation_step"] = s.animation_step
    results["track_idx"] = s[f"{s.animation_track}_idx"]

    # State files written before the extended layout keys existed
    legacy = copy.deepcopy(saved)
    for key in (
        "grid-interval",
        "map-center-lon",
        "map-center-lat",
        "bg-color",
        "continent-level",
    ):
        legacy["layout"].pop(key, None)
    try:
        await app._import_state(legacy)
        await settle(views)
        results["legacy"] = {
            "grid_interval": s.grid_interval,
            "spherical_center_lon": s.spherical_center_lon,
            "spherical_center_lat": s.spherical_center_lat,
            "continent_level": s.continent_level,
        }
    except Exception as e:
        results["legacy"] = e

    # Only part of the extended layout keys present
    partial = copy.deepcopy(legacy)
    partial["layout"]["grid-interval"] = 5
    try:
        await app._import_state(partial)
        await settle(views)
        results["partial_grid_interval"] = s.grid_interval
    except Exception as e:
        results["partial_grid_interval"] = e

    return results


@pytest.fixture(scope="module")
def scenario(tmp_path_factory, monkeypatch_module):
    from e3sm_quickview.app import EAMApp

    simulation = tmp_path_factory.mktemp("data") / "simulation.nc"
    write_simulation(simulation)

    monkeypatch_module.setattr(
        sys, "argv", ["quickview", "--server", "--port", "0", "--timeout", "0"]
    )
    app = EAMApp()
    outcome = {}

    async def drive(**_):
        try:
            outcome["results"] = await asyncio.wait_for(
                run_scenario(app, simulation), SCENARIO_TIMEOUT
            )
        except BaseException as e:  # surface any failure to the tests
            outcome["error"] = e
        finally:
            await app.server.stop()

    app.server.controller.on_server_ready.add(
        lambda **kw: asyncio.ensure_future(drive(**kw))
    )
    app.server.start(open_browser=False, show_connection_info=False)

    if "error" in outcome:
        raise outcome["error"]
    return outcome["results"]


@pytest.fixture(scope="module")
def monkeypatch_module():
    with pytest.MonkeyPatch.context() as mp:
        yield mp


def test_round_trip_preserves_saved_settings(scenario):
    assert differences(scenario["saved"], scenario["reloaded"]) == []


def test_round_trip_saves_coastline_resolution(scenario):
    assert scenario["saved"]["layout"]["continent-level"] == -1


def test_round_trip_keeps_diverging_parameters(scenario):
    cmap = scenario["reloaded"]["views"][0]["colormap"]
    assert cmap["diverging"] is True
    assert cmap["abs_max"] == "42"
    assert cmap["epsilon"] == "0.5"


def test_import_disables_cursor_probe(scenario):
    assert scenario["picking_mode"] is None


def test_import_aligns_animation_step_with_track_index(scenario):
    assert scenario["animation_track"] == "lev"
    assert scenario["track_idx"] == 3
    assert scenario["animation_step"] == 3


def test_import_of_legacy_state_uses_defaults(scenario):
    assert scenario["legacy"] == {
        "grid_interval": 30,
        "spherical_center_lon": 0,
        "spherical_center_lat": 0,
        "continent_level": 0,
    }


def test_import_of_partial_extended_layout(scenario):
    assert scenario["partial_grid_interval"] == 5
