"""Microduck dock: plywood base + printed cradle, post and cable clips.

The duck stands on the base with its feet on marked spots. Behind it a printed
post holds a U-shaped cradle at torso height that wraps around the duck's back
and sides, so a parked (or powered-off) duck can lean back into it instead of
falling over while it charges. The USB-C cable runs down the post and along the
base in clip-on/screw-down clips.

  base (plywood, Shaper) --tenon in slot-- post (print) --peg in socket-- cradle (print)

Robot sizes: only height (~25 cm), width (~14 cm) and mass (<800 g) are
published. Everything marked GUESS is a placeholder to confirm by measuring
the duck when it arrives (Christmas 2026). The base outline and post joint
don't depend on the guesses much; the foot marks and cradle do, which is why
the foot marks default to guide lines (drawn on screen, not cut).

Run:  python3 dock.py
Out:  out/base_x1.svg, out/*.stl, out/assembly.step

Units: millimetres.
"""

import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.printing import export_stl, interference  # noqa: E402
from lib.shaper_svg import (  # noqa: E402
    BITS,
    ShaperSVG,
    check_bit,
    cross_mark,
    relieved_rect,
    rounded_rect,
)

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

# Microduck. PUBLISHED = from Pollen Robotics / press coverage (Aug 2026).
DUCK_HEIGHT = 250.0  # PUBLISHED: ~25 cm tall
DUCK_WIDTH = 140.0  # PUBLISHED: ~14 cm wide (overall)
DUCK_MASS_KG = 0.8  # PUBLISHED: under 800 g
TORSO_W = 100.0  # GUESS: torso width where the cradle touches it
TORSO_D = 80.0  # GUESS: torso front-to-back depth
CRADLE_Z = 120.0  # GUESS: cradle centre height above the base top (aim for just below the torso's widest point)
FOOT_L = 60.0  # GUESS: foot length
FOOT_W = 40.0  # GUESS: foot width
FOOT_SPACING = 70.0  # GUESS: foot centre to foot centre, side to side, in a relaxed stance
CABLE_D = 4.0  # GUESS: USB-C cable outer diameter; measure the cable that ships with it

# Base: nominal 3/4 in plywood, heavy enough to keep a 25 cm robot from tipping it
BASE_T = 18.0  # MEASURE: sheet thickness, average of several caliper readings
THICKNESS_MEASURED = False
BASE_W = 200.0  # side to side (X)
BASE_D = 220.0  # front to back (Y); front edge at y = 0
BASE_R = 20.0  # outside corner radius (outside corners can be any radius on an exterior cut)
FEET_Y = 85.0  # foot centres, distance from the front edge
FOOT_MARKS = "guide"  # "guide" (drawn, not cut), "pocket" (recessed), or "none"
FOOT_POCKET_DEPTH = 3.0  # used only when FOOT_MARKS = "pocket"

# Shaper
BIT_D = BITS["1/4in"]
RELIEF_STYLE = "dogbone"
OVERCUT = 0.5

# Post and cradle
POST_W = 24.0  # post cross-section, X
POST_D = 16.0  # post cross-section, Y
TENON_W = 16.0  # tenon into the base slot, X
TENON_D = 10.0  # tenon, Y (must be wider than the bit)
TENON_SCREW_D = 3.0  # pilot hole up the tenon for a wood screw from under the base; 0 for none
PEG = 10.0  # square peg on top of the post into the cradle socket
PEG_LEN = 12.0
CRADLE_H = 20.0  # cradle band height
CRADLE_WALL = 5.0
CRADLE_GAP = 3.0  # space between torso and cradle each side (room for felt or foam tape)
CRADLE_REACH = 0.5  # how far the arms reach forward, as a fraction of TORSO_D
CRADLE_R = 15.0  # inside corner radius of the U
FLUSH_GAP = 0.5  # tenon stops this short of the base underside
FIT_CLEARANCE = 0.3  # total; take the winning value from the projects/02-box coupon

