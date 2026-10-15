"""ShaperTape spacing jig for the Shaper Origin (Gen 1).

Origin finds its position by looking at ShaperTape stuck to the work surface.
The tape works best laid in straight, parallel strips at a steady spacing.
This jig is a printed bar with grooves on its underside, each one exactly a
strip of tape wide. Sit one groove over a strip that's already down, then feed
the next strip along the other groove: it comes out parallel and at the set
spacing. Use two jigs (one near each end of the strip) for long strips.

Run:  python3 jig.py      (from this folder, or anywhere)
Out:  out/jig.stl, out/fit_coupon.stl

Units: millimetres.
"""

from pathlib import Path

import cadquery as cq

# ---------------------------------------------------------------------------
# Parameters. Values marked MEASURE or CHECK must be confirmed before printing.
# ---------------------------------------------------------------------------

# The tape
TAPE_WIDTH = 12.7  # MEASURE: ShaperTape is sold as 1/2 in wide; measure a strip with calipers
TAPE_SPACING = 80.0  # CHECK: centre-to-centre spacing; set from Shaper's current tape-placement guidance
N_GROOVES = 2  # 2 = place one new strip; 3 = place two at once (makes the bar longer)

# Fit of the tape in the groove
GROOVE_CLEARANCE = 0.4  # total extra width over TAPE_WIDTH (0.2 mm per side); tune with the coupon
GROOVE_DEPTH = 1.0  # tape is thin; this only needs to clear it and give its edges a wall
LEAD_IN = 0.6  # chamfer on groove edges so the tape doesn't snag going in

# The bar
BAR_WIDTH = 30.0  # along the tape direction; wider = squarer to the tape, longer print
BAR_THICKNESS = 6.0  # stiff enough not to flex, thin enough to print fast
END_MARGIN = 12.0  # solid material beyond the outer grooves
EDGE_FILLET = 1.0  # softens outside edges (top and ends only; the bottom stays sharp to sit flat)
CENTRE_NOTCH = 1.2  # depth of V notches on the long sides marking each groove's centre line

# Fit-test coupon: one groove per clearance, numbered on the groove face
COUPON_CLEARANCES = [0.2, 0.4, 0.6, 0.8]
COUPON_PITCH = 22.0  # groove-to-groove spacing on the coupon
COUPON_WIDTH = 20.0
COUPON_THICKNESS = 4.0

# Printer limit (FlashForge Creator Pro, comfortable size; see notes/printers.md)
PRINT_MAX = 140.0

OUT = Path(__file__).resolve().parent / "out"

# ---------------------------------------------------------------------------


def groove_width(clearance):
    return TAPE_WIDTH + clearance


def bar_with_grooves(groove_xs, widths, length, width, thickness):
    """A bar lying on XY with grooves cut into its underside (z = 0 face).

    Grooves run along Y (the tape direction), centred at each x in groove_xs.
    """
    bar = cq.Workplane("XY").box(length, width, thickness, centered=(True, True, False))
    if EDGE_FILLET > 0:
        # Round the top edges and vertical corners, keep the bottom face sharp
        # so the bar sits flat and the groove walls run right to the surface.
        bar = bar.edges(">Z or |Z").fillet(EDGE_FILLET)
    for x, w in zip(groove_xs, widths):
        groove = (
            cq.Workplane("XY")
            .center(x, 0)
            .rect(w, width + 2)  # run out past both sides of the bar
            .extrude(GROOVE_DEPTH)
        )
        bar = bar.cut(groove)
        if LEAD_IN > 0:
            # Chamfer the two long groove edges at the bottom face. A small
            # triangular prism each side does it without fragile edge selectors.
            for side in (-1, 1):
                edge_x = x + side * w / 2
                tri = (
                    cq.Workplane("XZ")
                    .polyline(
                        [
                            (edge_x, 0),
                            (edge_x + side * LEAD_IN, 0),
                            (edge_x, LEAD_IN),
                        ]
                    )
                    .close()
                    .extrude(width / 2 + 1, both=True)
                )
                bar = bar.cut(tri)
    return bar


def centre_notches(bar, xs, width, thickness):
    """V notches through the full thickness on both long sides at each x."""
    for x in xs:
        for side in (-1, 1):
            y_edge = side * width / 2
            v = (
                cq.Workplane("XY")
                .polyline(
                    [
                        (x - CENTRE_NOTCH, y_edge),
                        (x + CENTRE_NOTCH, y_edge),
                        (x, y_edge - side * CENTRE_NOTCH),
                    ]
                )
                .close()
                .extrude(thickness)
            )
            bar = bar.cut(v)
    return bar


def make_jig():
    span = (N_GROOVES - 1) * TAPE_SPACING
    w = groove_width(GROOVE_CLEARANCE)
    length = span + w + 2 * END_MARGIN
    xs = [-span / 2 + i * TAPE_SPACING for i in range(N_GROOVES)]
    bar = bar_with_grooves(xs, [w] * N_GROOVES, length, BAR_WIDTH, BAR_THICKNESS)
    bar = centre_notches(bar, xs, BAR_WIDTH, BAR_THICKNESS)
    return bar, length


def make_coupon():
    n = len(COUPON_CLEARANCES)
    widths = [groove_width(c) for c in COUPON_CLEARANCES]
    length = (n - 1) * COUPON_PITCH + max(widths) + 2 * 8.0
    xs = [-(n - 1) * COUPON_PITCH / 2 + i * COUPON_PITCH for i in range(n)]
    bar = bar_with_grooves(xs, widths, length, COUPON_WIDTH, COUPON_THICKNESS)
    # Number each groove 1..n, cut 0.4 mm into the groove face on the land just
    # left of each groove. Mirrored so it reads correctly when you look at the
    # groove face.
    for i, (x, w) in enumerate(zip(xs, widths)):
        # centre of the land between the previous groove (or the bar end) and this one
        left = -length / 2 if i == 0 else xs[i - 1] + widths[i - 1] / 2
        land_x = (left + x - w / 2) / 2
        label = (
            cq.Workplane("XY")
            .text(str(i + 1), 5, 0.4, kind="bold", halign="center", valign="center")
            .mirror("YZ")
            .translate((land_x, 0, 0))
        )
        bar = bar.cut(label)
    return bar, length


def check_size(name, shape):
    bb = shape.val().BoundingBox()
    dims = (bb.xlen, bb.ylen, bb.zlen)
    print(f"{name}: {dims[0]:.1f} x {dims[1]:.1f} x {dims[2]:.1f} mm")
    if max(dims) > PRINT_MAX:
        print(f"  WARNING: {name} is larger than {PRINT_MAX} mm; check it fits the printer")
    return dims


def main():
    OUT.mkdir(exist_ok=True)
    jig, _ = make_jig()
    coupon, _ = make_coupon()
    check_size("jig", jig)
    check_size("fit_coupon", coupon)
    # Export upside down (grooves facing up): the flat top prints on the bed,
    # the groove walls print crisp with no bridging, and elephant's foot lands
    # on a face that doesn't touch the tape.
    for name, part in (("jig", jig), ("fit_coupon", coupon)):
        flipped = part.rotate((0, 0, 0), (1, 0, 0), 180)
        bb = flipped.val().BoundingBox()
        flipped = flipped.translate((0, 0, -bb.zmin))
        path = OUT / f"{name}.stl"
        cq.exporters.export(flipped, str(path), tolerance=0.02, angularTolerance=0.1)
        print(f"wrote {path.relative_to(OUT.parent)}")


if __name__ == "__main__":
    main()
