# 3D printers

Specs below are the usual published figures for these models; confirm against the actual machines (and record nozzle size if either has been changed).

| | FlashForge Creator Pro (2014) | Monoprice Mini Delta |
|---|---|---|
| Build volume | ~225 × 145 × 150 mm | ~110 mm diameter × 120 mm tall (round bed) |
| Extruders | Dual | Single |
| Nozzle | 0.4 mm | 0.4 mm |
| Filament | 1.75 mm | 1.75 mm |
| Heated bed | Yes | Yes |
| File format | `.x3g` (Sailfish firmware); slice to G-code, then convert with GPX, or use FlashPrint | Plain G-code |
| Best for | Larger parts, ABS (partly enclosed), two-colour or soluble-support prints | Small, quick parts in PLA |

## What this means for designs

- **Default max part size: ~140 × 140 × 140 mm** to fit the Creator Pro comfortably; anything that must also fit the Mini Delta has to sit inside a ~100 mm circle.
- Bigger parts get split into pieces that join with pins, dovetails or screws.
- Older printers are less precise. Start with **0.3 mm clearance** for parts that slide together or fit into wood slots, then tune after a test print.
- Print a small fit-test coupon (a tab and slot at a few clearances) before the real part; it takes minutes and saves failed prints.

## Still to record
- Slicer actually in use for each printer
- Filaments on hand (PLA, ABS, PETG?)
- Any upgrades (nozzles, firmware, bed surface)
