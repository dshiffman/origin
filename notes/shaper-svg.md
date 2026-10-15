# Shaper Origin SVG conventions

> **Status: UNVERIFIED DRAFT.** Written from Shaper's support articles as seen through search results ("Cut Type Encoding", "Manual SVG Cut Depth Encoding"), plus general knowledge. The cloud session couldn't open the pages directly, so the exact hex values below have **not** been checked against Shaper's current docs. Before the first real cut, do the verification list at the bottom and update this file. `lib/shaper_svg.py` reads its colours from one table (`CUT_STYLES`), so a fix there updates every project.

## How Origin reads an SVG

- **Cut type comes from fill and stroke colour.** Stroke *width* doesn't matter; a hairline and a thick line cut the same.
- **Closed vs open paths:** open paths can only be *on-line* or *guide*. Closed paths can be any type, because Origin needs a closed shape to tell inside from outside.
- **Origin does the bit offset.** The SVG holds the *finished* part shape. You set the bit diameter on the tool, and for exterior/interior cuts it keeps the bit outside/inside the line. So designs never include tool offsets, but they **do** need corner reliefs (see `shaper-bits.md`), because a round bit can't cut a sharp inside corner.
- **Depth:** set on the tool by default. Newer firmware can read a per-shape depth from the file (below).

## Cut types (colours to verify)

| Cut type | Fill | Stroke | Meaning |
|---|---|---|---|
| Exterior | black `#000000` | black `#000000` | Cut out a part: bit runs **outside** the line |
| Interior | white `#FFFFFF` | black `#000000` | Cut a hole: bit runs **inside** the line |
| On-line | none | grey `#7F7F7F` | Bit centred on the line (engraving, scribe marks) |
| Pocket | grey `#7F7F7F` | none | Clear all material inside to a depth |
| Guide | none | blue `#0068FF` | Shown on screen, never cut |

## Units and size

- Files set `width`/`height` in `mm` with a matching `viewBox`, so 1 user unit = 1 mm and Origin imports at true size.
- After importing, check a known dimension on Origin's screen before cutting.

## Depth encoding (newer firmware)

Shaper's "Manual SVG Cut Depth Encoding" article: declare the namespace on the root element and add a depth to each shape.

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:shaper="http://www.shapertools.com/namespaces/shaper" ...>
  <rect shaper:cutDepth="6.35mm" width="1in" height="1in" .../>
</svg>
```

- Units by suffix: `mm` or `in`.
- It needs the firmware release that added it (named "Jenner" in the article). **Confirm the Gen 1 is on firmware that supports this.** If it isn't, Origin ignores the attribute and depth is set on the tool as usual.
- Community tools also mention `shaper:cutOffset` and `shaper:toolDia`. Our scripts don't use them.

## What our scripts write

- One SVG per part (or per identical set, with the count in the filename, e.g. `wall_long_x2.svg`).
- Each file has a `<desc>` block (shown in any text editor) stating the bit, material thickness, cut types used and depths.
- Through-cuts get `shaper:cutDepth` = material thickness + a small overcut into the spoilboard, both script parameters.
- Holes too small for the bit are written as **guide** cross-marks (drill by hand), never as interior cuts.

## Verification checklist (do once, then delete the status banner)

- [ ] Open Shaper's "Cut Type Encoding" article and compare every hex value in the table above. Fix `CUT_STYLES` in `lib/shaper_svg.py` if any differ.
- [ ] Check whether the Gen 1 firmware supports `shaper:cutDepth`.
- [ ] Import `projects/02-box/out/coupon_wood.svg` on Origin. Check it shows the right cut types (outline exterior, slot interior) and the right size.
- [ ] Cut the coupon in scrap and measure the slot and notch with calipers.
