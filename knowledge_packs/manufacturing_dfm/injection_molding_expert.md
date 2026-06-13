# Injection Molding Expert DFM Pack

Concept:
Injection molding is a coupled design/manufacturing problem. Geometry, material, tooling, cooling, ejection, surface quality, tolerance capability, and production volume must be considered together.

Rules:
- Confirm material family and grade before final wall thickness, shrinkage, draft, and tolerance decisions.
- Keep wall thickness uniform; avoid thick masses and abrupt transitions.
- Add draft to all pull-direction surfaces; textured surfaces need more draft.
- Use ribs for stiffness instead of thick sections; avoid overly thick rib roots.
- Core bosses and support them with ribs; avoid isolated thick bosses.
- Add generous radii to support flow, reduce stress concentration, and improve tool life.
- Reserve gate, runner, ejector, parting-line, and shutoff strategy before design freeze.
- Protect cosmetic A-surfaces from gates, ejector pins, sink, weld lines, and parting-line mismatch.
- Avoid tight plastic tolerances unless tied to functional datums and realistic process capability.
- Plan prototype, T0/T1 sampling, dimensional inspection, and functional validation.

Decision logic:
- If wall thickness is unknown, do not approve DFM; request nominal wall map.
- If material is unknown, identify candidate material family and grade-level risks.
- If annual volume is low, question whether injection tooling is economically justified.
- If cosmetic surface is critical, gate/ejector/parting-line placement becomes release-critical.

Failure risks:
- Sink marks, voids, short shot, weld line weakness, warpage, differential shrinkage, flash, ejection damage, brittle snaps, dimensional drift, high cycle time.

Required inputs:
- CAD/STEP or image, material grade, nominal wall thickness, surface class, production volume, assembly method, critical dimensions, tolerance requirements, operating environment.
