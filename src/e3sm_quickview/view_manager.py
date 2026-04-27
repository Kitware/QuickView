import math
import time

import numpy as np
from paraview import simple
from trame.app import TrameComponent, dataclass
from trame.decorators import controller
from trame.ui.html import DivLayout
from trame.widgets import client, html, rca
from trame.widgets import vuetify3 as v3
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper

from e3sm_quickview.components import view as tview
from e3sm_quickview.presets import COLOR_BLIND_SAFE
from e3sm_quickview.utils import perf
from e3sm_quickview.utils.color import COLORBAR_CACHE, lut_to_img
from e3sm_quickview.utils.math import (
    calculate_linthresh,
    compute_color_ticks,
    format_tick,
    tick_contrast_color,
)


def auto_size_to_col(size):
    if size == 1:
        return 12

    if size >= 8 and size % 2 == 0:
        return 3

    if size % 3 == 0:
        return 4

    if size % 2 == 0:
        return 6

    return auto_size_to_col(size + 1)


COL_SIZE_LOOKUP = {
    0: auto_size_to_col,
    1: 12,
    2: 6,
    3: 4,
    4: 3,
    6: 2,
    12: 1,
    "flow": None,
}


def lut_name(element):
    return element.get("name").lower()


class ViewConfiguration(dataclass.StateDataModel):
    variable: str = dataclass.Sync(str)
    preset: str = dataclass.Sync(str, "BuGnYl")
    invert: bool = dataclass.Sync(bool, False)
    color_blind: bool = dataclass.Sync(bool, False)
    use_log_scale: str = dataclass.Sync(str, "linear")
    discrete_log: bool = dataclass.Sync(bool, False)
    n_discrete_colors: int = dataclass.Sync(int, 1)
    color_value_min: str = dataclass.Sync(str, "0")
    color_value_max: str = dataclass.Sync(str, "1")
    color_value_min_valid: bool = dataclass.Sync(bool, True)
    color_value_max_valid: bool = dataclass.Sync(bool, True)
    color_range: list[float] = dataclass.Sync(tuple[float, float], (0, 1))
    override_range: bool = dataclass.Sync(bool, False)
    order: int = dataclass.Sync(int, 0)
    size: int = dataclass.Sync(int, 6)
    offset: int = dataclass.Sync(int, 0)
    break_row: bool = dataclass.Sync(bool, False)
    menu: bool = dataclass.Sync(bool, False)
    swap_group: list[str] = dataclass.Sync(list[str], list)
    search: str | None = dataclass.Sync(str)
    n_colors: int = dataclass.Sync(int, 255)
    lut_img: str = dataclass.Sync(str)
    color_ticks: list = dataclass.Sync(list, list)
    effective_color_range: list[float] = dataclass.Sync(tuple[float, float], (0, 1))


