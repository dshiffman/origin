"""Write Shaper Origin SVGs from CadQuery 2D geometry.

The idea: draw each wood part as a CadQuery Face (outline plus holes) at its
finished size, then hand it to ShaperSVG. The outline becomes an exterior cut,
each hole becomes an interior cut. Other shapes (pockets, engraving, guide
marks) can be added on their own.

Cut-type colours live in CUT_STYLES. They follow notes/shaper-svg.md, checked
against Shaper's "Cut Type Encoding" article (2026-10-15).

Also here: corner-relief helpers (dog-bone / T-bone) and a bit-size check.
"""

import math
from pathlib import Path
from xml.sax.saxutils import escape

import cadquery as cq

SHAPER_NS = "http://www.shapertools.com/namespaces/shaper"

# fill, stroke. See notes/shaper-svg.md (verified against Shaper's docs).
CUT_STYLES = {
    "exterior": ("#000000", "#000000"),
    "interior": ("#FFFFFF", "#000000"),
    "online": ("none", "#7F7F7F"),
    "pocket": ("#7F7F7F", "none"),
    "guide": ("none", "#0068FF"),
}

INCH = 25.4
BITS = {"1/8in": INCH / 8, "1/4in": INCH / 4}


# ---------------------------------------------------------------------------
# Corner reliefs and 2D shapes
# ---------------------------------------------------------------------------


def _face_from_sketch(sk):
    faces = sk.clean()._faces.Faces()
    if len(faces) != 1:
        raise ValueError(f"expected one face, got {len(faces)}")
    return faces[0]


def rect(cx, cy, w, h):
    """Plain rectangle as a Face, centred at (cx, cy)."""
    return _face_from_sketch(cq.Sketch().push([(cx, cy)]).rect(w, h))


def rounded_rect(cx, cy, w, h, r):
    """Rectangle with rounded corners. Use r >= bit radius for pockets."""
    sk = cq.Sketch().push([(cx, cy)]).rect(w, h).reset().vertices().fillet(r)
    return _face_from_sketch(sk)


def relieved_rect(cx, cy, w, h, bit_d, style="dogbone", corners="all"):
    """Rectangle with bit-sized corner reliefs, for a slot or notch that a
    square-cornered tab must fit into.

    A round bit of radius r leaves a radius-r fillet in every inside corner,
    which stops a square tab from seating. Adding a circle of radius r that
    passes through the corner lets the bit reach it.

    style:
      "dogbone": relief on the corner's diagonal. Symmetric, removes the least
                 material, but nibbles both walls.
      "tbone-x": relief pushed along X, so the walls running along Y stay
                 straight (better for a tab that must bear on the Y walls).
      "tbone-y": the same, pushed along Y.
    corners: "all", or a subset of {"+x+y", "-x+y", "-x-y", "+x-y"}.
    """
    r = bit_d / 2
    pts = []
    for sx in (1, -1):
        for sy in (1, -1):
            key = f"{'+' if sx > 0 else '-'}x{'+' if sy > 0 else '-'}y"
            if corners != "all" and key not in corners:
                continue
            x, y = cx + sx * w / 2, cy + sy * h / 2
            if style == "dogbone":
                d = r / math.sqrt(2)
                pts.append((x - sx * d, y - sy * d))
            elif style == "tbone-x":
                pts.append((x - sx * r, y))
            elif style == "tbone-y":
                pts.append((x, y - sy * r))
            else:
                raise ValueError(style)
    sk = cq.Sketch().push([(cx, cy)]).rect(w, h).reset()
    if pts:
        sk = sk.push(pts).circle(r, mode="a").reset()
    return _face_from_sketch(sk)


def cross_mark(x, y, size=6.0):
    """Two open line segments, e.g. a guide mark for a hole to drill by hand."""
    h = size / 2
    return [
        cq.Edge.makeLine(cq.Vector(x - h, y, 0), cq.Vector(x + h, y, 0)),
        cq.Edge.makeLine(cq.Vector(x, y - h, 0), cq.Vector(x, y + h, 0)),
    ]


