# Project 1: ShaperTape spacing jig

A printed bar for laying ShaperTape in straight, evenly spaced, parallel strips. Print only, no wood cutting.

```
python3 jig.py      →  out/jig.stl, out/fit_coupon.stl
```

## How to use it

1. Lay the first strip of tape.
2. Set the jig across it with one groove over the tape (grooves face down). The tape sits in the groove, so the jig is square to it.
3. Feed the next strip along the other groove and press it down as you go. Slide the jig along, or use two jigs, one near each end of the strip.
4. Repeat from the strip you just laid.

The V-notches on the sides of the bar mark each groove's centre line, so you can also line the jig up with a pencil line.

## Design choices

- **Why a tape jig?** Origin works out where it is by looking at the tape, and Shaper's guidance is to keep strips no more than 3 in apart with at least three in view at all times. To be honest about how much it matters: Shaper also says the strips *don't* need to be exactly parallel. So the jig is a convenience that keeps gaps under the limit quickly and evenly, not a precision requirement. It's still a good first print because it doesn't depend on any wood dimensions.
- **Grooves on the underside.** The groove walls hold the tape's edges, which is what sets the strips parallel. The grooves only need to be deeper than the tape is thick (1 mm is plenty), so the bar still sits flat on the table.
- **Clearance is total, not per side.** `GROOVE_CLEARANCE = 0.4` makes each groove 0.4 mm wider than the tape (0.2 mm each side). Too tight and the tape wrinkles going in; too loose and the spacing wanders. The coupon tells you which is right on your printer.
- **Lead-in chamfers** on the groove edges stop the tape catching as you feed it.
- **Printed upside down** (the STL is already oriented this way). The flat top goes on the bed. The groove walls then print as clean vertical walls with no bridging, and the first-layer squish ("elephant's foot") lands on the top face, which never touches the tape.
- **Sharp bottom, rounded top.** Only the top and end edges are filleted, so the groove walls run right down to the table.
- **Size:** ~117 × 30 × 6 mm, which fits the Creator Pro. It's too long for the Mini Delta's ~100 mm circle; drop `TAPE_SPACING` or use the Creator Pro.
- **One script, parameters at the top.** Change `TAPE_SPACING` or `N_GROOVES` (3 lays two strips at once) and re-run.

## Fit-test coupon (print this first)

`fit_coupon.stl` is a short bar with four grooves at 0.2 / 0.4 / 0.6 / 0.8 mm clearance, numbered 1–4 on the groove face. It is a quick print. Run a strip of tape through each groove. Pick the one where the tape slides in without curling but can't shift sideways, and set `GROOVE_CLEARANCE` to that value.

## Check before printing

- [ ] **Measure the tape width** with calipers and set `TAPE_WIDTH` (sold as 1/2 in = 12.7 mm).
- [x] **Spacing checked against Shaper's guidance.** Strips should be no more than 3 in (76 mm) apart, with rows 2–3 in apart. `TAPE_SPACING = 80` mm centre to centre leaves a ~67 mm (2.6 in) gap. Shaper also says to keep strips under 3 ft long and never overlap them.
- [ ] Print and test the coupon, then set `GROOVE_CLEARANCE`.
- [ ] Look over `out/jig.stl` in the slicer: grooves facing up, flat face on the bed.
- [ ] Material: PLA is fine. Nylon or PETG if you want it to survive being dropped a lot.

## Possible next steps

- An end hook that catches the table edge, to set the first strip's distance from the edge.
- A version with a pencil slot, to mark tape lines before peeling the backing.