class VariableView(TrameComponent):
    def __init__(self, server, source, variable_name, variable_type):
        super().__init__(server)
        self.source = source
        self.variable_name = variable_name
        self.variable_type = variable_type
        self.disable_render = False
        self.name = f"view_{self.variable_name}"
        self.config = ViewConfiguration(server, variable=variable_name)

        # ParaView
        self.view = simple.CreateRenderView()
        self.view.InteractionMode = "2D"
        self.view.OrientationAxesVisibility = 0
        self.view.UseColorPaletteForBackground = 0
        self.view.BackgroundColorMode = "Gradient"
        self.view.CameraParallelProjection = 1

        # VTK
        self._camera = self.view.GetActiveCamera()
        self.renderer = self.view.GetRenderer()
        self.render_window = self.view.GetRenderWindow()
        self.render_window.SetOffScreenRendering(True)

        # Perf: time the actual VTK render. The `render()` method only
        # calls `ctx[name].update()` which schedules a trame/RCA push,
        # so the `view.<var>.render` timer doesn't capture the work of
        # the render window itself. Observers on Start/EndEvent fire
        # for every VTK render (triggered by RCA, camera change, etc.)
        # and emit `view.<var>.render_window` with the elapsed time.
        self._render_t0 = None
        self.render_window.AddObserver("StartEvent", self._on_render_start)
        self.render_window.AddObserver("EndEvent", self._on_render_end)

        input = source.data_reader.vtk_geometry
        self.mapper = vtkPolyDataMapper(input_connection=input.output_port)
        self.actor = vtkActor(mapper=self.mapper)
        self.renderer.AddActor(self.actor)

        # Lookup table color management
        self.lut = simple.GetColorTransferFunction(variable_name)
        self.lut.NanOpacity = 0.0

        # Color mapping
        self.mapper.SetScalarVisibility(1)
        self.mapper.SetScalarModeToUseCellFieldData()
        self.mapper.SelectColorArray(variable_name)
        self.mapper.SetLookupTable(self.lut.GetClientSideObject())

        # Add annotation to the view (continents, gridlines)
        self.renderer.AddActor(source.continent.actor)
        self.renderer.AddActor(source.grid_lines.actor)

        # Reactive behavior
        self.config.watch(
            ["color_value_min", "color_value_max"],
            self.color_range_str_to_float,
        )
        self.config.watch(
            ["override_range", "color_range"], self.update_color_range, eager=True
        )
        self.config.watch(
            [
                "preset",
                "invert",
                "use_log_scale",
                "discrete_log",
                "n_discrete_colors",
            ],
            self.update_color_preset,
            eager=True,
        )

        # Initial flush
        simple.Render(self.view)

        # GUI
        self._build_ui()

        # Need to be after RCA initialization (gui build)
        self.reset_camera()

    def render(self):
        if self.disable_render or not self.ctx.has(self.name):
            return
        with perf.timed(f"view.{self.variable_name}.render"):
            self.ctx[self.name].update()

    def _on_render_start(self, *_):
        if perf.is_enabled():
            self._render_t0 = time.perf_counter()

    def _on_render_end(self, *_):
        if perf.is_enabled() and self._render_t0 is not None:
            dt_ms = (time.perf_counter() - self._render_t0) * 1000.0
            perf.log(f"view.{self.variable_name}.render_window", dt_ms)
            self._render_t0 = None

    def set_camera_modified(self, fn):
        self._observer = self.camera.AddObserver("ModifiedEvent", fn)

    @property
    def camera(self):
        return self._camera

    def reset_camera(self):
        self.view.ResetCamera(True, 0.9)
        self.render()

    def update_color_preset(
        self,
        name,
        invert,
        log_scale,
        discrete_log=False,
        n_discrete_colors=1,
        n_colors=255,
    ):
        self.config.preset = name

        # ApplyPreset resets range to [0,1], so always apply the linear
        # preset first, rescale to the current range, then apply transforms
        self._apply_linear_to_lut(invert)
        self.lut.RescaleTransferFunction(*self.config.color_range)

        # Capture the linear colorbar image (always the same regardless of scale)
        ctf = self.lut.GetClientSideObject()
        self.config.effective_color_range = ctf.GetRange()
        self.config.lut_img = lut_to_img(self.lut)

        # Save a reference to the linear LUT range for tick contrast sampling
        linear_rgb_points = list(self.lut.RGBPoints)

        # Compute linthresh (smallest positive non-zero value) from data
        # for log and symlog scales.
        linthresh = None
        if log_scale in ("log", "symlog"):
            from vtkmodules.util.numpy_support import vtk_to_numpy

            arr = self.data_array
            if arr is not None:
                linthresh = calculate_linthresh(vtk_to_numpy(arr))
            else:
                linthresh = 1.0

        n_sub = max(1, min(5, int(n_discrete_colors)))
        if log_scale == "linear" and discrete_log:
            display_rgb_points = self._apply_discrete_linear_to_lut(
                linear_rgb_points, n_sub
            )
            if display_rgb_points is not None:
                linear_rgb_points = display_rgb_points
        elif log_scale == "log":
            if discrete_log:
                display_rgb_points = self._apply_discrete_log_to_lut(
                    linthresh, linear_rgb_points, n_sub
                )
                if display_rgb_points is not None:
                    linear_rgb_points = display_rgb_points
            else:
                self._apply_log_to_lut(linthresh)
        elif log_scale == "symlog":
            if discrete_log:
                display_rgb_points = self._apply_discrete_symlog_to_lut(
                    linthresh, linear_rgb_points, n_sub
                )
                if display_rgb_points is not None:
                    linear_rgb_points = display_rgb_points
            else:
                self._apply_symlog_to_lut(linthresh, linear_rgb_points)

        self._compute_ticks(linthresh=linthresh, linear_rgb_points=linear_rgb_points)

        # For symlog (or any discrete mode), rebuild the client-side CTF as
        # the VERY LAST step so nothing (proxy sync, _compute_ticks, lut_to_img)
        # can overwrite it.
        if log_scale == "symlog" or (discrete_log and log_scale in ("log", "linear")):
            from vtkmodules.vtkRenderingCore import vtkColorTransferFunction

            pts = list(self.lut.RGBPoints)
            ctf = vtkColorTransferFunction()
            for i in range(0, len(pts), 4):
                ctf.AddRGBPoint(pts[i], pts[i + 1], pts[i + 2], pts[i + 3])
            self._symlog_ctf = ctf  # prevent GC
        else:
            self.lut.UpdateVTKObjects()
            ctf = self.lut.GetClientSideObject()

        self.mapper.SetLookupTable(ctf)
        self.mapper.Modified()

        self.render()

    def _apply_linear_to_lut(self, invert=False):
        """Apply preset with linear scale."""
        self.lut.UseLogScale = 0
        self.lut.ApplyPreset(self.config.preset, True)
        if invert:
            self.lut.InvertTransferFunction()

    def _apply_discrete_linear_to_lut(self, linear_rgb_points, n_sub=1):
        """Build a discrete (stepped) linear LUT.

        The data range is divided into N_INTERVALS equal-percentage intervals.
        Each interval is then split into *n_sub* equal sub-bands, each with a
        flat color sampled from the continuous linear LUT at the sub-band
        midpoint.  The boundary values are stored so ``_compute_ticks`` can
        place tick marks at the exact same positions.
        """
        N_INTERVALS = 4
        ctf = self.lut.GetClientSideObject()
        x_min, x_max = ctf.GetRange()
        data_range = x_max - x_min
        if data_range == 0:
            return

        # Evenly spaced boundaries (percentages of data range)
        boundaries = [
            x_min + data_range * i / N_INTERVALS for i in range(N_INTERVALS + 1)
        ]
        # Store boundary values and their display positions (%) for tick alignment
        self._discrete_tick_data = [
            {"val": boundaries[i], "pos": i / N_INTERVALS * 100}
            for i in range(1, N_INTERVALS)
        ]

        # Build a temporary linear CTF from the saved linear RGB points
        from vtkmodules.vtkRenderingCore import vtkColorTransferFunction

        linear_ctf = vtkColorTransferFunction()
        for i in range(0, len(linear_rgb_points), 4):
            linear_ctf.AddRGBPoint(
                linear_rgb_points[i],
                linear_rgb_points[i + 1],
                linear_rgb_points[i + 2],
                linear_rgb_points[i + 3],
            )

        rgb = [0.0, 0.0, 0.0]
        eps = data_range * 1e-9
        display_rgb_points = []
        render_rgb_points = []
        band_idx = 0
        total_bands = (len(boundaries) - 1) * n_sub
        for i in range(len(boundaries) - 1):
            lo = boundaries[i]
            hi = boundaries[i + 1]
            for j in range(n_sub):
                # Sub-band edges in linear space
                sub_lo = lo + (hi - lo) * j / n_sub
                sub_hi = lo + (hi - lo) * (j + 1) / n_sub
                sub_mid = (sub_lo + sub_hi) / 2.0
                linear_ctf.GetColor(sub_mid, rgb)
                r, g, b = float(rgb[0]), float(rgb[1]), float(rgb[2])

                is_first = band_idx == 0
                is_last = band_idx == total_bands - 1

                if is_first:
                    display_rgb_points.extend([sub_lo, r, g, b])
                    render_rgb_points.extend([sub_lo, r, g, b])
                else:
                    display_rgb_points.extend([sub_lo + eps, r, g, b])
                    render_rgb_points.extend([sub_lo + eps, r, g, b])

                if is_last:
                    display_rgb_points.extend([sub_hi, r, g, b])
                    render_rgb_points.extend([sub_hi, r, g, b])
                else:
                    display_rgb_points.extend([sub_hi - eps, r, g, b])
                    render_rgb_points.extend([sub_hi - eps, r, g, b])

                band_idx += 1

        # Generate the discrete banded colorbar image
        self.lut.RGBPoints = display_rgb_points
        self.config.lut_img = lut_to_img(self.lut)

        # Store rendering points on proxy
        self.lut.UseLogScale = 0
        self.lut.RGBPoints = render_rgb_points

        return display_rgb_points

    def _apply_log_to_lut(self, linthresh):
        """Transform the already-prepared LUT to log scale.

        Uses linthresh (smallest positive non-zero data value) as the floor
        when the range includes zero or negative values.
        The colorbar image is captured before this call, so it stays linear.
        """
        ctf = self.lut.GetClientSideObject()
        x_min, x_max = ctf.GetRange()
        if x_max <= 0:
            return
        if x_min <= 0:
            x_min = linthresh
            self.lut.RescaleTransferFunction(x_min, x_max)
        self.lut.MapControlPointsToLogSpace()
        self.lut.UseLogScale = 1

    def _apply_discrete_log_to_lut(self, linthresh, linear_rgb_points, n_sub=1):
        """Build a discrete (stepped) log-scale LUT.

        Decade boundaries are powers of 10 from linthresh to x_max.
        Each decade is split into *n_sub* equal sub-bands in log space,
        each with a flat color sampled from the continuous linear LUT.
        """
        ctf = self.lut.GetClientSideObject()
        x_min, x_max = ctf.GetRange()
        if x_max <= 0:
            return
        # Clamp floor
        x_min = max(x_min, linthresh)
        data_range = x_max - x_min
        if data_range == 0:
            return

        log_min = np.log10(x_min)
        log_max = np.log10(x_max)
        log_range = log_max - log_min
        if log_range == 0:
            return

        # Build decade boundaries
        boundaries = [x_min]
        e_lo = int(np.ceil(np.log10(x_min)))
        e_hi = int(np.floor(np.log10(x_max)))
        for e in range(e_lo, e_hi + 1):
            val = 10.0**e
            if x_min < val < x_max:
                boundaries.append(val)
        boundaries.append(x_max)

        if len(boundaries) < 2:
            return

        # Store boundary values and their display positions (%) for tick alignment
        log_min = np.log10(x_min)
        log_max = np.log10(x_max)
        log_range_val = log_max - log_min
        self._discrete_tick_data = []
        for bv in boundaries[1:-1]:
            pct = (np.log10(bv) - log_min) / log_range_val * 100 if log_range_val else 0
            self._discrete_tick_data.append({"val": bv, "pos": float(pct)})

        # Build a temporary linear CTF from the saved linear RGB points
        from vtkmodules.vtkRenderingCore import vtkColorTransferFunction

        linear_ctf = vtkColorTransferFunction()
        for i in range(0, len(linear_rgb_points), 4):
            linear_ctf.AddRGBPoint(
                linear_rgb_points[i],
                linear_rgb_points[i + 1],
                linear_rgb_points[i + 2],
                linear_rgb_points[i + 3],
            )

        rgb = [0.0, 0.0, 0.0]
        eps_data = data_range * 1e-9
        eps_lin = 1e-9
        display_rgb_points = []
        render_rgb_points = []
        band_idx = 0
        total_bands = (len(boundaries) - 1) * n_sub
        for i in range(len(boundaries) - 1):
            log_lo_decade = np.log10(boundaries[i])
            log_hi_decade = np.log10(boundaries[i + 1])
            for j in range(n_sub):
                # Sub-band edges in log space
                log_lo = log_lo_decade + (log_hi_decade - log_lo_decade) * j / n_sub
                log_hi = (
                    log_lo_decade + (log_hi_decade - log_lo_decade) * (j + 1) / n_sub
                )
                log_mid = (log_lo + log_hi) / 2.0
                # Sample color from linear LUT at normalized position
                t_mid = (log_mid - log_min) / log_range
                x_lookup = x_min + t_mid * data_range
                linear_ctf.GetColor(x_lookup, rgb)
                r, g, b = float(rgb[0]), float(rgb[1]), float(rgb[2])

                # Data-space boundaries for rendering
                v_lo = 10.0**log_lo
                v_hi = 10.0**log_hi
                v_lo = max(x_min, min(x_max, v_lo))
                v_hi = max(x_min, min(x_max, v_hi))

                # Linear positions for display image
                t_lo_pos = (log_lo - log_min) / log_range
                t_hi_pos = (log_hi - log_min) / log_range
                d_lo = x_min + t_lo_pos * data_range
                d_hi = x_min + t_hi_pos * data_range

                is_first = band_idx == 0
                is_last = band_idx == total_bands - 1

                if is_first:
                    display_rgb_points.extend([d_lo, r, g, b])
                    render_rgb_points.extend([float(v_lo), r, g, b])
                else:
                    display_rgb_points.extend([d_lo + eps_lin, r, g, b])
                    render_rgb_points.extend([float(v_lo) + eps_data, r, g, b])

                if is_last:
                    display_rgb_points.extend([d_hi, r, g, b])
                    render_rgb_points.extend([float(v_hi), r, g, b])
                else:
                    display_rgb_points.extend([d_hi - eps_lin, r, g, b])
                    render_rgb_points.extend([float(v_hi) - eps_data, r, g, b])

                band_idx += 1

        # Generate the discrete banded colorbar image
        self.lut.RGBPoints = display_rgb_points
        self.config.lut_img = lut_to_img(self.lut)

        # Store rendering points on proxy
        self.lut.UseLogScale = 0
        self.lut.RGBPoints = render_rgb_points

        return display_rgb_points

    def _apply_symlog_to_lut(self, linthresh, linear_rgb_points=None):
        """Build a symlog LUT with decade control points.

        Control points are placed at powers of 10 (and ±linthresh, 0 for
        mixed-sign data).  The RGB color for each control point is sampled
        from the linear colorbar at the position where that value falls in
        symlog space: t = (symlog(v) - symlog(min)) / (symlog(max) - symlog(min)).
        """
        ctf = self.lut.GetClientSideObject()
        x_min, x_max = ctf.GetRange()
        data_range = x_max - x_min
        if data_range == 0:
            return

        def symlog(v):
            v = np.asarray(v, dtype=float)
            return np.sign(v) * np.log10(1.0 + np.abs(v) / linthresh)

        # Build control points: N uniform samples in symlog space, plus
        # mandatory breakpoints at ±linthresh and 0 for exact transitions.
        n_samples = 256
        s_min_val = float(symlog(x_min))
        s_max_val = float(symlog(x_max))
        s_range_bp = s_max_val - s_min_val
        if s_range_bp == 0:
            return

        # Uniform in symlog space → invert to data space
        # Inverse of symlog: v = sign(s) * linthresh * (10^|s| - 1)
        s_vals = np.linspace(s_min_val, s_max_val, n_samples)
        breakpoints = []
        for s in s_vals:
            v = float(np.sign(s) * linthresh * (10.0 ** abs(s) - 1.0))
            v = max(x_min, min(x_max, v))
            breakpoints.append(v)

        # Symlog range for normalization
        s_min = float(symlog(x_min))
        s_max = float(symlog(x_max))
        s_range = s_max - s_min
        if s_range == 0:
            return

        # Build a standalone linear CTF for safe color sampling
        from vtkmodules.vtkRenderingCore import vtkColorTransferFunction

        linear_ctf = vtkColorTransferFunction()
        if linear_rgb_points:
            src = linear_rgb_points
        else:
            src = list(self.lut.RGBPoints)
        for i in range(0, len(src), 4):
            linear_ctf.AddRGBPoint(src[i], src[i + 1], src[i + 2], src[i + 3])

        # Sample RGB from the linear CTF at symlog-normalized positions
        rgb = [0.0, 0.0, 0.0]
        new_rgb_points = []
        for v in breakpoints:
            t = (float(symlog(v)) - s_min) / s_range
            x_lookup = x_min + t * data_range
            linear_ctf.GetColor(x_lookup, rgb)
            new_rgb_points.extend(
                [float(v), float(rgb[0]), float(rgb[1]), float(rgb[2])]
            )

        # Store on proxy for bookkeeping — the actual CTF used by the
        # mapper is a standalone vtkColorTransferFunction built in
        # update_color_preset to avoid proxy client-side object issues.
        self.lut.UseLogScale = 0
        self.lut.RGBPoints = new_rgb_points

    def _apply_discrete_symlog_to_lut(self, linthresh, linear_rgb_points, n_sub=1):
        """Build a discrete (stepped) symlog LUT.

        Each decade interval is split into *n_sub* equal sub-bands in symlog
        space, each with a flat color sampled from the continuous LUT at the
        sub-band midpoint.  Twin control points with a tiny offset create hard
        steps at the sub-band boundaries.  The display image is also replaced
        with a banded colorbar.
        """
        ctf = self.lut.GetClientSideObject()
        x_min, x_max = ctf.GetRange()
        data_range = x_max - x_min
        if data_range == 0:
            return

        def symlog(v):
            v = np.asarray(v, dtype=float)
            return np.sign(v) * np.log10(1.0 + np.abs(v) / linthresh)

        # Build decade boundaries (same logic as symlog ticks)
        boundaries = set()
        if x_min < 0:
            lo = max(linthresh, 1e-30)
            for e in range(
                int(np.floor(np.log10(lo))),
                int(np.floor(np.log10(abs(x_min)))) + 1,
            ):
                val = -(10.0**e)
                if x_min <= val < 0:
                    boundaries.add(val)
        if x_max > 0:
            lo = max(linthresh, 1e-30)
            for e in range(
                int(np.floor(np.log10(lo))),
                int(np.floor(np.log10(x_max))) + 1,
            ):
                val = 10.0**e
                if 0 < val <= x_max:
                    boundaries.add(val)
        if x_min < 0 and x_max > 0:
            boundaries.update((-linthresh, 0.0, linthresh))
        elif x_min < 0 and x_max <= 0:
            if -linthresh >= x_min:
                boundaries.add(-linthresh)
        elif x_min >= 0 and x_max > 0:
            if linthresh <= x_max:
                boundaries.add(linthresh)
        if x_min <= 0 <= x_max:
            boundaries.add(0.0)
        boundaries.add(x_min)
        boundaries.add(x_max)
        # Filter to only values within [x_min, x_max]
        boundaries = sorted(b for b in boundaries if x_min <= b <= x_max)

        if len(boundaries) < 2:
            return

        # Symlog range for normalization
        s_min = float(symlog(x_min))
        s_max = float(symlog(x_max))
        s_range = s_max - s_min
        if s_range == 0:
            return

        # Store boundary values and their display positions (%) for tick alignment.
        # All boundaries are used for discrete bands, but when x_min < 0 we
        # thin the displayed ticks: always show 0, then only every other
        # decade moving outward from 0 in each direction.
        all_tick_data = []
        for bv in boundaries[1:-1]:
            s_val = float(symlog(bv))
            pct = (s_val - s_min) / s_range * 100
            all_tick_data.append({"val": bv, "pos": float(pct)})

        if x_min < 0:
            # Exclude linthresh / -linthresh from tick labels
            lt = float(linthresh)
            filtered = [t for t in all_tick_data if abs(abs(t["val"]) - lt) > 1e-12]
            # Separate into negative, zero, and positive
            neg = [t for t in filtered if t["val"] < 0]
            zero = [t for t in filtered if t["val"] == 0]
            pos = [t for t in filtered if t["val"] > 0]
            # Keep every other decade tick moving outward from 0
            neg_outward = list(reversed(neg))
            thinned_neg = [neg_outward[i] for i in range(0, len(neg_outward), 2)]
            thinned_pos = [pos[i] for i in range(0, len(pos), 2)]
            self._discrete_tick_data = sorted(
                thinned_neg + zero + thinned_pos, key=lambda t: t["val"]
            )
        else:
            self._discrete_tick_data = all_tick_data

        # Build a temporary linear CTF from the saved linear RGB points
        from vtkmodules.vtkRenderingCore import vtkColorTransferFunction

        linear_ctf = vtkColorTransferFunction()
        for i in range(0, len(linear_rgb_points), 4):
            linear_ctf.AddRGBPoint(
                linear_rgb_points[i],
                linear_rgb_points[i + 1],
                linear_rgb_points[i + 2],
                linear_rgb_points[i + 3],
            )

        # For each decade interval, split into n_sub equal sub-bands in
        # symlog space.  Each sub-band gets a flat color sampled from the
        # continuous LUT at the sub-band midpoint.
        rgb = [0.0, 0.0, 0.0]
        eps_data = (x_max - x_min) * 1e-9
        eps_lin = 1e-9
        display_rgb_points = []
        render_rgb_points = []
        band_idx = 0
        total_bands = (len(boundaries) - 1) * n_sub
        for i in range(len(boundaries) - 1):
            s_lo_decade = float(symlog(boundaries[i]))
            s_hi_decade = float(symlog(boundaries[i + 1]))
            for j in range(n_sub):
                # Sub-band edges in symlog space
                s_lo = s_lo_decade + (s_hi_decade - s_lo_decade) * j / n_sub
                s_hi = s_lo_decade + (s_hi_decade - s_lo_decade) * (j + 1) / n_sub
                s_mid = (s_lo + s_hi) / 2.0
                t_mid = (s_mid - s_min) / s_range
                x_lookup = x_min + t_mid * data_range
                linear_ctf.GetColor(x_lookup, rgb)
                r, g, b = float(rgb[0]), float(rgb[1]), float(rgb[2])

                # Invert symlog to get data-space boundaries for rendering
                v_lo = float(np.sign(s_lo) * linthresh * (10.0 ** abs(s_lo) - 1.0))
                v_hi = float(np.sign(s_hi) * linthresh * (10.0 ** abs(s_hi) - 1.0))
                v_lo = max(x_min, min(x_max, v_lo))
                v_hi = max(x_min, min(x_max, v_hi))

                # Linear positions for display image
                t_lo_pos = (s_lo - s_min) / s_range
                t_hi_pos = (s_hi - s_min) / s_range
                d_lo = x_min + t_lo_pos * data_range
                d_hi = x_min + t_hi_pos * data_range

                is_first = band_idx == 0
                is_last = band_idx == total_bands - 1

                if is_first:
                    display_rgb_points.extend([d_lo, r, g, b])
                    render_rgb_points.extend([float(v_lo), r, g, b])
                else:
                    display_rgb_points.extend([d_lo + eps_lin, r, g, b])
                    render_rgb_points.extend([float(v_lo) + eps_data, r, g, b])

                if is_last:
                    display_rgb_points.extend([d_hi, r, g, b])
                    render_rgb_points.extend([float(v_hi), r, g, b])
                else:
                    display_rgb_points.extend([d_hi - eps_lin, r, g, b])
                    render_rgb_points.extend([float(v_hi) - eps_data, r, g, b])

                band_idx += 1

        # Generate the discrete banded colorbar image
        self.lut.RGBPoints = display_rgb_points
        self.config.lut_img = lut_to_img(self.lut)

        # Store rendering points on proxy — the actual CTF used by the
        # mapper is a standalone vtkColorTransferFunction built in
        # update_color_preset to avoid proxy client-side object issues.
        self.lut.RGBPoints = render_rgb_points

        return display_rgb_points

    def color_range_str_to_float(self, color_value_min, color_value_max):
        try:
            min_value = float(color_value_min)
            self.config.color_value_min_valid = not math.isnan(min_value)
        except ValueError:
            self.config.color_value_min_valid = False

        try:
            max_value = float(color_value_max)
            self.config.color_value_max_valid = not math.isnan(max_value)
        except ValueError:
            self.config.color_value_max_valid = False

        if self.config.color_value_min_valid and self.config.color_value_max_valid:
            self.config.color_range = (min_value, max_value)

    @property
    def data_array(self):
        self.source.data_reader.vtk_geometry.Update()
        ds = self.source.data_reader.vtk_geometry.GetOutput()
        return ds.GetCellData().GetArray(self.variable_name)

    def update_color_range(self, *_):
        with perf.timed(f"view.{self.variable_name}.update_color_range"):
            if self.config.override_range:
                skip_update = False
                if math.isnan(self.config.color_range[0]):
                    skip_update = True
                    self.config.color_value_min_valid = False

                if math.isnan(self.config.color_range[1]):
                    skip_update = True
                    self.config.color_value_max_valid = False

                if skip_update:
                    return

                self.lut.RescaleTransferFunction(*self.config.color_range)
            else:
                data_array = self.data_array
                if data_array:
                    with perf.timed(f"view.{self.variable_name}.get_range"):
                        data_range = data_array.GetRange()
                    self.config.color_range = data_range
                    self.config.color_value_min = str(data_range[0])
                    self.config.color_value_max = str(data_range[1])
                    self.config.color_value_min_valid = True
                    self.config.color_value_max_valid = True
                    self.lut.RescaleTransferFunction(*data_range)

            self.update_color_preset(
                self.config.preset,
                self.config.invert,
                self.config.use_log_scale,
                self.config.discrete_log,
                self.config.n_discrete_colors,
            )

    def _compute_ticks(self, linthresh=None, linear_rgb_points=None):
        vmin, vmax = self.config.color_range

        # For discrete mode, use pre-computed boundary positions.
        # For continuous linear, use the same evenly spaced percentage ticks.
        if self.config.discrete_log and hasattr(self, "_discrete_tick_data"):
            ticks = [
                {"position": round(td["pos"], 2), "label": format_tick(td["val"])}
                for td in self._discrete_tick_data
            ]
        elif self.config.use_log_scale == "linear":
            N_INTERVALS = 4
            data_range = vmax - vmin
            ticks = []
            if data_range > 0:
                for i in range(1, N_INTERVALS):
                    val = vmin + data_range * i / N_INTERVALS
                    pos = i / N_INTERVALS * 100
                    ticks.append({"position": round(pos, 2), "label": format_tick(val)})
        else:
            ticks = compute_color_ticks(
                vmin, vmax, scale=self.config.use_log_scale, n=5, linthresh=linthresh
            )
        # Sample colors from the *linear* LUT so tick contrast matches the
        # displayed colorbar image, not the log/symlog-remapped rendering LUT.
        rgb_points = (
            linear_rgb_points if linear_rgb_points else list(self.lut.RGBPoints)
        )
        if len(rgb_points) < 4:
            self.config.color_ticks = []
            return
        img_min = rgb_points[0]
        img_max = rgb_points[-4]
        img_range = img_max - img_min
        if img_range == 0:
            self.config.color_ticks = []
            return
        # Build a temporary linear CTF to sample colors from
        from vtkmodules.vtkRenderingCore import vtkColorTransferFunction

        linear_ctf = vtkColorTransferFunction()
        for i in range(0, len(rgb_points), 4):
            linear_ctf.AddRGBPoint(
                rgb_points[i], rgb_points[i + 1], rgb_points[i + 2], rgb_points[i + 3]
            )
        rgb = [0.0, 0.0, 0.0]
        for tick in ticks:
            t = tick["position"] / 100.0
            value = img_min + t * img_range
            linear_ctf.GetColor(value, rgb)
            tick["color"] = tick_contrast_color(rgb[0], rgb[1], rgb[2])
        self.config.color_ticks = ticks

    def _build_ui(self):
        with DivLayout(
            self.server, template_name=self.name, connect_parent=False, classes="h-100"
        ) as self.ui:
            self.ui.root.classes = "h-100"
            with v3.VCard(
                variant="tonal",
                style=(
                    "active_layout !== 'auto_layout' ? `height: calc(100% - ${top_padding}px;` : 'overflow-hidden'",
                ),
                tile=("active_layout !== 'auto_layout'",),
                raw_attrs=[f'data-field-name="{self.variable_name}"'],
            ):
                with v3.VRow(
                    dense=True,
                    classes="ma-0 pa-0 bg-black opacity-90 d-flex align-center flex-nowrap",
                ):
                    tview.create_size_menu(self.name, self.config)
                    with html.Div(
                        self.variable_name,
                        classes="text-subtitle-2 pr-2 text-truncate",
                        style="user-select: none;",
                        title=self.variable_name,
                    ):
                        with v3.VMenu(activator="parent"):
                            with v3.VList(density="compact", style="max-height: 40vh;"):
                                with self.config.provide_as("config"):
                                    v3.VListItem(
                                        subtitle=("name",),
                                        v_for="name, idx in config.swap_group",
                                        key="name",
                                        click=(
                                            self.ctrl.swap_variables,
                                            "[config.variable, name]",
                                        ),
                                    )

                    v3.VIcon(
                        "mdi-lock-outline",
                        size="x-small",
                        v_show=("lock_views", True),
                        style="transform: scale(0.75);",
                    )

                    v3.VSpacer()
                    html.Div(
                        "t = {{ time_idx }}",
                        classes="text-caption px-1 text-no-wrap",
                        v_if="timestamps.length > 1",
                    )
                    if self.variable_type == "m":
                        html.Div(
                            "[k = {{ midpoint_idx }}]",
                            classes="text-caption px-1 text-no-wrap",
                            v_if="midpoints.length > 1",
                        )
                    if self.variable_type == "i":
                        html.Div(
                            "[k = {{ interface_idx }}]",
                            classes="text-caption px-1 text-no-wrap",
                            v_if="interfaces.length > 1",
                        )
                    v3.VSpacer()
                    html.Div(
                        "avg = {{"
                        f"fields_avgs['{self.variable_name}']?.toExponential(2) || 'N/A'"
                        "}}",
                        classes="text-caption px-1 text-no-wrap",
                    )
                    v3.VIconBtn(
                        v_tooltip_bottom="'Capture panel as PNG'",
                        icon="mdi-camera",
                        size="x-small",
                        variant="plain",
                        click=f"utils.quickview.capturePanel('{self.variable_name}', time_idx, midpoint_idx, interface_idx)",
                    )

                with html.Div(
                    style=(
                        """
                        {
                            aspectRatio: active_layout === 'auto_layout' ? aspect_ratio : null,
                            height: active_layout !== 'auto_layout' ? 'calc(100% - 2.4rem)' : null,
                            pointerEvents: lock_views ? 'none': null,
                        }
                        """,
                    ),
                ):
                    display = rca.RemoteControlledArea(display="image")
                    handler = display.create_view_handler(
                        self.view.GetRenderWindow(),
                        encoder="turbo-jpeg",
                    )
                    self.ctx[self.name] = handler

                tview.create_bottom_bar(self.config, self.update_color_preset)


