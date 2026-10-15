"""Plywood box with printed corner brackets.

Five plywood panels (bottom + four walls) cut on the Shaper, held together by
four printed corner brackets inside the box. Each bracket has:

  - a vertical rib on each leg that drops into a notch in the wall's bottom
    edge (you see the rib's end on the outside of the box, a small coloured
    rectangle at each corner),
  - a square tab underneath that drops into a slot in the bottom panel,
  - optional screw holes through the legs.

The ribs and tabs locate everything square; glue or screws hold it.

Everything below comes from one set of parameters, so changing the measured
plywood thickness moves the wall lengths, the notches, and the rib depths
together.

Run:  python3 box.py
Out:  out/*.svg   panels for the Shaper (one file per identical set)
      out/*.stl   bracket and fit-test coupon for the printer
      out/assembly.step   the whole box in 3D, to look over in a viewer

Units: millimetres.
"""

import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.printing import export_stl, interference  # noqa: E402
from lib.shaper_svg import BITS, ShaperSVG, check_bit, rect, relieved_rect  # noqa: E402

# ---------------------------------------------------------------------------
# Parameters. Anything marked MEASURE must be set from the real material.
# ---------------------------------------------------------------------------

# Material: nominal 1/2 in plywood (see notes/materials.md)
T_WALL = 12.0  # MEASURE: wall sheet thickness, average of several caliper readings
T_BOTTOM = 12.0  # MEASURE: bottom sheet thickness (can be thinner ply, e.g. 1/4 in)
THICKNESS_MEASURED = False  # set True once both values above come from calipers

# Box, outside dimensions
BOX_L = 200.0  # along X (front and back walls run this way)
BOX_W = 150.0  # along Y
BOX_H = 100.0  # bottom of bottom panel to top of walls

# Shaper
BIT_D = BITS["1/4in"]  # bit used for every cut in these files; 1/8 in also on hand
RELIEF_STYLE = "dogbone"  # "dogbone", "tbone-x" or "tbone-y" (see lib/shaper_svg.py)
OVERCUT = 0.5  # through-cuts go this far past the material into the spoilboard

# Bracket
LEG_LEN = 50.0  # length of each leg along its wall, from the inside corner
LEG_T = 4.0  # leg thickness
CORNER_BLOCK = 14.0  # solid square post in the corner for stiffness
BRACKET_H = 50.0  # bracket height, also the wall-notch height
RIB_W = 12.0  # rib width along the wall (the wall notch is this wide)
RIB_POS = 24.0  # rib centre, distance from the inside corner along the leg
BOTTOM_TAB = 10.0  # square tab under the corner block (the bottom slot is this size)
FLUSH_GAP = 0.5  # ribs and tabs stop this far short of the outside face, so they never stick out
SCREW_D = 3.5  # through holes in the legs for small wood screws; 0 for glue only
SCREW_FROM_END = 6.0  # hole centre distance from the leg's far end

# Fit. Wood is cut at the nominal size; printed ribs and tabs are made smaller
# by this much in total (half each side). Tune with the coupon.
FIT_CLEARANCE = 0.3
COUPON_CLEARANCES = [0.1, 0.3, 0.5, 0.7]

OUT = Path(__file__).resolve().parent / "out"

# ---------------------------------------------------------------------------
# Derived sizes
# ---------------------------------------------------------------------------

WALL_H = BOX_H - T_BOTTOM
SIDE_L = BOX_W - 2 * T_WALL  # side walls fit between the front and back walls
NOTCH_OVERRUN = BIT_D  # notch rectangles run past the panel edge so the edge corners stay sharp


def check_params():
    ok = True
    ok &= check_bit("wall notch", RIB_W, BIT_D)
    ok &= check_bit("bottom slot", BOTTOM_TAB, BIT_D)
    if BOTTOM_TAB > CORNER_BLOCK - 2:
        print("WARNING: bottom tab is wider than the corner block it hangs from")
        ok = False
    if RIB_POS - RIB_W / 2 < CORNER_BLOCK / 2 or RIB_POS + RIB_W / 2 > LEG_LEN:
        print("WARNING: rib doesn't sit on the leg")
        ok = False
    if SCREW_D and LEG_LEN - SCREW_FROM_END - SCREW_D / 2 < RIB_POS + RIB_W / 2:
        print("WARNING: screw hole runs into the rib")
        ok = False
    if BRACKET_H > WALL_H:
        print("WARNING: bracket is taller than the walls")
        ok = False
    if not THICKNESS_MEASURED:
        print("NOTE: THICKNESS_MEASURED is False; these files use placeholder thicknesses.")
    return ok


