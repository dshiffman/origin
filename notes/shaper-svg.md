# Shaper Origin SVG conventions

> **Status: colours and depth syntax verified against Shaper's docs (2026-10-15).** Still open: whether the Gen 1's firmware shows encoded depth, and a real test cut (see the checklist at the bottom).

Sources:
- [Cut Type Encoding](https://support.shapertools.com/hc/en-us/articles/115002721473-cut-type-encoding). The colours appear only as images on that page; the hex values below were read from the pixels of Shaper's own swatch images.
- [Manual SVG Cut Depth Encoding](https://support.shapertools.com/hc/en-us/articles/12946815194011-manual-svg-cut-depth-encoding)
- [Encoded Depth](https://support.shapertools.com/hc/en-us/articles/10400926390683-encoded-depth)

`lib/shaper_svg.py` reads its colours from one table (`CUT_STYLES`), which matches the table below.

## How Origin reads an SVG

- **Cut type comes from fill and stroke colour.** Stroke *width* doesn't matter; a hairline and a 0.5 in stroke cut the same.
- **Closed vs open paths:** open paths can only be *on-line* or *guide* (Origin centres the bit on the path). Closed paths can be any type, because Origin needs a closed shape to tell inside from outside.
- **Origin does the bit offset.** The SVG holds the *finished* part shape. You set the bit diameter on the tool, and for exterior/interior cuts it keeps the bit outside/inside the line. So designs never include tool offsets, but they **do** need corner reliefs (see `shaper-bits.md`), because a round bit can't cut a sharp inside corner.

## Cut types (verified)

| Cut type | Fill | Stroke | Meaning (Shaper's wording) |
|---|---|---|---|
| Exterior | black `#000000` | black `#000000` | Cut out a positive shape at the specified dimensions |
| Interior | white `#FFFFFF` | black `#000000` | Cut a through-hole equal to the SVG shape |
| On-line | none | grey `#7F7F7F` | Engraving; bit centred on the path |
| Pocket | grey `#7F7F7F` | none | Remove material inside the shape to a depth set on-tool |
| Guide | blue `#0068FF` fill **or** stroke | | Helpful marks you don't plan to cut |

## Units and size

- Our files set `width`/`height` in `mm` with a matching `viewBox`, so 1 user unit = 1 mm and Origin imports at true size.
- After importing, check a known dimension on Origin's screen before cutting.

## Depth encoding

Syntax (from the "Manual SVG Cut Depth Encoding" article): declare the namespace on the root element and add `shaper:cutDepth` to a shape, with an `mm` or `in` suffix.

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:shaper="http://www.shapertools.com/namespaces/shaper" ...>
  <rect shaper:cutDepth="6.35mm" width="25.4mm" height="25.4mm"/>
</svg>
```

**What it does on the tool** (from the "Encoded Depth" article), which isn't what you might expect:

- Encoded depth is a **label and a safety check, not an automatic setting.** The tool's cut depth and each path's encoded depth are separate. **You still set the cut depth yourself** (the depth panel has a "transfer" button that copies a path's encoded depth to the tool's cut depth).
- When the tool depth equals the path's encoded depth, Origin shows a green check. If the tool depth is *deeper*, it warns you, and pops up a confirmation when you press cut.
- Deep cuts still need several passes; work down to the encoded depth.
- Paths without a depth show "unset".
- The feature came in the "Jenner" system update. **Not yet confirmed for the Gen 1:** Shaper's release-notes page (www.shapertools.com) is still blocked from the cloud session. If the Gen 1 doesn't support it, the attribute is ignored and nothing else changes.

## What our scripts write

- One SVG per part (or per identical set, with the count in the filename, e.g. `wall_long_x2.svg`).
- Each file has a `<desc>` block (shown in any text editor) stating the bit, material thickness, cut types used and depths.
- Through-cuts get `shaper:cutDepth` = material thickness + a small overcut into the spoilboard. Both are script parameters. On the tool it acts as the target and the over-depth guard described above.
- Holes too small for the bit are written as **guide** cross-marks (drill by hand), never as interior cuts.

## Still to check

- [x] Compare every colour against Shaper's "Cut Type Encoding" article. Matches `CUT_STYLES`.
- [x] Depth attribute syntax and what Origin does with it.
- [ ] Does the Gen 1 show encoded depth? Check for the depth label above the reticle when a path is selected, or check the firmware version against Shaper's release notes.
- [ ] Import `projects/02-box/out/coupon_wood.svg` on Origin: outline shows as exterior, slot as interior, and the size is right.
- [ ] Cut the coupon in scrap and measure the slot and notch with calipers.
