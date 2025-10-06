# Policy Cookbook (Stub)

## Export Policies
- Allow types: potree, potree_zip, laz, gltf, webm
- Allow CRS: EPSG:3857, EPSG:4978, EPSG:26915

## Examples
- Block unknown export type: return 403
- Enforce rounding limits: set max_rounding_mm in policy

## Decision Logging
- All policy evaluations are logged to `_decision_log.jsonl` with a timestamp and input details.

## Versioning
- The policy loader exposes a `policy_version` in responses (e.g., `/policy/check`).

## Air-gapped
- Place policy files under `configs/opa/` and set `ROBOROUTER_OPA_POLICY` to the path or directory.

## Files
- Config policy file path: `ROBOROUTER_OPA_POLICY` or `configs/opa/policy.yaml`
