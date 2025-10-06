# Policy Cookbook (Stub)

## Export Policies
- Allow types: potree, potree_zip, laz, gltf, webm
- Allow CRS: EPSG:3857, EPSG:4978, EPSG:26915

## Examples
- Block unknown export type: return 403
- Enforce rounding limits: set max_rounding_mm in policy

## Files
- Config policy file path: `ROBOROUTER_OPA_POLICY` or `configs/opa/policy.yaml`