def check_bit(name, min_width, bit_d):
    """Warn if a feature is narrower than the bit can cut. Returns True if OK."""
    if min_width < bit_d:
        print(
            f"WARNING: {name} is {min_width:.2f} mm wide but the bit is "
            f"{bit_d:.2f} mm; it can't be cut. Use a smaller bit or widen it."
        )
        return False
    return True


# ---------------------------------------------------------------------------
# Geometry -> SVG path data
# ---------------------------------------------------------------------------


def _ordered_edges(wire, tol=1e-4):
    """Edges of a wire chained end to start, each as (edge, reversed?).

    Chaining by matching end points is simpler and more robust than trusting
    each edge's stored orientation.
    """
    edges = list(wire.Edges())
    first = edges.pop(0)
    out = [(first, False)]
    cur = first.endPoint()
    while edges:
        for i, e in enumerate(edges):
            if (e.startPoint() - cur).Length < tol:
                out.append((e, False))
                cur = e.endPoint()
                break
            if (e.endPoint() - cur).Length < tol:
                out.append((e, True))
                cur = e.startPoint()
                break
        else:
            raise ValueError("wire edges don't connect")
        edges.pop(i)
    return out


def _edge_points(edge, rev):
    a, b = edge.startPoint(), edge.endPoint()
    return (b, a) if rev else (a, b)