# ---------------------------------------------------------------------------
# Wood panels, as 2D faces (X right, Y up, origin at the panel's lower left)
# ---------------------------------------------------------------------------


def edge_notch(u, width, height):
    """Notch up from the panel's bottom edge, reliefs only at the two inner corners."""
    h = height + NOTCH_OVERRUN
    return relieved_rect(u, height - h / 2, width, h, BIT_D, RELIEF_STYLE, corners={"+x+y", "-x+y"})


def wall_panel(length, notch_us):
    face = rect(length / 2, WALL_H / 2, length, WALL_H)
    for u in notch_us:
        face = face.cut(edge_notch(u, RIB_W, BRACKET_H)).Faces()[0]
    return face


def long_wall():
    """Front and back walls run the full box length."""
    return wall_panel(BOX_L, [T_WALL + RIB_POS, BOX_L - T_WALL - RIB_POS])


def short_wall():
    """Side walls fit between the long walls, so they're 2 x thickness shorter."""
    return wall_panel(SIDE_L, [RIB_POS, SIDE_L - RIB_POS])


def bottom_panel():
    face = rect(BOX_L / 2, BOX_W / 2, BOX_L, BOX_W)
    c = T_WALL + CORNER_BLOCK / 2
    for x in (c, BOX_L - c):
        for y in (c, BOX_W - c):
            face = face.cut(relieved_rect(x, y, BOTTOM_TAB, BOTTOM_TAB, BIT_D, RELIEF_STYLE)).Faces()[0]
    return face


def wood_coupon():
    """Same sheet, same bit: one wall-style notch and one bottom-style slot."""
    w, h = 80.0, 50.0
    face = rect(w / 2, h / 2, w, h)
    face = face.cut(edge_notch(20, RIB_W, 25)).Faces()[0]
    face = face.cut(relieved_rect(55, 25, BOTTOM_TAB, BOTTOM_TAB, BIT_D, RELIEF_STYLE)).Faces()[0]
    return face


# ---------------------------------------------------------------------------
# Printed parts (built in their in-box orientation: corner at the origin,
# legs along +X and +Y, bottom at z = 0, walls on the -X and -Y sides)
# ---------------------------------------------------------------------------


