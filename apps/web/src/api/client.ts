export const API_BASE = (import.meta as any).env?.VITE_API_BASE || 'http://localhost:8000'

function authHeaders(): Record<string, string> {
  try {
    const k = (globalThis as any).localStorage?.getItem('api_key')
    return k ? { 'X-API-Key': k } : {}
  } catch {
    return {}
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, { headers: { ...authHeaders() } })
  if (!r.ok) throw new Error(`${path} failed`)
  return r.json() as Promise<T>
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!r.ok) throw new Error(`${path} failed`)
  return r.json() as Promise<T>
}

export async function apiDelete<T>(path: string): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, { method: 'DELETE', headers: { ...authHeaders() } })
  if (!r.ok) throw new Error(`${path} failed`)
  return r.json() as Promise<T>
}

export type Health = { status: string; gpu: { name: string }[] }
export const getHealth = () => apiGet<Health>('/health')

export const runPipeline = (sceneId: string, steps: string[]) =>
  apiPost<any>(`/pipeline/run?scene_id=${sceneId}`, { steps, config_overrides: {} })

export const generateReport = (sceneId: string) =>
  apiPost<any>(`/report/generate?scene_id=${sceneId}`)

export type ArtifactUrl = { artifact_id: string; type: string; url: string }
export const getArtifactUrl = (artifactId: string) => apiGet<ArtifactUrl>(`/artifacts/${artifactId}`)

export type SceneArtifact = { id: string; type: string; uri: string; created_at: string }
export type SceneMetric = { name: string; value: number; created_at: string }
export type SceneAudit = { id: string; action: string; details?: Record<string, any> | null; created_at: string }
export type SceneDetail = { id: string; artifacts: SceneArtifact[]; metrics?: SceneMetric[]; audit?: SceneAudit[] }
export const getScene = (sceneId: string) => apiGet<SceneDetail>(`/scene/${sceneId}`)

export const requestExport = (sceneId: string, type: string, crs: string = 'EPSG:3857') =>
  apiPost<any>(`/export?scene_id=${sceneId}&type=${type}&crs=${crs}`)

export const getMeta = () => apiGet<any>('/meta')
export const getStats = () => apiGet<any>('/stats')
export const getConfig = () => apiGet<any>('/config')
export const policyCheck = (type: string, crs: string) => apiPost<{ allowed: boolean; reason: string }>(`/policy/check`, { export_type: type, crs })
export const adminCleanup = () => apiPost<any>('/admin/cleanup')
export const authPing = () => apiGet<any>('/auth/ping')
export const getRuns = (opts?: { only_failed?: boolean; only_passed?: boolean; limit?: number }) => {
  const p = new URLSearchParams()
  if (opts?.only_failed) p.set('only_failed', 'true')
  if (opts?.only_passed) p.set('only_passed', 'true')
  if (opts?.limit) p.set('limit', String(opts.limit))
  const qs = p.toString()
  return apiGet<any>(`/runs${qs ? `?${qs}` : ''}`)
}
export const deleteScene = (sceneId: string) => apiDelete<any>(`/scene/${sceneId}`)
export const getModels = () => apiGet<any>('/models')