# Cable clips
CLIP_WIDTH = 8.0  # along the cable
CLIP_WALL = 1.6
CLIP_SNAP = 0.75  # clip opening as a fraction of CABLE_D (smaller = tighter snap)
CLIP_SCREW_D = 3.5
CLIP_SCREW_SPACING = 18.0

OUT = Path(__file__).resolve().parent / "out"

# ---------------------------------------------------------------------------
# Derived layout (base top at z = 0, base centred on x = 0, front edge y = 0)
# ---------------------------------------------------------------------------

CRADLE_IN_W = TORSO_W + 2 * CRADLE_GAP
CRADLE_BACK_IN = FEET_Y + TORSO_D / 2 + CRADLE_GAP  # inside face of the cradle's back wall
CRADLE_BACK_OUT = CRADLE_BACK_IN + CRADLE_WALL
POST_Y = CRADLE_BACK_OUT + POST_D / 2  # post sits right behind the cradle
CRADLE_Z0 = CRADLE_Z - CRADLE_H / 2  # bottom of the cradle band
POST_LEN = CRADLE_Z0  # base top to cradle bottom
CLIP_X = POST_W / 2 + 20  # cable runs to the back edge alongside the post
BASE_CLIP_YS = [POST_Y, BASE_D - 15]


def check_params():
    check_bit("tenon slot", min(TENON_W, TENON_D), BIT_D)
    if FOOT_MARKS == "pocket":
        check_bit("foot pocket", min(FOOT_L, FOOT_W), BIT_D)
    if TENON_W > POST_W - 4 or TENON_D > POST_D - 2:
        print("WARNING: tenon leaves no shoulder for the post to sit on")
    if POST_Y + POST_D / 2 > BASE_D - 10:
        print("WARNING: post is too close to the back edge")
    if FEET_Y - FOOT_L / 2 < 10:
        print("WARNING: feet hang off the front of the base")
    if FOOT_SPACING + FOOT_W > BASE_W - 20:
        print("WARNING: feet are too wide for the base")
    if CRADLE_IN_W + 2 * CRADLE_WALL > 140:
        print("WARNING: cradle is too wide for the Creator Pro")
    if CRADLE_Z + CRADLE_H / 2 > DUCK_HEIGHT * 0.75:
        print("WARNING: cradle sits very high; check against the real duck")
    if not THICKNESS_MEASURED:
        print("NOTE: THICKNESS_MEASURED is False; base files use a placeholder thickness.")


# ---------------------------------------------------------------------------
# Plywood base (2D)
# ---------------------------------------------------------------------------


def base_face():
    face = rounded_rect(0, BASE_D / 2, BASE_W, BASE_D, BASE_R)
    slot = relieved_rect(0, POST_Y, TENON_W, TENON_D, BIT_D, RELIEF_STYLE)
    return face.cut(slot).Faces()[0]


def foot_shapes():
    r = min(FOOT_W / 2 - 0.01, 12.0)
    return [rounded_rect(sx * FOOT_SPACING / 2, FEET_Y, FOOT_W, FOOT_L, r) for sx in (-1, 1)]


def clip_screw_marks():
    marks = []
    for y in BASE_CLIP_YS:
        for dx in (-CLIP_SCREW_SPACING / 2, CLIP_SCREW_SPACING / 2):
            marks += cross_mark(CLIP_X + dx, y, 6)
    return marks


# ---------------------------------------------------------------------------
# Printed parts, built in place (in dock coordinates)
# ---------------------------------------------------------------------------


