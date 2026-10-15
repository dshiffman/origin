"""STL export and printer checks shared by projects.

Limits come from notes/printers.md: keep parts inside ~140 mm a side for the
FlashForge Creator Pro; a ~100 mm circle if it must also fit the Mini Delta.
"""

from pathlib import Path

import cadquery as cq

CREATOR_PRO_MAX = 140.0
MINI_DELTA_DIAMETER = 100.0


def _shape(part):
    return part.val() if isinstance(part, cq.Workplane) else part


def check_print_size(name, part, limit=CREATOR_PRO_MAX):
    """Print the part's size and which printer(s) it fits. Returns (x, y, z)."""
    bb = _shape(part).BoundingBox()
    dims = (bb.xlen, bb.ylen, bb.zlen)
    fits_delta = (bb.xlen**2 + bb.ylen**2) ** 0.5 <= MINI_DELTA_DIAMETER and bb.zlen <= 110
    note = "fits both printers" if fits_delta else "Creator Pro only"
    print(f"  {name}: {dims[0]:.1f} x {dims[1]:.1f} x {dims[2]:.1f} mm ({note})")
    if max(dims) > limit:
        print(f"  WARNING: {name} exceeds {limit:.0f} mm; split it or check it fits")
    return dims


def export_stl(part, path, name=None):
    """Export a part already rotated into its print orientation; drops it onto z=0."""
    shape = _shape(part)
    bb = shape.BoundingBox()
    shape = shape.translate(cq.Vector(0, 0, -bb.zmin))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    check_print_size(name or path.stem, shape)
    cq.exporters.export(shape, str(path), tolerance=0.02, angularTolerance=0.1)
    return path


def interference(a, b):
    """Volume (mm^3) shared by two solids. ~0 means they fit without clashing."""
    common = _shape(a).intersect(_shape(b))
    return sum(s.Volume() for s in common.Solids())
