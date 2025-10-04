Guardian ODD Checks
===================

Purpose
-------
The Guardian evaluates operational design domain (ODD) constraints before approving a route. It blocks plans that exceed configured thresholds and records reasons for auditability.

Current (Stub) Checks
---------------------
- Slope: reject when estimated slope exceeds `navigation.max_slope_deg`.
- Clearance: reject when estimated clearance is less than `navigation.min_clearance_m`.
- Uncertainty: reject when uncertainty is above `navigation.max_uncertainty`.

Configuration
-------------
Edit `configs/thresholds.yaml` under the `navigation:` section:
```
navigation:
  max_slope_deg: 15.0
  min_clearance_m: 0.2
  max_uncertainty: 0.7
```

Audit & Explainability
----------------------
Every plan attempt is logged to the audit log with `allowed` and `reasons`. The UI “Why not?” panel should surface these reasons alongside overlays.

Planned Enhancements
--------------------
- Derive slope/clearance from ESDF and semantic layers.
- Add per-class risk factors (e.g., vegetation vs. human pathway).
- Include cost breakdown by source (length, slope, clearance, uncertainty).