def box_solid(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def bracket(clearance=FIT_CLEARANCE):
    h = BRACKET_H
    rw = RIB_W - clearance
    rd = T_WALL - FLUSH_GAP
    bt = BOTTOM_TAB - clearance
    td = T_BOTTOM - FLUSH_GAP

    b = box_solid(0, LEG_LEN, 0, LEG_T, 0, h)  # leg along X
    b = b.union(box_solid(0, LEG_T, 0, LEG_LEN, 0, h))  # leg along Y
    b = b.union(box_solid(0, CORNER_BLOCK, 0, CORNER_BLOCK, 0, h))
    # Ribs, into the walls. Shortened at the top by the clearance so they
    # don't bottom out against the top of the notch.
    b = b.union(box_solid(RIB_POS - rw / 2, RIB_POS + rw / 2, -rd, 0, 0, h - clearance))
    b = b.union(box_solid(-rd, 0, RIB_POS - rw / 2, RIB_POS + rw / 2, 0, h - clearance))
    # Tab into the bottom panel
    c = CORNER_BLOCK / 2
    b = b.union(box_solid(c - bt / 2, c + bt / 2, c - bt / 2, c + bt / 2, -td, 0))
    if SCREW_D:
        u = LEG_LEN - SCREW_FROM_END
        for z in (h * 0.3, h * 0.75):
            b = b.cut(cq.Workplane("XZ").circle(SCREW_D / 2).extrude(-LEG_T * 3).translate((u, -LEG_T, z)))
            b = b.cut(cq.Workplane("YZ").circle(SCREW_D / 2).extrude(LEG_T * 3).translate((-LEG_T, u, z)))
    return b


def print_coupon():
    """Two rows of test tabs on a base plate: rib-sized and bottom-tab-sized,
    one per clearance, numbered 1..n."""
    n = len(COUPON_CLEARANCES)
    pitch = max(RIB_W, BOTTOM_TAB) + 8
    plate_t = 3.0
    length = n * pitch + 8
    row_rib_y, row_tab_y = 10.0, 10.0 + T_WALL + 8
    width = row_tab_y + BOTTOM_TAB + 8
    plate = box_solid(0, length, 0, width, 0, plate_t)
    for i, c in enumerate(COUPON_CLEARANCES):
        x = 4 + pitch * (i + 0.5)
        rw, rd = RIB_W - c, T_WALL - FLUSH_GAP
        plate = plate.union(box_solid(x - rw / 2, x + rw / 2, row_rib_y, row_rib_y + rd, plate_t, plate_t + 15))
        bt = BOTTOM_TAB - c
        plate = plate.union(
            box_solid(x - bt / 2, x + bt / 2, row_tab_y, row_tab_y + bt, plate_t, plate_t + T_BOTTOM - FLUSH_GAP)
        )
        label = cq.Workplane("XY").text(str(i + 1), 5, -0.6, kind="bold").translate((x, 4.5, plate_t))
        plate = plate.cut(label)
    return plate


# ---------------------------------------------------------------------------
# 3D assembly (for checking only)
# ---------------------------------------------------------------------------


def panel_solid(face, t):
    return cq.Workplane("XY").add(cq.Solid.extrudeLinear(face, cq.Vector(0, 0, t)))


def assembly():
    parts = {}
    lw = panel_solid(long_wall(), T_WALL).rotate((0, 0, 0), (1, 0, 0), 90)  # thickness now y in [-T, 0]
    parts["front"] = lw.translate((0, T_WALL, T_BOTTOM))
    parts["back"] = lw.translate((0, BOX_W, T_BOTTOM))
    sw = panel_solid(short_wall(), T_WALL).rotate((0, 0, 0), (1, 0, 0), 90).rotate((0, 0, 0), (0, 0, 1), 90)
    # after the second turn: length along y, thickness x in [0, T]
    parts["left"] = sw.translate((0, T_WALL, T_BOTTOM))
    parts["right"] = sw.translate((BOX_L - T_WALL, T_WALL, T_BOTTOM))
    parts["bottom"] = panel_solid(bottom_panel(), T_BOTTOM)
    br = bracket()
    for name, mx, my in (("br_fl", False, False), ("br_fr", True, False), ("br_bl", False, True), ("br_br", True, True)):
        b = br
        if mx:
            b = b.mirror("YZ")
        if my:
            b = b.mirror("XZ")
        x = BOX_L - T_WALL if mx else T_WALL
        y = BOX_W - T_WALL if my else T_WALL
        parts[name] = b.translate((x, y, T_BOTTOM))
    return parts


def check_assembly(parts):
    names = list(parts)
    worst = 0.0
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            v = interference(parts[a], parts[b])
            if v > 0.01:
                print(f"  CLASH: {a} and {b} overlap by {v:.2f} mm^3")
            worst = max(worst, v)
    if worst <= 0.01:
        print("  assembly check: no parts overlap")
    return worst


# ---------------------------------------------------------------------------


def svg_notes(t):
    status = "measured" if THICKNESS_MEASURED else "PLACEHOLDER - NOT MEASURED, do not cut good stock"
    return [
        f"Material thickness: {t:.2f} mm ({status}).",
        f"Through-cut depth: {t + OVERCUT:.2f} mm (thickness + {OVERCUT} mm overcut).",
        f"Corner reliefs: {RELIEF_STYLE}, sized for the {BIT_D:.2f} mm bit. A different bit needs a re-run.",
        "Panel orientation doesn't matter: every notch and slot goes right through.",
    ]


def main():
    OUT.mkdir(exist_ok=True)
    print("checks:")
    check_params()

    print("Shaper SVGs:")
    panels = [
        ("wall_long_x2", long_wall(), T_WALL, "Long wall (front/back), cut 2"),
        ("wall_short_x2", short_wall(), T_WALL, "Short wall (sides), cut 2"),
        ("bottom_x1", bottom_panel(), T_BOTTOM, "Bottom, cut 1"),
        ("coupon_wood", wood_coupon(), T_WALL, "Fit-test coupon, cut 1 from the wall sheet"),
    ]
    for name, face, t, title in panels:
        svg = ShaperSVG(BIT_D, notes=svg_notes(t))
        svg.add_part(face, depth=t + OVERCUT)
        path = svg.write(OUT / f"{name}.svg", title=title)
        bb = face.BoundingBox()
        print(f"  {path.name}: {bb.xlen:.1f} x {bb.ylen:.1f} mm, {svg.summary()}")

    print("STLs (in print orientation):")
    # Bracket printed upside down: flat top on the bed, ribs vertical, tab up.
    export_stl(bracket().rotate((0, 0, 0), (1, 0, 0), 180), OUT / "bracket_x4.stl")
    export_stl(print_coupon(), OUT / "coupon_print.stl")

    print("assembly:")
    parts = assembly()
    check_assembly(parts)
    cq.exporters.export(cq.Workplane().add([p.val() for p in parts.values()]), str(OUT / "assembly.step"))
    print("  wrote assembly.step")


if __name__ == "__main__":
    main()
