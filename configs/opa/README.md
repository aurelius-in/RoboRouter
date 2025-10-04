OPA Dev Loop
============

- Edit `policies.rego` and keep rules minimal and auditable.
- Validate with `opa eval` locally if available (air‑gapped ok).
- The API also includes a lightweight Python gate mirroring key checks.
- Exports call the gate and return 403 with a clear reason when blocked.

