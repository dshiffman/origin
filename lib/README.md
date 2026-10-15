# lib

Shared helpers. Project scripts add the repo root to `sys.path`, then `from lib.shaper_svg import ...`.

- `shaper_svg.py`: turn CadQuery 2D faces into Shaper Origin SVGs.
  - `ShaperSVG.add_part(face, depth)`: outline becomes an exterior cut, holes become interior cuts.
  - `add(face, "pocket" | "interior" | "online" | "guide", depth)` and `add_edges(edges, "guide")` for anything else.
  - Corner reliefs: `relieved_rect(..., bit_d, style="dogbone" | "tbone-x" | "tbone-y", corners=...)`.
  - Also `rect`, `rounded_rect`, `cross_mark` (drill marks), and `check_bit` (warns when a feature is narrower than the bit).
  - Output is in mm. Each file's `<desc>` states the bit and cut types. Colours come from `CUT_STYLES`, which follows `notes/shaper-svg.md` (checked against Shaper's docs).
- `printing.py`: `export_stl` (drops the part onto the bed and reports which printer it fits), `check_print_size`, and `interference` (overlap volume between two parts, for assembly checks).
