# Project 3: Microduck dock

A parking and charging stand for the Microduck. A plywood base (Shaper) carries a printed post with a U-shaped cradle at torso height. The duck stands on marked foot spots and leans back into the cradle, so it doesn't fall over when powered down. Clips route the USB-C cable down the post and off the back of the base.

```
python3 dock.py
  out/base_x1.svg        plywood base               (cut 1, 3/4 in ply)
  out/post_x1.stl        post with tenon and peg    (print 1)
  out/cradle_x1.stl      U-shaped cradle            (print 1)
  out/clip_base_x2.stl   screw-down cable clip      (print 2)
  out/clip_post_x2.stl   slide-on cable clip        (print 2)
  out/assembly.step      base + post + cradle in 3D
```

## What's known and what's guessed

Published figures (Pollen Robotics / Hugging Face launch, Aug 2026): **~25 cm tall, ~14 cm wide, under 800 g**, ships with a battery and a USB-C cable. I found **no** published foot size, torso size, charging-port location or dock. Those are parameters marked `GUESS` at the top of `dock.py`:

| Parameter | Guess | Measure when it arrives |
|---|---|---|
| `TORSO_W`, `TORSO_D` | 100, 80 mm | Torso width and depth at cradle height |
| `CRADLE_Z` | 120 mm | Height for the cradle: just below the widest part of the body, with the duck in its parked pose |
| `FOOT_L`, `FOOT_W` | 60, 40 mm | Foot outline |
| `FOOT_SPACING` | 70 mm | Foot centre to centre when parked |
| `CABLE_D` | 4 mm | The supplied USB-C cable's diameter |

The base outline, post joint and clips barely depend on these. The cradle and foot marks do. That's why the foot outlines are **guide lines by default** (shown on Origin's screen, not cut). Once you've measured real feet, set `FOOT_MARKS = "pocket"` to rout 3 mm recesses instead.

Worth checking in the `duck` repo / Pollen docs before Christmas: where the charging port is, and whether the duck should be powered off, sitting, or standing while charging. A different parked pose changes `CRADLE_Z` a lot.

## Design choices

- **Plywood base, printed everything else.** The base needs weight and area so a 25 cm robot can't tip it, and wood does that cheaply: 200 × 220 mm of 3/4 in ply is about half a kilo. The parts with fussy shapes (cradle, clips) are printed.
- **Cradle behind, not underneath.** A biped's legs leave no room for a post underneath, and we don't know its shape yet. A U wrapped around the back and sides stops it falling backwards or sideways and works for a range of body shapes. There's a 3 mm gap each side for felt or foam tape.
- **Mortise and tenon into the base**, the same idea as the box brackets. The post's tenon fits a through-slot with dog-bone reliefs (interior cut, 1/4 in bit). The tenon stops 0.5 mm short of the underside, and a wood screw from below goes up the pilot hole in the tenon. No visible fastener.
- **Peg and socket between post and cradle.** It's two parts because neither fits the printer in a good orientation as one. The post prints lying on its side (strongest along its length, no overhangs), and the cradle prints flat. You can swap in a taller or wider cradle later without reprinting the post.
- **Clips print flat.** Both clip types are an extruded 2D profile, so neither needs support. The post clips slide down the post before the cradle goes on; the base clips screw down.
- **Small holes become guide marks.** Clip screw holes (3.5 mm) are smaller than the 1/4 in bit, so the SVG shows them as blue crosses to drill by hand rather than impossible interior cuts.
- **Assembly check.** The script builds base + post + cradle + a placeholder torso and checks for overlap, so the cradle's gap around the (guessed) torso is real.
- **Walking onto the dock** (Phase 2 in the `duck` repo) would need a ramp or a thin base: 18 mm is a big step for a 25 cm robot. Not in this version.

## Check before cutting / printing

- [ ] **Shaper SVG conventions:** colours checked against Shaper's docs (`notes/shaper-svg.md`). Confirm on the tool with the box coupon first.
- [ ] **Measure the 3/4 in sheet,** set `BASE_T` and `THICKNESS_MEASURED = True`, re-run.
- [ ] **Bit:** 1/4 in in Origin and in `BIT_D`. Cut types: outline exterior, tenon slot interior, foot outlines and crosses guide only. Depth target = thickness + 0.5 mm, encoded in the file; set the tool depth yourself and take several passes.
- [ ] **Size check** on Origin's screen: the base is 200 × 220 mm.
- [ ] **Fit clearance:** use the winning value from the `projects/02-box` coupon for `FIT_CLEARANCE` (same printer, same kind of joint).
- [ ] **GUESS parameters:** fine to cut the base and print the post and clips now. Hold off on the cradle (and foot pockets) until the duck is here and measured. Cradle reprints are cheap.
- [ ] Look over `out/assembly.step` in a viewer to see the layout.
