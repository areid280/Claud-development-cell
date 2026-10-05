# 05 — Decision log

Append-only. Opus writes entries at gates and escalations. Newest at the bottom.

Template:

```
## D-NNN — <title>  (YYYY-MM-DD, gate/escalation id)
Context: <why a decision was needed>
Decision: <what we chose>
Alternatives: <what we rejected and why>
Consequences: <what this changes for later tasks>
```

## D-001 — MetaHuman-first, measurement-based body  (2026-10-05, planning)
Context: Generating a full body from one image gives poor topology and no rig.
Decision: Use a MetaHuman-compatible body driven by measurements in cm.
Alternatives: Raw image-to-3D body (ugly, unrigged); a parametric research body model as the final asset (licence limits, not UE-native).
Consequences: Body-fitting models only need to output measurements; they can be swapped without touching later stages.

## D-002 — Rented NVIDIA GPU for development  (2026-10-05, planning)
Context: Most 3D research code is NVIDIA/CUDA-only; owner has an AMD 7900 XT.
Decision: Develop and run on a RunPod RTX 4090. Revisit AMD at G5.
Consequences: Small hourly GPU cost outside the GitHub budget.

## D-003 — Three garment strategies  (2026-10-05, planning)
Context: Garment reconstruction from one image is unreliable for loose items.
Decision: `skin_layer` for tight items, `template` from a garment library for common items, `generated` image-to-3D for unusual items.
Consequences: Quality depends heavily on the garment library (assets/garment_library).
