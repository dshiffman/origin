# origin

AI-assisted making with **3D printers** and a **Shaper Origin (Gen 1)** handheld CNC router.

Goal: education and tinkering, building toward projects that combine 3D printing and woodworking. Companion repo: [`duck`](https://github.com/dshiffman/duck) (Microduck robot).

## Core workflow

One parametric model in **code-based CAD** (CadQuery, Python) produces both:

- **STL** for the 3D printers
- **SVG** for the Shaper Origin

Because both come from the same parameters, change one value (e.g. plywood thickness) and the wood cuts and printed parts update together and still fit.

```
describe the part → Claude writes CadQuery → STL (print) + SVG (cut) → check → make → measure → adjust parameters
```

## Conventions

- Units: millimetres everywhere; parameters at the top of each script
- Every project folder has a `params.py` (or parameters block), the script, and an `out/` folder for generated files
- Generated files are reviewed in a viewer before printing or cutting — never cut straight from an unchecked file
- Shaper SVGs: cut type is set by fill/stroke (exterior, interior, pocket, guide) and depth can be embedded. **Verify the exact conventions against Shaper's current docs before the first real cut** and record them in `notes/shaper-svg.md`
- Real material thickness varies: measure the actual sheet and set the parameter from that, not the nominal size

## Project ideas (rising difficulty)

1. [ ] **Printed Shaper jig**: spacing jig or corner-alignment block (print only, made for woodworking)
2. [ ] **Plywood box with printed corner brackets or hinges**: Shaper cuts panels, printers make the joinery, one script
3. [ ] **Microduck dock / stand**: plywood base cut on the Shaper, printed cradle and cable clips (ready before the duck arrives)
4. [ ] Later: a printed open-source robot arm (purchase decision, compare options and cost first)

## Layout

```
notes/      shaper-svg.md, printer settings, material notes
lib/        shared helpers (SVG export with Shaper cut types, common joints)
projects/   one folder per project
```

## Materials on hand

Plywood (3/4, 1/2, 1/4 in nominal), hardboard (1/8, 1/4 in), particle board (1/2 in nominal). Typical real thicknesses and a place to record measured ones: [`notes/materials.md`](notes/materials.md).

## Printers

FlashForge Creator Pro (2014, dual extruder, ~225 × 145 × 150 mm) and Monoprice Mini Delta (~110 mm round bed). Design limits and file formats: [`notes/printers.md`](notes/printers.md).

Filament: PLA by default, PETG or nylon for tough parts, **no ABS**.

## Router bits

Scribe, 1/8 in and 1/4 in. Corner reliefs and other rules: [`notes/shaper-bits.md`](notes/shaper-bits.md).

## Still to fill in
- Slicer in use for each printer
- Measured sheet thicknesses (in `notes/materials.md`)
