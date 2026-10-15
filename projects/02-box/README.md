# Project 2: plywood box with printed corner brackets

An open-top box: five plywood panels cut on the Shaper, held square by four identical printed corner brackets. One script, one set of parameters, including the **measured** plywood thickness.

```
python3 box.py
  out/wall_long_x2.svg    front + back walls   (cut 2)
  out/wall_short_x2.svg   side walls           (cut 2)
  out/bottom_x1.svg       bottom               (cut 1)
  out/coupon_wood.svg     fit-test coupon      (cut 1, from the wall sheet)
  out/bracket_x4.stl      corner bracket       (print 4)
  out/coupon_print.stl    fit-test coupon      (print 1)
  out/assembly.step       whole box in 3D, for looking over
```

Default size: 200 × 150 × 100 mm outside, 1/2 in plywood, 1/4 in bit.

## How it goes together

```
      wall (on top of the bottom panel)
     ┌──────────────┐
     │   ┌──┐       │  ← notch in the wall's bottom edge
     │   │▓▓│ rib   │    the bracket's rib fills it
─────┴───┴──┴───────┴───── bottom panel
          ▓ tab → slot in the bottom panel
```

- The walls sit **on** the bottom panel. The long walls run the full length, and the short walls fit between them (so they're 2 × thickness shorter).
- Each bracket is an L with a solid corner post. Each leg has a **vertical rib** that drops into a notch in that wall's bottom edge, and the post has a **square tab** underneath that drops into a slot in the bottom panel. Together they lock the corner square in all three directions.
- Glue it (wood glue doesn't stick well to PLA; use CA or epoxy for the plastic-to-wood faces), or drive small screws through the two holes in each leg.
- From outside you see the rib ends in each notch: a small coloured rectangle near every corner. Print in a contrasting colour if you like the look.

## Design choices

- **Thickness drives everything.** `T_WALL` sets the short-wall length, the rib depth, and the cut depth. `T_BOTTOM` sets the tab length. Plywood is rarely its nominal size (see `notes/materials.md`), and that's why the script has a `THICKNESS_MEASURED` flag: until you set it, every SVG says *PLACEHOLDER - NOT MEASURED* in its description.
- **Bit-sized corner reliefs.** A round bit leaves a radius in every inside corner, so a square rib won't seat. Each inside corner gets a **dog-bone**, a bit-radius circle that passes through the corner, so the bit can reach it. You can switch to T-bones with `RELIEF_STYLE`. Notches only get reliefs at their two inner corners; their corners at the panel edge are outside corners and come out sharp anyway.
- **Bit stated in every file.** All SVGs assume the 1/4 in bit (`BIT_D`). It's written into each file's `<desc>`, and the reliefs are sized to it. The script warns if a slot is narrower than the bit.
- **Cut types.** Panel outlines are **exterior** cuts; the bottom slots are **interior** cuts. Notches are part of the outline, so they're cut as part of the exterior pass. Depth is encoded as thickness + 0.5 mm overcut.
- **Clearance goes on the printed side.** Wood is cut at the nominal size and the printed ribs/tabs are made `FIT_CLEARANCE` smaller (total, half each side). Re-printing a bracket is cheaper than re-cutting a panel, so the plastic is the part you tune.
- **Ribs stop 0.5 mm short** (`FLUSH_GAP`) of the outside face. A rib that sticks out can't be sanded flush without chewing the wood around it; one slightly recessed looks fine.
- **Brackets print upside down** (flat top on the bed). The ribs are vertical, the tab points up, and the screw holes are horizontal, so nothing needs support.
- **Built-in assembly check.** The script builds the box in 3D from the same 2D panels and checks every pair of parts for overlap. "No parts overlap" means the notches, slots, ribs and tabs line up. Tested: oversizing the ribs makes it report clashes.

## Fit-test coupons (do these first)

1. Cut `coupon_wood.svg` from **the same sheet** as the walls. It has one notch and one slot exactly like the box's.
2. Print `coupon_print.stl`: rib-sized tabs (front row) and bottom-tab-sized tabs (back row) at 0.1 / 0.3 / 0.5 / 0.7 mm total clearance, numbered 1–4.
3. Try each tab in the notch and slot. Pick the snuggest one that goes in by hand, then set `FIT_CLEARANCE` and re-run.
4. Also measure the cut notch and slot with calipers. If they're off from the design size, Origin's bit diameter setting or the bit itself is off. Fix that before cutting panels.

## Check before cutting

- [ ] **Shaper SVG conventions:** colours now checked against Shaper's docs (`notes/shaper-svg.md`). The first import of the coupon still confirms them on the tool.
- [ ] **Thickness measured.** Caliper the sheet in several places, set `T_WALL` / `T_BOTTOM`, set `THICKNESS_MEASURED = True`, re-run.
- [ ] **Bit:** a 1/4 in (6.35 mm) bit is in Origin and Origin's bit setting matches. A different bit means changing `BIT_D` and re-running, because the reliefs depend on it.
- [ ] **Cut types on import:** the panel outline shows as exterior and the bottom slots as interior.
- [ ] **Depth:** target = thickness + 0.5 mm, encoded in the file. Origin doesn't apply it automatically: set the tool depth yourself (or use the transfer button) and work down in several passes. Origin warns if you go deeper than the encoded depth, if the Gen 1 firmware supports encoded depth.
- [ ] **Size check:** after import, measure one panel's length on Origin's screen against the file (`wall_long_x2.svg` is 200 mm long by default).
- [ ] **Fit coupons done** and `FIT_CLEARANCE` set from them.
- [ ] **Grain direction:** run the walls' face grain along their length.
- [ ] Spoilboard under the work and the workpiece held down: through-cuts free the part at the end.