def box_solid(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def post():
    c = FIT_CLEARANCE
    p = box_solid(-POST_W / 2, POST_W / 2, POST_Y - POST_D / 2, POST_Y + POST_D / 2, 0, POST_LEN)
    tw, td = TENON_W - c, TENON_D - c
    p = p.union(box_solid(-tw / 2, tw / 2, POST_Y - td / 2, POST_Y + td / 2, -(BASE_T - FLUSH_GAP), 0))
    pg = PEG - c
    p = p.union(box_solid(-pg / 2, pg / 2, POST_Y - pg / 2, POST_Y + pg / 2, POST_LEN, POST_LEN + PEG_LEN - c))
    if TENON_SCREW_D:
        hole = cq.Workplane("XY").circle(TENON_SCREW_D / 2).extrude(30).translate((0, POST_Y, -BASE_T))
        p = p.cut(hole)
    return p


def cradle():
    reach = TORSO_D * CRADLE_REACH
    outer_w = CRADLE_IN_W + 2 * CRADLE_WALL
    y_front = CRADLE_BACK_IN - reach
    outer = rounded_rect(0, (y_front + CRADLE_BACK_OUT) / 2, outer_w, CRADLE_BACK_OUT - y_front, CRADLE_R + CRADLE_WALL)
    # inner pocket runs out past the front so the U is open there
    inner_len = reach + CRADLE_R + 5
    inner = rounded_rect(0, CRADLE_BACK_IN - inner_len / 2, CRADLE_IN_W, inner_len, CRADLE_R)
    u = outer.cut(inner).Faces()[0]
    band = cq.Workplane("XY").add(cq.Solid.extrudeLinear(u, cq.Vector(0, 0, CRADLE_H)))
    # Socket boss behind the back wall, sitting on the post
    boss = box_solid(-POST_W / 2, POST_W / 2, CRADLE_BACK_OUT - 1, POST_Y + POST_D / 2, 0, CRADLE_H)
    c = band.union(boss)
    socket = box_solid(-PEG / 2, PEG / 2, POST_Y - PEG / 2, POST_Y + PEG / 2, 0, PEG_LEN)
    return c.cut(socket).translate((0, 0, CRADLE_Z0))


def _clip_ring(cx, cy):
    """Snap ring for the cable, opening facing +Y, as a 2D profile (Workplane)."""
    ri = CABLE_D / 2 + 0.2
    ro = ri + CLIP_WALL
    ring = cq.Workplane("XY").center(cx, cy).circle(ro).circle(ri).extrude(CLIP_WIDTH)
    gap = box_solid(cx - CABLE_D * CLIP_SNAP / 2, cx + CABLE_D * CLIP_SNAP / 2, cy, cy + ro + 1, -1, CLIP_WIDTH + 1)
    return ring.cut(gap)


def base_clip():
    """Screw-down clip. Built in print orientation: profile in XY, CLIP_WIDTH tall.
    In use the flat foot (y = 0..3) goes on the base and the cable runs along Z."""
    foot_t = 3.0
    length = CLIP_SCREW_SPACING + CLIP_SCREW_D + 6
    foot = box_solid(-length / 2, length / 2, 0, foot_t, 0, CLIP_WIDTH)
    ro = CABLE_D / 2 + 0.2 + CLIP_WALL
    clip = foot.union(_clip_ring(0, foot_t + ro - 0.8))
    for dx in (-CLIP_SCREW_SPACING / 2, CLIP_SCREW_SPACING / 2):
        clip = clip.cut(cq.Workplane("XZ").circle(CLIP_SCREW_D / 2).extrude(-10).translate((dx, -1, CLIP_WIDTH / 2)))
    return clip


def post_clip():
    """Sleeve that slides down the post (before the cradle goes on), with a
    cable ring on the back. Print orientation: profile in XY."""
    c = FIT_CLEARANCE + 0.2  # a little looser than a press fit so it slides
    iw, idp = POST_W + c, POST_D + c
    w = 2.0
    sleeve = box_solid(-iw / 2 - w, iw / 2 + w, -idp / 2 - w, idp / 2 + w, 0, CLIP_WIDTH)
    sleeve = sleeve.cut(box_solid(-iw / 2, iw / 2, -idp / 2, idp / 2, -1, CLIP_WIDTH + 1))
    ro = CABLE_D / 2 + 0.2 + CLIP_WALL
    return sleeve.union(_clip_ring(0, idp / 2 + w + ro - 0.8))


# ---------------------------------------------------------------------------


def svg_notes():
    status = "measured" if THICKNESS_MEASURED else "PLACEHOLDER - NOT MEASURED, do not cut good stock"
    notes = [
        f"Material: 3/4 in plywood, thickness {BASE_T:.2f} mm ({status}).",
        f"Outline and tenon slot: through, {BASE_T + OVERCUT:.2f} mm deep (thickness + {OVERCUT} mm).",
        "Tenon slot reliefs sized for the bit above; a different bit needs a re-run.",
        "Blue crosses are guide marks for the cable-clip screws: drill by hand, not cut.",
    ]
    if FOOT_MARKS == "guide":
        notes.append("Foot outlines are guide marks only (sizes are GUESSES until the duck arrives).")
    elif FOOT_MARKS == "pocket":
        notes.append(f"Foot pockets: {FOOT_POCKET_DEPTH} mm deep. Sizes are GUESSES; confirm before cutting.")
    notes.append("Top face is the face you see in this file (the foot marks go on top).")
    return notes


def main():
    OUT.mkdir(exist_ok=True)
    print("checks:")
    check_params()

    print("Shaper SVG:")
    svg = ShaperSVG(BIT_D, notes=svg_notes())
    svg.add_part(base_face(), depth=BASE_T + OVERCUT)
    for f in foot_shapes():
        if FOOT_MARKS == "guide":
            svg.add(f, "guide")
        elif FOOT_MARKS == "pocket":
            svg.add(f, "pocket", depth=FOOT_POCKET_DEPTH)
    svg.add_edges(clip_screw_marks(), "guide")
    path = svg.write(OUT / "base_x1.svg", title="Microduck dock base, cut 1")
    print(f"  {path.name}: {BASE_W:.0f} x {BASE_D:.0f} mm, {svg.summary()}")

    print("STLs (in print orientation):")
    # Post lies on its side (long axis along X): no overhangs, strong along its length.
    p = post().translate((0, -POST_Y, 0)).rotate((0, 0, 0), (0, 1, 0), 90)
    export_stl(p, OUT / "post_x1.stl")
    # Cradle prints flat as built; the socket opens onto the bed.
    export_stl(cradle(), OUT / "cradle_x1.stl")
    export_stl(base_clip(), OUT / "clip_base_x2.stl")
    export_stl(post_clip(), OUT / "clip_post_x2.stl")

    print("assembly:")
    base = cq.Workplane("XY").add(cq.Solid.extrudeLinear(base_face(), cq.Vector(0, 0, BASE_T))).translate((0, 0, -BASE_T))
    # Placeholder torso: a rounded block (the real one is rounder still), only
    # to check the cradle leaves the intended gap around it.
    t_face = rounded_rect(0, FEET_Y, TORSO_W, TORSO_D, CRADLE_R)
    torso = cq.Workplane("XY").add(cq.Solid.extrudeLinear(t_face, cq.Vector(0, 0, CRADLE_H + 40))).translate((0, 0, CRADLE_Z0 - 20))
    parts = {"base": base, "post": post(), "cradle": cradle(), "torso (guess)": torso}
    names = list(parts)
    clash = False
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            v = interference(parts[a], parts[b])
            if v > 0.01:
                print(f"  CLASH: {a} and {b} overlap by {v:.2f} mm^3")
                clash = True
    if not clash:
        print("  assembly check: no parts overlap")
    shapes = [parts[k].val() for k in ("base", "post", "cradle")]
    cq.exporters.export(cq.Workplane().add(shapes), str(OUT / "assembly.step"))
    print("  wrote assembly.step (torso placeholder left out)")


if __name__ == "__main__":
    main()
