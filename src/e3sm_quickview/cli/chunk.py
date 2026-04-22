"""Rechunk monthly_ne1024 with HDF5-friendly chunk sizes (~4 MB each).

Chunk shape for vars with ncol: (1,...,1M,...,1) — 1M cells in ncol,
1 in every other dim. Each chunk is ~4 MB (float32 × 1M). One lev-slice
read = 24 sequential chunks = ~100 MB of I/O, no small-chunk metadata
overhead, small enough for HDF5's default chunk cache.
"""

import argparse
import sys
import time
from pathlib import Path

import netCDF4

NCOL_CHUNK = 1_048_576  # ~4 MB per chunk at float32


def convert(src_file, dst_file=None):
    src_file = Path(src_file).resolve()

    if not src_file.exists():
        raise FileNotFoundError(f"Source file not found: {src_file}")

    if dst_file is None:
        dst_file = src_file.with_name(src_file.name.replace(".nc", ".chunked.nc"))

    dst_file = Path(dst_file).resolve()

    if dst_file.exists():
        dst_file.unlink()

    t_all = time.perf_counter()

    with netCDF4.Dataset(src_file, "r") as src:
        with netCDF4.Dataset(dst_file, "w", format="NETCDF4") as dst:
            for name, dim in src.dimensions.items():
                dst.createDimension(name, len(dim))
                dst.setncatts({k: src.getncattr(k) for k in src.ncattrs()})

            for name, var in src.variables.items():
                dims = var.dimensions
                sizes = var.shape
                if "ncol" in dims:
                    ncol_size = len(src.dimensions["ncol"])
                    chunks = tuple(
                        min(NCOL_CHUNK, ncol_size) if d == "ncol" else 1 for d in dims
                    )
                else:
                    chunks = None

                t0 = time.perf_counter()
                out_var = dst.createVariable(
                    name,
                    var.dtype,
                    dims,
                    chunksizes=chunks,
                    zlib=False,
                    fill_value=False,
                )
                out_var.setncatts({k: var.getncattr(k) for k in var.ncattrs()})

                data = var[:]
                t_read = time.perf_counter() - t0

                t0 = time.perf_counter()
                out_var[:] = data
                t_write = time.perf_counter() - t0

                sys.stdout.write(
                    f"  {name:20s} shape={sizes} chunks={chunks} "
                    f"read={t_read:6.1f}s write={t_write:6.1f}s "
                    f"size={data.nbytes / 1e9:.2f}GB\n"
                )
                sys.stdout.flush()
                del data

    print(f"\nTotal: {time.perf_counter() - t_all:.1f} s")
    print(f"Output size: {dst_file.stat().st_size / 1e9:.2f} GB")


def main():
    parser = argparse.ArgumentParser(
        prog="quickview-chunk",
        description="Chunk NetCDF dataset for faster data access",
    )
    parser.add_argument("--input", help="Input NetCDF file to chunk", required=True)
    parser.add_argument("--output", help="Name of the output NetCDF file", default=None)
    args = parser.parse_args()
    convert(args.input, args.output)


if __name__ == "__main__":
    main()