class ViewManager(TrameComponent):
    def __init__(self, server, source):
        super().__init__(server)
        self.use_image_stream = False
        self.source = source
        self._var2view = {}
        self._camera_sync_in_progress = False
        self._last_vars = {}
        self._active_configs = {}

        rca.initialize(self.server)

        self.state.luts_normal = [
            {"name": k, "url": v["normal"], "safe": k in COLOR_BLIND_SAFE}
            for k, v in COLORBAR_CACHE.items()
        ]
        self.state.luts_inverted = [
            {"name": k, "url": v["inverted"], "safe": k in COLOR_BLIND_SAFE}
            for k, v in COLORBAR_CACHE.items()
        ]

        # Sort lists
        self.state.luts_normal.sort(key=lut_name)
        self.state.luts_inverted.sort(key=lut_name)

    def refresh_ui(self, **_):
        for view in self._var2view.values():
            view._build_ui()

    def reset_camera(self):
        views = list(self._var2view.values())
        for view in views:
            view.disable_render = True

        for view in views:
            view.reset_camera()

        for view in views:
            view.disable_render = False

    def render(self):
        for view in list(self._var2view.values()):
            view.render()

    def update_color_range(self):
        for view in list(self._var2view.values()):
            view.update_color_range()

    def get_view(self, variable_name, variable_type):
        view = self._var2view.get(variable_name)
        if view is None:
            view = VariableView(self.server, self.source, variable_name, variable_type)
            self._var2view[variable_name] = view
            view.set_camera_modified(self.sync_camera)

        return view

    def sync_camera(self, camera, *_):
        if self._camera_sync_in_progress:
            return
        self._camera_sync_in_progress = True

        for var_view in self._var2view.values():
            cam = var_view.camera
            if cam is camera:
                continue
            cam.DeepCopy(camera)
            var_view.render()

        self._camera_sync_in_progress = False

    @controller.set("swap_variables")
    def swap_variable(self, variable_a, variable_b):
        config_a = self._active_configs[variable_a]
        config_b = self._active_configs[variable_b]
        config_a.order, config_b.order = config_b.order, config_a.order
        config_a.size, config_b.size = config_b.size, config_a.size
        config_a.offset, config_b.offset = config_b.offset, config_a.offset
        config_a.break_row, config_b.break_row = config_b.break_row, config_a.break_row

    def apply_size(self, n_cols):
        if not self._last_vars:
            return

        if n_cols == 0:
            # Auto based on group size
            if self.state.layout_grouped:
                for var_type in "smi":
                    var_names = self._last_vars[var_type]
                    total_size = len(var_names)

                    if total_size == 0:
                        continue

                    size = auto_size_to_col(total_size)
                    for name in var_names:
                        config = self.get_view(name, var_type).config
                        config.size = size

            else:
                size = auto_size_to_col(len(self._active_configs))
                for config in self._active_configs.values():
                    config.size = size
        else:
            # uniform size
            for config in self._active_configs.values():
                config.size = COL_SIZE_LOOKUP[n_cols]

    def build_auto_layout(self, variables=None):
        if variables is None:
            variables = self._last_vars

        self._last_vars = variables

        # Create UI based on variables
        self.state.swap_groups = {}
        # Build a lookup from type name to color from state.variable_types
        type_to_color = {vt["name"]: vt["color"] for vt in self.state.variable_types}
        with DivLayout(self.server, template_name="auto_layout") as self.ui:
            self.ui.root.classes = "all-variables"
            if self.state.layout_grouped:
                with v3.VCol(classes="pa-1"):
                    for var_type in variables.keys():
                        var_names = variables[var_type]
                        total_size = len(var_names)

                        if total_size == 0:
                            continue

                        # Look up color from variable_types to match chip colors
                        border_color = type_to_color.get(", ".join(var_type), "primary")
                        with v3.VAlert(
                            border="start",
                            classes="pr-1 py-1 pl-3 mb-1",
                            variant="flat",
                            border_color=border_color,
                        ):
                            with v3.VRow(dense=True):
                                for name in var_names:
                                    view = self.get_view(name, var_type)
                                    view.config.swap_group = sorted(
                                        [n for n in var_names if n != name]
                                    )
                                    with view.config.provide_as("config"):
                                        v3.VCol(
                                            v_if="config.break_row",
                                            cols=12,
                                            classes="pa-0",
                                            style=("`order: ${config.order};`",),
                                        )
                                        # For flow handling
                                        with v3.Template(v_if="!config.size"):
                                            v3.VCol(
                                                v_for="i in config.offset",
                                                key="i",
                                                style=("{ order: config.order }",),
                                            )
                                        with v3.VCol(
                                            offset=("config.offset * config.size",),
                                            cols=("config.size",),
                                            style=("`order: ${config.order};`",),
                                        ):
                                            client.ServerTemplate(name=view.name)
            else:
                all_names = [name for names in variables.values() for name in names]
                with v3.VRow(dense=True, classes="pa-2"):
                    for var_type in variables.keys():
                        var_names = variables[var_type]
                        for name in var_names:
                            view = self.get_view(name, var_type)
                            view.config.swap_group = sorted(
                                [n for n in all_names if n != name]
                            )
                            with view.config.provide_as("config"):
                                v3.VCol(
                                    v_if="config.break_row",
                                    cols=12,
                                    classes="pa-0",
                                    style=("`order: ${config.order};`",),
                                )

                                # For flow handling
                                with v3.Template(v_if="!config.size"):
                                    v3.VCol(
                                        v_for="i in config.offset",
                                        key="i",
                                        style=("{ order: config.order }",),
                                    )
                                with v3.VCol(
                                    offset=(
                                        "config.size ? config.offset * config.size : 0",
                                    ),
                                    cols=("config.size",),
                                    style=("`order: ${config.order};`",),
                                ):
                                    client.ServerTemplate(name=view.name)

        # Assign any missing order
        self._active_configs = {}
        existed_order = set()
        order_max = 0
        orders_to_update = []
        for var_type, var_names in variables.items():
            for name in var_names:
                config = self.get_view(name, var_type).config
                self._active_configs[name] = config
                if config.order:
                    order_max = max(order_max, config.order)
                    assert config.order not in existed_order, "Order already assigned"
                    existed_order.add(config.order)
                else:
                    orders_to_update.append(config)

        next_order = order_max + 1
        for config in orders_to_update:
            config.order = next_order
            next_order += 1
