# Human Review Checklist for KiCad PCB Generator

Even with automated validation, a manual design review remains essential before
sending a board for fabrication.  Use this checklist as the **final gate** in
your workflow.

## 1. Board Outline & Assembly
- [ ] Board outline closed, no stray graphic segments
- [ ] Mounting holes correct diameter & keep-outs
- [ ] Fiducials present (minimum 3) for pick-and-place
- [ ] Panelisation tabs/rails added if required by fab house

## 2. Components
- [ ] All footprints match manufacturer land-pattern (IPC-7351 or datasheet)
- [ ] Polarised parts (diodes, electrolytics, IC pin-1) oriented consistently
- [ ] Tall parts do not interfere with connectors, heatsinks, or enclosures
- [ ] Test points on critical nets (audio in/out, power rails, ground)

## 3. Silk & Labels
- [ ] Reference designators legible and not under components
- [ ] Polarity / orientation markers visible after assembly
- [ ] Revision, date, and project name on board
- [ ] Logo or text does not violate copper clearances

## 4. Power & Ground
- [ ] Decoupling capacitors placed within 2 mm of IC power pins
- [ ] Star-ground or ground-plane strategy consistent across layers
- [ ] Analog and digital grounds separated / stitched with resistor/ferrite if
      required
- [ ] Plane splits avoid return-path interruptions for high-speed or audio nets

## 5. Signal Integrity & Audio Performance
- [ ] High-impedance audio traces short and away from noisy digital lines
- [ ] Differential pairs length-matched and impedance-controlled where needed
- [ ] No stubs or acute (<45 °) trace angles on audio paths
- [ ] Shield tracks or guard rings applied to sensitive nodes (e.g. op-amp inputs)

## 6. DFM & Manufacturing
- [ ] Solder mask expansion meets fab capabilities (check DRC)
- [ ] Minimum annular ring and drill sizes within process spec
- [ ] Copper-to-edge clearance ok for castellations or card-edge connectors
- [ ] BOM fields (MPN, manufacturer) filled for every component

## 7. Validation Reports
- [ ] All automated KiCad DRC errors resolved (0 remaining)
- [ ] KiCad PCB Generator validations show no **ERROR** severity issues
- [ ] Warnings reviewed and accepted or fixed

## 8. Documentation Package
- [ ] PDF schematic generated and linked to revision
- [ ] Assembly drawings (top & bottom) exported as PDF
- [ ] Gerber, drill, and pick-and-place files generated & zipped
- [ ] README or manufacturing notes included (board thickness, finish, etc.)

---
Print this checklist (or include it in your PR) and tick each item before ordering 🚀 