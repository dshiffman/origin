# Shaper Origin bits

Bits on hand: **scribe / engraving**, **1/8 in (3.175 mm)**, **1/4 in (6.35 mm)**.

| Bit | Use in designs |
|---|---|
| Scribe | Layout lines, labels, guide marks (guide-type paths, no real depth) |
| 1/8 in | Fine detail, small slots, thin hardboard, tight inside corners |
| 1/4 in | Default for plywood cuts, faster and stronger; pockets and outlines |

## Design rules that follow

- Inside corners can't be sharper than the bit radius: 1.6 mm with the 1/8 in bit, 3.2 mm with the 1/4 in bit. Slots that take a square-cornered tab get **dog-bone or T-bone reliefs** in the corners.
- Every generated SVG states which bit it assumes. The bit diameter is a script parameter.
- Slots narrower than the bit can't be cut; scripts should warn rather than silently produce one.