def _fmt(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class _Flip:
    """Map CadQuery coordinates (Y up) to SVG (Y down) inside a bounding box."""

    def __init__(self, xmin, ymax):
        self.xmin, self.ymax = xmin, ymax

    def __call__(self, v):
        return (v.x - self.xmin, self.ymax - v.y)


def _arc_cmd(edge, start, end, flip, rev):
    r = edge.radius()
    mid = edge.positionAt(0.5)
    sx, sy = flip(start)
    mx, my = flip(mid)
    ex, ey = flip(end)
    # Turn direction start->mid->end in SVG coords decides the sweep flag.
    cross = (mx - sx) * (ey - my) - (my - sy) * (ex - mx)
    sweep = 1 if cross > 0 else 0
    large = 1 if edge.Length() > math.pi * r + 1e-9 else 0
    return f"A {_fmt(r)} {_fmt(r)} 0 {large} {sweep} {_fmt(ex)} {_fmt(ey)}"


def _edge_cmds(edge, rev, flip):
    start, end = _edge_points(edge, rev)
    kind = edge.geomType()
    if kind == "LINE":
        x, y = flip(end)
        return [f"L {_fmt(x)} {_fmt(y)}"]
    if kind == "CIRCLE":
        if (start - end).Length < 1e-6:  # full circle: two half arcs
            half = edge.positionAt(0.5)
            r = edge.radius()
            hx, hy = flip(half)
            ex, ey = flip(end)
            return [
                f"A {_fmt(r)} {_fmt(r)} 0 0 1 {_fmt(hx)} {_fmt(hy)}",
                f"A {_fmt(r)} {_fmt(r)} 0 0 1 {_fmt(ex)} {_fmt(ey)}",
            ]
        return [_arc_cmd(edge, start, end, flip, rev)]
    # Anything else (splines, ellipses): straight segments at fine spacing.
    n = max(8, int(edge.Length() / 0.2))
    ts = [i / n for i in range(1, n + 1)]
    if rev:
        ts = [1 - t for t in ts]
    return [f"L {_fmt(flip(edge.positionAt(t))[0])} {_fmt(flip(edge.positionAt(t))[1])}" for t in ts]


def wire_to_path(wire, flip):
    edges = _ordered_edges(wire)
    start, _ = _edge_points(*edges[0])
    x, y = flip(start)
    cmds = [f"M {_fmt(x)} {_fmt(y)}"]
    for e, rev in edges:
        cmds += _edge_cmds(e, rev, flip)
    if wire.IsClosed():
        cmds.append("Z")
    return " ".join(cmds)


def edges_to_path(edges, flip):
    """Open edges (each drawn as its own subpath)."""
    cmds = []
    for e in edges:
        x, y = flip(e.startPoint())
        cmds.append(f"M {_fmt(x)} {_fmt(y)}")
        cmds += _edge_cmds(e, False, flip)
    return " ".join(cmds)


# ---------------------------------------------------------------------------
# The document
# ---------------------------------------------------------------------------


class ShaperSVG:
    """Collect shapes with cut types and write one SVG.

    svg = ShaperSVG(bit_d=6.35, notes=["1/2 in plywood, measured 11.9 mm"])
    svg.add_part(panel_face, depth=12.4)       # outline exterior, holes interior
    svg.add(pocket_face, "pocket", depth=3)
    svg.add_edges(cross_mark(10, 10), "guide")
    svg.write("out/panel.svg", title="Box side")
    """

    def __init__(self, bit_d, notes=(), margin=0.0):
        self.bit_d = bit_d
        self.notes = list(notes)
        self.margin = margin
        self.items = []  # (kind, geometry, cut, depth)

    def add_part(self, face, depth=None):
        """A part: outer wire = exterior cut, inner wires (holes) = interior cuts."""
        self.items.append(("wire", face.outerWire(), "exterior", depth))
        for w in face.innerWires():
            self.items.append(("wire", w, "interior", depth))

    def add(self, face_or_wire, cut, depth=None):
        """A closed shape with an explicit cut type (pocket, interior, online, guide...)."""
        w = face_or_wire.outerWire() if isinstance(face_or_wire, cq.Face) else face_or_wire
        self.items.append(("wire", w, cut, depth))

    def add_edges(self, edges, cut="guide"):
        """Open lines: only "online" or "guide" make sense for these."""
        if cut not in ("online", "guide"):
            raise ValueError("open paths can only be online or guide cuts")
        self.items.append(("edges", edges, cut, None))

    def _bbox(self):
        shapes = []
        for kind, g, _, _ in self.items:
            shapes += g if kind == "edges" else [g]
        bb = cq.Compound.makeCompound(shapes).BoundingBox()
        m = self.margin
        return bb.xmin - m, bb.ymin - m, bb.xmax + m, bb.ymax + m

    def summary(self):
        counts = {}
        for _, _, cut, depth in self.items:
            key = cut if depth is None else f"{cut} @ {depth:.2f} mm deep"
            counts[key] = counts.get(key, 0) + 1
        return counts

    def write(self, path, title=""):
        xmin, ymin, xmax, ymax = self._bbox()
        w, h = xmax - xmin, ymax - ymin
        flip = _Flip(xmin, ymax)
        desc = [
            f"Bit: {self.bit_d:.3f} mm ({self.bit_d / INCH:.3f} in) - set this on Origin.",
            "Cut types: " + ", ".join(f"{k} x{v}" for k, v in self.summary().items()) + ".",
            "Geometry is the finished part size; Origin applies the bit offset.",
            "Colours per notes/shaper-svg.md (Shaper cut type encoding).",
            "shaper:cutDepth is a target and over-depth check; set the cut depth on Origin yourself.",
            *self.notes,
        ]
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:shaper="{SHAPER_NS}" '
            f'width="{_fmt(w)}mm" height="{_fmt(h)}mm" viewBox="0 0 {_fmt(w)} {_fmt(h)}">',
            f"  <title>{escape(title)}</title>",
            "  <desc>",
            *[f"    {escape(d)}" for d in desc],
            "  </desc>",
        ]
        # Draw order: exterior, interior, pocket, then marks on top.
        order = ["exterior", "pocket", "interior", "online", "guide"]
        for cut in order:
            for kind, g, c, depth in self.items:
                if c != cut:
                    continue
                fill, stroke = CUT_STYLES[cut]
                d = wire_to_path(g, flip) if kind == "wire" else edges_to_path(g, flip)
                depth_attr = f' shaper:cutDepth="{_fmt(depth)}mm"' if depth is not None else ""
                lines.append(
                    f'  <path d="{d}" fill="{fill}" stroke="{stroke}" '
                    f'stroke-width="0.2" fill-rule="evenodd"{depth_attr}/>'
                )
        lines.append("</svg>")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n")
        return path
